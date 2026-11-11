# ĐẶC TẢ KỸ THUẬT HỆ THỐNG (TECHNICAL SPECIFICATION)
## HỆ THỐNG QUẢN LÝ KHO CONNECTOR (CONNECTOR INVENTORY)

---

## 1. KIẾN TRÚC HỆ THỐNG & TECH STACK

- **Frontend:** HTML5 Semantic, Vanilla CSS3 (Custom Properties / Design Tokens, Dark UI, Glassmorphism, Responsive), Vanilla JavaScript (ES6+ Modules, Fetch API, không phụ thuộc framework nặng để đảm bảo tốc độ và sự trong sáng của mã nguồn).
- **Backend:** Python 3.10+ kết hợp **FastAPI** (Asynchronous REST API, Swagger OpenAPI 3.0 tự động tại `/docs`, Pydantic V2 data validation, JWT Authentication, Passlib/Bcrypt).
- **Cơ sở Dữ liệu:** **MySQL** (kết nối qua SQLAlchemy 2.0 ORM và PyMySQL driver).
- **Xử lý Tệp tin tĩnh (Static & Media):** Lưu trữ ảnh upload tại `backend/app/static/uploads/` hoặc `frontend/assets/uploads/`, phục vụ qua FastAPI StaticFiles.

---

## 2. CƠ SỞ DỮ LIỆU & RÀNG BUỘC TOÀN VẸN (DATABASE SCHEMA)

### 2.1. Bảng `users` (Tài khoản & Phân quyền)
| Cột | Kiểu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Mã định danh người dùng |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Tên đăng nhập |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Địa chỉ email |
| `password_hash`| VARCHAR(255) | NOT NULL | Mật khẩu đã băm (Bcrypt) |
| `full_name` | VARCHAR(100) | NOT NULL | Họ và tên hiển thị |
| `department` | VARCHAR(100) | NULLABLE | Bộ phận / Phòng ban |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'user' | Quyền: `admin` hoặc `user` |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Ngày tạo tài khoản |

### 2.2. Bảng `categories` (Phân loại Connector)
| Cột | Kiểu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Mã danh mục |
| `name` | VARCHAR(100) | NOT NULL | Tên danh mục (Circular, Automotive,...) |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | Đường dẫn định danh URL |
| `parent_id` | INT | FK $\rightarrow$ `categories.id` (ON DELETE SET NULL) | Danh mục cha (nếu có) |
| `description` | VARCHAR(255) | NULLABLE | Mô tả danh mục |

### 2.3. Bảng `connectors` (Thông tin Linh kiện Connector)
| Cột | Kiểu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Khóa chính |
| `digikey_part_number` | VARCHAR(100) | INDEX, NULLABLE | Mã Part Number DigiKey (Ví dụ: `965-APC06-12-12S-ND`) |
| `mfr_part_number` | VARCHAR(100) | UNIQUE, INDEX, NOT NULL | Mã nhà sản xuất MPN (Ví dụ: `APC06-12-12S`) |
| `manufacturer` | VARCHAR(100) | INDEX, NOT NULL | Tên nhà sản xuất (Amphenol, Molex, TE,...) |
| `description` | VARCHAR(255) | NOT NULL | Tên mô tả ngắn |
| `detailed_description` | TEXT | NULLABLE | Mô tả thông số chi tiết chuẩn công nghiệp |
| `lead_time` | VARCHAR(50) | DEFAULT 'Immediate / In Stock' | Thời gian giao hàng dự kiến |
| `customer_reference` | VARCHAR(100) | NULLABLE | Mã tham chiếu nội bộ / dự án |
| `datasheet_url` | VARCHAR(255) | NULLABLE | Đường dẫn tải PDF Datasheet |
| `image_url` | VARCHAR(255) | NULLABLE | Đường dẫn hình ảnh thật hoặc ảnh upload |
| `in_stock_qty` | INT | NOT NULL, DEFAULT 0 | Số lượng tồn kho thực tế |
| `min_stock_alert` | INT | NOT NULL, DEFAULT 5 | Ngưỡng tồn kho tối thiểu cần cảnh báo |
| `category_id` | INT | FK $\rightarrow$ `categories.id` (ON DELETE SET NULL) | Thuộc danh mục nào |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Ngày tạo |
| `updated_at` | DATETIME | ON UPDATE CURRENT_TIMESTAMP | Ngày cập nhật |

### 2.4. Bảng `connector_attributes` (Thông số kỹ thuật động - Specs)
| Cột | Kiểu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Khóa chính |
| `connector_id` | INT | FK $\rightarrow$ `connectors.id` (**ON DELETE CASCADE**) | Liên kết connector |
| `attr_key` | VARCHAR(100) | NOT NULL, INDEX | Tên thuộc tính (Fastening Type, Number of Positions,...) |
| `attr_value` | VARCHAR(255) | NOT NULL, INDEX | Giá trị (Bayonet Lock, 12, Gold Plated,...) |
| `group_name` | VARCHAR(50) | DEFAULT 'General' | Nhóm thuộc tính |

