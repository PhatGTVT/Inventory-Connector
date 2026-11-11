from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class RequestCreate(BaseModel):
    connector_id: int
    quantity: int
    reason: Optional[str] = None

class RequestApprove(BaseModel):
    admin_response: Optional[str] = "Yêu cầu đã được duyệt thành công."

class RequestReject(BaseModel):
    admin_response: str = "Yêu cầu không được duyệt do vượt hạn mức hoặc hết tồn kho."

class RequestResponseUpdate(BaseModel):
    admin_response: str

class RequestOut(BaseModel):
    id: int
    request_code: str
    user_id: int
    user_name: str
    user_department: Optional[str] = None
    connector_id: int
    connector_name: str
    connector_part_number: str
    connector_image: Optional[str] = None
    current_in_stock: int
    quantity: int
    status: str
    reason: Optional[str] = None
    admin_response: Optional[str] = None
    requested_at: datetime
    processed_at: Optional[datetime] = None
    processed_by_name: Optional[str] = None

    class Config:
        from_attributes = True
