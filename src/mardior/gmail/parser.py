from __future__ import annotations

import base64
from bs4 import BeautifulSoup


class EmailParser:
    @staticmethod
    def decode_data(data: str) -> str:
        if not data:
            return ""
        try:
            padded = data + "=" * (4 - len(data) % 4) if len(data) % 4 else data
            return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
        except Exception:
            return ""

    @staticmethod
    def extract_text_from_html(html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def extract_parts(parts: list, body: dict, mime_type: str) -> str:
        text = ""
        if mime_type == "text/plain":
            text = EmailParser.decode_data(body.get("data", ""))
        elif mime_type == "text/html":
            html = EmailParser.decode_data(body.get("data", ""))
            text = EmailParser.extract_text_from_html(html)

        for part in (parts or []):
            if "parts" in part:
                text += EmailParser.extract_parts(part["parts"], part.get("body", {}), part.get("mimeType", ""))
            elif part.get("mimeType") == "text/plain":
                text += EmailParser.decode_data(part.get("body", {}).get("data", ""))
            elif part.get("mimeType") == "text/html":
                html = EmailParser.decode_data(part.get("body", {}).get("data", ""))
                text += EmailParser.extract_text_from_html(html)

        return text

    @staticmethod
    def parse_message(msg: dict) -> dict:
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        body_text = EmailParser.extract_parts(
            payload.get("parts", []),
            payload.get("body", {}),
            payload.get("mimeType", ""),
        ) or payload.get("snippet", "")

        return {
            "id": msg["id"],
            "thread_id": msg.get("threadId", ""),
            "from_name": (headers.get("From", "").split("<")[0].strip().strip('"') or ""),
            "from_address": "",
            "to_address": headers.get("To", ""),
            "subject": headers.get("Subject", "(Sin asunto)"),
            "body_text": body_text.strip() or msg.get("snippet", ""),
            "received_at": headers.get("Date", ""),
        }

    @staticmethod
    def extract_email_from_header(from_header: str) -> str:
        if "<" in from_header:
            return from_header.split("<")[1].rstrip(">")
        return from_header.strip()
