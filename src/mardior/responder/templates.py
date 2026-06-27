RESPONSE_TEMPLATES = {
    "delivered": """Hola {customer_name},

Gracias por contactarnos. Segun la informacion de {carrier}, tu paquete con numero de seguimiento {tracking_number} fue entregado el {delivery_date}.

Si no lo has recibido, por favor verifica con vecinos o en la recepcion. Si despues de 24 horas aun no aparece, contactanos para iniciar un proceso de reclamacion.

Saludos,
{store_name}""",

    "in_transit": """Hola {customer_name},

Tu pedido #{order_number} esta en camino. Aqui esta la informacion de seguimiento:

Paqueteria: {carrier}
Tracking: {tracking_number}
Ultima ubicacion: {location}
Fecha estimada: {estimated_delivery}

Puedes darle seguimiento completo en nuestro dashboard.

Saludos,
{store_name}""",

    "exception": """Hola {customer_name},

Lamento informarte que hay una actualizacion en el estatus de tu envio #{order_number}:

{carrier} reporta: {exception_detail}

Ya estamos investigando con la paqueteria para resolverlo. Te mantendremos informado de cualquier avance.

Si tienes mas dudas, responde a este correo.

Saludos,
{store_name}""",

    "dispute": """Hola {customer_name},

Lamento que no hayas recibido tu pedido #{order_number}. Entiendo tu frustracion.

Voy a escalar esto inmediatamente para investigar con {carrier}. En maximo 48 horas te dare respuesta sobre:

1. Resultado de la investigacion con la paqueteria
2. Opciones de solucion (reemplazo o reembolso)

Gracias por tu paciencia.

Saludos,
{store_name}""",

    "no_tracking": """Hola {customer_name},

Gracias por contactarnos. Tu pedido #{order_number} esta siendo procesado y pronto recibiras un numero de seguimiento.

En cuanto este en camino, te notificaremos automaticamente.

Saludos,
{store_name}""",
}
