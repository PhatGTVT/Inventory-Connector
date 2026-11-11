import io
import sys
import requests
import openpyxl

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"

def run_tests():
    print("==================================================")
    print("BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG REFINE 2 (LIBRARY & STOCK)")
    print("==================================================")

    # 1. Health check
    try:
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200, f"Health check failed: {r.status_code}"
        print("✓ 1. Backend server đang hoạt động bình thường (200 OK)")
    except Exception as e:
        print(f"❌ Server không phản hồi: {e}")
        sys.exit(1)

    # 2. Login as admin
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    admin_token = r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✓ 2. Đăng nhập Admin thành công, nhận JWT token")

    # 3. Get Library Items
    r = requests.get(f"{BASE_URL}/api/library", headers=admin_headers)
    assert r.status_code == 200, f"Get library failed: {r.text}"
    lib_items = r.json()
    print(f"✓ 3. Lấy danh sách Thư viện thành công ({len(lib_items)} linh kiện)")

    # 4. Create Library Item
    test_mpn = "TEST-LIB-01"
    create_payload = {
        "mfr_part_number": test_mpn,
        "digikey_part_number": "DK-TEST-01-ND",
        "manufacturer": "Amphenol",
        "description": "Amphenol Automotive Sealed Receptacle 4P",
        "detailed_description": "IP67 waterproof, 14AWG",
        "lead_time": "Immediate / In Stock",
        "category_id": 1
    }
    r = requests.post(f"{BASE_URL}/api/library", json=create_payload, headers=admin_headers)
    if r.status_code == 400 and "đã tồn tại" in r.text:
        # Already exists from previous run, get its id
        r = requests.get(f"{BASE_URL}/api/library?q={test_mpn}", headers=admin_headers)
        created_item = r.json()[0]
    else:
        assert r.status_code == 201, f"Create library item failed: {r.text}"
        created_item = r.json()
    created_lib_id = created_item["id"]
    print(f"✓ 4. Thêm linh kiện mới vào Thư viện thành công (ID: {created_lib_id}, MPN: {test_mpn})")

    # 5. Download Template Excel
    r = requests.get(f"{BASE_URL}/api/library/template", headers=admin_headers)
    assert r.status_code == 200, f"Download template failed: {r.status_code}"
    assert "spreadsheetml" in r.headers.get("Content-Type", ""), "Not an Excel file"
    print(f"✓ 5. Tải file mẫu Excel template thành công ({len(r.content)} bytes)")

    # 6. Import Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Mã MPN", "Mã DigiKey", "Nhà sản xuất", "Danh mục", "Mô tả", "Thông số chi tiết", "Thời gian"])
    ws.append(["IMPORT-EXCEL-01", "DK-IMP-01", "Molex", "Automotive Connectors", "Molex Mini-Fit Jr 4P", "Pitch 4.2mm", "2 Weeks"])
    ws.append(["IMPORT-EXCEL-02", "DK-IMP-02", "JST", "Wire-to-Board", "JST XH 2.5mm 3P", "Pitch 2.5mm", "Immediate"])
    ws.append([test_mpn, "DK-TEST-01-ND", "Amphenol Updated", "Automotive Connectors", "Updated Description", "Updated", "Immediate"])

    excel_stream = io.BytesIO()
    wb.save(excel_stream)
    excel_stream.seek(0)

    files = {"file": ("test_import.xlsx", excel_stream, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = requests.post(f"{BASE_URL}/api/library/import-excel", files=files, headers=admin_headers)
    assert r.status_code == 200, f"Import Excel failed: {r.text}"
    import_res = r.json()
    print(f"✓ 6. Nhập file Excel thành công: {import_res['success_count']} mới, {import_res['updated_count']} cập nhật, {import_res['error_count']} lỗi")
    assert import_res["error_count"] == 0, f"Excel import had errors: {import_res['errors']}"

    # 7. Import from Library to Warehouse
    stock_payload = {
        "library_id": created_lib_id,
        "quantity": 25,
        "location": "Kệ B2-01",
        "min_stock_alert": 5
    }
    r = requests.post(f"{BASE_URL}/api/connectors/import-from-library", json=stock_payload, headers=admin_headers)
    assert r.status_code == 201, f"Stock in failed: {r.text}"
    wh_conn = r.json()
    wh_conn_id = wh_conn["id"]
    assert wh_conn["in_stock_qty"] >= 25, "Quantity mismatch"
    assert wh_conn["location"] == "Kệ B2-01", "Location mismatch"
    print(f"✓ 7a. Nhập từ Thư viện vào Kho thành công (ID kho: {wh_conn_id}, Tồn: {wh_conn['in_stock_qty']}, Vị trí: {wh_conn['location']})")

    # Restock (import again)
    stock_payload2 = {
        "library_id": created_lib_id,
        "quantity": 10,
        "location": "Kệ B2-01",
        "min_stock_alert": 5
    }
    r = requests.post(f"{BASE_URL}/api/connectors/import-from-library", json=stock_payload2, headers=admin_headers)
    assert r.status_code == 201, f"Restock failed: {r.text}"
    wh_conn_restocked = r.json()
    assert wh_conn_restocked["in_stock_qty"] == wh_conn["in_stock_qty"] + 10, "Restock quantity was not incremented correctly"
    print(f"✓ 7b. Nhập thêm (Restock) thành công: Tồn kho tự động tăng lên {wh_conn_restocked['in_stock_qty']}")

    # 8. Test Delete Library Item Protection
    # Try deleting item currently in warehouse -> must fail with 400
    r = requests.delete(f"{BASE_URL}/api/library/{created_lib_id}", headers=admin_headers)
    assert r.status_code == 400, f"Expected 400 when deleting library item in warehouse, got {r.status_code}"
    print("✓ 8a. Cơ chế bảo vệ hoạt động: Chặn xóa linh kiện trong Thư viện khi đang có trong Kho (400 Bad Request)")

    # Delete IMPORT-EXCEL-02 (not in warehouse) -> must succeed
    r = requests.get(f"{BASE_URL}/api/library?q=IMPORT-EXCEL-02", headers=admin_headers)
    imp2_id = r.json()[0]["id"]
    r = requests.delete(f"{BASE_URL}/api/library/{imp2_id}", headers=admin_headers)
    assert r.status_code == 204, f"Delete unused library item failed: {r.status_code}"
    print("✓ 8b. Xóa linh kiện Thư viện chưa nhập vào kho thành công (204 No Content)")

    # 9. Role protection
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "user", "password": "user123"})
    assert r.status_code == 200
    user_token = r.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    r = requests.post(f"{BASE_URL}/api/library", json=create_payload, headers=user_headers)
    assert r.status_code == 403, f"Expected 403 for user creating library item, got {r.status_code}"
    print("✓ 9. Phân quyền chặt chẽ: Tài khoản User thông thường bị chặn (403 Forbidden)")

    # 10. Check all Pages return 200 OK
    pages = ["/", "/admin-library", "/admin-manage", "/admin-approval", "/product-detail?id=1"]
    for page in pages:
        r = requests.get(f"{BASE_URL}{page}")
        assert r.status_code == 200, f"Page {page} returned {r.status_code}"
    print("✓ 10. Tất cả 5 trang web (Catalog, Thư viện, Quản lý kho, Duyệt yêu cầu, Chi tiết SP) phản hồi 200 OK")

    print("\n🎉 TOÀN BỘ CÁC BÀI KIỂM THỬ REFINE 2 ĐÃ VƯỢT QUA XUẤT SẮC!")

if __name__ == "__main__":
    run_tests()
