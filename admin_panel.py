import streamlit as st
import os

# Use session state to track authentication
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

def admin_panel():
    st.title("🔐 Admin Panel")
    st.write("Here you can manage emails, users, feedback, etc.")
    st.subheader("📬 Saved Emails")
    EMAIL_FILE = "emails.txt"
    if os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, "r") as f:
            emails = f.readlines()
        for email in reversed(emails[-50:]):
            st.write(email.strip())
    else:
        st.info("No emails collected.")

with st.sidebar:
    if not st.session_state["admin_authenticated"]:
        with st.expander("🔐 Admin Panel", expanded=False):
            password = st.text_input("Enter Admin Password", type="password", label_visibility="collapsed", placeholder="Admin password")
            if password and password == os.getenv("ADMIN_PASSWORD", "qwmnasfjfuifgf"):
                st.session_state["admin_authenticated"] = True
                st.success("Access granted. Please re-open the Admin Panel.")
            elif password:
                st.warning("Incorrect password.")
    else:
        with st.expander("🔐 Admin Panel", expanded=True):
            admin_panel()
