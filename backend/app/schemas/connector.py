from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class AttributeBase(BaseModel):
    attr_key: str
    attr_value: str
    group_name: Optional[str] = "General"

class AttributeCreate(AttributeBase):
    pass

class AttributeOut(AttributeBase):
    id: int

    class Config:
        from_attributes = True

class ConnectorBase(BaseModel):
    mfr_part_number: str
    digikey_part_number: Optional[str] = None
    manufacturer: str
    description: str
    detailed_description: Optional[str] = None
    lead_time: Optional[str] = "6 Weeks"
    customer_reference: Optional[str] = None
    datasheet_url: Optional[str] = None
    image_url: Optional[str] = None
    in_stock_qty: int = 0
    min_stock_alert: int = 5
    location: Optional[str] = "Kệ A1"
    library_id: Optional[int] = None
    category_id: Optional[int] = None

class ConnectorCreate(ConnectorBase):
    attributes: Optional[List[AttributeCreate]] = []

class ConnectorUpdate(BaseModel):
    mfr_part_number: Optional[str] = None
    digikey_part_number: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    lead_time: Optional[str] = None
    customer_reference: Optional[str] = None
    datasheet_url: Optional[str] = None
    image_url: Optional[str] = None
    in_stock_qty: Optional[int] = None
    min_stock_alert: Optional[int] = None
    location: Optional[str] = None
    library_id: Optional[int] = None
    category_id: Optional[int] = None
    attributes: Optional[List[AttributeCreate]] = None

class ConnectorListItemOut(ConnectorBase):
    id: int
    category_name: Optional[str] = None
    view_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ConnectorDetailOut(ConnectorBase):
    id: int
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    attributes: List[AttributeOut] = []
    view_count: Optional[int] = 0
    request_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ConnectorFilterOptions(BaseModel):
    manufacturers: List[str]
    categories: List[Dict[str, Any]]
    attributes: Dict[str, List[str]]  # e.g. {"Fastening Type": ["Bayonet Lock", ...], "Number of Positions": ["2", "4", "12"]}
