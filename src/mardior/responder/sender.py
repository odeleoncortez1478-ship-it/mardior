from __future__ import annotations

from mardior.gmail.client import GmailClient
from mardior.responder.templates import RESPONSE_TEMPLATES


class Responder:
    def __init__(self):
        self.gmail = GmailClient()
        self.store_name = "Mi Tienda"

    async def send_tracking_response(self, email: dict, tracking_data: dict, order: dict = None) -> str:
        status = tracking_data.get("status", "unknown")
        template_key = status if status in RESPONSE_TEMPLATES else "in_transit"

        context = {
            "customer_name": email.get("from_name", "Cliente"),
            "customer_email": email.get("from_address", ""),
            "order_number": order.get("order_number", "") if order else "",
            "carrier": tracking_data.get("carrier", "").upper(),
            "tracking_number": tracking_data.get("tracking_number", ""),
            "delivery_date": tracking_data.get("estimated_delivery", "").split("T")[0] if tracking_data.get("estimated_delivery") else "",
            "location": tracking_data.get("location", ""),
            "estimated_delivery": tracking_data.get("estimated_delivery", "").split("T")[0] if tracking_data.get("estimated_delivery") else "",
            "exception_detail": tracking_data.get("status_description", ""),
            "store_name": self.store_name,
        }

        body = RESPONSE_TEMPLATES.get(template_key, RESPONSE_TEMPLATES["in_transit"]).format(**context)

        await self.gmail.send_message(
            to=email["from_address"],
            subject=email.get("subject", ""),
            body=body,
            thread_id=email.get("thread_id"),
            in_reply_to=email.get("gmail_message_id"),
        )

        return body
