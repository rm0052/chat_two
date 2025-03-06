import streamlit as st
import json
from scrapingbee import ScrapingBeeClient
from google import genai
import os

# Streamlit App Title
st.title("Test Chatbot")

# API Keys
SCRAPINGBEE_API_KEY = "U3URPLPZWZ3QHVGEEP5HTXJ95873G9L58RJ3EHS4WSYTXOZAIE71L278CF589042BBMKNXZTRY23VYPF"
GENAI_API_KEY = "AIzaSyDFbnYmLQ1Q55jIYYmgQ83sxledB_MgTbw"

DATA_FILE = "news_data.json"  # File to store news data

# Function to load stored news data
def load_news_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"news_articles": "", "news_links": []}
    return {"news_articles": "", "news_links": []}

# Function to save news data
def save_news_data(news_articles, news_links):
    with open(DATA_FILE, "w") as f:
        json.dump({"news_articles": news_articles, "news_links": news_links}, f)

# Load data into session state at startup
if "news_articles" not in st.session_state or "news_links" not in st.session_state:
    saved_data = load_news_data()
    st.session_state["news_articles"] = saved_data["news_articles"]
    st.session_state["news_links"] = saved_data["news_links"]

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
    save_news_data(articles, st.session_state["news_links"])

# Function to extract article links using Gemini
def extract_links(response_text):
    client = genai.Client(api_key=GENAI_API_KEY)
    prompt = f"Extract the links from the following text: {response_text}"

    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    links = response.text.strip().split("\n")[1:-1]  # Remove first & last empty lines

    st.session_state["news_links"] = links
    save_news_data(st.session_state["news_articles"], links)

# Fetch News Button
if st.button("Fetch News"):
    st.write("🔍 Fetching latest news articles...")
    scrape_bloomberg()
    extract_links(st.session_state["news_articles"])
    st.write(f"✅ {len(st.session_state['news_links'])} articles found.")

# User Input: Question
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

question = st.text_area("Enter your question", height=100)
# Get Answer Button
if st.button("Get Answer") and question:
    if not st.session_state["news_links"]:
        st.write("⚠️ No articles found. Click 'Fetch News' first.")
    else:
        st.write("🔗 Fetching content from saved news articles...")

        links = st.session_state["news_links"]
        prompt = f"Answer only yes or no if the question requires specific information from the articles links. Question: {question} links: {links}."
        response = client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt
        )
        answer = response.text.strip()

        # Follow-up Question
        if answer.lower() == "yes":
            final_prompt = f"Respond with the article text of the link that the question is referring to. Question: {question} links: {links}"
        else:
            final_prompt = f'''Here are the links of news articles that have been published in the past few hours. Each article has a headline, the date/time it was published, and the article itself. The date appears right after the headline in the format 'day, date at time'. Use current time and date, for example, today is February 20th at 11:07 AM. Question: {question} Respond with the links that are useful: {links}'''

        # Generate response with Gemini
        client = genai.Client(api_key=GENAI_API_KEY)
        final_response = client.models.generate_content(
            model="gemini-1.5-flash", contents=final_prompt
        )
        st.session_state["chat_history"].append((question, final_response.text.replace("$", "\\$").replace("provided text", "available information")))
st.write("## Chat History")
for q, r in st.session_state["chat_history"]:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write(r)
