#!/usr/bin/env python3
"""
MARDIOR — Automatizacion Gmail + Shopify
========================================

Usage:
    python main.py                  # Arranca worker + dashboard
    python main.py --worker-only    # Solo worker (sin web)
    python main.py --web-only       # Solo dashboard web
    python main.py --seed           # Insertar datos de demo
    python main.py --setup-gmail    # Autenticar Gmail OAuth
"""

from __future__ import annotations

import asyncio
import sys
import uvicorn

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mardior.config.settings import settings
from mardior.db.seed import seed_demo_data
from mardior.notifications.sounds import SoundNotifier
from mardior.web.server import app
from mardior.worker.runner import WorkerRunner


async def main():
    args = set(sys.argv[1:])
    sounds = SoundNotifier()

    if "--setup-gmail" in args:
        from mardior.gmail.auth import GmailAuth
        auth = GmailAuth()
        token = auth.authorize()
        print("[OK] Gmail autenticado. Token guardado.")
        return

    if "--seed" in args:
        seed_demo_data()
        print("[OK] Datos de demo insertados en la base de datos.")
        return

    seed_demo_data()
    sounds.play_startup()

    worker_only = "--worker-only" in args
    web_only = "--web-only" in args

    if web_only:
        print(f"[MARDIOR] Dashboard: http://localhost:{settings.api_port}")
        uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level="info")
        return

    runner = WorkerRunner()

    async def run_worker():
        try:
            await runner.run_forever()
        except Exception as e:
            print(f"[MARDIOR] Worker error: {e}")
            runner.stop()

    async def run_web():
        config = uvicorn.Config(app, host=settings.api_host, port=settings.api_port, log_level="warning")
        server = uvicorn.Server(config)
        await server.serve()

    try:
        if worker_only:
            await run_worker()
        else:
            await asyncio.gather(run_worker(), run_web())
    except KeyboardInterrupt:
        print("\n[MARDIOR] Deteniendo...")
        runner.stop()
    except Exception as e:
        print(f"\n[MARDIOR] Error fatal: {e}")
        runner.stop()


if __name__ == "__main__":
    asyncio.run(main())
