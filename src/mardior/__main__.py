from __future__ import annotations

import asyncio
import os
import re
import sys
import webbrowser
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mardior.config.settings import settings
from mardior.db.seed import seed_demo_data
from mardior.notifications.sounds import SoundNotifier
from mardior.web.server import app
from mardior.worker.runner import WorkerRunner


def print_help():
    print("MARDIOR - Automatizacion Gmail + ReadyCloud")
    print()
    print("Uso:")
    print("  mardior                          Arranca worker + dashboard")
    print("  mardior --web-only               Solo dashboard web")
    print("  mardior --worker-only            Solo worker (sin web)")
    print("  mardior --seed                   Insertar datos de demo")
    print("  mardior --setup-gmail            Autenticar Gmail OAuth")
    print("  mardior --hash-password <pw>     Generar hash bcrypt")
    print("  mardior --tunnel                 Inicia con Cloudflare Tunnel (acceso movil)")
    print("  mardior --help                   Esta ayuda")


def validate_env():
    missing = []
    if not settings.readycloud_client_id:
        missing.append("READYCLOUD_CLIENT_ID")
    if not settings.readycloud_client_secret:
        missing.append("READYCLOUD_CLIENT_SECRET")
    if not settings.readycloud_org_pk:
        missing.append("READYCLOUD_ORG_PK")
    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")
    if not settings.dashboard_password_hash:
        missing.append("DASHBOARD_PASSWORD_HASH (genera uno con: mardior --hash-password tu_password)")
    if missing:
        print("(!) Variables requeridas faltantes en .env:")
        for v in missing:
            print(f"   - {v}")
        print(f"\n   Revisa: {Path('.env.example').resolve()}")
        return False
    return True


async def start_tunnel(api_port: int):
    """Start cloudflared quick tunnel and return (process, read_task, get_url)."""
    import shutil
    cloudflared_path = shutil.which("cloudflared")
    if not cloudflared_path:
        alt = Path.home() / "AppData" / "Local" / "cloudflared" / "cloudflared.exe"
        alt2 = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Cloudflare" / "cloudflared.exe"
        for p in [alt, alt2]:
            if p.exists():
                cloudflared_path = str(p)
                break
    if not cloudflared_path:
        print()
        print("[!] cloudflared no esta instalado.")
        print("    Instalalo con:  winget install cloudflare.cloudflared")
        print("    O descargalo de: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        print()
        return None, None, lambda: None

    try:
        proc = await asyncio.create_subprocess_exec(
            cloudflared_path, "tunnel", "--url", f"http://localhost:{api_port}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError:
        print(f"\n[!] No se encontro cloudflared en: {cloudflared_path}\n")
        return None, None, lambda: None

    url = None

    async def read_output():
        nonlocal url
        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                print(f"  [tunnel] {text}")
            if not url and ".trycloudflare.com" in text:
                m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", text)
                if m:
                    url = m.group(0)
                    print()
                    print(f"[MARDIOR] URL publica: {url}")
                    print(f"[MARDIOR] Abre esta URL en tu telefono")
                    print()
        await proc.wait()

    task = asyncio.create_task(read_output())
    return proc, task, lambda: url


def run():
    args = set(sys.argv[1:])

    if "--help" in args or "-h" in args:
        print_help()
        return

    if "--hash-password" in args:
        import bcrypt
        idx = list(sys.argv).index("--hash-password")
        if idx + 1 < len(sys.argv):
            pw = sys.argv[idx + 1]
            h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            print(f"DASHBOARD_PASSWORD_HASH={h}")
        return

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

    if not validate_env():
        print("\nConfigura .env primero (copia .env.example a .env y editalo)")
        return

    seed_demo_data()
    sounds = SoundNotifier()
    sounds.play_startup()

    worker_only = "--worker-only" in args
    web_only = "--web-only" in args
    use_tunnel = "--tunnel" in args
    timeout_seconds = settings.server_timeout_minutes * 60

    if not web_only:
        webbrowser.open(f"http://localhost:{settings.api_port}")

    print(f"[MARDIOR] Dashboard: http://localhost:{settings.api_port}")
    if timeout_seconds > 0:
        print(f"[MARDIOR] Auto-shutdown en {settings.server_timeout_minutes} min")

    async def run_server(server: uvicorn.Server):
        await server.serve()

    async def shutdown_timer(stop_callback):
        if timeout_seconds <= 0:
            return
        await asyncio.sleep(timeout_seconds)
        print(f"\n[MARDIOR] Auto-shutdown: {settings.server_timeout_minutes} min alcanzado")
        stop_callback()

    async def tunnel_cleanup(proc, task):
        if proc is None:
            return
        if proc.returncode is None:
            proc.kill()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    if web_only:
        tunnel_proc = None
        tunnel_task = None
        get_url = None

        async def web_only_main():
            nonlocal tunnel_proc, tunnel_task, get_url
            if use_tunnel:
                tunnel_proc, tunnel_task, get_url = await start_tunnel(settings.api_port)
                await asyncio.sleep(3)

            config = uvicorn.Config(app, host=settings.api_host, port=settings.api_port, log_level="info")
            server = uvicorn.Server(config)

            try:
                if timeout_seconds > 0:
                    t = asyncio.create_task(shutdown_timer(lambda: setattr(server, 'should_exit', True)))
                await server.serve()
            finally:
                if tunnel_proc:
                    await tunnel_cleanup(tunnel_proc, tunnel_task)

        asyncio.run(web_only_main())
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
        if timeout_seconds > 0:
            server.timeout_graceful_shutdown = timeout_seconds
        await server.serve()

    try:
        if worker_only:
            asyncio.run(run_worker())
        else:
            tasks = [run_worker(), run_web()]
            if timeout_seconds > 0:
                tasks.append(shutdown_timer(lambda: runner.stop()))
            tunnel_proc = None
            tunnel_task = None

            async def main_with_tunnel():
                nonlocal tunnel_proc, tunnel_task
                if use_tunnel:
                    tunnel_proc, tunnel_task, _ = await start_tunnel(settings.api_port)
                await asyncio.gather(*tasks)

            try:
                asyncio.run(main_with_tunnel())
            finally:
                if tunnel_proc:
                    asyncio.run(tunnel_cleanup(tunnel_proc, tunnel_task))

    except KeyboardInterrupt:
        print("\n[MARDIOR] Deteniendo...")
        runner.stop()
    except Exception as e:
        print(f"\n[MARDIOR] Error fatal: {e}")
        runner.stop()


if __name__ == "__main__":
    run()
