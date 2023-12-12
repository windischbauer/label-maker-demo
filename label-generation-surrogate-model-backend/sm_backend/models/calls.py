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

from sm_backend.models.surrogate_model import SurrogateModel
from sm_backend.models.weasel_m import WeaselM
from sm_backend.models.t_log_reg import TorchLogisticRegression
from sm_backend.models.plt_log_reg import PytorchLightningLogisticRegression
import pandas as pd
import io

class Calls(SurrogateModel):
    def __init__(self):
        self.model = None

    def restart(self):
        self.model = None
        print('Model cleared')
        return 'model cleared'

    def init_tflog_reg(self):
        print('Initializing TFLogReg')
        print(type(self.model))
        print(type(self.model) == PytorchLightningLogisticRegression)
        if type(self.model) == PytorchLightningLogisticRegression:
            print('model already initialized')
            return "model already initialized"
        else:
            self.model = PytorchLightningLogisticRegression()
            return "model initialized"
    
    def init_weasel(self):
        print('Initializing Weasel')
        print(type(self.model))
        print(type(self.model) == WeaselM)
        if type(self.model) == WeaselM:
            print('model already initialized')
            return "model already initialized"
        else: 
            self.model = WeaselM()
            return "model initialized"

    def apply(self, features, labels, fold=5):
        print('Applying some Model')
        feat = pd.read_json(io.StringIO(features))
        lab = pd.read_json(io.StringIO(labels))
        return self.model.apply(feat, lab, fold)
    
    def predict(self, features):
        print('Predicting some Model')
        feat = pd.read_json(io.StringIO(features))
        return self.model.predict(feat)



    