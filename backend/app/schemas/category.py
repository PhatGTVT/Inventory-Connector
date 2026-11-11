from typing import Optional, List
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    slug: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    connector_count: Optional[int] = 0

    class Config:
        from_attributes = True

class CategoryTree(CategoryOut):
    subcategories: List["CategoryTree"] = []

    class Config:
        from_attributes = True
