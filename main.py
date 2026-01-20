import schemas
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from sqlmodel import Session, select, create_engine, SQLModel

engine = create_engine("sqlite:///database.db")

def get_session():
    with Session(engine) as session:
        yield session

        
def main():
    print("Hello from project1!")


if __name__ == "__main__":
    main()
