from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # "admin" | "user"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    requests = relationship("InventoryRequest", back_populates="user", foreign_keys="InventoryRequest.user_id")
    processed_requests = relationship("InventoryRequest", back_populates="processor", foreign_keys="InventoryRequest.processed_by")
