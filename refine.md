# DANH SÁCH TINH CHỈNH & THEO DÕI YÊU CẦU (REFINEMENT LOG)
## DỰ ÁN QUẢN LÝ KHO CONNECTOR (CONNECTOR INVENTORY)

> **Ghi chú nguyên tắc làm việc:**
> - Chỉ chỉnh sửa đúng file trực tiếp chứa lỗi hoặc logic cần bổ sung.
> - Nếu việc sửa đổi có liên kết hoặc ảnh hưởng sang file khác, **cần thông báo và hỏi ý kiến trước khi tiến hành sửa**.
> - Bạn có thể trực tiếp bổ sung, sửa đổi hoặc đánh dấu hoàn thành các mục trong file này bất cứ lúc nào.

---

## 1. DANH SÁCH CÁC VẤN ĐỀ CẦN TINH CHỈNH HIỆN TẠI (TỪ ẢNH & PHẢN HỒI)

### Mục 1: Khắc phục lỗi KHÔNG THỂ XÓA CONNECTOR (Ảnh số 3)
- **Hiện tượng:** Khi Admin bấm nút xóa (biểu tượng thùng rác 🗑️) trên danh sách quản lý kho, hệ thống xuất hiện thông báo lỗi: `Unexpected token 'I', "Internal S"... is not valid JSON`.
- **Nguyên nhân kỹ thuật:**
  1. *Khóa ngoại (Foreign Key constraint 1451):* Trong MySQL, bảng `inventory_requests` tham chiếu tới `connectors.id` mà không có thuộc tính `ON DELETE CASCADE`. Khi connector đã từng có trong yêu cầu xuất kho, việc xóa trực tiếp sẽ kích hoạt lỗi toàn vẹn dữ liệu từ MySQL $\rightarrow$ Backend FastAPI ném lỗi `500 Internal Server Error`.
  2. *Xử lý lỗi Frontend:* Khi Backend trả về mã lỗi 500 kèm nội dung thô dạng chuỗi `"Internal Server Error"`, hàm `api.request()` gọi `res.json()` dẫn đến lỗi parse cú pháp JSON.
- **File cần chỉnh sửa dự kiến:**
  - `backend/app/routers/connectors.py`: Bọc khối `try...except IntegrityError` trong hàm `delete_connector`, xóa hoặc cập nhật trạng thái các bản ghi liên quan an toàn trước khi xóa connector, trả về JSON lỗi chuẩn nếu có.
  - `frontend/js/api.js`: Nâng cấp hàm `request()` kiểm tra nội dung text trước khi parse JSON, hiển thị thông báo lỗi rõ ràng thay vì văng lỗi cú pháp.
- **Trạng thái:** ✅ **ĐÃ HOÀN THÀNH** (Đã xử lý xóa cascade an toàn trong `connectors.py` và bọc try-parse JSON trong `api.js`).

---

### Mục 2: Khắc phục lỗi KHÔNG THỂ THÊM MỚI CONNECTOR (Ảnh số 4 & 5)
- **Hiện tượng:** Điền thông tin vào form "Thêm Connector Mới" và nhấn "Lưu Connector" thì bị báo lỗi `Unexpected token 'I', "Internal S"... is not valid JSON`.
- **Nguyên nhân kỹ thuật:**
  1. *Trùng lặp trường Unique:* Trường `digikey_part_number` trong bảng `connectors` đang có ràng buộc `unique=True`. Nếu người dùng nhập mã đã có, hoặc để trống mà DB ghi nhận chuỗi rỗng thay vì NULL, MySQL sẽ chặn lại.
  2. *Dữ liệu số/khóa ngoại:* Trường `category_id` hoặc số lượng nếu gửi chuỗi rỗng/sai kiểu gây lỗi validation hoặc lỗi câu lệnh SQL.
- **File cần chỉnh sửa dự kiến:**
  - `backend/app/routers/connectors.py`: Bắt lỗi trùng lặp `mfr_part_number` và `digikey_part_number`, trả về thông báo lỗi tiếng Việt cụ thể (Mã 400 Bad Request kèm JSON `{ "detail": "Mã linh kiện đã tồn tại" }`).
  - `frontend/js/admin-connector.js`: Xử lý giá trị form trước khi gửi (chuỗi rỗng chuyển thành `null`).
- **Trạng thái:** ✅ **ĐÃ HOÀN THÀNH** (Kiểm tra duplicate DigiKey PN sạch, chuẩn hóa rỗng thành `None`, trả thông báo lỗi tiếng Việt rõ ràng, không còn lỗi 500).

---

### Mục 3: Cải tiến BỘ LỌC TÌM KIẾM (Search Logic)
- **Hiện tượng:** Thanh tìm kiếm hiện đang khớp chung cả với tên nhà sản xuất, dẫn đến việc người dùng muốn tìm theo Tên hoặc Mã linh kiện (P/N, MPN) nhưng lại ra kết quả ưu tiên theo hãng.
- **Yêu cầu tinh chỉnh:**
  1. Tách biệt rõ ràng: Thanh tìm kiếm chính (`#global-search`) tập trung tìm kiếm theo **Mã linh kiện (MPN)**, **Mã Part Number (DigiKey P/N)**, và **Tên / Mô tả kỹ thuật**.
  2. Việc lọc theo **Nhà sản xuất (Manufacturer)** thực hiện thông qua dropdown chọn nhà sản xuất ở cột bộ lọc bên trái (Sidebar Filter).
