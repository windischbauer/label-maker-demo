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


import json

import numpy as np


class WeaselModel:
    def __init__(self,
                 server,
                 features=None,
                 labels=None,
                 **kwargs,
                 ) -> None:
        self.features = features
        self.labels = labels
        self.server = server
        self.def_labels = None

    def apply(self):
        # st.write('applying weasel model')
        self.server.init_weasel()
        result = self.server.apply(self.features.to_json(), json.dumps(self.labels.tolist()), 0)
        # st.write(result)

    def predict(self, features):
        preds = self.server.predict(features.to_json())
        return np.asarray(preds)

    def toJSON(self):
        pass

    def show(self):
        pass

    def get_definitive_labels(self):
        return self.def_labels
