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
        st.header("Upload File")

        uploaded_file = st.file_uploader("Choose file")

        if uploaded_file and st.button("Upload"):
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                auth=st.session_state.auth_token
            )
            if response.status_code == 200:
                st.success("File uploaded successfully")
            else:
                st.error("Upload failed")

    # ===============================
    # TAB 2 - DASHBOARD
    # ===============================
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
    st.warning("Please login to continue.")