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
import streamlit_extras.switch_page_button as switch_page
from yaml.loader import SafeLoader
import yaml
import streamlit_authenticator as stauth
from streamlit_extras.switch_page_button import switch_page
from util.session_constants import CURRENT_PAGE
from streamlit_extras.row import row


class AuthenticationService:
    def __init__(self) -> None:
        with open('./config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)

        self.authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
        )

        self.cookie_manager = self.authenticator.cookie_manager

    def authenticate(self, main=False):
        if main:
            self.name, self.authentication_status, self.username = self.authenticator.login(
                'Login', 'main')
        else:
            self.name, self.authentication_status, self.username = self.authenticator.login(
                'Login', 'sidebar')

    def showSidebar(self):
        if st.session_state["authentication_status"]:

            with st.sidebar:
                log_out_row = row([2,1], vertical_align='bottom')
                log_out_row.markdown('<div style="margin-bottom: 1rem"><div style="font-size: 14px; margin-bottom: 0.25rem">User</div><div style="background: white; border-radius: 0.5rem; padding: 0.5rem; display: flex; flex-grow: 1; color: black">' + st.session_state["username"] + '</div></div>', unsafe_allow_html=True)
                log_out_row.button('Logout', on_click=self.logout, use_container_width=True)

        elif st.session_state["authentication_status"] is False:
            st.sidebar.error('Username/password is incorrect')
        elif st.session_state["authentication_status"] is None:
            # login.authenticator.login('Login', 'sidebar')
            if st.session_state[CURRENT_PAGE] != 'Label_Maker_Home':
                switch_page('home')
            else:
                st.sidebar.warning('Please login before using the app')

    def logout(self):
        self.cookie_manager.delete(self.authenticator.cookie_name)
        st.session_state['logout'] = True
        st.session_state['name'] = None
        st.session_state['username'] = None
        st.session_state['authentication_status'] = None