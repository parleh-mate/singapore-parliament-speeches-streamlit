import streamlit as st
from agg_data import get_member_list

# BACKEND

members_df = get_member_list()
constituency_names = sorted(
    members_df[members_df["constituency"].notna()]["constituency"].unique()
)

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
                    st.image(member_image_link)
                    st.markdown(f"{member_name}")
                else:
                    st.empty()

    # Display the first 5 active members
    display_members(active_members, start_index=0)

    # Display the next 5 active members if they exist
    if len(active_members) > 5:
        display_members(active_members, start_index=5)

    st.dataframe(
        members_df[
            (members_df["constituency"] == select_constituency)
            & (members_df["is_active"] == True)
        ]
    )

    st.subheader("Former Members")

    st.dataframe(
        members_df[
            (members_df["constituency"] == select_constituency)
            & (members_df["is_active"] == False)
        ]
    )
