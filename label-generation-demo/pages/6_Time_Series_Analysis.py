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
from streamlit_extras.row import row
from streamlit_extras.switch_page_button import switch_page

import services.persistence_service as db
from model.model import GoldLabel
from pages.components.authentication_service import AuthenticationService
from pages.components.sidebar.sidebar_state_component import SidebarStateComponent
from util.session_constants import AVAILABLE_LABELS, BACK_BUTTON_PAGE, CURRENT_LABELING_STEP_RESULTS, CURRENT_PAGE, \
    SELECTED_LABELING_TASK, SELECTED_TIME_SERIES, SELECTED_TIME_SERIES_FEATURES
from util.string_convenience import display_labels

prev_page = db.load_cache(CURRENT_PAGE)
if prev_page != 'Time_Series_Analysis':
    back_button_page = prev_page
    db.cache(back_button_page, BACK_BUTTON_PAGE)
else:
    back_button_page = db.load_cache(BACK_BUTTON_PAGE)

st.session_state[CURRENT_PAGE] = 'Time_Series_Analysis'

auth = AuthenticationService()
auth.authenticate()
auth.showSidebar()

ssc = SidebarStateComponent()
ssc.show()
st.sidebar.divider()

if SELECTED_TIME_SERIES in st.session_state:
    time_series = db.load_cache(SELECTED_TIME_SERIES)
    features = db.load_cache(SELECTED_TIME_SERIES_FEATURES)
    labeling_results = db.load_cache(CURRENT_LABELING_STEP_RESULTS)
else:
    st.write(
        'No time series selected. Please select a time series on either the Labeling Results or the Labeling page.')
    btn_row = row(1)
    go_to_main_page = btn_row.button("Take me to the labeling task", use_container_width=True)
    if go_to_main_page:
        switch_page('Labeling_Task')
    st.stop()

gbbrow = row(3, vertical_align='bottom')
gbbrow.subheader('Time Series Analysis: ' + str(features.name))
gbbrow.empty()
go_back_button = gbbrow.button("Go back to " + display_labels(back_button_page), use_container_width=True)
if go_back_button:
    switch_page(back_button_page)

available_labels = db.load_cache(AVAILABLE_LABELS)
ts_name = time_series.loc[:, time_series.columns[0]].name

filter = GoldLabel.time_series_key == ts_name and GoldLabel.labeling_task_id == st.session_state[
    SELECTED_LABELING_TASK].id
existing_label = db.load(GoldLabel, filter=filter)
# st.write('Existing label: ')
# st.write(existing_label)

with st.form('test'):
    # c1, c2 = st.columns([5, 1])
    row1 = row([6, 1], vertical_align="bottom")

    label = row1.selectbox(
        label='Label',
        options=available_labels[:-1],
        key=time_series,
        index=existing_label[0].label if len(existing_label) > 0 else 0,
    )

    save_button = row1.form_submit_button("Save Gold Label")
    if save_button:
        new_gold = GoldLabel(
            id=existing_label[0].id if len(existing_label) > 0 else None,
            labeling_task_id=st.session_state[SELECTED_LABELING_TASK].id,
            time_series_key=str(features.name),
            label=available_labels.index(label),
            user_id=db.load_cache('username')
        )
        if len(existing_label) > 0:
            db.update(new_gold)
            # st.toast('Gold Label updated', icon='✅')
        else:
            db.save(new_gold)
            # st.toast('Gold Label saved', icon='✅')

lcts = time_series.reset_index(drop=True)
name = time_series.columns[0]
lcts.rename(columns={name: 'value'}, inplace=True)
st.line_chart(lcts)
st.dataframe(features, use_container_width=True)

if labeling_results is not None:
    st.write('Labeling results:')
    st.dataframe(labeling_results, use_container_width=True)
