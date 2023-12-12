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

import ast

import streamlit as st

import services.persistence_service as db
from model import time_series_data as tsd
from model.model import LabelingTask, RuleSet
from services.dataprovider import DataProvider
from util.session_constants import LABELING_RUN_DATAFRAME, SELECTED_LABELING_TASK, SELECTED_RULESET, AVAILABLE_LABELS, \
    LABELING_STEP_LIST, CURRENT_LABELING_STEP, CURRENT_LABELING_STEP_RESULTS


def change_lt():
    if st.session_state['ssc_slt']:
        prev_lt = db.load_cache(SELECTED_LABELING_TASK)
        new_lt = st.session_state.ssc_slt

        db.cache(st.session_state.ssc_slt, SELECTED_LABELING_TASK)

        if prev_lt is not None:
            if prev_lt.name != new_lt.name:
                # st.write('Labeling task changed.')
                db.clear_cache(LABELING_RUN_DATAFRAME)
                db.clear_cache(LABELING_STEP_LIST)
                db.clear_cache(CURRENT_LABELING_STEP)
                db.clear_cache(CURRENT_LABELING_STEP_RESULTS)

                dp = DataProvider.fromlabelingtask(new_lt)

                new_tsd = tsd.TimeSeriesData()
                new_tsd = dp.load_all(new_tsd)

                db.cache_time_series_data(new_tsd)
                # st.write('New tsd cached')
        else:
            dp = DataProvider.fromlabelingtask(new_lt)

            new_tsd = tsd.TimeSeriesData()
            new_tsd = dp.load_all(new_tsd)

            db.cache_time_series_data(new_tsd)
            # st.write('New tsd cached')


def change_rs():
    if st.session_state['ssc_srs']:
        db.cache(st.session_state.ssc_srs, SELECTED_RULESET)


class SidebarStateComponent:
    def __init__(self) -> None:
        self.labeling_tasks = None
        self.rulesets = None

    # selects the right index from the list of labeling tasks if it exists
    # or returns the latest task if not.
    def get_index(self, entity, constant_string):
        if constant_string in st.session_state:
            index = next((i for i, item in enumerate(entity) if item.id ==
                          st.session_state[constant_string].id), len(entity) - 1)
        else:
            index = len(entity) - 1
        return index

    def show(self):
        self.labeling_tasks = db.load(LabelingTask)

        index_lt = self.get_index(self.labeling_tasks, SELECTED_LABELING_TASK)

        if len(self.labeling_tasks) > 0:
            selected_lt = st.sidebar.selectbox(
                'Select a labeling task',
                options=self.labeling_tasks,
                format_func=lambda x: x.name,
                index=index_lt,
                key='ssc_slt',
                on_change=change_lt,
            )

            self.update_rulesets(selected_lt)

            if len(self.rulesets) > 0:
                index_rs = self.get_index(self.rulesets, SELECTED_RULESET)

                selected_rs = st.sidebar.selectbox(
                    'Select a ruleset',
                    options=self.rulesets,
                    format_func=lambda x: x.name,
                    index=index_rs,
                    key='ssc_srs',
                    on_change=change_rs,
                )
            else:
                st.sidebar.selectbox('Select a ruleset', options=[])
                db.clear_cache(SELECTED_RULESET)

            labels = ast.literal_eval(selected_lt.labels)
            labels.append('ABSTAIN')

            db.cache(labels, AVAILABLE_LABELS)
        else:
            # Option when there are no labeling tasks yet
            st.sidebar.selectbox('Select a labeling task', options=[])
            st.sidebar.selectbox('Select a ruleset', options=[])

    def update_rulesets(self, lt):
        ruleset_filter = lt.id == RuleSet.labeling_task_id
        self.rulesets = db.load(RuleSet, filter=ruleset_filter)
