"""SupeRR Intelligence V4.2 — Streamlit Dashboard (Final Submission UI).

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
TEXT_MUTED = "#475569"
GREEN_POS = "#0F766E"
RED_NEG = "#B91C1C"


st.set_page_config(
    page_title="SupeRR Intelligence V4.2",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {SLATE_BG};
        color: #0F172A;
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
        color: {NAVY} !important;
    }}
    .stApp p, .stApp li, .stApp label, .stApp span,
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
    button[data-baseweb="tab"] p {{
        color: #0F172A !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {NAVY};
        color: #FFFFFF;
    }}
    section[data-testid="stSidebar"] * {{
        color: #F8FAFC !important;
    }}
    .superr-header {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-left: 6px solid {NAVY};
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 16px;
    }}
    .superr-badge {{
        display: inline-block;
        background: #FDF2F8;
        color: {RR_PINK};
        border: 1px solid #FBCFE8;
        font-weight: 700;
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 999px;
        letter-spacing: 0.4px;
    }}
    .kpi-card {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-radius: 10px;
        padding: 14px 16px;
        height: 100%;
    }}
    .kpi-label {{
        font-size: 12px;
        font-weight: 600;
        color: {TEXT_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }}
    .kpi-val {{
        font-size: 24px;
        font-weight: 800;
        color: {NAVY};
        margin: 4px 0 2px 0;
    }}
    .kpi-sub {{
        font-size: 12px;
        color: {TEXT_MUTED};
    }}
    .avatar-circle {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: {NAVY};
        color: #FFFFFF;
        font-weight: 700;
        font-size: 13px;
        margin-right: 10px;
        border: 2px solid {RR_PINK};
    }}
    .notice-box {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-left: 4px solid {RR_PINK};
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
        font-size: 14px;
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
    data: dict[str, Any] = {
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
        "rr_2026_contrib": pd.read_csv(V3_DIR / "rr_2026_player_contribution.csv"),
    }
    return data


D = load_all_data()

# Sidebar navigation
st.sidebar.markdown("## 🏏 SupeRR Intelligence")
st.sidebar.caption("V4.2 PROVISIONAL — RESOURCE STRESS")
section = st.sidebar.radio(
    "Navigate",
    [
        "1. Overview",
        "2. Universal Top 10",
        "3. Player Explorer & Comparison",
        "4. Rajasthan Royals Intelligence",
        "5. Methodology & Transparency",
    ],
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Official Objective**\n\n"
    "Identify batters and bowlers who perform most consistently under pressure "
    "compared with their own usual performance levels."
)
st.sidebar.markdown("---")
st.sidebar.caption("Authoritative outputs: `data/outputs/final/`\n\nRR scouting is secondary and never alters Universal Top 10.")


# Top Header Banner
st.markdown(
    """
    <div class="superr-header">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
                <h1 style="margin:0; font-size:26px; color:#0B1B3D;">SupeRR Intelligence</h1>
                <p style="margin:4px 0 0 0; color:#475569; font-size:14px;">
                    Official Objective: Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels.
                </p>
            </div>
            <span class="superr-badge">V4.2 PROVISIONAL — RESOURCE STRESS</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def render_overview() -> None:
    all_est = D["all_est"]
    elig_bat = all_est[(all_est["role"] == "batter") & (all_est["eligible"] == True)]
    elig_bowl = all_est[(all_est["role"] == "bowler") & (all_est["eligible"] == True)]

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("Dataset Coverage", "837 Matches", "193,988 regular + 26 Super Over balls"),
        ("Eligible Batters", f"{len(elig_bat)}", "10 shortlisted (n_hi≥50, ≥10 matches)"),
        ("Eligible Bowlers", f"{len(elig_bowl)}", "10 shortlisted (n_hi≥50, ≥10 matches)"),
        ("Primary Estimator", "Complete FWL", "Option A Penalized FWL + REML EB"),
    ]
    for col, (lbl, val, sub) in zip([c1, c2, c3, c4], kpis):
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
            f'<div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="notice-box">
            <b>Provisional Resource-Stress Disclosure:</b> Because <code>ball_by_ball_ipl_t20i.csv</code> does not include verified cumulative match scores,
            chased targets, or required run rates (342/390 chase reconstructions fail margin checks as <code>MARGIN_MISMATCH_BLOCKED</code>),
            V4.2 measures <b>BATTING_RESOURCE_STRESS</b> (wicket-depletion anomaly) and <b>BOWLING_SCORING_THREAT</b> (expected scoring environment)
            rather than a calibrated Win-Probability / Chase-Leverage index.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_b, col_w = st.columns(2)
    with col_b:
        st.subheader("Top 5 Universal Batters (Preview)")
        top_b = D["top_bat"].head(5)
        for _, r in top_b.iterrows():
            st.markdown(
                f"{initials_badge(r['player_name'])} **#{int(r['shortlist_rank_display'])} {r['player_name']}** "
                f"— `EB Δ: {fmt_num(r['eb_delta'])}` | `EB vs Pop μ₀: {fmt_num(r['eb_vs_pop_mean_delta'])}` | "
                f"Matches: `{fmt_int(r['cs_matches'])}` ({r['sample_confidence']})",
                unsafe_allow_html=True,
            )

    with col_w:
        st.subheader("Top 5 Universal Bowlers (Preview)")
        top_w = D["top_bowl"].head(5)
        for _, r in top_w.iterrows():
            st.markdown(
                f"{initials_badge(r['player_name'])} **#{int(r['shortlist_rank_display'])} {r['player_name']}** "
                f"— `EB Δ: {fmt_num(r['eb_delta'])}` | `EB vs Pop μ₀: {fmt_num(r['eb_vs_pop_mean_delta'])}` | "
                f"Matches: `{fmt_int(r['cs_matches'])}` ({r['sample_confidence']})",
                unsafe_allow_html=True,
            )

    st.markdown("### Key Data-Quality & Identity Verifications")
    st.markdown(
        "- **Super Over Isolation:** 26 Super Over deliveries (`innings > 2`) isolated from regular-innings pressure estimation.\n"
        "- **Identity Normalization:** Zero duplicate `(match_id, innings, overid, over_ball_num, innings_ball_num)` regular balls; `Pat Cummins` resolved cleanly to `Patrick Cummins` (`player_id = 1758`, eligible `#101 / 136`).\n"
        "- **Universal vs RR Separation:** Rajasthan Royals scouting (Section 4) is strictly secondary and never influences Universal Top 10 ranks."
    )


