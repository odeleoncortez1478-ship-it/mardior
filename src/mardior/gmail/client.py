from __future__ import annotations

import base64
from email.mime.text import MIMEText
from typing import Optional
import httpx
from mardior.gmail.auth import GmailAuth


class GmailClient:
    BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

    def __init__(self):
        self.auth = GmailAuth()
        self._token: Optional[str] = None

    async def _ensure_token(self):
        if not self._token:
            self._token = await self.auth.get_access_token_async()

    async def _headers(self):
        await self._ensure_token()
        return {"Authorization": f"Bearer {self._token}"}

    async def list_messages(self, query: str = "is:unread", max_results: int = 50) -> list:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.BASE}/messages",
                headers=await self._headers(),
                params={"q": query, "maxResults": max_results},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("messages", [])

    async def get_message(self, msg_id: str, fmt: str = "full") -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.BASE}/messages/{msg_id}",
                headers=await self._headers(),
                params={"format": fmt},
            )
            r.raise_for_status()
            return r.json()

    async def modify_message(self, msg_id: str, add_labels: list[str] = None, remove_labels: list[str] = None):
        body = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.BASE}/messages/{msg_id}/modify",
                headers=await self._headers(),
                json=body,
            )
            r.raise_for_status()

    async def send_message(self, to: str, subject: str, body: str, thread_id: str = None, in_reply_to: str = None, references: str = None):
        msg = MIMEText(body, "plain", "utf-8")
        msg["To"] = to
        msg["Subject"] = f"Re: {subject}" if subject.startswith("Re:") else subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
        if references:
            msg["References"] = references

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        payload = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.BASE}/messages/send",
                headers=await self._headers(),
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    async def list_labels(self) -> list:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.BASE}/labels", headers=await self._headers())
            r.raise_for_status()
            return r.json().get("labels", [])

    async def create_label(self, name: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.BASE}/labels",
                headers=await self._headers(),
                json={
                    "name": name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            )
            r.raise_for_status()
            return r.json()

    # Keep sync versions for token loading
    def get_token_sync(self) -> str:
        if not self._token:
            self._token = self.auth.get_access_token()
        return self._token
