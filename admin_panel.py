
import streamlit as st
import os

if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

if not st.session_state["admin_authenticated"]:
    st.title("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if password == os.getenv("ADMIN_PASSWORD", "your-hardcoded-default"):
        st.session_state["admin_authenticated"] = True
        st.experimental_rerun()
    elif password:
        st.error("Incorrect password.")
    st.stop()

# your admin logic here...
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

