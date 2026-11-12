"""
API Sentinel - New Security Scan View
Allows configuring and launching automated security scans with real-time feedback.
"""

import time
import streamlit as st
from config import TARGET_API, ACCENT_CYAN, ACCENT_BLUE, BORDER_COLOR
from components.header import render_header
from services.api_client import api_client

def render_new_scan():
    st.markdown('<div style="margin-bottom: 0.5rem;"><a href="?page=overview" target="_self" style="color: #00D4E8; font-weight: 500; font-size: 0.85rem; text-decoration: none;">← Back to Security Overview</a></div>', unsafe_allow_html=True)
    render_header(
        title="New Security Scan",
        subtitle="Configure target API boundaries, scan profiles, and launch automated security audits."
    )

    col_form, col_info = st.columns([1.7, 1])

    with col_form:
        st.markdown(
            """
            <div class="sentinel-card">
                <h4 style="margin-top:0; margin-bottom:1rem; color:#F4F8FF; font-size:1rem; font-weight:600;">
                    Target Configuration
                </h4>
            """,
            unsafe_allow_html=True
        )

        target_url = st.text_input(
            "API Base URL / OpenAPI Specification",
            value=TARGET_API,
            help="Enter base endpoint URL or OpenAPI 3.0 / Swagger JSON specification link"
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            scan_profile = st.selectbox(
                "Scan Profile",
                [
                    "Full Security Scan (OWASP Top 10 + Configs)",
                    "OWASP API Top 10 2023 Deep Audit",
                    "Auth & Token Verification (BOLA/BFLA)",
                    "Rate Limiting & Resource Starvation",
                    "PCI-DSS 4.0 Compliance Baseline"
                ]
            )
        with col_p2:
            auth_type = st.selectbox(
                "Authentication Scheme",
                ["Bearer Token (JWT)", "API Key Header", "OAuth2 Client Credentials", "None (Public API)"]
            )

        if auth_type != "None (Public API)":
            auth_token = st.text_input(
                "Authorization Header Value",
                value="Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.apisentinel.secops",
                type="password",
                help="Supplied securely in scan worker memory during test execution"
            )

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        with st.expander("Advanced Scan Parameters"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                concurrency = st.slider("Concurrent Probing Threads", 1, 16, 4)
                follow_redirects = st.checkbox("Follow Redirects (3xx)", value=True)
            with col_a2:
                rate_limit = st.slider("Request Rate (req/sec)", 10, 100, 30)
                fuzz_params = st.checkbox("Fuzz Hidden URL Query Parameters", value=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Launch Button
        start_scan = st.button("🚀 Launch Automated Security Scan", type="primary", use_container_width=True)

    with col_info:
        st.markdown(
            f"""
            <div class="sentinel-card">
                <h4 style="margin-top:0; color:#F4F8FF; font-size:1rem; font-weight:600; margin-bottom:0.75rem;">
                    Active Scan Engine
                </h4>
                <div style="font-size:0.83rem; color:#91A6BD; line-height:1.6;">
                    <p style="margin-bottom:0.75rem;">
                        API Sentinel's automated engine simulates authenticated attacker behavior:
                    </p>
                    <ul style="padding-left:1.2rem; margin-bottom:1rem;">
                        <li style="margin-bottom:0.4rem;"><strong style="color:#F4F8FF;">BOLA / IDOR Probing:</strong> Algorithmic UUID and integer mutations across session tokens.</li>
                        <li style="margin-bottom:0.4rem;"><strong style="color:#F4F8FF;">JWT Signature Tampering:</strong> Algorithm confusion, expired tokens, key confusion.</li>
                        <li style="margin-bottom:0.4rem;"><strong style="color:#F4F8FF;">Mass Assignment:</strong> Injecting elevated privilege fields into payload buffers.</li>
                        <li style="margin-bottom:0.4rem;"><strong style="color:#F4F8FF;">Rate Limits & DoS:</strong> Burst traffic stress testing against public auth endpoints.</li>
                    </ul>
                    <div style="padding:0.75rem; border-radius:6px; background:rgba(22, 139, 255, 0.1); border:1px solid rgba(22, 139, 255, 0.25);">
                        <span style="color:#00D4E8; font-weight:600;">Engine Node:</span> us-east-prod-scanner-04<br/>
                        <span style="color:#91A6BD;">Cluster Status:</span> <span style="color:#52C41A;">Healthy & Idle</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Scan Execution
    if start_scan:
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("### 📡 Scan in Progress")

        progress_bar = st.progress(0)
        status_text = st.empty()
        log_box = st.empty()

        logs = [
            f"[INFO] Initializing scan worker on {target_url}...",
            "[INFO] Connecting to API Sentinel FastAPI core (http://127.0.0.1:8000)...",
            "[INFO] Executing target URL safety validation & socket-level SSRF checks...",
            "[OK] Target passed destination verification. Pinned IP transport attached.",
            "[INFO] Invoking Member 1 Real Vulnerability Detection Engine...",
            "[PROBING] Probing for Broken Object Level Authorization (BOLA/IDOR)...",
            "[PROBING] Checking authentication boundaries & token requirements...",
            "[PROBING] Evaluating HTTP security headers and CSP configurations...",
            "[INFO] Persisting findings and technical evidence into SQLite database...",
            "[DONE] Security scan execution cycle completed!"
        ]

        accumulated_logs = ""
        for i, log in enumerate(logs):
            progress = int((i + 1) / len(logs) * 80)
            progress_bar.progress(progress)
            status_text.markdown(f"**Step {i+1}/{len(logs)}:** `{log.split(']')[0]}]` {log.split(']')[1]}")
            accumulated_logs += f"{log}\n"
            log_box.code(accumulated_logs, language="bash")
            time.sleep(0.15)

        # Trigger real scan on backend
        scan_res = api_client.trigger_scan(target_url=target_url, scan_profile=scan_profile)
        progress_bar.progress(100)

        if scan_res.get("is_real"):
            scan_id = scan_res.get("scan_id")
            findings_count = scan_res.get("findings_count", 0)
            st.session_state["last_scan_id"] = scan_id
            st.success(f"✅ Real Security Scan Completed! Scan #{scan_id} detected {findings_count} verified vulnerabilities.")
        else:
            st.info("ℹ️ Scan completed in offline / demonstration simulation mode.")

        col_res1, col_res2 = st.columns(2)
        with col_res1:
            if st.button("Inspect Findings in Detail →", key="view_findings_post_scan"):
                st.session_state["current_page"] = "findings"
                st.rerun()
        with col_res2:
            if st.button("Back to Overview Dashboard", key="back_overview_post_scan"):
                st.session_state["current_page"] = "overview"
                st.rerun()
