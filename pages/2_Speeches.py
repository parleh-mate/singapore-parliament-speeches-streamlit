import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from agg_data import get_member_list, get_all_member_speeches
from members import aggregate_member_metrics
from utils import (
    project_id,
    query_to_dataframe,
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

tabs = ['By Member', 'By Party']
by_member, by_party = st.tabs(tabs)

with by_member:

    agg_mem_df = aggregate_member_metrics(
        speech_df,
        calculate_readability,
        group_by_fields=[
            "member_party",
            'member_name',
            'member_constituency'
        ],
    )

    # generate ranges for axes limits
    xmax = max(agg_mem_df.topics_per_sitting)
    ymax = max(agg_mem_df.speeches_per_sitting)

    xpad = xmax * 0.15
    ypad = ymax * 0.15

    xrange = [0, xmax + xpad]
    yrange = [0, ymax + ypad]

    # select constituency

    if select_parliament!="All":

        selected_constituency = st.multiselect(
            'Select constituency:',
            ['All'] + sorted(agg_mem_df['member_constituency'].unique()),
            default = 'All',
            help='Type and select one or more constituencies'
            )
        
         # filter out selected constituencies

        if 'All' not in selected_constituency:
            agg_mem_df = agg_mem_df[agg_mem_df.member_constituency.isin(selected_constituency)]
        
    # select members

    selected_members = st.multiselect(
        'Select member name(s):',
        options=['All'] + sorted(agg_mem_df['member_name'].unique()),
                                 default='All',
                                 help='Type and select one or more member names'
    )

    # filter out select members

    if 'All' not in selected_members:
        agg_mem_df = agg_mem_df[agg_mem_df.member_name.isin(selected_members)]
    
    # Create the scatter plot
    fig = px.scatter(
        agg_mem_df,
        y='topics_per_sitting',
        x='speeches_per_sitting',
        size = 'participation_rate',
        color='member_party',
        hover_name='member_name',
        title="Speeches per Sitting vs Topics per Sitting<br><sup>Point sizes correspond to an MP's participation rate</sup>",
        size_max=10,
        labels={
            'speeches_per_sitting': 'Speeches per Sitting',
            'topics_per_sitting': 'Topics per Sitting'
        },
        range_x = xrange,
        range_y = yrange,
        color_discrete_map=PARTY_COLOURS
    )

    fig.update_traces(marker_sizemin=2,
                      selector=dict(type='scatter'))  

    st.plotly_chart(fig)


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

    # Create the figure
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=("Speeches", "Questions"))
    
    vars = ['count_speeches', 'count_pri_questions']

    for i, var in enumerate(vars, start=1):
        for party, color in PARTY_COLOURS.items():
            show_legend = (i == 1)  # Show legend only for the first subplot
            fig.add_trace(go.Scatter(
                x=agg_speech_df.query(f'member_party=="{party}"').date,
                y=agg_speech_df.query(f'member_party=="{party}"')[var],
                mode='lines',
                line=dict(width=2, color=color),
                stackgroup='one',
                groupnorm='percent',
                name=party,
                legendgroup=party,
                showlegend=show_legend,
                hovertemplate='%{y:.1f}%<extra></extra>'
            ),
            row=1,
            col=i)

    # Update layout
    fig.update_layout(
        title='Percentage Speeches made by Party by Year-Month',
        xaxis_title='Date',
        yaxis_title='% of Total',
        hovermode='x unified',
        showlegend=True
    )
    st.plotly_chart(fig)




    


