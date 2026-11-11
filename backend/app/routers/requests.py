import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from ..database import get_db
from ..models.request import InventoryRequest
from ..models.connector import Connector
from ..models.user import User
from ..models.audit_log import AuditLog
from ..models.product_metric import ProductMetric
from ..schemas.request import (
    RequestCreate,
    RequestOut,
    RequestApprove,
    RequestReject,
    RequestResponseUpdate
)
from ..services.auth_service import get_current_user, get_current_admin
from ..services.email_service import notify_new_request, notify_request_status_updated, notify_low_stock_alert

router = APIRouter(prefix="/requests", tags=["Inventory Requests"])

def build_request_out(req: InventoryRequest) -> RequestOut:
    return RequestOut(
        id=req.id,
        request_code=req.request_code,
        user_id=req.user_id,
        user_name=req.user.full_name if req.user else "Unknown",
        user_department=req.user.department if req.user else None,
        connector_id=req.connector_id,
        connector_name=req.connector.description if req.connector else "",
        connector_part_number=req.connector.mfr_part_number if req.connector else "",
        connector_image=req.connector.image_url if req.connector else None,
        current_in_stock=req.connector.in_stock_qty if req.connector else 0,
        quantity=req.quantity,
        status=req.status,
        reason=req.reason,
        admin_response=req.admin_response,
        requested_at=req.requested_at,
        processed_at=req.processed_at,
        processed_by_name=req.processor.full_name if req.processor else None
    )

@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_inventory_request(
    req_in: RequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conn = db.query(Connector).filter(Connector.id == req_in.connector_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện connector yêu cầu")

    if req_in.quantity <= 0:
        raise HTTPException(status_code=400, detail="Số lượng yêu cầu phải lớn hơn 0")

    # Generate unique readable request code like REQ-YYYYMMDD-XXXX
    code_suffix = uuid.uuid4().hex[:6].upper()
    req_code = f"REQ-{datetime.utcnow().strftime('%Y%m%d')}-{code_suffix}"

    new_request = InventoryRequest(
        request_code=req_code,
        user_id=current_user.id,
        connector_id=conn.id,
        quantity=req_in.quantity,
        status="pending",
        reason=req_in.reason,
        requested_at=datetime.utcnow()
    )
    db.add(new_request)

    # Increment request metric for suggestions
    metric = db.query(ProductMetric).filter(ProductMetric.connector_id == conn.id).first()
    if metric:
        metric.request_count += 1
    else:
        metric = ProductMetric(connector_id=conn.id, view_count=0, request_count=1)
        db.add(metric)

    db.commit()
    db.refresh(new_request)

    # Gửi email thông báo cho Admin (chạy ngầm không chặn response)
    background_tasks.add_task(
        notify_new_request,
        request_id=new_request.id,
        user_name=current_user.full_name or current_user.username,
        user_email=current_user.email,
        part_number=conn.mfr_part_number,
        quantity=new_request.quantity,
        reason=new_request.reason
    )

    return build_request_out(new_request)

@router.get("", response_model=List[RequestOut])
def get_inventory_requests(
    status_filter: Optional[str] = Query(None, description="pending, approved, rejected, etc."),
    q: Optional[str] = Query(None, description="Search by request code, connector part number, user name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InventoryRequest).join(Connector).join(User, InventoryRequest.user_id == User.id)

    # Regular user can only see their own requests
    if current_user.role != "admin":
        query = query.filter(InventoryRequest.user_id == current_user.id)

    if status_filter:
        query = query.filter(InventoryRequest.status == status_filter)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                InventoryRequest.request_code.ilike(search_pattern),
                Connector.mfr_part_number.ilike(search_pattern),
                Connector.description.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
                User.username.ilike(search_pattern)
            )
        )

    requests = query.order_by(desc(InventoryRequest.requested_at)).all()
    return [build_request_out(r) for r in requests]

@router.put("/{id}/approve", response_model=RequestOut)
def approve_request(
    id: int,
    approve_data: RequestApprove,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(InventoryRequest).filter(InventoryRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    if req.status == "approved":
        raise HTTPException(status_code=400, detail="Yêu cầu này đã được phê duyệt trước đó")

    conn = db.query(Connector).filter(Connector.id == req.connector_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Không tìm thấy connector tương ứng")

    # Check stock availability
    if conn.in_stock_qty < req.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Tồn kho không đủ để xuất! Hiện còn: {conn.in_stock_qty}, yêu cầu: {req.quantity}"
        )

    # Deduct stock
    conn.in_stock_qty -= req.quantity

    # Create audit log
    audit = AuditLog(
        connector_id=conn.id,
        user_id=admin.id,
        change_qty=-req.quantity,
        action_type="export_approved",
        note=f"Xuất kho theo phiếu duyệt {req.request_code} cho {req.user.full_name}"
    )
    db.add(audit)

    # Update request
    req.status = "approved"
    req.admin_response = approve_data.admin_response or "Đã phê duyệt xuất kho"
    req.processed_by = admin.id
    req.processed_at = datetime.utcnow()

    db.commit()
    db.refresh(req)

    # Gửi email kết quả cho Kỹ sư yêu cầu (Background Task)
    background_tasks.add_task(
        notify_request_status_updated,
        request_id=req.id,
        user_email=req.user.email if req.user else None,
        user_name=req.user.full_name if req.user else "Kỹ sư",
        part_number=conn.mfr_part_number,
        quantity=req.quantity,
        new_status="APPROVED",
        admin_notes=req.admin_response
    )

    # Cảnh báo tồn kho thấp tới Admin nếu tồn kho giảm dưới/bằng mức tối thiểu
    if conn.in_stock_qty <= conn.min_stock_alert:
        background_tasks.add_task(
            notify_low_stock_alert,
            part_number=conn.mfr_part_number,
            mfr=conn.manufacturer,
            current_qty=conn.in_stock_qty,
            min_alert_qty=conn.min_stock_alert
        )

    return build_request_out(req)

@router.put("/{id}/reject", response_model=RequestOut)
def reject_request(
    id: int,
    reject_data: RequestReject,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(InventoryRequest).filter(InventoryRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    if req.status == "approved":
        raise HTTPException(status_code=400, detail="Yêu cầu đã duyệt không thể từ chối trực tiếp (hãy điều chỉnh lại tồn kho)")

    req.status = "rejected"
    req.admin_response = reject_data.admin_response
    req.processed_by = admin.id
    req.processed_at = datetime.utcnow()

    db.commit()
    db.refresh(req)

    # Gửi email thông báo từ chối cho Kỹ sư yêu cầu (Background Task)
    background_tasks.add_task(
        notify_request_status_updated,
        request_id=req.id,
        user_email=req.user.email if req.user else None,
        user_name=req.user.full_name if req.user else "Kỹ sư",
        part_number=req.connector.mfr_part_number if req.connector else "",
        quantity=req.quantity,
        new_status="REJECTED",
        admin_notes=req.admin_response
    )

    return build_request_out(req)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_request(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(InventoryRequest).filter(InventoryRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    # If already approved, do not silently delete without user knowing; allow deleting or archiving
    db.delete(req)
    db.commit()

    return {"message": "Đã xóa yêu cầu thành công", "id": id}

@router.put("/{id}/response", response_model=RequestOut)
def update_request_response(
    id: int,
    resp_data: RequestResponseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(InventoryRequest).filter(InventoryRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    req.admin_response = resp_data.admin_response
    req.processed_by = admin.id
    req.processed_at = datetime.utcnow()

    db.commit()
    db.refresh(req)

    return build_request_out(req)
