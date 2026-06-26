from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database.session import get_db
from app.models.user import User
from app.models.analytics import Analytics
from typing import List

router = APIRouter()

# Note: Add JWT authentication dependency here in a real scenario
# e.g., @router.get("/users", dependencies=[Depends(verify_admin_jwt)])

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
