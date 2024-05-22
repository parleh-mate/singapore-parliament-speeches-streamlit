import streamlit as st
import altair as alt
from agg_data import (
    get_member_list,
    get_member_positions,
    get_all_member_speeches,
    primary_question_topics,
)
import pandas as pd
from datetime import datetime
from scipy.stats import percentileofscore
from millify import millify
import numpy as np

st.set_page_config(
    page_title="Performance by Members",
    page_icon="💬",
    initial_sidebar_state="expanded",
)

# BACKEND


def average_non_zero(x):
    non_zero_values = x[x != 0]
    return np.mean(non_zero_values) if len(non_zero_values) > 0 else 0


def calculate_readability(row):
    total_words = row["count_words"]
    total_sentences = row["count_sentences"]
    total_syllables = row["count_syllables"]

    readability = (
        206.835
        - (1.015 * total_words / total_sentences)
        - (84.6 * total_syllables / total_words)
    )
    return readability


def aggregate_by_ministry(df):
    grouped_df = (
        df.groupby("ministry_addressed")["count_pri_questions"].sum().reset_index()
    )
    total_questions = grouped_df["count_pri_questions"].sum()
    grouped_df["proportion_of_questions"] = (
        grouped_df["count_pri_questions"] / total_questions
    )
    return grouped_df


def calculate_relative_proportion(selected_member, df, grouped_df):
    member_questions = df[df["member_name"] == selected_member]
    member_total_questions = member_questions["count_pri_questions"].sum()

    grouped_df["relative_proportion_pri_questions"] = (
        grouped_df["proportion_of_questions"] * member_total_questions
    )
    grouped_df = grouped_df[["ministry_addressed", "relative_proportion_pri_questions"]]
    grouped_df["member_name"] = "Relative Proportion"
    grouped_df = grouped_df.rename(
        columns={"relative_proportion_pri_questions": "count_pri_questions"}
    )

    final_df = pd.concat([member_questions, grouped_df], ignore_index=True)
    final_df = final_df[["member_name", "ministry_addressed", "count_pri_questions"]]

    return final_df


def get_member_speeches(member_name):
    all_members_speeches_summary = get_all_member_speeches()
    return all_members_speeches_summary[
        all_members_speeches_summary["member_name"] == member_name
    ]


@st.cache_data(ttl=6000)
def prepare_aggregated_data():
    members_df = get_member_list()
    member_positions_df = get_member_positions()
    all_members_speech_summary = get_all_member_speeches()

    column_names = [
        "count_sittings_attended",
        "count_sittings_spoken",
        "count_topics",
        "count_speeches",
        "count_words",
        "count_pri_questions",
        "count_sentences",
        "count_syllables",
    ]

    # agg by member
    agg_by_member_dict = {col: "sum" for col in column_names}
    aggregated_by_member = (
        all_members_speech_summary.groupby("member_name")
        .agg(agg_by_member_dict)
        .reset_index()
    )
    aggregated_by_member.columns = ["member_name"] + column_names

    aggregated_by_member["participation_rate"] = (
        aggregated_by_member["count_sittings_spoken"]
        / aggregated_by_member["count_sittings_attended"]
        * 100
    )
    aggregated_by_member["topics_per_sitting"] = (
        aggregated_by_member["count_topics"]
        / aggregated_by_member["count_sittings_spoken"]
    )
    aggregated_by_member["questions_per_sitting"] = (
        aggregated_by_member["count_pri_questions"]
        / aggregated_by_member["count_sittings_spoken"]
    )
    aggregated_by_member["words_per_sitting"] = (
        aggregated_by_member["count_words"]
        / aggregated_by_member["count_sittings_spoken"]
    )

    aggregated_by_member["readability"] = aggregated_by_member.apply(
        calculate_readability, axis=1
    )

    aggregated_by_member = aggregated_by_member[
        aggregated_by_member["count_sittings_attended"] != 0
    ]
    # agg by year (average metrics)
    agg_by_year_dict = {col: average_non_zero for col in column_names}
    aggregated_by_year = (
        all_members_speech_summary.groupby("year").agg(agg_by_year_dict).reset_index()
    )
    aggregated_by_year.columns = ["year"] + [f"avg_{col}" for col in column_names]
    aggregated_by_year["year"] = (
        aggregated_by_year["year"].astype(str).str.replace("[,.]", "", regex=True)
    )
    # agg by year (overall readability)
    readability_cols = ["count_words", "count_sentences", "count_syllables"]
    readability_dict = {col: sum for col in readability_cols}
    aggregated_by_year_readability = (
        all_members_speech_summary.groupby("year").agg(readability_dict).reset_index()
    )
    aggregated_by_year_readability.columns = ["year"] + readability_cols
    aggregated_by_year_readability[
        "overall_readability"
    ] = aggregated_by_year_readability.apply(calculate_readability, axis=1)
    aggregated_by_year_readability["year"] = (
        aggregated_by_year_readability["year"]
        .astype(str)
        .str.replace("[,.]", "", regex=True)
    )
    aggregated_by_year = aggregated_by_year.merge(
        aggregated_by_year_readability[["year", "overall_readability"]],
        how="left",
        on="year",
    )

    # primary questions
    agg_questions_by_members = primary_question_topics()

    return (
        members_df,
        member_positions_df,
        aggregated_by_member,
        aggregated_by_year,
        agg_questions_by_members,
    )


