import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .database import engine, Base
from .models import User, Category, Connector, ConnectorLibrary, ConnectorAttribute, InventoryRequest, ProductMetric, AuditLog
from .routers import auth, categories, connectors, requests, library

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống Quản lý Kho Connector (Connector Inventory) - REST API & Web Dashboard"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(categories.router, prefix=settings.API_V1_STR)
app.include_router(connectors.router, prefix=settings.API_V1_STR)
app.include_router(requests.router, prefix=settings.API_V1_STR)
app.include_router(library.router, prefix=settings.API_V1_STR)

# Locate Frontend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = FRONTEND_DIR / "assets" / "images" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

import uuid
import shutil
from fastapi import UploadFile, File, HTTPException

@app.post("/api/upload/image", tags=["Upload"])
async def upload_image(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ tệp ảnh (.png, .jpg, .jpeg, .webp, .gif)")
    
    unique_filename = f"conn_{uuid.uuid4().hex[:10]}{ext}"
    dest_path = UPLOAD_DIR / unique_filename
    
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu tệp ảnh: {str(e)}")
        
    return {
        "url": f"/assets/images/uploads/{unique_filename}",
        "filename": unique_filename
    }

if FRONTEND_DIR.exists():
    # Mount frontend static files (css, js, assets)
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/", tags=["Pages"])
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/product-detail", tags=["Pages"])
    def serve_detail():
        return FileResponse(str(FRONTEND_DIR / "product-detail.html"))

    @app.get("/admin-approval", tags=["Pages"])
    def serve_approval():
        return FileResponse(str(FRONTEND_DIR / "admin-approval.html"))

    @app.get("/admin-manage", tags=["Pages"])
    def serve_manage():
        return FileResponse(str(FRONTEND_DIR / "admin-manage.html"))

    @app.get("/admin-library", tags=["Pages"])
    def serve_library():
        return FileResponse(str(FRONTEND_DIR / "admin-library.html"))

    @app.get("/admin-users", tags=["Pages"])
    def serve_users():
        return FileResponse(str(FRONTEND_DIR / "admin-users.html"))

@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
