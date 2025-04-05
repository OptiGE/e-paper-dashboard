import os
import json
import time
import requests
import base64

class VasttrafikClient:
    TOKEN_URL = "https://ext-api.vasttrafik.se/token"
    TOKEN_CACHE_FILE = "vasttrafik_token.json"

    def __init__(self, auth_key_b64):
        self.auth_key_b64 = auth_key_b64
        self.access_token = None
        self.token_expiry = 0
        self._load_token_from_file()

    def _load_token_from_file(self):
        if os.path.exists(self.TOKEN_CACHE_FILE):
            with open(self.TOKEN_CACHE_FILE, "r") as f:
                try:
                    data = json.load(f)
                    if time.time() < data["expires_at"]:
                        self.access_token = data["access_token"]
                        self.token_expiry = data["expires_at"]
                except Exception:
                    pass  # ignore malformed file

    def _save_token_to_file(self):
        with open(self.TOKEN_CACHE_FILE, "w") as f:
            json.dump({
                "access_token": self.access_token,
                "expires_at": self.token_expiry
            }, f)

    def _fetch_access_token(self):
        print("Token expired, fetching new")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.auth_key_b64}"
        }
        data = {"grant_type": "client_credentials"}

        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expiry = time.time() + token_data["expires_in"] - 60
        self._save_token_to_file()

    def get_access_token(self):
        if not self.access_token or time.time() >= self.token_expiry:
            self._fetch_access_token()
        return self.access_token

    def get(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.get_access_token()}"
        return requests.get(url, headers=headers, **kwargs)
