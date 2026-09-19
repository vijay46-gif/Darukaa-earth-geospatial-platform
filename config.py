import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Darukaa.Earth API"
    PROJECT_SUBTITLE: str = "Carbon & Biodiversity Intelligence Platform"
    API_V1_STR: str = "/api"

    # Security
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "darukaa_earth_super_secret_production_key_2026_secure"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    # Primary: PostgreSQL + PostGIS (for Docker / Production / local Postgres)
    # Secondary fallback: SQLite with pure-python geospatial engine if PostgreSQL is unavailable locally
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/darukaa_earth"
    )
    SQLITE_FALLBACK_URL: str = (
        f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'darukaa_dev.db')).replace('\\', '/')}"
    )

    # Mapbox
    MAPBOX_TOKEN: str = os.getenv("MAPBOX_TOKEN", "")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:4173",
        "*",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
