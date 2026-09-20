from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://surfintel:surfintel@localhost:5432/surfintel"

    jwt_secret: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12

    # 32-byte urlsafe-base64 key for Fernet, e.g. Fernet.generate_key(). Must be set
    # explicitly in production — the default only works for local development.
    encryption_key: str = "A" * 43 + "="

    # CORS is origin-exact (see app/main.py) — "localhost" and "127.0.0.1" are
    # different origins even though they're the same machine, so both are
    # allowed by default to avoid that footgun. Override via CORS_ORIGINS as
    # either a JSON array or a comma-separated string, e.g.
    # CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip().startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
