import streamlit as st
from scrapingbee import ScrapingBeeClient
from google import genai

# Streamlit App Title
st.title("Bloomberg Article Summarizer")

# ScrapingBee API Key
SCRAPINGBEE_API_KEY = "U3URPLPZWZ3QHVGEEP5HTXJ95873G9L58RJ3EHS4WSYTXOZAIE71L278CF589042BBMKNXZTRY23VYPF"
GENAI_API_KEY = "AIzaSyDFbnYmLQ1Q55jIYYmgQ83sxledB_MgTbw"

# Function to scrape Bloomberg headlines
def scrape_bloomberg():
    client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
    response = client.get(
        "https://bloomberg.com/markets",
        params={"ai_query": "Extract all article headlines and their links — show links as absolute urls"}
    )
    return response.text

# Function to extract article links using Gemini
def extract_links(response_text):
    client = genai.Client(api_key=GENAI_API_KEY)
    prompt = f"Extract the links from the following text: {response_text}"
    
    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    links = response.text.strip().split("\n")[1:-1]  # Remove first & last empty lines
    return links

# Function to scrape articles and summarize them
def summarize_articles(links):
    client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
    context = ""
    
    for url in links:
        response = client.get(url, params={"render_js": "true"})
        context += " " + response.text[:500]  # Extract first 500 chars per article
        if len(context) >= 2000:
            break  # Stop after 2000 chars

    # Summarize using Gemini
    genai_client = genai.Client(api_key=GENAI_API_KEY)
    prompt = f"Summarize the following information: {context}"
    response = genai_client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    
    return response.text.strip()

# Streamlit Button to Start Process
if st.button("Summarize Bloomberg Market News"):
    st.write("🔍 Fetching article headlines...")

    # Step 1: Get Bloomberg Articles
    articles_text = scrape_bloomberg()
    
    st.write("✅ Headlines extracted. Getting links...")

    # Step 2: Extract Links
    links = extract_links(articles_text)
    
    st.write(f"🔗 {len(links)} articles found. Fetching content...")

    # Step 3: Summarize Articles
    summary = summarize_articles(links)
    
    # Display Summary
    st.subheader("📝 Summary:")
    st.write(summary)
