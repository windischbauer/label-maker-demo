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


import io
import json

import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from model.model import GoldLabel, LabelingResult, RuleSet
from pages.components.authentication_service import AuthenticationService
from pages.components.sidebar.sidebar_state_component import SidebarStateComponent
from services import persistence_service as db
from util.session_constants import AVAILABLE_LABELS, CURRENT_LABELING_STEP, CURRENT_LABELING_STEP_RESULTS, CURRENT_PAGE, \
    LABELING_RESULT_DATAFRAME, LABELING_RUN_DATAFRAME, LABELING_STEP_LIST, SELECTED_LABELING_TASK, SELECTED_TIME_SERIES, \
    SELECTED_TIME_SERIES_FEATURES
from util.string_convenience import display_date

st.session_state[CURRENT_PAGE] = 'Labeling_Results'

auth = AuthenticationService()
auth.authenticate()
auth.showSidebar()

ssc = SidebarStateComponent()
ssc.show()
st.sidebar.divider()

db.clear_cache(LABELING_RUN_DATAFRAME)

selected = db.load_cache(SELECTED_LABELING_TASK)
st.markdown(
    '<div style="display: flex; justify-content: space-between"><h2>Results</h2><h2 style="color: #2B66C2">LT: ' + (
        selected.name if selected is not None else 'None') + '</h2></div>', unsafe_allow_html=True)

if selected is None:
    st.write('No labeling task selected. Please select or create a labeling task on the Labeling Tasks page.')
    st.stop()

filter_lr_tid = LabelingResult.labeling_task_id == selected.id
results = db.load(LabelingResult, filter=filter_lr_tid)

tsd = db.load_time_series_data()

filter_gl_tid = GoldLabel.labeling_task_id == selected.id
gold_labels = db.load(GoldLabel, filter=filter_gl_tid)

if results is None or len(results) == 0:
    st.write('No labeling results available for this labeling task')
    st.stop()

available_labels = []

for i, l in enumerate(db.load_cache(AVAILABLE_LABELS)):
    if i < len(db.load_cache(AVAILABLE_LABELS)) - 1:
        available_labels.append(str(i) + ' (' + l + ')')

# Load data frame from cache and create new if not available
colnames = []
dfall = db.load_cache(LABELING_RESULT_DATAFRAME)
statsdf = db.load_cache(LABELING_RUN_DATAFRAME)

# Disabled until selectboxes allow empty values
# selected_user = c1.selectbox('Select User', options=db.load(
#     User), format_func=(lambda x: x.name))
stats_s = pd.DataFrame()
stats_l = pd.DataFrame()
stats_mod = pd.DataFrame()
ids = []

