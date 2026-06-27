from __future__ import annotations

import asyncio
from datetime import datetime

from mardior.config.settings import settings
from mardior.db.storage import Storage
from mardior.notifications.sounds import SoundNotifier
from mardior.worker.gmail_poll import GmailPoller
from mardior.worker.readycloud_sync import ReadyCloudSyncer
from mardior.worker.llm_pipeline import LLMPipeline


class WorkerRunner:
    def __init__(self):
        self.running = False
        self.storage = Storage()
        self.sounds = SoundNotifier()
        self.gmail_poller = GmailPoller()
        self.readycloud_syncer = ReadyCloudSyncer()
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
        rc_sync_interval = settings.readycloud_sync_interval_hours * 3600
        last_rc_sync = datetime.min

        print(f"[MARDIOR] Worker iniciado. Poll cada {settings.gmail_poll_interval_minutes} min.")
        print(f"[MARDIOR] Sync ReadyCloud cada {settings.readycloud_sync_interval_hours} h.")
        print(f"[MARDIOR] Dashboard: http://localhost:{settings.api_port}")

        while self.running:
            now = datetime.utcnow()

            stats = await self.run_once()
            if stats:
                for k, v in stats.items():
                    if v:
                        print(f"[{now.strftime('%H:%M:%S')}] {k}: {v}")

            if (now - last_rc_sync).total_seconds() > rc_sync_interval:
                synced = await self.readycloud_syncer.sync_orders()
                if synced:
                    print(f"[{now.strftime('%H:%M:%S')}] ReadyCloud: {synced} ordenes sincronizadas")
                last_rc_sync = now

            await asyncio.sleep(poll_interval)

    def stop(self):
        self.running = False
