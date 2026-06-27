from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import httpx
from mardior.config.settings import settings


class FedExTracker:
    AUTH_URL = "https://apis.fedex.com/oauth/token"
    TRACK_URL = "https://apis.fedex.com/track/v1/trackingnumbers"

    def __init__(self):
        self.api_key = settings.fedex_api_key
        self.secret_key = settings.fedex_secret_key
        self.account_number = settings.fedex_account_number
        self._token: Optional[str] = None

    def _get_token(self) -> str:
        if not self.api_key:
            return "demo"

        with httpx.Client() as client:
            r = client.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.secret_key,
                },
            )
            r.raise_for_status()
            return r.json()["access_token"]

    async def track(self, tracking_number: str) -> dict:
        if not self.api_key:
            return {
                "carrier": "fedex",
                "tracking_number": tracking_number,
                "status": "delivered",
                "status_description": "Entregado",
                "location": "Reynosa, TAM",
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "estimated_delivery": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "events": [
                    {"status": "Picked up", "location": "Nuevo Laredo, TAM", "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat()},
                    {"status": "In transit", "location": "Laredo, TX", "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat()},
                    {"status": "Delivered", "location": "Reynosa, TAM", "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat()},
                ],
            }

        token = self._get_token()
        async with httpx.AsyncClient() as client:
            r = await client.post(
                self.TRACK_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "trackingNumberInfo": {"trackingNumber": tracking_number},
                    "includeDetailedScans": True,
                },
            )
            r.raise_for_status()
            return self._parse_response(r.json())

    @staticmethod
    def _parse_response(data: dict) -> dict:
        output = data.get("output", {})
        complete = output.get("completeTrackResults", [{}])[0]
        track = complete.get("trackResults", [{}])[0]
        latest = track.get("latestStatusDetail", {})
        scans = track.get("scanEvents", [])
        return {
            "carrier": "fedex",
            "status": latest.get("code", "unknown"),
            "status_description": latest.get("description", ""),
            "location": scans[0].get("scanLocation", {}).get("city", "") if scans else "",
            "timestamp": scans[0].get("date", "") if scans else "",
            "estimated_delivery": track.get("estimatedDeliveryTimeWindow", {}).get("window", {}).get("begins", ""),
            "events": [
                {
                    "status": s.get("eventDescription", ""),
                    "location": s.get("scanLocation", {}).get("city", ""),
                    "timestamp": f"{s.get('date', '')} {s.get('time', '')}",
                }
                for s in scans
            ],
        }
