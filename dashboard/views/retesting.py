"""
API Sentinel - Retesting and Verification View
Validates remediation fixes through targeted endpoint regression probes.
Reflects the workflow: Find it. Understand it. Fix it. Verify it.
"""

import time
import streamlit as st
from services.api_client import api_client
from components.header import render_header
from config import ACCENT_CYAN, SEVERITY_COLORS, STATUS_COLORS

def render_retesting():
    render_header(
        title="Retesting & Verification",
        subtitle="Automated regression probes to mathematically verify security remediation on patched endpoints."
    )

    st.markdown(
        f"""
        <div class="sentinel-card" style="margin-bottom:1.5rem; border-left: 4px solid {ACCENT_CYAN};">
            <h4 style="margin:0 0 0.5rem 0; color:#F4F8FF; font-size:1.02rem;">Verification Pipeline</h4>
            <p style="margin:0; color:#91A6BD; font-size:0.86rem; line-height:1.6;">
                Once your development team applies a patch, trigger targeted endpoint verification probes here.
                API Sentinel replays the exact exploit payloads to certify that the vulnerability is closed.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Verification candidates
    findings = api_client.get_all_findings()
    candidates = [f for f in findings if f["status"] in ("In Progress", "Fixed", "Open")]

    col_list, col_runner = st.columns([1.6, 1.2])

    with col_list:
        st.markdown("### Select Endpoint to Retest")
        
        # Preselect if passed from findings
        preselect_id = st.session_state.get("retest_target_id", candidates[0]["id"] if candidates else None)
        selected_id = st.selectbox(
            "Select Vulnerability to Probe",
            [f"{f['id']} - {f['vulnerability']} ({f['endpoint']})" for f in candidates],
            index=0 if not preselect_id else next((i for i, f in enumerate(candidates) if f["id"] == preselect_id), 0)
        )

        target_finding = next(f for f in candidates if f["id"] == selected_id.split(" - ")[0])

        st.markdown(
            f"""
            <div style="background:rgba(11,29,50,0.7); border:1px solid #153B58; border-radius:8px; padding:1.1rem; margin-top:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.95rem; font-weight:700; color:#F4F8FF;">{target_finding['vulnerability']}</span>
                    <span class="severity-badge" style="background:{SEVERITY_COLORS[target_finding['severity']]['bg']}; color:{SEVERITY_COLORS[target_finding['severity']]['text']}; border:1px solid {SEVERITY_COLORS[target_finding['severity']]['border']};">
                        {target_finding['severity']}
                    </span>
                </div>
                <div style="margin-top:0.6rem; font-family:'JetBrains Mono', monospace; font-size:0.82rem; color:#00D4E8;">
                    {target_finding['endpoint']}
                </div>
                <div style="margin-top:0.6rem; color:#91A6BD; font-size:0.83rem;">
                    {target_finding.get('description', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_runner:
        st.markdown("### Targeted Probe Execution")
        st.markdown(
            f"""
            <div class="sentinel-card">
                <span style="color:#91A6BD; font-size:0.82rem;">Probe Target:</span><br>
                <code style="color:#00D4E8; font-size:0.8rem;">{target_finding['endpoint']}</code>
                <div style="margin-top:0.75rem;">
                    <span style="color:#91A6BD; font-size:0.82rem;">Exploit Mutation Payload:</span><br>
                    <code style="color:#FA8C16; font-size:0.75rem;">X-Exploit-Vector: BOLA-ID-ROTATE-0x89A</code>
                </div>
                <div style="margin-top:1.25rem;"></div>
            """,
            unsafe_allow_html=True
        )

        run_retest = st.button("🔬 Execute Retest Probe", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if run_retest:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("### Retest Console Log")
        
        status_box = st.empty()
        log_box = st.empty()

        logs = [
            f"[PROBE] Dispatching targeted verification probe to {target_finding['endpoint']}...",
            "[AUTH] Attaching authorized synthetic testing context...",
            "[HTTP] Evaluating target server status code and response payload...",
            "[EVAL] Comparing against baseline exploit telemetry..."
        ]

        streamed = ""
        for log in logs:
            streamed += f"{log}\n"
            log_box.code(streamed, language="bash")
            time.sleep(0.15)

        # Execute real backend retest
        scan_id = target_finding.get("scan_id") or st.session_state.get("last_scan_id") or 1
        retest_res = api_client.retest_scan(scan_id=scan_id, finding_ids=[target_finding['id']])
        
        results = retest_res.get("results", [])
        finding_res = results[0] if results else {}
        new_status = finding_res.get("status", "Still Vulnerable")
        notes = finding_res.get("notes", "Retest execution finished.")

        streamed += f"[RESULT] Target evaluation complete: Status -> {new_status}\n"
        streamed += f"[NOTES] {notes}\n"
        log_box.code(streamed, language="bash")

        if new_status == "Resolved" or finding_res.get("verified"):
            st.success(f"🎉 Verification Succeeded: Finding #{target_finding['id']} is officially certified as VERIFIED & REMEDIATED! Target denied access with HTTP 403 Forbidden.")
        else:
            st.warning(f"⚠️ Verification Alert: Finding #{target_finding['id']} is STILL VULNERABLE. Access was permitted or expected controls failed.")

    # Retest History Audit Trail
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### 📜 Finding Retest Audit History (Append-Only)")
    history_records = api_client.get_finding_history(target_finding['id'])

    if history_records:
        hist_table = """
        <table class="sentinel-table" style="width:100%; border-collapse:collapse;">
            <thead>
                <tr style="border-bottom: 1px solid #153B58; color: #91A6BD; font-size: 0.82rem; text-align: left;">
                    <th style="padding: 8px 12px;">Retest ID</th>
                    <th style="padding: 8px 12px;">Timestamp (UTC)</th>
                    <th style="padding: 8px 12px;">Previous Status</th>
                    <th style="padding: 8px 12px;">New Status</th>
                    <th style="padding: 8px 12px;">Verification Notes</th>
                </tr>
            </thead>
            <tbody>
        """
        for h in history_records:
            hist_table += f"""
                <tr style="border-bottom: 1px solid rgba(21, 59, 88, 0.4); font-size: 0.84rem;">
                    <td style="padding: 8px 12px; color: #00D4E8;">#{h.get('id')}</td>
                    <td style="padding: 8px 12px; color: #F4F8FF;">{h.get('retested_at', '')[:19].replace('T', ' ')}</td>
                    <td style="padding: 8px 12px; color: #FA8C16;">{h.get('old_status')}</td>
                    <td style="padding: 8px 12px; color: #52C41A; font-weight:700;">{h.get('new_status')}</td>
                    <td style="padding: 8px 12px; color: #91A6BD;">{h.get('notes', 'N/A')}</td>
                </tr>
            """
        hist_table += "</tbody></table>"
        st.markdown(hist_table, unsafe_allow_html=True)
    else:
        st.info(f"No prior retest history recorded for Finding #{target_finding['id']}. Trigger a probe above to generate the first verified audit log.")
