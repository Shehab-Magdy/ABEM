"""Pydantic-based configuration loader for ABEM test framework.

Reads from environment variables with .env file support.
All host references default to 127.0.0.1 but can be overridden
via environment variables or the .env file for any environment.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the ABEM test framework."""

    # ── Application URLs ──────────────────────────────────────
    BASE_URL: str = "http://127.0.0.1:5173"
    API_BASE_URL: str = "http://127.0.0.1:8000"

    # ── Admin credentials ─────────────────────────────────────
    ADMIN_EMAIL: str = "admin@abem.test"
    ADMIN_PASSWORD: str = "Admin@123!"

    # ── Owner credentials ─────────────────────────────────────
    OWNER_EMAIL: str = "owner@abem.test"
    OWNER_PASSWORD: str = "Owner@123!"

    # ── Second admin (multi-tenant isolation) ─────────────────
    ADMIN2_EMAIL: str = "admin2@abem.test"
    ADMIN2_PASSWORD: str = "Admin2@123!"

    # ── Database ──────────────────────────────────────────────
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str = "abem"
    DB_USER: str = "abem"
    DB_PASSWORD: str = "abem"

    # ── Browser ───────────────────────────────────────────────
    HEADLESS: bool = True
    SLOW_MO: int = 0

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def db_dsn(self) -> str:
        """PostgreSQL connection string."""
        return (
            f"host={self.DB_HOST} port={self.DB_PORT} "
            f"dbname={self.DB_NAME} user={self.DB_USER} "
            f"password={self.DB_PASSWORD}"
        )

    @property
    def api_login_url(self) -> str:
        return f"{self.API_BASE_URL}/api/v1/auth/login/"

    @property
    def api_base(self) -> str:
        return f"{self.API_BASE_URL}/api/v1"


settings = Settings()
