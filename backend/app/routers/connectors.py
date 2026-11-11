from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from ..database import get_db
from ..models.connector import Connector
from ..models.library import ConnectorLibrary
from ..models.connector_attribute import ConnectorAttribute
from ..models.category import Category
from ..models.product_metric import ProductMetric
from ..models.audit_log import AuditLog
from ..schemas.connector import (
    ConnectorListItemOut,
    ConnectorDetailOut,
    ConnectorCreate,
    ConnectorUpdate,
    ConnectorFilterOptions,
    AttributeOut
)
from ..schemas.library import WarehouseImportFromLibrary
from ..services.auth_service import get_current_admin

router = APIRouter(prefix="/connectors", tags=["Connectors"])

@router.get("/filters/options", response_model=ConnectorFilterOptions)
def get_filter_options(db: Session = Depends(get_db)):
    # Distinct manufacturers
    mfrs = [r[0] for r in db.query(Connector.manufacturer).distinct().order_by(Connector.manufacturer).all() if r[0]]
    
    # Categories
    cats = db.query(Category.id, Category.name, Category.slug).all()
    cat_list = [{"id": c[0], "name": c[1], "slug": c[2]} for c in cats]

    # Key attributes to filter by
    target_keys = ["Fastening Type", "Number of Positions", "Contact Type", "Shell Size - Insert", "Housing Color", "Ingress Protection"]
    attr_options: Dict[str, List[str]] = {}
    
    for key in target_keys:
        vals = db.query(ConnectorAttribute.attr_value)\
            .filter(ConnectorAttribute.attr_key == key)\
            .distinct()\
            .order_by(ConnectorAttribute.attr_value)\
            .all()
        attr_options[key] = [v[0] for v in vals if v[0]]

    return ConnectorFilterOptions(
        manufacturers=mfrs,
        categories=cat_list,
        attributes=attr_options
    )

@router.get("/suggestions/frequently-viewed", response_model=List[ConnectorListItemOut])
def get_frequently_viewed_connectors(limit: int = 4, db: Session = Depends(get_db)):
    # Query connectors with highest view_count or request_count in metrics
    query = db.query(Connector, func.coalesce(ProductMetric.view_count, 0).label("views"))\
        .outerjoin(ProductMetric, Connector.id == ProductMetric.connector_id)\
        .outerjoin(Category, Connector.category_id == Category.id)\
        .order_by(desc("views"), desc(Connector.id))\
        .limit(limit)

    results = []
    for conn, views in query.all():
        item = ConnectorListItemOut(
            id=conn.id,
            mfr_part_number=conn.mfr_part_number,
            digikey_part_number=conn.digikey_part_number,
            manufacturer=conn.manufacturer,
            description=conn.description,
            detailed_description=conn.detailed_description,
            lead_time=conn.lead_time,
            customer_reference=conn.customer_reference,
            datasheet_url=conn.datasheet_url,
            image_url=conn.image_url,
            in_stock_qty=conn.in_stock_qty,
            min_stock_alert=conn.min_stock_alert,
            category_id=conn.category_id,
            category_name=conn.category.name if conn.category else None,
            view_count=views
        )
        results.append(item)
    return results

@router.get("", response_model=List[ConnectorListItemOut])
def get_connectors(
    q: Optional[str] = Query(None, description="Search term across part number, manufacturer, or description"),
    category_id: Optional[int] = Query(None),
    manufacturer: Optional[str] = Query(None),
    fastening_type: Optional[str] = Query(None),
    positions: Optional[str] = Query(None),
    contact_type: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Connector).outerjoin(ProductMetric, Connector.id == ProductMetric.connector_id)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Connector.mfr_part_number.ilike(search_pattern),
                Connector.digikey_part_number.ilike(search_pattern),
                Connector.description.ilike(search_pattern),
                Connector.detailed_description.ilike(search_pattern)
            )
        )

    if category_id:
        query = query.filter(Connector.category_id == category_id)

    if manufacturer:
        query = query.filter(Connector.manufacturer == manufacturer)

    # Dynamic attribute filters
    attr_filters = []
    if fastening_type:
        attr_filters.append(("Fastening Type", fastening_type))
    if positions:
        attr_filters.append(("Number of Positions", positions))
    if contact_type:
        attr_filters.append(("Contact Type", contact_type))
    if color:
        attr_filters.append(("Housing Color", color))

    for k, v in attr_filters:
        query = query.filter(
            Connector.id.in_(
                db.query(ConnectorAttribute.connector_id)
                .filter(ConnectorAttribute.attr_key == k, ConnectorAttribute.attr_value == v)
            )
        )

    connectors = query.order_by(desc(Connector.id)).offset(skip).limit(limit).all()

    results = []
    for conn in connectors:
        views = conn.metric.view_count if conn.metric else 0
        item = ConnectorListItemOut(
            id=conn.id,
            mfr_part_number=conn.mfr_part_number,
            digikey_part_number=conn.digikey_part_number,
            manufacturer=conn.manufacturer,
            description=conn.description,
            detailed_description=conn.detailed_description,
            lead_time=conn.lead_time,
            customer_reference=conn.customer_reference,
            datasheet_url=conn.datasheet_url,
            image_url=conn.image_url,
            in_stock_qty=conn.in_stock_qty,
            min_stock_alert=conn.min_stock_alert,
            category_id=conn.category_id,
            category_name=conn.category.name if conn.category else None,
            view_count=views
        )
        results.append(item)

    return results

