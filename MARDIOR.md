# MARDIOR — Automatización Gmail + Shopify

## Visión General

Sistema local que monitorea Gmail, clasifica emails con LLM, sincroniza órdenes de Shopify, auto-responde consultas de tracking, y gestiona tarifas de envío. Todo corriendo localmente en Windows con dashboard PWA accesible desde celular vía Cloudflare Tunnel.

### Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 + aiosqlite, httpx, openai
- **Frontend:** Jinja2 + htmx 2.0 + Chart.js, CSS custom properties
- **Auth:** Password-based cookie session
- **Notificaciones:** winsound (Beep) + dashboard (sin Discord/Telegram)
- **Base de datos:** SQLite (data/mardior.db)
- **Desktop:** Inicio automático con开机脚本 o atajo en shell:startup

## Arquitectura

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   main.py                          │
                    │           asyncio.gather(worker, web)              │
                    └──────────┬──────────────────────────┬──────────────┘
                               │                          │
                    ┌──────────▼──────────┐    ┌──────────▼──────────┐
                    │  Worker Background   │    │   FastAPI Server    │
                    │                     │    │                     │
                    │  ┌───────────────┐  │    │  ┌───────────────┐  │
                    │  │ Gmail Poller  │  │    │  │ Route Pages   │  │
                    │  │ (15 min)      │  │    │  │ + API Routes  │  │
                    │  └───────┬───────┘  │    │  └───────┬───────┘  │
                    │          │          │    │          │          │
                    │  ┌───────▼───────┐  │    │  ┌───────▼───────┐  │
                    │  │ LLM Pipeline  │  │    │  │  Jinja2       │  │
                    │  │ classify→link │  │    │  │  + htmx       │  │
                    │  │ →track→respond│  │    │  └───────────────┘  │
                    │  └───────┬───────┘  │    │                     │
                    │          │          │    └─────────────────────┘
                    │  ┌───────▼───────┐
                    │  │  Shopify Sync │
                    │  │  (6 hours)    │
                    │  └───────────────┘
                    └─────────────────────┘
```

## Estructura del Proyecto

```
C:\Users\w11\Documents\mardior\
├── MARDIOR.md                         ← Este archivo (documentación maestra)
├── main.py                            ← Entry point (CLI + asyncio orchestrator)
├── .env                               ← API keys y configuración (gitignored)
├── .env.example                       ← Template de .env con URLs de registro
├── requirements.txt                   ← Dependencias Python
│
├── src/
│   ├── static/                        ← Archivos estáticos (PWA)
│   │   ├── manifest.json              ←   PWA manifest
│   │   ├── sw.js                      ←   Service Worker
│   │   ├── app.css                    ←   Dark theme CSS
│   │   └── icons/
│   │       ├── icon-192.png
│   │       └── icon-512.png
│   │
│   └── mardior/                       ← Paquete principal
│       ├── __init__.py
│       │
│       ├── config/
│       │   └── settings.py            ← Pydantic Settings (.env loader)
│       │
│       ├── db/
│       │   ├── schema.py              ← 10 modelos SQLAlchemy
│       │   ├── storage.py             ← CRUD operations
│       │   └── seed.py                ← Demo data (5 orders, 7 emails, 11 rates)
│       │
│       ├── gmail/
│       │   ├── auth.py                ← OAuth 2.0 con google-auth-oauthlib
│       │   ├── client.py              ← REST client httpx (+ async)
│       │   └── parser.py              ← MIME/HTML parser (beautifulsoup4)
│       │
│       ├── classifier/
│       │   ├── prompts.py             ← Prompts para GPT-4o-mini
│       │   └── llm.py                 ← LLM classifier + decision engine
│       │
│       ├── trackers/
│       │   ├── carrier.py             ← Regex patterns + domain detection
│       │   ├── ups.py                 ← UPS Tracking API (+ mock fallback)
│       │   ├── fedex.py               ← FedEx Tracking API (+ mock fallback)
│       │   └── usps.py                ← USPS Tracking API (+ mock fallback)
│       │
│       ├── shipping/
│       │   ├── reader.py              ← Shopify delivery profiles reader
│       │   ├── rates.py               ← Carrier rate API queries
│       │   ├── comparator.py          ← Compare shopify vs real prices
│       │   └── updater.py             ← deliveryProfileUpdate mutation
│       │
│       ├── responder/
│       │   ├── templates.py           ← 5 email templates
│       │   └── sender.py              ← Gmail send wrapper
│       │
│       ├── notifications/
│       │   └── sounds.py              ← winsound Beep patterns
│       │
│       ├── worker/
│       │   ├── runner.py              ← Async main loop orchestrator
│       │   ├── gmail_poll.py          ← Fetch + parse + store new emails
│       │   ├── shopify_sync.py        ← GraphQL orders query + upsert
│       │   └── llm_pipeline.py        ← Classify → link → track → respond
│       │
│       └── web/
│           ├── server.py              ← FastAPI app setup
│           ├── auth.py                ← Auth middleware
│           ├── routes_api.py          ← 10 REST endpoints
│           ├── routes_pages.py        ← 7 page routes
│           └── templates/             ← Jinja2 templates
│               ├── base.html          ←   PWA base layout
│               ├── login.html         ←   Login standalone
│               ├── dashboard.html     ←   Stats + recent emails
│               ├── emails.html        ←   Filterable email table
│               ├── orders.html        ←   Orders + sync button
│               ├── shipping.html      ←   Rate comparator + sort/filter
│               ├── influencers.html   ←   Collaboration requests
│               └── settings.html      ←   Connection status + seed
│
├── data/
│   └── mardior.db                     ← SQLite database (auto-creada)
│
├── credentials/                       ← Gmail OAuth tokens (gitignored)
│   ├── gmail_oauth.json               ←   Descargado de Google Cloud Console
│   └── gmail_token.json               ←   Generado automáticamente
│
└── venv/                              ← Python virtual environment
```

## Base de Datos — 10 Tablas

| Tabla | Propósito | PK |
|-------|-----------|----|
| `orders` | Órdenes de Shopify | shopify_id (Text) |
| `order_items` | Productos por orden | id (Integer auto) |
| `fulfillments` | Envíos con tracking | id (Integer auto) |
| `emails` | Emails recibidos | id (Integer auto) |
| `classification_logs` | Log de LLM | id (Integer auto) |
| `notifications` | Notificaciones al dueño | id (Integer auto) |
| `tracking_history` | Historial de tracking | id (Integer auto) |
| `sync_log` | Log de sincronización | id (Integer auto) |
| `shipping_profiles` | Perfiles de envío | id (Integer auto) |
| `shipping_rates` | Tarifas de envío | id (Integer auto) |

## API Endpoints

### Auth
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Login con contraseña |

### Dashboard
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/stats` | Stats: emails hoy, pendientes, órdenes, costo LLM |

