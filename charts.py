"""
charts.py  –  Visualisation helpers for MoveSmart 2.0.
Only charts that genuinely help users make travel decisions are included.
"""
import plotly.graph_objects as go
import streamlit as st


def render_fare_prediction_chart(prediction: dict):
    """
    Render an inline Plotly area chart showing fare now vs 15 min vs 30 min.
    Helps the user decide whether to book immediately or wait.
    """
    labels = ["Now", "In 15 min", "In 30 min"]
    fares  = [prediction["now"], prediction["in_15"], prediction["in_30"]]

    # Colour trend line green if falling, amber if flat, red if rising
    if fares[-1] < fares[0] * 0.97:
        line_color = "#10B981"
        fill_color = "rgba(16,185,129,0.12)"
    elif fares[-1] > fares[0] * 1.03:
        line_color = "#F43F5E"
        fill_color = "rgba(244,63,94,0.12)"
    else:
        line_color = "#F59E0B"
        fill_color = "rgba(245,158,11,0.12)"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=labels,
        y=fares,
        mode="lines+markers+text",
        line=dict(color=line_color, width=2.5),
        marker=dict(size=9, color=line_color),
        fill="tozeroy",
        fillcolor=fill_color,
        text=[f"₹{f:.0f}" for f in fares],
        textposition="top center",
        textfont=dict(color="#F1F5F9", size=13),
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#94A3B8", size=12),
            linecolor="#1E293B",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            tickfont=dict(color="#94A3B8", size=11),
            tickprefix="₹",
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
