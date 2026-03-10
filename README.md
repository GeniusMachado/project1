# 📁 File Upload Manager System

A complete microservices application for file management with a modern Streamlit UI and FastAPI backend, fully containerized with Docker Compose.

## ✨ Features

- 📤 **Secure File Upload** - Upload PDF files with authentication
- 📊 **Dashboard** - View all uploaded files with analytics and statistics
- 🗑️ **File Management** - Delete files from the database
- 🔐 **Authentication** - HTTP Basic authentication for secure access
- 📈 **Analytics** - Real-time charts and file statistics
- 🐳 **Docker Support** - Complete containerization with Docker Compose
- 🎨 **Beautiful UI** - Modern Streamlit interface with custom styling

## 🔧 Fixed Issues

### Backend (main.py)
✅ Fixed undefined `pdf` type hint - Changed to proper `UploadFile` with `File` dependency
✅ Fixed inverted file size logic - Now correctly checks if file exceeds 10MB limit
✅ Fixed undefined `data` variable - Changed to `file_record.id`
✅ Fixed file type comparison - Now compares against string "pdf" correctly
✅ Fixed database model usage - Integrated with `FileUpload` SQLModel
✅ Fixed dependency injection - Properly implemented `Depends(verify_credentials)`
✅ Fixed undefined `main()` function - Added proper uvicorn entry point
✅ Added CORS middleware - Enables frontend-backend communication
✅ Improved error handling - Returns proper HTTP exceptions

### Frontend (frontend.py)
✅ Fixed import typo - Changed `streamit` to `streamlit`
✅Built complete Streamlit UI with:
  - Authentication sidebar
  - File upload interface with preview
  - Dashboard with statistics and charts
  - File management panel
  - Custom CSS styling
  - Error handling

### Database (schemas.py)
✅ Added `FileUpload` SQLModel for proper database integration
✅ Includes timestamp for upload tracking
✅ Proper relationships and field definitions

## 📋 Project Structure

```
project1/
├── main.py                    # FastAPI backend (FIXED)
├── frontend.py               # Streamlit UI (FIXED)
├── schemas.py               # SQLModel definitions (UPDATED)
├── Dockerfile.backend       # Backend container (UPDATED - port 8000)
├── Dockerfile.frontend      # Frontend container (NEW)
├── docker-compose.yml       # Orchestration file (NEW)
├── requirements.txt         # Python dependencies (UPDATED)
├── .env.example            # Environment template (NEW)
├── database.db             # SQLite database (Auto-created)
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Environment variables configured

### Setup Steps

1. **Clone the repository** (or use your existing project):
   ```bash
   cd project1
   ```

2. **Create .env file from template**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials:
   ```
   ADMIN_USER=admin
   ADMIN_PASSWORD=your_secure_password
   ```

3. **Build and start all services**:
   ```bash
   docker-compose up --build
   ```

   This will start:
   - **Backend API**: http://localhost:8000
   - **Frontend UI**: http://localhost:8501
   - **Database**: SQLite (database.db)

4. **Access the application**:
   - Frontend: http://localhost:8501
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs (Swagger UI)

## 🔗 Services

### Backend API (FastAPI)
- **Port**: 8000
- **Container**: `file_upload_backend`
- **Endpoints**:
  - `POST /upload` - Upload a PDF file with authentication
  - `GET /dashboard` - View all uploaded files (requires auth)
  - `DELETE /files/{file_id}` - Delete a file (requires auth)
  - `GET /` - Health check
  - `GET /docs` - Swagger API documentation
  - `GET /redoc` - ReDoc documentation

### Frontend UI (Streamlit)
- **Port**: 8501
- **Container**: `file_upload_frontend`
- **Features**:
  - Login panel with username/password
  - File upload with PDF validation
  - Dashboard with statistics
  - File management interface

### Database
- **Type**: SQLite
- **Location**: `database.db`
- **Schema**: Automatically created on startup

## 🔐 Authentication

Default credentials (from `.env.example`):
- **Username**: `something`
- **Password**: `verysecured`

Change these in your `.env` file before deployment!

## 📊 API Examples

### Upload a File
```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Basic $(echo -n admin:password123 | base64)" \
  -F "file=@document.pdf"
