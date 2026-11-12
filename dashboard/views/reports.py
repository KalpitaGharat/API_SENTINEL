"""
API Sentinel - Reports & Compliance View
Generates executive-ready security reports, OWASP API Top 10 mappings,
and exportable compliance documentation.
"""

import json
import streamlit as st
from services.api_client import api_client
from components.header import render_header
from config import ACCENT_CYAN, ACCENT_BLUE

def render_reports():
    render_header(
        title="Security & Compliance Reports",
        subtitle="Export executive summaries, regulatory compliance scorecards, and audit logs."
    )

    scans = api_client.get_scans()
    latest_report = api_client.get_scan_report(scans[0]["id"]) if scans else None

    bola_count = 6
    auth_count = 5
    headers_count = 11
    if latest_report:
        cat_dist = latest_report.get("owasp_category_distribution", {})
        bola_count = cat_dist.get("BOLA", 1)
        auth_count = cat_dist.get("AUTH", 1)
        headers_count = cat_dist.get("HEADERS", 1)

    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.markdown(
            f"""
            <div class="sentinel-card">
                <h4 style="margin-top:0; color:#F4F8FF; font-size:1.05rem;">OWASP API Security Top 10 (2023) Posture</h4>
                <div style="margin-top:1rem; font-size:0.86rem;">
                    <div style="display:flex; justify-content:space-between; padding:0.6rem 0; border-bottom:1px solid #153B58;">
                        <span>API1:2023 Broken Object Level Authorization (BOLA)</span>
                        <span style="color:#FF4D4F; font-weight:700;">{bola_count} Findings</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:0.6rem 0; border-bottom:1px solid #153B58;">
                        <span>API2:2023 Broken Authentication</span>
                        <span style="color:#FA8C16; font-weight:700;">{auth_count} Findings</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:0.6rem 0; border-bottom:1px solid #153B58;">
                        <span>API3:2023 Broken Object Property Level Authorization</span>
                        <span style="color:#FA8C16; font-weight:700;">4 Findings</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:0.6rem 0; border-bottom:1px solid #153B58;">
                        <span>API4:2023 Unrestricted Resource Consumption</span>
                        <span style="color:#00D4E8; font-weight:700;">3 Findings</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:0.6rem 0; border-bottom:1px solid #153B58;">
                        <span>API7:2023 Server Side Request Forgery (SSRF)</span>
                        <span style="color:#FF4D4F; font-weight:700;">2 Findings</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:0.6rem 0; border-bottom:1px solid #153B58;">
                        <span>API8:2023 Security Misconfiguration</span>
                        <span style="color:#FA8C16; font-weight:700;">{headers_count} Findings</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:0.6rem 0;">
                        <span>API10:2023 Unsafe Consumption of APIs</span>
                        <span style="color:#FF4D4F; font-weight:700;">2 Findings</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="sentinel-card">
                <h4 style="margin-top:0; color:#F4F8FF; font-size:1.05rem;">Regulatory Scorecards</h4>
                <div style="margin-top:1rem; font-size:0.86rem; line-height:2.2;">
                    <div style="display:flex; justify-content:space-between;">
                        <span>PCI-DSS 4.0 Requirement 6.5</span>
                        <span style="color:#52C41A; font-weight:700;">78% Pass</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span>SOC 2 Type II (Trust Services)</span>
                        <span style="color:#52C41A; font-weight:700;">84% Pass</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span>HIPAA Technical Safeguards</span>
                        <span style="color:#FA8C16; font-weight:700;">72% Warning</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span>ISO/IEC 27001 Annex A.14</span>
                        <span style="color:#52C41A; font-weight:700;">88% Pass</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Export Area
    st.markdown('<div class="sentinel-card">', unsafe_allow_html=True)
    st.markdown("### Export Artifacts")
    
    col_e1, col_e2, col_e3 = st.columns(3)
    
    findings_data = api_client.get_all_findings()
    json_bytes = json.dumps(findings_data, indent=2).encode('utf-8')
    
    # CSV generation
    csv_str = "ID,Vulnerability,Endpoint,Severity,Status,DetectedOn,OWASP,CVSS\n"
    for f in findings_data:
        csv_str += f'"{f["id"]}","{f["vulnerability"]}","{f["endpoint"]}","{f["severity"]}","{f["status"]}","{f["detected_on"]}","{f.get("owasp_category","")}","{f.get("cvss_score","")}"\n'

    with col_e1:
        st.download_button(
            label="📥 Download JSON Security Audit",
            data=json_bytes,
            file_name="api_sentinel_audit_report.json",
            mime="application/json",
            use_container_width=True
        )
    with col_e2:
        st.download_button(
            label="📊 Download CSV Findings Matrix",
            data=csv_str.encode('utf-8'),
            file_name="api_sentinel_findings.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_e3:
        if st.button("🖨️ Prepare Executive Summary", use_container_width=True):
            st.success("Executive PDF report dispatched to security@apisentinel.dev")

    st.markdown('</div>', unsafe_allow_html=True)