### Emails
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/emails?limit=&offset=&classification=` | Lista de emails clasificados |

### Órdenes
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/orders?limit=&offset=&status=` | Lista de órdenes |
| POST | `/api/sync/orders` | Forzar sincronización Shopify |

### Shipping
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/shipping/rates` | Tarifas con comparativa |
| GET | `/api/shipping/best` | Mejor carrier por zona |

### Influencers
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/influencers` | Solicitudes de colaboración |

### System
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/llm/cost` | Costo acumulado del LLM |
| GET | `/api/sync/log` | Log de sincronizaciones |
| POST | `/api/seed` | Insertar datos de demo |

## Páginas (Frontend)

| Ruta | Descripción | Auto-refresh |
|------|-------------|-------------|
| `/login` | Login | No |
| `/dashboard` | Stats cards + últimos emails | Cada 30s |
| `/emails` | Bandeja filtrable por clasificación | Manual |
| `/orders` | Órdenes + botón sync | Manual |
| `/shipping` | Mejor carrier por zona + tabla comparativa | Manual |
| `/influencers` | Solicitudes pendientes/contactadas | Cada 30s |
| `/settings` | Estado de conexiones + seed | Cada 30s |

## Worker Background Tasks

| Tarea | Intervalo | Descripción |
|-------|-----------|-------------|
| Gmail Poll | 15 min | Busca emails no leídos, los parsea y guarda |
| LLM Pipeline | Cada poll | Clasifica, linkea orden, trackea, responde |
| Shopify Sync | 6 horas | Trae órdenes nuevas/actualizadas vía GraphQL |

## APIs Externas

| API | Propósito | Auth | Costo |
|-----|-----------|------|-------|
| Gmail API | Leer/enviar/modificar emails | OAuth 2.0 desktop | Gratis (cuotas) |
| OpenAI GPT-4o-mini | Clasificar y decidir | API Key | ~$1-3/mo (200 emails/día) |
| Shopify GraphQL | Leer órdenes y perfiles de envío | Client Credentials OAuth | Gratis |
| UPS Tracking | Consultar tracking | OAuth 2.0 client_credentials | Gratis |
| FedEx Tracking | Consultar tracking | OAuth 2.0 | Gratis (100K req/día) |
| USPS Tracking | Consultar tracking | OAuth 2.0 + Mailer ID | Gratis (si tienes MID) |

## Flujo de Procesamiento de Email

```
1. Gmail Poller detecta email no leído
2. Parsea MIME → texto plano (beautifulsoup4 si HTML)
3. LLM clasifica: tracking / influencer / ads / other
4. Si es tracking:
   a. Busca orden por email o número de orden
   b. Extrae tracking numbers del cuerpo del email
   c. Consulta API de la paquetería correspondiente
   d. LLM decide acción: responder / escalar / no acción
   e. Envía respuesta vía Gmail (en hilo)
   f. Si es excepción o dispute → winsound alerta
