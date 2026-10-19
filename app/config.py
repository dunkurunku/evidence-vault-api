"""Configuración de la aplicación, leída de variables de entorno o de un fichero .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./vault.db"
    jwt_secret: str = "solo-para-desarrollo"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    storage_dir: str = "./storage"
    anthropic_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
