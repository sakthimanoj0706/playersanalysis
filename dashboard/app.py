"""SupeRR Intelligence V4.2 — Professional Cricket Analytics Platform.

Light-mode, deep-navy + restrained RR-pink executive analytics platform.
Reads authoritative V4.2 outputs from data/outputs/final/ (plus validation/audit
tables from data/outputs/v4_2/ and RR 2026 context from data/outputs/v3/).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "data/outputs/final"
V42_DIR = ROOT / "data/outputs/v4_2"
V3_DIR = ROOT / "data/outputs/v3"

NAVY = "#0B1B3D"
NAVY_MID = "#1E3A6D"
RR_PINK = "#EA1A85"
SLATE_BG = "#F8FAFC"
CARD_BORDER = "#E2E8F0"
TEXT_MAIN = "#0F172A"
TEXT_MUTED = "#475569"
TEAL_POS = "#0F766E"
AMBER_WARN = "#B45309"

BAT_MU0 = -36.124
BOWL_MU0 = -50.884


st.set_page_config(
    page_title="SupeRR Intelligence V4.2",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    /* Force clean light theme even when OS prefers dark mode */
    header[data-testid="stHeader"] {{
        background-color: {SLATE_BG} !important;
        border-bottom: 1px solid {CARD_BORDER};
    }}
    .stApp {{
        background-color: {SLATE_BG} !important;
        color: {TEXT_MAIN};
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
        color: {NAVY} !important;
        letter-spacing: -0.01em;
    }}
    .stApp p, .stApp li, .stApp label,
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
    button[data-baseweb="tab"] p {{
        color: {TEXT_MAIN} !important;
    }}
    /* Light-mode form inputs & dropdowns */
    .stApp [data-baseweb="select"] > div,
    .stApp [data-baseweb="input"] > div,
    .stApp [data-baseweb="base-input"] > input {{
        background-color: #FFFFFF !important;
        color: {TEXT_MAIN} !important;
        border-color: #CBD5E1 !important;
    }}
    .stApp [data-baseweb="select"] span,
    .stApp [data-baseweb="select"] div {{
        color: {TEXT_MAIN} !important;
    }}
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {NAVY} !important;
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: #F8FAFC !important;
    }}
    /* Header & Cards */
    .superr-header {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-left: 5px solid {NAVY};
        border-radius: 8px;
        padding: 16px 22px;
        margin-bottom: 14px;
    }}
    .superr-badge {{
        display: inline-block;
        background: #FDF2F8;
        color: {RR_PINK} !important;
        border: 1px solid #FBCFE8;
        font-weight: 700;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 999px;
        letter-spacing: 0.5px;
    }}
    .kpi-card {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        padding: 13px 15px;
        height: 100%;
    }}
    .kpi-label {{
        font-size: 11px;
        font-weight: 700;
        color: {TEXT_MUTED} !important;
        letter-spacing: 0.4px;
    }}
    .kpi-val {{
        font-size: 22px;
        font-weight: 800;
        color: {NAVY} !important;
        font-variant-numeric: tabular-nums;
        margin: 4px 0 2px 0;
    }}
    .kpi-sub {{
        font-size: 12px;
        color: {TEXT_MUTED} !important;
    }}
    .avatar-circle {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: {NAVY};
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 13px;
        margin-right: 10px;
        border: 2px solid {RR_PINK};
        vertical-align: middle;
    }}
    .dossier-card {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-left: 4px solid {RR_PINK};
        border-radius: 8px;
        padding: 16px 18px;
        margin-top: 8px;
    }}
    .status-strip {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-left: 4px solid {NAVY_MID};
        border-radius: 6px;
        padding: 10px 14px;
        margin: 10px 0 14px 0;
        font-size: 13px;
        color: {TEXT_MAIN};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt_num(val: Any, fmt: str = "{:.2f}", unavailable: str = "Unavailable") -> str:
    """Format numeric value safely without ever turning NaN/None into 0."""
    if val is None or pd.isna(val):
        return unavailable
    try:
        return fmt.format(float(val))
    except (TypeError, ValueError):
        return unavailable


def fmt_int(val: Any, unavailable: str = "Unavailable") -> str:
    if val is None or pd.isna(val):
        return unavailable
    try:
        return f"{int(round(float(val))):,}"
    except (TypeError, ValueError):
        return unavailable


def initials_badge(name: str) -> str:
    parts = [p for p in str(name).strip().split() if p]
    if not parts:
        initials = "?"
    elif len(parts) == 1:
        initials = parts[0][:2].upper()
    else:
        initials = (parts[0][0] + parts[-1][0]).upper()
    return f'<span class="avatar-circle">{initials}</span>'


@st.cache_data(show_spinner=False)
def load_all_data() -> dict[str, Any]:
    sot = json.loads((FINAL_DIR / "FINAL_RANKING_SOURCE_OF_TRUTH.json").read_text(encoding="utf-8"))
    return {
        "sot": sot,
        "top_bat": pd.read_csv(FINAL_DIR / "FINAL_TOP_10_BATTERS.csv"),
        "top_bowl": pd.read_csv(FINAL_DIR / "FINAL_TOP_10_BOWLERS.csv"),
        "all_est": pd.read_csv(FINAL_DIR / "ALL_PLAYER_FINAL_ESTIMATES.csv"),
        "rr_req": pd.read_csv(FINAL_DIR / "RR_TEAM_REQUIREMENTS.csv"),
        "rr_top10": pd.read_csv(FINAL_DIR / "RR_TOP10_CANDIDATE_FIT.csv"),
        "rr_outside": pd.read_csv(FINAL_DIR / "RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv"),
        "rr_squad": pd.read_csv(FINAL_DIR / "RR_RECOMMENDED_SQUAD.csv"),
        "star_audit": pd.read_csv(ROOT / "STAR_PLAYER_ELIGIBILITY_AUDIT.csv"),
        "method_cmp": pd.read_csv(ROOT / "PRESSURE_METHODOLOGY_COMPARISON.csv"),
        "val_matrix": pd.read_csv(V42_DIR / "V4_2_VALIDATION_MATRIX.csv"),
        "score_audit": pd.read_csv(V42_DIR / "V4_2_SCORE_ENRICHMENT_AUDIT.csv"),
        "rr_2026_str": pd.read_csv(V3_DIR / "rr_2026_team_strengths.csv"),
        "rr_2026_wk": pd.read_csv(V3_DIR / "rr_2026_team_weaknesses.csv"),
    }


D = load_all_data()

# Sidebar navigation
st.sidebar.markdown("## SupeRR Intelligence")
st.sidebar.caption("V4.2 PROVISIONAL — RESOURCE STRESS")
section = st.sidebar.radio(
    "Workspace",
    [
        "1. Overview",
        "2. Universal Top 10",
        "3. Player Explorer & Comparison",
        "4. Rajasthan Royals Intelligence",
        "5. Methodology & Transparency",
    ],
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Authoritative outputs: `data/outputs/final/`\n\n"
    "Eligibility floor: `n_hi >= 50`, `n_lo >= 30`, `cs_matches >= 8`, `se_delta <= 25.0`.\n\n"
    "RR scouting is strictly secondary and never modifies Universal Top 10 ranks."
)

# Top Header Banner
st.markdown(
    """
    <div class="superr-header">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
                <h1 style="margin:0; font-size:24px; color:#0B1B3D;">SupeRR Intelligence</h1>
                <p style="margin:4px 0 0 0; color:#475569; font-size:13.5px;">
                    Official Objective: Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels.
                </p>
            </div>
            <span class="superr-badge">V4.2 PROVISIONAL — RESOURCE STRESS</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def _preview_table(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Rank": df["shortlist_rank_display"].apply(fmt_int),
            "Player": df["player_name"],
            "Matches": df["cs_matches"].apply(fmt_int),
            "EB Δ": df["eb_delta"].apply(fmt_num),
            "vs Pop μ₀": df["eb_vs_pop_mean_delta"].apply(lambda x: fmt_num(x, "{:+.2f}")),
            "P(Top 10)": df["prob_top_10"].apply(lambda x: fmt_num(x, "{:.3f}")),
            "Confidence": df["sample_confidence"],
        }
    )


