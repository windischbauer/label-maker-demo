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
from streamlit_extras.row import row

import services.persistence_service as db
from model.model import GoldLabel
from services.connectors.backend_connector import connect_server
from services.labeling import labeler as lb
from services.labeling.surrogate_models.probablistic_logistic_regression_model import TorchProbabilisticLogisticRegression
from services.labeling.surrogate_models.sk_logistic_regression_model import SKLogisticRegression
from services.labeling.surrogate_models.weasel_model import WeaselModel
from util.session_constants import SELECTED_LABELING_TASK
from util.string_convenience import escape_line_breaks_in_rules


class LabelingProperties:
    def __init__(self, data, properties=None) -> None:
        self.data = data
        self.properties = properties
        self.label_model_properties = LabelModelProperties(
            data, **properties['label_model_properties'] if properties else {})
        self.surrogate_model_properties = SurrogateModelProperties(
            data, **properties['surrogate_model_properties'] if properties else {})

    def show(self):
        self.label_model_properties.show()
        st.divider()
        self.surrogate_model_properties.show()

    def toJSON(self):
        return {
            'lm': self.label_model_properties.toJSON(),
            'sm': self.surrogate_model_properties.toJSON()
        }


class LabelModelProperties:
    def __init__(self,
                 data,
                 type='Label Model',
                 epochs=500,
                 seed=123,
                 tie_break_policy='abstain',
                 only_selected_lrs=False,
                 lrs=[]) -> None:
        self.data = data
        self.type = type
        self.epochs = epochs
        self.seed = seed
        self.tie_break_policy = tie_break_policy
        self.only_selected_lrs = only_selected_lrs
        self.lrs = lrs

    def show(self) -> None:
        st.subheader('Snorkel Labeling')
        self.type = st.selectbox(
            'Snorkel Model',
            options=['Label Model', 'Majority Model'],
            key='lm-type-sb'
        )

        c1, c2 = st.columns(2)
        if self.type == 'Label Model':
            self.epochs = c1.number_input(
                'Epochs',
                value=self.epochs,
                key='lm-epochs-ni'
            )
            self.seed = c2.number_input(
                'Seed',
                value=self.seed,
                key='lm-seed-ni'
            )

        tbp_options = ['abstain', 'random', 'true-random']
        self.tie_break_policy = st.selectbox(
            'Tie Break Policy',
            options=tbp_options,
            index=tbp_options.index(self.tie_break_policy),
            key='lm-tie-break-sb'
        )

        self.only_selected_lrs = st.checkbox(
            'Only use selected labeling functions',
            help='Only use labeling functions that are selected. All others are not used. \
                The minimum amount of labeling functions is 3.',
            value=self.only_selected_lrs,
            key='lm-only-selected-lrs-cb'
        )

        serialized_rules = {rule.id: {'name': rule.name, 'rule': rule.rule, 'l1': rule.l1, 'l2': rule.l2}
                            for rule in self.data['rules']}
        if self.only_selected_lrs:
            tmp = st.multiselect(
                'Selected Labeling Functions',
                options=serialized_rules,
                default=self.lrs if len(self.lrs) > 0 else serialized_rules,
                format_func=(
                    lambda x: serialized_rules[x]['name'] if serialized_rules[x]['name'] else serialized_rules[x][
                                                                                                  'rule'][:25]),
                key='lm-selected-lrs-ms'
            )
            # use escape_line_breaks function on each string
            self.lrs = {k: escape_line_breaks_in_rules(
                v) for k, v in serialized_rules.items() if k in tmp}
        else:
            self.lrs = {k: escape_line_breaks_in_rules(
                v) for k, v in serialized_rules.items()}

    def apply(self) -> lb.Labeler:
        if self.only_selected_lrs:
            applicable_rules = [
                rule for rule in self.data['rules'] if rule.id in self.lrs]
        else:
            applicable_rules = self.data['rules'].copy()

        # st.write('FM labeler')
        # st.write(lb.feature_matrix)
        lb.update_feature_matrix()
        # st.write('FM labeler after update')
        # st.write(lb.feature_matrix)
        labeler = lb.Labeler(applicable_rules, self.data['tsd'].feature_matrix)
        labeler.create_labeling_functions()
        labeler.apply()

        if self.type == 'Label Model':
            labeler.fit(n_epochs=self.epochs, seed=self.seed)

        return labeler

    def toJSON(self) -> str:
        json_string = self.__dict__.copy()
        del json_string['data']
        return json_string


