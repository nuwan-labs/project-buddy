"""
Application configuration loaded from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Ollama ──────────────────────────────────────────────────────────────
    ollama_host: str = "192.168.200.5"
    ollama_port: int = 11434
    ollama_model: str = "deepseek-r1:7b"
    ollama_timeout: int = 300
    ollama_analysis_enabled: bool = True

    # ── Scheduler ───────────────────────────────────────────────────────────
    scheduler_timezone: str = "Asia/Colombo"
    popup_start_hour: int = 8
    popup_start_minute: int = 30
    popup_end_hour: int = 17
    daily_note_hour: int = 16
    daily_note_minute: int = 55
    analysis_hour: int = 17
    analysis_minute: int = 0

    # ── Server ──────────────────────────────────────────────────────────────
    backend_host: str = "127.0.0.1"
    backend_port: int = 5000
    frontend_origin: str = "http://localhost:3000"

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./lab_notebook.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
