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
from selenium_stealth import stealth

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="Hunter Pro 2025", layout="wide")

try:
    # IMPORTANT: The new SDK (google-genai) automatically handles the endpoint
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Missing API Key in Streamlit Secrets!")

# --- 2. TOOL: THE EMAIL CRAWLER ---
def crawl_website_for_email(url):
    """Visits the business website to find hidden emails."""
    if not url or "http" not in url:
        return "No Website"
    try:
        response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        # Search for email patterns using Regex
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        return list(set(emails))[0] if emails else "No email on homepage"
    except:
        return "Website Blocked/Offline"

# --- 3. SCRAPER: GOOGLE MAPS TO WEBSITE ---
def scrape_leads(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    stealth(driver, languages=["en-US"], vendor="Google Inc.", platform="Win32")

    leads = []
    try:
        search_url = f"https://www.google.com/maps/search/{niche}+in+{location}".replace(" ", "+")
        driver.get(search_url)
        time.sleep(5)

        # Scroll to load requested amount
        pane = driver.find_element(By.XPATH, '//div[@role="feed"]')
        for _ in range(2):
            pane.send_keys(Keys.PAGE_DOWN)
            time.sleep(2)

        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for res in results[:limit]:
            name = res.get_attribute("aria-label")
            # Click result to see details
            res.click()
            time.sleep(2)
            
            # Look for website link
            try:
                website_elem = driver.find_element(By.CSS_SELECTOR, "a[aria-label*='website']")
                website = website_elem.get_attribute("href")
            except:
                website = None
            
            leads.append({"Name": name, "Website": website})
    finally:
        driver.quit()
    return leads

# --- 4. STREAMLIT UI ---
st.title("🚀 Hunter Pro Lead Gen (2025 Edition)")
niche = st.text_input("Business Type", "Dentists")
loc = st.text_input("City", "New York")
count = st.slider("Leads to Fetch", 5, 20, 10)

if st.button("Start Hunting"):
    with st.spinner("Step 1: Scraping Google Maps for Websites..."):
        raw_leads = scrape_leads(niche, loc, count)
        
    with st.spinner("Step 2: Crawling Websites for Emails..."):
        final_data = []
        for lead in raw_leads:
            email = crawl_website_for_email(lead["Website"])
            final_data.append({
                "Business Name": lead["Name"],
                "Website": lead["Website"],
                "Email": email
            })
        
        st.session_state['leads'] = final_data
        st.success(f"Found {len(final_data)} leads!")

if 'leads' in st.session_state:
    df = pd.DataFrame(st.session_state['leads'])
    st.dataframe(df)

    # AI Pitching - FIXED 404 Logic
    st.subheader("Draft Personalized Pitch")
    target = st.selectbox("Select Business", df["Business Name"])
    
    if st.button("Generate AI Email"):
        try:
            # FIXED: Using 'gemini-2.5-flash' without 'models/' prefix
            # This matches your CMD output rule for the new SDK
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Write a 2-sentence cold email to {target} about their website."
            )
            st.info(response.text)
        except Exception as e:
            st.error(f"API Error: {e}")
