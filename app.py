import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# --- SECURE KEYS ---
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
MY_EMAIL = st.secrets["MY_GMAIL"]
APP_PASS = st.secrets["GMAIL_APP_PASSWORD"]

st.set_page_config(page_title="AI Lead Hunter", layout="wide")
st.title("🎯 AI Lead Hunter & Pitcher")

# --- UI INPUTS ---
col1, col2 = st.columns(2)
niche = col1.text_input("Niche", "Dentists")
city = col2.text_input("City", "Miami, FL")

if st.button("Step 1: Hunt Leads"):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    
    # Hunter Logic (Selenium)
    with st.spinner("Scraping Google Maps..."):
        driver.get(f"https://www.google.com/maps/search/{niche}+in+{city}")
        time.sleep(5)
        # We find titles and emails (Note: Selenium can grab titles; usually needs a website click for emails)
        leads = [{"name": "Smile Dental", "rating": 3.5, "email": "contact@smiledental.com"}] # Sample result
        st.session_state['leads'] = leads
        st.table(leads)
    driver.quit()

# --- AI & EMAIL LOGIC ---
if 'leads' in st.session_state:
    st.subheader("Step 2: AI Pitching")
    for lead in st.session_state['leads']:
        if st.button(f"Draft & Send Pitch to {lead['name']}"):
            # Brain (Gemini AI)
            client = genai.Client(api_key=GEMINI_KEY)
            prompt = f"Write a 2-sentence sales email to {lead['name']}. Offer to fix their {lead['rating']} star rating."
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            pitch = response.text
            
            # Voice (Gmail)
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = MY_EMAIL, lead['email'], "Quick Question"
            msg.attach(MIMEText(pitch, 'plain'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(MY_EMAIL, APP_PASS)
            server.send_message(msg)
            server.quit()
            st.success(f"Sent to {lead['name']}!")
