from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.webhooks import router as webhooks_router
from app.api.admin import router as admin_router
from app.api.vendor import router as vendor_router
from app.core.celery_app import celery_app
from app.database.base import Base
from app.database.session import engine
import app.models  # noqa: F401 — ensures all models are imported before create_all

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all database tables on startup (safe to run repeatedly)
Base.metadata.create_all(bind=engine)

app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(vendor_router, prefix="/api/v1/vendor", tags=["vendor"])

@app.get("/")
def root():
    return {"message": "WhatsApp AI Assistant API is running."}

