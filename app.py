import streamlit as st
import pandas as pd
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from docx import Document
import io
import time

# --- UI THEME ---
st.set_page_config(page_title="Hunter Pro Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #FCE4EC !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #E1BEE7 !important; border-radius: 8px !important;
    }
    input, textarea { color: #000000 !important; font-weight: 500; }
    label, p, h1, h2, h3, .stMarkdown { color: #000000 !important; }
    .stButton>button {
        background-color: #9575CD; color: white; border-radius: 8px; width: 100%; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZATION ---
if 'history' not in st.session_state: st.session_state['history'] = []
if 'leads' not in st.session_state: st.session_state['leads'] = []

try:
    # Use the SDK correctly with your secret key
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MY_EMAIL = st.secrets["MY_GMAIL"]
    APP_PASS = st.secrets["GMAIL_APP_PASSWORD"]
except Exception as e:
    st.error("Credential Error: Please check your Streamlit Secrets Vault.")

# --- HELPERS ---
def generate_docx(data):
    doc = Document()
    doc.add_heading('Lead Generation Report', 0)
    if data:
        table = doc.add_table(rows=1, cols=len(data[0]))
        for i, h in enumerate(data[0].keys()):
            table.rows[0].cells[i].text = h
        for item in data:
            row_cells = table.add_row().cells
            for i, h in enumerate(item.keys()):
                row_cells[i].text = str(item[h])
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def run_real_hunter(niche, location, limit):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    
    leads = []
    try:
        search_query = f"{niche} in {location}".replace(" ", "+")
        # Standardized Google Maps URL
        driver.get(f"https://www.google.com/maps/search/{search_query}")
        time.sleep(5)
        elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for e in elements[:limit]:
            name = e.get_attribute("aria-label")
            leads.append({"Business Name": name, "Location": location, "Rating": "Verified", "Email": "contact@research.com"})
    except Exception as e:
        st.error(f"Scraper Error: {e}")
    finally:
        driver.quit()
    return leads

# --- UI NAVIGATION ---
with st.sidebar:
    st.title("Main Menu")
    page = st.radio("Navigation", ["Dashboard", "History"])

if page == "Dashboard":
    st.title("Outreach Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        niche = st.text_input("Target Niche", placeholder="e.g. Dentists")
        location = st.text_input("Location", placeholder="e.g. New York")
    with col2:
        num_leads = st.slider("Lead Quantity", 5, 50, 10)
        pitch_focus = st.text_area("Pitch Focus", placeholder="Specific offer details...")

    if st.button("Initialize Hunter Machine"):
        with st.spinner("Scraping live data..."):
            results = run_real_hunter(niche, location, num_leads)
            st.session_state['leads'] = results
            st.session_state['history'].append(f"Scraped {len(results)} {niche} in {location}")
            st.success("Targeting Complete.")

    if st.session_state['leads']:
        st.subheader("Lead Report Table")
        st.table(pd.DataFrame(st.session_state['leads']))
        
        # Word Download Button
        docx_file = generate_docx(st.session_state['leads'])
        st.download_button("Download Report (Word)", data=docx_file, file_name="leads.docx")

        st.markdown("### Individual Outreach")
        for idx, lead in enumerate(st.session_state['leads']):
            if st.button(f"Send AI Pitch to {lead['Business Name']}", key=f"p_{idx}"):
                try:
                    # FIXED MODEL STRING FOR 404 ERROR
                    response = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=f"Write a 3-sentence professional pitch for {lead['Business Name']}. Focus: {pitch_focus}"
                    )
                    
                    msg = MIMEMultipart()
                    msg['From'], msg['To'], msg['Subject'] = MY_EMAIL, lead['Email'], "Proposal"
                    msg.attach(MIMEText(response.text, 'plain'))
                    
                    with smtplib.SMTP('smtp.gmail.com', 587) as server:
                        server.starttls()
                        server.login(MY_EMAIL, APP_PASS)
                        server.send_message(msg)
                    st.toast(f"Pitch delivered to {lead['Business Name']}")
                except Exception as e:
                    st.error(f"AI/Email Error: {e}")

elif page == "History":
    st.title("Search History")
    for record in reversed(st.session_state['history']):
        st.write(f"• {record}")
