# TÀI LIỆU PHẠM VI DỰ ÁN (PROJECT SCOPE)
## HỆ THỐNG QUẢN LÝ KHO LINH KIỆN CONNECTOR (CONNECTOR INVENTORY)

---

## 1. TỔNG QUAN VÀ MỤC TIÊU DỰ ÁN
Hệ thống **Connector Inventory** là giải pháp phần mềm quản lý kho và danh mục linh kiện điện tử/công nghiệp chuyên biệt cho các dòng đầu nối (Connector). Hệ thống kết hợp hai nghiệp vụ cốt lõi:
1. **Catalog tra cứu kỹ thuật chuẩn công nghiệp (tương tự DigiKey):** Cung cấp giao diện trực quan, bảng thông số kỹ thuật (specs) chi tiết, hình ảnh thực tế, datasheet kỹ thuật và trạng thái tồn kho thời gian thực.
2. **Quy trình luân chuyển & xuất kho nội bộ (User Request - Admin Approval):** Phục vụ các kỹ sư, kỹ thuật viên gửi yêu cầu cấp phát linh kiện và thủ kho/quản trị viên phê duyệt, tự động cập nhật tồn kho.

---

## 2. PHÂN QUYỀN NGƯỜI DÙNG (USER ROLES & PERMISSIONS)

### 2.1. Người dùng Kỹ thuật (Role: `user` - Kỹ sư, Kỹ thuật viên)
- **Đăng ký / Đăng nhập:** Tự tạo tài khoản người dùng hoặc đăng nhập vào hệ thống.
- **Tra cứu linh kiện:** Tìm kiếm thông minh theo Mã linh kiện (MPN), Mã Part Number DigiKey, Tên gọi, và Mô tả chi tiết.
- **Bộ lọc đa thuộc tính (Faceted Filter):** Lọc theo Danh mục, Nhà sản xuất, Kiểu khóa (Fastening Type), Số chân tiếp điểm (Number of Positions), Kiểu tiếp điểm (Contact Type), Màu vỏ (Housing Color)...
- **Xem chi tiết:** Bảng thông số kỹ thuật chuẩn, tải tài liệu PDF Datasheet, xem hình ảnh thực tế, kiểm tra số lượng tồn kho.
- **Gửi yêu cầu xuất kho:** Chọn số lượng cần dùng, nhập lý do / tên dự án sử dụng, gửi tới Admin.
- **Xem gợi ý tra cứu:** Khu vực linh kiện thường xuyên được tra cứu / có nhu cầu cao.

### 2.2. Quản trị viên Kho (Role: `admin` - Thủ kho, Quản lý vật tư)
- Toàn quyền của người dùng kỹ thuật.
- **Quản lý Danh mục & Linh kiện (CRUD Connector):** Thêm mới linh kiện, tải ảnh trực tiếp (kéo thả / chọn tệp), đính kèm datasheet, chỉnh sửa thông tin, xóa linh kiện.
- **Quản lý Thông số kỹ thuật động (Dynamic Attributes):** Thêm/bớt/sửa các thuộc tính kỹ thuật linh hoạt cho từng dòng connector.
- **Quản lý Tồn kho & Cảnh báo:** Cập nhật số tồn, đặt ngưỡng cảnh báo tồn kho tối thiểu (Low Stock Alert).
- **Phê duyệt yêu cầu xuất kho (Approval Workflow):**
  - Xem danh sách yêu cầu đầy đủ: Mã đơn, Thời gian tạo, Người yêu cầu, Linh kiện, Số lượng, Trạng thái.
  - Thao tác: **Duyệt (Approve)** $\rightarrow$ tự động trừ kho; **Từ chối (Reject)**; **Phản hồi (Response)**; **Xóa yêu cầu (Delete)**.

---

## 3. PHẠM VI TÍNH NĂNG (IN-SCOPE & OUT-OF-SCOPE)

### 3.1. Tính năng Nằm trong Phạm vi (In-Scope)
- [x] **Xác thực & Người dùng:** Đăng nhập JWT, Đăng ký tài khoản mới, phân quyền Admin/User.
- [x] **Trang Catalog & Menu (Trang 1):** Cây danh mục, bộ lọc bên trái (Sidebar Filter), thanh tìm kiếm nhanh, lưới thẻ linh kiện kèm trạng thái tồn kho, khối gợi ý thường tra cứu.
- [x] **Trang Chi tiết Linh kiện (Trang 2):** Bảng thuộc tính 2 cột kiểu DigiKey, hộp trạng thái tồn kho, nút gửi yêu cầu xuất kho, tải datasheet PDF, ảnh linh kiện.
- [x] **Trang Duyệt yêu cầu (Trang 3):** Thống kê số lượng (Tổng đơn, Chờ duyệt, Đã duyệt, Từ chối), bộ lọc tab trạng thái, bảng danh sách chi tiết có cột "Ngày tạo yêu cầu", các nút phê duyệt và phản hồi.
- [x] **Trang/Modal Quản lý Linh kiện (Admin Manage):** Bảng danh sách quản lý, modal thêm mới/chỉnh sửa, tải ảnh kéo thả trực quan, quản lý thông số động.
- [x] **Quản lý Tệp tin tĩnh:** Lưu trữ và phục vụ hình ảnh thật của connector được upload trực tiếp từ máy cục bộ.
- [x] **Cơ sở dữ liệu MySQL:** Lưu trữ quan hệ an toàn, ràng buộc toàn vẹn khóa ngoại (Foreign Keys), cơ chế On Delete Cascade/Set Null hợp lý.

### 3.2. Tính năng Nằm ngoài Phạm vi (Out-of-Scope)
- Thanh toán điện tử / Thương mại điện tử (Dự án là quản lý kho nội bộ, không bán hàng online).
- Tích hợp máy quét mã vạch Barcode/QR Code phần cứng (có thể xem xét mở rộng ở giai đoạn sau).
- Gửi email thông báo tự động (SMTP Server) - hiện thông báo trực tiếp qua giao diện dashboard.

---

## 4. NGUYÊN TẮC VÀ QUY TRÌNH PHÁT TRIỂN (DEVELOPMENT RULES)

> [!IMPORTANT]
> **QUY TẮC CỐ ĐỊNH KHI SỬA ĐỔI CODE:**
> 1. **Khoanh vùng tối thiểu:** Chỉ chỉnh sửa đúng file trực tiếp gây ra lỗi hoặc chứa tính năng cần bổ sung. Không sửa lan man, không viết lại cấu trúc không cần thiết.
> 2. **Hỏi ý kiến người dùng trước khi sửa file liên kết:** Nếu việc sửa một file kéo theo sự thay đổi của file khác (ví dụ sửa bảng DB kéo theo router, hoặc sửa router kéo theo frontend API), **PHẢI THÔNG BÁO VÀ HỎI Ý KIẾN NGƯỜI DÙNG** trước khi áp dụng thay đổi.
> 3. **Mọi điểm chưa đúng ý:** Đều được ghi nhận vào file `refine.md` để đối chiếu, duyệt từng điểm và kiểm thử xác nhận.
