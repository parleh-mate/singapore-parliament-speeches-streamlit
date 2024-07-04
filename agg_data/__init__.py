import streamlit as st
from utils import project_id, query_to_dataframe


def get_member_list():
    query = f"""
    select
        member_name,
        member_birth_year,
        member_image_link,
        trim(latest_member_constituency) as constituency,
        party,
        earliest_sitting,
        latest_sitting,
        count_sittings_present,
        count_sittings_total,
        latest_sitting = max(latest_sitting) over() as is_active
    from `{project_id}.prod_dim.dim_members`
    where member_name != '' and member_name is not null
    """
    return query_to_dataframe(query)


def get_member_positions():
    query = f"""
    select * from `{project_id}.prod_fact.fact_member_positions`
    """
    return query_to_dataframe(query)


def get_all_member_speeches():
    query = f"""
      select
          parliament,
          year,
          month,
          member_name,
          member_party,
          member_constituency,

          count_sittings_total,
          count_sittings_present as count_sittings_attended,
          count_sittings_spoken,
          count_topics,
          count_pri_questions,
          count_speeches,

          count_words,
          count_sentences,
          count_syllables
      from `{project_id}.prod_agg.agg_speech_metrics_by_member`
    """
    return query_to_dataframe(query)


def primary_question_topics():
    query = f"""
        select member_name, ministry_addressed, count(*) as count_pri_questions
        from `{project_id}.prod_agg.agg_pri_questions_topics_by_member`
        group by all
    """
    return query_to_dataframe(query)

def get_speech_sum():
    query = f"""
        select *
        from `{project_id}.test.sum`
    """
    return query_to_dataframe(query)

