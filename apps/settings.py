from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_prefix="APP_")

    NAME: str
    SECRET_KEY: str
    DEBUG: bool = False
    CORS_ORIGINS: list[str] | str

    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str

    PHONEPE_CLIENT_ID: str
    PHONEPE_CLIENT_SECRET: str
    PHONEPE_PAYMENT_EXPIRY_SECONDS: int

    BACKEND_DOMAIN: str
    FRONTEND_DOMAIN: str

    @property
    def cors_origins(self) -> list[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [
                origin.strip()
                for origin in self.CORS_ORIGINS.split(",")
                if origin.strip()
            ]
        return self.CORS_ORIGINS


settings = CoreSettings()
