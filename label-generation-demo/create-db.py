#!/usr/bin/env python

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
import sys

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from yaml.loader import SafeLoader

import model.model as model

sqlite_location = os.getenv('SQLITE_DB_LOCATION')

engine = create_engine(
    'sqlite:///' + sqlite_location + '.sqlite'
)

if not database_exists(engine.url):
    print('Data base not existing')
    create_database(engine.url)
else:
    print('Data base existing')
    sys.exit(0)

creds = []
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

    creds = config['credentials']

# print(creds)
users = []
for username in creds['usernames']:
    users.append(model.User(id=username, name=creds['usernames'][username]
    ['name'], email=creds['usernames'][username]['email']))
connection = None
try:
    connection = engine.connect()
    print('Validating connection...')
    # results = connection.execute('select current_version()').fetchone()
    # print(results[0])

    print('Creating tables...')
    result = model.Base.metadata.create_all(engine)
    print(result)

    print('Inserting users...')
    with Session(engine) as session:
        existing_users = session.query(model.User).all()
        if len(existing_users) == 0:
            session.add_all(users)
            session.commit()
            print('Users created.')
        else:
            print('Some users may already exist.')
            for user in existing_users:
                print(user)
            # for users who are not in existing users list
            additional_users = [u for u in users if u not in existing_users]
            if len(additional_users) > 0:
                for user in additional_users:
                    session.add(user)
                    session.commit()
                    # print(user)
                print('Additional users created successfully.')
finally:
    if connection:
        connection.close()
        engine.dispose()
