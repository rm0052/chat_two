import streamlit as st
import json
from scrapingbee import ScrapingBeeClient
from google import genai
import os
import uuid
import time

# Streamlit App Title
st.title("Test Chatbot")

# API Keys
SCRAPINGBEE_API_KEY = "U3URPLPZWZ3QHVGEEP5HTXJ95873G9L58RJ3EHS4WSYTXOZAIE71L278CF589042BBMKNXZTRY23VYPF"
GENAI_API_KEY = "AIzaSyDFbnYmLQ1Q55jIYYmgQ83sxledB_MgTbw"

DATA_FILE = "news_data2.json"  # File to store news data

# Generate or retrieve a session ID
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())  # Unique session ID

session_id = st.session_state["session_id"]

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
    st.write("🔍 Fetching latest news articles...")
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

    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    links = response.text.strip().split("\n")[1:-1]  # Remove first & last empty lines

    st.session_state["news_links"] = links
    news_data[session_id]["news_links"] = links
    save_news_data(news_data)

# 🚀 Fetch news automatically on app load (with retry if no links found)
def auto_fetch_news():
    max_retries = 3
    retries = 0
    while retries < max_retries:
        scrape_bloomberg()
        extract_links(st.session_state["news_articles"])
        
        if st.session_state["news_links"]:
            st.write(f"✅ {len(st.session_state['news_links'])} articles found.")
            break
        else:
            retries += 1
            time.sleep(2)  # Short delay before retry

    if not st.session_state["news_links"]:
        st.write("❌ Failed to fetch news after multiple attempts.")

# ✅ Auto-fetch news on app load (only once per session)
if "run_once" not in st.session_state:
    auto_fetch_news()
    st.session_state["run_once"] = True

# Display Chat History
st.write("## Chat History")
for q, r in st.session_state["chat_history"]:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write(r)

# User Input: Question
question = st.chat_input("Type your question and press Enter...")

# ✅ If no links are available during Q&A, auto-fetch news again
if question:
    if not st.session_state["news_links"]:
        st.write("⚠️ No articles found. Fetching news again...")
        auto_fetch_news()

    if st.session_state["news_links"]:
        st.write("🔗 Fetching content from saved news articles...")

        links = st.session_state["news_links"]
        client = genai.Client(api_key=GENAI_API_KEY)
        prompt = f"Answer only yes or no if the question requires specific information from the articles links. Question: {question} links: {links}."
        response = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt
        )
        answer = response.text.strip()

        # Follow-up Question
        if answer.lower() == "yes":
            final_prompt = f"Each link represents a news article. Respond with the summary of the article text of the link that the question is referring to. Question: {question} links: {links}"
        else:
            final_prompt = f'''Here are the links of news articles that have been published in the past few hours. Each article has a headline, the date/time it was published, and the article itself. The date appears right after the headline in the format 'day, date at time'. Use current time and date, for example, today is February 20th at 11:07 AM. Question: {question} Respond with the links that are useful: {links}'''

        # Generate response with Gemini
        final_response = client.models.generate_content(
            model="gemini-1.5-flash", contents=final_prompt
        )

        # Update session state and save chat history
        st.session_state["chat_history"].append((question, final_response.text.replace("$", "\\$").replace("provided text", "available information")))
        news_data[session_id]["chat_history"] = st.session_state["chat_history"]
        save_news_data(news_data)

        st.rerun()
