# MARDIOR — Automatización Gmail + Shopify

## Requisitos

- Python 3.11+
- Windows 10/11

## Instalación Rápida

```bash
cd mardior
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env`
2. Agrega tus API keys en `.env`:

| Variable | Dónde conseguirla |
|----------|------------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `GMAIL_CREDENTIALS_PATH` | https://console.cloud.google.com/ → Gmail API → OAuth |
| `SHOPIFY_CLIENT_ID/SECRET` | https://partners.shopify.com/ → Dev Dashboard |
| `UPS_CLIENT_ID/SECRET` | https://developer.ups.com/ |
| `FEDEX_API_KEY/SECRET` | https://developer.fedex.com/ |
| `USPS_CLIENT_ID/SECRET` | https://www.usps.com/business/api-access.htm |

## Uso

```bash
# Arrancar todo (worker + dashboard)
python main.py

# Solo dashboard web
python main.py --web-only

# Insertar datos de demo
python main.py --seed

# Autenticar Gmail
python main.py --setup-gmail
```

## Dashboard

Abre `http://localhost:8000` en tu navegador.
Contraseña por defecto: `admin123`

## Estructura

```
mardior/
├── main.py                    # Entry point
├── .env                       # Tus API keys
├── requirements.txt
├── data/                      # SQLite DB
├── credentials/               # OAuth tokens (gitignored)
└── src/mardior/
    ├── config/                # Configuración
    ├── db/                    # Base de datos
    ├── gmail/                 # Gmail API
    ├── classifier/            # LLM clasificador
    ├── trackers/              # UPS/FedEx/USPS
    ├── shipping/              # Gestor de envíos
    ├── responder/             # Auto-responder
    ├── notifications/         # Sonidos
    ├── worker/                # Background tasks
    └── web/                   # FastAPI + PWA
```
