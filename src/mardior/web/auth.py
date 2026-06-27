from __future__ import annotations

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from mardior.config.settings import settings


async def check_auth(request: Request):
    password = request.cookies.get("mardior_auth")
    if password != settings.dashboard_password:
        raise HTTPException(status_code=303, detail="No autorizado")


def require_auth(handler):
    async def wrapper(request: Request, *args, **kwargs):
        try:
            await check_auth(request)
        except HTTPException:
            if request.url.path.startswith("/api/"):
                from fastapi.responses import JSONResponse
                return JSONResponse({"error": "No autorizado"}, status_code=401)
            return RedirectResponse(url="/login")
        return await handler(request, *args, **kwargs)
    return wrapper
