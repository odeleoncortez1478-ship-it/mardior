from __future__ import annotations

from typing import Optional

import httpx

from mardior.config.settings import settings


class CarrierRates:
    def __init__(self):
        self.ups_creds = (settings.ups_client_id, settings.ups_client_secret)
        self.usps_creds = (settings.usps_client_id, settings.usps_client_secret)

    async def get_ups_rate(self, destination_country: str, weight_kg: float = 1.0) -> Optional[float]:
        if not all(self.ups_creds):
            return None

        use_sandbox = settings.ups_use_sandbox
        base_url = "https://wwwcie.ups.com" if use_sandbox else "https://onlinetools.ups.com"

        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    f"{base_url}/security/v1/oauth/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.ups_creds[0],
                        "client_secret": self.ups_creds[1],
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if token_resp.status_code != 200:
                    return None
                token = token_resp.json().get("access_token")

                rate_payload = {
                    "RateRequest": {
                        "Shipment": {
                            "Shipper": {"ShipperNumber": ""},
                            "ShipTo": {
                                "Address": {
                                    "CountryCode": destination_country[:2].upper(),
                                }
                            },
                            "ShipFrom": {
                                "Address": {"CountryCode": "US"}
                            },
                            "Package": {
                                "PackagingType": {"Code": "02"},
                                "PackageWeight": {
                                    "UnitOfMeasurement": {"Code": "KGS"},
                                    "Weight": str(weight_kg),
                                },
                            },
                        }
                    }
                }
                rate_resp = await client.post(
                    f"{base_url}/api/rating/v2205/Rate",
                    json=rate_payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "transId": "mardior-rate",
                    },
                )
                if rate_resp.status_code != 200:
                    return None
                data = rate_resp.json()
                total_charge = (
                    data.get("RateResponse", {})
                    .get("RatedShipment", [{}])[0]
                    .get("TotalCharges", {})
                    .get("MonetaryValue", "0")
                )
                return round(float(total_charge), 2)
        except Exception:
            return None

    async def get_usps_rate(self, destination_country: str, weight_kg: float = 1.0) -> Optional[float]:
        if not all(self.usps_creds):
            return None

        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://api.usps.com/oauth2/v3/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.usps_creds[0],
                        "client_secret": self.usps_creds[1],
                    },
                )
                if token_resp.status_code != 200:
                    return None
                token = token_resp.json().get("access_token")

                weight_oz = round(weight_kg * 35.274, 1)
                rate_resp = await client.post(
                    "https://api.usps.com/prices/v3/priority-mail",
                    json={
                        "originZIPCode": "77001",
                        "destinationZIPCode": destination_country[:5],
                        "weight": weight_oz,
                        "mailClass": "PRIORITY_MAIL",
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
                if rate_resp.status_code != 200:
                    return None
                data = rate_resp.json()
                return float(data.get("totalRate", 0) or 0)
        except Exception:
            return None

    async def get_all_rates(self, destination_country: str, weight_kg: float = 1.0) -> dict:
        results = {}
        carriers = [
            ("UPS", self.get_ups_rate),
            ("USPS", self.get_usps_rate),
        ]
        for name, func in carriers:
            try:
                rate = await func(destination_country, weight_kg)
                if rate:
                    results[name] = rate
            except Exception:
                pass
        return results
