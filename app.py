import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# This line pulls your keys SAFELY from the Streamlit "Vault"
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
MY_EMAIL = st.secrets["MY_GMAIL"]
APP_PASS = st.secrets["GMAIL_APP_PASSWORD"]

st.title("🎯 AI Lead Hunter & Pitcher")

# --- Step 1: The Hunter (Selenium) ---
if st.button("Find Leads"):
    # (Your existing Selenium code goes here)
    st.success("Found 5 leads!")
    st.session_state['leads'] = [{"name": "Sample Biz", "email": "test@example.com"}]

# --- Step 2: The Pitcher (AI + Gmail) ---
if 'leads' in st.session_state:
    for lead in st.session_state['leads']:
        if st.button(f"Pitch {lead['name']}"):
            # AI writes the email
            client = genai.Client(api_key=GEMINI_KEY)
            response = client.models.generate_content(model="gemini-2.0-flash", contents=f"Write a pitch for {lead['name']}")
            
            # Gmail sends it
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = MY_EMAIL, lead['email'], "Question"
            msg.attach(MIMEText(response.text, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(MY_EMAIL, APP_PASS)
            server.send_message(msg)
            server.quit()
            st.balloons()
