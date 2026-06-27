from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import httpx
from mardior.config.settings import settings
from mardior.db.storage import Storage


class ShopifySyncer:
    def __init__(self, token: str = ""):
        self.shop = settings.shopify_shop
        self.token = token
        self.api_version = settings.shopify_api_version
        self.storage = Storage()

    @property
    def graphql_url(self) -> str:
        return f"https://{self.shop}/admin/api/{self.api_version}/graphql.json"

    async def _query(self, query: str, variables: dict = None) -> dict:
        if not self.token or not self.shop:
            return {}

        async with httpx.AsyncClient() as client:
            r = await client.post(
                self.graphql_url,
                headers={
                    "X-Shopify-Access-Token": self.token,
                    "Content-Type": "application/json",
                },
                json={"query": query, "variables": variables or {}},
            )
            r.raise_for_status()
            return r.json()

    async def sync_orders(self, days_back: int = 30) -> int:
        if not self.token or not self.shop:
            self.storage.log_sync("shopify_orders", 0, False, "Shopify no configurado. Agrega SHOPIFY_SHOP y token en .env")
            return 0

        date_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        query = """
        query($query: String!) {
            orders(first: 250, query: $query) {
                edges {
                    node {
                        id
                        name
                        displayFulfillmentStatus
                        displayFinancialStatus
                        createdAt
                        updatedAt
                        totalPriceSet { presentmentMoney { amount currencyCode } }
                        customer { firstName lastName email }
                        lineItems(first: 50) {
                            edges { node { name quantity sku originalUnitPriceSet { presentmentMoney { amount } } } }
                        }
                        fulfillments(first: 10) {
                            trackingInfo { company number }
                            status
                            createdAt
                        }
                    }
                }
            }
        }
        """
        variables = {"query": f"created_at:>={date_from}"}
        data = await self._query(query, variables)
        orders = data.get("data", {}).get("orders", {}).get("edges", [])

        count = 0
        for edge in orders:
            node = edge["node"]
            order_data = {
                "shopify_id": node["id"],
                "order_number": int(node["name"].lstrip("#")),
                "customer_email": (node.get("customer") or {}).get("email", ""),
                "customer_name": f"{(node.get('customer') or {}).get('firstName', '')} {(node.get('customer') or {}).get('lastName', '')}".strip(),
                "total_price": float(node.get("totalPriceSet", {}).get("presentmentMoney", {}).get("amount", 0)),
                "currency": node.get("totalPriceSet", {}).get("presentmentMoney", {}).get("currencyCode", "USD"),
                "financial_status": node.get("displayFinancialStatus", ""),
                "fulfillment_status": node.get("displayFulfillmentStatus", ""),
                "created_at": node.get("createdAt"),
                "updated_at": node.get("updatedAt"),
            }
            self.storage.upsert_order(order_data)
            count += 1

        self.storage.log_sync("shopify_orders", count, True)
        return count
