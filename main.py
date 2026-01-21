import schemas
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List
from pydantic import BaseModel
from sqlmodel import Session, select, create_engine, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()



def get_session():
    with Session(engine) as session:
        yield session


def main():
    print("Hello from project1!")


if __name__ == "__main__":
    main()
