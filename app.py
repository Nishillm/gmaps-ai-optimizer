import streamlit as st
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- THEME & STYLING (White, Lavender, Light Pink) ---
st.set_page_config(page_title="Lead Hunter Pro", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #FFFFFF; }
    
    /* Sidebar Styling (Light Pink) */
    [data-testid="stSidebar"] {
        background-color: #FCE4EC !important;
        color: #000000 !important;
    }
    
    /* Input Boxes (Lavender Background, Black Text, White Typing) */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #E1BEE7 !important; /* Lavender */
        border-radius: 4px !important;
    }
    input, textarea {
        color: #000000 !important; /* Text inside box is black */
    }
    /* Change text to white ONLY when typing/active to ensure visibility as requested */
    input:focus, textarea:focus {
        color: #FFFFFF !important; 
    }

    /* Labels and Headers (Professional Black) */
    label, p, h1, h2, h3 { color: #000000 !important; font-family: 'Arial', sans-serif; }

    /* Buttons */
    .stButton>button {
        background-color: #9575CD; color: white;
        border-radius: 4px; border: none; padding: 0.5rem 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION ---
try:
    # Probable Fix: Ensure model name is 'gemini-1.5-flash' if 2.0-flash triggers ClientError
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MY_EMAIL = st.secrets["MY_GMAIL"]
    APP_PASS = st.secrets["GMAIL_APP_PASSWORD"]
except Exception as e:
    st.error("Missing Credentials. Please check your Streamlit Secrets.")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Menu")
    st.write("Settings")
    st.write("History")

# --- MAIN INTERACTIVE UI ---
st.title("Outreach Dashboard")

col1, col2 = st.columns(2)
with col1:
    niche = st.text_input("Target Niche", placeholder="e.g. Dentists")
    location = st.text_input("Location", placeholder="e.g. London")

with col2:
    pitch_focus = st.text_area("Pitch Focus", placeholder="Mention their reviews...", height=100)

if st.button("Generate Leads", use_container_width=True):
    # Simulated lead for testing
    st.session_state['leads'] = [{"name": "Smile Clinic", "email": "info@example.com", "rating": 4.2}]
    st.success("Analysis complete.")

# --- RESULTS ---
if 'leads' in st.session_state:
    for lead in st.session_state['leads']:
        with st.container():
            st.markdown(f"**Lead:** {lead['name']} | **Rating:** {lead['rating']}")
            if st.button(f"Send Pitch to {lead['name']}"):
                try:
                    # FIX: Using 'gemini-1.5-flash' is often safer if 2.0-flash-exp fails
                    response = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=f"Write a 3-sentence pitch for {lead['name']}. Focus: {pitch_focus}"
                    )
                    
                    msg = MIMEMultipart()
                    msg['From'], msg['To'], msg['Subject'] = MY_EMAIL, lead['email'], "Improvement Opportunity"
                    msg.attach(MIMEText(response.text, 'plain'))
                    
                    with smtplib.SMTP('smtp.gmail.com', 587) as server:
                        server.starttls()
                        server.login(MY_EMAIL, APP_PASS)
                        server.send_message(msg)
                    st.toast("Pitch sent successfully.")
                except Exception as e:
                    st.error(f"Error: {e}")
