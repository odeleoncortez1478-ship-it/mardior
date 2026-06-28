# MARDIOR — Automatización Gmail + ReadyCloud

Automatización de atención al cliente vía Gmail: clasifica correos con **GPT-4o-mini** (8 categorías), genera resúmenes, marca lo urgente, consulta tracking en UPS/USPS/FedEx, sincroniza órdenes desde ReadyCloud/ReadyShipper X, y responde automáticamente.

## Requisitos

- Python 3.10+
- Windows 10/11

## Instalación Rápida

```bash
git clone <url-del-repo> mardior
cd mardior
pip install -e .
```

O con virtualenv:

```bash
cd mardior
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```

## Inicio Rápido

**Para no- técnicos:** da doble click en `mardior.vbs` — se abre el navegador solo, sin ventana de terminal.

**Para técnicos:**
```bash
mardior                          # worker + web
mardior --web-only               # solo web
mardior --seed                   # datos demo
mardior --hash-password admin123 # generar hash
```

Dashboard en `http://localhost:8000` (se abre automáticamente).  
Password por defecto: `admi123`

## Configuración

1. Copia `.env.example` a `.env`
2. Genera el hash de la contraseña del dashboard:
   ```bash
   mardior --hash-password tu_contraseña
   ```
   Pega el resultado en `DASHBOARD_PASSWORD_HASH` en `.env`
3. Agrega las API keys en `.env`:

| Variable | Dónde conseguirla |
|----------|------------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `GMAIL_CREDENTIALS_PATH` | https://console.cloud.google.com/ → Gmail API → OAuth |
| `READYCLOUD_CLIENT_ID/SECRET` | ReadyCloud → API Keys |
| `READYCLOUD_ORG_PK` | `GET /api/v2/orgs/` con tu token |
| `UPS_CLIENT_ID/SECRET` | https://developer.ups.com/ |
| `USPS_CLIENT_ID/SECRET` | https://www.usps.com/business/api-access.htm |
| `FEDEX_API_KEY/SECRET` | https://developer.fedex.com/ (tracking only) |

## Uso

```bash
# Arrancar todo (worker + web)
mardior

# Solo web (sin worker background)
mardior --web-only

# Web + Cloudflare Tunnel (acceso público)
mardior --web-only --tunnel

# Solo worker (sin web)
mardior --worker-only

# Insertar datos de demo
mardior --seed

# Generar hash bcrypt
mardior --hash-password mi_password
```

También funciona con `python -m mardior`.

## Dashboard

### Sidebar
```
📊 Dashboard
⚠️ Atención (3)      → correos que requieren acción
✅ Respondidos (1)    → respondidos automáticamente
❓ Pendientes (2)     → sin responder
📧 Todos los Emails
📦 Órdenes
📬 Envíos
📢 Influencers        → redirige a emails filtrados
📯 Publicidad         → ofertas de marketing/spam
⚙️ Configuración
🚪 Cerrar Sesión
```
Los badges se actualizan solos cada 15 segundos.

### Dashboard principal
- **Widgets**: emails hoy, pendientes, órdenes totales, por enviar
- **Cards de atención**: quejas, devoluciones, influencers con botón "Responder" directo
- **Auto-refresh** cada 30 segundos

### Emails (Bandeja Inteligente)

Clasificación automática con GPT-4o-mini en 8 categorías:

| Categoría | Icono | Acción |
|-----------|-------|--------|
| tracking | 📦 | Responde automáticamente con info de tracking |
| complaint | ❗ | Marca como urgente, notifica al dueño |
| refund | 💰 | Marca como urgente, notifica al dueño |
| distributor | 🏬 | Marca como oportunidad de negocio |
| partnership | 🤝 | Marca como oportunidad de negocio |
| influencer | 📢 | Marca como oportunidad de negocio |
| ads | 📯 | Ignorado (basura/publicidad) |
| other | 📥 | Depende del contenido |

Cada email muestra:
- **Resumen GPT** del contenido
- **Badge de urgencia**: 🔴 quejas/devoluciones, 🟡 influencers/partnerships
- **Estado de tracking**: ✅ Entregado, 🚚 En tránsito, ⚠️ Excepción
- **Link a la orden** (#123)
- **Botón Responder** (abre modal con campo de texto)

Vista por secciones: **Respondidos Automáticamente**, **Requieren Atención**, **Otros**.

### Órdenes

Tabla con: N° | Cliente | Total | Paquetería (UPS/USPS/FedEx) | Tracking | Estado | ✏️

Botón **✏️** para editar paquetería y número de tracking.

## Seguridad

- **CSRF**: cookie `mardior_csrf` + header `X-CSRF-Token` en cada POST/PUT
- **Sesiones**: token aleatorio en cookie `mardior_session` (httponly)
- **Rate limiting**: configurable via `RATE_LIMIT_PER_MINUTE` (default 60/min)
- **CORS**: orígenes configurables + regex para `*.trycloudflare.com`
- **Audit log**: todos los logins, syncs, respuestas se registran

## Cloudflare Tunnel (opcional)

Para acceder a MARDIOR desde internet sin exponer tu IP:

```bash
mardior --web-only --tunnel
```

O da doble click en `tunnel.bat`.

Requiere `cloudflared` instalado:
```bash
winget install cloudflare.cloudflared
```

La URL es aleatoria cada vez (`https://palabras.trycloudflare.com`).

## Variables de entorno extras

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SERVER_TIMEOUT_MINUTES` | 0 | Auto-shutdown (0 = sin timeout) |
| `CORS_ORIGINS` | `["http://localhost:8000"]` | Orígenes CORS permitidos |
| `RATE_LIMIT_PER_MINUTE` | 60 | Máximo requests/minuto a `/api/` |

## Estructura

```
mardior/
├── mardior.vbs              # Launcher — doble click, sin terminal
├── tunnel.bat               # Cloudflare Tunnel
├── pyproject.toml           # Package config
├── .env                     # Tus API keys (gitignored)
├── requirements.txt
├── data/                    # SQLite DB (gitignored)
├── credentials/             # OAuth tokens (gitignored)
├── src/static/              # CSS, manifest, icons
└── src/mardior/
    ├── __main__.py          # Entry point (mardior CLI)
    ├── config/              # Configuración (pydantic-settings)
    ├── db/                  # SQLAlchemy schema + storage + seed
    ├── gmail/               # Gmail API client + auth
    ├── classifier/          # LLM clasificador (8 categorías)
    ├── trackers/            # UPS / USPS / FedEx tracking
    ├── shipping/            # Comparador de tarifas reales vs tienda
    ├── responder/           # Auto-responder por Gmail
    ├── notifications/       # Sonidos (beep) + notificaciones
    ├── worker/              # Background: Gmail poll, LLM pipeline, ReadyCloud sync
    └── web/                 # FastAPI + Jinja2 templates + PWA
```