def _render_top10_discipline(df: pd.DataFrame, discipline_label: str, filename: str) -> None:
    f1, f2, f3, f4 = st.columns([2, 1.5, 1.5, 2])
    search_q = f1.text_input(f"Filter {discipline_label} by name", key=f"search_{discipline_label}")
    conf_filter = f2.selectbox(
        "Sample Confidence",
        ["All", "High", "Moderate", "Exploratory"],
        key=f"conf_{discipline_label}",
    )
    tradeoff_filter = f3.selectbox(
        "Tradeoff Flag",
        ["All", "Clean Only", "Flagged Only"],
        key=f"trade_{discipline_label}",
    )
    sort_col = f4.selectbox(
        "Sort By",
        ["Official Rank (EB Δ)", "Raw High−Low Δ", "P(Top 10)", "Matches (cs_matches)"],
        key=f"sort_{discipline_label}",
    )

    view = df.copy()
    if search_q.strip():
        view = view[view["player_name"].str.contains(search_q.strip(), case=False, na=False)]
    if conf_filter != "All":
        view = view[view["sample_confidence"].astype(str).str.lower() == conf_filter.lower()]
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

    # Formatted table
    lo_col = "Raw Lo (-Runs/100b)" if discipline_label == "Bowlers" else "Raw Lo (Runs/100b)"
    hi_col = "Raw Hi (-Runs/100b)" if discipline_label == "Bowlers" else "Raw Hi (Runs/100b)"
    disp = pd.DataFrame(
        {
            "Rank": view["shortlist_rank_display"].apply(fmt_int),
            "Player": view["player_name"],
            "Matches": view["cs_matches"].apply(fmt_int),
            "High-Stress Balls": view["n_hi"].apply(fmt_int),
            lo_col: view["raw_lo_perf"].apply(fmt_num),
            hi_col: view["raw_hi_perf"].apply(fmt_num),
            "Raw High−Low Δ": view["raw_hi_minus_lo"].apply(fmt_num),
            "EB Δ (Within-Player)": view["eb_delta"].apply(fmt_num),
            "EB vs Pop μ₀": view["eb_vs_pop_mean_delta"].apply(fmt_num),
            "95% Boot CI": view.apply(
                lambda r: f"[{fmt_num(r['eb_boot_ci_low'])}, {fmt_num(r['eb_boot_ci_high'])}]", axis=1
            ),
            "P(Top 10)": view["prob_top_10"].apply(lambda x: fmt_num(x, "{:.3f}")),
            "Confidence": view["sample_confidence"],
            "Tradeoff": view["secondary_tradeoff_flag"],
        }
    )
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # Interactive Plotly Chart: EB Delta vs Raw High-Low Delta with Bootstrap CI
    fig = go.Figure()
    plot_df = view.sort_values("shortlist_rank_display", ascending=False)
    fig.add_trace(
        go.Bar(
            y=plot_df["player_name"],
            x=plot_df["eb_delta"],
            orientation="h",
            name="EB Δ (Complete FWL + REML)",
            marker_color=NAVY,
            error_x=dict(
                type="data",
                symmetric=False,
                array=(plot_df["eb_boot_ci_high"] - plot_df["eb_delta"]).fillna(0).clip(lower=0),
                arrayminus=(plot_df["eb_delta"] - plot_df["eb_boot_ci_low"]).fillna(0).clip(lower=0),
                color=RR_PINK,
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            y=plot_df["player_name"],
            x=plot_df["raw_hi_minus_lo"],
            mode="markers",
            name="Raw High−Low Δ",
            marker=dict(color=RR_PINK, size=9, symbol="diamond"),
        )
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"{discipline_label} Top 10: EB Δ (with 95% Match-Cluster Bootstrap CI) vs Raw High−Low Δ",
            font=dict(color=NAVY, size=15),
        ),
        xaxis=dict(
            title="Outcome Delta (Runs/100 balls; negated for bowlers so positive = better)",
            title_font=dict(color=NAVY),
            tickfont=dict(color=NAVY),
            gridcolor="#E2E8F0",
        ),
        yaxis=dict(tickfont=dict(color=NAVY), gridcolor="#E2E8F0"),
        height=390,
        margin=dict(l=10, r=10, t=48, b=10),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color=NAVY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=NAVY)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Expandable Player Justifications
    st.markdown(f"#### Why Each {discipline_label[:-1]} Belongs in the Universal Top 10")
    for _, r in view.iterrows():
        with st.expander(
            f"#{int(r['shortlist_rank_display'])} {r['player_name']} — EB Δ {fmt_num(r['eb_delta'])} | "
            f"EB vs Pop μ₀ {fmt_num(r['eb_vs_pop_mean_delta'])} | {r['sample_confidence']} Confidence"
        ):
            st.markdown(
                f"{initials_badge(r['player_name'])} **Player ID:** `{int(r['player_id'])}` | "
                f"**Matches:** `{fmt_int(r['cs_matches'])}` | **High-Stress Balls:** `{fmt_int(r['n_hi'])}` | "
                f"**Boot Rank 95% CI:** `[{fmt_int(r['boot_rank_ci_low'])}, {fmt_int(r['boot_rank_ci_high'])}]`",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"- **Usual Normal Performance (`raw_lo_perf`):** `{fmt_num(r['raw_lo_perf'])}` | "
                f"**High-Stress Performance (`raw_hi_perf`):** `{fmt_num(r['raw_hi_perf'])}` | "
                f"**Raw High−Low Δ:** `{fmt_num(r['raw_hi_minus_lo'])}`\n"
                f"- **Within-Match Consistency (`claim_b_high_stress_pos_share`):** `{fmt_num(r['claim_b_high_stress_pos_share'] * 100 if pd.notna(r['claim_b_high_stress_pos_share']) else np.nan, '{:.1f}%')}`\n"
                f"- **Justification:** {r['player_explanation']}"
            )

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Download {filename}",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        key=f"dl_{filename}",
    )


