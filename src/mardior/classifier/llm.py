from __future__ import annotations

import json
from typing import Optional
from openai import OpenAI
from mardior.config.settings import settings
from mardior.classifier.prompts import CLASSIFY_PROMPT, DECIDE_PROMPT


class LLMClassifier:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.llm_model

    def classify(self, subject: str, from_addr: str, body: str) -> tuple[str, float, int, int, float]:
        if not self.client:
            return "tracking", 0.9, 0, 0, 0

        prompt = CLASSIFY_PROMPT.format(subject=subject[:200], from_addr=from_addr, body=body[:2000])

        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0,
        )

        category = r.choices[0].message.content.strip().lower()
        if category not in ("tracking", "influencer", "ads", "other"):
            category = "other"

        usage = r.usage
        in_tokens = usage.prompt_tokens if usage else 0
        out_tokens = usage.completion_tokens if usage else 0
        cost = 0
        if self.model == "gpt-4o-mini":
            cost = (in_tokens / 1_000_000 * 0.15) + (out_tokens / 1_000_000 * 0.60)

        return category, 0.9, in_tokens, out_tokens, cost

    def classify_structured(self, subject: str, from_addr: str, body: str) -> dict:
        if not self.client:
            return {
                "category": "tracking", "summary": body[:200] if body else "",
                "needs_attention": False, "attention_reason": "",
                "input_tokens": 0, "output_tokens": 0, "cost": 0,
            }

        prompt = CLASSIFY_PROMPT.format(subject=subject[:200], from_addr=from_addr, body=body[:2000])

        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0,
            response_format={"type": "json_object"},
        )

        usage = r.usage
        in_tokens = usage.prompt_tokens if usage else 0
        out_tokens = usage.completion_tokens if usage else 0
        cost = 0
        if self.model == "gpt-4o-mini":
            cost = (in_tokens / 1_000_000 * 0.15) + (out_tokens / 1_000_000 * 0.60)

        try:
            data = json.loads(r.choices[0].message.content)
        except (json.JSONDecodeError, AttributeError):
            data = {}

        valid_categories = ("tracking", "complaint", "refund", "distributor", "partnership", "influencer", "ads", "other")
        return {
            "category": data.get("category", "other") if data.get("category") in valid_categories else "other",
            "summary": data.get("summary", ""),
            "needs_attention": bool(data.get("needs_attention", False)),
            "attention_reason": data.get("attention_reason", ""),
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "cost": cost,
        }

    def decide(
        self,
        from_name: str, from_address: str, subject: str, body: str,
        order_number: int, items: str, total: float, created_at: str,
        carrier: str, tracking_number: str, tracking_status: str, last_update: str,
    ) -> dict:
        if not self.client:
            return {
                "action": "reply_customer",
                "response_text": f"Gracias por contactarnos. Tu pedido #{order_number} con {carrier} (tracking: {tracking_number}) está actualmente: {tracking_status}. Te mantendremos informado.",
                "notify_owner": False,
                "owner_message": "",
                "status_update": tracking_status,
            }

        prompt = DECIDE_PROMPT.format(
            from_name=from_name, from_address=from_address,
            subject=subject, body=body[:1500],
            order_number=order_number,
            items=items, total=total, created_at=created_at,
            carrier=carrier, tracking_number=tracking_number,
            tracking_status=tracking_status, last_update=last_update,
        )

        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(r.choices[0].message.content)
        except (json.JSONDecodeError, AttributeError):
            return {"action": "no_action", "response_text": "", "notify_owner": True, "owner_message": "Error decidiendo acción para este email", "status_update": "unknown"}
