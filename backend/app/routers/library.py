import io
import csv
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
import openpyxl

from ..database import get_db
from ..models.library import ConnectorLibrary
from ..models.connector import Connector
from ..models.category import Category
from ..schemas.library import (
    LibraryItemCreate,
    LibraryItemUpdate,
    LibraryItemOut,
    LibraryImportResult
)
from ..services.auth_service import get_current_admin

router = APIRouter(prefix="/library", tags=["Connector Library"])

@router.get("", response_model=List[LibraryItemOut])
def get_library_items(
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    manufacturer: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ConnectorLibrary)

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                ConnectorLibrary.mfr_part_number.ilike(pattern),
                ConnectorLibrary.digikey_part_number.ilike(pattern),
                ConnectorLibrary.description.ilike(pattern),
                ConnectorLibrary.detailed_description.ilike(pattern)
            )
        )

    if manufacturer and manufacturer.strip():
        query = query.filter(ConnectorLibrary.manufacturer.ilike(manufacturer.strip()))

    if category_id:
        query = query.filter(ConnectorLibrary.category_id == category_id)

    items = query.order_by(desc(ConnectorLibrary.id)).offset(skip).limit(limit).all()

    # Preload warehouse presence
    lib_ids = [item.id for item in items]
    warehouse_map = {}
    if lib_ids:
        wh_rows = db.query(
            Connector.library_id,
            Connector.id,
            Connector.in_stock_qty
        ).filter(Connector.library_id.in_(lib_ids)).all()
        for wh in wh_rows:
            warehouse_map[wh[0]] = {
                "in_warehouse": True,
                "warehouse_connector_id": wh[1],
                "warehouse_stock_qty": wh[2]
            }

    results = []
    for item in items:
        wh_info = warehouse_map.get(item.id, {
            "in_warehouse": False,
            "warehouse_connector_id": None,
            "warehouse_stock_qty": 0
        })
        results.append(
            LibraryItemOut(
                id=item.id,
                mfr_part_number=item.mfr_part_number,
                digikey_part_number=item.digikey_part_number,
                manufacturer=item.manufacturer,
                category_id=item.category_id,
                category_name=item.category.name if item.category else None,
                description=item.description,
                detailed_description=item.detailed_description,
                lead_time=item.lead_time,
                datasheet_url=item.datasheet_url,
                image_url=item.image_url,
                created_at=item.created_at,
                in_warehouse=wh_info["in_warehouse"],
                warehouse_stock_qty=wh_info["warehouse_stock_qty"],
                warehouse_connector_id=wh_info["warehouse_connector_id"]
            )
        )

    return results

