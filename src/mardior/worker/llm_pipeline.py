from __future__ import annotations

import asyncio
from datetime import datetime
from mardior.classifier.llm import LLMClassifier
from mardior.db.storage import Storage
from mardior.db.schema import ClassificationLog, Notification
from mardior.gmail.client import GmailClient
from mardior.notifications.sounds import SoundNotifier
from mardior.responder.sender import Responder
from mardior.trackers.carrier import CarrierDetector
from mardior.trackers.ups import UPSTracker
from mardior.trackers.fedex import FedExTracker
from mardior.trackers.usps import USPSTracker


class LLMPipeline:
    def __init__(self):
        self.classifier = LLMClassifier()
        self.storage = Storage()
        self.responder = Responder()
        self.sounds = SoundNotifier()
        self.gmail = GmailClient()
        self.trackers = {
            "ups": UPSTracker(),
            "fedex": FedExTracker(),
            "usps": USPSTracker(),
        }

    async def process_pending(self) -> dict:
        emails = self.storage.get_unprocessed_emails()
        stats = {"processed": 0, "classified": 0, "responded": 0, "notified": 0}

        for email in emails:
            result = await asyncio.to_thread(
                self.classifier.classify_structured, email.subject, email.from_address, email.body_text
            )

            self.storage.update_email(email.id, {
                "classification": result["category"],
                "summary": result["summary"],
                "needs_attention": result["needs_attention"],
                "attention_reason": result["attention_reason"],
                "processed_at": datetime.utcnow(),
            })

            with self.storage.get_session() as session:
                session.add(ClassificationLog(
                    email_id=email.id, model_used=self.classifier.model,
                    input_tokens=result["input_tokens"], output_tokens=result["output_tokens"], cost=result["cost"],
                    raw_prompt=f"Clasificar: {email.subject[:50]}",
                    raw_response=result["category"],
                ))
                session.commit()

            stats["classified"] += 1

            cat = result["category"]
            if cat == "tracking":
                await self._handle_tracking(email, stats)
            elif cat in ("influencer", "distributor", "partnership", "complaint", "refund"):
                self._handle_attention(email, stats, cat)
            elif cat == "ads":
                pass

            stats["processed"] += 1

        return stats

    async def _handle_tracking(self, email, stats: dict):
        order = None
        if email.linked_order_id:
            order = self.storage.get_order_by_id(email.linked_order_id)
        if not order:
            order = self.storage.get_order_by_email(email.from_address)

        if not order:
            await self.gmail.modify_message(email.gmail_message_id, add_labels=["INBOX"])
            response = self.responder.send_tracking_response(
                {"from_name": email.from_name, "from_address": email.from_address,
                 "subject": email.subject, "thread_id": email.thread_id,
                 "gmail_message_id": email.gmail_message_id},
                {"carrier": "desconocido", "status": "no_tracking", "tracking_number": "",
                 "estimated_delivery": "", "location": "",
                 "status_description": "No tenemos informacion de tracking"},
            )
            self.storage.update_email(email.id, {
                "response_sent": True, "response_body": response, "response_status": "sent",
            })
            stats["responded"] += 1
            return

        carrier_detect = CarrierDetector()
        tracking_numbers = carrier_detect.extract_tracking_numbers(email.body_text or "")
        carrier = carrier_detect.detect_by_domain(email.from_address)
        tracking_number = ""

        if not tracking_numbers:
            with self.storage.get_session() as session:
                order_obj = session.get(type(order), order.id)
                if order_obj:
                    for f in order_obj.fulfillments:
                        if f.tracking_number:
                            tracking_numbers.append((f.carrier, f.tracking_number))

        if tracking_numbers:
            carrier, tracking_number = tracking_numbers[0]

        self.storage.update_email(email.id, {"linked_order_id": order.id})

        tracking_data = None
        if carrier and tracking_number:
            tracker = self.trackers.get(carrier)
            if tracker:
                tracking_data = await tracker.track(tracking_number)
                self.storage.update_email(email.id, {
                    "tracking_fetched": True,
                    "tracking_status": tracking_data.get("status", "unknown"),
                })

        if not tracking_data:
            tracking_data = {"carrier": carrier or "desconocido", "status": "unknown",
                            "tracking_number": tracking_number, "estimated_delivery": "",
                            "location": "", "status_description": ""}

        items_str = ", ".join(
            f"{i.product_title} x{i.quantity}" for i in (order.items or [])
        ) if order.items else ""

        decision = await asyncio.to_thread(
            self.classifier.decide,
            email.from_name, email.from_address,
            email.subject, email.body_text,
            order.order_number,
            items_str, order.total_price,
            str(order.created_at) if order.created_at else "",
            tracking_data.get("carrier", ""),
            tracking_data.get("tracking_number", ""),
            tracking_data.get("status", ""),
            tracking_data.get("timestamp", ""),
        )

        if decision.get("action") in ("reply_customer", "escalate_owner"):
            response = await asyncio.to_thread(
                self.responder.send_tracking_response,
                {"from_name": email.from_name, "from_address": email.from_address,
                 "subject": email.subject, "thread_id": email.thread_id,
                 "gmail_message_id": email.gmail_message_id},
                tracking_data,
                {"order_number": order.order_number},
            )
            self.storage.update_email(email.id, {
                "response_sent": True, "response_body": response, "response_status": "sent",
            })
            stats["responded"] += 1

        if decision.get("notify_owner"):
            msg = decision.get("owner_message", f"Notificacion sobre orden #{order.order_number}")
            with self.storage.get_session() as session:
                session.add(Notification(
                    email_id=email.id, channel="sound",
                    message=msg, sent_at=datetime.utcnow(), success=True,
                ))
                session.commit()
            stats["notified"] += 1

        if tracking_data.get("status") == "exception" or decision.get("status_update") == "dispute":
            self.sounds.play_exception()

    async def _handle_attention(self, email, stats: dict, category: str):
        if category == "influencer":
            self.sounds.play_influencer()
        elif category in ("distributor", "partnership"):
            self.sounds.play_influencer()
        elif category in ("complaint", "refund"):
            self.sounds.play_exception()
        await self.gmail.modify_message(email.gmail_message_id, add_labels=["INBOX"])
        stats["notified"] += 1