def render_overview() -> None:
    all_est = D["all_est"]
    elig_bat = all_est[(all_est["role"] == "batter") & (all_est["eligible"] == True)]
    elig_bowl = all_est[(all_est["role"] == "bowler") & (all_est["eligible"] == True)]

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("DATASET COVERAGE", "837 Matches", "193,988 regular + 26 Super Over balls"),
        ("ELIGIBLE BATTERS", f"{len(elig_bat)}", "10 shortlisted (n_hi≥50, n_lo≥30, ≥8 matches)"),
        ("ELIGIBLE BOWLERS", f"{len(elig_bowl)}", "10 shortlisted (n_hi≥50, n_lo≥30, ≥8 matches)"),
        ("PRIMARY ESTIMATOR", "Complete FWL", "Option A Penalized FWL + REML EB"),
    ]
    for col, (lbl, val, sub) in zip([c1, c2, c3, c4], kpis):
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
            f'<div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="status-strip">
            <b>Provisional Scope:</b> Because chase targets/required run rates fail reconciliation on 342/390 non-DLS chases
            (<code>MARGIN_MISMATCH_BLOCKED</code>), V4.2 evaluates pre-delivery <b>BATTING_RESOURCE_STRESS</b> (wicket-depletion anomaly)
            and <b>BOWLING_SCORING_THREAT</b> (expected scoring environment) rather than calibrated Win-Probability Leverage.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_b, col_w = st.columns(2)
    with col_b:
        st.subheader("Universal Batters — Top 5")
        st.dataframe(_preview_table(D["top_bat"].head(5)), use_container_width=True, hide_index=True)
    with col_w:
        st.subheader("Universal Bowlers — Top 5")
        st.dataframe(_preview_table(D["top_bowl"].head(5)), use_container_width=True, hide_index=True)

    st.subheader("Data Integrity & Identity Verification")
    q1, q2, q3 = st.columns(3)
    q1.markdown(
        '<div class="kpi-card"><div class="kpi-label">SUPER OVER ISOLATION</div>'
        '<div class="kpi-val">26 Balls</div><div class="kpi-sub">Innings &gt; 2 isolated from regular baselines</div></div>',
        unsafe_allow_html=True,
    )
    q2.markdown(
        '<div class="kpi-card"><div class="kpi-label">IDENTITY RESOLUTION</div>'
        '<div class="kpi-val">0 Duplicates</div><div class="kpi-sub">Pat Cummins = Patrick Cummins (ID 1758)</div></div>',
        unsafe_allow_html=True,
    )
    q3.markdown(
        '<div class="kpi-card"><div class="kpi-label">RR DECOUPLING</div>'
        '<div class="kpi-val">100% Isolated</div><div class="kpi-sub">Scouting never alters Universal Top 10</div></div>',
        unsafe_allow_html=True,
    )


