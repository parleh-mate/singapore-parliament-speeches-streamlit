import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
import re

EARLIEST_SITTING = "2012-09-10"

PARTY_COLOURS = {
    "PAP": "#FF9999",  # pastel red
    "PSP": "#FFFF99",  # pastel yellow
    "WP": "#99CCFF",  # pastel blue
    "NMP": "#D3D3D3",  # pastel grey
    "SPP": "#D8BFD8",  # pastel purple
}

PARTY_SHAPES = {
    "PAP": "circle",
    "PSP": "square",
    "WP": "triangle",
    "NMP": "diamond",
    "SPP": "cross",
}

# Create API client.

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)
project_id = "singapore-parliament-speeches"


@st.cache_data(ttl=6000)
def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows


@st.cache_data(ttl=6000)
def query_to_dataframe(query):
    return pd.DataFrame(run_query(query))

def calculate_readability(row):
    total_words = row["count_words"]
    total_sentences = row["count_sentences"]
    total_syllables = row["count_syllables"]

    if total_sentences == 0 or total_words == 0:
        return float("nan")

    readability = (
        206.835
        - (1.015 * total_words / total_sentences)
        - (84.6 * total_syllables / total_words)
    )
    return readability


def process_metric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes DataFrame columns that contain the '%' symbol in their names.
    For these columns, rounds the values to 1 decimal place and adds a '%' suffix.

    Processes DataFrame columns that contain the '#' symbol in their names.
    For these columns, rounds the values to 0 decimal places.

    Parameters:
    - df (pd.DataFrame): The DataFrame to process.

    Returns:
    - pd.DataFrame: The processed DataFrame with percentage columns formatted.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input is not a DataFrame")

    def format_percentage(value):
        if pd.isna(value):
            return value
        return f"{value:.1f}%"

    def format_count(value):
        if pd.isna(value):
            return value
        return round(value)

    # Identify columns with '%' in their names
    percentage_columns = [col for col in df.columns if "%" in col]
    count_columns = [col for col in df.columns if "#" in col]

    for col in percentage_columns:
        df[col] = df[col].apply(lambda x: format_percentage(x))

    for col in count_columns:
        df[col] = df[col].apply(lambda x: format_count(x))

    return df

def tidy_sum_df(df):
    df = df[['date', 'parliament', 'member_name', 
             'member_party', 'member_constituency', 'speech_summary']]

    df = df.rename(columns = {"member_name": "name",
                              "member_party": "party",
                              "member_constituency": "constituency"})
    
    df['date'] = df['date'].apply(lambda x: re.search("\d{4}-\d{2}-\d{2}", x).group())

    return df

def filter_speech_fun(df, var, isin):
    return df[df[var].isin(isin)]
