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
from streamlit_extras.row import row
from streamlit_extras.switch_page_button import switch_page
from streamlit_tags import st_tags

# import util.database_connector as conn
import services.persistence_service as db
from model.model import GoldLabel, LabelingResult, LabelingTask, Rule, RuleSet
from pages.components.authentication_service import AuthenticationService
from pages.components.sidebar.sidebar_state_component import SidebarStateComponent
from util.session_constants import AVAILABLE_LABELS, CURRENT_LABELING_STEP, CURRENT_LABELING_STEP_RESULTS, CURRENT_PAGE, \
    LABELING_RUN_DATAFRAME, LABELING_STEP_LIST, SELECTED_LABELING_TASK, SELECTED_RULESET

st.session_state[CURRENT_PAGE] = '1_Labeling_Task'

auth = AuthenticationService()
auth.authenticate()
auth.showSidebar()

ssc = SidebarStateComponent()
ssc.show()
st.sidebar.divider()

time_series_data = db.load_time_series_data()
# st.write(time_series_data)

db.clear_cache(LABELING_RUN_DATAFRAME)
db.clear_cache(LABELING_STEP_LIST)
db.clear_cache(CURRENT_LABELING_STEP)
db.clear_cache(CURRENT_LABELING_STEP_RESULTS)

labeling_tasks = db.load(LabelingTask)
selected = db.load_cache(SELECTED_LABELING_TASK)

st.markdown(
    '<div style="display: flex; justify-content: space-between"><h2>Labeling Task</h2><h2 style="color: #2B66C2">' + (
        selected.name if selected is not None else 'None') + '</h2></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(
    ['Tasks',
     'Options'])

with tab1:
    if len(labeling_tasks) == 0 or selected is None:
        st.write('No labeling tasks available')
        # st.stop()
    else:
        # st.subheader(selected.name)
        # data_row = row([1, 7], vertical_align='center')
        # data_row.markdown('**Data Location:**')
        # data_row.code('stored local', language='text')

        ts_row = row([2, 3, 2, 3], vertical_align='center')
        ts_row.markdown('**Time Series:**')
        ts_row.code(str(len(time_series_data.feature_matrix)), language='text')
        ts_row.markdown('**Features:**')
        ts_row.code(str(len(time_series_data.feature_matrix.columns)), language='text')

        gl_row = row([2, 3, 2, 3], vertical_align='center')
        gl_row.markdown('**Gold Labels:**')
        filter_gl = GoldLabel.labeling_task_id == st.session_state[
            SELECTED_LABELING_TASK].id
        gls = db.load(GoldLabel, filter=filter_gl)
        gl_row.code(str(len(gls)), language='text')

        # get total number of labeling results for all rulesets
        filter_lr_tid = LabelingResult.labeling_task_id == st.session_state[SELECTED_LABELING_TASK].id
        results = db.load(LabelingResult, filter=filter_lr_tid)
        gl_row.markdown('**Available labeling results:** ')
        gl_row.code(str(len(results)), language='text')

        st.markdown('**Labels:**')

        labels = ast.literal_eval(selected.labels)
        labels.append('ABSTAIN')
        label_row = row(len(labels), vertical_align='bottom')
        for i, l in enumerate(labels):
            label_row.markdown(
                '<div style="border-radius: 0.25rem; background: #F8F9FB"; display: flex;><div style="display: flex; justify-content: center; padding: 0.25rem; margin-bottom: 1rem;">' + l + '</div></div>',
                unsafe_allow_html=True)

        filter = st.session_state[SELECTED_LABELING_TASK].id == RuleSet.labeling_task_id
        rulesets = db.load(RuleSet, filter=filter)

        st.markdown('**Rulesets:**')
        for rs in rulesets:
            tmp = '**' + rs.name + '** by **' + rs.user_id + '**'
            with st.expander(tmp):
                # get number of rules per ruleset
                filter_rs = Rule.ruleset_id == rs.id
                rules = db.load(Rule, filter=filter_rs)
                st.write('Number of rules: ' + str(len(rules)))
                # get number of labeling results per ruleset
                filter_lr = LabelingResult.ruleset_id == rs.id
                results = db.load(LabelingResult, filter=filter_lr)
                st.write('Number of labeling results: ' + str(len(results)))
                # button to go directly to relevant ruleset
                go_to_ruleset_button = st.button('Go to ruleset', key='gotors' + rs.id)
                if go_to_ruleset_button:
                    db.cache(rs, SELECTED_RULESET)
                    switch_page('Ruleset_Creator')



        st.divider()
        button_row = row(2, vertical_align='center')
        create_ruleset_button = button_row.button('Create ruleset', use_container_width=True)
        if create_ruleset_button:
            switch_page('Ruleset_Creator')

        disabled = len(results) == 0

        go_to_labeling_results_button = button_row.button(
            'Go to labeling results', disabled=disabled, use_container_width=True)
        if go_to_labeling_results_button:
            switch_page('Labeling_Results')