class SurrogateModelProperties:
    def __init__(self,
                 data,
                 type='SKLogisticRegression',
                 incl_gold=False,
                 only_lm_features=True,
                 additional_features=[],
                 train_test_split=80,
                 model=None,
                 **kwargs) -> None:
        self.data = data
        self.type = type
        self.incl_gold = incl_gold
        self.only_lm_features = only_lm_features
        self.additional_features = additional_features
        self.train_test_split = train_test_split
        self.model = model
        self.server = None

    def show(self) -> None:
        # for debugging
        import random
        key = random.randint(0, 1000000000)
        st.subheader('Surrogate Model')
        types = ['SKLogisticRegression',
                 'TorchProbabilisticLogisticRegression',
                 'WeaselModel']

        model_row = row([5, 3], vertical_align='bottom')
        self.type = model_row.selectbox(
            'Surrogate Model',
            options=types,
            index=types.index(self.type),
            key='sm-type-sb' + str(key)
        )

        new_server = model_row.button('Restart Surrogate Model Training', key='sm-restart-btn' + str(key),
                                      use_container_width=True)
        if new_server:
            self.server = connect_server(restart=True)
        else:
            self.server = connect_server()

        self.incl_gold = st.checkbox(
            'Use Gold Labels (where available)',
            help='Use gold labels instead of labeling model labels \
                where they are available. This might cause different \
                outcomes for labeling runs occuring at a later time  \
                when the gold labels or the amount of gold labels has\
                changed. If activated, there will be another column  \
                showing the training data for the surrogate model.  \
                \n    \
                :warning: Warning: Due to the nature of Streamlit\'s internal state you have to recheck \
                this box when you change gold labels for the changes to apply',
            value=False if self.type == 'WeaselModel' else self.incl_gold,
            key='sm-incl-gold-cb' + str(key),
            # disabled=self.type == 'WeaselModel'
        )
        self.only_lm_features = st.checkbox(
            'Only use the same features as the Snorkel Model',
            value=self.only_lm_features,
            key='sm-only-lm-features-cb' + str(key)
        )

        if self.only_lm_features:
            self.additional_features = st.multiselect(
                'Additional Features',
                options=self.data['tsd'].feature_matrix.columns[:-1],
                default=self.additional_features,
                key='sm-additional-features-ms' + str(key)
            )

        # self.train_test_split = st.slider(
        #     'Train-Test Split (not implemented yet)',
        #     min_value=0,
        #     max_value=100,
        #     value=self.train_test_split,
        #     key='sm-train-test-split-sl' + str(key)
        # )

        if self.type == 'SKLogisticRegression':
            if self.model is not None:
                self.model = SKLogisticRegression(
                    **self.model)
            else:
                self.model = SKLogisticRegression()

        elif self.type == 'TorchProbabilisticLogisticRegression':
            if self.model is not None:
                self.model = TorchProbabilisticLogisticRegression(server=self.server,
                                                                  **self.model)
            else:
                self.model = TorchProbabilisticLogisticRegression(server=self.server)

        elif self.type == 'WeaselModel':
            if self.model is not None:
                self.model = WeaselModel(server=self.server,
                                         **self.model)
            else:
                self.model = WeaselModel(server=self.server)

        self.model.show()

    def apply(self, labeler):
        if self.only_lm_features:
            features = list(labeler.get_features())
            features.extend(self.additional_features)
            surrogate_features = self.data['tsd'].feature_matrix[features]
        else:
            surrogate_features = self.data['tsd'].feature_matrix.iloc[:, :-1]

        filter_gl = GoldLabel.labeling_task_id == st.session_state[
            SELECTED_LABELING_TASK].id
        gold_labels = db.load(GoldLabel, filter=filter_gl)

        if self.type == 'SKLogisticRegression':
            y_labels = pd.DataFrame(
                labeler.predicted_labels[1].copy(), index=labeler.predicted_labels[0]
            )

            if self.incl_gold:
                for gl in gold_labels:
                    y_labels.loc[int(gl.time_series_key), 0] = gl.label

        elif self.type == 'TorchProbabilisticLogisticRegression':
            y_labels = pd.DataFrame(
                labeler.predicted_probs, index=labeler.predicted_labels[0]
            )

            if self.incl_gold:
                for gl in gold_labels:
                    y_labels.loc[int(gl.time_series_key), :] = 0.0
                    y_labels.loc[int(gl.time_series_key), gl.label] = 1.0

        elif self.type == 'WeaselModel':
            y_labels = labeler.L_train
            self.model.def_labels = labeler.predicted_labels[1]

            if self.incl_gold:
                y_labels = self._add_gold_to_weasel(gold_labels, y_labels, labeler.predicted_labels)

        self.model.features = surrogate_features
        self.model.labels = y_labels

        return self.model

    def predict(self, features):
        return self.model.predict(features)

    def toJSON(self):
        json_string = self.__dict__.copy()
        del json_string['data']
        del json_string['model']
        del json_string['server']
        json_string['model'] = self.model.toJSON()
        return json_string

    def _add_gold_to_weasel(self, gold_labels, y_labels, predictions):
        y_labels = y_labels.copy()
        for i in range(len(predictions[0])):
            for gl in gold_labels:
                if str(gl.time_series_key) == str(predictions[0][i]):
                    y_labels[i] = predictions[1][i]
        return y_labels


