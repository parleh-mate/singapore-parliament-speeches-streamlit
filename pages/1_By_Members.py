import streamlit as st
from utils import project_id, run_query
import pandas as pd
from datetime import datetime

# BACKEND

def get_member_list():
    query = f"""
    select
        member_name,
        member_birth_year,
        member_image_link,
        party,
        earliest_sitting,
        latest_sitting,
        count_sittings_present,
        count_sittings_total
    from `{project_id}.prod_dim.dim_members`
    where member_name != '' and member_name is not null
    """
    return pd.DataFrame(run_query(query))

def get_member_positions():
    query = f"""
    select * from `{project_id}.prod_fact.fact_member_positions`
    """
    return pd.DataFrame(run_query(query))

def get_member_speeches(member_name):
    query = f"""
    select
        extract(year from date) as year,
        count(distinct topic_id) as count_topics,
        count(*) as count_speeches,
        sum(count_speeches_words) as count_words,
        countif(is_primary_question) as count_pri_questions,
        206.835
        - (1.015 * sum(count_speeches_words) / sum(count_speeches_sentences))
        - (84.6 * sum(count_speeches_syllables) / sum(count_speeches_words)) as readability
    from `{project_id}.prod_mart.mart_speeches`
    where member_name = '{member_name}'
    group by all
    """

    return pd.DataFrame(run_query(query))

members_df = get_member_list()
member_names = sorted(members_df['member_name'].unique())
member_positions_df = get_member_positions()

EARLIEST_SITTING = '2012-09-10'

# FRONTEND

select_member = st.sidebar.selectbox(
    label="Which member are you interested in?",
    options=member_names,
    index=None,
    placeholder="Choose member name"
)

st.title('Performance by Members')
st.warning('Under construction.')
if select_member:
    member_info, member_picture = st.columns([3, 1])
    member_df = members_df[members_df['member_name'] == select_member]

    with member_info:
        st.header(select_member)

        member_birth_year = member_df['member_birth_year'].iloc[0]
        if member_birth_year:
            member_birth_year_int = int(member_birth_year)
            member_age_int = datetime.now().year - member_birth_year_int
            st.markdown(f"""
                        * Last Political Affiliation: {member_df['party'].iloc[0]}
                        * Birth Year: {member_birth_year_int} (_Age: {member_age_int}_)
                        """)
        else:
            st.markdown("""
                        * Birth Year: _unknown_
                        """)

        condition_earliest_sitting_in_dataset = str(member_df['earliest_sitting'].iloc[0]) > EARLIEST_SITTING

        if condition_earliest_sitting_in_dataset:
            member_earliest_sitting = member_df['earliest_sitting'].iloc[0]
        else:
            member_earliest_sitting = str(member_df['earliest_sitting'].iloc[0]) + " _or before_"
        member_latest_sitting = member_df['latest_sitting'].iloc[0]

        if not condition_earliest_sitting_in_dataset:
            st.info(f"The earliest sitting is likely before this date, but the earliest date in the dataset is {EARLIEST_SITTING}, and therefore this is the earliest date which is displayed.")

        count_sittings_present = member_df['count_sittings_present'].iloc[0]
        count_sittings_total = member_df['count_sittings_total'].iloc[0]

        st.markdown(f"""
                    * Earliest Sitting: {member_earliest_sitting}
                    * Latest Sitting: {member_latest_sitting}
                    * Attendance: {count_sittings_present/count_sittings_total*100:.1f}% (_{count_sittings_present} out of {count_sittings_total} sittings_)
                    """)

    with member_picture:
        member_image_link = member_df['member_image_link'].iloc[0]
        if member_image_link:
            st.image(
                image=str(member_image_link),
                width=150
            )

    st.divider()
    st.subheader("Speeches")

    speech_summary = get_member_speeches(select_member)

    if not condition_earliest_sitting_in_dataset:
        st.warning(f"As this member was elected before the earliest sitting ({EARLIEST_SITTING}), the information below reflects information from sittings on {EARLIEST_SITTING} and after.")

    # is political appointee
    if not member_positions_df.loc[(member_positions_df['member_name'] == select_member) &
                                 (member_positions_df['type'] == 'appointment')].empty:
        # and is not mayor
        if member_positions_df.loc[(member_positions_df['member_name'] == select_member) &
                                   member_positions_df['member_position'].str.contains('mayor', case=False)].empty:
            st.success(f"As this member has a political appointment (e.g. Minister, Parliamentary Secretary, Minister of State), they will not ask questions during parliamentary proceedings. Instead, they answer questions. If there are values for questions asked, this could either be before the member became a political appointee or a bug.")

    metric1, metric2, metric3, metric4, metric5 = st.columns(5)
    with metric1:
        st.metric(label='Sittings Attended',
                value=count_sittings_present)
    with metric2:
        st.metric(label='Topics',
                value=f"{speech_summary['count_topics'].sum():,}")
    with metric3:
        st.metric(label='Speeches Made',
                value=f"{speech_summary['count_speeches'].sum():,}")
    with metric4:
        st.metric(label='Qns Asked',
                value=f"{speech_summary['count_pri_questions'].sum():,}")
    with metric5:
        st.metric(label='Words Spoken',
                value=f"{speech_summary['count_words'].sum():,}")

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        st.bar_chart(data=speech_summary,
               x='year',
               y='count_topics',
               height=200)
        st.bar_chart(data=speech_summary,
               x='year',
               y='count_pri_questions',
               height=200)
    with col2:
        st.bar_chart(data=speech_summary,
               x='year',
               y='count_speeches',
               height=200)
        st.bar_chart(data=speech_summary,
               x='year',
               y='count_words',
               height=200)
    st.line_chart(data=speech_summary,
                  x='year',
                  y='readability',
                  height=200)

    st.divider()
    st.subheader("Positions")
    positions_df = member_positions_df[member_positions_df['member_name'] == select_member]
    columns_to_display = ['member_position', 'effective_from_date', 'effective_to_date', 'is_latest_position']

    constituencies_df = positions_df[positions_df['type'] == 'constituency'][columns_to_display]
    if not constituencies_df.empty:
        st.write("Constituencies")
        st.dataframe(constituencies_df, use_container_width=True, hide_index=True)

    appointments_df = positions_df[positions_df['type'] == 'appointment'][columns_to_display]
    if not appointments_df.empty:
        st.write("Political Appointments")
        st.dataframe(appointments_df, use_container_width=True, hide_index=True)
