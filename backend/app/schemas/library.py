from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class LibraryItemBase(BaseModel):
    mfr_part_number: str
    digikey_part_number: Optional[str] = None
    manufacturer: str
    category_id: Optional[int] = None
    description: str
    detailed_description: Optional[str] = None
    lead_time: Optional[str] = "Immediate / In Stock"
    datasheet_url: Optional[str] = None
    image_url: Optional[str] = None

class LibraryItemCreate(LibraryItemBase):
    pass

class LibraryItemUpdate(BaseModel):
    mfr_part_number: Optional[str] = None
    digikey_part_number: Optional[str] = None
    manufacturer: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    lead_time: Optional[str] = None
    datasheet_url: Optional[str] = None
    image_url: Optional[str] = None

class LibraryItemOut(LibraryItemBase):
    id: int
    category_name: Optional[str] = None
    created_at: Optional[datetime] = None
    in_warehouse: bool = False
    warehouse_stock_qty: int = 0
    warehouse_connector_id: Optional[int] = None

    class Config:
        from_attributes = True

class LibraryImportResult(BaseModel):
    total_rows: int
    success_count: int
    updated_count: int
    error_count: int
    errors: List[str] = []

class WarehouseImportFromLibrary(BaseModel):
    library_id: int
    quantity: int = 10
    location: Optional[str] = "Kệ A1"
    min_stock_alert: Optional[int] = 5
