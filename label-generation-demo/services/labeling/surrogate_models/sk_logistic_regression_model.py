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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, log_loss
from sklearn.model_selection import StratifiedKFold


class SKLogisticRegression:
    def __init__(self,
                 features=None,
                 labels=None,
                 C=1e3,
                 solver='liblinear',
                 **kwargs,
                 ) -> None:
        self.features = features
        self.labels = labels
        self.C = C
        self.solver = solver
        self.model = None
        self.folds = 5

    def apply(self):
        n_splits = self.folds
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        all_metrics = []

        for train_index, test_index in skf.split(self.features, self.labels):
            X_train, X_test = self.features.iloc[train_index], self.features.iloc[test_index]
            y_train, y_test = self.labels.iloc[train_index], self.labels.iloc[test_index]

            model = LogisticRegression(C=self.C, solver=self.solver, verbose=True)
            model.fit(X=X_train, y=y_train.values)

            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)

            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            loss = log_loss(y_test, y_prob)

            all_metrics.append(
                {'test_acc': accuracy, 'test_precision': precision, 'test_recall': recall, 'test_loss': loss})

        # Finally fit all data
        self.model = LogisticRegression(C=self.C, solver=self.solver, verbose=True)
        self.model.fit(X=self.features, y=self.labels.values)

        return all_metrics

    def predict(self, features):
        # print('predictions')
        # print(self.model.predict(features))
        return self.model.predict(features)

    def toJSON(self):
        return {
            'C': self.C,
            'solver': self.solver
        }

    def show(self):
        c1, c2 = st.columns(2)
        self.C = c1.number_input(
            'C',
            value=self.C,
            key='sklr-c-ni'
        )
        slv_options = ['liblinear', 'lbfgs', 'sag', 'saga']
        self.solver = c2.selectbox(
            'Solver',
            options=slv_options,
            index=slv_options.index(self.solver),
            key='sklr-solver-sb'
        )
        self.folds = st.number_input(
            'Number of Stratified K-Folds',
            min_value=1,
            max_value=100,
            value=5,
            help='Note that increasing the amount of folds also increases training time.'
        )

    def get_definitive_labels(self):
        return self.labels.values