### 2.5. Bảng `inventory_requests` (Yêu cầu Xuất kho)
| Cột | Kiểu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Khóa chính |
| `request_code` | VARCHAR(50) | UNIQUE, INDEX, NOT NULL | Mã đơn (Ví dụ: `REQ-20260916-CCA03C`) |
| `user_id` | INT | FK $\rightarrow$ `users.id` (ON DELETE CASCADE) | Người gửi yêu cầu |
| `connector_id` | INT | FK $\rightarrow$ `connectors.id` (**ON DELETE CASCADE hoặc SET NULL**) | Linh kiện yêu cầu |
| `quantity` | INT | NOT NULL, DEFAULT 1 | Số lượng xin cấp |
| `status` | VARCHAR(20) | INDEX, DEFAULT 'pending' | Trạng thái: `pending`, `approved`, `rejected` |
| `reason` | TEXT | NULLABLE | Mục đích sử dụng / Dự án |
| `admin_response`| TEXT | NULLABLE | Phản hồi của thủ kho |
| `processed_by` | INT | FK $\rightarrow$ `users.id` (ON DELETE SET NULL) | Thủ kho thực hiện duyệt |
| `requested_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | **Thời điểm gửi yêu cầu** |
| `processed_at` | DATETIME | NULLABLE | Thời điểm phê duyệt |

### 2.6. Bảng `product_metrics` (Thống kê Lượt xem & Gợi ý)
| Cột | Kiểu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | Khóa chính |
| `connector_id` | INT | FK $\rightarrow$ `connectors.id` (**ON DELETE CASCADE**) | Linh kiện |
| `view_count` | INT | DEFAULT 0 | Số lần được xem chi tiết |
| `request_count`| INT | DEFAULT 0 | Số lần được tạo yêu cầu xuất kho |
| `last_viewed_at`| DATETIME | NULLABLE | Lần xem gần nhất |

---

## 3. ĐẶC TẢ GIAO TIẾP API (API CONTRACTS)

### 3.1. Xác thực & Tài khoản (`/api/auth`)
- `POST /api/auth/register`: Đăng ký tài khoản người dùng mới (`username`, `email`, `password`, `full_name`, `department`). Trả về thông tin user mới và mã JWT token.
- `POST /api/auth/login`: Đăng nhập bằng Form Data (`username`, `password`). Trả về JWT token và thông tin user.
- `GET /api/auth/me`: Lấy thông tin tài khoản đang đăng nhập qua Header `Authorization: Bearer <token>`.

### 3.2. Quản lý Connector & Tra cứu (`/api/connectors`)
- `GET /api/connectors`: Tìm kiếm và lọc linh kiện.
  - Tham số query: `q` (từ khóa tìm kiếm), `category_id`, `manufacturer`, `fastening_type`, `positions`, `contact_type`, `color`, `skip`, `limit`.
  - **Quy tắc tìm kiếm:** Ưu tiên khớp chính xác hoặc khớp một phần theo `mfr_part_number`, `digikey_part_number`, `description`, sau đó mới đến `manufacturer`.
- `GET /api/connectors/{id}`: Xem chi tiết linh kiện kèm danh sách thuộc tính động (attributes).
- `GET /api/connectors/suggestions/frequently-viewed`: Lấy danh sách linh kiện tra cứu phổ biến nhất.
- `GET /api/connectors/filters/options`: Lấy các giá trị thuộc tính thực tế đang có trong DB để điền vào menu bộ lọc.
- `POST /api/connectors`: *(Yêu cầu quyền Admin)* Thêm mới connector kèm danh sách thuộc tính động. Trả về đối tượng JSON hoàn chỉnh.
- `PUT /api/connectors/{id}`: *(Yêu cầu quyền Admin)* Chỉnh sửa thông tin và thông số của connector.
- `DELETE /api/connectors/{id}`: *(Yêu cầu quyền Admin)* Xóa connector. Xử lý an toàn các bảng phụ thuộc (requests, metrics, attributes).

### 3.3. Tải lên Tệp tin Ảnh (`/api/upload`)
- `POST /api/upload/image`: *(Yêu cầu quyền Admin)* Tiếp nhận tệp tin hình ảnh dạng `multipart/form-data`. Kiểm tra định dạng cho phép (`jpg`, `jpeg`, `png`, `webp`). Lưu vào thư mục static và trả về đường dẫn URL (ví dụ: `/static/uploads/connector_123.png`).

### 3.4. Quản lý Yêu cầu Xuất kho (`/api/requests`)
- `POST /api/requests`: Kỹ sư gửi yêu cầu xuất kho (`connector_id`, `quantity`, `reason`).
- `GET /api/requests`: Thủ kho xem toàn bộ yêu cầu; Người dùng xem yêu cầu của chính mình.
- `PUT /api/requests/{id}/approve`: *(Yêu cầu Admin)* Phê duyệt đơn $\rightarrow$ tự động trừ `in_stock_qty` trong kho.
- `PUT /api/requests/{id}/reject`: *(Yêu cầu Admin)* Từ chối đơn cấp phát kèm lý do phản hồi.
- `PUT /api/requests/{id}/respond`: *(Yêu cầu Admin)* Ghi chú/phản hồi trao đổi với người yêu cầu.
- `DELETE /api/requests/{id}`: *(Yêu cầu Admin)* Xóa bản ghi yêu cầu.

---

## 4. QUY CHUẨN XỬ LÝ LỖI (ERROR HANDLING STANDARD)
Mọi phản hồi lỗi từ Backend (kể cả lỗi 400, 401, 403, 404, hay 500) **bắt buộc phải trả về định dạng chuẩn JSON**:
```json
{
  "detail": "Nội dung thông báo lỗi bằng tiếng Việt rõ ràng, dễ hiểu"
}
```
Tại Frontend, hàm `api.request()` bắt buộc kiểm tra `res.ok` và đọc nội dung an toàn (hỗ trợ cả trường hợp server trả text) để không bao giờ xảy ra lỗi cú pháp `Unexpected token 'I', "Internal S"... is not valid JSON`.
