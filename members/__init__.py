from typing import List, Tuple
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
