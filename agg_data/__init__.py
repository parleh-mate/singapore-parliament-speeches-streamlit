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
    with speeches_summary as (
        select
            member_name,
            extract(year from date) as year,
            count(distinct date) as count_sittings_spoken,
            count(distinct topic_id) as count_topics,
            count(*) as count_speeches,
            sum(count_speeches_words) as count_words,
            countif(is_primary_question) as count_pri_questions,
            sum(count_speeches_sentences) as count_sentences,
            sum(count_speeches_syllables) as count_syllables
        from `{project_id}.prod_mart.mart_speeches`
        where member_name != '' and not lower(member_name) like any ('%deputy%', '%speaker%', '%chairman%')
        group by all
    ),
    attendance_summary as (
        select
            member_name,
            extract(year from date) as year,
            countif(is_present) as count_sittings_attended
        from `{project_id}.prod_fact.fact_attendance`
        group by all
    )
    select
        s.member_name,
        s.year,
        a.count_sittings_attended,
        s.count_sittings_spoken,
        s.count_topics,
        s.count_speeches,
        s.count_words,
        s.count_pri_questions,
        s.count_syllables,
        s.count_sentences
    from speeches_summary as s
    left join attendance_summary as a on s.member_name = a.member_name and s.year = a.year
    """
    return query_to_dataframe(query)


def primary_question_topics():
    query = f"""
        select member_name, ministry_addressed, count(*) as count_pri_questions
        from `{project_id}.prod_mart.mart_speeches`
        where
            is_primary_question = true and ministry_addressed is not null and member_name != ''
        group by all
    """
    return query_to_dataframe(query)
