from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

from mardior.config.settings import settings
from mardior.db.storage import Storage


class ReadyCloudAuth:
    def __init__(self):
        self.client_id = settings.readycloud_client_id
        self.client_secret = settings.readycloud_client_secret
        self.token_path = settings.base_dir / "credentials" / "readycloud_token.json"

    def _load_token(self) -> Optional[dict]:
        if self.token_path.exists():
            return json.loads(self.token_path.read_text())
        return None

    def _save_token(self, token: dict):
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(token, indent=2))

    async def get_access_token(self) -> Optional[str]:
        token = self._load_token()
        if token and token.get("access_token"):
            return token["access_token"]

        if not self.client_id or not self.client_secret:
            return None

        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://www.readycloud.com/api/v2/token/",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "order tracking_number",
                },
            )
            if r.status_code != 200:
                return None
            data = r.json()
            self._save_token(data)
            return data.get("access_token")


class ReadyCloudSyncer:
    def __init__(self):
        self.org_pk = settings.readycloud_org_pk
        self.api_version = settings.readycloud_api_version
        self.auth = ReadyCloudAuth()
        self.storage = Storage()
        self.base_url = f"https://www.readycloud.com/api/{self.api_version}/orgs/{self.org_pk}"

    async def _get(self, path: str) -> dict:
        token = await self.auth.get_access_token()
        if not token:
            return {}
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code != 200:
                return {}
            return r.json()

    async def sync_orders(self, days_back: int = 30) -> int:
        if not self.org_pk:
            self.storage.log_sync("readycloud_orders", 0, False, "ReadyCloud no configurado. Agrega READYCLOUD_ORG_PK en .env")
            return 0

        date_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        data = await self._get(f"/orders/?created_at__gte={date_from}")
        results = data.get("results", [])

        count = 0
        for rc_order in results:
            order_data = self._map_order(rc_order)
            order = self.storage.upsert_order(order_data)
            self._sync_items(order, rc_order)
            self._sync_fulfillments(order, rc_order)
            count += 1

        self.storage.log_sync("readycloud_orders", count, True)
        return count

    def _map_order(self, rc: dict) -> dict:
        shipping = rc.get("shipping", {}) or {}
        billing = rc.get("billing", {}) or {}
        ship_to = shipping.get("ship_to", {}) or {}

        status_map = {
            "unshipped": "unfulfilled",
            "unfulfilled": "unfulfilled",
            "fulfilled": "fulfilled",
            "partially_fulfilled": "partial",
        }
        fulfillment_status = status_map.get(
            (shipping.get("status") or "").lower(), shipping.get("status", "unfulfilled")
        )

        return {
            "readycloud_id": str(rc.get("id", "")),
            "source": "readycloud",
            "order_number": int(rc.get("order_number", 0)),
            "customer_email": (ship_to.get("email") or ""),
            "customer_name": (ship_to.get("name") or ""),
            "total_price": float(billing.get("total", 0) or 0),
            "currency": (billing.get("currency", "USD") or "USD"),
            "financial_status": (billing.get("status", "paid") or "paid"),
            "fulfillment_status": fulfillment_status,
            "shipping_price": float(shipping.get("ship_cost", 0) or 0),
            "created_at": rc.get("created_at"),
            "updated_at": rc.get("updated_at"),
        }

    def _sync_items(self, order: object, rc: dict):
        items = rc.get("items") or []
        if not items:
            return

        with self.storage.get_session() as session:
            existing = {i.sku or i.product_title: i for i in (order.items or [])}
            for rc_item in items:
                sku = rc_item.get("sku", "") or ""
                title = rc_item.get("title", rc_item.get("product_id", ""))
                existing_item = existing.get(sku) or existing.get(title)
                if existing_item:
                    existing_item.quantity = int(rc_item.get("quantity", 1))
                    existing_item.price = float(rc_item.get("price", 0))
                else:
                    session.add(OrderItem(
                        order_id=order.id,
                        product_title=title,
                        quantity=int(rc_item.get("quantity", 1)),
                        price=float(rc_item.get("price", 0)),
                        sku=sku,
                    ))
            session.commit()

    def _sync_fulfillments(self, order: object, rc: dict):
        boxes = rc.get("boxes") or []
        if not boxes:
            return

        with self.storage.get_session() as session:
            existing_tns = {f.tracking_number: f for f in (order.fulfillments or []) if f.tracking_number}
            for box in boxes:
                tracking = box.get("tracking") or {}
                tracking_number = tracking.get("tracking_number", box.get("tracking_number", ""))
                if not tracking_number:
                    continue
                carrier = (tracking.get("carrier_code") or box.get("ship_via", "") or "").lower()
                carrier_map = {"ups": "ups", "usps": "usps", "fedex": "fedex"}
                carrier = carrier_map.get(carrier, carrier)

                if tracking_number in existing_tns:
                    continue

                session.add(Fulfillment(
                    order_id=order.id,
                    tracking_number=tracking_number,
                    carrier=carrier,
                    status="pending",
                ))
            session.commit()
