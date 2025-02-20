import streamlit as st
from scrapingbee import ScrapingBeeClient
from google import genai

# Streamlit App Title
st.title("Test Chatbot")

# API Keys
SCRAPINGBEE_API_KEY = "U3URPLPZWZ3QHVGEEP5HTXJ95873G9L58RJ3EHS4WSYTXOZAIE71L278CF589042BBMKNXZTRY23VYPF"
GENAI_API_KEY = "AIzaSyDFbnYmLQ1Q55jIYYmgQ83sxledB_MgTbw"

# Initialize session state variables
if "news_articles" not in st.session_state:
    st.session_state["news_articles"] = ""
if "news_links" not in st.session_state:
    st.session_state["news_links"] = []


# Function to scrape Bloomberg headlines
def scrape_bloomberg():
    client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
    urls = ["https://finance.yahoo.com/topic/latest-news/"]
    articles = ""
    for url in urls:
        response = client.get(
            url,
            params={
                "ai_query": "Extract all article headlines and their links — show links as absolute urls"
            },
        )
        articles += " " + response.text  # Store raw response

    st.session_state["news_articles"] = articles


# Function to extract article links using Gemini
def extract_links(response_text):
    client = genai.Client(api_key=GENAI_API_KEY)
    prompt = f"Extract the links from the following text: {response_text}"

    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    links = response.text.strip().split("\n")[1:-1]  # Remove first & last empty lines

    st.session_state["news_links"] = links  # Store links in session state


# Function to scrape and summarize articles
def summarize_articles(links):
    client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
    context = ""

    for url in links:
        response = client.get(url, params={"render_js": "true"})
        context += " " + response.text[:500]  # Extract first 500 chars per article
        if len(context) >= 2000:
            break  # Stop after 2000 chars
    return context


# Fetch News Button
if st.button("Fetch News"):
    st.write("🔍 Fetching latest news articles...")
    scrape_bloomberg()
    extract_links(st.session_state["news_articles"])
    st.write(f"✅ {len(st.session_state['news_links'])} articles found.")

# User Input: Question
question = st.text_input("Enter your question")

# Get Answer Button
if st.button("Get Answer") and question:
    if not st.session_state["news_links"]:
        st.write("⚠️ No articles found. Click 'Fetch News' first.")
    else:
        st.write("🔗 Fetching content from saved news articles...")
        # Summarize articles
        links=st.session_state["news_links"]
        # context = summarize_articles(st.session_state["news_links"])
        # final_prompt = f"Answer the question and if the information in the context does not have news then ignore it: {question}. Context: {context}"
        final_prompt=f'''Here are the links of news articles that have been published in the past few hours. Each article has a headline, the time it was published and the article itself. Based on the articles, users will ask questions like "which companies have appeared in the past hour?" or "summarize the news" Question: {question} Respond with the links that are useful: {links}'''
        # Generate response with Gemini
        client = genai.Client(api_key=GENAI_API_KEY)
        final_response = client.models.generate_content(
            model="gemini-1.5-flash", contents=final_prompt
        )

        st.write(final_response.text.replace("$", "\\$").replace("provided text", "available information"))
