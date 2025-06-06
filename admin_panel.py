import streamlit as st
import os

# Simple access control
st.set_page_config(page_title="Admin Panel", layout="centered",expanded=False)

password = st.text_input("Enter Admin Password", type="password", label_visibility="collapsed", placeholder="Admin password")

if password == os.getenv("ADMIN_PASSWORD", "qwmnasfjfuifgf"):  # Use environment variable or hardcoded
    st.success("Access granted.")
    
    st.title("🔐 Admin Panel")
    st.write("Here you can manage emails, users, feedback, etc.")
    # Add your admin logic here (e.g., load saved emails)
    st.subheader("📬 Saved Emails")
    EMAIL_FILE = "emails.txt"
    if os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, "r") as f:
            emails = f.readlines()
        for email in reversed(emails[-50:]):
            st.write(email.strip())
    else:
        st.info("No emails collected.")

else:
    st.warning("This page is restricted. Enter the correct password.")
    st.stop()
