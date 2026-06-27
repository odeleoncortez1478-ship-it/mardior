from __future__ import annotations

import secrets
import bcrypt

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from mardior.config.settings import settings
from mardior.db.storage import Storage

# In-memory session store (single-user, fine for local)
_sessions: dict[str, bool] = {}
_csrf_tokens: dict[str, str] = {}  # session_id -> csrf_token

AUTH_COOKIE = "mardior_session"
CSRF_COOKIE = "mardior_csrf"


def verify_password(password: str) -> bool:
    if not settings.dashboard_password_hash:
        return False
    try:
        return bcrypt.checkpw(
            password.encode(), settings.dashboard_password_hash.encode()
        )
    except Exception:
        return False


def create_session() -> str:
    token = secrets.token_hex(32)
    _sessions[token] = True
    return token


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(AUTH_COOKIE)


def validate_session(request: Request) -> bool:
    token = get_session_token(request)
    return token is not None and _sessions.get(token, False)


def destroy_session(token: str):
    _sessions.pop(token, None)
    _csrf_tokens.pop(token, None)


def get_csrf_token(session_token: str) -> str:
    if session_token not in _csrf_tokens:
        _csrf_tokens[session_token] = secrets.token_hex(16)
    return _csrf_tokens[session_token]


def validate_csrf(request: Request) -> bool:
    cookie_csrf = request.cookies.get(CSRF_COOKIE)
    header_csrf = request.headers.get("X-CSRF-Token")
    if not cookie_csrf or not header_csrf:
        return False
    return secrets.compare_digest(cookie_csrf, header_csrf)


async def check_auth(request: Request):
    if not validate_session(request):
        raise HTTPException(status_code=303, detail="No autorizado")


def require_auth(handler):
    async def wrapper(request: Request, *args, **kwargs):
        try:
            await check_auth(request)
        except HTTPException:
            if request.url.path.startswith("/api/"):
                return JSONResponse({"error": "No autorizado"}, status_code=401)
            return RedirectResponse(url="/login")
        return await handler(request, *args, **kwargs)
    return wrapper


def require_csrf(handler):
    async def wrapper(request: Request, *args, **kwargs):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            if not validate_csrf(request):
                return JSONResponse({"error": "CSRF invalido"}, status_code=403)
        return await handler(request, *args, **kwargs)
    return wrapper
