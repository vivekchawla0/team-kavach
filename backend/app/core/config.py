import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FLOODWATCH - Real-Time Flood Monitoring & Early Warning Platform"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "floodwatch-super-secret-production-key-2026-bad-muenstereifel")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    IOT_API_KEY: str = os.getenv("IOT_API_KEY", "fw_live_sec_99a8b7c6d5e4")

    # Database Mode & Strategy
    DB_MODE: str = os.getenv("DB_MODE", "postgresql")  # "postgresql" or "sqlite"
    ALLOW_SQLITE_FALLBACK: bool = os.getenv("ALLOW_SQLITE_FALLBACK", "true").lower() in ("true", "1", "yes")

    # PostgreSQL Database Credentials
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "floodwatch")
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/floodwatch"
    )
    SQLITE_FALLBACK_URL: str = os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./floodwatch.db")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

    # Sensor & Hydrological Threshold Defaults (Meters & Rates)
    DEFAULT_SAFE_LEVEL: float = 2.00
    DEFAULT_WARNING_LEVEL: float = 3.00
    DEFAULT_DANGER_LEVEL: float = 4.00
    RAPID_RISE_THRESHOLD_M_PER_HR: float = 0.20
    HEAVY_RAIN_THRESHOLD_MM_HR: float = 25.0
    HIGH_SOIL_MOISTURE_PERCENT: float = 85.0
    LOW_BATTERY_PERCENT: float = 20.0
    SENSOR_OFFLINE_MINUTES: int = 15
    SENSOR_TILT_THRESHOLD_DEG: float = 15.0

    # Geospatial Focus (Bad Münstereifel, Germany)
    DEFAULT_LATITUDE: float = 50.5539
    DEFAULT_LONGITUDE: float = 6.7633
    LOCATION_NAME: str = "Bad Münstereifel, Germany"


settings = Settings()
