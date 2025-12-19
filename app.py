import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth
import time
import random
import pandas as pd

st.set_page_config(page_title="GMaps Lead Hunter", layout="wide")

st.title("🎯 GMaps Lead Hunter")
st.write("Find 'Lacking' businesses to pitch your services.")

# Input Section
col1, col2 = st.columns(2)
with col1:
    niche = st.text_input("Niche (e.g. Plumbers)", "Dentists")
with col2:
    location = st.text_input("Location", "Miami, FL")

if st.button("Start Hunting"):
    # Browser Setup
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", fix_hairline=True)
    
    with st.spinner("Searching Google Maps..."):
        search_query = f"{niche} in {location}"
        driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}")
        time.sleep(random.uniform(5, 7)) # Allow results to load
        
        leads = []
        # Finding business elements (Selectors can change in 2025, but 'qBF1Pd' is common for titles)
        business_elements = driver.find_elements(By.CLASS_NAME, "qBF1Pd")
        
        for el in business_elements[:10]: # Limit to 10 for speed
            name = el.text
            if name:
                leads.append({"Business Name": name})
        
        driver.quit()
        
    if leads:
        df = pd.DataFrame(leads)
        st.success(f"Found {len(leads)} potential leads!")
        st.table(df)
        st.session_state['leads'] = leads
    else:
        st.error("No leads found. Google might be blocking the request—try again in a few minutes.")