@router.get("/{id}", response_model=ConnectorDetailOut)
def get_connector_detail(id: int, db: Session = Depends(get_db)):
    conn = db.query(Connector).filter(Connector.id == id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện connector")

    # Increment view metric for recommendation engine
    metric = db.query(ProductMetric).filter(ProductMetric.connector_id == id).first()
    if not metric:
        metric = ProductMetric(connector_id=id, view_count=1, last_viewed_at=datetime.utcnow())
        db.add(metric)
    else:
        metric.view_count += 1
        metric.last_viewed_at = datetime.utcnow()
    db.commit()

    attrs = [
        AttributeOut(
            id=a.id,
            attr_key=a.attr_key,
            attr_value=a.attr_value,
            group_name=a.group_name
        )
        for a in conn.attributes
    ]

    return ConnectorDetailOut(
        id=conn.id,
        mfr_part_number=conn.mfr_part_number,
        digikey_part_number=conn.digikey_part_number,
        manufacturer=conn.manufacturer,
        description=conn.description,
        detailed_description=conn.detailed_description,
        lead_time=conn.lead_time,
        customer_reference=conn.customer_reference,
        datasheet_url=conn.datasheet_url,
        image_url=conn.image_url,
        in_stock_qty=conn.in_stock_qty,
        min_stock_alert=conn.min_stock_alert,
        category_id=conn.category_id,
        category_name=conn.category.name if conn.category else None,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
        attributes=attrs,
        view_count=metric.view_count if metric else 0,
        request_count=metric.request_count if metric else 0
    )

@router.post("", response_model=ConnectorDetailOut, status_code=status.HTTP_201_CREATED)
def create_connector(
    conn_in: ConnectorCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    # Check duplicate MPN
    existing = db.query(Connector).filter(Connector.mfr_part_number == conn_in.mfr_part_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã linh kiện nhà sản xuất (MPN) đã tồn tại")

    # Check duplicate DigiKey PN if provided
    if conn_in.digikey_part_number and conn_in.digikey_part_number.strip():
        existing_dk = db.query(Connector).filter(Connector.digikey_part_number == conn_in.digikey_part_number.strip()).first()
        if existing_dk:
            raise HTTPException(status_code=400, detail=f"Mã DigiKey Part Number '{conn_in.digikey_part_number.strip()}' đã tồn tại trong hệ thống")

    conn_data = conn_in.model_dump(exclude={"attributes"})
    
    # Normalize empty strings to None to prevent unique constraint violations on empty strings
    for k in ["digikey_part_number", "detailed_description", "datasheet_url", "image_url", "customer_reference", "lead_time"]:
        if k in conn_data and (conn_data[k] is None or not str(conn_data[k]).strip()):
            conn_data[k] = None
        elif k in conn_data and conn_data[k] is not None:
            conn_data[k] = str(conn_data[k]).strip()

    try:
        new_conn = Connector(**conn_data)
        db.add(new_conn)
        db.commit()
        db.refresh(new_conn)

        # Add attributes
        if conn_in.attributes:
            for attr in conn_in.attributes:
                new_attr = ConnectorAttribute(
                    connector_id=new_conn.id,
                    attr_key=attr.attr_key.strip(),
                    attr_value=attr.attr_value.strip(),
                    group_name=(attr.group_name or "General").strip()
                )
                db.add(new_attr)

        # Initialize metric
        metric = ProductMetric(connector_id=new_conn.id, view_count=0, request_count=0)
        db.add(metric)
        db.commit()
        db.refresh(new_conn)

        return get_connector_detail(new_conn.id, db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi khi tạo connector: {str(e)}")

@router.put("/{id}", response_model=ConnectorDetailOut)
def update_connector(
    id: int,
    conn_in: ConnectorUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    conn = db.query(Connector).filter(Connector.id == id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện connector")

    # Check duplicate DigiKey PN if updated
    if conn_in.digikey_part_number and conn_in.digikey_part_number.strip():
        existing_dk = db.query(Connector).filter(
            Connector.digikey_part_number == conn_in.digikey_part_number.strip(),
            Connector.id != id
        ).first()
        if existing_dk:
            raise HTTPException(status_code=400, detail=f"Mã DigiKey Part Number '{conn_in.digikey_part_number.strip()}' đã được dùng cho linh kiện khác")

    update_data = conn_in.model_dump(exclude_unset=True, exclude={"attributes"})
    for field, val in update_data.items():
        if isinstance(val, str) and not val.strip():
            val = None
        setattr(conn, field, val)

    try:
        # Update attributes if specified
        if conn_in.attributes is not None:
            db.query(ConnectorAttribute).filter(ConnectorAttribute.connector_id == id).delete()
            for attr in conn_in.attributes:
                new_attr = ConnectorAttribute(
                    connector_id=id,
                    attr_key=attr.attr_key.strip(),
                    attr_value=attr.attr_value.strip(),
                    group_name=(attr.group_name or "General").strip()
                )
                db.add(new_attr)

        conn.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conn)

        return get_connector_detail(id, db)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi khi cập nhật connector: {str(e)}")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connector(
    id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    conn = db.query(Connector).filter(Connector.id == id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện connector")

    try:
        # Clean up related records in proper order to satisfy foreign keys
        from ..models.request import InventoryRequest
        from ..models.audit_log import AuditLog
        db.query(InventoryRequest).filter(InventoryRequest.connector_id == id).delete(synchronize_session=False)
        db.query(AuditLog).filter(AuditLog.connector_id == id).delete(synchronize_session=False)
        db.query(ConnectorAttribute).filter(ConnectorAttribute.connector_id == id).delete(synchronize_session=False)
        db.query(ProductMetric).filter(ProductMetric.connector_id == id).delete(synchronize_session=False)

        db.delete(conn)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Không thể xóa linh kiện do ràng buộc dữ liệu: {str(e)}")

    return None

@router.post("/import-from-library", response_model=ConnectorDetailOut, status_code=status.HTTP_201_CREATED)
def import_connector_from_library(
    payload: WarehouseImportFromLibrary,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    lib_item = db.query(ConnectorLibrary).filter(ConnectorLibrary.id == payload.library_id).first()
    if not lib_item:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện trong Thư viện.")

    # Check if already in warehouse
    existing_wh = db.query(Connector).filter(
        or_(
            Connector.library_id == payload.library_id,
            Connector.mfr_part_number == lib_item.mfr_part_number
        )
    ).first()

    try:
        if existing_wh:
            # Increment quantity (Restock)
            existing_wh.in_stock_qty += payload.quantity
            if payload.location:
                existing_wh.location = payload.location.strip()
            if payload.min_stock_alert:
                existing_wh.min_stock_alert = payload.min_stock_alert
            if not existing_wh.library_id:
                existing_wh.library_id = lib_item.id

            # Update specs and image from library
            if lib_item.image_url: existing_wh.image_url = lib_item.image_url
            if lib_item.datasheet_url: existing_wh.datasheet_url = lib_item.datasheet_url
            if lib_item.description: existing_wh.description = lib_item.description
            if lib_item.detailed_description: existing_wh.detailed_description = lib_item.detailed_description
            existing_wh.updated_at = datetime.utcnow()

            audit = AuditLog(
                connector_id=existing_wh.id,
                user_id=admin.id,
                action_type="import_library",
                change_qty=payload.quantity,
                note=f"Nhập thêm từ Thư viện: +{payload.quantity} cái (Tồn kho mới: {existing_wh.in_stock_qty}), Vị trí: {existing_wh.location}"
            )
            db.add(audit)
            db.commit()
            db.refresh(existing_wh)
            return get_connector_detail(existing_wh.id, db)
        else:
            # Create new warehouse item from library
            new_conn = Connector(
                library_id=lib_item.id,
                mfr_part_number=lib_item.mfr_part_number,
                digikey_part_number=lib_item.digikey_part_number,
                manufacturer=lib_item.manufacturer,
                description=lib_item.description,
                detailed_description=lib_item.detailed_description,
                lead_time=lib_item.lead_time or "Immediate / In Stock",
                datasheet_url=lib_item.datasheet_url,
                image_url=lib_item.image_url,
                category_id=lib_item.category_id,
                in_stock_qty=payload.quantity,
                min_stock_alert=payload.min_stock_alert or 5,
                location=payload.location.strip() if payload.location else "Kệ A1"
            )
            db.add(new_conn)
            db.flush()  # Retrieve new_conn.id safely within the same transaction

            # Initial metric
            metric = ProductMetric(connector_id=new_conn.id, view_count=0, request_count=0)
            db.add(metric)

            audit = AuditLog(
                connector_id=new_conn.id,
                user_id=admin.id,
                action_type="import_library",
                change_qty=payload.quantity,
                note=f"Nhập mới từ Thư viện vào Kho: Số lượng {payload.quantity}, Vị trí {new_conn.location}"
            )
            db.add(audit)
            db.commit()  # Single atomic commit for connector, metric, and audit log
            db.refresh(new_conn)
            return get_connector_detail(new_conn.id, db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi nhập linh kiện vào kho: {str(e)}")


