"""SupeRR Intelligence V4.2 — Professional Cricket Analytics SaaS UI.

Light-mode, deep-navy + restrained RR-pink executive analytics platform.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.charts import (
    comparison_sample_chart,
    dataset_coverage_chart,
    dumbbell_shift_chart,
    eb_forest_chart,
    rr_2026_contrib_chart,
    rr_component_chart,
)
from dashboard.data_loader import (
    AMBER_WARN,
    BAT_MU0,
    BOWL_MU0,
    CARD_BORDER,
    NAVY,
    NAVY_MID,
    RR_PINK,
    SLATE_BG,
    TEAL_POS,
    TEXT_MAIN,
    TEXT_MUTED,
    esc,
    fmt_int,
    fmt_num,
    initials_badge,
    load_all_data,
)

NAV_PAGES = [
    "1. Overview",
    "2. Universal Top 10",
    "3. Player Explorer & Comparison",
    "4. Rajasthan Royals Intelligence",
    "5. Methodology & Transparency",
]

st.set_page_config(
    page_title="SupeRR Intelligence V4.2",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
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
    section[data-testid="stSidebar"] {{
        background-color: {NAVY} !important;
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: #F8FAFC !important;
    }}
    [data-testid="stSidebar"] code {{
        background-color: rgba(255, 255, 255, 0.16) !important;
        color: #F8FAFC !important;
        border: 1px solid rgba(255, 255, 255, 0.28) !important;
        border-radius: 4px;
        padding: 1px 5px;
    }}
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
        letter-spacing: 0.4px;
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
    .gap-card {{
        background: #FFFFFF;
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }}
    .pill-crit {{
        background: #FEE2E2;
        color: #991B1B;
        font-weight: 700;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 999px;
    }}
    .pill-imp {{
        background: #FEF3C7;
        color: {AMBER_WARN};
        font-weight: 700;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 999px;
    }}
    .pill-depth {{
        background: #E0F2FE;
        color: #075985;
        font-weight: 700;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 999px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    D = load_all_data()
except FileNotFoundError as exc:
    st.error(f"Dashboard data initialization error: {exc}. Please regenerate authoritative outputs and restart.")
    st.stop()
except Exception:
    st.error("Unable to load authoritative analytics artifacts. Please verify CSV/JSON integrity and restart.")
    st.stop()

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = NAV_PAGES[0]


def _go_to_page(page_name: str) -> None:
    """Callback-safe navigation update executed before widgets re-instantiate."""
    st.session_state["nav_page"] = page_name


def _reset_top10_filters(discipline_label: str) -> None:
    """Callback-safe filter reset executed before widgets re-instantiate."""
    st.session_state[f"search_{discipline_label}"] = ""
    st.session_state[f"conf_{discipline_label}"] = "All"
    st.session_state[f"trade_{discipline_label}"] = "All"
    st.session_state[f"sort_{discipline_label}"] = "Official Rank (EB Δ)"

# Sidebar navigation
st.sidebar.markdown("## SupeRR Intelligence")
st.sidebar.caption("V4.2 PROVISIONAL — RESOURCE STRESS")
section = st.sidebar.radio("Workspace", NAV_PAGES, key="nav_page")
st.sidebar.markdown("---")
st.sidebar.caption(
    "Operational Eligibility Floor:\n"
    "- High-stress balls: `n_hi >= 50`\n"
    "- Normal-stress balls: `n_lo >= 30`\n"
    "- Common-support matches: `>= 8`\n"
    "- Max SE: `se_delta <= 25.0`\n\n"
    "RR scouting is strictly secondary and never modifies Universal Top 10 ranks."
)

# Persistent Top Header
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
            f'<div class="kpi-card"><div class="kpi-label">{esc(lbl)}</div>'
            f'<div class="kpi-val">{esc(val)}</div><div class="kpi-sub">{esc(sub)}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="status-strip">
            <b>Executive Summary & Provisional Scope:</b> High-stress T20 states depress scoring/economy across the entire player pool
            (cohort stress tax <b>μ₀ = -36.12</b> for batters; <b>μ₀ = -50.88</b> for bowlers). Rather than ranking career averages or raw crisis strike rates,
            V4.2 estimates each player's <i>within-player shift</i> from normal to high stress after removing match, phase, innings, and opponent confounders.
            Because chase targets fail reconciliation on 342/390 non-DLS chases (<code>MARGIN_MISMATCH_BLOCKED</code>), V4.2 uses pre-delivery
            <b>BATTING_RESOURCE_STRESS</b> and <b>BOWLING_SCORING_THREAT</b> proxies.
        </div>
        """,
        unsafe_allow_html=True,
    )

    cov_col, ins_col = st.columns([1.3, 1.0])
    with cov_col:
        st.plotly_chart(dataset_coverage_chart(), use_container_width=True)
    with ins_col:
        st.subheader("Key Analytical Findings")
        st.markdown(
            "- **Top Batter (#1 David Miller):** `EB Δ = -29.39` (`+6.73` vs cohort `μ₀`) across 81 common-support matches.\n"
            "- **Top Bowler (#1 Matheesha Pathirana):** `EB Δ = -34.95` (`+15.94` vs cohort `μ₀`), `P(Top 10) = 0.790`.\n"
            "- **Famous Players Audited Transparently:** Jasprit Bumrah ranks **#4** (`-38.13`); Virat Kohli (`#54`), MS Dhoni (`#82`), and Rohit Sharma (`#104`) show larger negative stress shifts than the Top 10; Yashasvi Jaiswal is ineligible (`n_hi = 27 < 50`)."
        )

    nav1, nav2, nav3 = st.columns(3)
    nav1.button("Explore Top 10 Batters", key="ov_btn_bat", on_click=_go_to_page, args=(NAV_PAGES[1],), use_container_width=True)
    nav2.button("Explore Top 10 Bowlers", key="ov_btn_bowl", on_click=_go_to_page, args=(NAV_PAGES[1],), use_container_width=True)
    nav3.button("Open Player Explorer", key="ov_btn_exp", on_click=_go_to_page, args=(NAV_PAGES[2],), use_container_width=True)

    col_b, col_w = st.columns(2)
    with col_b:
        st.subheader("Universal Batters — Top 5 Preview")
        st.dataframe(_preview_table(D["top_bat"].head(5)), use_container_width=True, hide_index=True)
    with col_w:
        st.subheader("Universal Bowlers — Top 5 Preview")
        st.dataframe(_preview_table(D["top_bowl"].head(5)), use_container_width=True, hide_index=True)

    st.subheader("Data Integrity & Governance Checks")
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


