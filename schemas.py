from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    id: Optional[int] = None
    email: str
    is_admin: bool = False
    created_at: Optional[datetime] = None


class UserRegister(BaseModel):
    email: str
    password: str


class FileUpload(BaseModel):
    id: Optional[int] = None
    user_id: int
    name: str
    file_type: str
    size: int  # in bytes
    status: str
    reason: str
    uploaded_at: Optional[datetime] = None