"""
API Sentinel - Scan History View
Historical log of the 24 security scans with status and export capabilities.
"""

import streamlit as st
from services.api_client import api_client
from components.header import render_header

def render_history():
    render_header(
        title="Scan History",
        subtitle="Complete audit trail of all 24 security scans, test runs, and regression probes."
    )

    history = api_client.get_scan_history()

    # Top Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="sentinel-card">
                <span class="kpi-title">Total Scans Performed</span>
                <div class="kpi-value">24</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div class="sentinel-card">
                <span class="kpi-title">Average Duration</span>
                <div class="kpi-value">2m 48s</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div class="sentinel-card">
                <span class="kpi-title">Clean Pass Rate</span>
                <div class="kpi-value">62.5%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Scans Table
    st.markdown('<div class="sentinel-card">', unsafe_allow_html=True)
    st.markdown("### Historical Scans")

    rows = ""
    for item in history:
        rows += f"""
        <tr>
            <td style="font-family:'JetBrains Mono', monospace; font-size:0.8rem; color:#00D4E8;">{item['id']}</td>
            <td style="font-family:'JetBrains Mono', monospace; font-size:0.8rem; color:#F4F8FF;">{item['target']}</td>
            <td>{item['scan_type']}</td>
            <td style="color:#91A6BD;">{item['timestamp']}</td>
            <td>{item['duration']}</td>
            <td>{item['endpoints']} eps</td>
            <td>
                <span style="color:#FF4D4F; font-weight:600;">{item['critical']}C</span> / 
                <span style="color:#FA8C16; font-weight:600;">{item['high']}H</span> / 
                <span style="color:#FADB14; font-weight:600;">{item['medium']}M</span>
            </td>
            <td>
                <span class="status-badge" style="background:rgba(82,196,26,0.12); color:#52C41A; border:1px solid rgba(82,196,26,0.3);">
                    {item['status']}
                </span>
            </td>
        </tr>
        """

    table_html = f"""
    <div class="table-container">
        <table class="sentinel-table">
            <thead>
                <tr>
                    <th>Scan ID</th>
                    <th>Target API</th>
                    <th>Scan Profile</th>
                    <th>Timestamp</th>
                    <th>Duration</th>
                    <th>Coverage</th>
                    <th>Findings</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
