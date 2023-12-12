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
from sklearn.metrics import precision_score, recall_score, accuracy_score


def display_surrogate_metrics(scores, prev_scores):
    with st.container():
        _display_metric_list(scores['score_s'],
                             prev_scores['score_s'], 'Gold Label')
        _display_metric_list(scores['score_l'],
                             prev_scores['score_l'], 'Label Model')


def display_label_model_metrics(scores):
    with st.container():
        if scores is not None:
            st.markdown('**:blue[Label Model compared to Gold Label]**')
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric('Number of Gold Labels', scores['model'])
            with s2:
                _display_single_metric(scores['accuracy'], None, 'Accuracy')
            with s3:
                _display_single_metric(scores['precision'], None, 'Precision')
            with s4:
                _display_single_metric(scores['recall'], None, 'Recall')

def display_average_training_metrics(scores):
    with st.container():
        if scores is not None:
            st.markdown('**:blue[Averaged Training Scores for Stratified K-Fold]**')
            s1, s2, s3, s4 = st.columns(4)
            # Initialize a dictionary to store the sum of values for each key
            sums = {key: 0 for key in scores[0]}

            # Calculate the sum of values for each key
            for entry in scores:
                for key, value in entry.items():
                    sums[key] += value

            # Calculate the average for each key
            num_entries = len(scores)
            averages = {key: total / num_entries for key, total in sums.items()}
            with s1:
                st.metric(
                    'Number of Stratified K-Folds',
                    num_entries
                )
            with s2:
                _display_single_metric(averages['test_acc'], None, 'Test Accuracy')
            with s3:
                _display_single_metric(averages['test_precision'], None, 'Test Precision')
            with s4:
                _display_single_metric(averages['test_recall'], None, 'Test Recall')
        else:
            st.markdown('**:red[No averaged training scores for this model available]**')


def _display_metric_list(scores, prev_scores, name):
    with st.container():
        st.markdown('**:blue[' + name + ' Scores]**',
                    help='Achieved by training on the whole dataset and evaluating against ' + name + ' labels')
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            if prev_scores['model'] is not None:
                delta = scores['model'] - prev_scores['model']
            else:
                delta = None
            st.metric(
                'Nr of Time Series',
                scores['model'],
                delta=delta,
                delta_color='off' if prev_scores is None else 'off' if prev_scores[
                                                                           'model'] == scores['model'] else 'normal'
            )
        with s2:
            _display_single_metric(
                scores['accuracy'], prev_scores['accuracy'], 'Accuracy Score')
        with s3:
            _display_single_metric(
                scores['precision'], prev_scores['precision'], 'Precision Score')
        with s4:
            _display_single_metric(
                scores['recall'], prev_scores['recall'], 'Recall Score')


def _display_single_metric(score, prev_score, name):
    delta = round((score -
                   prev_score) * 100, 2) if prev_score is not None else None
    if score is not None:
        st.metric(
            name,
            str(round(score * 100, 2)) + '%',
            delta=delta,
            delta_color='off' if delta is None else 'off' if delta == 0 else 'normal'
        )
    else:
        st.metric(
            name,
            None,
        )


def calculate_surrogate_scores(test, y_true, y_preds):
    model_sc = len(test)
    precision_sc = precision_score(y_true, y_preds, average='weighted')
    accuracy_sc = accuracy_score(y_true, y_preds)
    recall_sc = recall_score(y_true, y_preds, average='weighted')

    scores = {'model': model_sc, 'accuracy': accuracy_sc,
              'precision': precision_sc, 'recall': recall_sc}

    return scores
