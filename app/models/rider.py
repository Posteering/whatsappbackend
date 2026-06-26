from sqlalchemy import Column, String, Float, Boolean
from app.database.base import Base
import uuid

class DispatchRider(Base):
    __tablename__ = "dispatch_riders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False) # e.g., "Bike", "Van", "Truck"
    current_location = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)
