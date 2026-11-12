"""
API Sentinel - Sidebar Navigation Component
"""

import streamlit as st
from utils import render_html
from config import APP_TITLE_PREFIX, APP_TITLE_SUFFIX, APP_SUBTITLE, ACCENT_CYAN

def render_sidebar() -> str:
    """Renders the fixed sidebar matching the reference visual."""
    query_page = st.query_params.get("page", None)
    if query_page:
        st.session_state["current_page"] = query_page
    elif "current_page" not in st.session_state:
        st.session_state["current_page"] = "overview"

    current = st.session_state["current_page"]

    with st.sidebar:
        # Brand Logo and Title
        render_html(
            f"""
            <div class="brand-container">
                <div class="brand-shield">
                    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="{ACCENT_CYAN}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <polyline points="9 12 11 14 15 10"/>
                    </svg>
                </div>
                <div>
                    <div class="brand-text">
                        <span class="api">{APP_TITLE_PREFIX}</span> <span class="sentinel">{APP_TITLE_SUFFIX}</span><span class="dot">®</span>
                    </div>
                </div>
            </div>
            <div class="brand-subtext">{APP_SUBTITLE}</div>
            """
        )

        nav_items = [
            ("overview", "Security Overview", _home_svg),
            ("onboarding", "API Onboarding & Specs", _layers_svg),
            ("new_scan", "New Security Scan", _play_svg),
            ("findings", "Vulnerability Findings", _alert_svg),
            ("api_keys", "API Key Intelligence", _key_svg),
            ("retesting", "Retesting and Verification", _check_svg),
            ("history", "Scan History", _clock_svg),
            ("reports", "Reports", _chart_svg),
        ]

        nav_links_html = '<div style="display: flex; flex-direction: column; gap: 6px;">'
        for key, label, svg_fn in nav_items:
            is_active = (current == key)
            link_class = "sidebar-nav-item active-pill" if is_active else "sidebar-nav-item inactive-pill"
            icon_svg = svg_fn(is_active)
            nav_links_html += f"""
            <a href="?page={key}" target="_self" class="{link_class}">
                {icon_svg}
                <span>{label}</span>
            </a>
            """
        nav_links_html += '</div>'

        render_html(nav_links_html)

        render_html(
            """
            <div class="sidebar-footer-container">
                <div class="sidebar-slogan-text">
                    Find it.<br>
                    Understand it.<br>
                    Fix it.<br>
                    Verify it.
                </div>
                <div class="sidebar-wave-container">
                    <svg viewBox="0 0 270 140" style="width: 100%; height: 100%;">
                        <defs>
                            <linearGradient id="waveGlow" x1="0%" y1="100%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="#00D4E8" stop-opacity="0.8"/>
                                <stop offset="50%" stop-color="#168BFF" stop-opacity="0.4"/>
                                <stop offset="100%" stop-color="#05111F" stop-opacity="0"/>
                            </linearGradient>
                            <filter id="meshGlow" x="-20%" y="-20%" width="140%" height="140%">
                                <feGaussianBlur stdDeviation="2.5" result="blur"/>
                                <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                            </filter>
                        </defs>
                        <path d="M -10 130 C 50 110, 80 50, 150 90 C 200 120, 230 60, 280 40" fill="none" stroke="url(#waveGlow)" stroke-width="1.2" opacity="0.6"/>
                        <path d="M -10 140 C 60 115, 90 60, 160 95 C 210 125, 240 70, 280 50" fill="none" stroke="url(#waveGlow)" stroke-width="1.5" opacity="0.75" filter="url(#meshGlow)"/>
                        <path d="M -10 120 C 40 105, 70 40, 140 85 C 190 115, 220 50, 280 30" fill="none" stroke="url(#waveGlow)" stroke-width="0.8" opacity="0.4"/>
                        <circle cx="15" cy="122" r="1.5" fill="#00D4E8" opacity="0.8"/>
                        <circle cx="35" cy="115" r="2" fill="#00D4E8" opacity="0.9" filter="url(#meshGlow)"/>
                        <circle cx="55" cy="102" r="1.8" fill="#38E1FF" opacity="0.85"/>
                        <circle cx="75" cy="80" r="2.2" fill="#00D4E8" opacity="0.95" filter="url(#meshGlow)"/>
                        <circle cx="95" cy="65" r="1.6" fill="#00D4E8" opacity="0.7"/>
                        <circle cx="115" cy="68" r="2" fill="#38E1FF" opacity="0.85"/>
                        <circle cx="135" cy="80" r="2.5" fill="#00D4E8" opacity="0.95" filter="url(#meshGlow)"/>
                        <circle cx="155" cy="95" r="2" fill="#00D4E8" opacity="0.8"/>
                        <circle cx="175" cy="105" r="1.6" fill="#38E1FF" opacity="0.7"/>
                        <circle cx="195" cy="100" r="2" fill="#00D4E8" opacity="0.85"/>
                        <circle cx="215" cy="80" r="2.2" fill="#00D4E8" opacity="0.9" filter="url(#meshGlow)"/>
                        <circle cx="235" cy="60" r="1.7" fill="#38E1FF" opacity="0.75"/>
                        <circle cx="255" cy="45" r="2" fill="#00D4E8" opacity="0.8"/>
                    </svg>
                </div>
            </div>
            """
        )

    return st.session_state["current_page"]

def _home_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>"""

def _layers_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/></svg>"""

def _play_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><polygon points="5 3 19 12 5 21 5 3"/></svg>"""

def _alert_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""

def _check_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>"""

def _clock_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>"""

def _chart_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>"""

def _key_svg(active: bool) -> str:
    color = "#FFFFFF" if active else "#8EA5BC"
    return f"""<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="m21 2-2 2m-1.5 1.5L10 13l-4 4-4-1 1-4 4-4 7.5-7.5"/><circle cx="7.5" cy="16.5" r=".5"/></svg>"""
