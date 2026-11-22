from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DeployGuard"
    environment: str = "development"
    database_url: str = "sqlite:///./deployguard.db"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
