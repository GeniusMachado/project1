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
import hashlib
import secrets

load_dotenv()

# Local utilities for file processing, pandas/numpy analysis, and AI summarization
from utilities import process_uploaded_file, save_analysis_for_id, load_analysis_for_id

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


# --- Password hashing utilities ---
def hash_password(password: str) -> str:
    """Hash a password using SHA256 with a salt."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}:{hash_obj.hexdigest()}"


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, hash_value = stored_hash.split(":")
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except ValueError:
        return False


# --- Authentication layer ---
def authenticate_user(credentials: HTTPBasicCredentials) -> dict:
    """Authenticate a user from credentials (DB user or admin)."""
    email = credentials.username
    password = credentials.password

    # Check if admin
    admin_email = os.getenv("ADMIN_USER")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if email == admin_email and password == admin_password:
        return {"id": None, "email": email, "is_admin": True}

    # Check database for regular user
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, email, password_hash, is_admin FROM users WHERE email = :email"),
                {"email": email},
            ).mappings().first()

            if row and verify_password(row["password_hash"], password):
                return {
                    "id": row["id"],
                    "email": row["email"],
                    "is_admin": row["is_admin"],
                }
    except SQLAlchemyError:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Basic"},
    )


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """Dependency to verify and return authenticated user."""
    return authenticate_user(credentials)

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
    create_users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    create_files_table_sql = """
    CREATE TABLE IF NOT EXISTS files (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        file_type VARCHAR(255),
        size BIGINT DEFAULT 0,
        status VARCHAR(50),
        reason TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_users_table_sql))
            conn.execute(text(create_files_table_sql))
    except SQLAlchemyError as e:
        print("Failed to create tables:", e)


# Ensure tables exist at startup
create_db_and_tables()

# Track service start time for uptime reporting
START_TIME = datetime.utcnow()





@app.get("/")
def read_root():
    """Service info endpoint with helpful links and status. Returns JSON with uptime, available endpoints, docs link, allowed CORS origins, and a small DB summary (total files)."""
    uptime = datetime.utcnow() - START_TIME

    # Try to get a small DB summary
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
        "endpoints": [
            "/",
            "/auth/register",
            "/upload",
            "/dashboard",
            "/files/{file_id}",
            "/docs",
            "/openapi.json"
        ],
        "docs": "/docs",
        "allowed_origins": origins,
        "total_files": total_files,
        "note": "Use /docs for interactive API exploration and example requests."
    }







# USER REGISTRATION ENDPOINT
@app.post("/auth/register")
def register_user(user: schemas.UserRegister):
    """Register a new user account.
    
    Email must be unique and password is hashed before storage.
    Returns user ID and email on success.
    """
    email = user.email.strip().lower()
    password = user.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    password_hash = hash_password(password)

    try:
        with engine.begin() as conn:
            # Check if email already exists
            existing = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email},
            ).scalar()

            if existing:
                raise HTTPException(status_code=409, detail="Email already registered")

            # Insert new user
            conn.execute(
                text(
                    "INSERT INTO users (email, password_hash, is_admin) VALUES (:email, :password_hash, FALSE)"
                ),
                {"email": email, "password_hash": password_hash},
            )
            new_user_id = conn.execute(text("SELECT LAST_INSERT_ID() as id")).scalar()

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return {
        "message": "User registered successfully",
        "user_id": int(new_user_id) if new_user_id else None,
        "email": email,
    }