with tab2:
    # pass
    if selected is not None:
        # with st.expander('Data Loader'):
        #     if selected is not None:
        #         try:
        #             with st.form('data-loader'):
        #                 # st.subheader('Data Loader')
        #                 existing_count = len(time_series_data.data_dict)
        #                 max = len(time_series_data.feature_matrix.index.values)
        #                 st.write(str(existing_count) + ' time series of ' + str(
        #                     max) + ' already fetched.')
        #                 data_slider = st.slider(
        #                     label='How many (more) should be fetched?',
        #                     min_value=0,
        #                     max_value=max - existing_count,
        #                     value=5 if max - existing_count > 5 else max - existing_count,
        #                     key='lt_ds',
        #                 )
        #                 load_button = st.form_submit_button(
        #                     'Load Data',
        #                     # on_click=(
        #                     #     lambda slt, ds: db.cache_time_series_data(
        #                     #         dp.DataProvider.fromlabelingtasktoloadmore(slt)
        #                     #             .load_time_series(slt, ds))
        #                     # ),
        #                     # args=(selected, data_slider)
        #                 )
        #
        #
        #         except Exception as e:
        #             st.error(e)
        #             st.error(
        #                 'Could not load data. There might be an issue with the path you provided.')
        #             # st.stop()

        with st.expander('Import Gold Labels'):
            st.write(
                'Load gold labels from feature matrix if they are available and if no gold label has been set manually.')
            tmp = db.load(GoldLabel, filter=GoldLabel.labeling_task_id ==
                                            st.session_state[SELECTED_LABELING_TASK].id)
            # st.write(tmp)
            if len(tmp) > 0:
                st.info(
                    'There already exist (manually) set gold labels for this labeling task.')
                # st.stop()
            else:
                load_button = st.button('Import Gold Labels')
                if load_button:
                    fm = db.load_time_series_data().feature_matrix
                    if 'label' in fm:
                        fm_labels = list(fm.loc[:, 'label'].unique())
                        # check if there are any fm_labels in available labels
                        available_labels = db.load_cache(AVAILABLE_LABELS)
                        if len(set(fm_labels).intersection(available_labels)) > 0:
                            st.write('Matching labels found')
                            # st.write(fm.loc[:, 'label'])
                            st.write(
                                'Adding labels to the database... This might take some time. Please do not navigate away from the page while importing labels.')
                            gll = []
                            for key, label in fm.loc[:, 'label'].items():
                                if label in available_labels:
                                    gl = GoldLabel(
                                        label=available_labels.index(label),
                                        labeling_task_id=st.session_state[SELECTED_LABELING_TASK].id,
                                        time_series_key=key,
                                        user_id=db.load_cache('username'))
                                    gll.append(gl)
                            db.save(gll)
                            st.success('Labels successfully added.')
                        else:
                            st.write(
                                'No matching labels. Cannot set any gold labels.')
                            # st.stop()

        deletable = False
        if deletable:
            with st.expander('Delete labeling task'):
                st.write(
                    'If you delete a labeling task, all rulesets and rules associated with it will be deleted as well.')
                delete_button = st.button('Delete labeling task',
                                          on_click=lambda: db.delete(st.session_state[SELECTED_LABELING_TASK]))
                # if delete_button:
                # db.delete(st.session_state[SELECTED_LABELING_TASK])
                # db.clear_cache(SELECTED_LABELING_TASK)
                # st.experimental_rerun()

    with st.expander('Create new labeling task'):
        # t1, t2 = st.tabs(['Create new labeling task', 'Import Gold Labels'])

        # with st.form('labeling', clear_on_submit=True):
        st.subheader('Create new labeling task')
        name = st.text_input('Name', value='', key='nlt_name')
        data_url = st.text_input('Data URL', value='', key='nlt_du')
        time_series_location = st.text_input('Path where time series are located', value='', key='nlt_dl')
        labels = st_tags(
            label='',
            text='Press enter to add label',
            key='nlt_tags',
            value=[],
        )


        def create_task(name, data_url, labels):
            task = LabelingTask(name=name, data_url=data_url, time_series_path=time_series_location,
                                labels=str(labels))
            db.save(task)
            db.clear_cache(SELECTED_RULESET)
            db.cache(task, SELECTED_LABELING_TASK)


        label_button = st.button(
            'Save labeling task', on_click=create_task, args=(name, data_url, labels)
        )
