import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sqlalchemy import text
from app.database import engine, Base
from app.models.library import ConnectorLibrary
from app.models.connector import Connector

def run_migration():
    print("Running database migration for ConnectorLibrary and Connectors...")
    with engine.connect() as conn:
        # 1. Create connector_library table if not exists using SQLAlchemy Base
        Base.metadata.create_all(bind=engine)
        print("Ensured all tables created via Base.metadata.")

        # 2. Check and add location column to connectors if missing
        res = conn.execute(text("SHOW COLUMNS FROM connectors LIKE 'location'")).fetchall()
        if not res:
            print("Adding 'location' column to connectors...")
            conn.execute(text("ALTER TABLE connectors ADD COLUMN location VARCHAR(100) DEFAULT 'Kệ A1'"))
            conn.commit()

        # 3. Check and add library_id column to connectors if missing
        res2 = conn.execute(text("SHOW COLUMNS FROM connectors LIKE 'library_id'")).fetchall()
        if not res2:
            print("Adding 'library_id' column to connectors...")
            conn.execute(text("ALTER TABLE connectors ADD COLUMN library_id INT NULL"))
            conn.commit()
            try:
                conn.execute(text("ALTER TABLE connectors ADD CONSTRAINT fk_connectors_library FOREIGN KEY (library_id) REFERENCES connector_library(id) ON DELETE SET NULL"))
                conn.commit()
            except Exception as e:
                print(f"Note on FK constraint: {e}")

        # 4. Migrate existing connectors into connector_library
        connectors = conn.execute(text("SELECT id, mfr_part_number, digikey_part_number, manufacturer, category_id, description, detailed_description, lead_time, datasheet_url, image_url, library_id FROM connectors")).fetchall()
        
        migrated_count = 0
        for row in connectors:
            c_id = row[0]
            mpn = row[1]
            dk_pn = row[2]
            mfr = row[3]
            cat_id = row[4]
            desc = row[5]
            det_desc = row[6]
            lead = row[7]
            ds = row[8]
            img = row[9]
            lib_id = row[10]

            # Check if MPN already exists in connector_library
            existing = conn.execute(text("SELECT id FROM connector_library WHERE mfr_part_number = :mpn"), {"mpn": mpn}).fetchone()
            if existing:
                target_lib_id = existing[0]
            else:
                insert_res = conn.execute(text("""
                    INSERT INTO connector_library (mfr_part_number, digikey_part_number, manufacturer, category_id, description, detailed_description, lead_time, datasheet_url, image_url, created_at, updated_at)
                    VALUES (:mpn, :dk_pn, :mfr, :cat_id, :desc, :det_desc, :lead, :ds, :img, NOW(), NOW())
                """), {
                    "mpn": mpn,
                    "dk_pn": dk_pn,
                    "mfr": mfr,
                    "cat_id": cat_id,
                    "desc": desc,
                    "det_desc": det_desc,
                    "lead": lead,
                    "ds": ds,
                    "img": img
                })
                conn.commit()
                target_lib_id = insert_res.lastrowid
                migrated_count += 1

            if lib_id != target_lib_id:
                conn.execute(text("UPDATE connectors SET library_id = :lib_id WHERE id = :c_id"), {"lib_id": target_lib_id, "c_id": c_id})
                conn.commit()

        print(f"Migration completed! Migrated {migrated_count} new library items. Linked all existing connectors to connector_library.")

if __name__ == "__main__":
    run_migration()
