from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mardior.config.settings import settings
from mardior.web.routes_api import router as api_router
from mardior.web.routes_pages import router as pages_router

app = FastAPI(title="MARDIOR - Automatización Gmail")

templates_dir = Path(__file__).resolve().parent / "templates"
static_dir = Path(__file__).resolve().parent.parent.parent / "static"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.include_router(api_router, prefix="/api")
app.include_router(pages_router)

templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")
