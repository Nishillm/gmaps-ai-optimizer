import streamlit as st
import pandas as pd
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth
from docx import Document
import io
import time

# --- UI THEME (UNCHANGED) ---
st.set_page_config(page_title="Hunter Pro Dashboard", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #FCE4EC !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #E1BEE7 !important; border-radius: 8px !important;
    }
    input, textarea { color: #000000 !important; font-weight: 500; }
    label, p, h1, h2, h3, .stMarkdown, span { color: #000000 !important; }
    .stButton>button {
        background-color: #9575CD; color: white; border-radius: 8px; width: auto; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD SECRETS FROM DASHBOARD ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MY_EMAIL = st.secrets["MY_GMAIL"]
    APP_PASS = st.secrets["GMAIL_APP_PASSWORD"]
except Exception as e:
    st.error("Secrets not found! Check your Streamlit Cloud 'Secrets' tab.")

# --- SCRAPER WITH SCROLLING TO FIX LEAD COUNT ---
def run_real_hunter(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    
    leads = []
    try:
        query = f"{niche} in {location}".replace(" ", "+")
        driver.get(f"https://www.google.com/maps/search/{query}")
        time.sleep(5)
        
        # SCROLL FIX: Scroll the side pane to load more than 4 results
        try:
            scroll_container = driver.find_element(By.XPATH, '//div[@role="feed"]')
            for _ in range(3): 
                scroll_container.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
        except:
            pass 

        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for e in elements[:limit]:
            name = e.get_attribute("aria-label")
            # RATINGS FIX: Get actual ratings from class MW4Y7c
            try:
                parent = e.find_element(By.XPATH, "./../../..")
                rating = parent.find_element(By.CLASS_NAME, "MW4Y7c").text
            except:
                rating = "N/A"
            
            leads.append({
                "Business Name": name, 
                "Location": location, 
                "Rating": rating, 
                "Email": "contact@verifiedpro.com"
            })
    finally:
        driver.quit()
    return leads

# --- UI LOGIC ---
if 'leads' not in st.session_state: st.session_state['leads'] = []

with st.sidebar:
    st.title("Main Menu")
    page = st.radio("Navigate", ["Dashboard", "History"])

if page == "Dashboard":
    st.title("Outreach Dashboard")
    c1, c2 = st.columns(2)
    with c1:
        n_in = st.text_input("Target Niche", placeholder="e.g. Cafes")
        l_in = st.text_input("Location", placeholder="e.g. Guwahati")
    with c2:
        num_leads = st.slider("Lead Quantity", 5, 50, 10)
        p_in = st.text_area("Pitch Instructions", placeholder="Describe your offer...")

    if st.button("Initialize Hunter Machine"):
        if n_in and l_in:
            with st.spinner(f"Scraping {num_leads} leads..."):
                st.session_state['leads'] = run_real_hunter(n_in, l_in, num_leads)
                st.success("Targeting Complete.")

    if st.session_state['leads']:
        st.subheader("Lead Report Table")
        st.table(pd.DataFrame(st.session_state['leads']))
        
        for idx, lead in enumerate(st.session_state['leads']):
            if st.button(f"Send AI Pitch to {lead['Business Name']}", key=f"p_{idx}"):
                try:
                    # THE 404 FIX: Use EXACT string "gemini-1.5-flash"
                    response = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=f"Write a short professional pitch for {lead['Business Name']}. Context: {p_in}"
                    )
                    st.toast(f"Generated pitch for {lead['Business Name']}!")
                    # Email logic follows here...
                except Exception as e:
                    st.error(f"API Error: {e}")
