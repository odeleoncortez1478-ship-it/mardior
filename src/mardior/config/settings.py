from __future__ import annotations

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    gmail_credentials_path: str = "credentials/gmail_oauth.json"
    gmail_token_path: str = "credentials/gmail_token.json"
    gmail_user_id: str = "me"
    gmail_poll_interval_minutes: int = 15

    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    shopify_shop: str = ""
    shopify_client_id: str = ""
    shopify_client_secret: str = ""
    shopify_api_version: str = "2026-07"

    ups_client_id: str = ""
    ups_client_secret: str = ""
    ups_use_sandbox: bool = True

    fedex_api_key: str = ""
    fedex_secret_key: str = ""
    fedex_account_number: str = ""

    usps_client_id: str = ""
    usps_client_secret: str = ""
    usps_mailer_id: str = ""

    database_path: str = "data/mardior.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    dashboard_password: str = "admin123"
    secret_key: str = "cambiar-esta-clave-por-una-segura"

    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent

    @property
    def db_path(self) -> Path:
        return self.base_dir / self.database_path

    @property
    def credentials_dir(self) -> Path:
        return self.base_dir / "credentials"


settings = Settings()
