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


class Student:
    def __init__(self, name: str, age: int, student_id: str):
        self.name = name
        self.age = age
        self.student_id = student_id

    def __repr__(self):
        return f"Student(name={self.name}, age={self.age}, student_id={self.student_id})"