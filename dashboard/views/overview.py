"""
API Sentinel - Security Overview View
Exact Match to Reference Image
"""

import streamlit as st
from components.header import render_header
from components.kpi_cards import render_kpi_cards
from components.charts import render_analytics_section
from components.findings_table import render_recent_findings_table
from components.last_scan_card import render_last_scan_card

def render_overview():
    """Renders the exact layout matching the user's reference image."""
    # 1. Top Header Bar
    render_header(
        title="Security Overview",
        subtitle="Real-time view of your API security posture, findings, and scan activity."
    )

    # 2. Top 4 Distinct Glowing KPI Cards
    render_kpi_cards()

    st.markdown("<div style='height: 0.85rem;'></div>", unsafe_allow_html=True)

    # 3. Middle Analytics Section (Donut + Vertical Legend & 14-Day Line Activity)
    render_analytics_section()

    st.markdown("<div style='height: 0.85rem;'></div>", unsafe_allow_html=True)

    # 4. Bottom Grid (Recent Vulnerability Findings & Last Scan Summary)
    col_findings, col_summary = st.columns([1.75, 1])

    with col_findings:
        render_recent_findings_table()

    with col_summary:
        render_last_scan_card()
