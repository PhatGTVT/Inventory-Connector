from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class InventoryRequest(Base):
    __tablename__ = "inventory_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    connector_id = Column(Integer, ForeignKey("connectors.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(20), default="pending", index=True, nullable=False)  # pending, approved, rejected, deleted
    reason = Column(Text, nullable=True)
    admin_response = Column(Text, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="requests", foreign_keys=[user_id])
    connector = relationship("Connector", back_populates="requests")
    processor = relationship("User", back_populates="processed_requests", foreign_keys=[processed_by])
