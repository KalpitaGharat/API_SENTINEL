"""
API SENTINEL — Premium Dark Cybersecurity Dashboard
API Security Testing & Remediation Platform

Senior Enterprise UI/UX Implementation in Streamlit & Plotly
"""

import streamlit as st
import sys
import os

# Ensure project root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from styles import get_custom_css
from components.sidebar import render_sidebar
from views.overview import render_overview
from views.onboarding import render_onboarding
from views.new_scan import render_new_scan
from views.findings import render_findings
from views.api_keys import render_api_keys
from views.retesting import render_retesting
from views.history import render_history
from views.reports import render_reports

# Page Configuration
st.set_page_config(
    page_title="API Sentinel — Enterprise Security Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Cyber SaaS Styling
st.markdown(get_custom_css(), unsafe_allow_html=True)

def main():
    # Render Fixed Sidebar Navigation & Particles
    current_page = render_sidebar()

    # Route Views
    if current_page == "overview":
        render_overview()
    elif current_page == "onboarding":
        render_onboarding()
    elif current_page == "new_scan":
        render_new_scan()
    elif current_page == "findings":
        render_findings()
    elif current_page == "api_keys":
        render_api_keys()
    elif current_page == "retesting":
        render_retesting()
    elif current_page == "history":
        render_history()
    elif current_page == "reports":
        render_reports()
    else:
        render_overview()

if __name__ == "__main__":
    main()
