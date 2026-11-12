"""
API Sentinel - Top Header Component
"""

from utils import render_html
from config import TEAM_NAME

def render_header(title: str = "Security Overview", subtitle: str = "Real-time view of your API security posture, findings, and scan activity."):
    """Renders the top header bar."""
    render_html(
        f"""
        <div class="header-row">
            <div class="header-title-box">
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            <div class="header-right-box">
                <!-- Bell Icon with Cyan Glowing Dot -->
                <div class="bell-icon-wrapper" title="Alerts">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    </svg>
                    <div class="bell-dot"></div>
                </div>

                <div class="header-divider"></div>

                <!-- Profile with Blue Circle 'A' and Team Name -->
                <div class="profile-pill">
                    <div class="profile-avatar">A</div>
                    <span class="profile-name">{TEAM_NAME}</span>
                    <span class="profile-caret">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8EA5BC" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="6 9 12 15 18 9"/>
                        </svg>
                    </span>
                </div>
            </div>
        </div>
        """
    )
