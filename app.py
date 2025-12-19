import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

st.set_page_config(page_title="System Check", page_icon="🚀")

st.title("🚀 Hunter System Check")
st.write("Verifying if your Cloud Browser is ready for scraping...")

# Configuration for Streamlit Cloud
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

try:
    driver = webdriver.Chrome(options=options)
    
    # Apply Stealth
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    driver.get("https://www.google.com")
    st.success(f"✅ SUCCESS! Hunter is online. Browser Title: {driver.title}")
    driver.quit()
except Exception as e:
    st.error(f"❌ ERROR: Browser failed to launch. {e}")
