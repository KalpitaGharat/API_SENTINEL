"""
API Sentinel - Recent Vulnerability Findings Table
"""

from utils import render_html

def render_recent_findings_table():
    """Renders the recent findings card matching the reference image."""
    render_html(
        """
        <div class="ref-card" style="height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem;">
                <span class="card-header-title">Recent Vulnerability Findings</span>
                <a href="?page=findings" target="_self" style="color: #00D4E8; font-weight: 600; font-size: 0.85rem; text-decoration: none;">
                    View All →
                </a>
            </div>
            <div style="overflow-x: auto;">
                <table class="ref-table">
                    <thead>
                        <tr>
                            <th style="width: 4%;">#</th>
                            <th style="width: 38%;">Vulnerability</th>
                            <th style="width: 20%;">Affected Endpoint</th>
                            <th style="width: 12%;">Severity</th>
                            <th style="width: 14%;">Status</th>
                            <th style="width: 12%;">Detected On</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="color: #8EA5BC;">1</td>
                            <td style="font-weight: 500; color: #FFFFFF;">Broken Object Level Authorization (BOLA)</td>
                            <td style="color: #8EA5BC; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">GET /api/users/{id}</td>
                            <td><span class="pill-sev-critical">Critical</span></td>
                            <td><span class="pill-stat-open">⭕ Open</span></td>
                            <td style="color: #8EA5BC; font-size: 0.78rem;">Nov 09, 2026 14:32</td>
                        </tr>
                        <tr>
                            <td style="color: #8EA5BC;">2</td>
                            <td style="font-weight: 500; color: #FFFFFF;">Missing Security Headers</td>
                            <td style="color: #8EA5BC; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">/ (global)</td>
                            <td><span class="pill-sev-high">High</span></td>
                            <td><span class="pill-stat-inprogress">⭕ In Progress</span></td>
                            <td style="color: #8EA5BC; font-size: 0.78rem;">Nov 09, 2026 14:32</td>
                        </tr>
                        <tr>
                            <td style="color: #8EA5BC;">3</td>
                            <td style="font-weight: 500; color: #FFFFFF;">Weak Authentication Configuration</td>
                            <td style="color: #8EA5BC; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">POST /api/login</td>
                            <td><span class="pill-sev-high">High</span></td>
                            <td><span class="pill-stat-open">⭕ Open</span></td>
                            <td style="color: #8EA5BC; font-size: 0.78rem;">Nov 08, 2026 19:10</td>
                        </tr>
                        <tr>
                            <td style="color: #8EA5BC;">4</td>
                            <td style="font-weight: 500; color: #FFFFFF;">Insecure API Configuration</td>
                            <td style="color: #8EA5BC; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">GET /api/config</td>
                            <td><span class="pill-sev-medium">Medium</span></td>
                            <td><span class="pill-stat-fixed">✔ Fixed</span></td>
                            <td style="color: #8EA5BC; font-size: 0.78rem;">Nov 08, 2026 16:47</td>
                        </tr>
                        <tr>
                            <td style="color: #8EA5BC;">5</td>
                            <td style="font-weight: 500; color: #FFFFFF;">Missing Rate Limiting</td>
                            <td style="color: #8EA5BC; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">POST /api/register</td>
                            <td><span class="pill-sev-low">Low</span></td>
                            <td><span class="pill-stat-verified">✔ Verified</span></td>
                            <td style="color: #8EA5BC; font-size: 0.78rem;">Nov 07, 2026 11:20</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """
    )