def render_top10() -> None:
    st.subheader("Universal Top 10 Leaderboards (Official Deliverable)")
    st.caption(
        "By sign convention, positive EB Δ indicates improvement under high stress vs own baseline. Because high-stress states depress scoring across the entire cohort (μ₀ = -36.12 batters, -50.88 bowlers), all 20 shortlisted leaders still have negative absolute EB Δ (-29.39 to -43.71) and are ranked by smallest deterioration relative to the field (positive EB vs Pop μ₀)."
    )
    tab_bat, tab_bowl = st.tabs(["🏏 Top 10 Batters", "🎯 Top 10 Bowlers"])
    with tab_bat:
        _render_top10_discipline(D["top_bat"], "Batters", "FINAL_TOP_10_BATTERS.csv")
    with tab_bowl:
        _render_top10_discipline(D["top_bowl"], "Bowlers", "FINAL_TOP_10_BOWLERS.csv")


def render_explorer() -> None:
    st.subheader("Player Explorer & Same-Discipline Comparison")
    all_est = D["all_est"].copy()

    c1, c2, c3 = st.columns([1.5, 1.5, 3])
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
    default_idx = 0
    for i, lbl in enumerate(options):
        if "Virat Kohli" in lbl:
            default_idx = i
            break
    selected_lbl = c3.selectbox("Search any player in dataset (e.g., Virat Kohli, MS Dhoni, Jasprit Bumrah, Patrick Cummins)", options, index=default_idx if options else 0)

    if selected_lbl:
        row = pool[pool["label"] == selected_lbl].iloc[0]
        st.markdown(
            f"### {initials_badge(row['player_name'])} {row['player_name']} ({row['role'].title()})",
            unsafe_allow_html=True,
        )
        m_cards = [
            ("Eligibility", "Eligible" if row["eligible"] else "Ineligible", f"Role: {row['role']}"),
            ("Global EB Rank", fmt_int(row["eb_rank"]), "Within-discipline"),
            ("EB Δ (Within-Player)", fmt_num(row["eb_delta"]), "FWL + REML"),
            ("EB vs Pop μ₀", fmt_num(row["eb_vs_pop_mean_delta"]), "Vs cohort mean"),
        ]
        cols1 = st.columns(4)
        for col, (lbl, val, sub) in zip(cols1, m_cards):
            col.markdown(
                f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
                f'<div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        d_cards = [
            ("P(Top 10)", fmt_num(row["prob_top_10"], "{:.3f}"), "Bootstrap share"),
            ("Raw Overall Perf", fmt_num(row["raw_overall_perf"]), "All regular balls"),
            ("Normal Perf (Low Stress)", fmt_num(row["raw_lo_perf"]), "Baseline tier"),
            ("High-Stress Perf", fmt_num(row["raw_hi_perf"]), f"{fmt_int(row['n_hi'])} balls / {fmt_int(row['cs_matches'])} matches"),
        ]
        cols2 = st.columns(4)
        for col, (lbl, val, sub) in zip(cols2, d_cards):
            col.markdown(
                f'<div class="kpi-card"><div class="kpi-label">{lbl}</div>'
                f'<div class="kpi-val">{val}</div><div class="kpi-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

        if not row["eligible"]:
            st.warning(f"**Exclusion Reason:** {row['exclusion_reason']}")
        elif pd.notna(row["shortlist_rank_display"]):
            st.success(f"**Universal Top 10 Member:** Ranked **#{int(row['shortlist_rank_display'])}** among eligible {row['role']}s.")
        else:
            st.info(
                f"**Eligible but Outside Top 10:** Ranked **#{fmt_int(row['eb_rank'])}**; "
                f"95% Boot CI `[{fmt_num(row['eb_boot_ci_low'])}, {fmt_num(row['eb_boot_ci_high'])}]`, "
                f"Rank CI `[{fmt_int(row['boot_rank_ci_low'])}, {fmt_int(row['boot_rank_ci_high'])}]`."
            )

    st.markdown("---")
    st.markdown("### Same-Discipline Player Comparison (2–4 Players)")
    cmp_role = st.radio("Select discipline to compare", ["batter", "bowler"], horizontal=True)
    cmp_pool = all_est[(all_est["role"] == cmp_role) & (all_est["eligible"] == True)].sort_values("eb_rank")
    default_picks = cmp_pool["player_name"].head(3).tolist()
    if cmp_role == "batter" and "Virat Kohli" in cmp_pool["player_name"].values:
        default_picks = ["David Miller", "Andre Russell", "Virat Kohli"]
    elif cmp_role == "bowler" and "Jasprit Bumrah" in cmp_pool["player_name"].values:
        default_picks = ["Matheesha Pathirana", "Jasprit Bumrah", "Patrick Cummins"]

    selected_names = st.multiselect(
        f"Pick 2 to 4 eligible {cmp_role}s",
        cmp_pool["player_name"].tolist(),
        default=[p for p in default_picks if p in cmp_pool["player_name"].values][:3],
        max_selections=4,
    )
    if len(selected_names) >= 2:
        sub = cmp_pool[cmp_pool["player_name"].isin(selected_names)].copy()
        fig = go.Figure()
        for metric, label, color in [
            ("raw_lo_perf", "Normal Baseline (Low Stress)", "#94A3B8"),
            ("raw_hi_perf", "High-Stress Performance", RR_PINK),
            ("eb_delta", "EB Δ (FWL + REML)", NAVY),
        ]:
            fig.add_trace(go.Bar(name=label, x=sub["player_name"], y=sub[metric], marker_color=color))
        fig.update_layout(
            template="plotly_white",
            barmode="group",
            title=dict(text=f"Same-Discipline Comparison ({cmp_role.title()}s)", font=dict(color=NAVY, size=15)),
            xaxis=dict(tickfont=dict(color=NAVY), gridcolor="#E2E8F0"),
            yaxis=dict(tickfont=dict(color=NAVY), gridcolor="#E2E8F0"),
            height=380,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color=NAVY),
            legend=dict(font=dict(color=NAVY)),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            sub[
                [
                    "player_name",
                    "eb_rank",
                    "cs_matches",
                    "n_hi",
                    "raw_lo_perf",
                    "raw_hi_perf",
                    "raw_hi_minus_lo",
                    "eb_delta",
                    "eb_vs_pop_mean_delta",
                    "prob_top_10",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Select at least 2 players to render the comparison chart.")

    with st.expander("Star-Player Audit Lookup (21 Audited IPL/International Stars)"):
        st.dataframe(
            D["star_audit"][
                [
                    "player_name",
                    "discipline",
                    "canonical_player_id",
                    "eligible",
                    "eb_rank",
                    "n_hi",
                    "cs_matches",
                    "raw_hi_minus_lo",
                    "eb_delta",
                    "exclusion_reason",
                    "explanation",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_rr() -> None:
    st.subheader("Rajasthan Royals Intelligence (Secondary Application)")
    st.markdown(
        """
        <div class="notice-box">
            <b>Strict Decoupling Notice:</b> RR squad scouting evaluates <i>both</i> Universal Top 10 leaders and eligible specialists outside the Top 10
            using V4.2 complete-FWL estimates plus phase/pace-spin profiles. It <b>never</b> alters Universal Top 10 ranks.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### RR 2026 Observed Team Weaknesses")
        st.dataframe(D["rr_2026_wk"], use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### RR 2026 Team Strengths")
        st.dataframe(D["rr_2026_str"], use_container_width=True, hide_index=True)

    st.markdown("#### RR Tactical Requirements (`RR_TEAM_REQUIREMENTS.csv`)")
    st.dataframe(D["rr_req"], use_container_width=True, hide_index=True)

    weight_mode = st.selectbox(
        "RR Fit Weight Sensitivity Profile",
        [
            "Baseline (35% Phase / 25% Role Need / 20% V4.2 Pressure / 10% Confidence / 10% IPL Balance)",
            "Pressure-Heavy (25% Phase / 20% Role Need / 35% V4.2 Pressure / 10% Confidence / 10% IPL Balance)",
            "Role-Heavy (40% Phase / 35% Role Need / 10% V4.2 Pressure / 10% Confidence / 5% IPL Balance)",
        ],
    )
    score_col = (
        "RR_PLAYER_FIT_SCORE"
        if weight_mode.startswith("Baseline")
        else ("fit_score_pressure_heavy" if weight_mode.startswith("Pressure-Heavy") else "fit_score_role_heavy")
    )

    t1, t2, t3 = st.tabs(
        [
            "Universal Top 10 RR Fit",
            "Best Outside-Top-10 RR Fits",
            "Recommended Balanced RR Shortlist",
        ]
    )
    with t1:
        df1 = D["rr_top10"].sort_values(score_col, ascending=False)
        st.dataframe(
            df1[
                [
                    "player_name",
                    "role",
                    "shortlist_rank_display",
                    "rr_target_role",
                    "already_rr_2026",
                    "eb_delta",
                    "phase_exec_score",
                    "role_need_score",
                    score_col,
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    with t2:
        df2 = D["rr_outside"].sort_values(score_col, ascending=False)
        st.dataframe(
            df2[
                [
                    "player_name",
                    "role",
                    "eb_rank",
                    "rr_target_role",
                    "eb_delta",
                    score_col,
                    "why_better_rr_fit_than_some_top10",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    with t3:
        st.dataframe(
            D["rr_squad"][
                [
                    "player_name",
                    "role",
                    "selection_pool",
                    "squad_role",
                    "shortlist_rank_display",
                    "eb_rank",
                    "eb_delta",
                    "RR_PLAYER_FIT_SCORE",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Auction Assumptions Disclosure: Purse constraints and player availability are unverified external assumptions "
        "stored in `data/reference/rr_2027_auction_assumptions.csv` and kept strictly configurable."
    )


def render_methodology() -> None:
    st.subheader("Methodology, Validation & Data Transparency")
    st.markdown(
        """
        ### 1. Estimator & Key Metrics
        - **Primary Estimator:** `OPTION_A_COMPLETE_PENALIZED_FWL_REML` — residualizes **both** the ball-by-ball outcome `y` and the resource-stress/scoring-threat predictor `p` against identical state, match, player, and opponent nuisance designs, then applies REML Empirical Bayes shrinkage across eligible players.
        - **`EB Δ` (Within-Player):** Shrinkage-stabilized estimate of how much a player's performance changes under high pressure vs their own usual baseline (used for official ranking).
        - **`EB vs Pop μ₀ = EB Δ − μ₀`:** Deviation from the pooled eligible population average pressure effect (`μ₀`). For bowlers, because scoring environments tighten/expand at high scoring threat, even top-10 bowlers can have a positive `EB vs Pop μ₀` while their `absolute effect remains negative`.
        - **Eligibility Gate:** `n_hi >= 50`, `n_nonhi >= 50`, `cs_matches >= 10` (prevents tiny-sample spikes).
        """
    )

    st.markdown("### 2. Pressure Methodology Comparison (`PRESSURE_METHODOLOGY_COMPARISON.csv`)")
    st.dataframe(D["method_cmp"], use_container_width=True, hide_index=True)

    st.markdown("### 3. Score Reconstruction Audit (`V4_2_SCORE_ENRICHMENT_AUDIT.csv`)")
    st.dataframe(D["score_audit"], use_container_width=True, hide_index=True)

    st.markdown("### 4. Out-of-Time & Robustness Validation (`V4_2_VALIDATION_MATRIX.csv`)")
    st.dataframe(D["val_matrix"], use_container_width=True, hide_index=True)

    st.markdown("### 5. Authoritative Artifact Provenance (`FINAL_RANKING_SOURCE_OF_TRUTH.json`)")
    st.json(D["sot"])


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
