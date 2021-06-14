"""Connector module."""
import json
import logging
import pickle
import time
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .constants import API_ME_URL, CSRF_URL, TOKEN_URL

logger = logging.getLogger(__name__)


class OcConnector:
    def __init__(self, username=None, password=None):
        """Constructor"""
        self._access_token = None

        # HTTP strategy: retry on 429
        retry_strategy = Retry(
            total=3, status_forcelist=[429], method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Google Chrome"})

        if not self.load_token():
            self._authenticate(username, password)
            self.save_token()

        logger.info("!! Logged in.")

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, val):
        """Updates the requests headers when setting the access token"""
        self._access_token = val
        self.session.headers.update({"Authorization": "Bearer {}".format(val)})

    def save_token(self):
        with open("token.json", "w") as fp:
            expires = datetime.now() + timedelta(seconds=3500)
            data = {
                "token": self.access_token,
                "user_id": self.user_id,
                "expires": expires.isoformat(),
            }
            json.dump(data, fp)

        with open("cookies.dat", "wb") as fp:
            pickle.dump(self.session.cookies, fp)

    def load_token(self):
        try:
            with open("token.json", "r") as fp:
                data = json.load(fp)

                if datetime.fromisoformat(data["expires"]) < datetime.now():
                    raise FileNotFoundError

                self.access_token = data["token"]
                self.user_id = data["user_id"]

            with open("cookies.dat", "rb") as fp:
                self.session.cookies = pickle.load(fp)

            return True
        except FileNotFoundError:
            return False

    def _authenticate(self, username, password):
        """
        Tries to authenticate.
        Raises RuntimeError if it fails.
        """

        # CSRF token
        logger.info("-> Fetching CSRF token...")
        resp = self.session.get(CSRF_URL)
        data = resp.json()
        csrf = data["csrf"]

        # Build auth payload
        data = {
            "_username": username,
            "_password": password,
            "state": csrf,
        }

        logger.info("-> Logging in...")

        # Not sure why, but it seems to be needed
        time.sleep(0.2)

        # Post data
        self.session.post(TOKEN_URL, data=data)

        # We did not find the `access_token` cookie. :sad:
        if "access_token" not in self.session.cookies.get_dict():
            return False

        # Update the token
        self.access_token = self.session.cookies["access_token"]

        user_data = self.session.get(API_ME_URL).json()
        self.user_id = user_data["id"]

        logger.info(f" <- Got user ID: {self.user_id} - OK!")

        return True

    def get(self, url, *args, **kwargs):
        params_str = ",".join([f"{k}={v}" for k, v in kwargs.get("params", {}).items()])
        logger.info(f"-> Accessing {url} ({params_str})")
        return self.session.get(url, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def close(self):
        self.session.close()
