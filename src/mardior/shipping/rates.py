from __future__ import annotations

from typing import Optional
import httpx
from mardior.config.settings import settings


class CarrierRates:
    def __init__(self):
        self.ups_creds = (settings.ups_client_id, settings.ups_client_secret)
        self.fedex_creds = (settings.fedex_api_key, settings.fedex_secret_key)
        self.usps_creds = (settings.usps_client_id, settings.usps_client_secret)

    async def get_ups_rate(self, destination_country: str, weight_kg: float) -> Optional[float]:
        if not self.ups_creds[0]:
            return self._mock_rate(destination_country)
        return self._mock_rate(destination_country)

    async def get_fedex_rate(self, destination_country: str, weight_kg: float) -> Optional[float]:
        if not self.fedex_creds[0]:
            return self._mock_rate(destination_country, offset=-0.5)
        return self._mock_rate(destination_country, offset=-0.5)

    async def get_usps_rate(self, destination_country: str, weight_kg: float) -> Optional[float]:
        if not self.usps_creds[0]:
            return self._mock_rate(destination_country, offset=-2.0)
        return self._mock_rate(destination_country, offset=-2.0)

    async def get_all_rates(self, destination_country: str, weight_kg: float = 1.0) -> dict:
        results = {}
        carriers = [
            ("UPS", self.get_ups_rate),
            ("FedEx", self.get_fedex_rate),
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

    @staticmethod
    def _mock_rate(country: str, offset: float = 0) -> float:
        base_rates = {
            "MX": 15.0,
            "MEX": 15.0,
            "México": 15.0,
            "US": 12.0,
            "USA": 12.0,
            "Estados Unidos": 12.0,
            "CA": 18.0,
            "CAN": 18.0,
            "Canadá": 18.0,
            "Canada": 18.0,
        }
        base = base_rates.get(country.upper(), 25.0) if country else 15.0
        return round(base + offset, 2)