def _render_top10_discipline(df: pd.DataFrame, discipline_label: str, filename: str) -> None:
    is_bowler = discipline_label == "Bowlers"
    mu0 = BOWL_MU0 if is_bowler else BAT_MU0

    k_search = f"search_{discipline_label}"
    k_conf = f"conf_{discipline_label}"
    k_trade = f"trade_{discipline_label}"
    k_sort = f"sort_{discipline_label}"

    f1, f2, f3, f4, f5 = st.columns([2.0, 1.5, 1.4, 1.8, 0.9])
    search_q = f1.text_input(f"Search {discipline_label}", key=k_search, placeholder="e.g., Miller, Bumrah")
    conf_filter = f2.selectbox(
        "Sample Confidence",
        ["All", "HIGH", "MODERATE", "PROVISIONAL_BOUNDARY"],
        key=k_conf,
    )
    tradeoff_filter = f3.selectbox(
        "Tradeoff Status",
        ["All", "Clean Only", "Flagged Only"],
        key=k_trade,
    )
    sort_col = f4.selectbox(
        "Sort By",
        ["Official Rank (EB Δ)", "Raw High−Low Δ", "P(Top 10)", "Common-Support Matches"],
        key=k_sort,
    )
    f5.button(
        "Reset",
        key=f"reset_{discipline_label}",
        on_click=_reset_top10_filters,
        args=(discipline_label,),
        use_container_width=True,
    )

    active_filters = sum([bool(search_q.strip()), conf_filter != "All", tradeoff_filter != "All"])
    if active_filters:
        st.info(f"Active filters: {active_filters} | Showing subset of authoritative {discipline_label} Top 10.")

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
        st.warning("No shortlisted players match the active filters. Click Reset to view all 10.")
        return

    lo_col = "Raw Lo (-Runs/100b)" if is_bowler else "Raw Lo (Runs/100b)"
    hi_col = "Raw Hi (-Runs/100b)" if is_bowler else "Raw Hi (Runs/100b)"
    disp = pd.DataFrame(
        {
            "Rank": view["shortlist_rank_display"].apply(fmt_int),
            "Player": view["player_name"],
            "ID": view["player_id"].apply(fmt_int),
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
            dumbbell_shift_chart(view, is_bowler=is_bowler, title="Normal vs High-Stress Shift (Raw Baseline)"),
            use_container_width=True,
        )
    with c_right:
        st.plotly_chart(
            eb_forest_chart(view, mu0=mu0, title="Adjusted EB Δ vs Cohort Mean (μ₀)"),
            use_container_width=True,
        )

    st.markdown(f"#### {discipline_label[:-1]} Scouting Dossier")
    pick_name = st.selectbox(
        f"Select a shortlisted {discipline_label[:-1].lower()} to inspect full justification",
        view["player_name"].tolist(),
        key=f"dossier_{discipline_label}",
    )
    r = view[view["player_name"] == pick_name].iloc[0]
    cons_pct = (
        fmt_num(r["claim_b_high_stress_pos_share"] * 100, "{:.1f}%")
        if pd.notna(r["claim_b_high_stress_pos_share"])
        else "Unavailable"
    )
    st.markdown(
        f"""
        <div class="dossier-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>{initials_badge(r['player_name'])} <b style="font-size:17px; color:{NAVY};">#{int(r['shortlist_rank_display'])} {esc(r['player_name'])}</b>
                <span style="color:{TEXT_MUTED}; font-size:13px;"> (ID {int(r['player_id'])} | {esc(r['sample_confidence'])})</span></div>
                <span style="font-weight:700; color:{TEAL_POS};">EB vs Pop μ₀: {esc(fmt_num(r['eb_vs_pop_mean_delta'], '{:+.2f}'))}</span>
            </div>
            <p style="margin:10px 0 6px 0; font-size:13.5px;">
                <b>Normal Baseline:</b> {esc(fmt_num(r['raw_lo_perf']))} &nbsp;|&nbsp;
                <b>High-Stress:</b> {esc(fmt_num(r['raw_hi_perf']))} &nbsp;|&nbsp;
                <b>EB Δ:</b> {esc(fmt_num(r['eb_delta']))} &nbsp;|&nbsp;
                <b>Boot Rank 95% CI:</b> [{esc(fmt_int(r['boot_rank_ci_low']))}, {esc(fmt_int(r['boot_rank_ci_high']))}] &nbsp;|&nbsp;
                <b>Within-Match Consistency:</b> {esc(cons_pct)}
            </p>
            <p style="margin:0; font-size:13.5px; color:{TEXT_MAIN};">{esc(r['player_explanation'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dl1, dl2 = st.columns([1.4, 2.6])
    export_scope = dl1.radio(
        "CSV Export Scope",
        ["Full Authoritative Top 10", "Filtered Visible Rows"],
        horizontal=True,
        key=f"exp_scope_{discipline_label}",
    )
    export_df = df if export_scope == "Full Authoritative Top 10" else view
    dl2.download_button(
        label=f"Download {filename} ({len(export_df)} rows — {export_scope})",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name=filename if export_scope == "Full Authoritative Top 10" else f"filtered_{filename}",
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

    c1, c2, c3 = st.columns([1.3, 1.3, 3.4])
    disc = c1.selectbox("Discipline", ["All", "batter", "bowler"], key="exp_disc")
    elig_opt = c2.selectbox("Eligibility", ["All", "Eligible Only", "Ineligible Only"], key="exp_elig")

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
    if not options:
        st.warning("No players match the selected discipline/eligibility filter.")
        return

    default_idx = next((i for i, lbl in enumerate(options) if "Virat Kohli" in lbl), 0)
    selected_lbl = c3.selectbox(
        "Search any player (e.g., Virat Kohli, MS Dhoni, Jasprit Bumrah, Patrick Cummins)",
        options,
        index=default_idx,
        key="exp_player_pick",
    )

    row = pool[pool["label"] == selected_lbl].iloc[0]
    st.markdown(
        f"### {initials_badge(row['player_name'])} {esc(row['player_name'])} ({esc(str(row['role']).title())})",
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
            f'<div class="kpi-card"><div class="kpi-label">{esc(lbl)}</div>'
            f'<div class="kpi-val">{esc(val)}</div><div class="kpi-sub">{esc(sub)}</div></div>',
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
            f'<div class="kpi-card"><div class="kpi-label">{esc(lbl)}</div>'
            f'<div class="kpi-val">{esc(val)}</div><div class="kpi-sub">{esc(sub)}</div></div>',
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
    st.markdown("### Player Comparison Studio (2–4 Same-Discipline Players)")
    cmp_role = st.radio("Comparison Discipline", ["batter", "bowler"], horizontal=True, key="cmp_role")
    cmp_pool = all_est[(all_est["role"] == cmp_role) & (all_est["eligible"] == True)].sort_values("eb_rank")
    default_picks = ["David Miller", "Andre Russell", "Virat Kohli"] if cmp_role == "batter" else ["Matheesha Pathirana", "Jasprit Bumrah", "Patrick Cummins"]

    selected_names = st.multiselect(
        f"Pick 2 to 4 eligible {cmp_role}s",
        cmp_pool["player_name"].tolist(),
        default=[p for p in default_picks if p in cmp_pool["player_name"].values][:3],
        max_selections=4,
        key=f"cmp_multi_{cmp_role}",
    )
    if len(selected_names) >= 2:
        sub = cmp_pool[cmp_pool["player_name"].isin(selected_names)].copy()
        sub["shortlist_rank_display"] = sub["eb_rank"]
        is_bowl = cmp_role == "bowler"
        mu0 = BOWL_MU0 if is_bowl else BAT_MU0
        c_l, c_r = st.columns(2)
        with c_l:
            st.plotly_chart(
                dumbbell_shift_chart(sub, is_bowler=is_bowl, title=f"Normal vs High-Stress Shift ({cmp_role.title()}s)"),
                use_container_width=True,
            )
        with c_r:
            st.plotly_chart(
                eb_forest_chart(sub, mu0=mu0, title=f"Adjusted EB Δ vs Cohort Mean ({cmp_role.title()}s)"),
                use_container_width=True,
            )
        st.plotly_chart(comparison_sample_chart(sub), use_container_width=True)
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
                "Confidence": sub["sample_confidence"],
            }
        )
        st.dataframe(cmp_disp, use_container_width=True, hide_index=True)
    else:
        st.info("Select at least 2 players from the same discipline to unlock side-by-side comparison charts.")

    st.markdown("---")
    st.markdown("### Star-Player Eligibility Audit (21 Audited Players)")
    sa = D["star_audit"].copy()
    s1, s2 = st.columns([2, 1.2])
    sa_q = s1.text_input("Filter Star Audit by player name", key="sa_search", placeholder="e.g., Kohli, Cummins, Jaiswal")
    sa_elig = s2.selectbox("Audit Status", ["All", "Eligible Only", "Excluded Only"], key="sa_elig")
    if sa_q.strip():
        sa = sa[sa["player_name"].str.contains(sa_q.strip(), case=False, na=False)]
    if sa_elig == "Eligible Only":
        sa = sa[sa["eligible"] == True]
    elif sa_elig == "Excluded Only":
        sa = sa[sa["eligible"] == False]

    if sa.empty:
        st.warning("No audited star players match your filter.")
    else:
        sa_disp = pd.DataFrame(
            {
                "Player": sa["player_name"],
                "Discipline": sa["discipline"].str.title(),
                "Canonical ID": sa["canonical_player_id"].apply(fmt_int),
                "Status": sa["eligible"].map({True: "Eligible", False: "Excluded"}),
                "EB Rank": sa["eb_rank"].apply(fmt_int),
                "High-Stress Balls": sa["n_hi"].apply(fmt_int),
                "Matches": sa["cs_matches"].apply(fmt_int),
                "EB Δ": sa["eb_delta"].apply(fmt_num),
                "Exclusion / Status Detail": sa["exclusion_reason"].fillna("Eligible"),
                "Audit Explanation": sa["explanation"],
            }
        )
        st.dataframe(sa_disp, use_container_width=True, hide_index=True)


def render_rr() -> None:
    st.subheader("Rajasthan Royals Intelligence (Secondary Application)")
    st.markdown(
        '<div class="status-strip"><b>Strict Independence Guarantee:</b> Universal Top 10 rankings and RR-specific squad fit scoring are independent systems. '
        'RR scouting evaluates both Universal Top 10 leaders and eligible specialists outside the Top 10, and never alters Universal Top 10 ranks.</div>',
        unsafe_allow_html=True,
    )

    # Block A: RR 2026 Team Performance Analysis
    st.markdown("### A. RR 2026 Team Performance Analysis")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Observed Weaknesses")
        wk = D["rr_2026_wk"].rename(columns={"dimension": "Dimension", "metric": "Metric", "empirical_evidence": "Empirical Evidence", "sample_size": "Sample"})
        st.dataframe(wk[["Dimension", "Metric", "Empirical Evidence", "Sample"]], use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### Observed Strengths")
        st_df = D["rr_2026_str"].rename(columns={"dimension": "Dimension", "metric": "Metric", "empirical_evidence": "Empirical Evidence", "sample_size": "Sample"})
        st.dataframe(st_df[["Dimension", "Metric", "Empirical Evidence", "Sample"]], use_container_width=True, hide_index=True)

    st.plotly_chart(rr_2026_contrib_chart(D["rr_2026_contrib"]), use_container_width=True)

    # Block B: Tactical Gap Recruitment Board
    st.markdown("### B. Tactical Gap Recruitment Board")
    req = D["rr_req"]
    cols = st.columns(len(req))
    for col, (_, r) in zip(cols, req.iterrows()):
        urg = str(r["urgency"]).upper()
        pill_cls = "pill-crit" if "CRIT" in urg else ("pill-imp" if "IMP" in urg else "pill-depth")
        col.markdown(
            f"""
            <div class="gap-card">
                <span class="{pill_cls}">P{int(r['priority'])} · {esc(urg)}</span>
                <div style="font-weight:700; color:{NAVY}; margin:6px 0 4px 0; font-size:13.5px;">{esc(r['role_title'])}</div>
                <div style="font-size:12px; color:{TEXT_MUTED}; margin-bottom:6px;">{esc(r['tactical_objective'])}</div>
                <div style="font-size:11.5px; color:{TEXT_MAIN};">
                    <b>Cover:</b> {esc(r['existing_rr_cover'])}<br>
                    <b>Target Budget:</b> {esc(r['budget_allocation_cr'])} Cr &nbsp;|&nbsp; <b>Wt:</b> {esc(fmt_num(r['scouting_priority_weight']))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Block C: Sensitivity & Component Diagnostics
    st.markdown("### C. RR Fit Sensitivity & Component Diagnostics")
    weight_mode = st.selectbox(
        "Weight Sensitivity Profile",
        [
            "Baseline (35% Phase / 25% Role Need / 20% V4.2 Pressure / 10% Confidence / 10% T20 Balance)",
            "Pressure-Heavy (25% Phase / 20% Role Need / 35% V4.2 Pressure / 10% Confidence / 10% T20 Balance)",
            "Role-Heavy (40% Phase / 35% Role Need / 10% V4.2 Pressure / 10% Confidence / 5% T20 Balance)",
        ],
        key="rr_weight_mode",
    )
    score_col = (
        "RR_PLAYER_FIT_SCORE"
        if weight_mode.startswith("Baseline")
        else ("fit_score_pressure_heavy" if weight_mode.startswith("Pressure-Heavy") else "fit_score_role_heavy")
    )
    top_pool = pd.concat([D["rr_top10"][~D["rr_top10"]["already_rr_2026"]], D["rr_outside"]], ignore_index=True)
    st.plotly_chart(rr_component_chart(top_pool, score_col=score_col), use_container_width=True)

    # Block D: Recruitment Shortlists
    st.markdown("### D. Recruitment Shortlists")
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
                "Discipline": df1["role"].str.title(),
                "Universal Rank": df1["shortlist_rank_display"].apply(fmt_int),
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
                "Discipline": df2["role"].str.title(),
                "Global Rank": df2["eb_rank"].apply(fmt_int),
                "RR Target Role": df2["rr_target_role"],
                "EB Δ": df2["eb_delta"].apply(fmt_num),
                "RR Fit Score": df2[score_col].apply(fmt_num),
                "Tactical Fit Explanation": df2["why_better_rr_fit_than_some_top10"],
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
                "RR Target Role": df3["rr_target_role"],
                "EB Δ": df3["eb_delta"].apply(fmt_num),
                "RR Fit Score": df3["RR_PLAYER_FIT_SCORE"].apply(fmt_num),
            }
        )
        st.dataframe(disp3, use_container_width=True, hide_index=True)

    st.caption(
        "Unverified Auction Scenarios Disclosure: Purse constraints, retention slots, and player availability remain unverified external assumptions "
        "(configurable in reference scenario tables) and are never presented as confirmed auction facts."
    )


def render_methodology() -> None:
    st.subheader("Methodology, Governance & Artifact Provenance")

    m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs(
        [
            "1. Estimator & Proxies",
            "2. Metric Glossary & Eligibility",
            "3. Validation & Score Audit",
            "4. Artifact Provenance (SHA-256)",
        ]
    )

    with m_tab1:
        st.markdown(
            """
            - **Primary Estimator (`OPTION_A_COMPLETE_PENALIZED_FWL_REML`):** Residualizes both the ball-by-ball outcome `y` and the resource-stress/scoring-threat predictor `p` against identical state, match, player, and opponent nuisance designs via Schur-complement normal equations, then applies REML Empirical Bayes shrinkage across eligible players.
            - **Batting Proxy (`BATTING_WICKET_DEPLETION_ANOMALY`):** Excess wickets lost relative to a typical innings at `(innings, overid)`. Cannot distinguish needing 12 vs 70 runs when overs and wickets remaining are identical.
            - **Bowling Proxy (`BOWLING_EXPECTED_SCORING_THREAT`):** Pre-delivery expected batter runs/100 legal balls from phase, innings, format, wickets remaining, and balls remaining. Primary bowler outcome is negated batter runs conceded per 100 legal balls (`-100 * batter_runs / legal_ball`), not full bowling economy with multi-run extras.
            """
        )
        with st.expander("View Complete FWL & Empirical Bayes Equations"):
            st.latex(r"\tilde{y} = y - Z\hat{\theta}_y, \qquad \tilde{W} = W - Z\hat{\theta}_W, \qquad \Delta_{\text{unshrunk}, i} = 0.75\,\hat{\beta}_{\text{FWL}, i}")
            st.latex(r"\text{EB }\Delta_i = w_i\,\Delta_{\text{unshrunk}, i} + (1 - w_i)\,\mu_0, \qquad w_i = \frac{\tau^2}{\tau^2 + \text{SE}_i^2}")

    with m_tab2:
        st.markdown(
            """
            | Term | Exact Definition & Interpretation |
            |---|---|
            | **`EB Δ`** | Shrinkage-stabilized absolute within-player shift from P12.5 to P87.5 stress vs the player's own baseline. Used for official ranking. |
            | **`EB vs Pop μ₀ = EB Δ − μ₀`** | Deviation from the pooled eligible cohort average stress tax (`μ₀ = -36.12` batters; `-50.88` bowlers). Across all 20 shortlisted players, `EB vs Pop μ₀` is positive while their `absolute effect remains negative`. |
            | **`P(Top 10)`** | Match-cluster bootstrap probability (`B = 2,000`) of entering the Top 10 candidate group. Never interpret or present `P(Top 10)` as `P(Δ > 0)`. |
            | **Operational Eligibility Gate** | `n_hi >= 50` high-stress balls, `n_lo >= 30` normal-stress balls, `cs_matches >= 8` common-support matches, and `se_delta <= 25.0`. |
            """
        )

    with m_tab3:
        st.markdown("#### Pressure Methodology Comparison")
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

        st.markdown("#### Chase-Score Reconstruction Audit (`MARGIN_MISMATCH_BLOCKED`)")
        st.dataframe(D["score_audit"], use_container_width=True, hide_index=True)

        st.markdown("#### Out-of-Time & Robustness Validation Matrix")
        vm = D["val_matrix"].copy()
        disc_vm = st.selectbox("Filter Validation Matrix by Discipline", ["All", "batter", "bowler", "both"], key="vm_disc")
        if disc_vm != "All" and "role" in vm.columns:
            vm = vm[vm["role"].astype(str).str.lower() == disc_vm]
        st.dataframe(vm, use_container_width=True, hide_index=True)
        st.download_button(
            "Download PRESSURE_METHODOLOGY_COMPARISON.csv",
            data=mc.to_csv(index=False).encode("utf-8"),
            file_name="PRESSURE_METHODOLOGY_COMPARISON.csv",
            mime="text/csv",
            key="dl_method_cmp",
        )

    with m_tab4:
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
