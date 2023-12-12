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


import textwrap

from streamlit_extras.row import row

from model.model import Rule
from pages.components.creators.advanced_rule_creator import advanced_creator
from pages.components.authentication_service import AuthenticationService
from pages.components.sidebar.sidebar_state_component import SidebarStateComponent
from pages.components.creators.simple_rule_creator import simple_creator
from pages.components.creators.free_form_rule_creator import free_form_creator
from pages.components.labeling.timeseries_rule_list import TimeseriesRuleList
import streamlit as st
from util.session_constants import AVAILABLE_LABELS, CURRENT_PAGE, LABELING_RUN_DATAFRAME, SELECTED_LABELING_TASK, \
    SELECTED_RULE, SELECTED_RULE_CREATOR, SELECTED_RULESET
import services.persistence_service as db
from streamlit_extras.switch_page_button import switch_page
from util.string_convenience import make_code_label

st.session_state[CURRENT_PAGE] = 'Rule_Creator'

auth = AuthenticationService()
auth.authenticate()
auth.showSidebar()

ssc = SidebarStateComponent()
ssc.show()
st.sidebar.divider()


def store_rc():
    db.cache(st.session_state.rc_type, SELECTED_RULE_CREATOR)


db.clear_cache(LABELING_RUN_DATAFRAME)

# st.header('Rule Creator')
st.markdown(
    '<div style="display: flex; justify-content: space-between"><h2>Rule Creator</h2><h2 style="color: #2B66C2">' + db.load_cache(
        SELECTED_RULESET).name + ' (' + db.load_cache(SELECTED_LABELING_TASK).name + ')</h2></div>',
    unsafe_allow_html=True)
rc = db.load_cache(SELECTED_RULE_CREATOR)

with st.expander('Change rule creator'):
    rc_types = ['Simple', 'Advanced', 'Free Form']
    creator = st.selectbox(
        'Select type',
        options=rc_types,
        index=rc_types.index(rc) if rc is not None else 0,
        on_change=store_rc,
        key='rc_type'
    )

time_series_data = db.load_time_series_data()
if time_series_data is None:
    st.write('No time series data available')
    st.stop()

edit_rule = db.load_cache(SELECTED_RULE)
error = True

if edit_rule is not None:
    st.subheader('Edit Rule')
    edit_rule.rule = textwrap.dedent(str(edit_rule.rule))
else:
    st.subheader('New Rule')

rule_name = st.text_input(
    "Rule name", value=edit_rule.name if edit_rule else '')

l1_set, l2_set, l3_set = [], [], []

if creator == 'Simple':
    (rule, label_set), error, free_form = simple_creator(
        time_series_data), False, False
elif creator == 'Advanced':
    (rule, label_set, error), free_form = advanced_creator(
        time_series_data), False
elif creator == 'Free Form':
    (rule, label_set), error, free_form = free_form_creator(
        time_series_data), False, True
    # st.write('Free Form')

if l1_set is not None:
    rule_list = TimeseriesRuleList(
        rule, label_set, edit_rule=edit_rule, free_form=free_form)
    rule_list.show()

if creator != 'Simple':
    c1, c2 = st.columns(2)
    with c1:
        with st.expander('Available features'):
            st.write(list(time_series_data.feature_matrix.columns))
    with c2:
        with st.expander('Available labels'):
            st.markdown(
                ':warning: :red[**Note:**] the abstain label shows up last in the list but is actually referenced by index -1')
            st.write([make_code_label(l) for l in db.load_cache(AVAILABLE_LABELS)])

save_row = row(1)
if not error:
    c1, c2, c3 = st.columns(3)
    # save_rule = c1.button('Save rule')
    save_rule = False
    save_rule_exit = save_row.button('Save rule', use_container_width=True)

    rule = Rule(id=(edit_rule.id if edit_rule else None),
                rule=rule,
                name=rule_name,
                ruleset_id=db.load_cache(SELECTED_RULESET).id,
                l1=(rule_list.l1 if not free_form else -2),
                l2=(rule_list.l2 if not free_form else -2))

    if save_rule or save_rule_exit:
        if edit_rule:
            db.update(rule)
            db.clear_cache(SELECTED_RULE)
        else:
            db.save(rule)

    if save_rule_exit:
        switch_page('Ruleset_Creator')
