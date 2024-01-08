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

import datetime

import pandas as pd
import streamlit as st
from sklearn.metrics import confusion_matrix
from streamlit_extras.row import row
from streamlit_extras.switch_page_button import switch_page

import pages.components.sidebar.sidebar_labeling_step_list as sbsl
import util.session_constants as const
from model.model import GoldLabel, LabelingResult, Rule
from pages.components.authentication_service import AuthenticationService
from pages.components.labeling.metrics import calculate_surrogate_scores, display_surrogate_metrics, \
    display_average_training_metrics, display_label_model_metrics
from pages.components.sidebar.sidebar_state_component import SidebarStateComponent
from services import persistence_service as db
from services.labeling import properties as lp
from util.string_convenience import display_date

st.session_state[const.CURRENT_PAGE] = 'Labeling'

auth = AuthenticationService()
auth.authenticate()
auth.showSidebar()

ssc = SidebarStateComponent()
ssc.show()
st.sidebar.divider()

st.header('Labeling')

ruleset = db.load_cache(const.SELECTED_RULESET)

filter_rs = Rule.ruleset_id == ruleset.id
rules = db.load(Rule, filter=filter_rs)

if len(rules) < 3:
    st.write(
        'At least 3 rules are required to start a labeling run. Please go to the Ruleset Creator page and create some rules.')
    rule_row = row(1, vertical_align='center')
    go_to_ruleset = rule_row.button('Go to Rule Creator', use_container_width=True)
    if go_to_ruleset:
        switch_page('Ruleset_Creator')
    st.stop()

selected_lt = db.load_cache(const.SELECTED_LABELING_TASK)
df = db.load_cache(const.LABELING_RUN_DATAFRAME)
# df = None
# st.write(df)
# if df is None:
#     data_provider = dp.DataProvider(
#         path=selected_lt.data_url, time_series_path=selected_lt.time_series_path, local=True)
#     time_series_data = data_provider.load_all(time_series_data=tsd.TimeSeriesData())
# else:
time_series_data = db.load_time_series_data()

available_labels = []
for i, l in enumerate(db.load_cache(const.AVAILABLE_LABELS)):
    if i < len(db.load_cache(const.AVAILABLE_LABELS)) - 1:
        available_labels.append(str(i) + ' (' + l + ')')

lsl = db.load_cache(const.LABELING_STEP_LIST)
tmp = db.load_cache(const.CURRENT_LABELING_STEP)
index = -1
if tmp is not None:
    csl = tmp[0]
else:
    csl = None

if lsl is None:
    lsl = []

if len(lsl) > 1:
    if csl is not None:
        index = [csl.date == x.date for x in lsl].index(True)
    csl = st.select_slider(
        'Labeling Runs',
        options=lsl,
        help='Select a labeling run to view its results and properties',
        format_func=(lambda x: display_date(x.date)),
        value=lsl[index],
        on_change=(lambda x: db.cache([x], const.CURRENT_LABELING_STEP)),
        args=(lsl[index],)
    )

    db.cache([csl], const.CURRENT_LABELING_STEP)

rdata = {'tsd': time_series_data, 'ruleset': ruleset, 'rules': rules}

with st.expander('Model Properties'):
    if csl is not None:
        lmp = lp.LabelModelProperties(data=rdata, **csl.properties['lm'])
        smp = lp.SurrogateModelProperties(data=rdata, **csl.properties['sm'])
    else:
        lmp = lp.LabelModelProperties(data=rdata)
        smp = lp.SurrogateModelProperties(data=rdata)
    lmp.show()
    smp.show()

labeler = lmp.apply()

labeler.predict(tie_break_policy=lmp.tie_break_policy)
labeler.predict_proba()

st.subheader('Results',
             help="If more time series graphs should be displayed you have to load them manually by going to the Labeling Task page and selecting the amount of time series to load.")
# if rrb:
#     datap = dp.DataProvider.fromlabelingtasktoloadmore(selected_lt)
#     datap.load_more()

filter_gl = GoldLabel.labeling_task_id == st.session_state[
    const.SELECTED_LABELING_TASK].id
