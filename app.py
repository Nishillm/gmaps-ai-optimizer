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

# --- 1. UI THEME ---
st.set_page_config(page_title="Hunter Pro Dashboard", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div[data-baseweb="input"] > div { background-color: #E1BEE7 !important; border-radius: 8px !important; }
    .stButton>button { background-color: #9575CD; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .send-btn { background-color: #4CAF50 !important; }
    label, p, h1 { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE ENGINES (Mailing & AI) ---
def send_personalized_email(target_email, subject, body):
    """Automates the actual email sending via Gmail SMTP."""
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

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. THE DEEP SCRAPER (Pain-Point Finder) ---
def deep_scrape_business(url):
    """Scrapes more info to find business weaknesses (slow site, no social, etc)."""
    if not url or url == "N/A": return "No website to analyze."
    try:
        start_time = time.time()
        res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        load_time = time.time() - start_time
        
        analysis = []
        if load_time > 3: analysis.append("Slow website loading speed")
        if "instagram.com" not in res.text.lower(): analysis.append("No Instagram link found")
        if "facebook.com" not in res.text.lower(): analysis.append("No Facebook link found")
        if "viewport" not in res.text.lower(): analysis.append("Not mobile-optimized")
        
        return ", ".join(analysis) if analysis else "Standard business presence."
    except: return "Could not reach website for analysis."

def run_stealth_hunter(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    
    leads = []
    try:
        query = f"{niche} in {location}".replace(" ", "+")
        driver.get(f"https://www.google.com/maps/search/{query}")
        time.sleep(5)
        
        # Improved Feed Selector for December 2025 Layout
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for e in results[:limit]:
            name = e.get_attribute("aria-label")
            driver.execute_script("arguments[0].click();", e)
            time.sleep(2)
            try:
                web_elem = driver.find_element(By.CSS_SELECTOR, "a[aria-label*='website']")
                website = web_elem.get_attribute("href")
            except: website = "N/A"
            
            leads.append({"Name": name, "Website": website})
    finally:
        driver.quit()
    return leads

# --- 4. UI DASHBOARD ---
st.title("Outreach Dashboard & Automated Sender")

c1, c2 = st.columns(2)
with c1:
    niche = st.text_input("Target Niche", value="cafes")
    loc = st.text_input("Location", value="guwahati assam")
with c2:
    qty = st.slider("Lead Quantity", 5, 20, 10)
    service = st.text_input("What are you selling?", "Social Media Marketing")

if st.button("Initialize Hunter Machine"):
    with st.spinner("Hunting leads..."):
        data = run_stealth_hunter(niche, loc, qty)
        st.session_state['leads_list'] = data

if 'leads_list' in st.session_state:
    for idx, lead in enumerate(st.session_state['leads_list']):
        with st.container():
            col_a, col_b, col_c = st.columns([2, 2, 1])
            col_a.write(f"**{lead['Name']}**")
            col_b.write(lead['Website'])
            
            # Action Button per Lead
            if col_c.button(f"Deep Scrape & Send", key=f"btn_{idx}"):
                with st.spinner(f"Analyzing {lead['Name']}..."):
                    # Step 1: Find Email
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    try:
                        res = requests.get(lead['Website'], timeout=5)
                        found_emails = re.findall(email_pattern, res.text)
                        target_mail = found_emails[0] if found_emails else None
                    except: target_mail = None

                    if not target_mail:
                        st.error(f"No email found for {lead['Name']}. Cannot send.")
                    else:
                        # Step 2: Identify Pain Points
                        pain_points = deep_scrape_business(lead['Website'])
                        
                        # Step 3: AI Generation based on analyzed info
                        prompt = f"Write a highly personalized short cold email to {lead['Name']}. " \
                                 f"I found these issues on their site: {pain_points}. " \
                                 f"Offer my service: {service}. Be professional and helpful."
                        
                        ai_res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                        pitch = ai_res.text
                        
                        # Step 4: Send the Email
                        success = send_personalized_email(target_mail, f"Quick question regarding {lead['Name']}", pitch)
                        if success:
                            st.success(f"Email sent to {target_mail}!")
                        else:
                            st.error("Email failed to send.")
        st.divider()
