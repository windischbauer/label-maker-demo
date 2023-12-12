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

import datetime
import json
import uuid

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import DateTime

Base = declarative_base()


def generate_id(): return str(uuid.uuid4())


class Rule(Base):
    __tablename__ = 'rule'

    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String)
    rule = Column(String, nullable=False)
    l1 = Column(Integer, nullable=True)
    l2 = Column(Integer, nullable=True)
    ruleset_id = Column(String, ForeignKey('ruleset.id'), nullable=False)

    ruleset = relationship("RuleSet", back_populates="rules", lazy='noload')

    def __repr__(self):
        return "<Rule(id='%s', rule='%s', l1='%s', l2='%s')>" % (
            self.id,
            self.rule,
            self.l1,
            self.l2)

    def toJSON(self):
        return {
            self.id: {
                'name': self.name,
                'rule': self.rule,
                'l1': self.l1,
                'l2': self.l2
            }
        }


class RuleSet(Base):
    __tablename__ = 'ruleset'

    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey('user.id'))
    labeling_task_id = Column(String, ForeignKey(
        'labeling_task.id'), nullable=False)

    rules = relationship("Rule", back_populates="ruleset",
                         cascade="all, delete-orphan", lazy='noload')
    user = relationship("User", back_populates="rulesets", lazy='noload')
    labeling_task = relationship(
        "LabelingTask", back_populates="rulesets", lazy='noload')

    labeling_results = relationship(
        "LabelingResult", back_populates="ruleset", lazy='noload')

    def __repr__(self):
        return "<RuleSet(id='%s', name='%s', rules='%s', user='%s', labeling_task='%s')>" % (
            self.id,
            self.name,
            self.rules,
            self.user,
            self.labeling_task)


class User(Base):
    __tablename__ = 'user'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    rulesets = relationship("RuleSet", back_populates="user", lazy='noload')
    labeling_results = relationship(
        "LabelingResult", back_populates="user", lazy='noload')
    gold_labels = relationship(
        "GoldLabel", back_populates="user", lazy='noload')

    def __repr__(self):
        return "<User(id='%s', name='%s', rulesets='%s')>" % (
            self.id,
            self.name,
            self.rulesets)


class LabelingResult(Base):
    __tablename__ = 'labeling_result'

    id = Column(String, primary_key=True, default=generate_id)
    labeling_task_id = Column(String, ForeignKey(
        'labeling_task.id'), nullable=False)
    labeling_task = relationship(
        "LabelingTask", back_populates="labeling_results")

    ruleset_id = Column(String, ForeignKey('ruleset.id'), nullable=False)
    ruleset = relationship("RuleSet", back_populates="labeling_results")

    user_id = Column(String, ForeignKey('user.id'), nullable=False)
    user = relationship(
        "User", back_populates="labeling_results")

    date = Column(DateTime, nullable=False, default=datetime.datetime.now())
    rules = Column(String, nullable=True)
    properties = Column(String, nullable=True)
    results = Column(String, nullable=True)
    scores = Column(String, nullable=True)

    def __repr__(self):
        return "<LabelingResult(id='%s', labeling_task_id='%s', ruleset_id='%s', user_id='%s', date='%s', rules='%s', properties='%s', results='%s', scores='%s')>" % (
            self.id,
            self.labeling_task_id,
            self.ruleset_id,
            self.user_id,
            self.date,
            self.rules,
            self.properties,
            self.results,
            self.scores)

    def toJSON(self):
        return {
            'id': self.id,
            'labeling_task_id': self.labeling_task_id,
            'ruleset_id': self.ruleset_id,
            'user_id': self.user_id,
            'date': self.date,
            'rules': self.rules,
            'properties': self.properties,
            'results': self.results,
            'scores': self.scores
        }

    def jsonify_variants(self):
        self.properties = json.loads(self.properties)
        self.results = json.loads(self.results)
        self.scores = json.loads(self.scores)


class LabelingTask(Base):
    __tablename__ = 'labeling_task'

    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False, unique=True)
    data_url = Column(String, nullable=False)
    time_series_path = Column(String, nullable=False)
    labels = Column(String, nullable=False)

    rulesets = relationship(
        "RuleSet", back_populates="labeling_task", lazy='noload')

    labeling_results = relationship(
        "LabelingResult", cascade="all, delete-orphan", back_populates="labeling_task", lazy='noload')

    gold_labels = relationship(
        "GoldLabel", cascade="all, delete-orphan", back_populates="labeling_task", lazy='noload')

    def __repr__(self):
        return "<LabelingTask(id='%s', name='%s', data_url='%s', time_series_path='%s', rulesets='%s', labels='%s'>" % (
            self.id,
            self.name,
            self.data_url,
            self.time_series_path,
            self.rulesets,
            self.labels)


class GoldLabel(Base):
    __tablename__ = 'gold_label'
    __table_args__ = (
        UniqueConstraint('labeling_task_id', 'time_series_key', name='unique_labeling_task_id_time_series_key'),
    )

    id = Column(String, primary_key=True, default=generate_id)
    labeling_task_id = Column(String, ForeignKey(
        'labeling_task.id'), nullable=False)
    labeling_task = relationship(
        "LabelingTask", back_populates="gold_labels")
    time_series_key = Column(String, nullable=False)
    label = Column(Integer, nullable=False)
    user_id = Column(String, ForeignKey('user.id'), nullable=False)
    user = relationship(
        "User", back_populates="gold_labels", lazy='noload')

    def __repr__(self):
        return "<GoldLabel(id='%s', labeling_task_id='%s', time_series_key='%s', label='%s', user='%s')>" % (
            self.id,
            self.labeling_task_id,
            self.time_series_key,
            self.label,
            self.user)
