from typing import List, Any
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserLogin, UserOut, Token, UserAdminCreate, UserUpdate, UserResetPassword
from ..services.auth_service import hash_password, verify_password, create_access_token, get_current_user, get_current_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    if user_in.email:
        existing_email = db.query(User).filter(User.email == user_in.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email này đã được sử dụng")

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        department=user_in.department,
        role=user_in.role if user_in.role in ["admin", "user"] else "user",
        password_hash=hash_password(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.username, "role": new_user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản này đã bị khóa hoặc vô hiệu hóa. Vui lòng liên hệ Quản trị viên."
        )
    
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    admin: Any = Depends(get_current_admin)
):
    """Lấy danh sách toàn bộ người dùng trong hệ thống (Chỉ dành cho Admin)"""
    return db.query(User).order_by(User.role.asc(), User.id.asc()).all()

@router.get("/users/export-excel")
def export_users_excel(
    db: Session = Depends(get_db),
    admin: Any = Depends(get_current_admin)
):
    """Xuất danh sách tài khoản ra file Excel tải về trực tiếp"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh Sách Tài Khoản"

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Arial", size=10)
    bold_font = Font(name="Arial", size=10, bold=True)
    admin_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    user_fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = "DANH SÁCH TÀI KHOẢN HỆ THỐNG QUẢN LÝ KHO CONNECTOR (CONNECTOR INVENTORY)"
    title_cell.font = Font(name="Arial", size=13, bold=True, color="1E3A8A")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    headers = [
        "STT",
        "Tên đăng nhập (Username)",
        "Mật khẩu ban đầu / Ghi chú",
        "Họ và tên",
        "Vai trò (Role)",
        "Email",
        "Phòng ban / Bộ phận"
    ]
    ws.append([])
    ws.append(headers)
    ws.row_dimensions[3].height = 26

    for col_num, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    known_passwords = {
        "admin": "admin123 (Mặc định Quản trị)",
        "user": "user123 (Mặc định Kỹ sư)",
        "user2": "user123 (Mặc định Xưởng)",
        "test_engineer_01": "user123 (Mặc định Test)",
        "2dphat13": "(User tự đặt khi đăng ký)",
        "manh": "(User tự đặt khi đăng ký)"
    }

    users = db.query(User).order_by(User.role.asc(), User.id.asc()).all()
    for idx, u in enumerate(users, 1):
        row_idx = 3 + idx
        ws.row_dimensions[row_idx].height = 22
        role_str = (u.role or "user").upper()
        pwd_note = known_passwords.get(u.username, "(User tự đặt khi đăng ký)")

        row_data = [
            idx,
            u.username,
            pwd_note,
            u.full_name or "",
            role_str,
            u.email or "",
            u.department or ""
        ]
        ws.append(row_data)

        for col_num in range(1, 8):
            cell = ws.cell(row=row_idx, column=col_num)
            cell.font = bold_font if col_num in [2, 5] else data_font
            cell.border = thin_border
            cell.alignment = Alignment(
                horizontal="center" if col_num in [1, 5] else "left",
                vertical="center"
            )
            if role_str == "ADMIN":
                cell.fill = admin_fill
            else:
                cell.fill = user_fill

    for col in ws.columns:
        if col[0].row < 3:
            continue
        max_len = max(len(str(cell.value or '')) for cell in col if cell.row >= 3)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"Danh_Sach_Tai_Khoan_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    user_in: UserAdminCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin tạo mới tài khoản trực tiếp từ trang quản lý"""
    existing = db.query(User).filter(User.username == user_in.username.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập này đã tồn tại trong hệ thống")

    if user_in.email and user_in.email.strip():
        existing_email = db.query(User).filter(User.email == user_in.email.strip()).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email này đã được sử dụng bởi tài khoản khác")

    new_user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip() if user_in.email else None,
        full_name=user_in.full_name.strip(),
        department=user_in.department.strip() if user_in.department else None,
        role=user_in.role if user_in.role in ["admin", "user"] else "user",
        is_active=user_in.is_active,
        password_hash=hash_password(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{id}", response_model=UserOut)
def admin_update_user(
    id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin cập nhật thông tin cá nhân hoặc vai trò của tài khoản"""
    target = db.query(User).filter(User.id == id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # Không cho phép tự giáng cấp tài khoản Admin của chính mình
    if admin.id == id and user_update.role and user_update.role != "admin":
        raise HTTPException(status_code=400, detail="Bạn không thể tự giáng cấp quyền Admin của chính mình")

    if user_update.full_name is not None and user_update.full_name.strip():
        target.full_name = user_update.full_name.strip()

    if user_update.email is not None:
        email_val = user_update.email.strip() if user_update.email else None
        if email_val:
            ex = db.query(User).filter(User.email == email_val, User.id != id).first()
            if ex:
                raise HTTPException(status_code=400, detail="Email này đã thuộc về tài khoản khác")
        target.email = email_val

    if user_update.department is not None:
        target.department = user_update.department.strip() if user_update.department else None

    if user_update.role in ["admin", "user"]:
        target.role = user_update.role

    if user_update.is_active is not None:
        if admin.id == id and not user_update.is_active:
            raise HTTPException(status_code=400, detail="Bạn không thể tự khóa tài khoản Admin của chính mình")
        target.is_active = user_update.is_active

    db.commit()
    db.refresh(target)
    return target

@router.put("/users/{id}/reset-password")
def admin_reset_password(
    id: int,
    pwd_in: UserResetPassword,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin đặt lại mật khẩu cho tài khoản"""
    target = db.query(User).filter(User.id == id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if not pwd_in.new_password or len(pwd_in.new_password) < 4:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 4 ký tự")

    target.password_hash = hash_password(pwd_in.new_password)
    db.commit()
    return {"message": f"Đã đặt lại mật khẩu thành công cho tài khoản '{target.username}'"}

@router.put("/users/{id}/toggle-status", response_model=UserOut)
def admin_toggle_user_status(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin Khóa hoặc Mở khóa tài khoản người dùng"""
    target = db.query(User).filter(User.id == id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if admin.id == id:
        raise HTTPException(status_code=400, detail="Bạn không thể tự khóa tài khoản Admin của chính mình")

    target.is_active = not target.is_active
    db.commit()
    db.refresh(target)
    return target

@router.delete("/users/{id}")
def admin_delete_user(
    id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin xóa tài khoản (Áp dụng quy tắc xóa an toàn & bảo toàn kiểm toán)"""
    target = db.query(User).filter(User.id == id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    # 1. Chặn tự xóa
    if admin.id == id:
        raise HTTPException(status_code=400, detail="Bạn không thể tự xóa tài khoản của chính mình")

    # 2. Chặn xóa nếu hệ thống không còn Admin nào khác đang hoạt động
    if target.role == "admin":
        other_active_admins = db.query(User).filter(User.role == "admin", User.is_active == True, User.id != id).count()
        if other_active_admins < 1:
            raise HTTPException(status_code=400, detail="Không thể xóa vì không còn Quản trị viên (Admin) nào khác đang hoạt động trong hệ thống")

    # 3. Kiểm tra ràng buộc lịch sử kho (InventoryRequest và AuditLog)
    from ..models.request import InventoryRequest
    from ..models.audit_log import AuditLog
    req_count = db.query(InventoryRequest).filter(
        (InventoryRequest.user_id == id) | (InventoryRequest.processed_by == id)
    ).count()
    audit_count = db.query(AuditLog).filter(AuditLog.user_id == id).count()

    if req_count > 0 or audit_count > 0:
        # Xóa an toàn: Vô hiệu hóa vĩnh viễn để bảo tồn dữ liệu kiểm toán
        target.is_active = False
        db.commit()
        return {
            "status": "deactivated",
            "message": f"Tài khoản '{target.username}' đã có {req_count} phiếu yêu cầu xuất kho và {audit_count} nhật ký kho. Để bảo vệ toàn vẹn lịch sử kiểm toán, tài khoản đã được chuyển sang trạng thái 'Khóa vĩnh viễn' thay vì xóa cứng khỏi cơ sở dữ liệu."
        }
    else:
        # Xóa cứng hoàn toàn
        username_deleted = target.username
        db.delete(target)
        db.commit()
        return {
            "status": "deleted",
            "message": f"Đã xóa vĩnh viễn tài khoản '{username_deleted}' khỏi hệ thống."
        }