def _dumbbell_chart(df: pd.DataFrame, is_bowler: bool, title: str) -> go.Figure:
    """Normal -> High-Stress Dumbbell Shift in natural positive cricket units."""
    plot_df = df.sort_values("shortlist_rank_display", ascending=False).copy()
    if is_bowler:
        # Convert negative suppression units back to positive batter-runs conceded/100b
        lo_vals = -plot_df["raw_lo_perf"]
        hi_vals = -plot_df["raw_hi_perf"]
        lo_lbl = "Normal Baseline (Runs Conceded/100b)"
        hi_lbl = "High-Threat (Runs Conceded/100b)"
        x_title = "Batter Runs Conceded per 100 Legal Balls (lower = tighter)"
    else:
        lo_vals = plot_df["raw_lo_perf"]
        hi_vals = plot_df["raw_hi_perf"]
        lo_lbl = "Normal Baseline (Strike Rate)"
        hi_lbl = "High-Stress (Strike Rate)"
        x_title = "Batting Strike Rate (Runs per 100 Balls Faced)"

    fig = go.Figure()
    for name, x0, x1 in zip(plot_df["player_name"], lo_vals, hi_vals):
        if pd.notna(x0) and pd.notna(x1):
            fig.add_trace(
                go.Scatter(
                    x=[x0, x1],
                    y=[name, name],
                    mode="lines",
                    line=dict(color="#CBD5E1", width=3),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
    fig.add_trace(
        go.Scatter(
            x=lo_vals,
            y=plot_df["player_name"],
            mode="markers",
            name=lo_lbl,
            marker=dict(color="#64748B", size=10),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hi_vals,
            y=plot_df["player_name"],
            mode="markers",
            name=hi_lbl,
            marker=dict(color=RR_PINK, size=11, symbol="diamond"),
        )
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, font=dict(color=NAVY, size=14)),
        xaxis=dict(title=x_title, title_font=dict(color=NAVY), tickfont=dict(color=NAVY), gridcolor="#E2E8F0"),
        yaxis=dict(tickfont=dict(color=NAVY), gridcolor="#F1F5F9"),
        height=390,
        margin=dict(l=10, r=10, t=48, b=10),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color=NAVY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=NAVY, size=11)),
    )
    return fig


def _eb_forest_chart(df: pd.DataFrame, mu0: float, title: str) -> go.Figure:
    """EB Delta Forest Plot with 95% Bootstrap CI and Cohort Mean mu0 reference line."""
    plot_df = df.sort_values("shortlist_rank_display", ascending=False).copy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=plot_df["eb_delta"],
            y=plot_df["player_name"],
            mode="markers",
            name="EB Δ (FWL + REML)",
            marker=dict(color=NAVY, size=10),
            error_x=dict(
                type="data",
                symmetric=False,
                array=(plot_df["eb_boot_ci_high"] - plot_df["eb_delta"]).fillna(0).clip(lower=0),
                arrayminus=(plot_df["eb_delta"] - plot_df["eb_boot_ci_low"]).fillna(0).clip(lower=0),
                color="#94A3B8",
                thickness=1.8,
            ),
        )
    )
    fig.add_vline(
        x=mu0,
        line_width=2,
        line_dash="dash",
        line_color=RR_PINK,
        annotation_text=f"Cohort Mean μ₀ = {mu0:.2f}",
        annotation_position="top left",
        annotation_font=dict(color=RR_PINK, size=11),
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, font=dict(color=NAVY, size=14)),
        xaxis=dict(
            title="EB Δ (95% Match-Cluster Bootstrap CI; right of μ₀ = outperforms cohort)",
            title_font=dict(color=NAVY),
            tickfont=dict(color=NAVY),
            gridcolor="#E2E8F0",
        ),
        yaxis=dict(tickfont=dict(color=NAVY), gridcolor="#F1F5F9"),
        height=390,
        margin=dict(l=10, r=10, t=48, b=10),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color=NAVY),
        showlegend=False,
    )
    return fig


