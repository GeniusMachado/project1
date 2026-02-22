import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64
import os

# Page configuration
st.set_page_config(
    page_title="File Upload Manager",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2ca02c;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #2ca02c;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 4px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Backend API endpoint
API_BASE_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")

# Initialize session state for authentication
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "username" not in st.session_state:
    st.session_state.username = None

# Sidebar for authentication (credentials are sent to backend for validation)
st.sidebar.title("🔐 Authentication")
st.sidebar.info("📌 Credentials are securely transmitted to the backend API for validation.")

username = st.sidebar.text_input("Username", value=st.session_state.username or "", type="default")
password = st.sidebar.text_input("Password", value="", type="password")

if st.sidebar.button("Login", use_container_width=True, type="primary"):
    if username and password:
        # Send credentials to backend for validation
        try:
            response = requests.get(
                f"{API_BASE_URL}/dashboard",
                auth=(username, password),
                timeout=5
            )
            if response.status_code == 200:
                st.session_state.auth_token = (username, password)
                st.session_state.username = username
                st.success("✅ Authenticated successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Authentication failed.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Make sure it's running.")
        except Exception as e:
            st.error(f"❌ Authentication error: {str(e)}")
    else:
        st.error("❌ Please enter both username and password")

# Main content
st.markdown('<div class="main-header">📁 File Upload Manager System</div>', unsafe_allow_html=True)

if st.session_state.auth_token:
    st.sidebar.success(f"✅ Authenticated as: **{st.session_state.username}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        st.session_state.auth_token = None
        st.session_state.username = None
        st.success("✅ Logged out successfully!")
        st.rerun()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload File", "📊 Dashboard", "📋 File Details"])
    
    # TAB 1: Upload File
    with tab1:
        st.markdown('<div class="section-header">Upload a New File</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("📌 **Supported Format:** PDF files only\n\n⚠️ **Max Size:** 10MB")
        
        with col2:
            st.warning("🔒 Only authenticated users can upload files")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file to upload",
            type=["pdf"],
            help="Select a PDF file from your computer"
        )
        
        if uploaded_file is not None:
            # Show file preview
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Name", uploaded_file.name)
            with col2:
                st.metric("File Size", f"{uploaded_file.size / (1024*1024):.2f} MB")
            with col3:
                st.metric("File Type", uploaded_file.type)
            
            if st.button("🚀 Upload File", use_container_width=True, type="primary"):
                try:
                    # Prepare the file for upload
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    
                    # Make request with authentication
                    response = requests.post(
                        f"{API_BASE_URL}/upload",
                        files=files,
                        auth=st.session_state.auth_token,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.markdown(f"""
                        <div class="success-box">
                        <h4>✅ Upload Successful!</h4>
                        <p><strong>Status:</strong> {result['status']}</p>
                        <p><strong>Message:</strong> {result['reason']}</p>
                        <p><strong>Database ID:</strong> {result['database_id']}</p>
                        <p><strong>Uploaded by:</strong> {result['uploaded_by']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.success("File stored in database successfully!")
                    else:
                        st.markdown(f"""
                        <div class="error-box">
                        <h4>❌ Upload Failed</h4>
                        <p><strong>Status Code:</strong> {response.status_code}</p>
                        <p><strong>Error:</strong> {response.text}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend server. Make sure it's running.")
                except requests.exceptions.Timeout:
                    st.error("❌ Request timeout. File might be too large.")
                except Exception as e:
                    st.error(f"❌ Error uploading file: {str(e)}")
    
    # TAB 2: Dashboard
    with tab2:
        st.markdown('<div class="section-header">📊 Dashboard</div>', unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.session_state.refresh = True
        
        try:
            # Fetch dashboard data
            response = requests.get(
                f"{API_BASE_URL}/dashboard",
                auth=st.session_state.auth_token,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Retrieved by", data['retrieved_by'])
                with col2:
                    st.metric("Total Files", data['total_files'], delta=None)
                with col3:
                    st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))
                
                # Display files table
                if data['files']:
                    st.subheader("📋 File List")
                    
                    # Convert to DataFrame for better display
                    df_data = []
                    for file in data['files']:
                        df_data.append({
                            "ID": file['id'],
                            "Name": file['name'],
                            "Type": file['file_type'],
                            "Size (MB)": f"{file['size'] / (1024*1024):.2f}",
                            "Status": file['status'],
                            "Reason": file['reason'],
                            "Uploaded": file['uploaded_at'][:10] if 'uploaded_at' in file else "N/A"
                        })
                    
                    df = pd.DataFrame(df_data)
                    
                    # Color code status
                    def color_status(status):
                        if status == "Accepted":
                            return "background-color: #d4edda"
                        elif status == "Rejected":
                            return "background-color: #f8d7da"
                        else:
                            return "background-color: #fff3cd"
                    
                    st.dataframe(
                        df,
                        use_container_width=True,
                        height=400
                    )
                    
                    # File statistics
                    st.subheader("📈 File Statistics")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Status breakdown
                        status_counts = {}
                        for file in data['files']:
                            status_counts[file['status']] = status_counts.get(file['status'], 0) + 1
                        
                        st.bar_chart(status_counts)
                    
                    with col2:
                        # File types breakdown
                        type_counts = {}
                        for file in data['files']:
                            ftype = file['file_type'].split('/')[-1] if '/' in file['file_type'] else file['file_type']
                            type_counts[ftype] = type_counts.get(ftype, 0) + 1
                        
                        st.pie_chart(type_counts)
                else:
                    st.info("📭 No files uploaded yet.")
            
            else:
                st.error(f"❌ Error fetching dashboard: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend server.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # TAB 3: File Details & Management
    with tab3:
        st.markdown('<div class="section-header">🗂️ File Management</div>', unsafe_allow_html=True)
        
        # Delete file section
        st.subheader("🗑️ Delete File")
        
        col1, col2 = st.columns(2)
        
        with col1:
            file_id = st.number_input(
                "Enter File ID to delete:",
                min_value=1,
                step=1,
                help="Enter the ID of the file you want to delete"
            )
        
        with col2:
            if st.button("🗑️ Delete File", use_container_width=True, type="secondary"):
                try:
                    response = requests.delete(
                        f"{API_BASE_URL}/files/{file_id}",
                        auth=st.session_state.auth_token,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.markdown(f"""
                        <div class="success-box">
                        <h4>✅ Deletion Successful!</h4>
                        <p>{result['message']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="error-box">
                        <h4>❌ Deletion Failed</h4>
                        <p>{response.json().get('detail', 'Unknown error')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.divider()
        
        # API Information
        st.subheader("ℹ️ API Information")
        st.info(f"""
        **Backend API Base URL:** `{API_BASE_URL}`
        
        **Available Endpoints:**
        - `POST /upload` - Upload a new file
        - `GET /dashboard` - View all files
        - `DELETE /files/{{file_id}}` - Delete a file
        - `GET /` - API health check
        """)

else:
    st.warning("⚠️ Please authenticate using the sidebar to continue.")
    
    # Display info for unauthenticated users
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        ### 🔐 Backend Authentication:
        1. Enter your username in the sidebar
        2. Enter your password in the sidebar
        3. Click the Login button
        4. Your credentials are validated on the backend
        5. Start uploading files!
        """)
    
    with col2:
        st.success("""
        ### ✨ Features:
        - 📤 Upload PDF files securely
        - 📊 View dashboard with analytics
        - 🗑️ Delete files from database
        - 🔐 Backend-handled authentication
        - 📋 File statistics and charts
        - 🌐 Cloudflare Tunnel support
        """)

# Footer
st.divider()
st.markdown("""
---
<div style="text-align: center; color: gray; font-size: 0.85rem;">
    <p>File Upload Manager System © 2026| All rights reserved</p>
    <p>Built with <strong>Streamlit</strong> + <strong>FastAPI</strong> + <strong>SQLModel</strong> + <strong>Cloudflare Tunnel</strong></p>
    <p><em>Authentication handled on backend • Powered by uv package manager</em></p>
</div>
""", unsafe_allow_html=True)

