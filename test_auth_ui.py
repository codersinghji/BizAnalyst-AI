
import streamlit as st

from auth.auth_ui import show_auth_page, logout_user

st.set_page_config(
    page_title="BizAnalyst-AI Authentication",
    page_icon="🔐",
    layout="centered"
)

if show_auth_page():

    user = st.session_state.user

    st.success("Login successful!")

    st.title("Welcome to BizAnalyst-AI")

    st.write("Name:", user["name"])
    st.write("Email:", user["email"])
    st.write("Role:", user["role"])

    if st.button("Logout"):
        logout_user()
