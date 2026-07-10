from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database.session import get_db
from app.models.user import User
from app.models.analytics import Analytics
from app.core.config import settings
from typing import List

def verify_admin_api_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin API key")
    return x_admin_key

router = APIRouter(dependencies=[Depends(verify_admin_api_key)])

@router.get("/users")
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all users."""
    stmt = select(User).offset(skip).limit(limit)
    users = db.execute(stmt).scalars().all()
    return users

@router.get("/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Get basic analytics."""
    total_users = db.scalar(select(func.count(User.id)))
    total_events = db.scalar(select(func.count(Analytics.id)))
    
    return {
        "total_users": total_users,
        "total_events": total_events
    }

@router.post("/broadcast")
def broadcast_message(message: str, db: Session = Depends(get_db)):
    """Broadcast a message to all active users."""
    # This should be implemented as a Celery task that iterators over users
    # and calls the WhatsApp API client.
    return {"status": "broadcast_initiated", "message": message}
