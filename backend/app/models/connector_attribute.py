from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class ConnectorAttribute(Base):
    __tablename__ = "connector_attributes"

    id = Column(Integer, primary_key=True, index=True)
    connector_id = Column(Integer, ForeignKey("connectors.id", ondelete="CASCADE"), nullable=False, index=True)
    attr_key = Column(String(100), nullable=False, index=True)
    attr_value = Column(String(255), nullable=False)
    group_name = Column(String(100), default="General", nullable=False)

    connector = relationship("Connector", back_populates="attributes")
