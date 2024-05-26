import streamlit as st
import pandas as pd
from millify import millify
from agg_data import get_member_list, get_member_positions, get_all_member_speeches
from members import (
    categorise_active_members_with_appointments,
    aggregate_member_metrics,
)
from utils import calculate_readability, EARLIEST_SITTING

# BACKEND

members_df = get_member_list()
constituency_names = sorted(
    members_df[members_df["constituency"].notna()]["constituency"].unique()
)

# current appointments:
all_member_positions = get_member_positions()
current_member_appointments = all_member_positions[
    (all_member_positions["type"] == "appointment")
    & (all_member_positions["is_latest_position"])
]

# metrics by member:
all_members_speech_summary = get_all_member_speeches()
aggregated_by_member = aggregate_member_metrics(
    all_members_speech_summary, calculate_readability, group_by_fields=["member_name"]
)
metrics_to_display = [
    "member_name",
    "participation_rate",
    "topics_per_sitting",
    "questions_per_sitting",
    "words_per_sitting",
    "readability",
]
aggregated_by_member_display = aggregated_by_member[metrics_to_display]
aggregated_by_member_display["participation_rate"] = (
    aggregated_by_member["participation_rate"].round(1).astype(str) + "%"
)
for metric in metrics_to_display:
    if metric not in [
        "member_name",
        "participation_rate",
    ] and pd.api.types.is_numeric_dtype(aggregated_by_member_display[metric]):
        aggregated_by_member_display[metric] = aggregated_by_member_display[
            metric
        ].round(2)


# former members:
def filter_former_members(select_constituency):
    former_members = members_df[
        (members_df["constituency"] == select_constituency)
        & (members_df["is_active"] == False)
    ]

    return former_members


# FRONTEND

st.title("Performance by Constituency")

st.warning("Under construction.")

select_constituency = st.sidebar.selectbox(
    label="Which constituency are you interested in?",
    options=constituency_names,
    index=None,
    placeholder="Choose constituency name",
)

if not select_constituency:
    st.error("Please select a constituency on the sidebar.")

if select_constituency:
    st.header(f"{select_constituency}")

    st.subheader("Active Members")

    active_members = sorted(
        members_df[
            (members_df["constituency"] == select_constituency)
            & (members_df["is_active"] == True)
        ]["member_name"].tolist()
    )

    def display_members(members, start_index=0):
        columns = st.columns(5, gap="medium")
        for i, col in enumerate(columns):
            member_index = start_index + i
            with col:
                if member_index < len(members):
                    member_name = members[member_index]
                    member_image_link = members_df[
                        members_df["member_name"] == member_name
                    ]["member_image_link"].iloc[0]
                    st.image(member_image_link, width=100, caption=member_name)
                else:
                    st.empty()

    # Display the first 5 active members
    display_members(active_members, start_index=0)

    # Display the next 5 active members if they exist
    if len(active_members) > 5:
        display_members(active_members, start_index=5)

    (
        active_members_with_appointments,
        active_member_appointments,
        active_members_without_appointments,
    ) = categorise_active_members_with_appointments(
        active_members, current_member_appointments
    )

    def display_metrics(member_name):
        columns = st.columns(5, gap="medium")
        metrics = [
            ("participation_rate", "Participation (%)", "1"),
            ("topics_per_sitting", "Topics/Sitting", "1"),
            ("questions_per_sitting", "Qns/Sitting", "2"),
            ("words_per_sitting", "Words/Sitting", "2"),
            ("readability", "Readability", "1"),
        ]
        for i, col in enumerate(columns):
            with col:
                value = aggregated_by_member_display[
                    aggregated_by_member_display["member_name"] == member_name
                ][metrics[i][0]].iloc[0]
                if isinstance(value, (int, float)):
                    value = millify(value, precision=metrics[i][2])
                st.metric(
                    label=metrics[i][1],
                    value=value,
                )

    if active_members_with_appointments:
        with st.expander("### Appointment Holders"):
            st.success(
                f"As these member(s) have a political appointment (e.g. Minister, Parliamentary Secretary, Minister of State), they will not ask questions during parliamentary proceedings. Instead, they answer questions. If there are values for questions asked, this could either be before the member became a political appointee or a bug."
            )
            for idx, member_name in enumerate(active_members_with_appointments):
                st.write(f"**{member_name}** ({active_member_appointments[idx]})")
                display_metrics(member_name)

    if active_members_without_appointments:
        with st.expander("### Backbenchers"):
            for idx, member_name in enumerate(active_members_without_appointments):
                st.write(f"**{member_name}**")
                display_metrics(member_name)

    if len(filter_former_members(select_constituency)) > 0:
        with st.expander("### Former Members"):
            st.warning(
                f"The information below reflects information from sittings on {EARLIEST_SITTING} and after."
            )
            former_members = filter_former_members(select_constituency)["member_name"]
            for member_name in former_members:
                if member_name in aggregated_by_member_display["member_name"].values:
                    position_dates = all_member_positions[
                        (all_member_positions["member_name"] == member_name)
                        & (
                            all_member_positions["member_position"]
                            == select_constituency
                        )
                    ][["effective_from_date", "effective_to_date"]]
                    earliest_date = position_dates["effective_from_date"].min()
                    latest_date = position_dates["effective_to_date"].max()
                    st.write(f"**{member_name}** ({earliest_date} to {latest_date})")
                    display_metrics(member_name)
