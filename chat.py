import streamlit as st
from scrapingbee import ScrapingBeeClient
from google import genai
from bs4 import BeautifulSoup

# Streamlit App Title
st.title("Test Chatbot")

# API Keys
SCRAPINGBEE_API_KEY = "U3URPLPZWZ3QHVGEEP5HTXJ95873G9L58RJ3EHS4WSYTXOZAIE71L278CF589042BBMKNXZTRY23VYPF"
GENAI_API_KEY = "AIzaSyDFbnYmLQ1Q55jIYYmgQ83sxledB_MgTbw"

# Initialize session state
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
        response = client.get(url, params={"render_js": "true"})  # Load JavaScript-rendered content
        soup = BeautifulSoup(response.text, "html.parser")
        
        for a_tag in soup.find_all("a", href=True):
            link = a_tag["href"]
            if link.startswith("https://finance.yahoo.com") and "/news/" in link:
                st.session_state["news_links"].append(link)
        
        articles += " " + response.text

    st.session_state["news_articles"] = articles


# Function to scrape and summarize articles
def summarize_articles(links):
    client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
    context = ""

    for url in links:
        response = client.get(url, params={"render_js": "true"})
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        article_text = "\n".join(p.get_text(strip=True) for p in paragraphs)
        
        context += " " + article_text[:500]  # Extract first 500 chars per article
        if len(context) >= 2000:
            break  # Stop after 2000 chars
    return context


# Fetch News Button
if st.button("Fetch News"):
    st.write("🔍 Fetching latest news articles...")
    scrape_bloomberg()
    st.write(f"✅ {len(st.session_state['news_links'])} articles fetched.")

# User Input: Question
question = st.text_input("Enter your question")

# Get Answer Button
if st.button("Get Answer") and question:
    if not st.session_state["news_links"]:
        st.write("⚠️ No articles found. Click 'Fetch News' first.")
    else:
        st.write("🔗 Fetching content from saved news articles...")
        
        # Summarize articles
        context = summarize_articles(st.session_state["news_links"])
        final_prompt = f"Answer the question and if the information in the context does not have news then ignore it: {question}. Context: {context}"
        
        # Generate response with Gemini
        client = genai.Client(api_key=GENAI_API_KEY)
        final_response = client.models.generate_content(
            model="gemini-1.5-flash", contents=final_prompt
        )

        st.write(final_response.text.replace("$", "\\$").replace("provided text", "available information"))
