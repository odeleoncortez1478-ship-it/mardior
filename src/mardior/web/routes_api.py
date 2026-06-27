from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from mardior.config.settings import settings
from mardior.db.storage import Storage
from mardior.db.seed import seed_demo_data
from mardior.shipping.comparator import ShippingComparator
from mardior.worker.shopify_sync import ShopifySyncer
from mardior.web.auth import check_auth

router = APIRouter()
storage = Storage()


@router.post("/auth/login")
async def login(request: Request):
    data = await request.json()
    if data.get("password") == settings.dashboard_password:
        resp = JSONResponse({"success": True, "redirect": "/dashboard"})
        resp.set_cookie(key="mardior_auth", value=settings.dashboard_password, httponly=True)
        resp.headers.append("HX-Redirect", "/dashboard")
        return resp
    raise HTTPException(status_code=401, detail="Contrasena incorrecta")


@router.get("/stats")
async def get_stats(request: Request):
    await check_auth(request)
    return storage.get_dashboard_stats()


@router.get("/emails")
async def get_emails(request: Request, limit: int = 50, offset: int = 0, classification: str = None):
    await check_auth(request)
    emails = storage.get_emails(limit, offset, classification)
    results = []
    for e in emails:
        d = {
            "id": e.id, "gmail_message_id": e.gmail_message_id, "from_name": e.from_name,
            "from_address": e.from_address, "subject": e.subject, "body_text": e.body_text[:300] if e.body_text else "",
            "received_at": str(e.received_at) if e.received_at else "",
            "classification": e.classification, "confidence": e.confidence,
            "linked_order_id": e.linked_order_id,
            "tracking_status": e.tracking_status,
            "response_sent": e.response_sent, "response_status": e.response_status,
        }
        results.append(d)
    return {"emails": results, "total": storage.count_emails(classification)}


@router.get("/orders")
async def get_orders(request: Request, limit: int = 100, offset: int = 0, status: str = None):
    await check_auth(request)
    orders = storage.get_all_orders(limit, offset, status)
    results = []
    for o in orders:
        d = {
            "shopify_id": o.shopify_id, "order_number": o.order_number,
            "customer_email": o.customer_email, "customer_name": o.customer_name,
            "total_price": o.total_price, "currency": o.currency,
            "financial_status": o.financial_status, "fulfillment_status": o.fulfillment_status,
            "created_at": str(o.created_at) if o.created_at else "",
            "items": [{"product_title": i.product_title, "quantity": i.quantity, "price": i.price} for i in (o.items or [])],
            "fulfillments": [{"tracking_number": f.tracking_number, "carrier": f.carrier, "status": f.status} for f in (o.fulfillments or [])],
        }
        results.append(d)
    return {"orders": results, "total": storage.count_orders(status)}


@router.get("/shipping/rates")
async def get_shipping_rates(request: Request):
    await check_auth(request)
    comparator = ShippingComparator()
    return {"rates": comparator.compare_all(), "zones": comparator.get_zones(), "carriers": comparator.get_carriers()}


@router.get("/shipping/best")
async def get_best_rates(request: Request):
    await check_auth(request)
    comparator = ShippingComparator()
    return {"best": comparator.get_best_carrier_per_zone()}


@router.get("/influencers")
async def get_influencers(request: Request):
    await check_auth(request)
    emails = storage.get_emails(classification="influencer")
    results = []
    for e in emails:
        results.append({
            "id": e.id, "from_name": e.from_name, "from_address": e.from_address,
            "subject": e.subject, "body": e.body_text[:500] if e.body_text else "",
            "received_at": str(e.received_at) if e.received_at else "",
            "response_sent": e.response_sent,
        })
    return {"influencers": results}


@router.post("/sync/orders")
async def sync_orders(request: Request):
    await check_auth(request)
    if not settings.shopify_shop:
        return {"synced": 0, "error": "Shopify no configurado. Agrega SHOPIFY_SHOP en .env"}
    syncer = ShopifySyncer(token=settings.shopify_client_secret)
    count = await syncer.sync_orders()
    return {"synced": count}


@router.get("/sync/log")
async def get_sync_log(request: Request):
    await check_auth(request)
    with storage.get_session() as session:
        from mardior.db.schema import SyncLog
        logs = session.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(20).all()
    return {"logs": [
        {"type": l.sync_type, "started_at": str(l.started_at), "orders": l.orders_processed, "success": l.success, "error": l.error_message}
        for l in logs
    ]}


@router.get("/llm/cost")
async def get_llm_cost(request: Request):
    await check_auth(request)
    with storage.get_session() as session:
        from mardior.db.schema import ClassificationLog
        from sqlalchemy import func
        total = session.query(func.sum(ClassificationLog.cost)).scalar() or 0
        count = session.query(func.count(ClassificationLog.id)).scalar() or 0
    return {"total_cost": round(total, 4), "total_classifications": count}


@router.post("/seed")
async def seed_data(request: Request):
    await check_auth(request)
    seed_demo_data()
    return {"success": True, "message": "Datos de demo insertados"}
