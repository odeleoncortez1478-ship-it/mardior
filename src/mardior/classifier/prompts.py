CLASSIFY_PROMPT = """Clasifica el siguiente email de una tienda Shopify.

Categorías:
- tracking: El cliente pregunta por el estatus de su envío, proporciona un número de tracking, o reporta problemas con la entrega (no llegó, llegó dañado, retraso, etc.)
- influencer: Un influencer/creador de contenido ofrece promocionar productos a cambio de producto gratis o pago
- ads: Ofertas de publicidad, marketing, SEO, servicios de promoción
- other: Cualquier otra cosa (facturas, consultas generales, spam, etc.)

Responde SOLO con el nombre de la categoría en minúsculas, nada más.

Asunto: {subject}
De: {from_addr}
Cuerpo: {body}"""


DECIDE_PROMPT = """Eres un asistente de atención al cliente para una tienda Shopify.
Basado en la siguiente información, decide qué hacer.

EMAIL del cliente:
- De: {from_name} ({from_address})
- Asunto: {subject}
- Mensaje: {body}

ORDEN:
- Número: #{order_number}
- Producto(s): {items}
- Total: ${total}
- Fecha: {created_at}

TRACKING:
- Paquetería: {carrier}
- Número: {tracking_number}
- Estado actual: {tracking_status}
- Última actualización: {last_update}

Decide la acción a tomar. Responde SOLO con un JSON válido con estos campos:
1. "action": "reply_customer" | "escalate_owner" | "no_action"
2. "response_text": Texto para responder al cliente (si aplica, en español amable)
3. "notify_owner": true | false
4. "owner_message": Mensaje corto para el dueño (si notify_owner es true)
5. "status_update": "delivered" | "in_transit" | "exception" | "dispute" | "unknown"

Reglas:
- Si el cliente está molesto o hay un problema con la entrega, escalar al dueño
- Si el paquete está en tránsito y solo pregunta, responder con info de tracking
- Si el paquete fue entregado pero el cliente dice no haberlo recibido, escalar como dispute
- Si hay una excepción/demora, responder con disculpas y escalar al dueño"""
