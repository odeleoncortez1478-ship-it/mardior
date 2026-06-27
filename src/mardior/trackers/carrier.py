from __future__ import annotations

import re
from typing import Optional


TRACKING_PATTERNS = {
    "ups": [
        r"\b1Z\s?[A-Z0-9]{6}\s?\d{2}\s?[A-Z0-9]{4}\s?\d{2}\s?\d{1,2}\s?\d{1,2}\b",
        r"\b1Z[A-Z0-9]{14,18}\b",
    ],
    "fedex": [
        r"\b\d{12,15}\b",
        r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",
    ],
    "usps": [
        r"\b(?:94|92|93|91|82|70)\d{18,20}\b",
        r"\b[A-Z]{2}\d{9}US\b",
    ],
}

CARRIER_DOMAINS = {
    "ups.com": "ups",
    "ups": "ups",
    "fedex.com": "fedex",
    "fedex": "fedex",
    "usps.com": "usps",
    "usps": "usps",
    "stamps.com": "usps",
}


class CarrierDetector:
    @staticmethod
    def detect_by_domain(from_address: str) -> Optional[str]:
        for domain, carrier in CARRIER_DOMAINS.items():
            if domain in from_address.lower():
                return carrier
        return None

    @staticmethod
    def detect_by_tracking_number(text: str) -> Optional[str]:
        for carrier, patterns in TRACKING_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return carrier
        return None

    @staticmethod
    def extract_tracking_numbers(text: str) -> list[tuple[str, str]]:
        results = []
        for carrier, patterns in TRACKING_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    tn = match.group(0).replace(" ", "")
                    results.append((carrier, tn))
        return results