def _render_top10_discipline(df: pd.DataFrame, discipline_label: str, filename: str) -> None:
    is_bowler = discipline_label == "Bowlers"
    mu0 = BOWL_MU0 if is_bowler else BAT_MU0

    f1, f2, f3, f4 = st.columns([2, 1.5, 1.5, 2])
    search_q = f1.text_input(f"Filter {discipline_label} by name", key=f"search_{discipline_label}")
    conf_filter = f2.selectbox(
        "Sample Confidence",
        ["All", "HIGH", "MODERATE", "PROVISIONAL_BOUNDARY"],
        key=f"conf_{discipline_label}",
    )
    tradeoff_filter = f3.selectbox(
        "Tradeoff Flag",
        ["All", "Clean Only", "Flagged Only"],
        key=f"trade_{discipline_label}",
    )
    sort_col = f4.selectbox(
        "Sort By",
        ["Official Rank (EB Δ)", "Raw High−Low Δ", "P(Top 10)", "Common-Support Matches"],
        key=f"sort_{discipline_label}",
    )

    view = df.copy()
    if search_q.strip():
        view = view[view["player_name"].str.contains(search_q.strip(), case=False, na=False)]
    if conf_filter != "All":
        view = view[view["sample_confidence"].astype(str).str.upper() == conf_filter]
    if tradeoff_filter == "Clean Only":
        view = view[view["secondary_tradeoff_flag"].astype(str).str.lower() == "none"]
    elif tradeoff_filter == "Flagged Only":
        view = view[view["secondary_tradeoff_flag"].astype(str).str.lower() != "none"]

    if sort_col == "Official Rank (EB Δ)":
        view = view.sort_values("shortlist_rank_display", ascending=True)
    elif sort_col == "Raw High−Low Δ":
        view = view.sort_values("raw_hi_minus_lo", ascending=False)
    elif sort_col == "P(Top 10)":
        view = view.sort_values("prob_top_10", ascending=False)
    else:
        view = view.sort_values("cs_matches", ascending=False)

    if view.empty:
        st.warning("No shortlisted players match the current filter selection.")
        return

    lo_col = "Raw Lo (-Runs/100b)" if is_bowler else "Raw Lo (Runs/100b)"
    hi_col = "Raw Hi (-Runs/100b)" if is_bowler else "Raw Hi (Runs/100b)"
    disp = pd.DataFrame(
        {
            "Rank": view["shortlist_rank_display"].apply(fmt_int),
            "Player": view["player_name"],
            "Matches": view["cs_matches"].apply(fmt_int),
            "High-Stress Balls": view["n_hi"].apply(fmt_int),
            lo_col: view["raw_lo_perf"].apply(fmt_num),
            hi_col: view["raw_hi_perf"].apply(fmt_num),
            "Raw High−Low Δ": view["raw_hi_minus_lo"].apply(fmt_num),
            "EB Δ": view["eb_delta"].apply(fmt_num),
            "EB vs Pop μ₀": view["eb_vs_pop_mean_delta"].apply(lambda x: fmt_num(x, "{:+.2f}")),
            "95% Boot CI": view.apply(
                lambda r: f"[{fmt_num(r['eb_boot_ci_low'])}, {fmt_num(r['eb_boot_ci_high'])}]", axis=1
            ),
            "P(Top 10)": view["prob_top_10"].apply(lambda x: fmt_num(x, "{:.3f}")),
            "Confidence": view["sample_confidence"],
            "Tradeoff": view["secondary_tradeoff_flag"],
        }
    )
    st.dataframe(disp, use_container_width=True, hide_index=True)

    c_left, c_right = st.columns(2)
    with c_left:
        st.plotly_chart(
            _dumbbell_chart(view, is_bowler=is_bowler, title="Normal vs High-Stress Shift (Raw Baseline)"),
            use_container_width=True,
        )
    with c_right:
        st.plotly_chart(
            _eb_forest_chart(view, mu0=mu0, title="Adjusted EB Δ vs Cohort Mean (μ₀)"),
            use_container_width=True,
        )

    # Selected-Player Scouting Dossier (replaces 10 stacked expanders)
    st.markdown(f"#### {discipline_label[:-1]} Scouting Dossier")
    pick_name = st.selectbox(
        f"Inspect full justification & match consistency for a shortlisted {discipline_label[:-1].lower()}",
        view["player_name"].tolist(),
        key=f"dossier_{discipline_label}",
    )
    r = view[view["player_name"] == pick_name].iloc[0]
    cons_pct = fmt_num(r["claim_b_high_stress_pos_share"] * 100, "{:.1f}%") if pd.notna(r["claim_b_high_stress_pos_share"]) else "Unavailable"
    st.markdown(
        f"""
        <div class="dossier-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>{initials_badge(r['player_name'])} <b style="font-size:17px; color:{NAVY};">#{int(r['shortlist_rank_display'])} {r['player_name']}</b>
                <span style="color:{TEXT_MUTED}; font-size:13px;"> (ID {int(r['player_id'])} | {r['sample_confidence']})</span></div>
                <span style="font-weight:700; color:{TEAL_POS};">EB vs Pop μ₀: {fmt_num(r['eb_vs_pop_mean_delta'], '{:+.2f}')}</span>
            </div>
            <p style="margin:10px 0 6px 0; font-size:13.5px;">
                <b>Normal Baseline:</b> {fmt_num(r['raw_lo_perf'])} &nbsp;|&nbsp;
                <b>High-Stress:</b> {fmt_num(r['raw_hi_perf'])} &nbsp;|&nbsp;
                <b>EB Δ:</b> {fmt_num(r['eb_delta'])} &nbsp;|&nbsp;
                <b>Boot Rank 95% CI:</b> [{fmt_int(r['boot_rank_ci_low'])}, {fmt_int(r['boot_rank_ci_high'])}] &nbsp;|&nbsp;
                <b>Within-Match Consistency:</b> {cons_pct}
            </p>
            <p style="margin:0; font-size:13.5px; color:{TEXT_MAIN};">{r['player_explanation']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        label=f"Download {filename}",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=f"dl_{filename}",
    )


def render_top10() -> None:
    st.subheader("Universal Top 10 Leaderboards (Official Deliverable)")
    st.caption(
        "Positive EB Δ indicates improvement under high stress vs own baseline. Because high-stress states depress scoring across the cohort "
        "(μ₀ = -36.12 batters, -50.88 bowlers), all 20 leaders have negative absolute EB Δ (-29.39 to -43.71) and are ranked by smallest deterioration relative to μ₀."
    )
    tab_bat, tab_bowl = st.tabs(["Top 10 Batters", "Top 10 Bowlers"])
    with tab_bat:
        _render_top10_discipline(D["top_bat"], "Batters", "FINAL_TOP_10_BATTERS.csv")
    with tab_bowl:
        _render_top10_discipline(D["top_bowl"], "Bowlers", "FINAL_TOP_10_BOWLERS.csv")


def render_explorer() -> None:
    st.subheader("Player Explorer & Same-Discipline Comparison")
    all_est = D["all_est"].copy()

    c1, c2, c3 = st.columns([1.4, 1.4, 3.2])
    disc = c1.selectbox("Discipline", ["All", "batter", "bowler"])
    elig_opt = c2.selectbox("Eligibility", ["All", "Eligible Only", "Ineligible Only"])

    pool = all_est.copy()
    if disc != "All":
        pool = pool[pool["role"] == disc]
    if elig_opt == "Eligible Only":
        pool = pool[pool["eligible"] == True]
    elif elig_opt == "Ineligible Only":
        pool = pool[pool["eligible"] == False]

    pool = pool.sort_values(["role", "eb_rank", "total_balls"], ascending=[True, True, False], na_position="last")
    pool["label"] = pool.apply(
        lambda r: f"{r['player_name']} ({r['role']} | {'Eligible #' + fmt_int(r['eb_rank']) if r['eligible'] else 'Ineligible'})",
        axis=1,
    )
    options = pool["label"].tolist()
    default_idx = next((i for i, lbl in enumerate(options) if "Virat Kohli" in lbl), 0)
    selected_lbl = c3.selectbox(
        "Search any player (e.g., Virat Kohli, MS Dhoni, Jasprit Bumrah, Patrick Cummins)",
        options,
        index=default_idx if options else 0,
    )

    if selected_lbl:
        row = pool[pool["label"] == selected_lbl].iloc[0]
        st.markdown(
            f"### {initials_badge(row['player_name'])} {row['player_name']} ({row['role'].title()})",
            unsafe_allow_html=True,
        )
        m_cards = [
            ("ELIGIBILITY", "Eligible" if row["eligible"] else "Ineligible", f"Role: {row['role']}"),
            ("GLOBAL EB RANK", fmt_int(row["eb_rank"]), "Within-discipline"),
            ("EB Δ (WITHIN-PLAYER)", fmt_num(row["eb_delta"]), "Complete FWL + REML"),
            ("EB vs Pop μ₀", fmt_num(row["eb_vs_pop_mean_delta"], "{:+.2f}"), "Relative to cohort mean"),
        ]
        for col, (lbl, val, sub) in zip(st.columns(4), m_cards):
            col.markdown(
                f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
                f'<div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        d_cards = [
            ("P(TOP 10)", fmt_num(row["prob_top_10"], "{:.3f}"), "Bootstrap probability"),
            ("RAW OVERALL", fmt_num(row["raw_overall_perf"]), "All regular balls"),
            ("NORMAL BASELINE", fmt_num(row["raw_lo_perf"]), "Low-stress tier"),
            ("HIGH-STRESS PERF", fmt_num(row["raw_hi_perf"]), f"{fmt_int(row['n_hi'])} balls / {fmt_int(row['cs_matches'])} matches"),
        ]
        for col, (lbl, val, sub) in zip(st.columns(4), d_cards):
            col.markdown(
                f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
                f'<div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

        if not row["eligible"]:
            st.warning(f"Exclusion Reason: {row['exclusion_reason']}")
        elif pd.notna(row["shortlist_rank_display"]):
            st.success(f"Universal Top 10 Member: Ranked #{int(row['shortlist_rank_display'])} among eligible {row['role']}s.")
        else:
            st.info(
                f"Eligible outside Top 10 (Rank #{fmt_int(row['eb_rank'])}) — "
                f"95% Boot CI [{fmt_num(row['eb_boot_ci_low'])}, {fmt_num(row['eb_boot_ci_high'])}], "
                f"Rank CI [{fmt_int(row['boot_rank_ci_low'])}, {fmt_int(row['boot_rank_ci_high'])}]."
            )

    st.markdown("---")
    st.markdown("### Same-Discipline Comparison (2–4 Players)")
    cmp_role = st.radio("Comparison Discipline", ["batter", "bowler"], horizontal=True)
    cmp_pool = all_est[(all_est["role"] == cmp_role) & (all_est["eligible"] == True)].sort_values("eb_rank")
    default_picks = ["David Miller", "Andre Russell", "Virat Kohli"] if cmp_role == "batter" else ["Matheesha Pathirana", "Jasprit Bumrah", "Patrick Cummins"]

    selected_names = st.multiselect(
        f"Pick 2 to 4 eligible {cmp_role}s",
        cmp_pool["player_name"].tolist(),
        default=[p for p in default_picks if p in cmp_pool["player_name"].values][:3],
        max_selections=4,
    )
    if len(selected_names) >= 2:
        sub = cmp_pool[cmp_pool["player_name"].isin(selected_names)].copy()
        sub["shortlist_rank_display"] = sub["eb_rank"]  # reuse dumbbell helper cleanly
        is_bowl = cmp_role == "bowler"
        mu0 = BOWL_MU0 if is_bowl else BAT_MU0
        c_l, c_r = st.columns(2)
        with c_l:
            st.plotly_chart(
                _dumbbell_chart(sub, is_bowler=is_bowl, title=f"Normal vs High-Stress Shift ({cmp_role.title()}s)"),
                use_container_width=True,
            )
        with c_r:
            st.plotly_chart(
                _eb_forest_chart(sub, mu0=mu0, title=f"Adjusted EB Δ vs Cohort Mean ({cmp_role.title()}s)"),
                use_container_width=True,
            )

        cmp_disp = pd.DataFrame(
            {
                "Player": sub["player_name"],
                "EB Rank": sub["eb_rank"].apply(fmt_int),
                "Matches": sub["cs_matches"].apply(fmt_int),
                "High-Stress Balls": sub["n_hi"].apply(fmt_int),
                "Normal Baseline": sub["raw_lo_perf"].apply(fmt_num),
                "High-Stress Perf": sub["raw_hi_perf"].apply(fmt_num),
                "Raw High−Low Δ": sub["raw_hi_minus_lo"].apply(fmt_num),
                "EB Δ": sub["eb_delta"].apply(fmt_num),
                "EB vs Pop μ₀": sub["eb_vs_pop_mean_delta"].apply(lambda x: fmt_num(x, "{:+.2f}")),
                "P(Top 10)": sub["prob_top_10"].apply(lambda x: fmt_num(x, "{:.3f}")),
            }
        )
        st.dataframe(cmp_disp, use_container_width=True, hide_index=True)
    else:
        st.info("Select at least 2 players to render comparison charts.")

    with st.expander("Star-Player Eligibility Audit (21 Audited IPL/International Stars)"):
        sa = D["star_audit"]
        sa_disp = pd.DataFrame(
            {
                "Player": sa["player_name"],
                "Discipline": sa["discipline"],
                "Canonical ID": sa["canonical_player_id"].apply(fmt_int),
                "Eligible": sa["eligible"],
                "EB Rank": sa["eb_rank"].apply(fmt_int),
                "High-Stress Balls": sa["n_hi"].apply(fmt_int),
                "Matches": sa["cs_matches"].apply(fmt_int),
                "EB Δ": sa["eb_delta"].apply(fmt_num),
                "Exclusion / Status": sa["exclusion_reason"].fillna("Eligible"),
                "Audit Explanation": sa["explanation"],
            }
        )
        st.dataframe(sa_disp, use_container_width=True, hide_index=True)


def render_rr() -> None:
    st.subheader("Rajasthan Royals Intelligence (Secondary Application)")
    st.markdown(
        '<div class="status-strip"><b>Strict Decoupling:</b> RR scouting evaluates both Universal Top 10 leaders and eligible specialists outside the Top 10 '
        'using V4.2 complete-FWL estimates plus phase and pace/spin profiles. It never alters Universal Top 10 ranks.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### RR 2026 Team Weaknesses")
        st.dataframe(D["rr_2026_wk"], use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### RR 2026 Team Strengths")
        st.dataframe(D["rr_2026_str"], use_container_width=True, hide_index=True)

    st.markdown("#### Tactical Gaps & Scouting Requirements")
    req_disp = D["rr_req"].rename(
        columns={
            "priority": "Priority",
            "role_title": "Target Role",
            "urgency": "Urgency",
            "tactical_objective": "Tactical Objective",
            "existing_rr_cover": "Existing RR Cover",
            "budget_allocation_cr": "Target Allocation (Cr)",
            "scouting_priority_weight": "Weight",
        }
    )[["Priority", "Target Role", "Urgency", "Tactical Objective", "Existing RR Cover", "Target Allocation (Cr)", "Weight"]]
    st.dataframe(req_disp, use_container_width=True, hide_index=True)

    weight_mode = st.selectbox(
        "RR Fit Weight Sensitivity Profile",
        [
            "Baseline (35% Phase / 25% Role Need / 20% V4.2 Pressure / 10% Confidence / 10% T20 Balance)",
            "Pressure-Heavy (25% Phase / 20% Role Need / 35% V4.2 Pressure / 10% Confidence / 10% T20 Balance)",
            "Role-Heavy (40% Phase / 35% Role Need / 10% V4.2 Pressure / 10% Confidence / 5% T20 Balance)",
        ],
    )
    score_col = (
        "RR_PLAYER_FIT_SCORE"
        if weight_mode.startswith("Baseline")
        else ("fit_score_pressure_heavy" if weight_mode.startswith("Pressure-Heavy") else "fit_score_role_heavy")
    )

    # Stacked RR Fit Component Chart (top 10 combined non-RR candidates)
    top_pool = pd.concat([D["rr_top10"][~D["rr_top10"]["already_rr_2026"]], D["rr_outside"]], ignore_index=True)
    top_pool = top_pool.sort_values(score_col, ascending=False).head(10).iloc[::-1]
    fig_rr = go.Figure()
    for col_name, lbl, clr in [
        ("phase_exec_score", "Phase Execution", NAVY),
        ("role_need_score", "Tactical Role Need", NAVY_MID),
        ("pressure_v42_score", "V4.2 Pressure", RR_PINK),
        ("sample_conf_score", "Sample Confidence", "#64748B"),
        ("balance_ipl_score", "T20 Exposure", "#94A3B8"),
    ]:
        fig_rr.add_trace(go.Bar(name=lbl, y=top_pool["player_name"], x=top_pool[col_name], orientation="h", marker_color=clr))
    fig_rr.update_layout(
        template="plotly_white",
        barmode="stack",
        title=dict(text="Top 10 Non-RR Scouting Targets — Component Breakdown", font=dict(color=NAVY, size=14)),
        xaxis=dict(title="Component Score Sum (Unweighted Diagnostic)", title_font=dict(color=NAVY), tickfont=dict(color=NAVY), gridcolor="#E2E8F0"),
        yaxis=dict(tickfont=dict(color=NAVY)),
        height=370,
        margin=dict(l=10, r=10, t=46, b=10),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color=NAVY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=NAVY, size=11)),
    )
    st.plotly_chart(fig_rr, use_container_width=True)

    t1, t2, t3 = st.tabs(
        [
            "Universal Top 10 RR Fit",
            "Best Outside-Top-10 RR Fits",
            "Recommended Balanced RR Shortlist",
        ]
    )
    with t1:
        df1 = D["rr_top10"].sort_values(score_col, ascending=False)
        disp1 = pd.DataFrame(
            {
                "Player": df1["player_name"],
                "Role": df1["role"].str.title(),
                "Top-10 Rank": df1["shortlist_rank_display"].apply(fmt_int),
                "RR Target Role": df1["rr_target_role"],
                "RR 2026?": df1["already_rr_2026"].map({True: "Yes", False: "No"}),
                "EB Δ": df1["eb_delta"].apply(fmt_num),
                "Phase Score": df1["phase_exec_score"].apply(lambda x: fmt_num(x, "{:.1f}")),
                "RR Fit Score": df1[score_col].apply(fmt_num),
            }
        )
        st.dataframe(disp1, use_container_width=True, hide_index=True)
    with t2:
        df2 = D["rr_outside"].sort_values(score_col, ascending=False)
        disp2 = pd.DataFrame(
            {
                "Player": df2["player_name"],
                "Role": df2["role"].str.title(),
                "Global Rank": df2["eb_rank"].apply(fmt_int),
                "RR Target Role": df2["rr_target_role"],
                "EB Δ": df2["eb_delta"].apply(fmt_num),
                "RR Fit Score": df2[score_col].apply(fmt_num),
                "Tactical Fit Rationale": df2["why_better_rr_fit_than_some_top10"],
            }
        )
        st.dataframe(disp2, use_container_width=True, hide_index=True)
    with t3:
        df3 = D["rr_squad"]
        disp3 = pd.DataFrame(
            {
                "Player": df3["player_name"],
                "Discipline": df3["role"].str.title(),
                "Source Pool": df3["selection_pool"],
                "Squad Role": df3["squad_role"],
                "Global Rank": df3["eb_rank"].apply(fmt_int),
                "EB Δ": df3["eb_delta"].apply(fmt_num),
                "RR Fit Score": df3["RR_PLAYER_FIT_SCORE"].apply(fmt_num),
            }
        )
        st.dataframe(disp3, use_container_width=True, hide_index=True)

    st.caption(
        "Auction Assumptions Disclosure: Purse constraints and player availability remain unverified external assumptions "
        "stored in `data/reference/rr_2027_auction_assumptions.csv` and kept strictly configurable."
    )


def render_methodology() -> None:
    st.subheader("Methodology, Validation & Artifact Provenance")
    st.markdown(
        """
        - **Primary Estimator (`OPTION_A_COMPLETE_PENALIZED_FWL_REML`):** Residualizes both the ball-by-ball outcome `y` and the resource-stress/scoring-threat predictor `p` against identical state, match, player, and opponent nuisance designs, then applies REML Empirical Bayes shrinkage across eligible players.
        - **`EB Δ` vs `EB vs Pop μ₀`:** `EB vs Pop μ₀ = EB Δ − μ₀` measures each player's deviation from the pooled eligible cohort stress tax (`μ₀ = -36.12` batters; `-50.88` bowlers). Across all 20 shortlisted batters and bowlers, `EB vs Pop μ₀` is positive while their `absolute effect remains negative`.
        - **Operational Eligibility Gate:** `n_hi >= 50`, `n_lo >= 30`, `cs_matches >= 8`, and `se_delta <= 25.0`.
        """
    )

    st.markdown("#### 1. Pressure Methodology Comparison")
    mc = D["method_cmp"]
    mc_disp = pd.DataFrame(
        {
            "Methodology": mc["methodology_id"],
            "Discipline": mc["discipline"],
            "Eligible": mc["eligible_players"].apply(fmt_int),
            "REML μ₀": mc["reml_mu0"].apply(fmt_num),
            "REML τ": mc["reml_tau"].apply(fmt_num),
            "I² (%)": mc["reml_i2_pct"].apply(lambda x: fmt_num(x, "{:.1f}%")),
            "OOT ρ": mc["oot_claim_c_rho"].apply(lambda x: fmt_num(x, "{:.3f}")),
            "Spearman vs V4.2": mc["spearman_vs_v42_baseline"].apply(lambda x: fmt_num(x, "{:.3f}")),
            "Status": mc["selection_status"],
        }
    )
    st.dataframe(mc_disp, use_container_width=True, hide_index=True)

    st.markdown("#### 2. Chase-Score Reconstruction Audit (`MARGIN_MISMATCH_BLOCKED`)")
    st.dataframe(D["score_audit"], use_container_width=True, hide_index=True)

    st.markdown("#### 3. Out-of-Time & Robustness Validation Matrix")
    st.dataframe(D["val_matrix"], use_container_width=True, hide_index=True)

    st.markdown("#### 4. Authoritative Artifact Provenance (`FINAL_RANKING_SOURCE_OF_TRUTH.json`)")
    sot = D["sot"]
    prov_rows = [
        {"Artifact": k, "Scope": "Universal Rankings", "SHA-256": v}
        for k, v in sot.get("hashes", {}).items()
    ] + [
        {"Artifact": k, "Scope": "RR Secondary Module", "SHA-256": v}
        for k, v in sot.get("rr_hashes", {}).items()
    ]
    st.dataframe(pd.DataFrame(prov_rows), use_container_width=True, hide_index=True)


if section.startswith("1."):
    render_overview()
elif section.startswith("2."):
    render_top10()
elif section.startswith("3."):
    render_explorer()
elif section.startswith("4."):
    render_rr()
else:
    render_methodology()
