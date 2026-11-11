# Connector Inventory - Hệ thống Quản lý Kho Linh kiện Connector

Ứng dụng web quản lý kho và tra cứu linh kiện đầu nối (connector), kết hợp hai nghiệp vụ:

1. **Catalog tra cứu kỹ thuật** theo phong cách DigiKey: tìm kiếm, bộ lọc đa thuộc tính, bảng thông số kỹ thuật, datasheet PDF, ảnh thực tế và trạng thái tồn kho.
2. **Quy trình xuất kho nội bộ**: kỹ sư gửi yêu cầu cấp phát, thủ kho phê duyệt và hệ thống tự động trừ tồn kho.

## Tính năng chính

**Người dùng (user)**
- Đăng ký, đăng nhập (JWT)
- Tìm kiếm theo MPN, DigiKey Part Number, tên, mô tả
- Lọc theo danh mục, nhà sản xuất, kiểu khóa, số chân, kiểu tiếp điểm, màu vỏ
- Xem chi tiết linh kiện, tải datasheet, kiểm tra tồn kho
- Gửi yêu cầu xuất kho kèm lý do / tên dự án
- Xem gợi ý linh kiện được tra cứu nhiều

**Quản trị viên (admin)**
- Thêm, sửa, xóa linh kiện; tải ảnh bằng kéo thả
- Quản lý thông số kỹ thuật động (dynamic attributes)
- Đặt ngưỡng cảnh báo tồn kho tối thiểu
- Duyệt, từ chối, phản hồi, xóa yêu cầu xuất kho (duyệt sẽ tự trừ kho)
- Thống kê yêu cầu theo trạng thái (tổng, chờ duyệt, đã duyệt, từ chối)

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Frontend | HTML5, CSS3 (Custom Properties, Dark UI, Responsive), JavaScript ES6+ (Fetch API) |
| Backend | Python 3.10+, FastAPI, Pydantic V2, JWT, Passlib/Bcrypt |
| Cơ sở dữ liệu | MySQL, SQLAlchemy 2.0 ORM, PyMySQL |
| Tài liệu API | Swagger / OpenAPI tự động tại `/docs` |

## Cơ sở dữ liệu

Gồm 6 bảng: `users`, `categories`, `connectors`, `connector_attributes`, `inventory_requests`, `product_metrics`, có ràng buộc khóa ngoại và cơ chế `ON DELETE CASCADE / SET NULL`.

## Cài đặt và chạy

**Yêu cầu:** Python 3.10+, MySQL.

1. Clone dự án:
   ```bash
   git clone https://github.com/PhatGTVT/Inventory-Connector.git
   cd Inventory-Connector/backend
   ```
2. Cài thư viện:
   ```bash
   pip install -r requirements.txt
   ```
3. Tạo cơ sở dữ liệu MySQL và cấu hình kết nối (tên DB, user, mật khẩu) trong file cấu hình của backend.
4. Chạy server:
   ```bash
   python run.py
   ```
5. Mở trình duyệt:
   - Ứng dụng: địa chỉ hiển thị trong terminal (thường là `http://localhost:8000`)
   - Tài liệu API: `http://localhost:8000/docs`

## Cấu trúc thư mục

```
Inventory-Connector/
├── backend/            # Mã nguồn FastAPI, chạy bằng run.py
├── frontend/           # Giao diện HTML/CSS/JS
├── scope.md            # Tài liệu phạm vi dự án
├── spec.md             # Đặc tả kỹ thuật
├── rule.md             # Quy tắc phát triển
├── refine.md           # Danh sách điểm cần tinh chỉnh
├── pageanduser.pdf     # Mô tả các trang và phân quyền người dùng
└── README.md
```

## API chính

- `/api/auth`: đăng ký, đăng nhập, thông tin tài khoản
- `/api/connectors`: tìm kiếm, lọc, xem chi tiết, thêm/sửa/xóa (admin)
- `/api/upload/image`: tải ảnh linh kiện (admin)
- `/api/requests`: gửi, xem, duyệt, từ chối, phản hồi, xóa yêu cầu xuất kho

Chi tiết xem tại `spec.md` hoặc Swagger `/docs`.

## Hình ảnh minh họa

_(Thêm ảnh chụp màn hình: trang Catalog, trang Chi tiết, trang Duyệt yêu cầu)_

## Tác giả

PhatGTVT
