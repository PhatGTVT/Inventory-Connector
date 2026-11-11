from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.category import Category
from ..models.connector import Connector
from ..schemas.category import CategoryCreate, CategoryOut
from ..services.auth_service import get_current_admin

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    # Annotate with connector count
    result = []
    for cat in categories:
        count = db.query(func.count(Connector.id)).filter(Connector.category_id == cat.id).scalar() or 0
        cat_data = CategoryOut(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            parent_id=cat.parent_id,
            description=cat.description,
            icon=cat.icon,
            connector_count=count
        )
        result.append(cat_data)
    return result

@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(cat_in: CategoryCreate, db: Session = Depends(get_db), admin = Depends(get_current_admin)):
    existing = db.query(Category).filter(Category.slug == cat_in.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã danh mục (slug) đã tồn tại")
    
    new_cat = Category(**cat_in.model_dump())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return CategoryOut(
        id=new_cat.id,
        name=new_cat.name,
        slug=new_cat.slug,
        parent_id=new_cat.parent_id,
        description=new_cat.description,
        icon=new_cat.icon,
        connector_count=0
    )
