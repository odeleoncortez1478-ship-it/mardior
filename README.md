# MARDIOR — Automatización Gmail + ReadyCloud

Automatización de atención al cliente vía Gmail: clasifica correos con LLM, consulta tracking en UPS/USPS,
sincroniza órdenes desde ReadyCloud/ReadyShipper X, y responde automáticamente.

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

## Configuración

1. Copia `.env.example` a `.env`
2. Genera el hash de la contraseña del dashboard:
   ```bash
   mardior --hash-password tu_contraseña_segura
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

## Uso

```bash
# Arrancar todo (worker + dashboard + abre navegador)
mardior

# Solo dashboard web
mardior --web-only

# Solo worker (sin web)
mardior --worker-only

# Insertar datos de demo
mardior --seed

# Autenticar Gmail
mardior --setup-gmail

# Generar hash bcrypt
mardior --hash-password mi_password
```

También funciona con `python main.py` o `python -m mardior`.

## Dashboard

Abre `http://localhost:8000` en tu navegador (se abre automáticamente al iniciar).

## Estructura

```
mardior/
├── main.py                    # Entry point (legacy)
├── pyproject.toml             # Package config
├── .env                       # Tus API keys
├── requirements.txt
├── data/                      # SQLite DB
├── credentials/               # OAuth tokens (gitignored)
└── src/mardior/
    ├── __main__.py            # Entry point (mardior CLI)
    ├── config/                # Configuración
    ├── db/                    # Base de datos
    ├── gmail/                 # Gmail API
    ├── classifier/            # LLM clasificador
    ├── trackers/              # UPS/USPS tracking
    ├── shipping/              # Gestor de envíos
    ├── responder/             # Auto-responder
    ├── notifications/         # Sonidos
    ├── worker/                # Background tasks
    └── web/                   # FastAPI + PWA
```