if dfall is None or statsdf is None:
    dfall = pd.DataFrame()
    for res in results:
        df = pd.read_json(io.StringIO(res.results), orient='index')
        props = json.loads(res.properties)

        colname = display_date(res.date, no_year=True) + \
                  '' + ' by ' + res.user_id
        colnames.append(colname)
        df.rename(columns={0: colname}, inplace=True)
        dfall = pd.concat([dfall, df], axis=1)

        ids.append(res.id)

        statsdf = pd.read_json(io.StringIO(res.scores), orient='index')
        rs_name = db.load(RuleSet, filter=RuleSet.id == res.ruleset_id)[0].name
        l_statsdf = statsdf.loc['score_l', :].add_suffix('_l')
        l_statsdf['rs_name'] = rs_name
        s_statsdf = statsdf.loc['score_s', :].add_suffix('_s')
        l_statsdf = pd.DataFrame(l_statsdf).rename(
            columns={'score_l': colname})
        s_statsdf = pd.DataFrame(s_statsdf).rename(
            columns={'score_s': colname})
        l_statsdf.loc['type_l'] = props['lm']['type']
        s_statsdf.loc['type_s'] = props['sm']['type']
        stats_l = pd.concat([stats_l, l_statsdf], axis=1)
        stats_s = pd.concat([stats_s, s_statsdf], axis=1)

    statsdf = pd.concat([stats_l, stats_s]).transpose()
    statsdf['ids'] = ids

    dfall.insert(0, 'timeseries', [[] for x in range(len(dfall))])
    dfall.insert(1, 'gold_label', None)
    dfall.index.name = 'mkey'

    for gl in gold_labels:
        dfall.at[int(gl.time_series_key),
                 'gold_label'] = available_labels[gl.label]

    for k, v in tsd.data_dict.items():
        t = v.fillna(0).copy()
        t = t.reset_index().iloc[:, 1]
        t = t.groupby(t.index // 20).mean()
        v = t.values[0:2000]
        dfall.at[k, 'timeseries'] = v

# Set go_to to false
dfall['go_to'] = False
statsdf['go_to'] = False


def cache_dfs(df, sdf):
    db.cache(df, LABELING_RESULT_DATAFRAME)
    db.cache(sdf, LABELING_RUN_DATAFRAME)


st.markdown('### Scores per Labeling Run :runner:')
df_stats = st.data_editor(
    statsdf,
    column_config={
        'accuracy_l': st.column_config.Column(
            'LM Accuracy',
            help='Accuracy in regard to the label model',
            disabled=True
        ),
        'accuracy_s': st.column_config.Column(
            'GL Accuracy',
            help='Accuracy in regard to the surrogate model',
            disabled=True
        ),
        'precision_l': st.column_config.Column(
            'LM Precision',
            help='Precision in regard to the label model',
            disabled=True
        ),
        'precision_s': st.column_config.Column(
            'GL Precision',
            help='Precision in regard to the surrogate model',
            disabled=True
        ),
        'recall_l': st.column_config.Column(
            'LM Recall',
            help='Recall in regard to the label model',
            disabled=True
        ),
        'recall_s': st.column_config.Column(
            'GL Recall',
            help='Recall in regard to the surrogate model',
            disabled=True
        ),
        'model_l': st.column_config.Column(
            'TS Count LM',
            help='Score of the label model',
            disabled=True
        ),
        'model_s': st.column_config.Column(
            'TS Count GL',
            help='Score of the surrogate model',
            disabled=True
        ),
        'rs_name': st.column_config.Column(
            'Rule Set',
            help='Name of the rule set',
            disabled=True
        ),
        'type_l': st.column_config.Column(
            'LM Type',
            help='Type of the label model',
            disabled=True
        ),
        'type_s': st.column_config.Column(
            'SM Type',
            help='Type of the surrogate model',
            disabled=True
        ),

    },
    column_order=[
        'rs_name',
        'type_l', 'model_l', 'accuracy_l', 'precision_l', 'recall_l',
        'type_s', 'model_s', 'accuracy_s', 'precision_s', 'recall_s',
        'go_to'
    ],
    on_change=cache_dfs,
    args=(dfall, statsdf,),
    use_container_width=True,
)

st.markdown('### Labels per Timeseries :chart_with_upwards_trend:')
df_go_to = st.data_editor(
    dfall,
    column_config={
                      'timeseries': st.column_config.LineChartColumn(
                          'Time Series (down sampled)',
                          width='medium',
                          help='20x down sampled time series'
                      ),
                      'gold_label': st.column_config.SelectboxColumn(
                          'GL',
                          help='Gold label introduced by hand',
                          options=available_labels,
                          width='small'
                      ),
                  } | {coln: st.column_config.Column(
        coln + '\n  ' + 'test',
        width='small',
        help=coln + ' ',
        disabled=True
    ) for coln in colnames},
    # column_config=colname_conf,
    on_change=cache_dfs,
    args=(dfall, statsdf,),
    height=600,
    use_container_width=True,
)

goto = df_go_to.loc[df_go_to['go_to'] == True]
if len(goto) > 0:
    mmk = goto.index.values[0]
    db.cache(tsd.data_dict[mmk], SELECTED_TIME_SERIES)
    db.cache(tsd.feature_matrix.loc[mmk],
             SELECTED_TIME_SERIES_FEATURES)
    db.cache(df_go_to.loc[mmk], CURRENT_LABELING_STEP_RESULTS)
    del st.session_state[LABELING_RESULT_DATAFRAME]
    switch_page('Time_Series_Analysis')

keys = dict([(str(gl.time_series_key), {'label': gl.label, 'id': gl.id})
             for gl in gold_labels])
changed_gold_labels = df_go_to.loc[df_go_to['gold_label'].notnull()].loc[:, ['gold_label']]

stats_goto = df_stats.loc[df_stats['go_to'] == True]
if len(stats_goto) > 0:
    csl = [r for r in results if r.id == stats_goto.loc[:, 'ids'].values[0]][0]
    csl.jsonify_variants()

    db.cache([csl], CURRENT_LABELING_STEP)
    db.cache([csl], LABELING_STEP_LIST)

    switch_page('Labeling')

for i in changed_gold_labels.index.values:
    if str(i) in keys:
        if keys[str(i)]['label'] != int(changed_gold_labels.loc[i].values[0].split(' ')[0]):
            changed_gold = GoldLabel(
                id=keys[str(i)]['id'],
                labeling_task_id=st.session_state[SELECTED_LABELING_TASK].id,
                time_series_key=str(i),
                label=changed_gold_labels.loc[i].values[0].split(' ')[0],
                user_id=db.load_cache('username')
            )
            db.update(entity=changed_gold)
    else:
        new_gold = GoldLabel(
            labeling_task_id=st.session_state[SELECTED_LABELING_TASK].id,
            time_series_key=str(i),
            label=int(changed_gold_labels.loc[i].values[0].split(' ')[0]),
            user_id=db.load_cache('username')
        )
        db.save(new_gold)
    db.cache(df_go_to, LABELING_RESULT_DATAFRAME)