from __future__ import annotations

import asyncio
from datetime import datetime
from email.utils import parsedate_to_datetime
from mardior.gmail.client import GmailClient
from mardior.gmail.parser import EmailParser
from mardior.db.storage import Storage


class GmailPoller:
    def __init__(self):
        self.gmail = GmailClient()
        self.parser = EmailParser()
        self.storage = Storage()

    async def poll(self):
        messages = await asyncio.to_thread(self.gmail.list_messages, "is:unread", 50)
        new_count = 0

        for msg_summary in messages:
            msg_id = msg_summary["id"]

            if self.storage.get_email_by_gmail_id(msg_id):
                continue

            full_msg = await asyncio.to_thread(self.gmail.get_message, msg_id)
            parsed = self.parser.parse_message(full_msg)
            parsed["from_address"] = self.parser.extract_email_from_header(
                next((h["value"] for h in full_msg.get("payload", {}).get("headers", []) if h["name"] == "From"), "")
            )

            try:
                if parsed["received_at"]:
                    parsed["received_at"] = parsedate_to_datetime(parsed["received_at"])
                else:
                    parsed["received_at"] = datetime.utcnow()
            except Exception:
                parsed["received_at"] = datetime.utcnow()

            self.storage.insert_email(parsed)
            new_count += 1

        return new_count
