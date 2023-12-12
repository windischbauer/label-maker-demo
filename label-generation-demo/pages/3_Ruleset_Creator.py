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


import streamlit as st
import services.persistence_service as db
from model.model import RuleSet, Rule
from streamlit_extras.switch_page_button import switch_page
from pages.components.authentication_service import AuthenticationService
from pages.components.sidebar.sidebar_state_component import SidebarStateComponent
from util.session_constants import AVAILABLE_LABELS, CURRENT_PAGE, LABELING_RUN_DATAFRAME, SELECTED_LABELING_TASK, \
    SELECTED_RULE, SELECTED_RULE_CREATOR, SELECTED_RULESET
from util.string_convenience import display_labels, reduce_string
from streamlit_extras.row import row

st.session_state[CURRENT_PAGE] = '6_Ruleset_Creator'

auth = AuthenticationService()
auth.authenticate()
auth.showSidebar()

ssc = SidebarStateComponent()
ssc.show()
st.sidebar.divider()

# new_set = st.button('New ruleset')

filter = st.session_state[SELECTED_LABELING_TASK].id == RuleSet.labeling_task_id
rulesets = db.load(RuleSet, filter=filter)
db.clear_cache(SELECTED_RULE)
db.clear_cache(LABELING_RUN_DATAFRAME)

# st.header('Ruleset')

st.markdown('<div style="display: flex; justify-content: space-between"><h2>Ruleset</h2><h2 style="color: #2B66C2">' + (
    db.load_cache(SELECTED_RULESET).name if len(rulesets) > 0 else 'None') + ' (' + db.load_cache(
    SELECTED_LABELING_TASK).name + ')</h2></div>', unsafe_allow_html=True)

labels = db.load_cache(AVAILABLE_LABELS)
# st.write('Labels: ' + str(rs.labels))
# st.write('Features: ' + str(rs.features()))

tab1, tab2 = st.tabs(
    ['Ruleset',
     #  'Edit ruleset',
     'Options'])

with tab1:
    if len(rulesets) == 0:
        st.write('No rulesets for this labeling task available. Create one in the options tab.')
        # st.button('Reload rulesets', key='reload_rulesets', on_click=st.experimental_rerun)
    else:
        selected = db.load_cache(SELECTED_RULESET)
        st.markdown('**Rules**')
        filter = Rule.ruleset_id == st.session_state[SELECTED_RULESET].id
        rules = db.load(Rule, filter=filter)

        # st.write(selected)
        if len(rules) == 0:
            st.write('No rules for this ruleset available. Please start by creating one.')
            # st.button('Reload rules', key='reload_rules', on_click=st.experimental_rerun)

        for rule in rules:
            rule_name = rule.name if rule.name else reduce_string(
                str(rule.rule), 25)
            tmp = (':blue[(*)] ' if rule.l1 == -
            2 or rule.l2 == -2 else '') + rule_name
            with st.expander(tmp):
                st.code(rule.rule)
                if (rule.l1 != -2 and rule.l2 != -2):
                    st.markdown('**Label 1:** ' + display_labels(labels[rule.l1]))
                    st.markdown('**Label 2:** ' + display_labels(labels[rule.l2]))
                st.markdown('**Coverage:** ' + ' n/A')
                col1, col2 = st.columns([0.5, 1])
                with col1:
                    edit_button = st.button(
                        'edit rule', key='edit_' + str(rule.id))
                    if edit_button:
                        db.cache(rule, SELECTED_RULE)
                        if rule.l1 == -2 or rule.l2 == -2:
                            db.cache('Free Form', SELECTED_RULE_CREATOR)
                            switch_page('Rule_Creator')
                        else:
                            db.cache('Advanced', SELECTED_RULE_CREATOR)
                            switch_page('Rule_Creator')
                with col2:
                    remove_button = st.button(
                        'remove rule', key='delete_' + str(rule.id))
                    if remove_button:
                        db.delete(rule)
                        st.experimental_rerun()

        st.divider()
        button_row = row(2)
        create_s_rule_button = button_row.button('Create new rule', use_container_width=True)
        if create_s_rule_button:
            switch_page('Rule_Creator')

        goto_labeling_page_button = button_row.button('Run Labeling', use_container_width=True)
        if goto_labeling_page_button:
            switch_page('Labeling')

        # goto_labeling_results_page_button = button_row.button('Labeling Results', use_container_width=True)
        # if goto_labeling_results_page_button:
        #     switch_page('Labeling_Results')

with tab2:
    deletable = False
    if deletable:
        if db.load_cache(SELECTED_RULESET) is not None:
            with st.expander('Delete ruleset'):
                st.write('If you really want to delete the ruleset, click the button below.')
                delete_button = st.button('Delete ruleset',
                                          on_click=lambda: db.delete(st.session_state[SELECTED_RULESET]))

    with st.expander('Create new ruleset'):
        def create_rs(name):
            ruleset = RuleSet(
                name=name,
                labeling_task_id=st.session_state[SELECTED_LABELING_TASK].id,
                user_id=st.session_state['username'])
            db.save(ruleset)
            db.cache(ruleset, SELECTED_RULESET)


        # with st.form('ruleset', clear_on_submit=True):
        st.subheader('Create new ruleset')
        name = st.text_input('Name', key='rc_rsn')
        label_button = st.button('Create ruleset', on_click=create_rs, args=(name,))
