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

# --- 1. UI THEME (Matches your Lavender/Purple Screenshot) ---
st.set_page_config(page_title="Hunter Pro Dashboard", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #E1BEE7 !important; border-radius: 8px !important;
    }
    .stButton>button {
        background-color: #9575CD; color: white; border-radius: 8px; font-weight: bold;
    }
    label, p, h1 { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True) # FIXED: Changed from unsafe_allow_index to unsafe_allow_html

# --- 2. INITIALIZATION ---
try:
    # Uses the exact keys from your Secrets screenshot
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Credential Error: Please check your Streamlit Secrets.")

# --- 3. STEALTH SCRAPER ENGINE ---
def run_stealth_hunter(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)

    # Apply Stealth to bypass Google bot detection
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    leads = []
    try:
        query = f"{niche} in {location}".replace(" ", "+")
        driver.get(f"https://www.google.com/maps/search/{query}")
        time.sleep(5)
        
        # Scroll logic to load results
        try:
            scroll_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
            for _ in range(2): 
                scroll_div.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
        except: pass

        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for e in elements[:limit]:
            name = e.get_attribute("aria-label")
            
            # Use JS Click to avoid 'ElementClickIntercepted' error
            driver.execute_script("arguments[0].scrollIntoView(true);", e)
            driver.execute_script("arguments[0].click();", e)
            time.sleep(2)
            
            try:
                web_elem = driver.find_element(By.CSS_SELECTOR, "a[aria-label*='website']")
                website = web_elem.get_attribute("href")
            except: website = None
            
            leads.append({"Business Name": name, "Website": website or "N/A"})
    finally:
        driver.quit()
    return leads

def find_email(url):
    """Crawls website for email patterns."""
    if not url or url == "N/A": return "N/A"
    try:
        res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        return list(set(emails))[0] if emails else "Manual Check Needed"
    except: return "Link Blocked"

# --- 4. DASHBOARD UI ---
st.title("Outreach Dashboard")
c1, c2 = st.columns(2)
with c1:
    target_niche = st.text_input("Target Niche", placeholder="cafes")
    location = st.text_input("Location", placeholder="guwahati assam")
with c2:
    lead_qty = st.slider("Lead Quantity", 5, 20, 10)
    pitch_focus = st.text_area("Pitch Focus", placeholder="Specific offer details...")

if st.button("Initialize Hunter Machine"):
    if target_niche and location:
        with st.spinner("Hunting leads with Stealth Mode..."):
            raw_data = run_stealth_hunter(target_niche, location, lead_qty)
            for lead in raw_data:
                lead["Email"] = find_email(lead["Website"])
            st.session_state['leads'] = raw_data
    else:
        st.warning("Please enter both Niche and Location.")

if 'leads' in st.session_state:
    st.table(pd.DataFrame(st.session_state['leads']))
    
    st.subheader("Generate AI Content")
    if st.button("Draft AI Pitches"):
        try:
            # FIXED: Used 'gemini-2.0-flash' (clean ID) to resolve 404
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Draft a short pitch for {target_niche} in {location}. Focus: {pitch_focus}"
            )
            st.success("Draft Generated!")
            st.info(response.text)
        except Exception as e:
            st.error(f"API Error: {e}")
