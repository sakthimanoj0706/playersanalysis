"""Reusable Power BI-inspired design system & Plotly theme helpers for SupeRR Intelligence."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

PBI_BG_GRADIENT = "linear-gradient(135deg, #07142E 0%, #0F234B 52%, #3D1E38 100%)"
PBI_PANEL_BG = "rgba(13, 28, 62, 0.84)"
PBI_PANEL_BORDER = "rgba(148, 163, 184, 0.24)"
PBI_BLUE = "#38BDF8"
PBI_BLUE_DEEP = "#2563EB"
PBI_CORAL = "#FB7185"
PBI_YELLOW = "#FACC15"
PBI_TEAL = "#2DD4BF"
PBI_TEXT = "#F8FAFC"
PBI_MUTED = "#CBD5E1"


def inject_v5_powerbi_theme() -> None:
    """Inject Power BI-inspired blue-to-muted-red gradient theme & translucent glass panels."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {PBI_BG_GRADIENT} !important;
            color: {PBI_TEXT};
        }}
        .block-container {{
            max-width: 100% !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }}
        header[data-testid="stHeader"] {{
            background: rgba(7, 20, 46, 0.78) !important;
            border-bottom: 1px solid {PBI_PANEL_BORDER};
        }}
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label {{
            color: {PBI_TEXT} !important;
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #07122A 0%, #0E2044 100%) !important;
            border-right: 1px solid {PBI_PANEL_BORDER};
        }}
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: {PBI_TEXT} !important;
        }}
        /* Ensure selectbox/text_input values inside white inputs remain readable */
        section[data-testid="stSidebar"] [data-baseweb="select"] div,
        section[data-testid="stSidebar"] input {{
            color: #0F172A !important;
        }}
        /* Fix white-on-white buttons across main & sidebar */
        .stButton > button,
        section[data-testid="stSidebar"] .stButton > button {{
            background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(56, 189, 248, 0.55) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        .stButton > button *,
        section[data-testid="stSidebar"] .stButton > button * {{
            color: #FFFFFF !important;
        }}
        .pbi-card code {{
            background: rgba(56, 189, 248, 0.16) !important;
            color: #38BDF8 !important;
            border: 1px solid rgba(56, 189, 248, 0.35);
            padding: 1px 5px;
            border-radius: 4px;
        }}
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary:hover,
        [data-testid="stExpander"] summary * {{
            background: rgba(13, 28, 62, 0.92) !important;
            color: {PBI_TEXT} !important;
            border-color: {PBI_PANEL_BORDER} !important;
        }}
        .pbi-header {{
            background: {PBI_PANEL_BG};
            border: 1px solid {PBI_PANEL_BORDER};
            border-left: 5px solid {PBI_BLUE};
            border-radius: 12px;
            padding: 16px 22px;
            margin-bottom: 14px;
            box-shadow: 0 8px 24px rgba(2, 6, 23, 0.35);
            backdrop-filter: blur(8px);
        }}
        .pbi-badge {{
            display: inline-block;
            background: rgba(251, 113, 133, 0.16);
            color: #FDA4AF !important;
            border: 1px solid rgba(251, 113, 133, 0.45);
            font-weight: 700;
            font-size: 11px;
            padding: 4px 11px;
            border-radius: 999px;
            letter-spacing: 0.4px;
        }}
        .pbi-kpi {{
            background: {PBI_PANEL_BG};
            border: 1px solid {PBI_PANEL_BORDER};
            border-top: 3px solid {PBI_BLUE};
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 10px;
            box-shadow: 0 4px 14px rgba(2, 6, 23, 0.25);
        }}
        .pbi-kpi-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: {PBI_MUTED};
            margin-bottom: 4px;
        }}
        .pbi-kpi-val {{
            font-size: 19px;
            font-weight: 700;
            color: {PBI_TEXT};
            white-space: nowrap;
        }}
        .pbi-kpi-sub {{
            font-size: 11.5px;
            color: {PBI_YELLOW};
            margin-top: 2px;
        }}
        .pbi-card {{
            background: {PBI_PANEL_BG};
            border: 1px solid {PBI_PANEL_BORDER};
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 12px;
        }}
        .pbi-avatar {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: linear-gradient(135deg, {PBI_BLUE_DEEP}, {PBI_CORAL});
            color: #FFFFFF !important;
            font-weight: 800;
            font-size: 18px;
            border: 2px solid {PBI_BLUE};
            margin-right: 14px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_pbi_figure(fig: go.Figure, title: str, x_title: str = "", y_title: str = "", height: int = 380) -> go.Figure:
    """Apply consistent Power BI dark-glass Plotly styling."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=PBI_TEXT)),
        xaxis_title=x_title,
        yaxis_title=y_title,
        paper_bgcolor="rgba(13, 28, 62, 0.72)",
        plot_bgcolor="rgba(7, 20, 46, 0.45)",
        font=dict(color=PBI_TEXT, size=11.5),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=PBI_MUTED)),
        margin=dict(l=46, r=24, t=48, b=42),
        height=height,
    )
    fig.update_xaxes(automargin=True, gridcolor="rgba(148, 163, 184, 0.14)", zerolinecolor="rgba(148, 163, 184, 0.25)")
    fig.update_yaxes(automargin=True, gridcolor="rgba(148, 163, 184, 0.14)", zerolinecolor="rgba(148, 163, 184, 0.25)")
    return fig


def render_kpi_card(label: str, value: str, sub: str = "") -> str:
    """Return HTML for a compact Power BI KPI card."""
    sub_html = f'<div class="pbi-kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="pbi-kpi">'
        f'<div class="pbi-kpi-label">{label}</div>'
        f'<div class="pbi-kpi-val">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )
