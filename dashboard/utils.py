"""
API Sentinel - HTML Rendering Helper
Prevents Markdown from converting 4-space indented HTML strings into <pre><code> blocks.
"""

import streamlit as st
import textwrap

def render_html(html_str: str):
    """Safely renders HTML without Markdown whitespace indentation artifacts."""
    clean_html = textwrap.dedent(html_str).strip()
    st.markdown(clean_html, unsafe_allow_html=True)
