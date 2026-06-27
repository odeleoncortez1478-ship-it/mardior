from __future__ import annotations

import asyncio
from datetime import datetime

from mardior.config.settings import settings
from mardior.db.storage import Storage
from mardior.notifications.sounds import SoundNotifier
from mardior.worker.gmail_poll import GmailPoller
from mardior.worker.shopify_sync import ShopifySyncer
from mardior.worker.llm_pipeline import LLMPipeline


class WorkerRunner:
    def __init__(self):
        self.running = False
        self.storage = Storage()
        self.sounds = SoundNotifier()
        self.gmail_poller = GmailPoller()
        self.shopify_syncer = ShopifySyncer()
        self.llm_pipeline = LLMPipeline()

    async def run_once(self):
        try:
            new_emails = await self.gmail_poller.poll()
            if new_emails:
                stats = await self.llm_pipeline.process_pending()
                return stats
            return {"emails_fetched": 0}
        except Exception as e:
            self.sounds.play_error()
            return {"error": str(e)}

    async def run_forever(self):
        self.running = True
        self.sounds.play_startup()

        poll_interval = settings.gmail_poll_interval_minutes * 60
        last_shopify_sync = datetime.min

        print(f"[MARDIOR] Worker iniciado. Poll cada {settings.gmail_poll_interval_minutes} min.")
        print(f"[MARDIOR] Dashboard: http://localhost:{settings.api_port}")

        while self.running:
            now = datetime.utcnow()

            stats = await self.run_once()
            if stats:
                for k, v in stats.items():
                    if v:
                        print(f"[{now.strftime('%H:%M:%S')}] {k}: {v}")

            if (now - last_shopify_sync).total_seconds() > 21600:
                synced = await self.shopify_syncer.sync_orders()
                if synced:
                    print(f"[{now.strftime('%H:%M:%S')}] Shopify: {synced} ordenes sincronizadas")
                last_shopify_sync = now

            await asyncio.sleep(poll_interval)

    def stop(self):
        self.running = False
