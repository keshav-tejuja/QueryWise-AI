from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    # Application database (users, connections, history). NOT the user's analytics database.
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

    # Required: the app refuses to start without a strong key.
    secret_key: str = Field(min_length=32)
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


settings = Settings()