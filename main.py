import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
from visualizer import show_visuals  # Your own visuals module

# 1. Database Connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="raman@1234",  # Replace with your actual password
        database="bizpulse_db"
    )

# 2. User Account Functions
def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    cursor.close()
    conn.close()

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# 3. Upload Log Functions
def log_file_upload(username, filename):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_uploads (username, filename, upload_time) VALUES (%s, %s, %s)",
        (username, filename, datetime.now())
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_user_uploads(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename, upload_time FROM user_uploads WHERE username = %s ORDER BY upload_time DESC",
        (username,)
    )
    uploads = cursor.fetchall()
    cursor.close()
    conn.close()
    return uploads

# 4. Streamlit UI
st.set_page_config(page_title="BizPulse", layout="wide")

from PIL import Image
import streamlit as st

# Load logo image
logo = Image.open("logo.png")

# Two-column layout: title on the left, logo on the right
col1, col2 = st.columns([3, 2])  # Adjust ratio for better space usage

with col1:
    st.markdown("## 🔐 Welcome to BizPulse – Business Analytics App")

with col2:
    st.image(logo, width=250)  # Increase width to cover more space



option = st.sidebar.selectbox("🔒 Login / Signup", ["Login", "Signup"])

if option == "Signup":
    st.subheader("Create an Account")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")
    if st.button("Signup"):
        try:
            create_user(new_username, new_password)
            st.success("✅ Account created! Please log in.")
        except Exception as e:
            st.error(f"Error: {e}").append(item)

elif option == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login successful!")
        else:
            st.error("❌ Invalid username or password")

# 5. Main App (after login)
if st.session_state.get("logged_in"):
    st.markdown(f"### 👋 Hello, {st.session_state.username}! Upload your sales data below.")
    st.markdown("#### 📁 Upload Your Sales CSV File")

    # 🧠 CSV format reminder
    st.info("""
    To ensure proper analysis, your CSV must include the following columns:

    - `Order Date` (in YYYY-MM-DD format)
    - `Customer ID`
    - `Product`
    - `Category`
    - `Quantity`
    - `Unit Price`

    ✅ `Total Revenue` will be calculated if not provided.
    """)

    uploaded_file = st.file_uploader("Choose your CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()  # Clean column names

            st.write("📌 CSV Columns Detected:", df.columns.tolist())

            # Convert 'Order Date' to datetime
            if "Order Date" in df.columns:
                df["Order Date"] = pd.to_datetime(df["Order Date"], errors='coerce')

            # Validate & Calculate Total Revenue
            if "Quantity" in df.columns and "Unit Price" in df.columns:
                df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
                df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce")

                if "Total Revenue" not in df.columns:
                    df["Total Revenue"] = df["Quantity"] * df["Unit Price"]
                    st.success("✅ 'Total Revenue' calculated successfully.")
                else:
                    st.info("ℹ️ 'Total Revenue' already present in the file.")
            else:
                st.error("❌ Columns 'Quantity' and 'Unit Price' are required to compute 'Total Revenue'.")
                st.stop()

            # Log upload in DB
            log_file_upload(st.session_state.username, uploaded_file.name)

            # Show preview and visuals
            st.success("✅ File uploaded successfully!")
            st.dataframe(df.head())
            show_visuals(df)

            # Upload history
            st.subheader("📂 Your Uploaded Files:")
            for fname, ftime in get_user_uploads(st.session_state.username):
                st.write(f"- **{fname}** uploaded at `{ftime}`")

        except Exception as e:
            st.error(f"⚠️ Failed to process file: {e}")
