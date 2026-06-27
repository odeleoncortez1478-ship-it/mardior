from __future__ import annotations

import base64
from datetime import datetime, timedelta
from typing import Optional
import httpx
from mardior.config.settings import settings


class UPSTracker:
    TOKEN_URL_TEST = "https://wwwcie.ups.com/security/v1/oauth/token"
    TOKEN_URL_PROD = "https://onlinetools.ups.com/security/v1/oauth/token"
    TRACK_URL_TEST = "https://wwwcie.ups.com/api/track/v1/details"
    TRACK_URL_PROD = "https://onlinetools.ups.com/api/track/v1/details"

    def __init__(self):
        self.client_id = settings.ups_client_id
        self.client_secret = settings.ups_client_secret
        self.sandbox = settings.ups_use_sandbox
        self._token: Optional[str] = None
        self._token_expires: datetime = datetime.min

    @property
    def token_url(self) -> str:
        return self.TOKEN_URL_TEST if self.sandbox else self.TOKEN_URL_PROD

    @property
    def track_url(self) -> str:
        return self.TRACK_URL_TEST if self.sandbox else self.TRACK_URL_PROD

    def _get_token(self) -> str:
        if self._token and datetime.utcnow() < self._token_expires:
            return self._token

        if not self.client_id:
            return "demo"

        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        with httpx.Client() as client:
            r = client.post(
                self.token_url,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            r.raise_for_status()
            data = r.json()
            self._token = data["access_token"]
            self._token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 14400) - 60)
            return self._token

    async def track(self, tracking_number: str) -> dict:
        if not self.client_id:
            return {
                "carrier": "ups",
                "tracking_number": tracking_number,
                "status": "in_transit",
                "status_description": "En tránsito",
                "location": "Laredo, TX",
                "timestamp": datetime.utcnow().isoformat(),
                "estimated_delivery": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                "events": [
                    {"status": "Origin Scan", "location": "Monterrey, MX", "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat()},
                    {"status": "Departure Scan", "location": "Monterrey, MX", "timestamp": (datetime.utcnow() - timedelta(hours=20)).isoformat()},
                    {"status": "Arrival", "location": "Laredo, TX", "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()},
                ],
            }

        token = self._get_token()
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.track_url}/{tracking_number}",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return self._parse_response(r.json())

    @staticmethod
    def _parse_response(data: dict) -> dict:
        shipment = data.get("trackResponse", {}).get("shipment", [{}])[0]
        package = shipment.get("package", [{}])[0]
        activity = package.get("activity", [{}])
        current_status = package.get("currentStatus", {})
        return {
            "carrier": "ups",
            "status": current_status.get("type", "unknown"),
            "status_description": current_status.get("description", ""),
            "location": activity[0].get("location", {}).get("address", {}).get("city", "") if activity else "",
            "timestamp": activity[0].get("date", "") if activity else "",
            "estimated_delivery": shipment.get("estimatedDeliveryDate", {}).get("date", ""),
            "events": [
                {
                    "status": e.get("status", {}).get("description", ""),
                    "location": e.get("location", {}).get("address", {}).get("city", ""),
                    "timestamp": f"{e.get('date', '')} {e.get('time', '')}",
                }
                for e in activity
            ],
        }
