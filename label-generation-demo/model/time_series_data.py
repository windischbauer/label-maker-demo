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

from util.annotations import logger as l


class TimeSeriesData:

    @l.log
    # @st.cache_data
    def __init__(self, data_dict=None, feature_matrix=None, mkeys=None):
        if mkeys is None:
            mkeys = []
        if data_dict is None:
            data_dict = {}
        if feature_matrix is None:
            feature_matrix = pd.DataFrame()
        self._data_dict = data_dict
        self._feature_matrix = feature_matrix
        self._mkeys = mkeys

    @property
    def data_dict(self):
        return self._data_dict

    @data_dict.setter
    def data_dict(self, val):
        self._data_dict = val
        self._mkeys = list(self._data_dict.keys())

    @property
    def feature_matrix(self):
        return self._feature_matrix

    @feature_matrix.setter
    def feature_matrix(self, val):
        self._feature_matrix = val

    @property
    def mkeys(self):
        return self._mkeys
