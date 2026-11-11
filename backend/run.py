import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("=" * 55)
    print("  Connector Inventory API & Web Dashboard")
    print("  http://localhost:8000  - Web Catalog")
    print("  http://localhost:8000/docs - Swagger API Docs")
    print("=" * 55)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
