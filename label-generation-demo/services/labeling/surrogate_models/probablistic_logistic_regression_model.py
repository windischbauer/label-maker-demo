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


import numpy as np
import streamlit as st


class TorchProbabilisticLogisticRegression:

    def __init__(self,
                 server,
                 features=None,
                 labels=None,
                 **kwargs,
                 ) -> None:
        self.features = features
        self.labels = labels
        self.server = server
        self.folds = 5

    def apply(self):
        # st.write('applying tflogreg model')
        self.server.init_tflog_reg()
        fold = 5
        result = self.server.apply(self.features.to_json(), self.labels.to_json(), self.folds)
        return result
        # st.write('received results')
        # st.write(result)

    def predict(self, features):
        # st.write('predicting')
        preds = self.server.predict(features.to_json())
        return np.asarray(preds)

    def toJSON(self):
        pass

    def show(self):
        self.folds = st.number_input(
            'Number of Stratified K-Folds',
            min_value=1,
            max_value=100,
            value=5,
            help='Note that increasing the amount of folds also increases training time.'
        )

    # from a dataframe get the column with the highest value
    def get_definitive_labels(self):
        return self.labels.idxmax(axis=1).values
