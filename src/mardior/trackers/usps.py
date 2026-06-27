from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import httpx
from mardior.config.settings import settings


class USPSTracker:
    AUTH_URL = "https://apis.usps.com/oauth2/v3/token"
    TRACK_URL = "https://apis.usps.com/tracking/v3/tracking"

    def __init__(self):
        self.client_id = settings.usps_client_id
        self.client_secret = settings.usps_client_secret
        self.mailer_id = settings.usps_mailer_id
        self._token: Optional[str] = None

    def _get_token(self) -> str:
        if not self.client_id:
            return "demo"

        with httpx.Client() as client:
            r = client.post(
                self.AUTH_URL,
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
            )
            r.raise_for_status()
            return r.json()["access_token"]

    async def track(self, tracking_number: str) -> dict:
        if not self.client_id:
            return {
                "carrier": "usps",
                "tracking_number": tracking_number,
                "status": "delivered",
                "status_description": "Delivered",
                "location": "Reynosa, TAM",
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "estimated_delivery": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "events": [
                    {"status": "Shipping Label Created", "location": "Monterrey, MX", "timestamp": (datetime.utcnow() - timedelta(days=5)).isoformat()},
                    {"status": "Arrived at USPS Facility", "location": "Laredo, TX", "timestamp": (datetime.utcnow() - timedelta(days=4)).isoformat()},
                    {"status": "Out for Delivery", "location": "Reynosa, TAM", "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat()},
                    {"status": "Delivered", "location": "Reynosa, TAM", "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat()},
                ],
            }

        token = self._get_token()
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.TRACK_URL}/{tracking_number}",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return self._parse_response(r.json())

    @staticmethod
    def _parse_response(data: dict) -> dict:
        events = data.get("events", [])
        return {
            "carrier": "usps",
            "status": data.get("status", "unknown"),
            "status_description": data.get("statusDescription", ""),
            "location": events[0].get("location", {}).get("city", "") if events else "",
            "timestamp": events[0].get("timestamp", "") if events else "",
            "estimated_delivery": data.get("expectedDeliveryDate", ""),
            "events": [
                {"status": e.get("eventDescription", ""), "location": e.get("location", {}).get("city", ""), "timestamp": e.get("timestamp", "")}
                for e in events
            ],
        }
