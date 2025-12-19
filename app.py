import streamlit as st
import pandas as pd
import re
import requests
import time
from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- UI & THEME ---
st.set_page_config(page_title="Hunter Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { background-color: #6a5acd; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_index=True)

# --- INITIALIZATION ---
try:
    # Use clean API key initialization
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Credential Error: Please check your Streamlit Secrets.")

# --- SCRAPER LOGIC ---
def get_email_from_site(url):
    """Crawls business website for email addresses."""
    if not url or "http" not in url: return "N/A"
    try:
        res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        return emails[0] if emails else "No email found"
    except: return "Connection failed"

def run_scraper(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080") # Prevents element overlap
    driver = webdriver.Chrome(options=options)
    leads = []

    try:
        url = f"https://www.google.com/maps/search/{niche}+in+{location}".replace(" ", "+")
        driver.get(url)
        time.sleep(5)

        # Scroll loop to load more leads
        feed = driver.find_element(By.XPATH, '//div[@role="feed"]')
        for _ in range(2):
            feed.send_keys(Keys.PAGE_DOWN)
            time.sleep(2)

        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for res in results[:limit]:
            name = res.get_attribute("aria-label")
            
            # FIX: JS Click to avoid ElementClickInterceptedException
            driver.execute_script("arguments[0].scrollIntoView(true);", res)
            driver.execute_script("arguments[0].click();", res)
            time.sleep(2)

            try:
                # Extract Website URL
                web_elem = driver.find_element(By.CSS_SELECTOR, "a[aria-label*='website']")
                website = web_elem.get_attribute("href")
            except: website = None

            leads.append({"Name": name, "Website": website or "N/A"})
    finally:
        driver.quit()
    return leads

# --- DASHBOARD UI ---
st.title(" Lead Hunter Dashboard")
col1, col2 = st.columns(2)
with col1: niche = st.text_input("Niche", "Real Estate")
with col2: loc = st.text_input("Location", "Miami")
count = st.slider("Leads", 5, 20, 10)

if st.button("Start Extraction"):
    with st.spinner("Hunting leads..."):
        raw_data = run_scraper(niche, loc, count)
        for lead in raw_data:
            lead["Email"] = get_email_from_site(lead["Website"])
        st.session_state['leads'] = raw_data

if 'leads' in st.session_state:
    df = pd.DataFrame(st.session_state['leads'])
    st.table(df)

    # FIXED AI CALL
    if st.button("Generate AI Pitches"):
        try:
            # FIX: Use clean ID 'gemini-2.5-flash' to avoid 404
            res = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents="Write a cold email for these businesses."
            )
            st.success("Drafts Ready!")
            st.write(res.text)
        except Exception as e:
            st.error(f"404 Fix needed: Ensure model name is exactly 'gemini-2.5-flash'. Error: {e}")
