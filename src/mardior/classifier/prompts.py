CLASSIFY_PROMPT = """Clasifica el siguiente email de una tienda en linea.

Categorias:
- tracking: El cliente pregunta por tracking, estatus de envio, numero de seguimiento, o reporta problemas con la entrega
- complaint: El cliente esta molesto, reporta un problema grave (producto danado, no llego, cobro incorrecto), quiere cancelar, o amenaza con demanda
- refund: Solicita devolucion de dinero, cambio de producto, o reporta que le cobraron de mas
- distributor: La persona quiere ser distribuidor, revendedor, comprar al mayoreo, o vender los productos en su tienda
- partnership: Propone una asociacion comercial, joint venture, colaboracion entre marcas, o proyecto conjunto
- influencer: Un influencer/creador de contenido ofrece promocionar productos a cambio de producto gratis o pago
- ads: Ofertas de publicidad, marketing, SEO, diseno web, servicios de promocion
- other: Cualquier otra cosa (facturas, consultas generales, proveedores, empleo, spam, etc.)

Responde SOLO con un JSON valido con estos campos exactos:
1. "category": una de las categorias de arriba
2. "summary": resumen de 1-2 oraciones en espanol de lo que trata el email
3. "needs_attention": true si requiere atencion humana, false si puede ser automatico
4. "attention_reason": texto corto explicando por que requiere atencion ("" si needs_attention es false)

Reglas para needs_attention:
- complaint → siempre necesita atencion
- refund → necesita atencion
- distributor → necesita atencion (oportunidad de negocio)
- partnership → necesita atencion (oportunidad de negocio)
- influencer → necesita atencion (oportunidad de negocio)
- tracking → NO necesita atencion (se responde automaticamente) A MENOS que sea queja o problema grave
- ads → NO necesita atencion
- other → depende del contenido

Asunto: {subject}
De: {from_addr}
Cuerpo: {body}"""


DECIDE_PROMPT = """Eres un asistente de atencion al cliente para una tienda en linea.
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