(
    members_df,
    member_positions_df,
    aggregated_by_member,
    aggregated_by_year,
    agg_questions_by_members,
) = prepare_aggregated_data()
member_names = sorted(members_df["member_name"].unique())

EARLIEST_SITTING = "2012-09-10"

# FRONTEND

select_member = st.sidebar.selectbox(
    label="Which member are you interested in?",
    options=member_names,
    index=None,
    placeholder="Choose member name",
)

st.title("Performance by Members")
st.warning("Under construction.")

if not select_member:
    st.error("Please select a member on the sidebar.")

if select_member:
    member_info, member_picture = st.columns([3, 1])
    member_df = members_df[members_df["member_name"] == select_member]

    with member_info:
        st.header(select_member)
        member_birth_year = member_df["member_birth_year"].iloc[0]

        if member_birth_year:
            member_birth_year_int = int(member_birth_year)
            member_age_int = datetime.now().year - member_birth_year_int
            st.markdown(
                f"""
                * Last Political Affiliation: {member_df['party'].iloc[0]}
                * Latest Constituency: {member_df['constituency'].iloc[0]}{' (Inactive)' if member_df['is_active'].iloc[0] == False else ''}
                * Birth Year: {member_birth_year_int} (_Age: {member_age_int}_)
                """
            )
        else:
            st.markdown("* Birth Year: _unknown_")

        condition_earliest_sitting_in_dataset = (
            str(member_df["earliest_sitting"].iloc[0]) > EARLIEST_SITTING
        )
        member_earliest_sitting = (
            member_df["earliest_sitting"].iloc[0]
            if condition_earliest_sitting_in_dataset
            else str(member_df["earliest_sitting"].iloc[0]) + " _or before_"
        )
        member_latest_sitting = member_df["latest_sitting"].iloc[0]

        if not condition_earliest_sitting_in_dataset:
            st.info(
                f"The earliest sitting is likely before this date, but the earliest date in the dataset is {EARLIEST_SITTING}, and therefore this is the earliest date which is displayed."
            )

        count_sittings_present = member_df["count_sittings_present"].iloc[0]
        count_sittings_total = member_df["count_sittings_total"].iloc[0]

        st.markdown(
            f"""
            * Earliest Sitting: {member_earliest_sitting}
            * Latest Sitting: {member_latest_sitting}
            * Attendance: {count_sittings_present/count_sittings_total*100:.1f}% (_{count_sittings_present} out of {count_sittings_total} sittings_)
            """
        )

    with member_picture:
        member_image_link = member_df["member_image_link"].iloc[0]
        if member_image_link:
            st.image(image=str(member_image_link), width=150)

    st.divider()
    st.subheader("Speeches")

    speech_summary = get_member_speeches(select_member)
    speech_summary["readability"] = speech_summary.apply(calculate_readability, axis=1)
    speech_summary["year"] = (
        speech_summary["year"].astype(str).str.replace("[,.]", "", regex=True)
    )
    speech_summary = speech_summary.merge(aggregated_by_year, how="left", on="year")

    if not condition_earliest_sitting_in_dataset:
        st.warning(
            f"As this member was elected before the earliest sitting ({EARLIEST_SITTING}), the information below reflects information from sittings on {EARLIEST_SITTING} and after."
        )

    not_eligible_to_ask_questions = (
        # is a political appointee
        not member_positions_df.loc[
            (member_positions_df["member_name"] == select_member)
            & (member_positions_df["type"] == "appointment")
        ].empty
        # and not a mayor
        and member_positions_df.loc[
            (member_positions_df["member_name"] == select_member)
            & member_positions_df["member_position"].str.contains("mayor", case=False)
        ].empty
    )

    if not_eligible_to_ask_questions:
        st.success(
            f"As this member has a political appointment (e.g. Minister, Parliamentary Secretary, Minister of State), they will not ask questions during parliamentary proceedings. Instead, they answer questions. If there are values for questions asked, this could either be before the member became a political appointee or a bug."
        )

    metric1, metric2, metric3, metric4, metric5 = st.columns(5)
    with metric1:
        st.metric(
            label="Sittings Attended",
            value=f"{speech_summary['count_sittings_attended'].sum():,.0f}",
        )
        st.metric(
            label="Sittings Spoken",
            value=f"{speech_summary['count_sittings_spoken'].sum():,.0f}",
        )
    with metric2:
        st.metric(label="Topics", value=f"{speech_summary['count_topics'].sum():,.0f}")
        member_participation_rate = (
            speech_summary["count_sittings_spoken"].sum()
            / speech_summary["count_sittings_attended"].sum()
            * 100
        )
        st.metric(
            label="Participation (%)",
            value=f"{member_participation_rate:.1f}%",
            help="Sittings Spoken in divided by Sittings Attended",
        )
        st.caption(
            f"Percentile: {percentileofscore(aggregated_by_member['participation_rate'], member_participation_rate):.1f}"
        )
        st.caption(f"Average: {aggregated_by_member['participation_rate'].mean():.1f}%")
    with metric3:
        st.metric(
            label="Speeches Made",
            value=f"{speech_summary['count_speeches'].sum():,.0f}",
        )
        member_topics_per_sitting = (
            speech_summary["count_topics"].sum()
            / speech_summary["count_sittings_spoken"].sum()
        )
        st.metric(
            label="Topics/Sitting",
            value=f"{member_topics_per_sitting:,.2f}",
        )
        st.caption(
            f"Percentile: {percentileofscore(aggregated_by_member['topics_per_sitting'], member_topics_per_sitting):.1f}"
        )
        st.caption(f"Average: {aggregated_by_member['topics_per_sitting'].mean():,.2f}")
    with metric4:
        st.metric(
            label="Qns Asked",
            value=f"{speech_summary['count_pri_questions'].sum():,.0f}",
        )
        member_questions_per_sitting = (
            speech_summary["count_pri_questions"].sum()
            / speech_summary["count_sittings_spoken"].sum()
        )
        st.metric(
            label="Qns/Sitting",
            value=f"{member_questions_per_sitting:,.2f}",
        )
        if not_eligible_to_ask_questions:
            st.caption("N/A")
        else:
            st.caption(
                f"Percentile: {percentileofscore(aggregated_by_member['questions_per_sitting'], member_questions_per_sitting):.1f}"
            )
            st.caption(
                f"Average: {aggregated_by_member[aggregated_by_member['questions_per_sitting'] != 0]['questions_per_sitting'].mean():,.2f}"
            )
    with metric5:
        st.metric(
            label="Words Spoken",
            value=f"{millify(speech_summary['count_words'].sum(), precision=1)}",
        )
        member_words_per_sitting = (
            speech_summary["count_words"].sum()
            / speech_summary["count_sittings_spoken"].sum()
        )
        st.metric(
            label="Words/Sitting",
            value=f"{millify(member_words_per_sitting, precision=1)}",
        )
        st.caption(
            f"Percentile: {percentileofscore(aggregated_by_member['words_per_sitting'], member_words_per_sitting):.1f}"
        )
        st.caption(
            f"Average: {millify(aggregated_by_member['words_per_sitting'].mean(), precision=1)}"
        )

    if not not_eligible_to_ask_questions:
        agg_by_ministry_addressed = aggregate_by_ministry(agg_questions_by_members)
        questions_summary_with_relative_proportion = calculate_relative_proportion(
            select_member, agg_questions_by_members, agg_by_ministry_addressed
        )

        st.divider()
        st.write("Parliamentary questions asked:")

        chart = (
            alt.Chart(questions_summary_with_relative_proportion)
            .mark_bar()
            .encode(
                x=alt.X(
                    "sum(count_pri_questions):Q", title="Count of Primary Questions"
                ),
                y=alt.Y("member_name:N", sort="x", title="Ministry Addressed"),
                color="member_name:N",
                row="ministry_addressed:N",
                tooltip=["member_name", "ministry_addressed", "count_pri_questions"],
            )
            .properties(
                height=20,
            )
        )

        horizontal_chart = (
            chart.configure_view(continuousHeight=100)
            .configure_axis(labelFontSize=0)
            .configure_title(fontSize=0)
            .configure_legend(titleFontSize=14, labelFontSize=12)
            .configure_axisY(disable=True)
            .configure_header(labelAngle=0, labelAnchor="start", labelBaseline="middle")
            .configure_scale(bandPaddingInner=0.001, bandPaddingOuter=0.001)
        )

        st.altair_chart(horizontal_chart, use_container_width=True)

    st.divider()
    st.write("Over the years:")
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.line_chart(
            data=speech_summary,
            x="year",
            y=["count_topics", "avg_count_topics"],
            height=200,
        )
        st.line_chart(
            data=speech_summary,
            x="year",
            y=["count_pri_questions", "avg_count_pri_questions"],
            height=200,
        )
    with col2:
        st.line_chart(
            data=speech_summary,
            x="year",
            y=["count_speeches", "avg_count_speeches"],
            height=200,
        )
        st.line_chart(
            data=speech_summary,
            x="year",
            y=["count_words", "avg_count_words"],
            height=200,
        )
    st.line_chart(
        data=speech_summary,
        x="year",
        y=["readability", "overall_readability"],
        height=200,
    )

    st.divider()
    st.subheader("Positions")
    positions_df = member_positions_df[
        member_positions_df["member_name"] == select_member
    ]
    columns_to_display = [
        "member_position",
        "effective_from_date",
        "effective_to_date",
        "is_latest_position",
    ]

    constituencies_df = positions_df[positions_df["type"] == "constituency"][
        columns_to_display
    ]
    if not constituencies_df.empty:
        st.write("Constituencies")
        st.dataframe(constituencies_df, use_container_width=True, hide_index=True)

    appointments_df = positions_df[positions_df["type"] == "appointment"][
        columns_to_display
    ]
    if not appointments_df.empty:
        st.write("Political Appointments")
        st.dataframe(appointments_df, use_container_width=True, hide_index=True)
