import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

from ..config import settings

logger = logging.getLogger("connector.email")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def send_email_sync(to_emails: List[str], subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
    """
    Gửi email qua SMTP (hoặc log Mock nếu SMTP_ENABLED=False).
    Hàm này được chạy trong BackgroundTask để không chặn luồng chính của FastAPI.
    """
    if not to_emails:
        logger.warning("Không có email người nhận (to_emails is empty). Bỏ qua gửi email.")
        return False

    # Lọc email hợp lệ
    recipients = [e.strip() for e in to_emails if e and "@" in e]
    if not recipients:
        logger.warning(f"Danh sách người nhận không hợp lệ: {to_emails}. Bỏ qua gửi email.")
        return False

    if not settings.SMTP_ENABLED:
        # CHẾ ĐỘ MÔ PHỎNG (MOCK DEVELOPMENT MODE)
        border = "=" * 65
        logger.info(f"\n{border}\n[EMAIL NOTIFICATION SERVICE - MOCK MODE]\n"
                    f"Người nhận  : {', '.join(recipients)}\n"
                    f"Tiêu đề     : {subject}\n"
                    f"Thời gian   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Nội dung tóm tắt:\n{text_body or '(Xem HTML preview)'}\n"
                    f"{border}")
        return True

    # CHẾ ĐỘ GỬI THẬT QUA SMTP SERVER
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = ", ".join(recipients)

        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Kết nối SMTP
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()

        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM_EMAIL, recipients, msg.as_string())
        server.quit()

        logger.info(f"Đã gửi email thành công tới: {recipients} | Tiêu đề: {subject}")
        return True

    except Exception as e:
        logger.error(f"Lỗi khi gửi email qua SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT}): {str(e)}", exc_info=True)
        return False


# --- TEMPLATES THÔNG BÁO TỰ ĐỘNG ---

