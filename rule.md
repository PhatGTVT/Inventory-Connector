# BỘ QUY TẮC PHÁT TRIỂN & VẬN HÀNH (DEVELOPMENT RULES)
## DỰ ÁN QUẢN LÝ KHO CONNECTOR (CONNECTOR INVENTORY)

> **MỤC ĐÍCH:** Tài liệu này đóng vai trò là "Luật Bất Di Bất Dịch" quy định cách thức làm việc, giao tiếp, phân tích yêu cầu và chỉnh sửa mã nguồn giữa AI và Người dùng trong toàn bộ vòng đời dự án.

---

## 1. NGUYÊN TẮC GIAO TIẾP & THỰC THI (INTERACTION RULES)

### Điều 1: Cấm Code Khi Đang Thảo Luận
- **Quy tắc:** Khi người dùng đang hỏi, trao đổi, góp ý hoặc yêu cầu phân tích, **TUYỆT ĐỐI CẤM SỬA HOẶC VIẾT CODE DỰ ÁN**.
- **Quy trình:** Phải tập trung giải đáp thắc mắc, phân tích phương án, làm rõ rủi ro/đánh đổi. **Chỉ khi nào người dùng phê duyệt phương án (chốt rõ ràng), mới được tiến hành chỉnh sửa mã nguồn.**

### Điều 2: Minh Bạch Giữa Sự Thật, Suy Luận và Giả Định
Trong mọi báo cáo và câu trả lời, bắt buộc phải phân định rõ ràng 3 cấp độ thông tin:
1. **Sự thật đã xác nhận (Confirmed Facts):** Thông tin có chứng cứ cụ thể từ mã nguồn, ảnh chụp, cơ sở dữ liệu hoặc văn bản người dùng cung cấp.
2. **Suy luận hợp lý (Reasonable Inferences):** Kết luận được rút ra logic dựa trên các sự thật đã biết.
3. **Giả định / Thiếu thông tin (Hypotheses / Missing Info):** Những điểm chưa đủ dữ kiện, tuyệt đối không tự biên tự diễn; bắt buộc phải chỉ rõ điểm thiếu và đặt câu hỏi làm rõ với người dùng.

### Điều 3: Bắt Buộc Trình Bày Đánh Đổi (Trade-offs) và Rủi Ro (Risks)
- Bất kỳ giải pháp kiến trúc, giao diện hay thay đổi kỹ thuật nào được đề xuất **đều phải chỉ rõ ưu điểm, nhược điểm, sự đánh đổi và rủi ro tiềm ẩn** (về hiệu năng, độ phức tạp, tính tương thích, hoặc trải nghiệm người dùng).

---

## 2. NGUYÊN TẮC BẢO TOÀN & CHỈNH SỬA MÃ NGUỒN (CODE INTEGRITY RULES)

### Điều 4: Khoanh Vùng Sửa Đổi Tối Thiểu (Single-File Scoping)
- Không chỉnh sửa lan man. File nào chứa lỗi hoặc logic cần bổ sung thì **chỉ chỉnh sửa tập trung tại file đó**.
- Không tự ý tái cấu trúc (refactor) hoặc viết lại các file đang hoạt động ổn định nếu không có yêu cầu trực tiếp.

### Điều 5: Kiểm Soát File Liên Kết (Cross-file Dependency Protocol)
- Nếu việc sửa đổi một file dẫn đến việc bắt buộc phải sửa file khác liên kết với nó (ví dụ: sửa Schema DB kéo theo Router API, hoặc sửa Router API kéo theo Frontend JS), **PHẢI THÔNG BÁO VÀ HỎI Ý KIẾN NGƯỜI DÙNG TRƯỚC KHI THỰC HIỆN**.
- Liệt kê cụ thể: Tên file bị ảnh hưởng, lý do phải sửa, và mức độ rủi ro liên đới.

---

## 3. TIÊU CHUẨN GIAO DIỆN & TRẢI NGHIỆM (UI/UX DESIGN RULES)

### Điều 6: Học Hỏi & Chuẩn Hóa Ngôn Ngữ Thiết Kế
Dựa trên phân tích các giao diện chuẩn (như giao diện mẫu Bài tập PHP):
- **Phân cấp thị giác rõ ràng (Visual Hierarchy):** Header nổi bật, Breadcrumb định vị vị trí, Sidebar có trạng thái Active rõ ràng (màu nền + biểu tượng mũi tên chỉ báo), Thẻ thống kê (Stats Cards) có điểm nhấn viền màu (accent border).
- **Hộp thông tin chuyên nghiệp:** Sử dụng Callout Box (khung viền trái) cho các lưu ý/hướng dẫn; Sử dụng Badge/Pills bo tròn cho các nhãn phân loại, trạng thái tồn kho, và thông số kỹ thuật.
- **Tính nhất quán về bảng màu:** Duy trì bảng màu có chủ đích, không pha trộn lộn xộn giữa các phong cách khi chưa có quyết định thống nhất về Theme (Dark Mode vs Light Mode).

---

## 4. TIÊU CHUẨN XỬ LÝ LỖI & TOÀN VẸN HỆ THỐNG (ERROR HANDLING RULES)

### Điều 7: Tiêu Chuẩn Phản Hồi API (API Error Contract)
- Mọi phản hồi lỗi từ Backend (HTTP 4xx, 5xx) bắt buộc phải trả về JSON chuẩn định dạng `{"detail": "Nội dung lỗi chi tiết bằng tiếng Việt"}`.
- Cấm để lọt trang lỗi thô (HTML error page hoặc plain text) từ máy chủ Uvicorn/FastAPI làm vỡ cơ chế parse JSON tại Frontend.

### Điều 8: Toàn Vẹn Khóa Ngoại Cơ Sở Dữ Liệu
- Khi thiết kế hoặc can thiệp quan hệ dữ liệu trong MySQL, phải quy định rõ ràng hành vi `ON DELETE` (`CASCADE`, `SET NULL` hoặc `RESTRICT`), đảm bảo khi xóa linh kiện hoặc danh mục không gây lỗi `IntegrityError (1451)`.

### Điều 9: Quản Lý Phiên Bản Kế Hoạch Triển Khai (Plan Versioning)
- **Quy tắc:** Mỗi lần lập kế hoạch tinh chỉnh, xử lý lỗi hoặc triển khai giai đoạn mới, **BẮT BUỘC PHẢI TẠO FILE KẾ HOẠCH RIÊNG BIỆT** được đánh số thứ tự (ví dụ: `Implementation Plan Refine 1.md`, `Implementation Plan Refine 2.md`...).
- **Cấm:** TUYỆT ĐỐI KHÔNG ghi đè lên file Implementation Plan gốc hoặc các file kế hoạch đã lập trước đó để bảo toàn trọn vẹn lịch sử thiết kế và yêu cầu ban đầu.

---

## 5. CƠ CHẾ CẬP NHẬT TÀI LIỆU
- **Hệ thống tài liệu cốt lõi:**
  1. `scope.md`: Định hình phạm vi và phân quyền.
  2. `spec.md`: Định hình kiến trúc và đặc tả kỹ thuật.
  3. `rule.md`: Định hình quy tắc làm việc và ứng xử.
  4. `refine.md`: Nhật ký tinh chỉnh, theo dõi các vấn đề thực tế cần sửa.
  5. `Implementation Plan.md`: Kế hoạch khởi tạo ban đầu (gốc).
  6. `Implementation Plan Refine X.md`: Kế hoạch chi tiết của từng đợt tinh chỉnh.
- Mọi thay đổi về phạm vi hay quy tắc phải được ghi nhận đồng bộ vào các tài liệu này.

