import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from app.database import engine
from sqlalchemy import text

def generate_users_excel():
    print("Generating Danh_Sach_Tai_Khoan_He_Thong.xlsx...")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Danh Sách Tài Khoản"

    # Header styling
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Blue
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Arial", size=10)
    bold_font = Font(name="Arial", size=10, bold=True)
    admin_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Amber light
    user_fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")  # Green light

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Title block
    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = "DANH SÁCH TÀI KHOẢN HỆ THỐNG QUẢN LÝ KHO CONNECTOR (CONNECTOR INVENTORY)"
    title_cell.font = Font(name="Arial", size=14, bold=True, color="1E3A8A")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    ws.merge_cells("A2:G2")
    sub_cell = ws["A2"]
    sub_cell.value = "Ghi chú: Mật khẩu mặc định hệ thống được cấp ban đầu. Mật khẩu mới đăng ký được bảo mật mã hóa Bcrypt trong Database."
    sub_cell.font = Font(name="Arial", size=9, italic=True, color="64748B")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    headers = [
        "STT",
        "Tên đăng nhập (Username)",
        "Mật khẩu ban đầu / Ghi chú",
        "Họ và tên",
        "Vai trò (Role)",
        "Email",
        "Phòng ban / Bộ phận"
    ]
    ws.append([]) # Row 3 empty
    ws.append(headers) # Row 4
    ws.row_dimensions[4].height = 28

    for col_num, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    # Known initial passwords mapping
    known_passwords = {
        "admin": "admin123 (Mặc định Quản trị)",
        "user": "user123 (Mặc định Kỹ sư)",
        "user2": "user123 (Mặc định Xưởng)",
        "test_engineer_01": "user123 (Mặc định Test)",
        "2dphat13": "(User tự đặt khi đăng ký)",
        "manh": "(User tự đặt khi đăng ký)"
    }

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, username, full_name, email, department, role, created_at FROM users ORDER BY role ASC, id ASC")).fetchall()

        for idx, r in enumerate(rows, 1):
            row_idx = 4 + idx
            ws.row_dimensions[row_idx].height = 22
            username = r[1]
            fullname = r[2] or ""
            email = r[3] or ""
            dept = r[4] or ""
            role = (r[5] or "user").upper()

            pwd_note = known_passwords.get(username, "(User tự đặt khi đăng ký)")

            row_data = [
                idx,
                username,
                pwd_note,
                fullname,
                role,
                email,
                dept
            ]
            ws.append(row_data)

            # Apply styling
            for col_num in range(1, 8):
                cell = ws.cell(row=row_idx, column=col_num)
                cell.font = bold_font if col_num in [2, 5] else data_font
                cell.border = thin_border
                cell.alignment = Alignment(
                    horizontal="center" if col_num in [1, 5] else "left",
                    vertical="center"
                )
                if role == "ADMIN":
                    cell.fill = admin_fill
                else:
                    cell.fill = user_fill

    # Auto-fit column widths
    for col in ws.columns:
        if col[0].row < 4:
            continue
        max_len = max(len(str(cell.value or '')) for cell in col if cell.row >= 4)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 5, 14)

    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Danh_Sach_Tai_Khoan_He_Thong.xlsx"))
    wb.save(output_path)
    print(f"SUCCESS: Saved Excel file at: {output_path}")

if __name__ == "__main__":
    generate_users_excel()