def email_template_wrapper(title: str, preheader: str, content_html: str) -> str:
    """Khung HTML email chuyên nghiệp, tương thích hiển thị trên mọi mail client"""
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b; }}
    .container {{ max-width: 600px; margin: 24px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
    .header {{ background: linear-gradient(135deg, #3b4de8 0%, #06b6d4 100%); padding: 24px 32px; color: #ffffff; text-align: left; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }}
    .header p {{ margin: 4px 0 0; font-size: 13px; opacity: 0.9; }}
    .content {{ padding: 32px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
    .badge-pending {{ background: #fef3c7; color: #b45309; }}
    .badge-approved {{ background: #dcfce7; color: #15803d; }}
    .badge-rejected {{ background: #fee2e2; color: #b91c1c; }}
    .badge-warning {{ background: #ffedd5; color: #c2410c; }}
    .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: #f8fafc; border-radius: 8px; overflow: hidden; }}
    .info-table td {{ padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
    .info-table td.label {{ color: #64748b; font-weight: 600; width: 38%; }}
    .info-table td.value {{ color: #0f172a; font-weight: 700; }}
    .btn {{ display: inline-block; background: #3b4de8; color: #ffffff !important; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 14px; margin-top: 16px; }}
    .footer {{ padding: 20px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🔌 Connector Inventory System</h1>
      <p>{preheader}</p>
    </div>
    <div class="content">
      {content_html}
    </div>
    <div class="footer">
      Email tự động từ Hệ thống Quản Lý Kho Connector. Vui lòng không trả lời trực tiếp email này.
    </div>
  </div>
</body>
</html>"""


def notify_new_request(request_id: int, user_name: str, user_email: Optional[str],
                       part_number: str, quantity: int, reason: Optional[str]):
    """Gửi email tới Ban Quản Trị khi có yêu cầu mượn/xuất kho mới"""
    admin_email = settings.ADMIN_NOTIFICATION_EMAIL
    subject = f"📋 [Yêu cầu xuất kho #{request_id}] Linh kiện {part_number} (SL: {quantity})"

    content = f"""
      <h2 style="font-size:18px;margin-top:0;color:#0f172a;">Thông Báo Yêu Cầu Xuất Kho Mới</h2>
      <p style="font-size:14px;color:#475569;">
        Kỹ sư <strong>{user_name}</strong> vừa gửi một yêu cầu xuất kho linh kiện mới và đang chờ xét duyệt:
      </p>
      <table class="info-table">
        <tr><td class="label">Mã Yêu Cầu</td><td class="value">#{request_id}</td></tr>
        <tr><td class="label">Mã Linh Kiện (MPN)</td><td class="value">{part_number}</td></tr>
        <tr><td class="label">Số Lượng Yêu Cầu</td><td class="value">{quantity} chiếc</td></tr>
        <tr><td class="label">Người Yêu Cầu</td><td class="value">{user_name} {f'({user_email})' if user_email else ''}</td></tr>
        <tr><td class="label">Lý Do / Dự Án</td><td class="value">{reason or '(Không có)'}</td></tr>
        <tr><td class="label">Trạng Thái</td><td><span class="badge badge-pending">Chờ Duyệt (PENDING)</span></td></tr>
      </table>
      <div style="text-align:center;margin-top:24px;">
        <a href="http://localhost:8000/admin-approval" class="btn">Mở Trang Duyệt Yêu Cầu &rarr;</a>
      </div>
    """
    html_body = email_template_wrapper("Yêu cầu xuất kho mới", "Thông báo phê duyệt kho", content)
    text_body = f"Yêu cầu #{request_id}: Kỹ sư {user_name} yêu cầu xuất {quantity} chiếc {part_number}. Lý do: {reason or 'Không có'}. Vui lòng đăng nhập http://localhost:8000/admin-approval để xét duyệt."

    send_email_sync([admin_email], subject, html_body, text_body)


def notify_request_status_updated(request_id: int, user_email: Optional[str], user_name: str,
                                 part_number: str, quantity: int, new_status: str, admin_notes: Optional[str]):
    """Gửi email tới Kỹ sư khi yêu cầu đã được Admin Duyệt hoặc Từ chối"""
    if not user_email:
        logger.info(f"Yêu cầu #{request_id}: Người dùng {user_name} không có email trong hồ sơ. Bỏ qua gửi email.")
        return

    is_approved = (new_status.upper() == "APPROVED")
    status_label = "ĐÃ ĐƯỢC PHÊ DUYỆT" if is_approved else "BỊ TỪ CHỐI"
    badge_class = "badge-approved" if is_approved else "badge-rejected"
    icon = "✅" if is_approved else "❌"

    subject = f"{icon} [Yêu cầu #{request_id}] {status_label}: {part_number} (SL: {quantity})"

    content = f"""
      <h2 style="font-size:18px;margin-top:0;color:#0f172a;">Kết Quả Xét Duyệt Yêu Cầu Xuất Kho</h2>
      <p style="font-size:14px;color:#475569;">
        Chào <strong>{user_name}</strong>, yêu cầu xuất kho linh kiện của bạn đã được Ban Quản Trị cập nhật:
      </p>
      <table class="info-table">
        <tr><td class="label">Mã Yêu Cầu</td><td class="value">#{request_id}</td></tr>
        <tr><td class="label">Mã Linh Kiện (MPN)</td><td class="value">{part_number}</td></tr>
        <tr><td class="label">Số Lượng</td><td class="value">{quantity} chiếc</td></tr>
        <tr><td class="label">Trạng Thái Mới</td><td><span class="badge {badge_class}">{new_status.upper()}</span></td></tr>
        <tr><td class="label">Ghi Chú Từ Admin</td><td class="value">{admin_notes or '(Không có ghi chú thêm)'}</td></tr>
      </table>
      {'<p style="font-size:14px;color:#15803d;background:#dcfce7;padding:12px;border-radius:8px;"><strong>Hướng dẫn nhận hàng:</strong> Yêu cầu đã được duyệt thành công. Bạn có thể đến kho nhận linh kiện hoặc liên hệ thủ kho.</p>' if is_approved else '<p style="font-size:14px;color:#b91c1c;background:#fee2e2;padding:12px;border-radius:8px;">Nếu có bất kỳ thắc mắc nào về lý do từ chối, vui lòng liên hệ trực tiếp với Ban Quản Trị.</p>'}
      <div style="text-align:center;margin-top:20px;">
        <a href="http://localhost:8000/" class="btn">Truy Cập Tra Cứu Linh Kiện</a>
      </div>
    """
    html_body = email_template_wrapper("Kết quả duyệt yêu cầu", "Cập nhật trạng thái phiếu xuất kho", content)
    text_body = f"Yêu cầu #{request_id} của bạn ({part_number}, SL: {quantity}) đã chuyển sang: {new_status}. Ghi chú: {admin_notes or 'Không có'}."

    send_email_sync([user_email], subject, html_body, text_body)


def notify_low_stock_alert(part_number: str, mfr: str, current_qty: int, min_alert_qty: int):
    """Gửi email cảnh báo tới Admin khi tồn kho chạm ngưỡng tối thiểu"""
    admin_email = settings.ADMIN_NOTIFICATION_EMAIL
    subject = f"⚠️ [CẢNH BÁO TỒN KHO THẤP] Linh kiện {part_number} chỉ còn {current_qty} chiếc"

    content = f"""
      <h2 style="font-size:18px;margin-top:0;color:#c2410c;">Cảnh Báo: Linh Kiện Sắp Hết Hàng Trong Kho</h2>
      <p style="font-size:14px;color:#475569;">
        Linh kiện dưới đây vừa giảm xuống dưới hoặc bằng ngưỡng cảnh báo tồn kho tối thiểu. Vui lòng lên kế hoạch nhập hàng bổ sung:
      </p>
      <table class="info-table">
        <tr><td class="label">Mã Linh Kiện (MPN)</td><td class="value" style="color:#c2410c;">{part_number}</td></tr>
        <tr><td class="label">Nhà Sản Xuất</td><td class="value">{mfr or 'N/A'}</td></tr>
        <tr><td class="label">Tồn Kho Hiện Tại</td><td class="value" style="color:#b91c1c;font-size:16px;">{current_qty} chiếc</td></tr>
        <tr><td class="label">Ngưỡng Tối Thiểu</td><td class="value">{min_alert_qty} chiếc</td></tr>
        <tr><td class="label">Mức Độ Cảnh Báo</td><td><span class="badge badge-warning">CẦN NHẬP THÊM (LOW STOCK)</span></td></tr>
      </table>
      <div style="text-align:center;margin-top:24px;">
        <a href="http://localhost:8000/admin-library" class="btn" style="background:#ea580c;">Nhập Kho Từ Thư Viện (Stock In) &rarr;</a>
      </div>
    """
    html_body = email_template_wrapper("Cảnh báo tồn kho thấp", "Cảnh báo tự động từ kho linh kiện", content)
    text_body = f"Cảnh báo: Linh kiện {part_number} hiện chỉ còn {current_qty} chiếc (Ngưỡng cảnh báo: {min_alert_qty}). Vui lòng nhập thêm hàng."

    send_email_sync([admin_email], subject, html_body, text_body)
