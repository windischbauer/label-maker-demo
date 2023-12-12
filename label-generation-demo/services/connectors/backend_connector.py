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
import xmlrpc.client

import streamlit as st


@st.cache_resource
def connect_server(restart=False):
    """
    Connects to the backend server and returns the server proxy object.

    Args:
        restart (bool, optional): Whether to restart the server. Defaults to False.
        
    Returns:
        xmlrpc.client.ServerProxy: The server proxy object.
    """
    backend_host = os.getenv('BACKEND_HOST')
    backend_port = os.getenv('BACKEND_PORT')
    server = xmlrpc.client.ServerProxy('http://' + backend_host + ':' + backend_port)
    if restart:
        server.restart()
    return server
