"""
API Sentinel - Custom CSS and Exact Reference Styling
"""

from config import (
    BG_MIDNIGHT,
    BG_SIDEBAR,
    BG_CARD,
    BG_CARD_BORDER,
    ACCENT_CYAN,
    ACCENT_BLUE,
    TEXT_WHITE,
    TEXT_MUTED,
    TEXT_DIM,
)
import textwrap

def get_custom_css() -> str:
    raw_css = f"""
<style>
/* === Google Fonts (Inter & JetBrains Mono) === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* === Global Application Reset === */
html, body, [class*="st-"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: {TEXT_WHITE};
    background-color: {BG_MIDNIGHT};
}}

.stApp {{
    background-color: {BG_MIDNIGHT};
}}

/* Hide Default Streamlit Chrome Completely */
#MainMenu {{display: none !important;}}
footer {{display: none !important;}}
header[data-testid="stHeader"] {{display: none !important;}}
div[data-testid="stToolbar"] {{display: none !important;}}
div[data-testid="stDecoration"] {{display: none !important;}}

/* Main Block Layout Padding */
.main .block-container {{
    padding-top: 1.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1560px !important;
}}

/* === Sidebar Styling === */
section[data-testid="stSidebar"] {{
    background-color: {BG_SIDEBAR} !important;
    border-right: 1px solid rgba(18, 48, 77, 0.7) !important;
    width: 275px !important;
    min-width: 275px !important;
}}

section[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    padding-bottom: 1.5rem !important;
}}

/* Brand in Sidebar */
.brand-container {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.2rem;
}}

.brand-shield {{
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    filter: drop-shadow(0 0 10px rgba(0, 212, 232, 0.6));
}}

.brand-text {{
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.1;
}}

.brand-text .api {{
    color: {TEXT_WHITE};
}}

.brand-text .sentinel {{
    color: {ACCENT_CYAN};
}}

.brand-text .dot {{
    color: {ACCENT_CYAN};
    font-size: 0.85rem;
    vertical-align: super;
}}

.brand-subtext {{
    color: {TEXT_MUTED};
    font-size: 0.72rem;
    margin-top: 0.2rem;
    margin-bottom: 1.8rem;
    letter-spacing: 0.01em;
}}

/* Native HTML Sidebar Nav Items */
.sidebar-nav-item {{
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 0.65rem 1rem !important;
    border-radius: 10px !important;
    font-size: 0.88rem !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}}

.active-pill {{
    background: linear-gradient(90deg, rgba(22, 139, 255, 0.28) 0%, rgba(0, 212, 232, 0.2) 100%) !important;
    border: 1.5px solid {ACCENT_CYAN} !important;
    color: {TEXT_WHITE} !important;
    font-weight: 600 !important;
    box-shadow: 0 0 18px rgba(0, 212, 232, 0.4), inset 0 0 12px rgba(0, 212, 232, 0.15) !important;
}}

.inactive-pill {{
    background: transparent !important;
    border: 1.5px solid transparent !important;
    color: {TEXT_MUTED} !important;
    font-weight: 500 !important;
}}

.inactive-pill:hover {{
    background: rgba(22, 139, 255, 0.08) !important;
    color: {TEXT_WHITE} !important;
    border-color: rgba(22, 139, 255, 0.2) !important;
}}

/* Sidebar Footer Slogan & 3D Wave */
.sidebar-footer-container {{
    position: relative;
    margin-top: 5.5rem;
    padding-top: 1rem;
}}

.sidebar-slogan-text {{
    font-size: 0.88rem;
    font-weight: 600;
    color: {TEXT_WHITE};
    line-height: 1.55;
    position: relative;
    z-index: 3;
}}

.sidebar-wave-container {{
    position: absolute;
    bottom: -15px;
    left: -20px;
    width: 270px;
    height: 140px;
    pointer-events: none;
    z-index: 1;
    overflow: hidden;
}}

/* === Top Header Styling === */
.header-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 1.25rem;
    margin-bottom: 0.5rem;
}}

.header-title-box h1 {{
    font-size: 1.65rem;
    font-weight: 700;
    color: {TEXT_WHITE};
    margin: 0;
    letter-spacing: -0.01em;
}}

.header-title-box p {{
    color: {TEXT_MUTED};
    font-size: 0.86rem;
    margin: 0.2rem 0 0 0;
}}

.header-right-box {{
    display: flex;
    align-items: center;
    gap: 1.2rem;
}}

.bell-icon-wrapper {{
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    color: {TEXT_WHITE};
    cursor: pointer;
}}

.bell-dot {{
    position: absolute;
    top: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: {ACCENT_CYAN};
    box-shadow: 0 0 8px {ACCENT_CYAN};
}}

.header-divider {{
    width: 1px;
    height: 22px;
    background-color: rgba(142, 165, 188, 0.3);
}}

.profile-pill {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
    cursor: pointer;
}}

.profile-avatar {{
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #164673;
    color: {TEXT_WHITE};
    font-size: 0.8rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(0, 212, 232, 0.4);
}}

.profile-name {{
    font-size: 0.86rem;
    font-weight: 500;
    color: {TEXT_WHITE};
}}

.profile-caret {{
    color: {TEXT_MUTED};
    font-size: 0.75rem;
}}

/* === Universal Dark Cards === */
.ref-card {{
    background: {BG_CARD};
    border-radius: 12px;
    border: 1px solid {BG_CARD_BORDER};
    padding: 1.25rem 1.35rem;
    position: relative;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}}

/* 4 Distinct Glowing KPI Cards */
.kpi-card-blue {{
    background: {BG_CARD};
    border-radius: 12px;
    border: 1px solid #165287;
    box-shadow: 0 0 18px rgba(22, 139, 255, 0.12);
    padding: 1.15rem 1.25rem;
    height: 100%;
}}

.kpi-card-red {{
    background: {BG_CARD};
    border-radius: 12px;
    border: 1px solid #6E1F24;
    box-shadow: 0 0 18px rgba(255, 77, 79, 0.12);
    padding: 1.15rem 1.25rem;
    height: 100%;
}}

.kpi-card-green {{
    background: {BG_CARD};
    border-radius: 12px;
    border: 1px solid #1E5C2D;
    box-shadow: 0 0 18px rgba(82, 196, 26, 0.12);
    padding: 1.15rem 1.25rem;
    height: 100%;
}}

.kpi-card-cyan {{
    background: {BG_CARD};
    border-radius: 12px;
    border: 1px solid #13556B;
    box-shadow: 0 0 18px rgba(0, 212, 232, 0.12);
    padding: 1.15rem 1.25rem;
    height: 100%;
    position: relative;
}}

.kpi-layout {{
    display: flex;
    align-items: center;
    gap: 1.1rem;
}}

.kpi-icon-box {{
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

.kpi-content {{
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}}

.kpi-label {{
    color: {TEXT_MUTED};
    font-size: 0.82rem;
    font-weight: 500;
    margin-bottom: 0.2rem;
}}

.kpi-metric-row {{
    display: flex;
    align-items: baseline;
    gap: 0.55rem;
}}

.kpi-number {{
    font-size: 1.85rem;
    font-weight: 700;
    color: {TEXT_WHITE};
    line-height: 1;
}}

.kpi-delta-pill {{
    display: inline-flex;
    align-items: center;
    gap: 2px;
    font-size: 0.74rem;
    font-weight: 600;
    padding: 0.12rem 0.45rem;
    border-radius: 12px;
    background: rgba(82, 196, 26, 0.18);
    color: #52C41A;
    border: 1px solid rgba(82, 196, 26, 0.4);
}}

.kpi-subtext {{
    color: {TEXT_DIM};
    font-size: 0.72rem;
    margin-top: 0.35rem;
}}

.kpi-progress-bar {{
    margin-top: 0.65rem;
    width: 100%;
    height: 5px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    overflow: hidden;
}}

.kpi-progress-fill {{
    width: 76%;
    height: 100%;
    background: linear-gradient(90deg, #52C41A, #00D4E8);
    border-radius: 4px;
}}

/* Card Titles */
.card-header-title {{
    font-size: 0.98rem;
    font-weight: 600;
    color: {TEXT_WHITE};
    margin: 0;
}}

/* Recent Vulnerability Findings Table */
.ref-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
}}

.ref-table th {{
    color: {TEXT_MUTED};
    font-size: 0.74rem;
    font-weight: 600;
    text-align: left;
    padding: 0.65rem 0.8rem;
    border-bottom: 1px solid rgba(18, 48, 77, 0.8);
}}

.ref-table td {{
    padding: 0.75rem 0.8rem;
    border-bottom: 1px solid rgba(18, 48, 77, 0.5);
    color: {TEXT_WHITE};
    vertical-align: middle;
}}

.ref-table tr:last-child td {{
    border-bottom: none;
}}

/* Exact Severity Pills */
.pill-sev-critical {{
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
    background: #FF4D4F;
    color: #FFFFFF;
}}

.pill-sev-high {{
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
    background: #FA8C16;
    color: #FFFFFF;
}}

.pill-sev-medium {{
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
    background: #FADB14;
    color: #1A1A1A;
}}

.pill-sev-low {{
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
    background: #00D4E8;
    color: #030C16;
}}

/* Exact Status Pills */
.pill-stat-open {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 0.18rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 500;
    background: rgba(255, 77, 79, 0.12);
    color: #FF4D4F;
    border: 1px solid rgba(255, 77, 79, 0.4);
}}

.pill-stat-inprogress {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 0.18rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 500;
    background: rgba(250, 140, 22, 0.12);
    color: #FA8C16;
    border: 1px solid rgba(250, 140, 22, 0.4);
}}

.pill-stat-fixed {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 0.18rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 500;
    background: rgba(82, 196, 26, 0.12);
    color: #52C41A;
    border: 1px solid rgba(82, 196, 26, 0.4);
}}

.pill-stat-verified {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 0.18rem 0.65rem;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 500;
    background: rgba(82, 196, 26, 0.12);
    color: #52C41A;
    border: 1px solid rgba(82, 196, 26, 0.4);
}}

/* Last Scan Summary */
.summary-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 0;
    border-bottom: 1px solid rgba(18, 48, 77, 0.4);
    font-size: 0.83rem;
}}

.summary-row:last-of-type {{
    border-bottom: none;
}}

.summary-key {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: {TEXT_MUTED};
    font-size: 0.82rem;
}}

.summary-val {{
    color: {TEXT_WHITE};
    font-weight: 500;
    font-size: 0.82rem;
}}

.summary-val a {{
    color: {ACCENT_CYAN};
    text-decoration: none;
}}

.summary-val a:hover {{
    text-decoration: underline;
}}

/* Solid Cyan CTA Button */
.btn-run-scan {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    width: 100% !important;
    margin-top: 1.1rem !important;
    padding: 0.75rem 1rem !important;
    background: {ACCENT_CYAN} !important;
    color: #030C16 !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    border: none !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    box-shadow: 0 4px 16px rgba(0, 212, 232, 0.4) !important;
    transition: all 0.2s ease !important;
    text-decoration: none !important;
}}

.btn-run-scan:hover {{
    background: #38E1FF !important;
    box-shadow: 0 6px 22px rgba(0, 212, 232, 0.6) !important;
    transform: translateY(-1px) !important;
}}
</style>
"""
    return textwrap.dedent(raw_css).strip()
