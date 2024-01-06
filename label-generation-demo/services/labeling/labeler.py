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
from snorkel.labeling import PandasLFApplier, LFAnalysis, LabelingFunction
from snorkel.labeling.model import LabelModel, MajorityLabelVoter

import services.persistence_service as db
from services.parser.rule_parser import RuleParser
from util.session_constants import AVAILABLE_LABELS
from util.string_convenience import make_code_label, replace_binop, translate_rule_name

if st.session_state['authentication_status'] is None:
    st.stop()

feature_matrix = db.load_time_series_data().feature_matrix


def update_feature_matrix():
    global feature_matrix
    feature_matrix = db.load_time_series_data().feature_matrix


def lookup(x, feature, feature_matrix):
    return feature_matrix.at[x.name, feature]


class Labeler:

    def __init__(self, rules, f_m) -> None:
        global feature_matrix

        self.rules = rules
        self.labeling_functions = []
        self.applier = None
        self.f_m = f_m
        self.L_train = None
        self.predicted_labels = None
        self.predicted_probs = None
        self.__labels = db.load_cache(AVAILABLE_LABELS)
        self.cardinality = len(self.__labels) - 1
        self.label_model = MajorityLabelVoter(cardinality=self.cardinality)
        feature_matrix = f_m.copy()

    def create_labeling_functions(self):
        features = self.get_features()
        self.create_simple_labeling_functions(features)
        self.create_advanced_labeling_functions(features)

    def create_simple_labeling_functions(self, features):
        for rule in self.rules:
            if rule.l1 != -2 and rule.l2 != -2:
                rule_name = translate_rule_name(
                    rule.name if rule.name else rule.id)
                lf = "def {}(x): return {} if {} else {}".format(
                    rule_name, rule.l1, replace_binop(self.wrap_lookup(rule.rule, features)), rule.l2)

                compiled = compile(lf, filename="<string>", mode="exec")
                exec(compiled)
                lfexec = locals()[rule_name]

                new_lf = LabelingFunction(name=rule_name, f=lfexec)

                self.labeling_functions.append(new_lf)

    def create_advanced_labeling_functions(self, features):
        for rule in self.rules:
            if rule.l1 == -2 or rule.l2 == -2:
                rule_name = translate_rule_name(
                    rule.name if rule.name else rule.id)
                lf = "def {}(x):\n{}".format(
                    rule_name, self.wrap_lookup(rule.rule, features))

                if lf.count('if') > lf.count('else'):
                    lf += '\n\treturn ABSTAIN'

                compiled = compile(lf, filename="<string>", mode="exec")
                exec(compiled)
                lfexec = locals()[rule_name]

                new_lf = LabelingFunction(name=rule_name, f=lfexec)
                self.labeling_functions.append(new_lf)

    def wrap_lookup(self, rule, features):
        for f in features:
            rule = rule.replace(f, 'lookup(x, "' + f + '", feature_matrix)')
        return rule

    def apply(self):
        i = -1
        while i < len(self.__labels) - 1:
            label = make_code_label(self.__labels[i]) + ' = ' + str(i)
            exec(label, globals())
            i += 1
        self.applier = PandasLFApplier(lfs=self.labeling_functions)
        self.L_train = self.applier.apply(self.f_m)

    def fit(self, verbose=True, n_epochs=500, log_freq=50, seed=123):
        self.label_model = LabelModel(
            cardinality=self.cardinality, verbose=verbose)
        self.label_model.fit(self.L_train, n_epochs=n_epochs,
                             log_freq=log_freq, seed=seed)

    def predict(self, tie_break_policy='abstain'):
        self.predicted_labels = self.f_m.index, self.label_model.predict(
            L=self.L_train, tie_break_policy=tie_break_policy)

    def predict_proba(self):
        self.predicted_probs = self.label_model.predict_proba(
            L=self.L_train)

    def fit_predict(self, verbose=True, n_epochs=500, log_freq=50, seed=123, tie_break_policy='abstain'):
        self.fit(cardinality=self.cardinality, verbose=verbose,
                 n_epochs=n_epochs, log_freq=log_freq, seed=seed)
        self.predict(tie_break_policy=tie_break_policy)

    def LF_analysis(self):
        return LFAnalysis(L=self.L_train, lfs=self.labeling_functions).lf_summary()

    def get_features(self):
        features = set()
        for r in self.rules:
            rp = RuleParser()
            rp.parse(r.rule)
            features = features.union(rp.features)
        return features
