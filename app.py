import streamlit as st
import pandas as pd
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- THEME & UI STYLING ---
st.set_page_config(page_title="Hunter Pro Dashboard", layout="wide")

st.markdown("""
    <style>
    /* Main Background White */
    .stApp { background-color: #FFFFFF; }
    
    /* Sidebar Light Pink with Black Text */
    [data-testid="stSidebar"] { 
        background-color: #FCE4EC !important; 
        color: #000000 !important;
    }
    
    /* Input Boxes: Lavender BG, Black Text, White Typing */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #E1BEE7 !important;
        border-radius: 8px !important;
    }
    input, textarea { 
        color: #000000 !important; 
        font-weight: 500;
    }
    input:focus, textarea:focus { 
        color: #FFFFFF !important; 
    }

    /* All Labels and Headers forced to Black */
    label, p, h1, h2, h3, .stMarkdown { 
        color: #000000 !important; 
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    /* Professional Buttons */
    .stButton>button {
        background-color: #9575CD; color: white;
        border-radius: 8px; border: none; padding: 12px;
        width: 100%;
    }
    .stButton>button:hover { background-color: #7E57C2; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZE SYSTEM ---
if 'history' not in st.session_state: st.session_state['history'] = []
if 'leads' not in st.session_state: st.session_state['leads'] = []

try:
    # Initializing with modern SDK
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MY_EMAIL = st.secrets["MY_GMAIL"]
    APP_PASS = st.secrets["GMAIL_APP_PASSWORD"]
except:
    st.error("Setup Error: Please verify your API keys in Streamlit Secrets.")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("Main Menu")
    page = st.radio("Navigation", ["Dashboard", "History"])
    st.markdown("---")
    st.write("System Status: Active")

# --- DASHBOARD PAGE ---
if page == "Dashboard":
    st.title("Outreach Dashboard")
    
    # User Control Inputs
    col1, col2 = st.columns(2)
    with col1:
        niche = st.text_input("Target Niche", placeholder="Type business type...")
        location = st.text_input("Location", placeholder="Type city/country...")
    with col2:
        num_leads = st.slider("Lead Quantity", 5, 50, 10)
        pitch_focus = st.text_area("Pitch Instructions", placeholder="Describe your offer details...")

    if st.button("Initialize Hunter Machine"):
        with st.spinner(f"Fetching {num_leads} leads for {niche}..."):
            # Simulation of Selenium Hunter using your dynamic inputs
            leads_data = []
            for i in range(num_leads):
                leads_data.append({
                    "Business Name": f"{niche} Specialist {i+1}",
                    "Location": location,
                    "Rating": round(3.5 + (i * 0.1), 1),
                    "Email": f"contact{i}@example.com"
                })
            st.session_state['leads'] = leads_data
            # Save to History
            st.session_state['history'].append(f"Found {num_leads} {niche} in {location}")
            st.success("Targeting Complete.")

    # --- PROFESSIONAL LEAD REPORT TABLE ---
    if st.session_state['leads']:
        st.subheader("Lead Report Table")
        df = pd.DataFrame(st.session_state['leads'])
        st.table(df) # Structured ordered display

        # Action Buttons for each lead
        st.markdown("### Individual Outreach")
        for idx, lead in enumerate(st.session_state['leads']):
            with st.expander(f"Action: {lead['Business Name']}"):
                if st.button(f"Send AI Pitch to {lead['Business Name']}", key=f"pitch_{idx}"):
                    try:
                        # FIXED: Using stable model identifier to prevent 404
                        # Removed "models/" prefix as required by new SDK
                        response = client.models.generate_content(
                            model="gemini-2.0-flash-001", 
                            contents=f"Write a 4-sentence pitch for {lead['Business Name']}. Use these details: {pitch_focus}"
                        )
                        
                        # Gmail Logic
                        msg = MIMEMultipart()
                        msg['From'], msg['To'], msg['Subject'] = MY_EMAIL, lead['Email'], "Growth Opportunity"
                        msg.attach(MIMEText(response.text, 'plain'))
                        
                        with smtplib.SMTP('smtp.gmail.com', 587) as server:
                            server.starttls()
                            server.login(MY_EMAIL, APP_PASS)
                            server.send_message(msg)
                        
                        st.toast(f"Successfully pitched {lead['Business Name']}")
                    except Exception as e:
                        st.error(f"Logic Error: {e}")

# --- HISTORY PAGE ---
elif page == "History":
    st.title("Past Activity")
    if st.session_state['history']:
        for record in reversed(st.session_state['history']):
            st.write(f"• {record}")
    else:
        st.info("No records found.")
