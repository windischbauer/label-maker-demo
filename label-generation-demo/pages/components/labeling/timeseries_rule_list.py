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

from collections import deque

import altair as alt
import pandas as pd
import streamlit as st
from streamlit_extras.row import row

import services.persistence_service as db
from model.model import GoldLabel
from util.session_constants import AVAILABLE_LABELS, SELECTED_LABELING_TASK
from util.string_convenience import display_labels


def update_l1(_self):
    if st.session_state.l1 == st.session_state.l2:
        st.session_state.l2 = _self.labels[0]


def update_l2(_self):
    if st.session_state.l1 == st.session_state.l2:
        st.session_state.l1 = _self.labels[0]


def shuffle_thumbs(_self):
    _self.shuffled_thumbs = []
    for i in range(len(_self.label_set)):
        _self.shuffled_thumbs.append(
            _self.label_set[i].sample(frac=1) if len(_self.label_set[i]) > 0 else pd.DataFrame())
    db.cache(_self.shuffled_thumbs, 'SHUFFLED_THUMBS')


class TimeseriesRuleList:
    def __init__(self, rule, label_set, negated_rule=None, edit_rule=None, free_form=False) -> None:
        self.rule = rule
        if AVAILABLE_LABELS in st.session_state:
            self.labels = deque(st.session_state[AVAILABLE_LABELS])
            self.labels.rotate(1)
            self.labels = list(self.labels)
        # self.labels = labels
        self.negated_rule = negated_rule
        self.l1 = None
        self.l2 = None
        self.label_set = label_set
        self.display_thumbs = False
        self.thumb_count = 5
        cached_st = db.load_cache('SHUFFLED_THUMBS')
        if cached_st is None:
            self.shuffled_thumbs = label_set
        else:
            self.shuffled_thumbs = cached_st
            for i in range(len(cached_st)):
                if label_set is not None:
                    if len(cached_st[i]) != len(label_set[i]):
                        shuffle_thumbs(self)
                        break
        self.edit_rule = edit_rule
        self.free_form = free_form
        filter_gl = GoldLabel.labeling_task_id == st.session_state[
            SELECTED_LABELING_TASK].id
        self.gold_labels = db.load(GoldLabel, filter=filter_gl)

    def show(self):
        thumb_row = row(4, vertical_align='bottom')

        self.display_thumbs = thumb_row.toggle(
            label="Display thumbnails",
            key="switch_1",
            value=self.display_thumbs,
            help='You can choose to view thumbnails of different time series. To gain a wider view over the available series you can shuffle them randomly. Should you change a value which results in a time series being moved between labels the displayed thumbnails are also shuffled.',
        )

        thumb_row.empty()

        if self.display_thumbs:
            self.thumb_count = thumb_row.number_input(
                label="Number of thumbnails to display",
                min_value=1,
                value=self.thumb_count,
                key="number_input_1",
            )

            thumb_row.button(
                label="Shuffle thumbnails", on_click=shuffle_thumbs, args=(self,), key="button_1",
                use_container_width=True)

        if not self.free_form:
            if len(self.label_set) == 2:
                col1, col2 = st.columns(2)
                self.show_two_cols(col1, col2)
        elif self.label_set is not None:
            cols = st.columns(len(self.labels))
            for i in range(len(cols)):
                cols[i].write(self.labels[i - len(self.labels) + 1])
            # if len(self.label_set) == 3:
            #     self.show_three_cols(cols[0], cols[1], cols[2])
            # else:
            self.show_x_cols(cols)

    def display_dots(self, set, match_set=None, no_match_set=None):
        dot_count = len(set)
        s = ''
        if match_set:
            match_count = len(match_set)
            for i in range(match_count):
                s += ':green[&#9679;] '
            dot_count -= match_count
        if no_match_set:
            no_match_count = len(no_match_set)
            for i in range(no_match_count):
                s += ':red[&#9679;] '
            dot_count -= no_match_count
        for i in range(dot_count):
            s += '&#9679; '
        return s

    def show_x_cols(self, cols):
        for i in range(len(cols)):
            j = i
            if j == len(cols) - 1:
                j = -1
            match_set = []
            no_match_set = []

            for gl in self.gold_labels:
                if int(gl.time_series_key) in self.label_set[i].index.values:
                    if gl.label == j:
                        match_set.append(gl.time_series_key)
                    else:
                        no_match_set.append(gl.time_series_key)

            col = cols[i]
            self.show_col(self.label_set[i], self.shuffled_thumbs[i], 'black', col, match_set, no_match_set)

    def show_three_cols(self, col1, col2, col3):
        self.show_col(self.label_set[0], self.shuffled_thumbs[0], 'black', col1)
        self.show_col(self.label_set[1], self.shuffled_thumbs[1], 'black', col2)
        self.show_col(self.label_set[2], self.shuffled_thumbs[2], 'black', col3)

    def show_col(self, label_set, thumb_set, color, col, match_set=None, no_match_set=None):
        if self.display_thumbs:
            with col.container():
                self.display_ts(thumb_set, match_set, no_match_set)
        c_s = self.display_dots(label_set, match_set, no_match_set)
        col.write(':' + color + '[' + c_s + ']')

    def show_two_cols(self, col1, col2):

        ol1 = col1.selectbox(
            'Select label',
            options=self.labels,
            key='l1',
            index=1 if not self.edit_rule else self.edit_rule.l1 + 1,
            format_func=display_labels,
            on_change=update_l1,
            args=(self,)
        )
        self.l1 = self.labels.index(ol1) - 1

        col1.write('for: ' + self.rule)

        ol2 = col2.selectbox(
            'Select label',
            options=self.labels,
            key='l2',
            index=2 if not self.edit_rule else self.edit_rule.l2 + 1,
            format_func=display_labels,
            on_change=update_l2,
            args=(self,)
        )
        self.l2 = self.labels.index(ol2) - 1

        if self.negated_rule is not None:
            col2.write('for: ' + self.negated_rule)
        else:
            col2.write('for: not (' + self.rule + ')')

        # dot_row = row(2 if not self.display_thumbs else 4, vertical_align='top')

        if len(self.label_set[0]) > 0 or len(self.label_set[1]) > 0:
            match_set1 = []
            no_match_set1 = []
            match_set2 = []
            no_match_set2 = []
            for gl in self.gold_labels:
                if int(gl.time_series_key) in self.label_set[0].index.values:
                    if self.l1 == gl.label:
                        match_set1.append(gl.time_series_key)
                    else:
                        no_match_set1.append(gl.time_series_key)
                if int(gl.time_series_key) in self.label_set[1].index.values:
                    if self.l2 == gl.label:
                        match_set2.append(gl.time_series_key)
                    else:
                        no_match_set2.append(gl.time_series_key)
            # st.write(match_set1)
            # st.write(no_match_set1)
            # st.write(match_set2)
            # st.write(no_match_set2)

            self.show_col(self.label_set[0], self.shuffled_thumbs[0], 'black', col1, match_set1, no_match_set1)
            self.show_col(self.label_set[1], self.shuffled_thumbs[1], 'black', col2, match_set2, no_match_set2)

    def display_ts(self, set, match_set=None, no_match_set=None):
        i = 0
        tsd = db.load_time_series_data()
        if tsd is None:
            return
        if len(set) == 0:
            return

        ts_data = tsd.data_dict.copy()

        while i < self.thumb_count and i < len(set):
            name = set.iloc[i].name
            i += 1
            if name not in ts_data:
                continue
            ts = ts_data[name]
            t = ts.fillna(0).copy()
            t = t.reset_index(drop=True)
            t = t.groupby(t.index // 20).mean()

            cname = t.columns[0]
            downsampled = t.rename(columns={cname: 'value'})
            downsampled['time_captured'] = downsampled.index
            # st.write(downsampled)
            title = str(name)
            color = "#3B65B5"
            if match_set:
                if str(name) in match_set:
                    color = "#3C8040"
                    title += ' matches the label'
            if no_match_set:
                if str(name) in no_match_set:
                    color = "#EA4339"
                    title += ' does not match the label'

            c = alt.Chart(downsampled).mark_line(color=color).encode(
                x=alt.X(
                    "time_captured:T", title="", axis=alt.Axis(labels=False)
                ),
                y=alt.Y('value', title="", type='quantitative',
                        axis=alt.Axis(labels=False)),
            ).properties(height=50, title=title).configure_title(
                anchor='start', offset=0, orient='top', fontSize=12)
            st.altair_chart(c, use_container_width=True)
