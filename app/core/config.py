from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "WhatsApp AI Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # WhatsApp API
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_APP_SECRET: str

    # Anthropic API
    ANTHROPIC_API_KEY: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