- **File cần chỉnh sửa dự kiến:**
  - `backend/app/routers/connectors.py`: Tối ưu hóa điều kiện `WHERE` trong câu lệnh truy vấn tìm kiếm `q`, ưu tiên `mfr_part_number`, `digikey_part_number`, `description`.
- **Trạng thái:** ✅ **ĐÃ HOÀN THÀNH** (Thanh tìm kiếm ưu tiên khớp chính xác MPN, P/N, Mô tả; phân tách riêng bộ lọc Hãng ở sidebar).

---

### Mục 4: Bổ sung CỘT "NGÀY TẠO YÊU CẦU" trên bảng Duyệt yêu cầu (Ảnh số 2)
- **Hiện tượng:** Trang `admin-approval.html` hiện tại đang hiển thị ngày tạo nhỏ mờ bên dưới mã đơn hàng (`REQ-...`), chưa có một cột riêng biệt độc lập rõ ràng.
- **Yêu cầu tinh chỉnh:**
  - Thêm cột tiêu đề riêng: **`NGÀY TẠO`** trên thẻ `<thead>`.
  - Hiển thị ngày giờ tạo yêu cầu dạng bảng chuẩn: `DD/MM/YYYY HH:mm` rõ nét, dễ nhìn cho thủ kho.
- **File cần chỉnh sửa dự kiến:**
  - `frontend/admin-approval.html`: Thêm thẻ `<th>NGÀY TẠO</th>`.
  - `frontend/js/approval.js`: Thêm thẻ `<td>` hiển thị ngày giờ tạo độc lập vào hàm `renderTable()`.
- **Trạng thái:** ✅ **ĐÃ HOÀN THÀNH** (Đã bổ sung cột tiêu đề và ô dữ liệu ngày giờ rõ ràng, chuẩn định dạng).

---

### Mục 5: Thêm chức năng TẢI ẢNH KÉO THẢ / CHỌN TỆP CHO CONNECTOR (Ảnh 1 & 5)
- **Hiện tượng:** Hiện tại người dùng chỉ có một ô nhập URL đường dẫn ảnh dạng text (`form-image-url`), không thể tự tải ảnh thật từ máy tính lên. Các connector hiện tại dùng icon vector tạm thời.
- **Yêu cầu tinh chỉnh:**
  1. *Vùng kéo-thả (Drag & Drop Zone):* Cho phép kéo thả trực tiếp tệp ảnh (`.png`, `.jpg`, `.jpeg`, `.webp`) hoặc bấm vào để chọn tệp từ máy tính.
  2. *Xem trước ảnh (Image Preview):* Hiển thị ngay ảnh vừa chọn trước khi bấm lưu.
  3. *Lưu trữ ảnh trên Server:* Tải ảnh lên backend lưu vào thư mục `frontend/assets/images/uploads/` và tự động gán đường dẫn vào linh kiện.
  4. *Ghi chú người dùng:* Người dùng trực tiếp kéo thả/tải ảnh thật của connector từ máy tính cá nhân khi thêm/sửa linh kiện (không sử dụng AI tạo ảnh).
- **File đã chỉnh sửa:**
  - `backend/app/main.py`: Endpoint `POST /api/upload/image`.
  - `frontend/admin-manage.html`: Khung Drag & Drop ảnh và xem trước ảnh với nút đổi/xóa ảnh.
  - `frontend/js/admin-connector.js`: Xử lý kéo thả, gửi ảnh trực tiếp và gán URL tự động.
- **Trạng thái:** ✅ **ĐÃ HOÀN THÀNH** (Kéo thả, chọn tệp từ máy tính và lưu trữ ảnh hoạt động trơn tru).

---

### Mục 6: Thêm tính năng ĐĂNG KÝ TÀI KHOẢN (Sign Up)
- **Hiện tượng:** Hiện tại hệ thống mới chỉ có modal Đăng nhập (`auth.js`), chưa có form để người dùng/kỹ sư mới tự tạo tài khoản.
- **Yêu cầu tinh chỉnh:**
  1. Thêm API đăng ký người dùng mới: `POST /api/auth/register` (hỗ trợ nhập: Tên đăng nhập, Email, Mật khẩu, Họ và tên, Phòng ban). Mặc định phân quyền `role = 'user'`.
  2. Thêm tab hoặc nút chuyển đổi "Chưa có tài khoản? Đăng ký ngay" trên modal đăng nhập ở thanh Navigation Header.
- **File đã chỉnh sửa:**
  - `backend/app/routers/auth.py`: Endpoint `POST /register`.
  - `frontend/js/auth.js`: Chuyển modal sang 2 Tab động "Đăng Nhập" / "Đăng Ký", tự động kích hoạt phiên khi đăng ký.
- **Trạng thái:** ✅ **ĐÃ HOÀN THÀNH** (Đăng ký tài khoản mới thành công và phân quyền chuẩn).

---

## 2. KHU VỰC DÀNH CHO BẠN TỰ GHI CHÚ VÀ ĐIỀU CHỈNH (USER NOTES & REFINEMENTS)

*(Bạn có thể tự do chỉnh sửa, gạch bỏ hoặc viết thêm các mong muốn, góp ý hoặc tiêu chí mới vào phần dưới đây)*

- [ ] **Góp ý 1:** ...
- [ ] **Góp ý 2:** ...
- [ ] **Góp ý 3:** ...
