import streamlit as st
import altair as alt

from agg_data import get_member_list, get_all_member_speeches
from members import aggregate_member_metrics
from utils import (
    calculate_readability,
    process_metric_columns,
    EARLIEST_SITTING,
    PARTY_COLOURS,
    PARTY_SHAPES,
)

# BACKEND

members_df = get_member_list()
member_names = sorted(members_df["member_name"].unique())

all_members_speech_summary = get_all_member_speeches()

aggregated_by_member_parliament = aggregate_member_metrics(
    all_members_speech_summary,
    calculate_readability,
    group_by_fields=[
        "member_name",
        "member_party",
        "member_constituency",
        "parliament",
    ],
)

constituency_names = sorted(
    all_members_speech_summary[
        all_members_speech_summary["member_constituency"].notna()
    ]["member_constituency"].unique()
)

# SELECTIONS

parliaments = {"13th Parliament": [13], "14th Parliament": [14], "All": [12, 13, 14]}

select_parliament = st.sidebar.radio(
    label="Which parliament?", options=parliaments.keys(), index=1
)

select_by = st.sidebar.radio(
    label="Find by:", options=["Constituency", "Member"], index=0
)

if select_by == "Constituency":
    select_constituency = st.sidebar.selectbox(
        label="Which constituency are you interested in?",
        options=constituency_names,
        index=None,
        placeholder="Choose constituency",
    )

    if select_constituency:
        selected_members = (
            aggregated_by_member_parliament[
                (
                    aggregated_by_member_parliament["member_constituency"]
                    == select_constituency
                )
                & (
                    aggregated_by_member_parliament["parliament"].isin(
                        parliaments[select_parliament]
                    )
                )
            ]["member_name"]
            .unique()
            .tolist()
        )
    else:
        selected_members = [""]

elif select_by == "Member":
    select_member = st.sidebar.selectbox(
        label="Which member are you interested in?",
        options=member_names,
        index=None,
        placeholder="Choose member name",
    )

    # where the selection is members and not GRCs
    selected_members = [select_member if select_member else ""]

# FRONTEND

st.title("Leaderboard")
st.warning("Under construction.")


tabs = [
    "Participation",
    "Questions Asked",
    "Sitting Contributions",
    "Readability",
]

participation, questions, contributions, readability = st.tabs(tabs)


def display_header(select_by):
    if select_by == "Member":
        if not select_member:
            st.error("Please select a member on the sidebar.")
        if select_member:
            st.subheader(select_member)

    elif select_by == "Constituency":
        if "" in selected_members:
            st.error("Please select a constituency on the sidebar.")
        else:
            st.subheader(select_constituency)


with participation:
    # PROCESSING
    participation_cols = {
        "member_name": "Member Name",
        "participation_rate": "Participation (%)",
        "attendance": "Attendance (%)",
        "count_sittings_spoken": "# Spoken",
        "count_sittings_attended": "# Attended",
        "count_sittings_total": "# Total",
        "member_party": "Party",
        "member_constituency": "Constituency",
    }
    processed = aggregate_member_metrics(
        aggregated_by_member_parliament[
            aggregated_by_member_parliament["parliament"].isin(
                parliaments[select_parliament]
            )
        ],
        calculate_readability,
        group_by_fields=["member_name", "member_party", "member_constituency"],
    )
    processed = processed[participation_cols.keys()]
    processed["# Rank"] = processed["participation_rate"].rank(
        ascending=False, method="min"
    )
    processed.rename(columns=participation_cols, inplace=True)
    to_display = processed.copy()
    to_display = process_metric_columns(to_display)
    to_display.sort_values("# Rank", inplace=True)
    to_display = to_display.style.apply(
        lambda row: [
            "background-color: yellow" if row["Member Name"] in selected_members else ""
            for _ in row
        ],
        axis=1,
    )

    # FRONTEND
    st.header(tabs[0])
    st.warning("Under construction.")

    display_header(select_by)

    if select_by == "Constituency":
        members_md = ""
        for selected_member in selected_members:
            members_md += f"* {selected_member}\n"
        st.markdown(members_md)

    if select_parliament == "All":
        st.warning(
            f"The information below reflects information from sittings on {EARLIEST_SITTING} and after."
        )

    chart = (
        alt.Chart(processed)
        .mark_point()
        .encode(
            alt.X("Attendance (%)").scale(zero=False).axis(alt.Axis(grid=False)),
            alt.Y("Participation (%)").scale(zero=False).axis(alt.Axis(grid=False)),
            color=alt.Color("Party").scale(
                alt.Scale(
                    domain=list(PARTY_COLOURS.keys()),
                    range=list(PARTY_COLOURS.values()),
                )
            ),
            shape=alt.Shape("Party").scale(
                alt.Scale(
                    domain=list(PARTY_SHAPES.keys()), range=list(PARTY_SHAPES.values())
                )
            ),
            tooltip=[
                alt.Tooltip("Member Name"),
                alt.Tooltip("Party"),
                alt.Tooltip("Constituency"),
                alt.Tooltip("Attendance (%)", format=".1f"),
                alt.Tooltip("Participation (%)", format=".1f"),
            ],
        )
        .encode(
            size=alt.condition(
                alt.FieldOneOfPredicate("Member Name", selected_members),
                alt.value(200),  # Increase the size of emphasized points
                alt.value(30),  # Default size for other points
            ),
            opacity=alt.condition(
                alt.FieldOneOfPredicate("Member Name", selected_members),
                alt.value(1),  # Full opacity for emphasized points
                alt.value(0.4),  # Reduced opacity for other points
            ),
            fill=alt.condition(
                alt.FieldOneOfPredicate("Member Name", selected_members),
                alt.ColorValue("green"),
                alt.value("transparent"),
            ),
        )
    )

    st.altair_chart(chart, use_container_width=True)

    st.divider()

    st.subheader("All members")
    st.dataframe(to_display, hide_index=True, use_container_width=False)

with questions:
    st.header(tabs[1])
    display_header(select_by)
    st.warning("Under construction.")

with contributions:
    st.header(tabs[2])
    display_header(select_by)
    st.warning("Under construction.")

with readability:
    st.header(tabs[3])
    display_header(select_by)
    st.warning("Under construction.")
