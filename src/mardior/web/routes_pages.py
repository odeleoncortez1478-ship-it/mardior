from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from mardior.web.auth import check_auth

router = APIRouter()
templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


async def auth_or_redirect(request: Request):
    try:
        await check_auth(request)
        return None
    except HTTPException:
        return RedirectResponse(url="/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    redirect = await auth_or_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "dashboard.html")


@router.get("/emails", response_class=HTMLResponse)
async def emails_page(request: Request):
    redirect = await auth_or_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "emails.html")


@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    redirect = await auth_or_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "orders.html")


@router.get("/shipping", response_class=HTMLResponse)
async def shipping_page(request: Request):
    redirect = await auth_or_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "shipping.html")


@router.get("/influencers", response_class=HTMLResponse)
async def influencers_page(request: Request):
    redirect = await auth_or_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "influencers.html")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    redirect = await auth_or_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "settings.html")
