import streamlit as st
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- THEME & STYLING (White & Lavender) ---
st.set_page_config(page_title="Lead Hunter Pro", layout="wide")

st.markdown("""
    <style>
    /* Main background and text colors */
    .stApp {
        background-color: #FFFFFF;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F3E5F5; /* Light Lavender */
    }
    /* Primary Button styling */
    .stButton>button {
        background-color: #9575CD; /* Deep Lavender */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #7E57C2;
        border: none;
        color: white;
    }
    /* Input field styling */
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        border-radius: 8px;
        border: 1px solid #D1C4E9;
    }
    /* Headers */
    h1, h2, h3 {
        color: #4527A0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION ---
# Ensure these are in your Streamlit Secrets!
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MY_EMAIL = st.secrets["MY_GMAIL"]
    APP_PASS = st.secrets["GMAIL_APP_PASSWORD"]
except:
    st.error("Credentials missing in Secrets Vault.")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("⚙️ Lead Hunter")
    st.markdown("---")
    menu = st.radio("Navigation", ["Dashboard", "Campaign History", "Settings"])
    st.markdown("---")
    st.info("Status: System Active")

# --- MAIN INTERACTIVE UI ---
st.title("Outreach Dashboard")
st.write("Find and connect with local businesses using AI-driven research.")

# Interactive Search Bars
with st.container():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("🔍 **Targeting**")
        niche = st.text_input("Business Niche", placeholder="e.g. Luxury Spas")
        city = st.text_input("Location", placeholder="e.g. Beverly Hills, CA")
    
    with col2:
        st.write("📝 **Instructions**")
        pitch_details = st.text_area(
            "AI Pitch Focus", 
            placeholder="e.g. Focus on their Google Maps ranking. Offer a free 15-min audit.",
            height=110
        )

# Action Bar
st.markdown("---")
if st.button("Initialize Search", use_container_width=True):
    with st.spinner("Scanning Google Maps data..."):
        # Placeholder for your Selenium Hunter Logic
        st.session_state['leads'] = [
            {"name": "Elite Wellness", "email": "hello@elitewell.com", "rating": 3.9},
            {"name": "Glow Skin Clinic", "email": "contact@glowskin.com", "rating": 4.2}
        ]
        st.success(f"Successfully identified {len(st.session_state['leads'])} target prospects.")

# --- RESULTS TABLE ---
if 'leads' in st.session_state:
    st.subheader("Prospect Analysis")
    
    # Header Row
    head_col1, head_col2, head_col3 = st.columns([2, 1, 1])
    head_col1.write("**Business Name**")
    head_col2.write("**Rating**")
    head_col3.write("**Action**")
    
    for lead in st.session_state['leads']:
        with st.expander(f"📍 {lead['name']}"):
            c1, c2 = st.columns([3, 1])
            c1.write(f"The AI will generate a custom pitch based on the rating of **{lead['rating']}** stars.")
            
            if c2.button("✉️ Send Pitch", key=lead['name']):
                # AI Logic
                prompt = f"Write a professional email to {lead['name']} regarding their {lead['rating']} star rating. {pitch_details}"
                response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                
                # Email Logic
                msg = MIMEMultipart()
                msg['From'], msg['To'], msg['Subject'] = MY_EMAIL, lead['email'], "Business Growth Inquiry"
                msg.attach(MIMEText(response.text, 'plain'))
                
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(MY_EMAIL, APP_PASS)
                    server.send_message(msg)
                
                st.toast(f"Email delivered to {lead['name']}!")