```

### Get Dashboard
```bash
curl -X GET http://localhost:8000/dashboard \
  -H "Authorization: Basic $(echo -n admin:password123 | base64)"
```

### Delete a File
```bash
curl -X DELETE http://localhost:8000/files/1 \
  -H "Authorization: Basic $(echo -n admin:password123 | base64)"
```

## 🛠️ Development

### Local Development (without Docker)

1. **Setup Python virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt or you can also use uv sync
   ```

3. **Set environment variables**:
   ```bash
   export ADMIN_USER=something444
   export ADMIN_PASSWORD=verystrong
   ```

4. **Run backend**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Run frontend** (in another terminal):
   Update `API_BASE_URL` in `frontend.py` to `http://localhost:8000`
   ```bash
   streamlit run frontend.py
   ```

### Docker Commands

**View container logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Stop services**:
```bash
docker-compose down
```

**Rebuild without cache**:
```bash
docker-compose up --build --no-cache
```

**Execute command in container**:
```bash
docker-compose exec backend bash
```

## 📝 Environment Variables

| `ADMIN_USER` | very strong | Backend admin username |
| `ADMIN_PASSWORD` | very secured | Backend admin password |
| `DATABASE_URL` | sqlite:///database.db | Database connection string |
| `STREAMLIT_SERVER_PORT` | 8501 | Frontend port |



### Backend can't connect
- Check if backend container is running: `docker-compose ps`
- View logs: `docker-compose logs backend`
- Ensure `.env` file exists with proper credentials

### Frontend can't reach backend
- Verify backend is healthy: `docker-compose exec backend curl http://backend:8000/`
- Check network: `docker network ls`
- Restart services: `docker-compose restart`

### Database issues
- Delete and recreate: `rm database.db && docker-compose up --build`
- Check permissions: `ls -la database.db`
- On my linux machine sometimes I face race condition and also sometimes MariaDB takes time to boot up and sometimes there is port conflicts with 8000 or 8080 for backend and the DB trying to populate on the same port number of localhost. 
- You might wanna debug this if your docker compose up breaks and the application does not start.
### Port conflicts
- Change ports in `docker-compose.yml`
- Check existing services: `netstat -tuln | grep LISTEN`

## 📦 Dependencies

- **FastAPI**: Modern web framework for Python
- **Streamlit**: ML app framework with UI
- **SQLModel**: SQL database ORM with pydantic validation
- **Uvicorn**: ASGI server
- **python-dotenv**: Environment variable management
- **requests**: HTTP library for frontend-backend communication
- **pandas**: Data manipulation and analysis

## 🔐 Security Notes

⚠️ **Important**: The current setup uses:
- HTTP Basic Authentication
- CORS allows all origins (`*`)
- SQLite database (not recommended for production)

For production deployment:
1. Use HTTPS/SSL
2. Configure specific CORS origins
3. Use a production database (PostgreSQL, MySQL)
4. Implement JWT or OAuth2 authentication
5. Add rate limiting
6. Use environment-specific configs

## 📄 License

This project is provided as-is for educational purposes.

## ✅ What Was Fixed

1. **Type Definition**: Changed undefined `pdf` to `UploadFile` with proper dependency injection
2. **Logic Errors**: Fixed inverted file size check (was accepting large files, rejecting small ones)
3. **Variable References**: Fixed undefined `data` variable referencing in response
4. **Database Operations**: Properly integrated FileUpload SQLModel for database operations
5. **Authentication**: Fixed dependency injection syntax for verify_credentials
6. **Frontend**: Complete rewrite with modern Streamlit UI including authentication, uploads, and dashboard
7. **Docker Setup**: Updated backend port to 8000, added frontend Dockerfile, created docker-compose orchestration
8. **Dependencies**: Added all required packages (streamlit, pandas, requests, python-multipart)
