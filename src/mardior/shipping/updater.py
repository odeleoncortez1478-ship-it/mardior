from __future__ import annotations

from typing import Optional
import httpx
from mardior.config.settings import settings
from mardior.db.storage import Storage


class ShippingUpdater:
    def __init__(self, token: str = ""):
        self.shop = settings.shopify_shop
        self.token = token
        self.api_version = settings.shopify_api_version
        self.storage = Storage()

    @property
    def graphql_url(self) -> str:
        return f"https://{self.shop}/admin/api/{self.api_version}/graphql.json"

    async def update_rate(self, profile_id: str, method_definition_id: str, new_price: float) -> dict:
        if not self.token or not self.shop:
            return {"success": False, "error": "Shopify no configurado. Agrega SHOPIFY_SHOP y token en .env"}

        mutation = """
        mutation deliveryProfileUpdate($id: ID!, $profile: DeliveryProfileInput!) {
            deliveryProfileUpdate(id: $id, profile: $profile) {
                profile { id name }
                userErrors { field message }
            }
        }
        """
        variables = {
            "id": profile_id,
            "profile": {
                "methodDefinitionsToUpdate": [
                    {
                        "id": method_definition_id,
                        "rateDefinition": {
                            "price": {"amount": new_price, "currencyCode": "USD"}
                        },
                    }
                ]
            },
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(
                self.graphql_url,
                headers={
                    "X-Shopify-Access-Token": self.token,
                    "Content-Type": "application/json",
                },
                json={"query": mutation, "variables": variables},
            )
            data = r.json()
            errors = data.get("data", {}).get("deliveryProfileUpdate", {}).get("userErrors", [])
            if errors:
                return {"success": False, "error": errors[0].get("message", "Error desconocido")}
            return {"success": True, "profile_id": profile_id, "new_price": new_price}

    async def apply_recommended_rate(self, rate_id: int) -> dict:
        with self.storage.get_session() as session:
            from mardior.db.schema import ShippingRate, ShippingProfile
            rate = session.query(ShippingRate).filter(ShippingRate.id == rate_id).first()
            if not rate or not rate.real_price:
                return {"success": False, "error": "Tarifa no encontrada o sin precio real"}
            profile = session.query(ShippingProfile).filter(ShippingProfile.id == rate.profile_id).first()
            if not profile:
                return {"success": False, "error": "Perfil de envio no encontrado"}
            return await self.update_rate(
                profile.shopify_profile_id,
                f"gid://shopify/DeliveryMethodDefinition/{rate.id}",
                rate.real_price,
            )