gold_labels = db.load(GoldLabel, filter=filter_gl)
# st.write(gold_labels)

sm_model = smp.apply(labeler)
training_stats = sm_model.apply()

labeler_predictions = labeler.predicted_labels[1]
surrogate_predictions = sm_model.predict(smp.model.features)

# st.write(type(surrogate_predictions))
# st.write(surrogate_predictions)

if df is None:
    data = {
        'label model': labeler_predictions,
        'label model proba': labeler.predicted_probs.max(axis=1),
        'surrogate model': surrogate_predictions,
        'go to': False}

    df = pd.DataFrame(data=data, index=time_series_data.feature_matrix.index.values)
    df.index.name = 'mkey'
    df.insert(0, 'timeseries', [[] for x in range(len(df))])
    df.insert(1, 'gold_label', None)

    for gl in gold_labels:
        df.at[int(gl.time_series_key),
              'gold_label'] = available_labels[gl.label]

    for itm in time_series_data.data_dict.items():
        t = itm[1].fillna(0).copy()
        t = t.reset_index().iloc[:, 1]
        t = t.groupby(t.index // 20).mean()
        itm_ts = t.values[0:2000]
        df.at[itm[0], 'timeseries'] = itm_ts


if smp.incl_gold:
    if 'training_label' not in df.columns:
        df.insert(4, 'training_label', smp.model.get_definitive_labels())
    else:
        df['training_label'] = smp.model.get_definitive_labels()
else:
    if 'training_label' in df.columns:
        df = df.drop(columns=['training_label'])

df['label model'] = labeler_predictions
df['label model proba'] = labeler.predicted_probs.max(axis=1)
df['surrogate model'] = surrogate_predictions
dfe = st.data_editor(
    df,
    column_config={
        'mkey': st.column_config.Column(
            'Key',
            disabled=True,
        ),
        'label model': st.column_config.Column(
            'Label Model',
            disabled=True,
        ),
        'label model proba': st.column_config.Column(
            'LM Prob',
            disabled=True,
        ),
        'surrogate model': st.column_config.Column(
            'Surrogate Model',
            disabled=True,
        ),
        'gold_label': st.column_config.SelectboxColumn(
            'Gold Label',
            help='Gold label introduced by hand',
            options=available_labels,
            width='small'
        ),
        'timeseries': st.column_config.LineChartColumn(
            'Time Series',
            help='Time Series',
            width='medium',
        ),
        'training_label': st.column_config.Column(
            'Training Label',
            disabled=True,
        )
    },
    disabled=False,
    use_container_width=True,
    key='lb_dfe'
)

changed_gold_labels = dfe.loc[dfe['gold_label'].notnull()].loc[:, ['gold_label']]

keys = dict([(str(gl.time_series_key), {'label': gl.label, 'id': gl.id})
             for gl in gold_labels])
change = False
for i in changed_gold_labels.index.values:
    if str(i) in keys:
        if keys[str(i)]['label'] != int(changed_gold_labels.loc[i].values[0].split(' ')[0]):
            changed_gold = GoldLabel(
                id=keys[str(i)]['id'],
                labeling_task_id=st.session_state[const.SELECTED_LABELING_TASK].id,
                time_series_key=str(i),
                label=changed_gold_labels.loc[i].values[0].split(' ')[0],
                user_id=db.load_cache('username')
            )
            db.update(entity=changed_gold)
            change = True
    elif changed_gold_labels.loc[i].values[0].split(' ')[0] == 'None':
        # Delete from db
        pass
    else:
        new_gold = GoldLabel(
            labeling_task_id=st.session_state[const.SELECTED_LABELING_TASK].id,
            time_series_key=str(i),
            label=int(changed_gold_labels.loc[i].values[0].split(' ')[0]),
            user_id=db.load_cache('username')
        )
        db.save(new_gold)
        change = True

if change:
    db.cache(dfe, const.LABELING_RUN_DATAFRAME)
    st.rerun()

goto = dfe.loc[dfe['go to'] == True]
if len(goto) > 0:
    mmk = goto.index.values[0]
    db.cache(time_series_data.data_dict[mmk], const.SELECTED_TIME_SERIES)
    db.cache(time_series_data.feature_matrix.loc[mmk],
             const.SELECTED_TIME_SERIES_FEATURES)
    db.cache(df.loc[mmk], const.CURRENT_LABELING_STEP_RESULTS)
    db.clear_cache(const.LABELING_RUN_DATAFRAME)
    switch_page('Time_Series_Analysis')

st.subheader('Labeling Function Analysis')
with st.expander('Labeling Function Analysis'):
    st.dataframe(labeler.LF_analysis(), use_container_width=True)

    # Update gold labels so that changed scores are available
    gold_labels = db.load(GoldLabel, filter=filter_gl)

    scores_gllm = calculate_surrogate_scores(
        df.loc[[int(gl.time_series_key) for gl in gold_labels], 'label model'],
        [gl.label for gl in gold_labels],
        df.loc[[int(gl.time_series_key) for gl in gold_labels], 'label model'],
    )

    display_label_model_metrics(scores_gllm)

    st.markdown('**Features used**')
    st.write(labeler.get_features())
    with st.expander('**Labeling Rules used**'):
        st.write(lmp.lrs)

st.subheader('Surrogate Model Analysis')
with st.expander('Surrogate Model Analysis'):
    empty_scores = {"score_s": {"model": None, "accuracy": None, "precision": None, "recall": None},
                    "score_l": {"model": None, "accuracy": None, "precision": None, "recall": None}}
    scores = empty_scores.copy()
    if len(gold_labels) > 0:
        scores_s = calculate_surrogate_scores(
            smp.model.features.loc[[int(gl.time_series_key) for gl in gold_labels], :],
            [gl.label for gl in gold_labels],
            sm_model.predict(
                smp.model.features.loc[[int(gl.time_series_key) for gl in gold_labels], :])
        )
        scores['score_s'] = scores_s
    scores_l = calculate_surrogate_scores(
        smp.model.features,
        smp.model.get_definitive_labels(),
        surrogate_predictions)
    scores['score_l'] = scores_l

    # scores = {'score_s': scores_s, 'score_l': scores_l}

    previous_step = lsl[index] if len(lsl) >= 1 else None
    prev_scores = previous_step.scores if previous_step is not None else empty_scores

    display_average_training_metrics(training_stats)
    display_surrogate_metrics(scores, prev_scores)

    st.markdown('**Features used**')
    st.write(set(smp.model.features.columns.values))

    with st.expander('Confusion Matrix'):
        cm = confusion_matrix(
            smp.model.get_definitive_labels(), surrogate_predictions,
        )
        st.table(cm)

labeling_step_list = sbsl.SidebarLabelingStepList()
labeling_step_list.show(lsl)

btn_row = row(3, vertical_align='bottom')

timestamp = datetime.datetime.now()

properties = {
    'lm': lmp.toJSON(),
    'sm': smp.toJSON(),
}
lr = LabelingResult(labeling_task_id=ruleset.labeling_task_id,
                    user_id=db.load_cache('username'),
                    ruleset_id=ruleset.id,
                    properties=properties,
                    date=timestamp,
                    rules=lmp.lrs,
                    results=df.loc[:, 'surrogate model'].to_json(),
                    scores=scores)

add = btn_row.button('Cache Temporary Labeling Run', use_container_width=True)
if add:
    lsl.append(lr)
    db.cache(lsl, const.LABELING_STEP_LIST)
    db.cache([lr], const.CURRENT_LABELING_STEP)
    labeling_step_list.update(lsl)
    # st.experimental_rerun()

save = btn_row.button('Persist Labeling Result', use_container_width=True)
if save:
    lsl.append(lr)
    db.cache(lsl, const.LABELING_STEP_LIST)
    db.cache([lr], const.CURRENT_LABELING_STEP)
    db.save_labeling_result(lr)
    labeling_step_list.update(lsl)
    # st.experimental_rerun()

restart = btn_row.button('Clear the Labeling Run Cache', use_container_width=True)
if restart:
    db.clear_cache(const.LABELING_STEP_LIST)
    db.clear_cache(const.CURRENT_LABELING_STEP)
    labeling_step_list.show([])
    # st.experimental_rerun()
