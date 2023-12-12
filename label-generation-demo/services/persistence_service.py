#  Copyright (c) 2023. Dynatrace LCC. All Rights Reserved.

#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied. See the License for the specific language governing
#  permissions and limitations under the License.

import json

import streamlit as st
# from sqlalchemy.orm import Session
from sqlalchemy.sql import true

import model.model as model
import model.time_series_data as tsd
from services.connectors import database_connector as c
from util.session_constants import PERSISTENCE_TIME_SERIES_DATA, PERSISTENCE_RULESET

# Time Series Data
# connection = c.connect_db()
Session = c.get_session()


# @b.benchmark
# @l.log
def cache_time_series_data(tsd):
    st.session_state[PERSISTENCE_TIME_SERIES_DATA] = tsd


# @b.benchmark
# @l.log
def load_time_series_data():
    if PERSISTENCE_TIME_SERIES_DATA not in st.session_state:
        return tsd.TimeSeriesData()
    return st.session_state[PERSISTENCE_TIME_SERIES_DATA]


# @b.benchmark
# @l.log
def append_rule_to_ruleset(rule):
    if PERSISTENCE_RULESET not in st.session_state:
        st.session_state[PERSISTENCE_RULESET] = []
    st.session_state[PERSISTENCE_RULESET].append(rule)


# @b.benchmark
# @l.log
def update_ruleset(rule):
    if PERSISTENCE_RULESET not in st.session_state:
        st.session_state[PERSISTENCE_RULESET] = []
    rs = st.session_state[PERSISTENCE_RULESET]
    for r in rs:
        if r.id == rule.id:
            r.rule = rule.rule
            r.l1 = rule.l1
            r.l2 = rule.l2
    st.session_state[PERSISTENCE_RULESET] = rs


# @b.benchmark
# @l.log
def save(entity):
    with Session() as session:
        if type(entity) is list:
            session.add_all(entity)
        else:
            session.add(entity)
        session.commit()
        st.toast('{} saved successfully'.format(
            type(entity).__name__), icon='✅')


# @b.benchmark
# @l.log
def update(entity):
    with Session() as session:
        session.merge(entity)
        session.commit()
        st.toast('{} updated successfully'.format(
            type(entity).__name__), icon='✅')


# @b.benchmark
# @l.log
def load(model, filter=true()):
    with Session() as session:
        result = session.query(model).filter(filter).all()
        if result is None:
            return []
        return result


# @b.benchmark
# @l.log
def delete(entity):
    with Session() as session:
        session.delete(entity)
        session.commit()
        st.toast('{} deleted successfully'.format(
            type(entity).__name__), icon='✅')


# @b.benchmark
# @l.log
def cache(entity, key):
    st.session_state[key] = entity


# @b.benchmark
# @l.log
def load_cache(key):
    if key not in st.session_state:
        return None
    return st.session_state[key]


# @b.benchmark
# @l.log
def clear_cache(key):
    if key in st.session_state:
        del st.session_state[key]


# ID
# LabelingTask.id
# Ruleset.id
# Result
# @b.benchmark
# @l.log
def save_labeling_result(labeling_result):
    with Session() as session:
        # Insert new entry into database but remove rules, results and properties so that
        # the insertion into the database works.

        tmpLr = model.LabelingResult(
            labeling_task_id=labeling_result.labeling_task_id, ruleset_id=labeling_result.ruleset_id,
            user_id=labeling_result.user_id, date=labeling_result.date)

        session.add(tmpLr)
        session.flush()

        # Retrieve ID of new entry from context
        id = tmpLr.id

        # Update datebase entry with properties and results
        session.execute("UPDATE labeling_result SET properties = '{}' WHERE id = '{}'"
                        .format(json.dumps(labeling_result.properties),
                                id))

        # Update datebase entry with properties and results
        session.execute("UPDATE labeling_result SET results = '{}' WHERE id = '{}'"
        .format(
            json.dumps(json.loads(
                labeling_result.results)),
            id))

        # Serialize rules before insertion
        # serialized_rules = {rule.id: {'name': rule.name, 'rule': rule.rule, 'l1': rule.l1, 'l2': rule.l2}
        #                     for rule in labeling_result.rules}

        # Update database entry with rules
        session.execute("UPDATE labeling_result SET rules = '{}' WHERE id = '{}'"
                        .format(json.dumps(labeling_result.rules),
                                id))

        # Update database entry with scores
        session.execute("UPDATE labeling_result SET scores = '{}' WHERE id = '{}'"
                        .format(json.dumps(labeling_result.scores),
                                id))

        st.toast('LR saved successfully', icon='✅')
        session.commit()
