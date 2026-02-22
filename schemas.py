from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class FileUpload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    file_type: str
    size: int  # in bytes
    status: str
    reason: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class Student:
    def __init__(self, name: str, age: int, student_id: str):
        self.name = name
        self.age = age
        self.student_id = student_id

    def __repr__(self):
        return f"Student(name={self.name}, age={self.age}, student_id={self.student_id})"