import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import re
from agg_data import get_all_member_speeches, get_speech_sum
from members import aggregate_member_metrics
from utils import (
    calculate_readability,
    PARTY_COLOURS
)

# BACKEND

speech_df = get_all_member_speeches()
sum_df = get_speech_sum()

parliaments = {"12th (2011-2015)": [12], "13th (2016-2020)": [13], "14th (2020-present)": [14], "All": [12, 13, 14]}

# selection

def filter_fun(df, var, isin):
    return df[df[var].isin(isin)]

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

        l_df = [agg_mem_df, sum_df]

        for i in range(len(l_df)):
            l_df[i] = filter_fun(l_df[i], "member_constituency",
                                 selected_constituency)
                        
        agg_mem_df, sum_df = l_df
        
    # select members

    selected_members = st.multiselect(
        'Select member name(s):',
        options=['All'] + sorted(agg_mem_df['member_name'].unique()),
                                 default='All',
                                 help='Type and select one or more member names'
    )

    # filter out select members

    if 'All' not in selected_members:
        for i in range(len(l_df)):
            l_df[i] = filter_fun(l_df[i], "member_name",
                                 selected_members)
                                    
        agg_mem_df, sum_df = l_df
    
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
    
    sum_df = sum_df[['date', 'parliament', 'session',
                     'member_name', 'member_party',
                     'member_constituency', 'speech_summary']]
    st.plotly_chart(fig)

    #prepare the table
    st.header("Speech summaries")
    st.info("Speech summaries generated using openai's GPT-3.5. Double click on each speech to display it in full. For more information, consult our Methodology section.", icon="ℹ️")

    sum_df = sum_df.drop(['session'], axis = 1)
    sum_df = sum_df.rename(columns = {"member_name": "name",
                                      "member_party": "party",
                                      "member_constituency": "constituency"})
    
    sum_df['date'] = sum_df['date'].apply(lambda x: re.search("\d{4}-\d{2}-\d{2}", x).group())    
    
    st.dataframe(sum_df, hide_index=True)    

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

    fig = px.scatter()

    for party, color in PARTY_COLOURS.items():
        fig.add_trace(go.Scatter(
            x=agg_speech_df.query(f'member_party=="{party}"').date,
            y=agg_speech_df.query(f'member_party=="{party}"')["count_speeches"],
            mode='lines',
            line=dict(width=2, color=color),
            stackgroup='one',
            groupnorm='percent',
            name=party,
            legendgroup=party,
            hovertemplate='%{y:.1f}%<extra></extra>'
        ))

    # Update layout
    fig.update_layout(
        title='Percentage Speeches made by Party by Year-Month',
        xaxis_title='Date',
        yaxis_title='% of Total',
        hovermode='x unified',
        showlegend=True
    )
    st.plotly_chart(fig)




    


