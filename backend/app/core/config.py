from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://stockuser:stockpass@localhost:5432/stockdb"
    data_dir: str = "/app/data"

    # Agenda: visitas sugeridas por día (lun–vie 09–18) si no se pasa visits_per_day en query
    visits_per_day_default: int = Field(default=2, validation_alias="VISITS_PER_DAY")

    llm_provider: Literal["mock", "ollama", "openai"] = "mock"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # SharePoint / Microsoft Graph (para bajar el Excel)
    sp_tenant_id: str = ""
    sp_client_id: str = ""
    sp_client_secret: str = ""
    # Opción simple: URL de "compartir" del archivo en SharePoint/OneDrive
    sp_share_url: str = ""
    sp_sheet_name: str = "Sheet1"
    sp_download_filename: str = "sharepoint_stock.xlsx"

    # Sync
    sync_enabled: bool = False
    sync_interval_seconds: int = 1800  # 30 min

    # Telegram bot (gratis)
    telegram_bot_token: str = ""
    bot_backend_url: str = "http://backend:8000"


settings = Settings()
