"""
API Sentinel - Vulnerability Findings View
Detailed view of all 37 findings with filtering, CVSS breakdown,
and enterprise remediation guidance with code samples.
"""

import streamlit as st
from services.api_client import api_client
from components.header import render_header
from config import SEVERITY_COLORS, STATUS_COLORS

def render_findings():
    st.markdown('<div style="margin-bottom: 0.5rem;"><a href="?page=overview" target="_self" style="color: #00D4E8; font-weight: 500; font-size: 0.85rem; text-decoration: none;">← Back to Security Overview</a></div>', unsafe_allow_html=True)
    render_header(
        title="Vulnerability Findings",
        subtitle="Explore all detected security vulnerabilities, CVSS impact assessments, and remediation code."
    )

    all_findings = api_client.get_all_findings()

    # Filter Bar
    st.markdown('<div class="sentinel-card" style="padding: 1rem 1.25rem; margin-bottom: 1.25rem;">', unsafe_allow_html=True)
    col_search, col_sev, col_stat = st.columns([2, 1, 1])

    with col_search:
        search_query = st.text_input(
            "Search Findings",
            placeholder="Search by vulnerability name or endpoint (e.g. BOLA, /api/users)...",
            label_visibility="collapsed"
        )
    with col_sev:
        selected_sev = st.selectbox(
            "Filter by Severity",
            ["All Severities", "Critical", "High", "Medium", "Low"],
            label_visibility="collapsed"
        )
    with col_stat:
        selected_stat = st.selectbox(
            "Filter by Status",
            ["All Statuses", "Open", "In Progress", "Fixed", "Verified"],
            label_visibility="collapsed"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Filter logic
    filtered = all_findings
    if search_query:
        q = search_query.lower()
        filtered = [f for f in filtered if q in f["vulnerability"].lower() or q in f["endpoint"].lower()]
    if selected_sev != "All Severities":
        filtered = [f for f in filtered if f["severity"] == selected_sev]
    if selected_stat != "All Statuses":
        filtered = [f for f in filtered if f["status"] == selected_stat]

    # Metrics row for findings
    crit_count = sum(1 for f in filtered if f["severity"] == "Critical")
    high_count = sum(1 for f in filtered if f["severity"] == "High")
    med_count = sum(1 for f in filtered if f["severity"] == "Medium")
    low_count = sum(1 for f in filtered if f["severity"] == "Low")

    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1rem;">
            <div style="color:#91A6BD; font-size:0.9rem;">
                Showing <strong style="color:#F4F8FF;">{len(filtered)}</strong> of 37 Total Findings
            </div>
            <div style="display:flex; gap:0.6rem; font-size:0.8rem;">
                <span class="severity-badge" style="background:{SEVERITY_COLORS['Critical']['bg']}; color:{SEVERITY_COLORS['Critical']['text']}; border:1px solid {SEVERITY_COLORS['Critical']['border']};">
                    {crit_count} Critical
                </span>
                <span class="severity-badge" style="background:{SEVERITY_COLORS['High']['bg']}; color:{SEVERITY_COLORS['High']['text']}; border:1px solid {SEVERITY_COLORS['High']['border']};">
                    {high_count} High
                </span>
                <span class="severity-badge" style="background:{SEVERITY_COLORS['Medium']['bg']}; color:{SEVERITY_COLORS['Medium']['text']}; border:1px solid {SEVERITY_COLORS['Medium']['border']};">
                    {med_count} Medium
                </span>
                <span class="severity-badge" style="background:{SEVERITY_COLORS['Low']['bg']}; color:{SEVERITY_COLORS['Low']['text']}; border:1px solid {SEVERITY_COLORS['Low']['border']};">
                    {low_count} Low
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Prominent NVIDIA Nemotron AI Spotlight Callout
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.18) 0%, rgba(0, 212, 232, 0.12) 100%); border: 1.5px solid #8B5CF6; border-radius: 10px; padding: 14px 18px; margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 20px rgba(139, 92, 246, 0.25);">
            <div style="display:flex; align-items:center; gap: 14px;">
                <span style="font-size: 1.6rem;">✨</span>
                <div>
                    <div style="color: #FFFFFF; font-weight: 700; font-size: 0.98rem; letter-spacing: -0.01em;">
                        NVIDIA Nemotron AI Security Intelligence — Active Inside Every Finding
                    </div>
                    <div style="color: #A5B8CE; font-size: 0.83rem; margin-top: 2px;">
                        Click and expand any vulnerability below to view plain-English breakdowns, simulated attack vectors, and click <strong>✨ Explain with Nemotron AI</strong>.
                    </div>
                </div>
            </div>
            <div style="display:flex; gap: 6px;">
                <span style="background: rgba(139, 92, 246, 0.35); border: 1px solid #A78BFA; color: #E8F1FF; padding: 5px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 700;">
                    ⚡ NEMOTRON AI READY
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not filtered:
        st.info("No findings match the current filters.")
        return

    # Render each finding with expandable details (auto-expand first finding)
    for idx, item in enumerate(filtered):
        sev = item["severity"]
        sev_style = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["Low"])
        stat = item["status"]
        stat_style = STATUS_COLORS.get(stat, STATUS_COLORS["Open"])

        # Auto-expand first finding so AI panel is visible immediately upon page load
        with st.expander(f"[{item['id']}]  {sev.upper()}  —  {item['vulnerability']} ({item['endpoint']})   ✨ [AI Analysis Inside]", expanded=(idx == 0)):
            col_d1, col_d2 = st.columns([2, 1])

            with col_d1:
                st.markdown(f"**Description:** {item.get('description', 'N/A')}")
                st.markdown(f"**Remediation Guidance:** {item.get('remediation', 'N/A')}")
                
                # Technical HTTP Evidence Telemetry
                ev = item.get("evidence") or {}
                if ev and isinstance(ev, dict) and any(ev.values()):
                    with st.expander("🔍 Inspect Technical HTTP Telemetry (Evidence)", expanded=False):
                        if ev.get("sent_request"):
                            st.markdown("**Sent HTTP Request:**")
                            st.code(ev["sent_request"], language="http")
                        if ev.get("received_response"):
                            st.markdown("**Received Server Telemetry:**")
                            st.code(ev["received_response"], language="http")
                        if ev.get("expected_behavior"):
                            st.markdown(f"**Expected Secure Behavior:** {ev['expected_behavior']}")
                        if ev.get("evidence_notes"):
                            st.markdown(f"**Engine Notes:** `{ev['evidence_notes']}`")

                if "code_snippet" in item:
                    st.markdown("**Remediation Code (FastAPI / Python):**")
                    st.code(item["code_snippet"], language="python")

                # AI Nemotron Explain Section
                explain_key = f"ai_exp_{item['id']}"
                if explain_key in st.session_state:
                    ai_exp = st.session_state[explain_key]
                    st.markdown(
                        f"""
                        <div style="background: rgba(0, 212, 232, 0.08); border: 1px solid #00D4E8; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                                <span style="color:#00D4E8; font-weight:700; font-size:0.92rem;">✨ NVIDIA Nemotron AI Security Analysis</span>
                                <span style="color:#91A6BD; font-size:0.75rem;">Model: {ai_exp.get('model_name', 'nemotron-3.5')}</span>
                            </div>
                            <p style="color:#F4F8FF; font-size:0.86rem; line-height:1.6; margin-bottom:0.6rem;"><strong>Explanation:</strong> {ai_exp.get('explanation')}</p>
                            <p style="color:#FA8C16; font-size:0.86rem; line-height:1.6; margin-bottom:0.6rem;"><strong>Business Impact:</strong> {ai_exp.get('impact')}</p>
                            <p style="color:#52C41A; font-size:0.86rem; line-height:1.6; margin:0;"><strong>Remediation Strategy:</strong> {ai_exp.get('remediation')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    if st.button("✨ Explain with Nemotron AI", key=f"btn_ai_{item['id']}"):
                        with st.spinner("Invoking NVIDIA Nemotron explainability engine..."):
                            exp_res = api_client.explain_finding(item['id'])
                            st.session_state[explain_key] = exp_res
                            st.rerun()

            with col_d2:
                st.markdown(
                    f"""
                    <div style="background:rgba(7, 24, 43, 0.8); border:1px solid #153B58; border-radius:8px; padding:0.9rem; font-size:0.82rem; line-height:1.7;">
                        <div><strong style="color:#91A6BD;">OWASP Category:</strong><br><span style="color:#F4F8FF;">{item.get('owasp_category', 'API Security')}</span></div>
                        <div style="margin-top:0.5rem;"><strong style="color:#91A6BD;">CVSS v3.1 Score:</strong> <span style="color:{sev_style['text']}; font-weight:700;">{item.get('cvss_score', 'N/A')}</span></div>
                        <div style="margin-top:0.5rem;"><strong style="color:#91A6BD;">Status:</strong> 
                            <span class="status-badge" style="background:{stat_style['bg']}; color:{stat_style['text']}; border:1px solid {stat_style['border']};">
                                <span class="status-dot" style="background:{stat_style['dot']};"></span>
                                {stat}
                            </span>
                        </div>
                        <div style="margin-top:0.5rem;"><strong style="color:#91A6BD;">Detected On:</strong> <span style="color:#F4F8FF;">{item['detected_on']}</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Mark Fixed", key=f"fix_{item['id']}"):
                        st.success(f"{item['id']} marked as Fixed!")
                with col_btn2:
                    if st.button("Retest Now", key=f"retest_{item['id']}"):
                        st.session_state["current_page"] = "retesting"
                        st.session_state["retest_target_id"] = item['id']
                        st.rerun()
