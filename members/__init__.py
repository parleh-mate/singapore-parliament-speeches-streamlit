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
    all_members_speech_summary: pd.DataFrame,
    calculate_readability: Callable,
    group_by_fields: List[str]
) -> pd.DataFrame:
    """
    Aggregates speech summary data by specified group-by fields and calculates additional metrics.

    Parameters:
    - all_members_speech_summary (pd.DataFrame): DataFrame containing the speech summary data for all members.
    - calculate_readability (Callable): Function to calculate readability for each group of data.
    - group_by_fields (List[str]): List of fields to group by.

    Returns:
    - pd.DataFrame: DataFrame with aggregated data and calculated metrics for each group.
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

    # Aggregate by specified fields
    agg_by_fields_dict = {col: "sum" for col in column_names}
    aggregated = (
        all_members_speech_summary.groupby(group_by_fields)
        .agg(agg_by_fields_dict)
        .reset_index()
    )

    # Calculate additional metrics
    aggregated["participation_rate"] = (
        aggregated["count_sittings_spoken"]
        / aggregated["count_sittings_attended"]
        * 100
    )
    aggregated["topics_per_sitting"] = (
        aggregated["count_topics"]
        / aggregated["count_sittings_spoken"]
    )
    aggregated["questions_per_sitting"] = (
        aggregated["count_pri_questions"]
        / aggregated["count_sittings_spoken"]
    )
    aggregated["words_per_sitting"] = (
        aggregated["count_words"]
        / aggregated["count_sittings_spoken"]
    )

    # Apply readability calculation
    aggregated["readability"] = aggregated.apply(
        calculate_readability, axis=1
    )

    # Filter out rows where count_sittings_attended is zero
    aggregated = aggregated[
        aggregated["count_sittings_attended"] != 0
    ]

    return aggregated
