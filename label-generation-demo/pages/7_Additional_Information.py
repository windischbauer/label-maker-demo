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

st.header('Additional Information', divider='blue')

st.subheader('Feature extraction tools and extracted features')
st.write('The features for the use case have been extracted with the TSFresh and the PyCatch22 library.'
         'For TSFresh the `EfficientFCParameters()` have been used to limit the computation time.'
         'For further information about the feature set follow the links below.')

tools_f = {
    'TSFresh':
        'https://tsfresh.readthedocs.io/en/latest/text/introduction.html',
    'TSFresh Features':
        'https://tsfresh.readthedocs.io/en/latest/text/list_of_features.html',
    'Catch22':
        'https://feature-based-time-series-analys.gitbook.io/catch22-features/',
    'Catch22 Features':
        'https://feature-based-time-series-analys.gitbook.io/catch22-features/feature-overview-table',
}

st.dataframe(tools_f, use_container_width=True, column_config={
    'value': st.column_config.LinkColumn(
        label='Link',
    ),
    '': st.column_config.Column(
        label='Info',
    )
})

st.subheader('Labeling')
st.write('The data labeling is enabled by Snorkel. Snorkel uses a set of labeling functions to generate a label '
         'matrix. The snorkel internal models, the LabelModel or the MajorityVoter, then output probabilistic labels '
         'for each time series. The output of these models is then used as an input for a surrogate model that '
         'generalizes over the labeling functions. As an additional surrogate model there is also WeaSEL, that utilizes'
         'the full labeling matrix and has an end-model, our so-called surrogate model, directly built in.')

tools_l = {
    'Snorkel':
        'https://www.snorkel.org',
    'WeaSEL':
        'https://github.com/autonlab/weasel/tree/main',
}

st.dataframe(tools_l, use_container_width=True, column_config={
    'value': st.column_config.LinkColumn(
        label='Link',
    ),
    '': st.column_config.Column(
        label='Info',
    )
})

st.subheader('Use Case')
st.write('The use case focuses on generating training data for constant/static thresholds and seasonal baselining data '
         'to ultimately improve anomaly detection models. Further information about seasonal baselining and '
         'constant/static thresholds can be found on the following links.')

tools_dt = {
    'Dynatrace Constant/Static Threshold':
        'https://docs.dynatrace.com/docs/platform/davis-ai/anomaly-detection/metric-events/static-thresholds',
    'Dynatrace Seasonal Baselining':
        'https://docs.dynatrace.com/docs/platform/davis-ai/anomaly-detection/metric-events/seasonal-baseline',
}

st.dataframe(tools_dt, use_container_width=True, column_config={
    'value': st.column_config.LinkColumn(
        label='Link',
    ),
    '': st.column_config.Column(
        label='Info',
    )
})

st.subheader('Further questions and survey')
st.write('Finally, if you have spent enough time with the Label Maker and are satisfied with the outcome, please send'
         'the resulting `label_maker.sqlite` file to johannes.windischbauer@gmail.com. Furthermore, please fill out the'
         'survey under this link https://forms.gle/gXSs1qFrtFdiAqK26. Thank you for your participation.')

tools_s = {
    'Email Address':
        'johannes.windischbauer@tuwien.ac.at',
    'Survey Link':
        'https://forms.gle/gXSs1qFrtFdiAqK26',
}

st.dataframe(tools_s, use_container_width=True, column_config={
    'value': st.column_config.LinkColumn(
        label='Link',
    ),
    '': st.column_config.Column(
        label='Info',
    )
})

# df = pd.DataFrame(tools)
