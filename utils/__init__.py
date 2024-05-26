import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

EARLIEST_SITTING = "2012-09-10"

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
        return float('nan')

    readability = (
        206.835
        - (1.015 * total_words / total_sentences)
        - (84.6 * total_syllables / total_words)
    )
    return readability

def process_percentage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes DataFrame columns that contain the '%' symbol in their names.
    For these columns, rounds the values to 1 decimal place and adds a '%' suffix.

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

    # Identify columns with '%' in their names
    percentage_columns = [col for col in df.columns if '%' in col]

    for col in percentage_columns:
        df[col] = df[col].apply(lambda x: format_percentage(x))

    return df