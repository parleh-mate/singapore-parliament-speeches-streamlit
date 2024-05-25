from typing import List, Tuple, Callable
import pandas as pd


def parse_appointments(appointments: List[str]) -> str:
    """
    Parses a list of appointment strings and returns them in a formatted string.

    Parameters:
    appointments (List[str]): A list of appointment strings.

    Returns:
    str: A formatted string of appointments. If there are no appointments,
         returns an empty string. If there is one appointment, returns that
         appointment. If there are multiple appointments, returns them in a
         comma-separated format with 'and' before the last appointment.
    """
    appointments = sorted(appointments)
    count_appointments = len(appointments)

    if count_appointments == 0:
        return ""
    elif count_appointments == 1:
        return appointments[0]
    else:
        return f"{', '.join(appointments[:-1])} and {appointments[-1]}"


def categorise_active_members_with_appointments(
    active_members: List[str], current_member_appointments: pd.DataFrame
) -> Tuple[List[str], List[str], List[str]]:
    """
    Categorizes active members into those with and without appointments.

    Parameters:
    active_members (List[str]): A list of active member names.
    current_member_appointments (pd.DataFrame): A DataFrame containing member appointments.
        It should have at least two columns: 'member_name' and 'member_position'.

    Returns:
    Tuple[List[str], List[str], List[str]]:
        - List of active members with appointments.
        - List of parsed appointment strings corresponding to the active members with appointments.
        - List of active members without appointments.
    """
    active_members_with_appointments = []
    active_member_appointments = []
    active_members_without_appointments = []

    for member in active_members:
        appointments = current_member_appointments[
            current_member_appointments["member_name"] == member
        ]["member_position"]

        if appointments.empty:
            active_members_without_appointments.append(member)
        else:
            active_members_with_appointments.append(member)
            active_member_appointments.append(parse_appointments(appointments))

    return (
        active_members_with_appointments,
        active_member_appointments,
        active_members_without_appointments,
    )


def aggregate_member_metrics(
    all_members_speech_summary: pd.DataFrame, calculate_readability: Callable
) -> pd.DataFrame:
    """
    Aggregates speech summary data by member and calculates additional metrics.

    Parameters:
    - all_members_speech_summary (pd.DataFrame): DataFrame containing the speech summary data for all members.
    - calculate_readability (Callable): Function to calculate readability for each member's data.

    Returns:
    - pd.DataFrame: DataFrame with aggregated data and calculated metrics for each member.
    """
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

    # Aggregate by member
    agg_by_member_dict = {col: "sum" for col in column_names}
    aggregated_by_member = (
        all_members_speech_summary.groupby("member_name")
        .agg(agg_by_member_dict)
        .reset_index()
    )
    aggregated_by_member.columns = ["member_name"] + column_names

    # Calculate additional metrics
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

    # Apply readability calculation
    aggregated_by_member["readability"] = aggregated_by_member.apply(
        calculate_readability, axis=1
    )

    # Filter out rows where count_sittings_attended is zero
    aggregated_by_member = aggregated_by_member[
        aggregated_by_member["count_sittings_attended"] != 0
    ]

    return aggregated_by_member
