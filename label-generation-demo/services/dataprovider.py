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

import services.persistence_service as db
from util.annotations import benchmark as b, logger as l
from util.session_constants import FETCHED_TIME_SERIES_MKEYS


# @st.cache_resource
class DataProvider():

    def __init__(self, path, time_series_path, local=False) -> None:
        self.local = local
        self.path = path
        self.time_series_path = time_series_path

    @classmethod
    def fromlabelingtask(cls, labeling_task):
        db.clear_cache(FETCHED_TIME_SERIES_MKEYS)
        return cls(labeling_task.data_url, labeling_task.time_series_path, local=True)

    @classmethod
    def fromlabelingtasktoloadmore(cls, labeling_task):
        return cls(labeling_task.data_url, labeling_task.time_series_path, local=True)

    @b.benchmark
    @l.log
    def load_feature_matrix(self, index_col='mkey') -> pd.DataFrame:
        time_series_data = db.load_time_series_data()
        feature_matrix = None
        try:
            if self.local:
                feature_matrix = pd.read_csv(self.path, index_col=index_col)
        except FileNotFoundError:
            feature_matrix = pd.DataFrame()
        # else:
        #     # conn = st.experimental_connection('s3', type=FilesConnection)
        #     df = conn.read(
        #         self.path, input_format="csv")
        #     feature_matrix = df.set_index(index_col)
        time_series_data.feature_matrix = feature_matrix
        db.cache_time_series_data(time_series_data)
        return feature_matrix

    @b.benchmark
    @l.log
    def load_time_series(self, time_series_data, max=None) -> dict:
        # st.write('Starting data preparation. This may take some time...')
        fm = time_series_data.feature_matrix
        dd = time_series_data.data_dict
        keys = self._key_difference(fm, dd)

        tmp = {}
        pbar = st.progress(0)
        size = len(keys) if max is None else max
        idx = 0
        if self.local:
            for k in keys:
                tmp[k] = pd.read_csv(self.time_series_path + '/' + str(k) + '.csv', index_col='time_captured')
                tmp[k].index = pd.to_datetime(tmp[k].index)
                idx += 1
                if max is not None:
                    if idx % max == 0:
                        break
                pbar.progress(idx * 100 // size)

            pbar.progress(100)

        else:
            # TODO: read dataframe containing ts data from s3 or locally
            #  and add them one by one to the respective time series meta key
            #  or maybe move this to the fetch_time_series function and work
            #  accordingly to the tsdb flag
            pass
        # self.fetched.update(tmp)
        # db.cache(self.fetched, FETCHED_TIME_SERIES_MKEYS)
        return tmp

    # def load_more(self):
    #
    #     keys = self._key_difference()
    #     tmp = {}
    #     i = 0
    #     for k in keys:
    #         if i >= 10:
    #             break
    #         tmp[k] = pd.read_csv(self.time_series_path + '/' + str(k) + '.csv', index_col='time_captured')
    #         tmp[k].index = pd.to_datetime(tmp[k].index)
    #         i += 1
    #     time_series_data = db.load_time_series_data()
    #     time_series_data.data_dict.update(tmp)
    #     db.cache_time_series_data(time_series_data)

    def load_all(self, time_series_data):
        time_series_data.feature_matrix = self.load_feature_matrix()
        time_series_data.data_dict = self.load_time_series(
            time_series_data
        )
        return time_series_data

    def _key_difference(self, feature_matrix, data_dict):
        return set(data_dict.keys()) ^ set(feature_matrix.index.values)
