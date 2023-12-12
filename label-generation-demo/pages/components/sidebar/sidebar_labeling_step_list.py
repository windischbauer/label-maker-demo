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

from util.string_convenience import display_date, display_dict


class SidebarLabelingStepList:
    def __init__(self) -> None:
        self.header = st.sidebar.empty()
        self.list_container = st.sidebar.empty()

    def show(self, labeling_step_list):
        self.header.subheader('Current Labeling Runs')
        if len(labeling_step_list) == 0:
            self.list_container.write('No labeling runs saved yet')
        else:
            self.display(labeling_step_list)

    def update(self, labeling_step_list):
        self.display(labeling_step_list)

    def display(self, labeling_step_list):
        with self.list_container.container():
            c1, c2 = st.columns([1, 20])
            for l in reversed(labeling_step_list):
                c1.markdown('&#8594; ')

                body = 'LR @ ' + display_date(l.date)
                help = '**:green[Run:]** ' + str(l.date) + '   \n' \
                                                           '**:blue[Label Model Properties:]**   \n' + display_dict(
                    l.properties['lm']) + '   \n' \
                       + '**:blue[Surrogate Model Properties:]**   \n' + \
                       display_dict(l.properties['sm'])

                c2.markdown(body=body, help=help)
