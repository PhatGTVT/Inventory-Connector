from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class ProductMetric(Base):
    __tablename__ = "product_metrics"

    id = Column(Integer, primary_key=True, index=True)
    connector_id = Column(Integer, ForeignKey("connectors.id", ondelete="CASCADE"), unique=True, nullable=False)
    view_count = Column(Integer, default=0, index=True)
    request_count = Column(Integer, default=0, index=True)
    last_viewed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    connector = relationship("Connector", back_populates="metric")
