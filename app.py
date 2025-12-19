import streamlit as st
import pandas as pd
import re
import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth

# --- 1. UI THEME (Lavender Styles) ---
st.set_page_config(page_title="Hunter Pro Dashboard", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #E1BEE7 !important; border-radius: 8px !important;
    }
    .stButton>button {
        background-color: #9575CD; color: white; border-radius: 8px; font-weight: bold; width: 100%;
    }
    label, p, h1 { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MAILING & AI INITIALIZATION ---
def send_personalized_email(target_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["MY_GMAIL"]
        msg['To'] = target_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(st.secrets["MY_GMAIL"], st.secrets["GMAIL_APP_PASSWORD"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail Error: {e}")
        return False

try:
    # Using the Client initialization that worked in your older version
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Credential Error: Please check your Streamlit Secrets.")

# --- 3. AUDIT ENGINE ---
def deep_scrape_business(url, business_name):
    if not url or url == "N/A": return "No website found."
    try:
        res = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        analysis = []
        if "schema.org/LocalBusiness" not in res.text: analysis.append("Missing Local SEO Schema")
        if "viewport" not in res.text.lower(): analysis.append("Not mobile-optimized")
        if res.elapsed.total_seconds() > 2.5: analysis.append("Poor site speed")
        return f"Audit for {business_name}: " + (", ".join(analysis) if analysis else "Standard site.")
    except: return "Audit limited: Website unreachable."

# --- 4. STEALTH SCRAPER (Fixed Stale Error) ---
def run_stealth_hunter(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    
    leads = []
    try:
        query = f"{niche} in {location}".replace(" ", "+")
        driver.get(f"https://www.google.com/maps/search/{query}")
        time.sleep(6)
        
        # Fresh search for feed and scrolling
        try:
            feed = driver.find_element(By.XPATH, '//div[@role="feed"]')
            for _ in range(2):
                feed.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
        except: pass

        # Index-based loop to prevent StaleElementReferenceException
        for i in range(limit):
            try:
                # Re-find results inside the loop for stability
                results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                if i >= len(results): break
                
                target = results[i]
                name = target.get_attribute("aria-label")
                driver.execute_script("arguments[0].scrollIntoView(true);", target)
                driver.execute_script("arguments[0].click();", target)
                time.sleep(2)
                
                try:
                    website = driver.find_element(By.CSS_SELECTOR, "a[aria-label*='website']").get_attribute("href")
                except: website = "N/A"
                
                leads.append({"Name": name, "Website": website})
            except: continue
    finally:
        driver.quit()
    return leads

# --- 5. UI & AUTOMATION DASHBOARD ---
st.title("Outreach Dashboard & Automated Sender")

c1, c2 = st.columns(2)
with c1:
    target_niche = st.text_input("Target Niche", value="cafes")
    location = st.text_input("Location", value="guwahati assam")
with c2:
    lead_qty = st.slider("Lead Quantity", 5, 20, 10)
    service = st.text_input("Offering", "GMaps Ranking & 10% Demo Audit")

if st.button("Initialize Hunter Machine"):
    with st.spinner("Hunting leads with Stealth Mode..."):
        st.session_state['leads_list'] = run_stealth_hunter(target_niche, location, lead_qty)

if 'leads_list' in st.session_state:
    for idx, lead in enumerate(st.session_state['leads_list']):
        with st.container():
            col_a, col_b, col_c = st.columns([2, 2, 1])
            col_a.write(f"**{lead['Name']}**")
            col_b.write(lead['Website'])
            
            if col_c.button(f"Deep Audit & Send", key=f"btn_{idx}"):
                with st.spinner(f"Processing {lead['Name']}..."):
                    # 1. Email Extraction
                    try:
                        res = requests.get(lead['Website'], timeout=5)
                        email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)[0]
                    except: email = None

                    if not email:
                        st.error("No email found.")
                    else:
                        # 2. Audit Analysis
                        audit_results = deep_scrape_business(lead['Website'], lead['Name'])
                        
                        # 3. AI Generation (Using the prompt format from your working version)
                        try:
                            # Use the exact model name from your working snippet
                            # and ensure contents is passed clearly
                            ai_response = client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents=f"Draft a short pitch for {lead['Name']} in {location}. Focus on these audit findings: {audit_results}. My offer is {service}. Mention I'll do 10% demo work for free."
                            )
                            pitch_text = ai_response.text
                            
                            # 4. Automatic Send
                            if send_personalized_email(email, f"Business Audit: {lead['Name']}", pitch_text):
                                st.success(f"Email sent to {email}!")
                                st.info(f"Pitch Content: {pitch_text[:150]}...")
                        except Exception as ai_e:
                            st.error(f"Gemini Error: {ai_e}")
        st.divider()
