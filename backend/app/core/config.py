from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    # Application database (users, connections, history). NOT the user's analytics database.
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

    # Required: the app refuses to start without strong keys.
    secret_key: str = Field(min_length=32)
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    # Comma-separated Fernet keys, newest first (older keys stay only so old data remains readable).
    fernet_keys: str = Field(min_length=44)

    # Outbound network policy for user-supplied database hosts.
    db_allow_private_hosts: bool = False
    db_host_allowlist: str = ""
    db_connect_timeout_seconds: int = 5
    connection_test_rate_per_minute: int = 10

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def fernet_key_list(self) -> list[str]:
        return [key.strip() for key in self.fernet_keys.split(",") if key.strip()]

    @property
    def allowed_hosts(self) -> frozenset[str]:
        return frozenset(h.strip().lower() for h in self.db_host_allowlist.split(",") if h.strip())


settings = Settings()