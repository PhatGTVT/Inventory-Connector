from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    connector_id = Column(Integer, ForeignKey("connectors.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    change_qty = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)  # import, export_approved, manual_adjustment
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    connector = relationship("Connector", back_populates="audit_logs")
