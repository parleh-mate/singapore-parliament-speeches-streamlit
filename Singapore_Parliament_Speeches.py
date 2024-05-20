# streamlit_app.py

import streamlit as st
from millify import millify
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

### BACKEND

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)
project_id = 'singapore-parliament-speeches'

@st.cache_data(ttl=6000)
def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows

def get_dataset_overview():
    query = f"""
    select min(date) as earliest_date, max(date) as latest_date, count(*) as count_sittings
    from `{project_id}.prod_fact.fact_sittings`
    """
    return run_query(query)[0]

def get_member_counts(latest_date):
    query = f"""
    select
        countif(latest_sitting = '{latest_date}') as count_current_members,
        count(*) as count_members
    from `{project_id}.prod_dim.dim_members`
    where member_name != ''
    """
    return run_query(query)[0]

def get_speech_counts():
    query = f"""
    select
        countif(is_primary_question) as count_primary_questions,
        count(distinct topic_id) as count_topics,
        count(*) as count_speeches
    from `{project_id}.prod_mart.mart_speeches`

    """
    return run_query(query)[0]

def get_bill_counts():
    query = f"""
    select count(*) as count_bills from `{project_id}.prod_mart.mart_bills`
    """
    return run_query(query)[0]

# Fetch data
min_max_sittings = get_dataset_overview()
earliest_date = min_max_sittings['earliest_date'].strftime('%Y-%m-%d')
latest_date = min_max_sittings['latest_date'].strftime('%Y-%m-%d')
count_members = get_member_counts(latest_date)
count_speeches = get_speech_counts()
count_bills = get_bill_counts()

### FRONTEND
st.title('Singapore Parliament Speeches')
st.markdown("This webapp is built to help Singaporeans understand the legislative outputs of their elected representatives.")
st.warning("""
           Please note that this is an entirely independent effort, and this initiative is by no means affiliated with the Singapore Parliament nor Singapore Government. 

           While best efforts are made to ensure the information is accurate, there may be inevitable parsing errors. Please use the information here with caution and check the underlying data.
           """)
st.subheader("Dataset overview")
st.info("Parliament typically takes 2 weeks to put the hansard (record) for sittings out. When new information is available, it will be displayed here.")
st.write(f"The earliest sitting in this dataset is _**{earliest_date}**_, and the latest sitting available in this dataset is _**{latest_date}**_. There is information from _**{min_max_sittings['count_sittings']}**_ sittings in this dataset.")
col1, col2, col3 = st.columns(3, gap="medium")
with col1:
    st.metric('# Current Members', count_members['count_current_members'])
    st.metric('# Members (Past & Present)', count_members['count_members'])
with col2:
    st.metric('# Speeches', millify(count_speeches['count_speeches'], precision=1))
    st.metric('# Topics', millify(count_speeches['count_topics'], precision=1))
with col3:
    st.metric('# Bills', millify(count_bills['count_bills'], precision=1))
    st.metric('# Primary Questions', millify(count_speeches['count_primary_questions'], precision=1))
st.divider()
st.markdown("""
            Want to learn more? See source code:
            * Data pipeline: [singapore-parliament-speeches](https://github.com/jeremychia/singapore-parliament-speeches) (Github).
            * Data modelling with dbt: [singapore-parliament-speeches-dbt](https://github.com/jeremychia/singapore-parliament-speeches-dbt) (Github).
            * Streamlit app (_this_): [singapore-parliament-speeches-streamlit](https://github.com/jeremychia/singapore-parliament-speeches-streamlit) (Github).
            * Data visualisation: [Looker Studio Dashboard](https://lookerstudio.google.com/u/1/reporting/e41e239f-a88a-45b9-b133-5c91bb1f3f13/page/p_jniba4ngfd).
            """)
