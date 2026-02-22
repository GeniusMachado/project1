import schemas
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

app = FastAPI(title="File Upload API", version="1.0.0")

# Enable CORS for frontend communication

# Origins that are allowed to make requests to the backend API
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "https://geniusmachado.com"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# --- Authenticaton layer for user ---
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ADMIN_USER")
    correct_password = os.getenv("ADMIN_PASSWORD")
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ---- Database connection initial setup (MySQL)
# Read MySQL connection info from environment variables
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "files_db")

# Example URL: mysql+pymysql://user:pass@host:3306/dbname
mysql_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
engine = create_engine(mysql_url, future=True)


def create_db_and_tables():
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS files (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        file_type VARCHAR(255),
        size BIGINT DEFAULT 0,
        status VARCHAR(50),
        reason TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
    except SQLAlchemyError as e:
        print("Failed to create tables:", e)


# Ensure tables exist at startup
create_db_and_tables()

# Track service start time for uptime reporting
START_TIME = datetime.utcnow()





@app.get("/")
def read_root():
    """Service info endpoint with helpful links and status.

    Returns JSON with uptime, available endpoints, docs link, allowed CORS origins,
    and a small DB summary (total files).
    """
    uptime = datetime.utcnow() - START_TIME

    # Try to get a small DB summary (total files)
    try:
        with engine.connect() as conn:
            total_files = conn.execute(text("SELECT COUNT(*) FROM files")).scalar()
    except Exception:
        total_files = None

    return {
        "service": getattr(app, "title", "File Upload API"),
        "version": getattr(app, "version", "1.0.0"),
        "status": "ok",
        "uptime_seconds": int(uptime.total_seconds()),
        "endpoints": ["/", "/upload", "/dashboard", "/files/{file_id}", "/docs", "/openapi.json"],
        "docs": "/docs",
        "allowed_origins": origins,
        "total_files": total_files,
        "note": "Use /docs for interactive API exploration and example requests."
    }







# --- THE ENDPOINT for collecting data from the user most likely will be an upload option for send a file over TCP ---
@app.post("/upload")
def upload_data(file: UploadFile = File(...), username: str = Depends(verify_credentials)):
    # 1. Extract file info
    file_name = file.filename
    file_size = file.size if file.size else 0
    file_type = file.content_type

    # 2. Apply Rules (Logic)
    status = ""
    reason = ""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    if file_size > MAX_FILE_SIZE:
        status = "Rejected"
        reason = "File size exceeds 10MB limit. Please reduce the file size."
    elif file_type and "pdf" not in file_type.lower():
        status = "Invalid Format"
        reason = "Only PDF files are accepted."
    elif not file_name:
        status = "Rejected"
        reason = "File name is required."
    else:
        status = "Accepted"
        reason = "File successfully received by the system."

    # 3. SAVE TO DATABASE (raw MySQL)
    insert_sql = text(
        "INSERT INTO files (name, file_type, size, status, reason) VALUES (:name, :file_type, :size, :status, :reason)"
    )

    try:
        with engine.begin() as conn:
            conn.execute(
                insert_sql,
                {
                    "name": file_name,
                    "file_type": file_type or "unknown",
                    "size": file_size,
                    "status": status,
                    "reason": reason,
                },
            )
            # Fetch last insert id
            new_id = conn.execute(text("SELECT LAST_INSERT_ID() as id")).scalar()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return {
        "status": status,
        "reason": reason,
        "database_id": int(new_id) if new_id is not None else None,
        "file_name": file_name,
        "uploaded_by": username,
    }






# --An endpoint to display all the files in our database with security for access control  --
@app.get("/dashboard")
def view_dashboard(username: str = Depends(verify_credentials)):
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT id, name, file_type, size, status, reason, uploaded_at FROM files ORDER BY uploaded_at DESC"
                )
            ).mappings().all()

            files = [dict(r) for r in rows]
            total_files = len(files)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return {"retrieved_by": username, "total_files": total_files, "files": files}

	



@app.delete("/files/{file_id}")
def delete_file(file_id: int, username: str = Depends(verify_credentials)):
    try:
        with engine.begin() as conn:
            existing = conn.execute(text("SELECT id FROM files WHERE id = :id"), {"id": file_id}).scalar()
            if not existing:
                raise HTTPException(status_code=404, detail="File not found")

            conn.execute(text("DELETE FROM files WHERE id = :id"), {"id": file_id})
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return {"ok": True, "message": f"File {file_id} has been deleted by {username}."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
