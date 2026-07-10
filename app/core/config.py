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
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_APP_SECRET: str

    # Anthropic API
    ANTHROPIC_API_KEY: str

    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str
    
    # Posteering API config
    POSTEERING_API_KEY: str = ""
    POSTEERING_API_SECRET: str = ""
    POSTEERING_KEY_ID: str = ""
    ESCROW_LEDGER_ACCOUNT_ID: str = ""
    
    # Internal Admin Auth
    ADMIN_API_KEY: str = "violet-admin-secret"
    POSTEERING_CONTEXT_ID: str = ""
    WEBHOOK_BASE_URL: str = "https://dummy.example.com"  # Public URL for Posteering callbacks

    # Posteering Escrow API (simple X-API-Key)
    POSTEERING_ESCROW_KEY: str = ""  # Get from admin@posteering.com

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
