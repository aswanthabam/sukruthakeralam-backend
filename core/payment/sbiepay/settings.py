from pydantic_settings import BaseSettings, SettingsConfigDict


class SbiePaySettings(BaseSettings):
    """
    Pydantic settings model for SBIePay client configuration.
    Values can be loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(case_sensitive=True, env_prefix="APP_")
    DEBUG: bool = False
    SBIEPAY_MERCHANT_ID: str
    SBIEPAY_ENCRYPTION_KEY: str
    SBIEPAY_AGGREGATOR_ID: str = "SBIEPAY"
    SBIEPAY_SUCCESS_URL: str
    SBIEPAY_FAIL_URL: str
    SBIEPAY_PUSH_RESPONSE_URL: str
    SBIEPAY_GATEWAY_URL: str
    SBIEPAY_DV_QUERY_URL: str


settings = SbiePaySettings()
