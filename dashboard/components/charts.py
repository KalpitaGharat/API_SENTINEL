"""
API Sentinel - Plotly Analytics Charts Component
"""

import plotly.graph_objects as go
import streamlit as st
from utils import render_html
from config import BG_CARD

def render_analytics_section():
    """Renders the middle analytics section with the Donut + vertical legend and 14-day Scan Activity."""
    col_donut, col_activity = st.columns([1, 1.25])

    # Left Card: Vulnerability Severity Distribution
    with col_donut:
        render_html(
            """
            <div class="ref-card" style="height: 100%;">
                <div class="card-header-title" style="margin-bottom: 0.5rem;">
                    Vulnerability Severity Distribution
                </div>
            """
        )

        col_chart, col_legend = st.columns([1.2, 1])
        with col_chart:
            fig_donut = _create_donut_chart()
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

        with col_legend:
            render_html(
                """
                <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; gap: 14px; padding-top: 15px; font-size: 0.85rem;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #FF4D4F; display: inline-block;"></span>
                            <span style="color: #FFFFFF; font-weight: 500;">Critical</span>
                        </div>
                        <span style="color: #8EA5BC; font-weight: 500;">6 (16%)</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #FA8C16; display: inline-block;"></span>
                            <span style="color: #FFFFFF; font-weight: 500;">High</span>
                        </div>
                        <span style="color: #8EA5BC; font-weight: 500;">10 (27%)</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #FADB14; display: inline-block;"></span>
                            <span style="color: #FFFFFF; font-weight: 500;">Medium</span>
                        </div>
                        <span style="color: #8EA5BC; font-weight: 500;">14 (38%)</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #00D4E8; display: inline-block;"></span>
                            <span style="color: #FFFFFF; font-weight: 500;">Low</span>
                        </div>
                        <span style="color: #8EA5BC; font-weight: 500;">7 (19%)</span>
                    </div>
                </div>
                """
            )

        render_html("</div>")

    # Right Card: Scan Activity (Last 14 Days)
    with col_activity:
        render_html(
            """
            <div class="ref-card" style="height: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
                    <span class="card-header-title">Scan Activity (Last 14 Days)</span>
                    <span style="display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: #FFFFFF; font-weight: 500;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: #00D4E8; display: inline-block;"></span>
                        Scans Run
                    </span>
                </div>
            """
        )

        fig_activity = _create_activity_chart()
        st.plotly_chart(fig_activity, use_container_width=True, config={"displayModeBar": False})

        render_html("</div>")

def _create_donut_chart() -> go.Figure:
    """Exact donut chart matching the reference."""
    labels = ["Critical", "High", "Medium", "Low"]
    values = [6, 10, 14, 7]
    colors = ["#FF4D4F", "#FA8C16", "#FADB14", "#00D4E8"]

    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.68,
            marker=dict(
                colors=colors,
                line=dict(color=BG_CARD, width=3.5)
            ),
            textinfo='none',
            hoverinfo='label+value+percent',
            sort=False,
            direction='clockwise',
        )
    ])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=10, l=10, r=10),
        height=200,
        showlegend=False,
        annotations=[
            dict(
                text="<span style='font-size:26px; font-weight:700; color:#FFFFFF;'>37</span><br><span style='font-size:12px; font-weight:500; color:#8EA5BC;'>Findings</span>",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(family="Inter"),
                align="center"
            )
        ]
    )
    return fig

def _create_activity_chart() -> go.Figure:
    """Exact 14-day scan activity line chart matching the reference."""
    dates = [
        "Oct 27", "Oct 28", "Oct 29", "Oct 30", "Oct 31",
        "Nov 01", "Nov 02", "Nov 03", "Nov 04", "Nov 05",
        "Nov 06", "Nov 07", "Nov 08", "Nov 09"
    ]
    scans = [1.0, 1.8, 3.1, 2.0, 5.0, 3.2, 4.0, 7.6, 4.2, 4.0, 5.1, 6.8, 4.1, 6.0]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=scans,
        mode='lines+markers',
        name='Scans Run',
        line=dict(
            color='#00D4E8',
            width=2.5,
            shape='spline',
            smoothing=0.85
        ),
        marker=dict(
            size=6,
            color='#FFFFFF',
            line=dict(color='#00D4E8', width=2.5)
        ),
        fill='tozeroy',
        fillcolor='rgba(0, 212, 232, 0.12)',
        hoverinfo='x+y'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=15, b=20, l=25, r=10),
        height=200,
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            color='#8EA5BC',
            tickfont=dict(size=10, family="Inter", color="#8EA5BC"),
            showline=False,
            ticks="",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(18, 48, 77, 0.45)',
            gridwidth=1,
            color='#8EA5BC',
            tickfont=dict(size=10, family="Inter", color="#8EA5BC"),
            showline=False,
            zeroline=False,
            range=[0, 10.5],
            dtick=2
        )
    )
    return fig
