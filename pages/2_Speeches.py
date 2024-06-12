import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from agg_data import get_member_list, get_all_member_speeches
from members import aggregate_member_metrics
from utils import (
    calculate_readability,
    PARTY_COLOURS
)

# BACKEND

speech_df = get_all_member_speeches()

parliaments = {"12th (2011-2015)": [12], "13th (2016-2020)": [13], "14th (2020-present)": [14], "All": [12, 13, 14]}

# selection

st.title("Speeches")

select_parliament = st.radio(
        label="Which parliament?", 
        options=parliaments.keys(), 
        index=3,
        horizontal=True
    )

speech_df = speech_df[
    speech_df["parliament"].isin(parliaments[select_parliament])
    ]

tabs = ['party', 'member']
by_party, by_member = st.tabs(tabs)

with by_party:

    agg_speech_df = aggregate_member_metrics(
        speech_df,
        calculate_readability,
        group_by_fields=[
            'year',
            'month',
            "member_party",
            "parliament",
        ],
    )

    # give a date column

    agg_speech_df['date'] = pd.to_datetime(agg_speech_df[['year', 'month']].assign(day=1))

    # create graph for speech composition 

    # Create the figure
    fig = go.Figure()

    for party, color in PARTY_COLOURS.items():
        fig.add_trace(go.Scatter(
            x=agg_speech_df.query(f'member_party=="{party}"').date,
            y=agg_speech_df.query(f'member_party=="{party}"').count_words,
            mode='lines',
            line=dict(width=2, color=color),
            stackgroup='one',
            groupnorm='percent',
            name=party,
            hovertemplate='%{y:.1f}%<extra></extra>'
        ))

    # Update layout
    fig.update_layout(
        title='Percentage Words Spoken by Party by Year-Month',
        xaxis=dict(title='Date'),
        yaxis=dict(title='% of Total Words'),
        hovermode='x unified',
        showlegend=True
    )

    st.plotly_chart(fig)

with by_member:

    agg_mem_df = aggregate_member_metrics(
        speech_df,
        calculate_readability,
        group_by_fields=[
            "member_party",
            'member_name'
        ],
    )

    # Filter out rows where words_per_sitting is nan
    agg_mem_df = agg_mem_df[
        ~(agg_mem_df["speeches_per_sitting"].isna())
    ]

    selected_members = st.multiselect(
        'Select member name(s):',
        options=['All'] + sorted(agg_mem_df['member_name'].unique()),
                                 default='All',
                                 help='Type and select one or more member names'
    )   

    # round 

    columns_to_round = ['topics_per_sitting', 'speeches_per_sitting', 'words_per_sitting']

    agg_mem_df[columns_to_round] = agg_mem_df[columns_to_round].apply(lambda x: x.round(2)) 

    # generate ranges
    xmax = max(agg_mem_df.topics_per_sitting)
    ymax = max(agg_mem_df.speeches_per_sitting)

    xpad = xmax * 0.1
    ypad = ymax * 0.1

    xrange = [0, xmax + xpad]
    yrange = [0, ymax + ypad]

    # sizing

    min_size = 5
    max_size = 20

    agg_mem_df['absolute_size'] = agg_mem_df['words_per_sitting'].apply(lambda x: min_size + (max_size - min_size) * (x - agg_mem_df['words_per_sitting'].min()) / (agg_mem_df['words_per_sitting'].max() - agg_mem_df['words_per_sitting'].min()))

    # filter out select members

    if 'All' in selected_members:
        filtered_mem_df = agg_mem_df
    else: 
        filtered_mem_df = agg_mem_df[agg_mem_df.member_name.isin(selected_members)]
    
    # Create the scatter plot
    fig = px.scatter(
        filtered_mem_df,
        x='topics_per_sitting',
        y='speeches_per_sitting',
        color='member_party',
        hover_name='member_name',
        title='Speeches per Sitting vs Topics per Sitting<br><sup>Point sizes correspond to words used in speeches</sup>',
        size_max=15,
        labels={
            'speeches_per_sitting': 'Speeches per Sitting',
            'topics_per_sitting': 'Topics per Sitting'
        },
        range_x = xrange,
        range_y = yrange,
        color_discrete_map=PARTY_COLOURS,
        custom_data=['absolute_size', 'member_party']
    )

    fig.update_traces(
    marker=dict(size=filtered_mem_df['absolute_size']),
    hovertemplate=(
        '<b>%{hovertext}</b><br><br>' +  # Member name
        'size: %{customdata[0]}<br>' +  # Custom data for words_per_sitting
        '<extra></extra>'  # Removes the secondary box
    ),
    selector=dict(type='scatter')
)

    st.plotly_chart(fig)



    


