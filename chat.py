import streamlit as st
from scrapingbee import ScrapingBeeClient
from google import genai

# Streamlit App Title
st.title("Test chatbot")

# ScrapingBee API Key
SCRAPINGBEE_API_KEY = "U3URPLPZWZ3QHVGEEP5HTXJ95873G9L58RJ3EHS4WSYTXOZAIE71L278CF589042BBMKNXZTRY23VYPF"
GENAI_API_KEY = "AIzaSyDFbnYmLQ1Q55jIYYmgQ83sxledB_MgTbw"

# Function to scrape Bloomberg headlines
def scrape_bloomberg():
    client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
    # urls = [ "https://bloomberg.com/markets", "https://finance.yahoo.com/topic/latest-news/" ] 
    urls = ["https://finance.yahoo.com/topic/latest-news/"]
    articles="" 
    for url in urls: 
        response = client.get(url, params={"ai_query": "Extract all article headlines and their links — show links as absolute urls"} ) 
        articles+=" " + response.text # Check the response
    return articles

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
    return context

# Streamlit Button to Start Process

# User Input: Question
question = st.text_input("Enter your question")

# Search Button
if st.button("Get Answer") and question:
    st.write("🔍 Fetching article headlines...")

    # Step 1: Get Bloomberg Articles
    articles_text = scrape_bloomberg()
    
    st.write("✅ Headlines extracted. Getting links...")

    # Step 2: Extract Links
    links = extract_links(articles_text)
    
    st.write(f"🔗 {len(links)} articles found. Fetching content...")

    # Step 3: Summarize Articles
    context = summarize_articles(links)
    final_prompt = f"Answer the question and if the information in the context does not have news then ignore it: {question}. Context: {context}"
    client = genai.Client(api_key=GENAI_API_KEY)
    final_response = client.models.generate_content(
            model="gemini-1.5-flash", contents=final_prompt
        )

    st.write(final_response.text.replace("$", "\\$").replace("provided text", "available information"))
    
