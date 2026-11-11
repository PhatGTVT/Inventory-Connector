from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: str
    department: Optional[str] = None
    role: str = "user"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserAdminCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    department: Optional[str] = None
    role: str = "user"
    is_active: bool = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResetPassword(BaseModel):
    new_password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