# for collecting data from the user most likely will be an upload option for send a file over TCP
@app.post("/upload")
def upload_data(file: UploadFile = File(...), user: dict = Depends(verify_credentials)):
    """Upload a file. User must be authenticated.
    
    File owner is recorded in the database. Returns file ID and upload status.
    """
    # Admin cannot upload via basic auth (use is_admin=True check)
    if user.get("is_admin") and user.get("id") is None:
        raise HTTPException(status_code=403, detail="Admin cannot upload files via this endpoint")

    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User must be logged in to upload")

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

    # 3. SAVE TO DATABASE (raw MySQL) with user_id
    insert_sql = text(
        "INSERT INTO files (user_id, name, file_type, size, status, reason) VALUES (:user_id, :name, :file_type, :size, :status, :reason)"
    )

    try:
        with engine.begin() as conn:
            conn.execute(
                insert_sql,
                {
                    "user_id": user_id,
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

    # Save uploaded file bytes to disk and process it (background processing could be used later)
    try:
        uploads_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        saved_path = None
        # Read bytes from UploadFile
        try:
            file.file.seek(0)
        except Exception:
            pass
        try:
            file_bytes = file.file.read()
        except Exception:
            file_bytes = b""

        if new_id is not None:
            save_name = f"{int(new_id)}_{file_name}"
            saved_path = os.path.join(uploads_dir, save_name)
            with open(saved_path, "wb") as f:
                f.write(file_bytes)

            # Process file: pandas/numpy analysis + AI summary
            try:
                analysis = process_uploaded_file(file_bytes, file_name)
                save_analysis_for_id(int(new_id), analysis)
            except Exception as e:
                # Log but don't abort upload
                print("Analysis failed:", e)

    except Exception as e:
        print("Failed to save/process uploaded file:", e)

    return {
        "status": status,
        "reason": reason,
        "database_id": int(new_id) if new_id is not None else None,
        "file_name": file_name,
        "uploaded_by": user.get("email"),
    }






# An endpoint to display all the files in our database with security for access control  
@app.get("/dashboard")
def view_dashboard(user: dict = Depends(verify_credentials)):
    """Get dashboard with files.
    
    - Regular users see only their own files.
    - Admin sees all files from all users with user email.
    """
    try:
        with engine.connect() as conn:
            if user.get("is_admin"):
                # Admin sees all files with user info
                rows = conn.execute(
                    text(
                        """
                        SELECT f.id, f.user_id, f.name, f.file_type, f.size, f.status, f.reason, 
                               f.uploaded_at, u.email as uploaded_by
                        FROM files f
                        JOIN users u ON f.user_id = u.id
                        ORDER BY f.uploaded_at DESC
                        """
                    )
                ).mappings().all()
            else:
                # Regular user sees only their files
                rows = conn.execute(
                    text(
                        """
                        SELECT id, user_id, name, file_type, size, status, reason, uploaded_at
                        FROM files
                        WHERE user_id = :user_id
                        ORDER BY uploaded_at DESC
                        """
                    ),
                    {"user_id": user.get("id")},
                ).mappings().all()

            files = [dict(r) for r in rows]
            total_files = len(files)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return {
        "retrieved_by": user.get("email"),
        "is_admin": user.get("is_admin"),
        "total_files": total_files,
        "files": files,
    }

	



@app.delete("/files/{file_id}")
def delete_file(file_id: int, user: dict = Depends(verify_credentials)):
    """Delete a file. Only admin or the file owner can delete.Regular users can only delete their own files.
    Admin can delete any file.
    """
    try:
        with engine.begin() as conn:
            # Get file info
            file_row = conn.execute(
                text("SELECT id, user_id FROM files WHERE id = :id"),
                {"id": file_id},
            ).mappings().first()

            if not file_row:
                raise HTTPException(status_code=404, detail="File not found")

            # Check permissions
            if not user.get("is_admin") and file_row["user_id"] != user.get("id"):
                raise HTTPException(
                    status_code=403,
                    detail="You can only delete your own files",
                )

            # Delete the file
            conn.execute(text("DELETE FROM files WHERE id = :id"), {"id": file_id})
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return {
        "ok": True,
        "message": f"File {file_id} has been deleted by {user.get('email')}.",
    }


@app.get("/files/{file_id}/analysis")
def get_file_analysis(file_id: int, user: dict = Depends(verify_credentials)):
    """Return analysis results for a given file if available."""
    try:
        # Check permission: file owner or admin
        with engine.connect() as conn:
            row = conn.execute(text("SELECT id, user_id FROM files WHERE id = :id"), {"id": file_id}).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="File not found")
            if not user.get("is_admin") and row["user_id"] != user.get("id"):
                raise HTTPException(status_code=403, detail="Forbidden")

        analysis = load_analysis_for_id(file_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not available for this file")
        return analysis
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
