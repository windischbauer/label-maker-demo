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


def simple_creator(time_series_data):
    def opp(cond):
        if cond == '<':
            return '>='
        elif cond == '<=':
            return '>'
        elif cond == '==':
            return '!='
        elif cond == '!=':
            return '=='
        elif cond == '>=':
            return '<'
        elif cond == '>':
            return '<='

    def update_slider():
        st.session_state.vsl = st.session_state.numeric

    def update_numin():
        st.session_state.numeric = st.session_state.vsl

    fm = time_series_data.feature_matrix

    col1, col2 = st.columns([1, 1])
    feature_select = col1.selectbox('Select feature', options=fm.columns)

    condition_select = col2.selectbox('Select condition', options=[
        '<', '<=', '==', '!=', '>=', '>'])

    rounding_precision = 3
    max_val = round(fm.loc[:, [feature_select]].max().values[0], rounding_precision)
    med_val = round(fm.loc[:, [feature_select]].median().values[0], rounding_precision)
    min_val = round(fm.loc[:, [feature_select]].min().values[0], rounding_precision)
    q1_val = round(fm.loc[:, [feature_select]].quantile(0.25).values[0], rounding_precision)
    q3_val = round(fm.loc[:, [feature_select]].quantile(0.75).values[0], rounding_precision)

    css_pre = '<div style="border-radius: 0.5rem; background: #F8F9FB"; display: flex;><div style="display: flex; justify-content: center; padding: 0.25rem; margin-bottom: 1rem;">'
    css_post = '</div></div>'

    # st.write(max_val)
    cv1, cv2 = st.columns([1, 0.3])

    value = cv1.slider(label='Value slider', min_value=float(min_val), max_value=max_val, step=max_val / 1000.,
                       key='vsl', value=float(med_val), on_change=update_numin)
    numin_value = cv2.number_input(
        label='Value input', min_value=float(min_val), max_value=max_val, value=value, on_change=update_slider,
        key='numeric')

    with st.expander('Show statistics'):
        csv1, csv2, csv3, csv4, csv5 = st.columns([1, 1, 1, 1, 1])
        csv1.markdown(css_pre + 'Minimum  <br>' + display_value(min_val) + css_post, unsafe_allow_html=True)
        csv2.markdown(css_pre + 'First quartile  <br>' + display_value(q1_val) + css_post, unsafe_allow_html=True)
        csv3.markdown(css_pre + 'Median  <br>' + display_value(med_val) + css_post, unsafe_allow_html=True)
        csv4.markdown(css_pre + 'Third quartile  <br>' + display_value(q3_val) + css_post, unsafe_allow_html=True)
        csv5.markdown(css_pre + 'Maximum  <br>' + display_value(max_val) + css_post, unsafe_allow_html=True)

    ev1 = 'fm[fm["' + feature_select + '"]' + \
          condition_select + str(value) + ']'
    ev2 = 'fm[fm["' + feature_select + '"]' + \
          opp(condition_select) + str(value) + ']'

    label_sets = [eval(ev1), eval(ev2)]

    r = feature_select + ' ' + condition_select + ' ' + str(value)

    return r, label_sets


def display_value(value, size=1e5):
    return str(value) if value < size and value > -size else '{:0.3e}'.format(value)
