from __future__ import annotations

from typing import Optional
import httpx
from mardior.config.settings import settings
from mardior.db.storage import Storage


class ShopifyShippingReader:
    def __init__(self, token: str = ""):
        self.shop = settings.shopify_shop
        self.token = token
        self.api_version = settings.shopify_api_version

    @property
    def graphql_url(self) -> str:
        return f"https://{self.shop}/admin/api/{self.api_version}/graphql.json"

    def _query(self, query: str, variables: dict = None) -> dict:
        if not self.token or not self.shop:
            return {}

        with httpx.Client() as client:
            r = client.post(
                self.graphql_url,
                headers={
                    "X-Shopify-Access-Token": self.token,
                    "Content-Type": "application/json",
                },
                json={"query": query, "variables": variables or {}},
            )
            r.raise_for_status()
            return r.json()

    def get_delivery_profiles(self) -> list[dict]:
        if not self.token:
            return []

        query = """
        {
            deliveryProfiles(first: 10) {
                edges {
                    node {
                        id
                        name
                        profileLocationGroups(first: 5) {
                            edges {
                                node {
                                    locationGroup {
                                        locations(first: 5) {
                                            nodes { name }
                                        }
                                    }
                                    locationGroupZones(first: 5) {
                                        edges {
                                            node {
                                                zone {
                                                    id
                                                    name
                                                    countries { code { countryCode } }
                                                }
                                                methodDefinitions(first: 10) {
                                                    edges {
                                                        node {
                                                            id
                                                            name
                                                            price {
                                                                amount
                                                                currencyCode
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        data = self._query(query)
        profiles = []
        for edge in data.get("data", {}).get("deliveryProfiles", {}).get("edges", []):
            profiles.append(edge["node"])
        return profiles
