from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class ConnectorLibrary(Base):
    __tablename__ = "connector_library"

    id = Column(Integer, primary_key=True, index=True)
    mfr_part_number = Column(String(100), unique=True, index=True, nullable=False)
    digikey_part_number = Column(String(100), unique=True, index=True, nullable=True)
    manufacturer = Column(String(100), index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(255), nullable=False)
    detailed_description = Column(Text, nullable=True)
    lead_time = Column(String(50), nullable=True, default="Immediate / In Stock")
    datasheet_url = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category")
    connectors = relationship("Connector", back_populates="library")
