"""
API Sentinel - Streamlit API Onboarding & OpenAPI Discovery View
Queries FastAPI backend targets endpoints as single source of truth.
Features Target Registration, OpenAPI Spec Import, Endpoint Discovery,
Dual-Principal BOLA Setup, and Targeted Scan Launchpad.
"""

import streamlit as st
import requests
import json
from config import BACKEND_BASE_URL, ACCENT_CYAN, TEXT_MUTED

TARGETS_API_BASE = f"{BACKEND_BASE_URL}/api/targets"
DEMO_API_URL = "http://127.0.0.1:8001"
DEMO_SPEC_URL = "http://127.0.0.1:8001/openapi.json"

METHOD_BADGES = {
    "GET": "background: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.4);",
    "POST": "background: rgba(34, 197, 94, 0.2); color: #4ADE80; border: 1px solid rgba(34, 197, 94, 0.4);",
    "PUT": "background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4);",
    "PATCH": "background: rgba(168, 85, 247, 0.2); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.4);",
    "DELETE": "background: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4);",
}

def render_onboarding():
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="color: #E8F1FF; font-size: 1.8rem; font-weight: 800; margin: 0 0 6px 0;">
                API Onboarding &amp; OpenAPI Discovery
            </h1>
            <p style="color: {TEXT_MUTED}; font-size: 0.92rem; margin: 0;">
                Register target APIs, import OpenAPI/Swagger specifications, discover sensitive IDOR endpoints, and configure dual-principal authorization testing.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch targets from backend
    try:
        targets_res = requests.get(f"{TARGETS_API_BASE}?limit=50", timeout=5).json()
        targets = targets_res.get("items", [])
    except Exception as e:
        st.error(f"Failed to connect to FastAPI backend on {BACKEND_BASE_URL}: {e}")
        return

    # Calculate overall stats
    total_targets = len(targets)
    total_endpoints = sum(t.get("endpoint_count", 0) for t in targets)
    total_sensitive = sum(t.get("sensitive_endpoint_count", 0) for t in targets)

    # KPI Metrics Row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div style="background: #07182B; border: 1px solid rgba(0, 200, 255, 0.15); border-radius: 10px; padding: 14px 18px;">
                <div style="color: {TEXT_MUTED}; font-size: 0.78rem;">REGISTERED TARGETS</div>
                <div style="color: #F8FAFC; font-size: 1.6rem; font-weight: 800; margin-top: 4px;">{total_targets}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div style="background: #07182B; border: 1px solid rgba(0, 200, 255, 0.15); border-radius: 10px; padding: 14px 18px;">
                <div style="color: {TEXT_MUTED}; font-size: 0.78rem;">DISCOVERED OPERATIONS</div>
                <div style="color: #38BDF8; font-size: 1.6rem; font-weight: 800; margin-top: 4px;">{total_endpoints}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div style="background: #07182B; border: 1px solid rgba(0, 200, 255, 0.15); border-radius: 10px; padding: 14px 18px;">
                <div style="color: {TEXT_MUTED}; font-size: 0.78rem;">SENSITIVE IDOR CANDIDATES</div>
                <div style="color: #FBBF24; font-size: 1.6rem; font-weight: 800; margin-top: 4px;">{total_sensitive}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Tabs for Workflow
    tab_list, tab_add, tab_discovery, tab_auth, tab_scan = st.tabs([
        "1. Target Catalog",
        "2. Register API / Spec",
        "3. Endpoints & Discovery",
        "4. Authentication (BOLA)",
        "5. Launch Targeted Scan"
    ])

    # ---------------------------------------------------------
    # TAB 1: CATALOG
    # ---------------------------------------------------------
    with tab_list:
        if not targets:
            st.info("No API targets registered yet. Click 'Register API / Spec' or load the Healthcare Demo API below.")
            if st.button("🚀 1-Click Load Healthcare Demo API", key="load_demo_empty"):
                _load_demo_api()
        else:
            for t in targets:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: #07182B; border: 1px solid rgba(0, 200, 255, 0.15); border-radius: 10px; padding: 16px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="color: #F1F5F9; font-size: 1.1rem; font-weight: 700;">{t.get('name')}</span>
                                    <span style="margin-left: 10px; background: rgba(25, 211, 255, 0.15); color: {ACCENT_CYAN}; font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; font-family: monospace;">{t.get('environment')}</span>
                                </div>
                                <span style="color: #60A5FA; font-family: monospace; font-size: 0.85rem;">{t.get('base_url')}</span>
                            </div>
                            <div style="color: {TEXT_MUTED}; font-size: 0.82rem; margin-top: 6px;">
                                {t.get('description') or 'No description provided.'}
                            </div>
                            <div style="display: flex; gap: 20px; margin-top: 10px; font-size: 0.8rem; color: #8AA4C8;">
                                <span>Operations: <strong style="color: #F1F5F9;">{t.get('endpoint_count', 0)}</strong></span>
                                <span>Selected: <strong style="color: #38BDF8;">{t.get('selected_endpoint_count', 0)}</strong></span>
                                <span>Sensitive IDOR: <strong style="color: #FBBF24;">{t.get('sensitive_endpoint_count', 0)}</strong></span>
                                <span>Spec Version: <strong style="color: #A78BFA;">{t.get('specification_version') or 'None'}</strong></span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # ---------------------------------------------------------
    # TAB 2: REGISTER API / SPEC
    # ---------------------------------------------------------
    with tab_add:
        st.subheader("Register Target API & Import OpenAPI Specification")

        # 1-Click Demo Shortcut
        st.markdown(
            """
            <div style="background: rgba(25, 211, 255, 0.08); border: 1px solid rgba(25, 211, 255, 0.25); border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
                <span style="color: #19D3FF; font-weight: 600;">Fast Track:</span>
                <span style="color: #8AA4C8; font-size: 0.85rem; margin-left: 6px;">
                    Test against the local Healthcare Demo API (vulnerable to BOLA/IDOR on port 8001).
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("⚡ 1-Click Load Healthcare Demo API", key="load_demo_btn"):
            _load_demo_api()

        st.divider()

        with st.form("new_target_form"):
            name = st.text_input("API Name", placeholder="e.g. Core Banking Service")
            base_url = st.text_input("Base URL", placeholder="https://api.example.com or http://127.0.0.1:8001")
            environment = st.selectbox("Environment", ["development", "staging", "production", "testing"])
            description = st.text_area("Description (Optional)", placeholder="API purpose and testing boundary context...")
            
            st.markdown("##### OpenAPI / Swagger Specification")
            spec_file = st.file_uploader("Upload OpenAPI Spec (.json or .yaml)", type=["json", "yaml", "yml"])
            spec_url = st.text_input("Or Remote Spec URL", placeholder="http://127.0.0.1:8001/openapi.json")

            submitted = st.form_submit_button("Register Target & Discover Endpoints")
            if submitted:
                if not name or not base_url:
                    st.error("API Name and Base URL are required.")
                else:
                    try:
                        create_res = requests.post(TARGETS_API_BASE, json={
                            "name": name,
                            "base_url": base_url,
                            "environment": environment,
                            "description": description or None,
                            "api_type": "REST"
                        }, timeout=5)
                        if create_res.status_code == 201:
                            target_data = create_res.json()
                            target_id = target_data["id"]
                            st.success(f"Target '{name}' registered successfully!")

                            # Handle spec import if provided
                            if spec_file:
                                spec_bytes = spec_file.read()
                                spec_text = spec_bytes.decode("utf-8")
                                imp_res = requests.post(f"{TARGETS_API_BASE}/{target_id}/import-spec", json={"spec_content": spec_text}, timeout=10)
                                if imp_res.status_code == 200:
                                    st.success(f"Imported specification with {imp_res.json().get('discovered_endpoints', 0)} endpoints!")
                            elif spec_url:
                                imp_res = requests.post(f"{TARGETS_API_BASE}/{target_id}/import-spec", json={"spec_url": spec_url}, timeout=10)
                                if imp_res.status_code == 200:
                                    st.success(f"Imported specification from URL!")
                            
                            st.rerun()
                        else:
                            st.error(f"Failed to create target: {create_res.text}")
                    except Exception as ex:
                        st.error(f"Request error: {ex}")

    # ---------------------------------------------------------
    # TAB 3: DISCOVERY & ENDPOINTS
    # ---------------------------------------------------------
    with tab_discovery:
        if not targets:
            st.warning("Please register a target API first.")
        else:
            target_names = {t["id"]: f"{t['name']} ({t['base_url']})" for t in targets}
            selected_target_id = st.selectbox(
                "Select API Target to Explore",
                options=list(target_names.keys()),
                format_func=lambda x: target_names[x],
                key="discovery_target_select"
            )

            # Filter row
            f1, f2, f3 = st.columns([1, 1, 2])
            with f1:
                method_choice = st.selectbox("HTTP Method", ["ALL", "GET", "POST", "PUT", "PATCH", "DELETE"])
            with f2:
                sens_choice = st.checkbox("Sensitive Candidates Only", value=False)
            with f3:
                search_term = st.text_input("Search Path / Operation", placeholder="e.g. /patients")

            # Fetch endpoints
            try:
                params = {"limit": 200}
                if method_choice != "ALL":
                    params["method"] = method_choice
                if sens_choice:
                    params["sensitive_only"] = True
                if search_term:
                    params["search"] = search_term

                ep_res = requests.get(f"{TARGETS_API_BASE}/{selected_target_id}/endpoints", params=params, timeout=5).json()
                endpoints_list = ep_res.get("items", [])

                # Bulk actions
                b1, b2, b3 = st.columns([1, 1, 2])
                with b1:
                    if st.button("Select All"):
                        requests.post(f"{TARGETS_API_BASE}/{selected_target_id}/endpoints/select", json={"select_all": True}, timeout=5)
                        st.rerun()
                with b2:
                    if st.button("Select Sensitive Only"):
                        requests.post(f"{TARGETS_API_BASE}/{selected_target_id}/endpoints/select", json={"sensitive_only": True}, timeout=5)
                        st.rerun()
                with b3:
                    if st.button("Deselect All"):
                        requests.post(f"{TARGETS_API_BASE}/{selected_target_id}/endpoints/select", json={"deselect_all": True}, timeout=5)
                        st.rerun()

                st.markdown(f"**Discovered Operations ({len(endpoints_list)}):**")
                for ep in endpoints_list:
                    m_badge = METHOD_BADGES.get(ep['method'], "background: #334155; color: #FFF;")
                    sens_badge = "<span style='background: rgba(245, 158, 11, 0.2); color: #FBBF24; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; margin-left: 8px;'>⚠️ SENSITIVE IDOR</span>" if ep.get("is_sensitive_candidate") else ""
                    sel_icon = "✅" if ep.get("is_selected") else "⬜"

                    st.markdown(
                        f"""
                        <div style="background: #07182B; border: 1px solid rgba(0, 200, 255, 0.1); border-radius: 6px; padding: 10px 14px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>{sel_icon}</span>
                                <span style="{m_badge} padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 0.75rem;">{ep['method']}</span>
                                <span style="font-family: monospace; font-size: 0.85rem; color: #F1F5F9;">{ep['path']}</span>
                                {sens_badge}
                            </div>
                            <span style="color: #6482A6; font-size: 0.75rem;">{ep.get('summary') or ''}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            except Exception as e:
                st.error(f"Failed to fetch endpoints: {e}")

    # ---------------------------------------------------------
    # TAB 4: AUTHENTICATION (BOLA)
    # ---------------------------------------------------------
    with tab_auth:
        if not targets:
            st.warning("Please register a target API first.")
        else:
            target_names = {t["id"]: f"{t['name']} ({t['base_url']})" for t in targets}
            auth_target_id = st.selectbox(
                "Select API Target",
                options=list(target_names.keys()),
                format_func=lambda x: target_names[x],
                key="auth_target_select"
            )

            st.markdown(
                f"""
                <div style="background: #07182B; border: 1px solid rgba(0, 200, 255, 0.15); border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                    <div style="color: #F8FAFC; font-weight: 600; font-size: 0.95rem;">Dual-Principal Authorization Probing</div>
                    <div style="color: {TEXT_MUTED}; font-size: 0.82rem; margin-top: 4px;">
                        Configure two distinct user profiles. Member 1's detection engine checks whether User B (Probe) can access User A's private resources.
                        Credentials are stored with Fernet authenticated symmetric encryption.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### User A (Resource Owner)")
                with st.form("auth_a_form"):
                    type_a = st.selectbox("Auth Type", ["bearer", "api_key", "basic", "none"], key="type_a")
                    tok_a = st.text_input("Secret / Token", type="password", key="tok_a")
                    user_a = st.text_input("Username", value="alice", key="user_a")
                    hdr_a = st.text_input("Header Name", value="Authorization", key="hdr_a")
                    res_a = st.text_input("Owned Resource ID", value="101", key="res_a")
                    sub_a = st.form_submit_button("Save User A Profile")
                    if sub_a:
                        requests.post(f"{TARGETS_API_BASE}/{auth_target_id}/auth-profiles", json={
                            "account_label": "User A",
                            "auth_type": type_a,
                            "token_or_secret": tok_a,
                            "header_name": hdr_a,
                            "username": user_a,
                            "owned_resource_id": res_a,
                            "role": "owner"
                        }, timeout=5)
                        st.success("User A profile saved!")

            with col_b:
                st.markdown("#### User B (Attacker / Probe)")
                with st.form("auth_b_form"):
                    type_b = st.selectbox("Auth Type", ["bearer", "api_key", "basic", "none"], key="type_b")
                    tok_b = st.text_input("Secret / Token", type="password", key="tok_b")
                    user_b = st.text_input("Username", value="bob", key="user_b")
                    hdr_b = st.text_input("Header Name", value="Authorization", key="hdr_b")
                    sub_b = st.form_submit_button("Save User B Profile")
                    if sub_b:
                        requests.post(f"{TARGETS_API_BASE}/{auth_target_id}/auth-profiles", json={
                            "account_label": "User B",
                            "auth_type": type_b,
                            "token_or_secret": tok_b,
                            "header_name": hdr_b,
                            "username": user_b,
                            "role": "probe"
                        }, timeout=5)
                        st.success("User B profile saved!")

    # ---------------------------------------------------------
    # TAB 5: LAUNCH SCAN
    # ---------------------------------------------------------
    with tab_scan:
        if not targets:
            st.warning("Please register a target API first.")
        else:
            target_names = {t["id"]: f"{t['name']} ({t['base_url']})" for t in targets}
            scan_target_id = st.selectbox(
                "Select API Target to Scan",
                options=list(target_names.keys()),
                format_func=lambda x: target_names[x],
                key="scan_target_select"
            )

            # Test target connectivity button
            if st.button("🔌 Test Target Connectivity & SSRF Safety"):
                try:
                    val_res = requests.post(f"{TARGETS_API_BASE}/{scan_target_id}/validate", timeout=5).json()
                    if val_res.get("is_valid"):
                        st.success(f"Host reachable and safe! HTTP {val_res.get('status_code')} ({val_res.get('latency_ms')}ms)")
                    else:
                        st.error(f"Validation error: {val_res.get('error_message')}")
                except Exception as ex:
                    st.error(f"Validation request failed: {ex}")

            with st.form("targeted_scan_form"):
                p_name = st.text_input("Scan Profile Name", value="Targeted Endpoint Security Audit")
                cats = st.multiselect("Test Categories", ["BOLA", "AUTH", "HEADERS", "CONFIG"], default=["BOLA", "AUTH", "HEADERS", "CONFIG"])
                auth_confirm = st.checkbox("I confirm I am authorized to perform security testing against this target API.")

                launch_btn = st.form_submit_button("🚀 Launch Targeted Security Scan")
                if launch_btn:
                    if not auth_confirm:
                        st.error("You must confirm authorization before initiating a scan.")
                    else:
                        with st.spinner("Executing Member 1 Security Detection Engine..."):
                            try:
                                scan_res = requests.post(f"{TARGETS_API_BASE}/{scan_target_id}/scan", json={
                                    "scan_profile": p_name,
                                    "categories": cats,
                                    "user_authorized": True
                                }, timeout=60).json()

                                st.success(f"Scan Completed! Status: {scan_res.get('status')}")
                                st.metric("Vulnerabilities Detected", scan_res.get("total_findings", 0))
                                st.info("Navigate to 'Vulnerability Findings' tab to review detected vulnerabilities and AI explanations.")
                            except Exception as ex:
                                st.error(f"Scan execution failed: {ex}")


def _load_demo_api():
    """Helper to 1-click register local demo API."""
    try:
        t_res = requests.post(TARGETS_API_BASE, json={
            "name": "Healthcare Patient Portal Demo API",
            "base_url": DEMO_API_URL,
            "environment": "development",
            "description": "Simulated clinic management API vulnerable to BOLA and missing security headers.",
            "api_type": "REST",
            "api_version": "1.0.0"
        }, timeout=5).json()

        target_id = t_res["id"]
        requests.post(f"{TARGETS_API_BASE}/{target_id}/import-spec", json={"spec_url": DEMO_SPEC_URL}, timeout=10)

        requests.post(f"{TARGETS_API_BASE}/{target_id}/auth-profiles", json={
            "account_label": "User A",
            "auth_type": "bearer",
            "token_or_secret": "alice_demo_token_secret",
            "header_name": "Authorization",
            "username": "alice",
            "role": "owner",
            "owned_resource_id": "101"
        }, timeout=5)

        requests.post(f"{TARGETS_API_BASE}/{target_id}/auth-profiles", json={
            "account_label": "User B",
            "auth_type": "bearer",
            "token_or_secret": "bob_attacker_probe_token",
            "header_name": "Authorization",
            "username": "bob",
            "role": "probe"
        }, timeout=5)

        st.success("Healthcare Demo API loaded successfully with dual principals!")
        st.rerun()
    except Exception as ex:
        st.error(f"Failed to load demo API: {ex}")
