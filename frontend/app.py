import streamlit as st
import requests
from add_update import add_update_tab
from analytics_by_category import analytics_category_tab
from analytics_by_months import analytics_months_tab
import os
API_URL = os.getenv("API_URL", "https://expense-tracking-system-app.onrender.com")

st.set_page_config(page_title="Expense Tracking System", layout="wide")
st.title("Expense Tracking System")


# Session state for user and token
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None

# Login / Signup Tabs
if st.session_state.user is None:
    auth_tab = st.tabs(["Login", "Signup"])

    # Login Tab
    with auth_tab[0]:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            try:
                response = requests.post("http://127.0.0.1:8000/login", json={
                    "username": username,
                    "password": password
                })

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.user = data["user"]
                    st.session_state.token = data["access_token"]  # Store the token
                    st.success(f"Welcome {st.session_state.user['name']}!")
                    st.rerun()
                else:
                    error_detail = response.json().get("detail", "Login failed")
                    st.error(error_detail)
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

    # Signup Tab
    with auth_tab[1]:
        st.subheader("Signup")
        actual_name = st.text_input("Full Name", key="signup_name")
        username_s = st.text_input("Username", key="signup_username")
        password_s = st.text_input("Password", type="password", key="signup_password")

        st.info("Password requirements: At least 8 characters, 1 uppercase, 1 lowercase, 1 digit")

        if st.button("Signup", key="signup_button"):
            try:
                response = requests.post("http://127.0.0.1:8000/signup", json={
                    "actual_name": actual_name,
                    "username": username_s,
                    "password": password_s
                })

                if response.status_code == 200:
                    st.success("Signup successful! Please log in.")
                else:
                    error_detail = response.json().get("detail", "Signup failed")
                    st.error(error_detail)
            except Exception as e:
                st.error(f"Connection error: {str(e)}")


# Main Tabs for Expenses
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"Logged in as: **{st.session_state.user['name']}**")
    with col2:
        if st.button("Logout", key="logout_button"):
            st.session_state.user = None
            st.session_state.token = None
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["Add/Update", "Analytics By Category", "Analytics By Months"])

    with tab1:
        add_update_tab(user_id=st.session_state.user["id"], token=st.session_state.token)

    with tab2:
        analytics_category_tab(user_id=st.session_state.user["id"], token=st.session_state.token)

    with tab3:
        analytics_months_tab(user_id=st.session_state.user["id"], token=st.session_state.token)

