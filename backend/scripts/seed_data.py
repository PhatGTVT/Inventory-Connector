import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.category import Category
from app.models.connector import Connector
from app.models.connector_attribute import ConnectorAttribute
from app.models.request import InventoryRequest
from app.models.product_metric import ProductMetric
from app.models.audit_log import AuditLog
from app.services.auth_service import hash_password

def seed():
    print("Creating tables if not exists...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users
        print("Seeding Users...")
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@connector.local",
                full_name="Quản Trị Kho",
                department="Bộ phận Quản lý Kho & Vật tư",
                role="admin",
                password_hash=hash_password("admin123")
            )
            db.add(admin)

        user1 = db.query(User).filter(User.username == "user").first()
        if not user1:
            user1 = User(
                username="user",
                email="nam.tran@company.com",
                full_name="Trần Hoàng Nam",
                department="Phòng R&D Điện - Điện tử",
                role="user",
                password_hash=hash_password("user123")
            )
            db.add(user1)

        user2 = db.query(User).filter(User.username == "user2").first()
        if not user2:
            user2 = User(
                username="user2",
                email="tuan.le@company.com",
                full_name="Lê Minh Tuấn",
                department="Xưởng Cơ Điện Tử & Lắp Ráp",
                role="user",
                password_hash=hash_password("user123")
            )
            db.add(user2)

        db.commit()
        db.refresh(admin)
        db.refresh(user1)
        db.refresh(user2)

        # 2. Seed Categories
        print("Seeding Categories...")
        cat_tree = [
            {"name": "Circular Connectors", "slug": "circular-connectors", "icon": "bi-disc", "desc": "Đầu nối tròn công nghiệp & quân sự"},
            {"name": "Circular Connector Housings", "slug": "circular-connector-housings", "parent_slug": "circular-connectors", "icon": "bi-shield", "desc": "Vỏ đầu nối tròn (Plug/Receptacle housing)"},
            {"name": "Automotive Connectors", "slug": "automotive-connectors", "icon": "bi-truck", "desc": "Đầu nối chống nước dùng trong ô tô, xe cơ giới"},
            {"name": "Rectangular Connectors", "slug": "rectangular-connectors", "icon": "bi-grid-3x3", "desc": "Đầu nối vuông nhiều pin, bo mạch"},
            {"name": "Terminal Blocks", "slug": "terminal-blocks", "icon": "bi-hdd-stack", "desc": "Cầu đấu dây công nghiệp"}
        ]

        cat_map = {}
        for c in cat_tree:
            existing = db.query(Category).filter(Category.slug == c["slug"]).first()
            if not existing:
                parent_id = cat_map.get(c.get("parent_slug")) if c.get("parent_slug") else None
                cat_obj = Category(name=c["name"], slug=c["slug"], icon=c["icon"], description=c["desc"], parent_id=parent_id)
                db.add(cat_obj)
                db.commit()
                db.refresh(cat_obj)
                cat_map[c["slug"]] = cat_obj.id
            else:
                cat_map[c["slug"]] = existing.id

        # 3. Seed Connectors
        print("Seeding Connectors and Specifications...")
        connectors_data = [
            {
                "mfr_part_number": "APC06-12-12S REV.II",
                "digikey_part_number": "965-APC06-12-12SREV.II-ND",
                "manufacturer": "Amphenol Industrial Operations",
                "description": "PLUG 12-12 SOCKET REV.II",
                "detailed_description": "12 Position Circular Connector Plug Housing Free Hanging (In-Line) Coupling Nut",
                "lead_time": "6 Weeks",
                "customer_reference": "CR-APC-2026-X1",
                "datasheet_url": "https://www.amphenol-industrial.com/datasheet-apc.pdf",
                "image_url": "/assets/images/apc06-12-12s.png",
                "in_stock_qty": 142,
                "min_stock_alert": 10,
                "category_id": cat_map["circular-connector-housings"],
                "views": 482,
                "requests": 28,
                "attributes": [
                    ("Category", "Connectors, Interconnects > Circular Connectors > Circular Connector Housings", "Classification"),
                    ("Fastening Type", "Bayonet Lock", "Mechanical"),
                    ("Orientation", "N (Normal)", "Mechanical"),
                    ("Series", "APC", "General"),
                    ("Primary Material", "Plastic", "Material"),
                    ("Packaging", "Bag", "Packaging"),
                    ("Shell Material", "Synthetic Resin", "Material"),
                    ("Part Status", "Active", "Status"),
                    ("Housing Color", "Black", "Appearance"),
                    ("Connector Type", "Plug Housing", "Mechanical"),
                    ("Ingress Protection", "IP67 - Dust Tight, Waterproof", "Environmental"),
                    ("Type", "For Female Sockets", "Electrical"),
                    ("Material Flammability Rating", "UL94 V-0", "Environmental"),
                    ("Number of Positions", "12", "Electrical"),
                    ("Features", "Coupling Nut", "Mechanical"),
                    ("Shell Size - Insert", "12-12", "Mechanical"),
                    ("Shielding", "Unshielded", "Electrical"),
                    ("Contact Type", "Crimp", "Electrical"),
                    ("Note", "Contacts Sold Separately", "General"),
                    ("Contact Size", "20", "Electrical"),
                    ("Contact Shape", "Circular", "Mechanical"),
                    ("Mounting Type", "Free Hanging (In-Line)", "Mechanical"),
                    ("Operating Temperature", "-40°C ~ 105°C", "Environmental")
                ]
            },
            {
                "mfr_part_number": "D38999/26WE35PN",
                "digikey_part_number": "D3899926WE35PN-ND",
                "manufacturer": "Amphenol Aerospace Operations",
                "description": "CONN PLUG W/PINS 55POS CRIMP",
                "detailed_description": "35 Position Circular Connector Plug, Male Pins Crimp Gold Free Hanging (In-Line) Triple Start Threaded",
                "lead_time": "Immediate / In Stock",
                "customer_reference": "MIL-SPEC-D38999",
                "datasheet_url": "https://www.amphenol-aerospace.com/datasheets/38999.pdf",
                "image_url": "/assets/images/d38999-26.png",
                "in_stock_qty": 35,
                "min_stock_alert": 5,
                "category_id": cat_map["circular-connectors"],
                "views": 395,
                "requests": 19,
                "attributes": [
                    ("Category", "Connectors > Circular Military Connectors", "Classification"),
                    ("Fastening Type", "Threaded (Triple Start)", "Mechanical"),
                    ("Orientation", "N (Normal)", "Mechanical"),
                    ("Series", "MIL-DTL-38999 Series III, Tri-Start", "General"),
                    ("Shell Material", "Aluminum Alloy", "Material"),
                    ("Housing Color", "Olive Drab Cadmium", "Appearance"),
                    ("Connector Type", "Plug, Male Pins", "Mechanical"),
                    ("Ingress Protection", "IP68 - Submersible, Moisture Resistant", "Environmental"),
                    ("Number of Positions", "35", "Electrical"),
                    ("Shell Size - Insert", "17-35", "Mechanical"),
                    ("Contact Type", "Crimp Gold", "Electrical"),
                    ("Contact Size", "22D", "Electrical"),
                    ("Mounting Type", "Free Hanging (In-Line)", "Mechanical"),
                    ("Operating Temperature", "-65°C ~ 175°C", "Environmental")
                ]
            },
            {
                "mfr_part_number": "D38999/20WE35PN",
                "digikey_part_number": "D3899920WE35PN-ND",
                "manufacturer": "Amphenol Aerospace Operations",
                "description": "CONN RCPT 35POS WALL MNT W/PINS",
                "detailed_description": "35 Position Circular Connector Receptacle, Male Pins Crimp Wall Mount Flange",
                "lead_time": "1-2 Weeks",
                "customer_reference": "RECPT-WALL-17",
                "datasheet_url": "https://www.amphenol-aerospace.com/datasheets/38999.pdf",
                "image_url": "/assets/images/d38999-20.png",
                "in_stock_qty": 48,
                "min_stock_alert": 8,
                "category_id": cat_map["circular-connectors"],
                "views": 210,
                "requests": 14,
                "attributes": [
                    ("Category", "Connectors > Circular Military Connectors", "Classification"),
                    ("Fastening Type", "Threaded", "Mechanical"),
                    ("Series", "MIL-DTL-38999 Series III", "General"),
                    ("Shell Material", "Aluminum Alloy", "Material"),
                    ("Housing Color", "Olive Drab Cadmium", "Appearance"),
                    ("Connector Type", "Receptacle, Male Pins", "Mechanical"),
                    ("Ingress Protection", "IP67 / IP68", "Environmental"),
                    ("Number of Positions", "35", "Electrical"),
                    ("Shell Size - Insert", "17-35", "Mechanical"),
                    ("Mounting Type", "Panel Mount, Flange", "Mechanical"),
                    ("Operating Temperature", "-65°C ~ 175°C", "Environmental")
                ]
            },
            {
                "mfr_part_number": "DT06-2S-CE06",
                "digikey_part_number": "DT06-2S-CE06-ND",
                "manufacturer": "TE Connectivity DEUTSCH",
                "description": "CONN PLUG 2POS CABLE MNT BLACK",
                "detailed_description": "2 Position Circular / Automotive Connector Plug Housing for Female Sockets Black Free Hanging with Enhanced Seal",
                "lead_time": "In Stock",
                "customer_reference": "AUTO-DT-2PIN",
                "datasheet_url": "https://www.te.com/usa-en/product-DT06-2S-CE06.pdf",
                "image_url": "/assets/images/dt06-2s.png",
                "in_stock_qty": 310,
                "min_stock_alert": 25,
                "category_id": cat_map["automotive-connectors"],
                "views": 520,
                "requests": 42,
                "attributes": [
                    ("Category", "Connectors > Automotive Connectors", "Classification"),
                    ("Fastening Type", "Latch Lock", "Mechanical"),
                    ("Series", "DT", "General"),
                    ("Primary Material", "Polyamide (PA) / Nylon", "Material"),
                    ("Housing Color", "Black", "Appearance"),
                    ("Connector Type", "Plug Housing", "Mechanical"),
                    ("Ingress Protection", "IP68 - Waterproof, Dust Tight", "Environmental"),
                    ("Number of Positions", "2", "Electrical"),
                    ("Contact Type", "Socket (Female)", "Electrical"),
                    ("Contact Size", "16", "Electrical"),
                    ("Mounting Type", "Free Hanging (In-Line)", "Mechanical"),
                    ("Operating Temperature", "-55°C ~ 125°C", "Environmental")
                ]
            },
            {
                "mfr_part_number": "DT04-4P",
                "digikey_part_number": "DT04-4P-ND",
                "manufacturer": "TE Connectivity DEUTSCH",
                "description": "CONN RECEPTACLE 4POS FLANGE GRAY",
                "detailed_description": "4 Position Automotive Connector Receptacle Housing for Male Pins Gray Panel/Flange Mount",
                "lead_time": "In Stock",
                "customer_reference": "AUTO-DT-4PIN",
                "datasheet_url": "https://www.te.com/usa-en/product-DT04-4P.pdf",
                "image_url": "/assets/images/dt04-4p.png",
                "in_stock_qty": 185,
                "min_stock_alert": 20,
                "category_id": cat_map["automotive-connectors"],
                "views": 315,
                "requests": 22,
                "attributes": [
                    ("Category", "Connectors > Automotive Connectors", "Classification"),
                    ("Fastening Type", "Latch Lock", "Mechanical"),
                    ("Series", "DT", "General"),
                    ("Primary Material", "Polyamide (PA) / Nylon", "Material"),
                    ("Housing Color", "Gray", "Appearance"),
                    ("Connector Type", "Receptacle Housing", "Mechanical"),
                    ("Ingress Protection", "IP68", "Environmental"),
                    ("Number of Positions", "4", "Electrical"),
                    ("Contact Type", "Pin (Male)", "Electrical"),
                    ("Contact Size", "16", "Electrical"),
                    ("Mounting Type", "Panel Mount", "Mechanical"),
                    ("Operating Temperature", "-55°C ~ 125°C", "Environmental")
                ]
            },
            {
                "mfr_part_number": "43025-0600",
                "digikey_part_number": "WM1784-ND",
                "manufacturer": "Molex",
                "description": "CONN HOUSING 6POS 3.00MM BLACK",
                "detailed_description": "6 Position Rectangular Connector Housing Receptacle Black 3.00mm Pitch Dual Row Micro-Fit 3.0",
                "lead_time": "Immediate / In Stock",
                "customer_reference": "MOLEX-MICROFIT-6P",
                "datasheet_url": "https://www.molex.com/pdm_docs/sd/430250600_sd.pdf",
                "image_url": "/assets/images/molex-43025.png",
                "in_stock_qty": 450,
                "min_stock_alert": 50,
                "category_id": cat_map["rectangular-connectors"],
                "views": 410,
                "requests": 35,
                "attributes": [
                    ("Category", "Connectors > Rectangular Connectors - Housings", "Classification"),
                    ("Fastening Type", "Locking Ramp", "Mechanical"),
                    ("Series", "Micro-Fit 3.0 43025", "General"),
                    ("Primary Material", "Polyester", "Material"),
                    ("Housing Color", "Black", "Appearance"),
                    ("Connector Type", "Receptacle Housing", "Mechanical"),
                    ("Number of Positions", "6", "Electrical"),
                    ("Contact Type", "Female Socket", "Electrical"),
                    ("Pitch", "3.00mm", "Mechanical"),
                    ("Operating Temperature", "-40°C ~ 105°C", "Environmental")
                ]
            },
            {
                "mfr_part_number": "MS3106A-18-1S",
                "digikey_part_number": "MS3106A18-1S-ND",
                "manufacturer": "Amphenol Industrial Operations",
                "description": "CONN PLUG 10POS STRAIGHT W/SKTS",
                "detailed_description": "10 Position Circular Connector Plug, Female Sockets Solder Cup Free Hanging (In-Line) MIL-DTL-5015",
                "lead_time": "2 Weeks",
                "customer_reference": "MIL-5015-10PIN",
                "datasheet_url": "https://www.amphenol-industrial.com/5015.pdf",
                "image_url": "/assets/images/ms3106.png",
                "in_stock_qty": 65,
                "min_stock_alert": 10,
                "category_id": cat_map["circular-connectors"],
                "views": 280,
                "requests": 15,
                "attributes": [
                    ("Category", "Connectors > Circular Industrial Connectors", "Classification"),
                    ("Fastening Type", "Threaded", "Mechanical"),
                    ("Series", "MIL-DTL-5015", "General"),
                    ("Shell Material", "Aluminum Alloy", "Material"),
                    ("Housing Color", "Olive Drab", "Appearance"),
                    ("Connector Type", "Plug, Female Sockets", "Mechanical"),
                    ("Ingress Protection", "Environmental Resisting", "Environmental"),
                    ("Number of Positions", "10", "Electrical"),
                    ("Shell Size - Insert", "18-1", "Mechanical"),
                    ("Contact Type", "Solder Cup", "Electrical"),
                    ("Mounting Type", "Free Hanging (In-Line)", "Mechanical")
                ]
            }
        ]

        for item in connectors_data:
            existing = db.query(Connector).filter(Connector.mfr_part_number == item["mfr_part_number"]).first()
            if not existing:
                conn_obj = Connector(
                    mfr_part_number=item["mfr_part_number"],
                    digikey_part_number=item["digikey_part_number"],
                    manufacturer=item["manufacturer"],
                    description=item["description"],
                    detailed_description=item["detailed_description"],
                    lead_time=item["lead_time"],
                    customer_reference=item["customer_reference"],
                    datasheet_url=item["datasheet_url"],
                    image_url=item["image_url"],
                    in_stock_qty=item["in_stock_qty"],
                    min_stock_alert=item["min_stock_alert"],
                    category_id=item["category_id"]
                )
                db.add(conn_obj)
                db.commit()
                db.refresh(conn_obj)

                # Add attributes
                for k, v, grp in item["attributes"]:
                    attr = ConnectorAttribute(connector_id=conn_obj.id, attr_key=k, attr_value=v, group_name=grp)
                    db.add(attr)

                # Add metric
                metric = ProductMetric(connector_id=conn_obj.id, view_count=item["views"], request_count=item["requests"])
                db.add(metric)
                db.commit()

        # 4. Seed sample inventory requests
        print("Seeding Sample Inventory Requests...")
        apc_conn = db.query(Connector).filter(Connector.mfr_part_number == "APC06-12-12S REV.II").first()
        dt_conn = db.query(Connector).filter(Connector.mfr_part_number == "DT06-2S-CE06").first()
        d38_conn = db.query(Connector).filter(Connector.mfr_part_number == "D38999/26WE35PN").first()

        req_samples = [
            {
                "code": "REQ-20260915-A101",
                "user": user1,
                "conn": apc_conn,
                "qty": 4,
                "status": "pending",
                "reason": "Sử dụng cho tủ điều khiển động cơ servo - Dự án Robot AGV",
                "date": datetime.utcnow() - timedelta(hours=3)
            },
            {
                "code": "REQ-20260915-B202",
                "user": user2,
                "conn": dt_conn,
                "qty": 8,
                "status": "pending",
                "reason": "Lắp ráp bó dây điện cảm biến rung xưởng số 2",
                "date": datetime.utcnow() - timedelta(hours=6)
            },
            {
                "code": "REQ-20260914-C303",
                "user": user1,
                "conn": d38_conn,
                "qty": 2,
                "status": "approved",
                "reason": "Thử nghiệm kết nối cáp quang và tín hiệu Radar",
                "response": "Đã phê duyệt xuất kho 2 chiếc, giao ca chiều.",
                "admin": admin,
                "date": datetime.utcnow() - timedelta(days=1)
            }
        ]

        for rs in req_samples:
            if rs["conn"]:
                existing = db.query(InventoryRequest).filter(InventoryRequest.request_code == rs["code"]).first()
                if not existing:
                    new_req = InventoryRequest(
                        request_code=rs["code"],
                        user_id=rs["user"].id,
                        connector_id=rs["conn"].id,
                        quantity=rs["qty"],
                        status=rs["status"],
                        reason=rs["reason"],
                        admin_response=rs.get("response"),
                        processed_by=rs.get("admin").id if rs.get("admin") else None,
                        requested_at=rs["date"],
                        processed_at=datetime.utcnow() if rs["status"] == "approved" else None
                    )
                    db.add(new_req)
        db.commit()

        print("=== Database Seed Completed Successfully! ===")

    except Exception as e:
        db.rollback()
        print("Error while seeding data:", e)
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
