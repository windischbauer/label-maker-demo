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


import pandas as pd
import streamlit as st

from services import persistence_service as db
from services.parser import rule_parser as rp
from util.session_constants import SELECTED_RULE


def advanced_creator(time_series_data):
    error = True
    label_sets = [[], []]

    edit_rule = db.load_cache(SELECTED_RULE)
    with st.form('rule gen'):
        if edit_rule is not None:
            st.subheader('Edit Rule')
        else:
            st.subheader('New Rule')

        fm = time_series_data.feature_matrix

        st.write('In the format of: <feature> <comparator> <value> <operator> ...')

        r = st.text_input("Labeling rule", value=str(
            edit_rule.rule) if edit_rule else '')
        st.form_submit_button('refresh')

        parser = rp.RuleParser()

        if r != '':
            parsed_rule = parser.parse(r)
            error = False
            if parsed_rule is None:
                st.write('Invalid rule. This might occur due to a syntax error.')
                error = True
            else:
                try:
                    label_sets[0] = fm.query(parsed_rule)
                    label_sets[1] = pd.concat(
                        [label_sets[0], fm]).drop_duplicates(keep=False)
                    # st.write(parser.features)
                except Exception as e:
                    st.write(
                        'Something went wrong. One or more of the features might not exist.')
                    st.write(e)
                    error = True

    st.subheader(r)
    return r, label_sets, error
