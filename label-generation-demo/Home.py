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
from streamlit_extras.switch_page_button import switch_page
import streamlit_nested_layout

from pages.components.authentication_service import AuthenticationService
from util.session_constants import CURRENT_PAGE

st.set_page_config(layout="wide", page_title='Label Maker')

st.title('Label Maker')

st.session_state[CURRENT_PAGE] = 'Label_Maker_Home'

styling_pre = '<div style="background: #F8F9FB; border-radius: 0.25rem; padding: 1rem; color: black">'
styling_post = '</div>'

st.header('Welcome to the Label Maker Demo', divider='blue')
st.write('Thank you for taking the time to demo the application. Please read the following instructions carefully '
         'before proceeding.')
st.write('Before you can continue to explore the application and the available time series data, please log in with the'
         ' credentials provided to you. Logging in with the credentials adds a user to every labeling run and allows to'
         ' combine the data afterwards easier.')
st.write('After logging in successfully you can visit all other pages. The Labeling Task page is a good start to '
         'familiarize yourself with the task at hand. There is a task and ruleset switcher on the side bar. You can '
         'switch between tasks and rulesets any time you want. However, be careful when switching, as this will take '
         'some time. The time series need to fetched from their respective files and loaded into the context.')
st.write('From there on you can create rulesets or choose existing ones to add, edit or remove rules. Once you are '
         'satisfied with the ruleset you can start labeling the data on the Labeling page.')
st.write('Finally, you will be able to view your labeling results on the labeling results page.')

st.subheader('Sample Task')
st.write('The sample task is a subset of the time series for the Seasonal or Constant use case. It only contains 300 '
         'time series. There is a ruleset with 3 different types of rules (simple, advanced, free form) available to '
         'try out. There are also already labeling results in the database persisted.')
st.write('This is just to show off the functionality. The time series and rules and labeling parameters were chosen at '
         'random.')

st.subheader('Use Case: Seasonal or Constant')
st.write('The use case labeling task contains `4514 time series` and `793 features`. The features are extracted using '
         'the TSFresh and Catch22 libraries. For more information on the feature extraction go to the additional '
         'information section.')
st.write('You are tasked to label the time series data with the labels `Seasonal Baselining` and `Constant Threshold`. '
         'To achieve this you must create a ruleset and add at least three rules to it. There is no limit to how many '
         'rules you can create.'
         'Once you have a ruleset you are satisfied with, you can start the labeling process on the Labeling page.')
st.write('During the labeling process you can temporarily save your run if you want to change more parameters and '
         'want to see the metrics change, or once you are satisfied with a result, can persist them to the database. '
         'Results that are persisted to the database can be viewed and directly compared on the labeling results page.')
st.write('Please persist multiple results to the database when you feel they are "good enough".')
st.write('Finally, when you are finished and content with your labeling results email the `label_maker.sqlite` '
         'database file to johannes.windischbauer@tuwien.ac.at and fill out the survey. The `label_maker.sqlite` file '
         'can be found in the projects data directory.')
st.write(
    'Hint: In the labeling task switcher you can already find a labeling task called "Use Case 1". Select this use '
    'case and create a ruleset.')

st.subheader('Please fill out the survey')
st.write('https://forms.gle/gXSs1qFrtFdiAqK26')

st.subheader('Additional Information')
st.write('Find additional information on the Additional Information page.')
btn = st.button('Take me there')
if btn:
    switch_page('Additional_Information')

auth = AuthenticationService()
auth.authenticate(main=True)
auth.showSidebar()
