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

import os

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import util.annotations.benchmark as b
import util.annotations.logger as l


@l.log
@b.benchmark
@st.cache_resource(ttl=3600)
def connect_db():
    """
    Connects to the database and returns a connection object.

    Returns:
        connection: A connection object to interact with the database.
    """
    sqlite_location = os.getenv('SQLITE_DB_LOCATION')
    print('Sqlite location')
    print(sqlite_location)

    engine = create_engine(
        'sqlite:///' + sqlite_location + '.sqlite?check_same_thread=False'
    )

    try:
        connection = engine.connect()
        return connection
    finally:
        # connection.close()
        # engine.dispose()
        pass


@st.cache_resource(ttl=3600)
def get_session():
    """
    Returns a session object for interacting with the database.

    :return: Session object
    """
    return sessionmaker(bind=connect_db(), expire_on_commit=False)