5. Si es influencer → winsound alerta + marca como pendiente
6. Si es ads → ignora
```

## Costos Estimados (200 emails/día)

| Concepto | Costo |
|----------|-------|
| GPT-4o-mini (clasificación) | ~$0.03/día (450 tokens in / 15 out) |
| GPT-4o-mini (decisión) | ~$0.05/día (1500 tokens in / 200 out) |
| **Total mensual** | **~$2.40/mes** |
| Hosting | $0 (local) |
| APIs de tracking | $0 (gratuitas) |

## Instalación

```powershell
cd C:\Users\w11\Documents\mardior
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env  # Editar .env con API keys
python main.py --seed   # Datos demo
python main.py          # Arrancar
```

## Configuración de API Keys

### Gmail API
1. Ir a https://console.cloud.google.com/
2. Crear proyecto → Gmail API → Enable
3. Credenciales → OAuth 2.0 Client ID → Desktop application
4. Descargar JSON como `credentials/gmail_oauth.json`
5. Ejecutar `python main.py --setup-gmail`

### OpenAI
1. Ir a https://platform.openai.com/api-keys
2. Crear API key → Pegar en `.env` como `OPENAI_API_KEY=sk-...`

### Shopify
1. Ir a https://partners.shopify.com/ → Dev Dashboard
2. Crear app → Client Credentials
3. Pegar `SHOPIFY_CLIENT_ID` y `SHOPIFY_CLIENT_SECRET` en `.env`
4. La app genera token automáticamente con refresh cada 24h

### UPS Tracking
1. Ir a https://developer.ups.com/
2. Registrarse → App → OAuth Client Credentials
3. Pegar `UPS_CLIENT_ID` y `UPS_CLIENT_SECRET`

### FedEx Tracking
1. Ir a https://developer.fedex.com/
2. Registrarse → App → API Key
3. Pegar `FEDEX_API_KEY` y `FEDEX_SECRET_KEY`

### USPS Tracking
1. Ir a https://www.usps.com/business/api-access.htm
2. Requiere Mailer ID (lo tiene quien imprime etiquetas USPS)
3. Pegar `USPS_CLIENT_ID`, `USPS_CLIENT_SECRET`, `USPS_MAILER_ID`

## Cloudflare Tunnel (Acceso Móvil)

```powershell
# Instalar cloudflared
winget install cloudflare.cloudflared

# Autenticar
cloudflared tunnel login

# Crear tunnel
cloudflared tunnel create mardior

# Configurar CNAME apuntando a localhost:8000
# Luego:
cloudflared tunnel run mardior
```

## Inicio Automático en Windows

Crear acceso directo a `main.py` en `shell:startup`:
```powershell
cmd /c "mklink ""%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MARDIOR.lnk"" ""C:\Users\w11\Documents\mardior\run.vbs"""
```

O crear `run.vbs`:
```vbscript
CreateObject("WScript.Shell").Run """C:\Users\w11\Documents\mardior\venv\Scripts\python.exe"" ""C:\Users\w11\Documents\mardior\main.py""", 0, False
```

## Errores Conocidos / Soluciones

| Problema | Solución |
|----------|----------|
| Gmail OAuth falla | Borrar `credentials/gmail_token.json` y re-autenticar |
| USPS no funciona | Verificar que tienes Mailer ID (preguntar a tu amigo) |
| `winsound` no suena | Verificar que el volumen del sistema no está en mute |
| Dashboard no carga | Revisar que el puerto 8000 no esté ocupado (`netstat -ano | findstr :8000`) |
| LLM no clasifica | Verificar `OPENAI_API_KEY` en `.env` y que tenga crédito |
| Shopify sync no funciona | Verificar token (expira cada 24h, necesita refresh) |
