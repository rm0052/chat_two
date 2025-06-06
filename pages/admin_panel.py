import streamlit as st
import os

st.title("🔐 Admin Panel")

if "is_admin" not in st.session_state or not st.session_state["is_admin"]:
    password = st.text_input("Enter admin password", type="password")
    if password == "qwmnasfjfuifgf":
        st.session_state["is_admin"] = True
        st.experimental_rerun()
    elif password:
        st.error("Incorrect password")
    st.stop()

st.success("✅ Admin access granted.")
st.subheader("📬 Saved Emails")

EMAIL_FILE = "emails.txt"
if os.path.exists(EMAIL_FILE):
    with open(EMAIL_FILE, "r") as f:
        emails = f.readlines()
    for email in reversed(emails[-50:]):
        st.write(email.strip())
else:
    st.info("No emails collected.")
