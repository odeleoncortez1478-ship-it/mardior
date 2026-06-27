from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from mardior.db.schema import Order, OrderItem, Fulfillment, Email, ClassificationLog, ShippingRate
from mardior.db.storage import Storage


def seed_demo_data():
    storage = Storage()
    with storage.get_session() as session:
        if session.query(Order).count() > 0:
            return

        now = datetime.utcnow()

        # ─── Orders ───
        orders_data = [
            {
                "readycloud_id": "rc-1001",
                "order_number": 1001,
                "customer_email": "maria@email.com",
                "customer_name": "María García",
                "total_price": 89.99,
                "currency": "USD",
                "financial_status": "paid",
                "fulfillment_status": "fulfilled",
                "shipping_price": 12.00,
                "created_at": now - timedelta(days=5),
                "updated_at": now - timedelta(days=3),
            },
            {
                "readycloud_id": "rc-1002",
                "order_number": 1002,
                "customer_email": "carlos@email.com",
                "customer_name": "Carlos López",
                "total_price": 145.50,
                "currency": "USD",
                "financial_status": "paid",
                "fulfillment_status": "unfulfilled",
                "shipping_price": 15.00,
                "created_at": now - timedelta(days=2),
                "updated_at": now - timedelta(days=1),
            },
            {
                "readycloud_id": "rc-1003",
                "order_number": 1003,
                "customer_email": "ana@email.com",
                "customer_name": "Ana Martínez",
                "total_price": 250.00,
                "currency": "MXN",
                "financial_status": "paid",
                "fulfillment_status": "fulfilled",
                "shipping_price": 20.00,
                "created_at": now - timedelta(days=7),
                "updated_at": now - timedelta(days=5),
            },
            {
                "readycloud_id": "rc-1004",
                "order_number": 1004,
                "customer_email": "jose@email.com",
                "customer_name": "José Hernández",
                "total_price": 67.30,
                "currency": "USD",
                "financial_status": "paid",
                "fulfillment_status": "fulfilled",
                "shipping_price": 11.50,
                "created_at": now - timedelta(days=10),
                "updated_at": now - timedelta(days=8),
            },
            {
                "readycloud_id": "rc-1005",
                "order_number": 1005,
                "customer_email": "laura@email.com",
                "customer_name": "Laura Torres",
                "total_price": 320.00,
                "currency": "MXN",
                "financial_status": "paid",
                "fulfillment_status": "in_transit",
                "shipping_price": 25.00,
                "created_at": now - timedelta(days=1),
                "updated_at": now,
            },
        ]

        order_objs = []
        for od in orders_data:
            obj = Order(**od)
            session.add(obj)
            order_objs.append(obj)
        session.flush()

        # ─── Order Items ───
        items_data = [
            {"order_id": order_objs[0].id, "product_title": "Zapatos Nike Air Max", "quantity": 1, "price": 89.99, "sku": "ZK-001"},
            {"order_id": order_objs[1].id, "product_title": "Camisa Polo Ralph Lauren", "quantity": 2, "price": 45.00, "sku": "PL-202"},
            {"order_id": order_objs[1].id, "product_title": "Gorra New Era", "quantity": 1, "price": 55.50, "sku": "NE-055"},
            {"order_id": order_objs[2].id, "product_title": "Bolsa Michael Kors", "quantity": 1, "price": 250.00, "sku": "MK-500"},
            {"order_id": order_objs[3].id, "product_title": "Reloj Casio G-Shock", "quantity": 1, "price": 67.30, "sku": "GS-100"},
            {"order_id": order_objs[4].id, "product_title": "Audífonos Sony WH-1000XM5", "quantity": 1, "price": 320.00, "sku": "SN-999"},
        ]
        for it in items_data:
            session.add(OrderItem(**it))

        # ─── Fulfillments ───
        fulf_data = [
            {"order_id": order_objs[0].id, "tracking_number": "1Z999AA10123456784", "carrier": "ups", "status": "delivered"},
            {"order_id": order_objs[2].id, "tracking_number": "79456789012345678901", "carrier": "usps", "status": "delivered"},
            {"order_id": order_objs[3].id, "tracking_number": "123456789012", "carrier": "fedex", "status": "delivered"},
            {"order_id": order_objs[4].id, "tracking_number": "1Z888BB20234567890", "carrier": "ups", "status": "in_transit"},
        ]
        for f in fulf_data:
            session.add(Fulfillment(**f))

        # ─── Emails ───
        emails_data = [
            {
                "gmail_message_id": "msg-001", "thread_id": "thr-001",
                "from_name": "María García", "from_address": "maria@email.com",
                "subject": "¿Dónde está mi pedido?",
                "body_text": "Hola, hice un pedido hace 5 días y el tracking dice entregado pero no lo recibí. ¿Pueden ayudarme?",
                "received_at": now - timedelta(hours=2),
                "classification": "complaint", "confidence": 0.98,
                "summary": "La cliente reporta que su pedido aparece como entregado pero ella no lo recibio. Solicita ayuda para localizarlo.",
                "needs_attention": True, "attention_reason": "posible robo o extravio",
                "linked_order_id": order_objs[0].id, "linking_method": "email_match",
                "tracking_fetched": True, "tracking_status": "delivered",
                "response_sent": False,
            },
            {
                "gmail_message_id": "msg-002", "thread_id": "thr-002",
                "from_name": "Laura Torres", "from_address": "laura@email.com",
                "subject": "Número de seguimiento",
                "body_text": "Buen día, quería saber el número de tracking de mi pedido #1005. Gracias.",
                "received_at": now - timedelta(hours=5),
                "classification": "tracking", "confidence": 0.95,
                "summary": "La cliente solicita el numero de tracking de su pedido #1005.",
                "needs_attention": False, "attention_reason": "",
                "linked_order_id": order_objs[4].id, "linking_method": "order_number",
                "tracking_fetched": True, "tracking_status": "in_transit",
                "response_sent": True, "response_body": "Tu pedido #1005 está en camino con UPS. Tracking: 1Z888BB20234567890",
                "response_status": "sent",
            },
            {
                "gmail_message_id": "msg-003", "thread_id": "thr-003",
                "from_name": "Influencer Beauty", "from_address": "beauty.influencer@instagram.com",
                "subject": "Colaboración — Quiero promocionar tus productos",
                "body_text": "Hola! Soy creadora de contenido con 50K seguidores en Instagram. Me encantaría probar tus productos y hacerles review. ¿Les interesa una colaboración?",
                "received_at": now - timedelta(hours=8),
                "classification": "influencer", "confidence": 0.99,
                "summary": "Influencer con 50K seguidores en Instagram ofrece probar productos y hacer review a cambio de producto gratis.",
                "needs_attention": True, "attention_reason": "oportunidad de colaboracion",
                "response_sent": False,
            },
            {
                "gmail_message_id": "msg-004", "thread_id": "thr-004",
                "from_name": "Agencia Ads Pro", "from_address": "ventas@agenciaadspro.com",
                "subject": "Multiplica tus ventas con Google Ads",
                "body_text": "Te ofrecemos manejo profesional de Google Ads para tu tienda. Primera semana gratis. Contáctanos para más info.",
                "received_at": now - timedelta(hours=12),
                "classification": "ads", "confidence": 0.97,
                "summary": "Agencia de publicidad ofrece servicios de Google Ads con primera semana gratis.",
                "needs_attention": False, "attention_reason": "",
                "response_sent": False,
            },
            {
                "gmail_message_id": "msg-005", "thread_id": "thr-005",
                "from_name": "Ana Martínez", "from_address": "ana@email.com",
                "subject": "Devolución — Bolsa Michael Kors",
                "body_text": "Compré una bolsa y llegó con un pequeño defecto. Quiero hacer una devolución. ¿Cómo procedo?",
                "received_at": now - timedelta(days=1),
                "classification": "refund", "confidence": 0.92,
                "summary": "La cliente recibio una bolsa con defecto y solicita instrucciones para devolverla y obtener reembolso.",
                "needs_attention": True, "attention_reason": "devolucion por defecto",
                "linked_order_id": order_objs[2].id,
                "tracking_fetched": True, "tracking_status": "delivered",
                "response_sent": False,
            },
            {
                "gmail_message_id": "msg-006", "thread_id": "thr-006",
                "from_name": "TikTok Influencer", "from_address": "tiktok.star@tiktok.com",
                "subject": "Propuesta de colaboración",
                "body_text": "Hola! Tengo 120K seguidores en TikTok y hago reviews de productos. Me gustaría recibir algunos productos para mostrarles a mi audiencia. Saludos!",
                "received_at": now - timedelta(hours=3),
                "classification": "influencer", "confidence": 0.98,
                "summary": "Creadora de contenido con 120K seguidores en TikTok propone colaboracion para review de productos.",
                "needs_attention": True, "attention_reason": "oportunidad de colaboracion",
                "response_sent": False,
            },
            {
                "gmail_message_id": "msg-007", "thread_id": "thr-007",
                "from_name": "Carlos López", "from_address": "carlos@email.com",
                "subject": "¿Cuándo se envía mi pedido #1002?",
                "body_text": "Ya pagué mi pedido hace 2 días y sigue sin enviarse. ¿Cuándo lo van a mandar?",
                "received_at": now - timedelta(hours=1),
                "classification": "tracking", "confidence": 0.96,
                "summary": "El cliente pregunta por el estatus de envio de su pedido #1002 que ya pago pero aun no se envia.",
                "needs_attention": False, "attention_reason": "",
                "linked_order_id": order_objs[1].id, "linking_method": "email_match",
                "tracking_fetched": False,
                "response_sent": False,
            },
        ]
        email_objs = []
        for e in emails_data:
            obj = Email(**e)
            session.add(obj)
            email_objs.append(obj)
        session.flush()

        # ─── Classification Logs ───
        for email_obj, email_data in zip(email_objs, emails_data):
            session.add(ClassificationLog(
                email_id=email_obj.id, model_used="gpt-4o-mini",
                input_tokens=450, output_tokens=15, cost=0.00015,
                raw_prompt=f"Clasifica: {email_data['subject'][:50]}",
                raw_response=email_data["classification"],
            ))

        # ─── Shipping Rates (demo) ───
        rates_data = [
            {"zone": "México", "carrier": "UPS", "method_name": "UPS Standard", "store_price": 15.00, "real_price": 8.50, "source": "ups"},
            {"zone": "México", "carrier": "USPS", "method_name": "USPS Priority", "store_price": 20.00, "real_price": 6.00, "source": "usps"},
            {"zone": "Estados Unidos", "carrier": "UPS", "method_name": "UPS Ground", "store_price": 12.00, "real_price": 12.00, "source": "ups"},
            {"zone": "Estados Unidos", "carrier": "USPS", "method_name": "USPS First", "store_price": 13.50, "real_price": 13.50, "source": "usps"},
            {"zone": "Canadá", "carrier": "UPS", "method_name": "UPS Standard", "store_price": 18.00, "real_price": 14.00, "source": "ups"},
            {"zone": "Canadá", "carrier": "USPS", "method_name": "USPS Priority", "store_price": 25.00, "real_price": 10.00, "source": "usps"},
            {"zone": "Europa", "carrier": "UPS", "method_name": "UPS Express", "store_price": 35.00, "real_price": 28.00, "source": "ups"},
        ]
        for r in rates_data:
            session.add(ShippingRate(**r))

        session.commit()
