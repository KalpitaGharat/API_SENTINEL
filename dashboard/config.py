"""
API Sentinel - Configuration and Theme Constants
Exact Palette Matching Reference Image
"""

# Base Theme Colors
BG_MIDNIGHT = "#030C16"       # Deep midnight background
BG_SIDEBAR = "#05111F"        # Deep navy sidebar
BG_CARD = "#091B2E"           # Card background
BG_CARD_BORDER = "#12304D"    # Card border
BORDER_COLOR = "#12304D"      # Backward compatibility
ACCENT_CYAN = "#00D4E8"       # Bright cyan primary accent
ACCENT_BLUE = "#168BFF"       # Electric blue
TEXT_WHITE = "#FFFFFF"        # Pure white headings & values
TEXT_MUTED = "#8EA5BC"        # Muted bluish gray
TEXT_DIM = "#536E88"          # Dim helper text

# Severity Colors
SEVERITY_COLORS = {
    "Critical": {
        "text": "#FF4D4F",
        "bg": "rgba(255, 77, 79, 0.18)",
        "border": "#FF4D4F",
    },
    "High": {
        "text": "#FA8C16",
        "bg": "rgba(250, 140, 22, 0.18)",
        "border": "#FA8C16",
    },
    "Medium": {
        "text": "#FADB14",
        "bg": "rgba(250, 219, 20, 0.18)",
        "border": "#FADB14",
    },
    "Low": {
        "text": "#00D4E8",
        "bg": "rgba(0, 212, 232, 0.18)",
        "border": "#00D4E8",
    },
}

# Status Colors
STATUS_COLORS = {
    "Open": {
        "text": "#FF4D4F",
        "bg": "rgba(255, 77, 79, 0.12)",
        "border": "#FF4D4F",
        "dot": "#FF4D4F",
        "icon": "⭕",
    },
    "In Progress": {
        "text": "#FA8C16",
        "bg": "rgba(250, 140, 22, 0.12)",
        "border": "#FA8C16",
        "dot": "#FA8C16",
        "icon": "⭕",
    },
    "Fixed": {
        "text": "#52C41A",
        "bg": "rgba(82, 196, 26, 0.12)",
        "border": "#52C41A",
        "dot": "#52C41A",
        "icon": "✔",
    },
    "Verified": {
        "text": "#52C41A",
        "bg": "rgba(82, 196, 26, 0.12)",
        "border": "#52C41A",
        "dot": "#52C41A",
        "icon": "✔",
    },
}

APP_TITLE_PREFIX = "API"
APP_TITLE_SUFFIX = "Sentinel"
APP_SUBTITLE = "API Security Testing & Remediation"
TARGET_API = "https://demo-api.apisentinel.dev"
TEAM_NAME = "API Sentinel Team"
BACKEND_BASE_URL = "http://127.0.0.1:8000"
