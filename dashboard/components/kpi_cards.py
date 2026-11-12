"""
API Sentinel - 4 Glowing KPI Metric Cards
"""

import streamlit as st
from utils import render_html

def render_kpi_cards():
    """Renders the 4 distinct glowing KPI cards in a 4-column layout."""
    col1, col2, col3, col4 = st.columns(4)

    # 1. Total Scans (Blue Glow)
    with col1:
        render_html(
            """
            <div class="kpi-card-blue">
                <div class="kpi-layout">
                    <div class="kpi-icon-box">
                        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#168BFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="9"/>
                            <path d="M12 3v4"/>
                            <path d="M12 17v4"/>
                            <path d="M3 12h4"/>
                            <path d="M17 12h4"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </div>
                    <div class="kpi-content">
                        <span class="kpi-label">Total Scans</span>
                        <div class="kpi-metric-row">
                            <span class="kpi-number">24</span>
                            <span class="kpi-delta-pill">▲ +26%</span>
                        </div>
                        <span class="kpi-subtext">vs. previous 7 days</span>
                    </div>
                </div>
            </div>
            """
        )

    # 2. Total Vulnerabilities (Red Glow)
    with col2:
        render_html(
            """
            <div class="kpi-card-red">
                <div class="kpi-layout">
                    <div class="kpi-icon-box">
                        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#FF4D4F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                    </div>
                    <div class="kpi-content">
                        <span class="kpi-label">Total Vulnerabilities</span>
                        <div class="kpi-metric-row">
                            <span class="kpi-number">37</span>
                            <span class="kpi-delta-pill">▼ -18%</span>
                        </div>
                        <span class="kpi-subtext">vs. previous 7 days</span>
                    </div>
                </div>
            </div>
            """
        )

    # 3. Fixed / Verified (Green Glow)
    with col3:
        render_html(
            """
            <div class="kpi-card-green">
                <div class="kpi-layout">
                    <div class="kpi-icon-box">
                        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#52C41A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="9 12 11 14 15 10"/>
                        </svg>
                    </div>
                    <div class="kpi-content">
                        <span class="kpi-label">Fixed / Verified</span>
                        <div class="kpi-metric-row">
                            <span class="kpi-number">28</span>
                            <span class="kpi-delta-pill">▲ +40%</span>
                        </div>
                        <span class="kpi-subtext">vs. previous 7 days</span>
                    </div>
                </div>
            </div>
            """
        )

    # 4. Security Health (Cyan Glow + Info Icon + Progress Bar)
    with col4:
        render_html(
            """
            <div class="kpi-card-cyan">
                <div style="position: absolute; top: 12px; right: 14px; color: #8EA5BC; font-size: 0.85rem; cursor: pointer;">
                    ⓘ
                </div>
                <div class="kpi-layout">
                    <div class="kpi-icon-box">
                        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#00D4E8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            <polyline points="9 12 11 14 15 10"/>
                        </svg>
                    </div>
                    <div class="kpi-content">
                        <span class="kpi-label">Security Health</span>
                        <div class="kpi-metric-row">
                            <span class="kpi-number">76%</span>
                            <span class="kpi-delta-pill">▲ +12 pts</span>
                        </div>
                        <span class="kpi-subtext">vs. previous 7 days</span>
                    </div>
                </div>
                <div class="kpi-progress-bar">
                    <div class="kpi-progress-fill"></div>
                </div>
            </div>
            """
        )
