import streamlit as st
import requests
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="File Upload Manager",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")

# ===============================
# SESSION STATE
# ===============================
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "username" not in st.session_state:
    st.session_state.username = None

# ===============================
# SIDEBAR AUTH
# ===============================
st.sidebar.title("🔐 Authentication")
login_tab, register_tab = st.sidebar.tabs(["Login", "Register"])

# LOGIN
with login_tab:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", width="stretch"):
        try:
            response = requests.get(
                f"{API_BASE_URL}/dashboard",
                auth=(email, password),
                timeout=5
            )
            if response.status_code == 200:
                st.session_state.auth_token = (email, password)
                st.session_state.username = email
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")
        except:
            st.error("Backend connection failed")

# REGISTER
with register_tab:
    reg_email = st.text_input("Email", key="reg_email")
    reg_pass = st.text_input("Password", type="password", key="reg_pass")
    reg_confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register", width="stretch"):
        if reg_pass != reg_confirm:
            st.error("Passwords do not match")
        else:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/auth/register",
                    json={"email": reg_email, "password": reg_pass},
                    timeout=5
                )
                if response.status_code == 200:
                    st.success("Registration successful")
                else:
                    st.error(response.json().get("detail", "Error"))
            except:
                st.error("Backend connection failed")

# ===============================
# MAIN APP
# ===============================
st.title("📁 File Upload Manager System")

if st.session_state.auth_token:

    st.sidebar.success(f"Logged in as {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.auth_token = None
        st.session_state.username = None
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📤 Upload", "📊 Dashboard", "📋 File Management", "🧠 ML Studio"]
    )

    # ===============================
    # TAB 1 - UPLOAD
    # ===============================
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
        st.header("Dashboard")

        response = requests.get(
            f"{API_BASE_URL}/dashboard",
            auth=st.session_state.auth_token
        )

        if response.status_code == 200:
            data = response.json()
            st.metric("Total Files", data["total_files"])

            if data["files"]:
                df = pd.DataFrame(data["files"])
                st.dataframe(df, width="stretch")

    # ===============================
    # TAB 3 - FILE MANAGEMENT
    # ===============================
    with tab3:
        st.header("Delete File")

        file_id = st.number_input("File ID", min_value=1)
        if st.button("Delete"):
            response = requests.delete(
                f"{API_BASE_URL}/files/{file_id}",
                auth=st.session_state.auth_token
            )
            if response.status_code == 200:
                st.success("File deleted")
            else:
                st.error("Deletion failed")

    # ===============================
    # TAB 4 - ML STUDIO
    # ===============================
    with tab4:
        st.header("🧠 ML Studio")

        ml_file = st.file_uploader("Upload CSV dataset", type=["csv"], key="ml")

        if ml_file:
            df = pd.read_csv(ml_file)
            st.dataframe(df.head(), width="stretch")

            if df.isna().sum().sum() > 0:
                st.warning("Dataset contains missing values. Automatic imputation will be applied.")

            target = st.selectbox("Select Target Column", df.columns)
            task_type = st.radio("Task Type", ["Classification", "Regression"])
            test_size = st.slider("Test Size %", 10, 40, 20) / 100

            if task_type == "Classification":
                model_choice = st.selectbox(
                    "Model",
                    ["Logistic Regression", "Random Forest", "Decision Tree"]
                )
            else:
                model_choice = st.selectbox(
                    "Model",
                    ["Linear Regression", "Random Forest Regressor"]
                )

            if st.button("Train Model"):

                try:
                    from sklearn.model_selection import train_test_split
                    from sklearn.impute import SimpleImputer
                    from sklearn.preprocessing import OneHotEncoder, StandardScaler
                    from sklearn.compose import ColumnTransformer
                    from sklearn.pipeline import Pipeline
                    from sklearn.metrics import (
                        accuracy_score,
                        confusion_matrix,
                        classification_report,
                        mean_squared_error,
                        r2_score
                    )
                    from sklearn.linear_model import LogisticRegression, LinearRegression
                    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
                    from sklearn.tree import DecisionTreeClassifier

                    X = df.drop(columns=[target])
                    y = df[target]

                    numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
                    categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()

                    numeric_pipeline = Pipeline([
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler())
                    ])

                    categorical_pipeline = Pipeline([
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore"))
                    ])

                    preprocessor = ColumnTransformer([
                        ("num", numeric_pipeline, numeric_cols),
                        ("cat", categorical_pipeline, categorical_cols)
                    ])

                    if model_choice == "Logistic Regression":
                        model = LogisticRegression(max_iter=1000)
                    elif model_choice == "Random Forest":
                        model = RandomForestClassifier()
                    elif model_choice == "Decision Tree":
                        model = DecisionTreeClassifier()
                    elif model_choice == "Linear Regression":
                        model = LinearRegression()
                    else:
                        model = RandomForestRegressor()

                    pipeline = Pipeline([
                        ("preprocessor", preprocessor),
                        ("model", model)
                    ])

                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=test_size, random_state=42
                    )

                    pipeline.fit(X_train, y_train)
                    y_pred = pipeline.predict(X_test)

                    st.success("Model trained successfully")

                    # =====================
                    # CLASSIFICATION
                    # =====================
                    if task_type == "Classification":
                        acc = accuracy_score(y_test, y_pred)
                        st.metric("Accuracy", f"{acc:.4f}")

                        cm = confusion_matrix(y_test, y_pred)

                        fig, ax = plt.subplots()
                        ax.imshow(cm)
                        ax.set_xlabel("Predicted")
                        ax.set_ylabel("Actual")

                        for i in range(len(cm)):
                            for j in range(len(cm[0])):
                                ax.text(j, i, cm[i, j],
                                        ha="center", va="center")

                        st.pyplot(fig)
                        st.text(classification_report(y_test, y_pred))

                    # =====================
                    # REGRESSION
                    # =====================
                    else:
                        mse = mean_squared_error(y_test, y_pred)
                        r2 = r2_score(y_test, y_pred)

                        col1, col2 = st.columns(2)
                        col1.metric("MSE", f"{mse:.4f}")
                        col2.metric("R² Score", f"{r2:.4f}")

                        fig, ax = plt.subplots()
                        ax.scatter(y_test, y_pred)
                        ax.set_xlabel("Actual")
                        ax.set_ylabel("Predicted")
                        st.pyplot(fig)

                except Exception as e:
                    st.error(f"Training failed: {str(e)}")

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

