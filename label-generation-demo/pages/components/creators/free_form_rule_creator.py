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
from code_editor import code_editor

import services.persistence_service as db
import util.session_constants as const
from services.parser import rule_parser as rp
from util.string_convenience import make_code_label


def free_form_creator(time_series_data):
    fm = time_series_data.feature_matrix

    btn_settings_editor_btns = [{
        "name": "Refresh",
        "feather": "RefreshCw",
        "primary": True,
        "hasText": True,
        "showWithIcon": True,
        "commands": ["submit"],
        "style": {"bottom": "0rem", "right": "0.4rem"}
    }]

    edit_rule = db.load_cache(const.SELECTED_RULE)

    r = code_editor(str(
        edit_rule.rule) if edit_rule else '', lang="python", height=[
        5, 15], buttons=btn_settings_editor_btns, key="rule_editor")
    # st.write(r)
    labels = db.load_cache(const.AVAILABLE_LABELS)

    label_sets = [[]
                  for i in range(len(labels))]
    i = -1
    while i < len(labels) - 1:
        label = make_code_label(labels[i]) + ' = ' + str(i)
        exec(label, globals())
        i += 1
    # st.write(l)

    if r['type'] == "submit":
        if r['text'] == '':
            return None, None

        parser = rp.RuleParser(feature_matrix_name='x', level=1)

        parsed_rule = parser.parse(r['text'])

        func = "def func(x):\n" + parsed_rule

        # This is needed for the function to be available in the global scope
        #  upon calling exec from within a function
        exec(func, globals())
        lf = globals()['func']

        for i in range(len(fm)):
            res = lf(fm.iloc[i, :])
            if res is not None:
                label_sets[res].append(fm.iloc[i, :])

        label_df = [pd.DataFrame(data=l) for l in label_sets]

        p2 = rp.RuleParser(level=1)
        rule = p2.parse(r['text'])
        return rule, label_df
    return None, None
