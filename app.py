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
from selenium_stealth import stealth # New Import

# --- 1. UI THEME ---
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

# --- 2. INITIALIZATION ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("API Key missing! Please check Streamlit Secrets.")

# --- 3. STEALTH SCRAPER ENGINE ---
def run_real_hunter(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Random User-Agent to look like a real person
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)

    # --- STEALTH CONFIGURATION ---
    # This makes the bot invisible to Google's anti-bot detectors
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
        
        # Scroll logic
        try:
            scrollable = driver.find_element(By.XPATH, '//div[@role="feed"]')
            for _ in range(3): 
                scrollable.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
        except: pass

        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for e in elements[:limit]:
            name = e.get_attribute("aria-label")
            
            # JavaScript Click for stability
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
    if not url or url == "N/A": return "N/A"
    try:
        # Use a timeout so the app doesn't hang
        res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        return emails[0] if emails else "No email found"
    except: return "Connection failed"

# --- 4. DASHBOARD UI ---
st.title("Outreach Dashboard")
c1, c2 = st.columns(2)
with c1:
    n_in = st.text_input("Target Niche", placeholder="cafes")
    l_in = st.text_input("Location", placeholder="guwahati assam")
with c2:
    num_leads = st.slider("Lead Quantity", 5, 20, 10)
    p_in = st.text_area("Pitch Focus", placeholder="Specific offer details...")

if st.button("Initialize Hunter Machine"):
    if n_in and l_in:
        with st.spinner("Hunting leads with Stealth..."):
            raw = run_real_hunter(n_in, l_in, num_leads)
            for lead in raw:
                lead["Email"] = find_email(lead["Website"])
            st.session_state['leads'] = raw
    else:
        st.warning("Please enter both Niche and Location.")

if 'leads' in st.session_state:
    st.table(pd.DataFrame(st.session_state['leads']))
    
    st.subheader("Generate AI Content")
    if st.button("Draft AI Pitches"):
        try:
            # FIXED: Corrected string for Gemini 2.5 SDK
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Write a 1-sentence sales pitch for {n_in} businesses. Context: {p_in}"
            )
            st.success("Draft Generated!")
            st.write(response.text)
        except Exception as e:
            st.error(f"API Error: {e}")
