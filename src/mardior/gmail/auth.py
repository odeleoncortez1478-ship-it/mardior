from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest
from mardior.config.settings import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
]


class GmailAuth:
    def __init__(self):
        self.creds_path: Path = settings.base_dir / settings.gmail_credentials_path
        self.token_path: Path = settings.base_dir / settings.gmail_token_path
        self._creds: Optional[Credentials] = None

    def _load_creds(self) -> Optional[Credentials]:
        if self.token_path.exists():
            self._creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            return self._creds
        return None

    def _save_creds(self, creds: Credentials):
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        creds_json = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes),
        }
        with open(self.token_path, "w") as f:
            json.dump(creds_json, f)

    def _refresh_if_expired(self):
        if self._creds and self._creds.expired and self._creds.refresh_token:
            self._creds.refresh(GoogleRequest())
            self._save_creds(self._creds)

    def get_access_token(self) -> str:
        self._load_creds()
        self._refresh_if_expired()
        if self._creds and self._creds.token:
            return self._creds.token
        creds = self._authorize()
        return creds.token

    async def get_access_token_async(self) -> str:
        self._load_creds()
        self._refresh_if_expired()
        if self._creds and self._creds.token:
            return self._creds.token
        creds = await asyncio.to_thread(self._authorize)
        return creds.token

    def _authorize(self) -> Credentials:
        self._load_creds()
        if self._creds and self._creds.token:
            self._refresh_if_expired()
            if self._creds.token:
                return self._creds

        if not self.creds_path.exists():
            raise FileNotFoundError(
                f"No se encontro {self.creds_path}.\n\n"
                "1. Ve a https://console.cloud.google.com/\n"
                "2. Crea un proyecto -> Gmail API -> Credenciales\n"
                "3. OAuth 2.0 Client ID -> Desktop application\n"
                "4. Descarga el JSON y guardalo como:\n"
                f"   {self.creds_path}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(self.creds_path), SCOPES)
        creds = flow.run_local_server(port=0)
        self._save_creds(creds)
        return creds

    def authorize(self) -> str:
        creds = self._authorize()
        return creds.token