@router.get("/template")
def download_excel_template():
    """Tạo và tải về file Excel mẫu để nhập hàng loạt linh kiện vào Thư viện"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Connector Library Template"

    headers = [
        "Mã MPN (*)",
        "Mã DigiKey P/N",
        "Nhà sản xuất (*)",
        "Tên danh mục",
        "Mô tả tóm tắt (*)",
        "Mô tả kỹ thuật chi tiết",
        "Thời gian đặt hàng",
        "Đường dẫn Datasheet URL",
        "Đường dẫn Ảnh"
    ]
    ws.append(headers)

    # Dòng mẫu 1
    ws.append([
        "DT04-2P",
        "1734-DT04-2P-ND",
        "TE Connectivity",
        "Automotive Connectors",
        "Receptacle housing, 2 positions, IP68 rated",
        "Series DT, 2 Contacts, Male Pin Housing, Wedgelock W2P required",
        "Immediate / In Stock",
        "https://www.te.com/commerce/DocumentDelivery/DDEController?DocNr=DT04-2P",
        "/assets/images/dt04_2p.jpg"
    ])

    # Dòng mẫu 2
    ws.append([
        "282104-1",
        "A105432-ND",
        "TE Connectivity",
        "AMP Superseal 1.5mm",
        "Superseal 1.5mm Series 2-Position Tab Housing",
        "Pitch 6.0mm, IP67 Waterproof automotive plug",
        "4 Weeks",
        "",
        ""
    ])

    # Tự động co giãn độ rộng cột
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"Connector_Library_Template_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/import-excel", response_model=LibraryImportResult)
async def import_excel_to_library(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Any = Depends(get_current_admin)
):
    """Tiếp nhận file .xlsx hoặc .csv và nạp hàng loạt connector vào Thư viện"""
    filename = file.filename.lower() if file.filename else ""
    if not (filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".csv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Định dạng tệp không được hỗ trợ. Vui lòng tải lên tệp .xlsx hoặc .csv."
        )

    content = await file.read()
    rows_data = []

    if filename.endswith(".csv"):
        text_stream = io.StringIO(content.decode("utf-8-sig", errors="ignore"))
        reader = csv.reader(text_stream)
        for row in reader:
            if any(cell.strip() for cell in row):
                rows_data.append([c.strip() for c in row])
    else:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(values_only=True):
            if any(row):
                rows_data.append([str(c).strip() if c is not None else "" for c in row])

    if len(rows_data) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp không chứa dữ liệu hoặc chỉ có dòng tiêu đề."
        )

    # Map headers
    headers = [h.lower() for h in rows_data[0]]
    def find_col_idx(aliases):
        for idx, h in enumerate(headers):
            for alias in aliases:
                if alias in h:
                    return idx
        return -1

    idx_mpn = find_col_idx(["mpn", "mã linh kiện", "mã mpn", "part number"])
    idx_dk = find_col_idx(["digikey", "dk_pn", "digi-key", "mã digikey"])
    idx_mfr = find_col_idx(["nhà sản xuất", "manufacturer", "mfr", "hãng"])
    idx_cat = find_col_idx(["danh mục", "category", "nhóm"])
    idx_desc = find_col_idx(["mô tả tóm tắt", "description", "mô tả"])
    idx_detail = find_col_idx(["chi tiết", "detailed", "thông số"])
    idx_lead = find_col_idx(["lead time", "thời gian"])
    idx_ds = find_col_idx(["datasheet", "pdf"])
    idx_img = find_col_idx(["ảnh", "image", "hình"])

    if idx_mpn == -1 or idx_mfr == -1 or idx_desc == -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp thiếu các cột bắt buộc: 'Mã MPN', 'Nhà sản xuất', hoặc 'Mô tả tóm tắt'."
        )

    # Cache categories
    categories = {c.name.lower(): c.id for c in db.query(Category).all()}

    success_count = 0
    updated_count = 0
    error_count = 0
    errors = []

    for row_num, row in enumerate(rows_data[1:], start=2):
        try:
            mpn = row[idx_mpn] if idx_mpn < len(row) else ""
            if not mpn:
                error_count += 1
                errors.append(f"Dòng {row_num}: Thiếu mã MPN bắt buộc.")
                continue

            mfr = row[idx_mfr] if idx_mfr < len(row) else ""
            if not mfr:
                error_count += 1
                errors.append(f"Dòng {row_num} ({mpn}): Thiếu tên nhà sản xuất.")
                continue

            desc_val = row[idx_desc] if idx_desc < len(row) else ""
            if not desc_val:
                desc_val = f"Connector {mpn} - {mfr}"

            dk_val = (row[idx_dk] if idx_dk != -1 and idx_dk < len(row) else "") or None
            detail_val = (row[idx_detail] if idx_detail != -1 and idx_detail < len(row) else "") or None
            lead_val = (row[idx_lead] if idx_lead != -1 and idx_lead < len(row) else "") or "Immediate / In Stock"
            ds_val = (row[idx_ds] if idx_ds != -1 and idx_ds < len(row) else "") or None
            img_val = (row[idx_img] if idx_img != -1 and idx_img < len(row) else "") or None

            # Handle category
            cat_id = None
            if idx_cat != -1 and idx_cat < len(row) and row[idx_cat]:
                cat_name = row[idx_cat].strip()
                cat_lower = cat_name.lower()
                if cat_lower in categories:
                    cat_id = categories[cat_lower]
                else:
                    # Create new category if not existing
                    new_cat = Category(name=cat_name, slug=cat_lower.replace(" ", "-"))
                    db.add(new_cat)
                    db.commit()
                    db.refresh(new_cat)
                    cat_id = new_cat.id
                    categories[cat_lower] = cat_id

            # Check existing by MPN
            existing = db.query(ConnectorLibrary).filter(ConnectorLibrary.mfr_part_number == mpn).first()
            if existing:
                # Update existing
                existing.manufacturer = mfr
                existing.description = desc_val
                if dk_val: existing.digikey_part_number = dk_val
                if detail_val: existing.detailed_description = detail_val
                if lead_val: existing.lead_time = lead_val
                if ds_val: existing.datasheet_url = ds_val
                if img_val: existing.image_url = img_val
                if cat_id: existing.category_id = cat_id
                db.commit()
                updated_count += 1
            else:
                new_lib = ConnectorLibrary(
                    mfr_part_number=mpn,
                    digikey_part_number=dk_val,
                    manufacturer=mfr,
                    category_id=cat_id,
                    description=desc_val,
                    detailed_description=detail_val,
                    lead_time=lead_val,
                    datasheet_url=ds_val,
                    image_url=img_val
                )
                db.add(new_lib)
                db.commit()
                success_count += 1
        except Exception as e:
            db.rollback()
            error_count += 1
            errors.append(f"Dòng {row_num}: Lỗi xử lý ({str(e)})")

    return LibraryImportResult(
        total_rows=len(rows_data) - 1,
        success_count=success_count,
        updated_count=updated_count,
        error_count=error_count,
        errors=errors[:20]  # Return at most 20 errors
    )

@router.get("/{id}", response_model=LibraryItemOut)
def get_library_item(id: int, db: Session = Depends(get_db)):
    item = db.query(ConnectorLibrary).filter(ConnectorLibrary.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện trong thư viện.")

    wh = db.query(Connector).filter(Connector.library_id == item.id).first()
    return LibraryItemOut(
        id=item.id,
        mfr_part_number=item.mfr_part_number,
        digikey_part_number=item.digikey_part_number,
        manufacturer=item.manufacturer,
        category_id=item.category_id,
        category_name=item.category.name if item.category else None,
        description=item.description,
        detailed_description=item.detailed_description,
        lead_time=item.lead_time,
        datasheet_url=item.datasheet_url,
        image_url=item.image_url,
        created_at=item.created_at,
        in_warehouse=wh is not None,
        warehouse_stock_qty=wh.in_stock_qty if wh else 0,
        warehouse_connector_id=wh.id if wh else None
    )

@router.post("", response_model=LibraryItemOut, status_code=status.HTTP_201_CREATED)
def create_library_item(
    payload: LibraryItemCreate,
    db: Session = Depends(get_db),
    admin: Any = Depends(get_current_admin)
):
    mpn = payload.mfr_part_number.strip()
    existing = db.query(ConnectorLibrary).filter(ConnectorLibrary.mfr_part_number == mpn).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã MPN '{mpn}' đã tồn tại trong Thư viện."
        )

    dk = payload.digikey_part_number.strip() if payload.digikey_part_number else None
    if dk:
        existing_dk = db.query(ConnectorLibrary).filter(ConnectorLibrary.digikey_part_number == dk).first()
        if existing_dk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã DigiKey P/N '{dk}' đã tồn tại trong Thư viện."
            )

    item = ConnectorLibrary(
        mfr_part_number=mpn,
        digikey_part_number=dk,
        manufacturer=payload.manufacturer.strip(),
        category_id=payload.category_id,
        description=payload.description.strip(),
        detailed_description=payload.detailed_description,
        lead_time=payload.lead_time,
        datasheet_url=payload.datasheet_url,
        image_url=payload.image_url
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return LibraryItemOut(
        id=item.id,
        mfr_part_number=item.mfr_part_number,
        digikey_part_number=item.digikey_part_number,
        manufacturer=item.manufacturer,
        category_id=item.category_id,
        category_name=item.category.name if item.category else None,
        description=item.description,
        detailed_description=item.detailed_description,
        lead_time=item.lead_time,
        datasheet_url=item.datasheet_url,
        image_url=item.image_url,
        created_at=item.created_at,
        in_warehouse=False,
        warehouse_stock_qty=0,
        warehouse_connector_id=None
    )

@router.put("/{id}", response_model=LibraryItemOut)
def update_library_item(
    id: int,
    payload: LibraryItemUpdate,
    db: Session = Depends(get_db),
    admin: Any = Depends(get_current_admin)
):
    item = db.query(ConnectorLibrary).filter(ConnectorLibrary.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện trong thư viện.")

    update_data = payload.dict(exclude_unset=True)
    if "mfr_part_number" in update_data and update_data["mfr_part_number"]:
        new_mpn = update_data["mfr_part_number"].strip()
        existing = db.query(ConnectorLibrary).filter(
            ConnectorLibrary.mfr_part_number == new_mpn,
            ConnectorLibrary.id != id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Mã MPN '{new_mpn}' đã tồn tại.")
        item.mfr_part_number = new_mpn

    for field, val in update_data.items():
        if field != "mfr_part_number":
            setattr(item, field, val)

    db.commit()
    db.refresh(item)

    wh = db.query(Connector).filter(Connector.library_id == item.id).first()
    return LibraryItemOut(
        id=item.id,
        mfr_part_number=item.mfr_part_number,
        digikey_part_number=item.digikey_part_number,
        manufacturer=item.manufacturer,
        category_id=item.category_id,
        category_name=item.category.name if item.category else None,
        description=item.description,
        detailed_description=item.detailed_description,
        lead_time=item.lead_time,
        datasheet_url=item.datasheet_url,
        image_url=item.image_url,
        created_at=item.created_at,
        in_warehouse=wh is not None,
        warehouse_stock_qty=wh.in_stock_qty if wh else 0,
        warehouse_connector_id=wh.id if wh else None
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_library_item(
    id: int,
    db: Session = Depends(get_db),
    admin: Any = Depends(get_current_admin)
):
    item = db.query(ConnectorLibrary).filter(ConnectorLibrary.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện trong thư viện.")

    # Check if this library item is currently in the warehouse
    in_wh = db.query(Connector).filter(Connector.library_id == id).first()
    if in_wh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể xóa '{item.mfr_part_number}' khỏi Thư viện vì linh kiện này đang có trong Kho hàng (Mã kho #{in_wh.id}, tồn kho: {in_wh.in_stock_qty}). Vui lòng xóa khỏi Kho trước."
        )

    db.delete(item)
    db.commit()
    return None
