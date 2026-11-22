from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DeployGuard"
    environment: str = "development"
    database_url: str = "sqlite:///./deployguard.db"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DEPLOYGUARD_API_KEY", "API_KEY"),
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def require_api_key_in_production(self) -> "Settings":
        if self.environment == "production" and not self.api_key:
            raise ValueError("DEPLOYGUARD_API_KEY is required in production")
        return self


settings = Settings()
