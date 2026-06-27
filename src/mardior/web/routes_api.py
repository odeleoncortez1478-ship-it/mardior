from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from mardior.config.settings import settings
from mardior.db.storage import Storage, Email
from mardior.db.seed import seed_demo_data
from mardior.shipping.comparator import ShippingComparator
from mardior.worker.readycloud_sync import ReadyCloudSyncer
from mardior.web.auth import (
    verify_password, create_session, get_session_token,
    validate_session, destroy_session, get_csrf_token,
    check_auth, require_csrf,
)

router = APIRouter()
storage = Storage()


@router.post("/auth/login")
async def login(request: Request):
    data = await request.form()
    password = data.get("password", "")

    if verify_password(password):
        session_token = create_session()
        csrf_token = get_csrf_token(session_token)
        storage.log_audit("login", ip_address=request.client.host if request.client else "")

        resp = JSONResponse({"success": True})
        resp.set_cookie(
            key="mardior_session", value=session_token,
            httponly=True, samesite="lax",
        )
        resp.set_cookie(
            key="mardior_csrf", value=csrf_token,
            httponly=False, samesite="lax",
        )
        resp.headers.append("HX-Redirect", "/dashboard")
        return resp

    storage.log_audit("login_failed", ip_address=request.client.host if request.client else "")
    return HTMLResponse(
        '<div class="card" style="max-width:400px;width:100%;margin:auto;">'
        '<h1 style="text-align:center;margin-bottom:2rem;">MARDIOR</h1>'
        '<form hx-post="/api/auth/login" hx-target="body" hx-swap="outerHTML">'
        '<div class="form-group">'
        '<label>Contrasena</label>'
        '<input type="password" name="password" class="form-input" placeholder="Ingresa la contrasena" required>'
        '</div>'
        '<p class="text-danger" style="text-align:center;">Contrasena incorrecta</p>'
        '<button type="submit" class="btn btn-primary" style="width:100%;">Entrar</button>'
        '</form></div>',
        status_code=401,
    )


@router.post("/auth/logout")
async def logout(request: Request):
    session_token = get_session_token(request)
    if session_token:
        destroy_session(session_token)
    resp = JSONResponse({"success": True})
    resp.delete_cookie("mardior_session")
    resp.delete_cookie("mardior_csrf")
    return resp


@router.get("/csrf")
async def get_csrf(request: Request):
    await check_auth(request)
    session_token = get_session_token(request)
    token = get_csrf_token(session_token) if session_token else ""
    return {"csrf_token": token}


@router.get("/email-counts")
async def get_email_counts(request: Request):
    await check_auth(request)
    return storage.get_email_counts()


@router.get("/stats")
async def get_stats(request: Request):
    await check_auth(request)
    return storage.get_dashboard_stats()


@router.get("/emails")
async def get_emails(request: Request, limit: int = 50, offset: int = 0, classification: str = None, filter: str = None):
    await check_auth(request)
    total_filter = filter or classification
    emails = storage.get_emails(limit, offset, classification, filter)
    results = []
    for e in emails:
        d = {
            "id": e.id, "gmail_message_id": e.gmail_message_id, "from_name": e.from_name,
            "from_address": e.from_address, "subject": e.subject, "body_text": e.body_text[:300] if e.body_text else "",
            "summary": e.summary or "",
            "needs_attention": bool(e.needs_attention),
            "attention_reason": e.attention_reason or "",
            "received_at": str(e.received_at) if e.received_at else "",
            "classification": e.classification, "confidence": e.confidence,
            "linked_order_id": e.linked_order_id,
            "tracking_status": e.tracking_status,
            "response_sent": e.response_sent, "response_status": e.response_status,
        }
        results.append(d)
    return {"emails": results, "total": storage.count_emails(total_filter)}


@router.get("/orders")
async def get_orders(request: Request, limit: int = 100, offset: int = 0, status: str = None):
    await check_auth(request)
    orders = storage.get_all_orders(limit, offset, status)
    results = []
    for o in orders:
        d = {
            "id": o.id, "readycloud_id": o.readycloud_id, "order_number": o.order_number,
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
@require_csrf
async def sync_orders(request: Request):
    await check_auth(request)
    syncer = ReadyCloudSyncer()
    count = await syncer.sync_orders()
    storage.log_audit("sync_orders", ip_address=request.client.host if request.client else "", details=f"synced={count}")
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
@require_csrf
async def seed_data(request: Request):
    await check_auth(request)
    seed_demo_data()
    storage.log_audit("seed_data", ip_address=request.client.host if request.client else "")
    return {"success": True, "message": "Datos de demo insertados"}


@router.post("/emails/{email_id}/reply")
@require_csrf
async def reply_email(request: Request, email_id: int):
    await check_auth(request)
    data = await request.form()
    response_body = data.get("response_body", "")
    if not response_body:
        raise HTTPException(status_code=400, detail="response_body requerido")
    storage.update_email(email_id, {
        "response_sent": True,
        "response_body": response_body,
        "response_status": "draft",
    })
    storage.log_audit("reply_email", ip_address=request.client.host if request.client else "", details=f"email_id={email_id}")
    return {"success": True, "message": "Respuesta guardada"}


@router.put("/orders/{order_id}/shipping")
@require_csrf
async def update_order_shipping(request: Request, order_id: int):
    await check_auth(request)
    data = await request.form()
    carrier = data.get("carrier", "")
    tracking_number = data.get("tracking_number", "")
    fulfillment_id = data.get("fulfillment_id", None)
    with storage.get_session() as session:
        from mardior.db.schema import Fulfillment
        if fulfillment_id:
            f = session.query(Fulfillment).filter(Fulfillment.id == int(fulfillment_id)).first()
            if f:
                if carrier:
                    f.carrier = carrier
                if tracking_number:
                    f.tracking_number = tracking_number
                session.commit()
                storage.log_audit("update_shipping", ip_address=request.client.host if request.client else "",
                                  details=f"order_id={order_id}, carrier={carrier}, tn={tracking_number}")
                return {"success": True}
    raise HTTPException(status_code=404, detail="Fulfillment no encontrado")
