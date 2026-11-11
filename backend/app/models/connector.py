from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Connector(Base):
    __tablename__ = "connectors"

    id = Column(Integer, primary_key=True, index=True)
    digikey_part_number = Column(String(100), unique=True, index=True, nullable=True)
    mfr_part_number = Column(String(100), unique=True, index=True, nullable=False)
    manufacturer = Column(String(100), index=True, nullable=False)
    description = Column(String(255), nullable=False)
    detailed_description = Column(Text, nullable=True)
    lead_time = Column(String(50), nullable=True, default="Immediate / In Stock")
    customer_reference = Column(String(100), nullable=True)
    datasheet_url = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    in_stock_qty = Column(Integer, default=0, nullable=False)
    min_stock_alert = Column(Integer, default=5, nullable=False)
    location = Column(String(100), nullable=True, default="Kệ A1")
    library_id = Column(Integer, ForeignKey("connector_library.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="connectors")
    library = relationship("ConnectorLibrary", back_populates="connectors")
    attributes = relationship("ConnectorAttribute", back_populates="connector", cascade="all, delete-orphan")
    requests = relationship("InventoryRequest", back_populates="connector")
    metric = relationship("ProductMetric", back_populates="connector", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="connector")
