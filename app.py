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

# --- 1. UI THEME (Intact & Fixed) ---
st.set_page_config(page_title="Hunter Pro Dashboard", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div[data-baseweb="input"] > div { background-color: #E1BEE7 !important; border-radius: 8px !important; }
    .stButton>button { background-color: #9575CD; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    label, p, h1 { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MAILING ENGINE ---
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

# AI Client Initialization
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. DEEP AUDIT ENGINE (Gmaps Focus) ---
def deep_scrape_business(url, business_name):
    """Pinpoints ranking weaknesses for the audit pitch."""
    if not url or url == "N/A": return "No website found to audit."
    try:
        res = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        analysis = []
        if "schema.org/LocalBusiness" not in res.text: analysis.append("Missing Local SEO Schema")
        if "viewport" not in res.text.lower(): analysis.append("Not mobile-optimized")
        if res.elapsed.total_seconds() > 2.5: analysis.append("Slow site speed (ranking killer)")
        
        return f"Audit for {business_name}: " + (", ".join(analysis) if analysis else "Standard site.")
    except: return "Website unreachable for full audit."

# --- 4. STABLE STEALTH SCRAPER (Fixed Stale Errors) ---
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
        time.sleep(6) # Wait for DOM stability
        
        # Scroll to load requested amount
        try:
            feed = driver.find_element(By.XPATH, '//div[@role="feed"]')
            for _ in range(3):
                feed.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
        except: pass

        # INDEX-BASED LOOP: Prevents StaleElementReferenceException
        for i in range(limit):
            try:
                # Refresh elements list every iteration
                results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                if i >= len(results): break
                
                target = results[i]
                name = target.get_attribute("aria-label")
                
                # JS Click to bypass overlays
                driver.execute_script("arguments[0].scrollIntoView(true);", target)
                driver.execute_script("arguments[0].click();", target)
                time.sleep(2)
                
                try:
                    web_elem = driver.find_element(By.CSS_SELECTOR, "a[aria-label*='website']")
                    website = web_elem.get_attribute("href")
                except: website = "N/A"
                
                leads.append({"Name": name, "Website": website})
            except: continue
    finally:
        driver.quit()
    return leads

# --- 5. UI DASHBOARD ---
st.title("Outreach Dashboard & Automated Sender")

c1, c2 = st.columns(2)
with c1:
    n_in = st.text_input("Target Niche", value="cafes")
    l_in = st.text_input("Location", value="guwahati assam")
with c2:
    qty = st.slider("Lead Quantity", 5, 20, 10)
    service = st.text_input("Offering", "GMaps Ranking Optimization & 10% Demo Audit")

if st.button("Initialize Hunter Machine"):
    with st.spinner("Hunting leads in Stealth Mode..."):
        st.session_state['leads_list'] = run_stealth_hunter(n_in, l_in, qty)

if 'leads_list' in st.session_state:
    for idx, lead in enumerate(st.session_state['leads_list']):
        with st.container():
            col_a, col_b, col_c = st.columns([2, 2, 1])
            col_a.write(f"**{lead['Name']}**")
            col_b.write(lead['Website'])
            
            if col_c.button(f"Deep Audit & Send", key=f"btn_{idx}"):
                with st.spinner(f"Auditing {lead['Name']}..."):
                    # Step 1: Find Email
                    try:
                        res = requests.get(lead['Website'], timeout=5)
                        email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)[0]
                    except: email = None

                    if not email:
                        st.error("No email found. Check site manually.")
                    else:
                        # Step 2: Pain Point Analysis
                        audit_results = deep_scrape_business(lead['Website'], lead['Name'])
                        
                        # Step 3: AI Personalization
                        prompt = f"Write a professional cold email to {lead['Name']}. " \
                                 f"Tell them I found these ranking killers in an audit: {audit_results}. " \
                                 f"Offer: {service}. Mention I will provide 10% demo work for free."
                        
                        ai_pitch = client.models.generate_content(model="gemini-2.0-flash", contents=prompt).text
                        
                        # Step 4: Automate Send
                        if send_personalized_email(email, f"Audit for {lead['Name']}", ai_pitch):
                            st.success(f"Audit Sent to {email}!")
        st.divider()
