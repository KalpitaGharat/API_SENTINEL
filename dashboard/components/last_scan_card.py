"""
API Sentinel - Last Scan Summary Card
"""

from utils import render_html

def render_last_scan_card():
    """Renders the Last Scan Summary card matching the reference image."""
    render_html(
        """
        <div class="ref-card" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.85rem;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="4" y="2" width="16" height="20" rx="2" ry="2"/>
                        <line x1="8" y1="6" x2="16" y2="6"/>
                        <line x1="8" y1="10" x2="16" y2="10"/>
                        <line x1="8" y1="14" x2="12" y2="14"/>
                    </svg>
                    <span class="card-header-title">Last Scan Summary</span>
                </div>

                <div class="summary-row">
                    <span class="summary-key">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8EA5BC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="2" y1="12" x2="22" y2="12"/>
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                        </svg>
                        Target API
                    </span>
                    <span class="summary-val">
                        <a href="https://demo-api.apisentinel.dev" target="_blank">
                            https://demo-api.apisentinel.dev <span style="font-size: 0.75rem;">↗</span>
                        </a>
                    </span>
                </div>

                <div class="summary-row">
                    <span class="summary-key">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8EA5BC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                            <polyline points="2 17 12 22 22 17"/>
                            <polyline points="2 12 12 17 22 12"/>
                        </svg>
                        Scan Type
                    </span>
                    <span class="summary-val">Full Security Scan</span>
                </div>

                <div class="summary-row">
                    <span class="summary-key">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8EA5BC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        Findings
                    </span>
                    <span class="summary-val" style="font-size: 0.8rem;">7 (2 Critical, 2 High, 2 Medium, 1 Low)</span>
                </div>

                <div class="summary-row">
                    <span class="summary-key">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8EA5BC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                        Completed On
                    </span>
                    <span class="summary-val">Nov 09, 2026 14:32</span>
                </div>

                <div class="summary-row">
                    <span class="summary-key">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8EA5BC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12 6 12 12 16 14"/>
                        </svg>
                        Duration
                    </span>
                    <span class="summary-val">3 min 26 sec</span>
                </div>
            </div>

            <a href="?page=new_scan" target="_self" class="btn-run-scan">
                <span style="font-size: 0.8rem;">▶</span> Run New Security Scan
            </a>
        </div>
        """
    )
