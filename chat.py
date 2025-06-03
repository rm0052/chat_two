import streamlit as st
import json
from scrapingbee import ScrapingBeeClient
from google import genai
import os
import uuid
from streamlit_js_eval import streamlit_js_eval
import sqlite3

DB_FILE = "emails.db"  # SQLite database file

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
# Streamlit App Title
st.title("News Chatbot")
init_db()
# API Keys
SCRAPINGBEE_API_KEY = "U3URPLPZWZ3QHVGEEP5HTXJ95873G9L58RJ3EHS4WSYTXOZAIE71L278CF589042BBMKNXZTRY23VYPF"
GENAI_API_KEY = "AIzaSyDFbnYmLQ1Q55jIYYmgQ83sxledB_MgTbw"

DATA_FILE = "news_data2.json"  # File to store news data

# Generate or retrieve a session ID
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())  # Unique session ID

session_id = st.session_state["session_id"]

EMAIL_FILE = "emails.txt"


DB_FILE = "emails.db"  # SQLite database file

def save_email(email):
    # Save to text file
    with open(EMAIL_FILE, "a") as f:
        f.write(email + "\n")
    
    # Save to SQLite database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO emails (email) VALUES (?)", (email,))
        conn.commit()
    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()

# Get user ID (unique per browser, stored in local storage)
user_id = streamlit_js_eval(js_expressions="window.localStorage.getItem('user_id')", key="get_user_id")

if not user_id:
    # Ask for email only if user_id not found
    email = st.text_input("Enter your email to continue:")
# Show admin panel ONLY if user_id is not set (i.e., user hasn't entered their email yet)
    if email and "@" in email:
        save_email(email)
        # Store user_id in browser
        streamlit_js_eval(js_expressions=f"window.localStorage.setItem('user_id', '{email}')", key="set_user_id")
        st.success("✅ Thanks! You're now connected.")
    else:
        st.warning("Please enter a valid email to start.")
        st.stop()
    with st.sidebar.expander("Admin Access"):
        if "is_admin" not in st.session_state:
            st.session_state["is_admin"] = False

        if not st.session_state["is_admin"]:
            admin_password = st.text_input("Enter admin password", type="password")
            if admin_password == "qwmnasfjfuifgf":  # Replace with your actual password
                st.session_state["is_admin"] = True
                st.success("Admin access granted.")
            elif admin_password:
                st.error("Incorrect password")
        else:
            st.sidebar.write("👋 Admin logged in")
            if st.sidebar.checkbox("Show saved emails"):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT email, timestamp FROM emails ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                conn.close()

                st.sidebar.write("### Saved Emails")
                for email, timestamp in rows:
                    st.sidebar.write(f"{email} (saved on {timestamp})")
else:
    st.success("✅ Welcome back!")
    # Proceed to chatbot

# Function to load stored news data
def load_news_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Function to save news data
def save_news_data(news_data):
    with open(DATA_FILE, "w") as f:
        json.dump(news_data, f)

# Load data into session state at startup
news_data = load_news_data()
if session_id not in news_data:
    news_data[session_id] = {"news_articles": "", "news_links": [], "chat_history": []}

st.session_state["news_articles"] = news_data[session_id]["news_articles"]
st.session_state["news_links"] = news_data[session_id]["news_links"]
st.session_state["chat_history"] = news_data[session_id]["chat_history"]


# Function to scrape Bloomberg headlines
def scrape_bloomberg():
    client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
    urls = ["https://finance.yahoo.com/topic/latest-news/"]
    articles = ""

    for url in urls:
        response = client.get(
            url,
            params={"ai_query": "Extract all article headlines and their links — show links as absolute urls"},
        )
        articles += " " + response.text  # Store raw response

    st.session_state["news_articles"] = articles
    news_data[session_id]["news_articles"] = articles
    save_news_data(news_data)

# Function to extract article links using Gemini
def extract_links(response_text):
    client = genai.Client(api_key=GENAI_API_KEY)
    prompt = f"Extract the links from the following text: {response_text}"

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    links = response.text.strip().split("\n")[1:-1]  # Remove first & last empty lines

    st.session_state["news_links"] = links
    news_data[session_id]["news_links"] = links
    save_news_data(news_data)
        
# Fetch News Button
if st.button("Fetch latest news"):
    st.write("🔍 Fetching latest news articles...")
    scrape_bloomberg()
    extract_links(st.session_state["news_articles"])
    st.write(f"✅ {len(st.session_state['news_links'])} articles found.")

# Display Chat History
st.write("## Chat History")
for q, r in st.session_state["chat_history"]:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write(r)

# User Input: Question
question = st.chat_input("Type your question and press Enter...")

# Get Answer Button
if question:
    if not st.session_state["news_links"]:
        st.write("⚠️ No articles found. Click 'Fetch News' first.")
    else:
        st.write("🔗 Fetching content from saved news articles...")

        links = st.session_state["news_links"]
        client = genai.Client(api_key=GENAI_API_KEY)
        prompt = f"Answer only yes or no if the question requires specific information from the articles links. Question: {question} links: {links}."
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        answer = response.text.strip()

        # Follow-up Question
        if answer.lower() == "yes":
            # final_prompt = f"Respond with the article text of the link that the question is referring to. Question: {question} links: {links}"
            final_prompt = f"Each link represents a news article. Respond with the summary of the article text of the link that the question is referring to. Question: {question} links: {links}"
        else:
            final_prompt = f'''Here are the links of news articles that have been published in the past few hours. Each article has a headline, the date/time it was published, and the article itself. The date appears right after the headline in the format 'day, date at time'. Use current time and date, for example, today is February 20th at 11:07 AM. Question: {question} Respond with the links that are useful: {links}'''

        # Generate response with Gemini
        final_response = client.models.generate_content(
            model="gemini-2.0-flash", contents=final_prompt
        )

        # Update session state and save chat history
        st.session_state["chat_history"].append((question, final_response.text.replace("$", "\\$").replace("provided text", "available information")))
        news_data[session_id]["chat_history"] = st.session_state["chat_history"]
        save_news_data(news_data)

        st.rerun()
