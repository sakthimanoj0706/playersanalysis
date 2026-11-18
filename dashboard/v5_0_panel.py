"""SupeRR Intelligence V5.0 — Power BI-Inspired 5-Page Analytics Dashboard."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.ui_theme import (
    PBI_BLUE,
    PBI_BLUE_DEEP,
    PBI_CORAL,
    PBI_MUTED,
    PBI_TEAL,
    PBI_TEXT,
    PBI_YELLOW,
    inject_v5_powerbi_theme,
    render_kpi_card,
    style_pbi_figure,
)

ROOT = Path(__file__).resolve().parents[1]
V50_DIR = ROOT / "data" / "outputs" / "v5_0"
V44_DIR = ROOT / "data" / "outputs" / "v4_4"
DATA_DIR = ROOT / "data"

V50_NAV_PAGES = [
    "1. Overview",
    "2. Team Analysis",
    "3. Player Explorer",
    "4. Match Explorer",
    "5. Pressure Analytics",
]


@st.cache_data(show_spinner=False)
def load_v50_dashboard_data() -> Dict[str, Any]:
    """Load precomputed V5.0, V4.4 Track A, and reference match/team metadata."""
    bat = pd.read_csv(V50_DIR / "V5_0_GLOBAL_BATTER_PRESSURE.csv")
    bowl = pd.read_csv(V50_DIR / "V5_0_GLOBAL_BOWLER_PRESSURE.csv")
    inn = pd.read_csv(V50_DIR / "V5_0_INNINGS_SPLIT_RANKINGS.csv")
    scales = pd.read_csv(V50_DIR / "V5_0_PRESSURE_SCALES_SUMMARY.csv")
    stab = pd.read_csv(V50_DIR / "V5_0_RANKING_STABILITY.csv")
    trv = pd.read_parquet(V44_DIR / "V4_4_TOTAL_RUN_VALUE.parquet")
    enr = pd.read_parquet(
        V44_DIR / "artifacts" / "v4_4_regular_deliveries_enriched.parquet",
        columns=[
            "match_id",
            "innings",
            "event_index_in_innings",
            "batting_team_id",
            "bowling_team_id",
            "innings_phase",
            "is_ball_faced",
            "batting_order",
            "dismissed_player_id",
        ],
    )
    trv = trv.merge(enr, on=["match_id", "innings", "event_index_in_innings"], how="left")
    mean_raw = float(trv["raw_expected_wp_swing"].mean())
    trv["LI_global"] = trv["raw_expected_wp_swing"] / max(mean_raw, 1e-9)
    inn_means = trv.groupby("innings")["raw_expected_wp_swing"].transform("mean")
    trv["LI_innings"] = trv["raw_expected_wp_swing"] / np.maximum(inn_means, 1e-9)
    trv["year"] = pd.to_datetime(trv["match_date"], errors="coerce").dt.year.fillna(2024).astype(int)

    matches = pd.read_csv(DATA_DIR / "matches_ipl_t20i.csv")
    mapping = pd.read_csv(DATA_DIR / "competition_team_player_mapping_ipl_t20i.csv")
    return {
        "bat": bat,
        "bowl": bowl,
        "inn": inn,
        "scales": scales,
        "stab": stab,
        "trv": trv,
        "matches": matches,
        "mapping": mapping,
    }


def _initials(name: str) -> str:
    parts = [p for p in str(name).strip().split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _reset_v50_filters() -> None:
    st.session_state["v50_comp_flt"] = "All Competitions"
    st.session_state["v50_season_flt"] = "All Seasons"
    st.session_state["v50_team_flt"] = "All Teams"
    st.session_state["v50_role_flt"] = "All"
    st.session_state["v50_player_search"] = ""


def _filter_trv_and_matches(D: Dict[str, Any], comp: str, season: str, team: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter Track A verified deliveries & matches by competition, season, and team."""
    trv = D["trv"]
    matches = D["matches"]
    m_ver = matches[matches["match_id"].isin(trv["match_id"].unique())].copy()
    m_ver["year_str"] = pd.to_datetime(m_ver["match_date"], errors="coerce").dt.year.fillna(0).astype(int).astype(str)

    if comp == "IPL (T20)":
        m_ver = m_ver[m_ver["match_format"] == "T20"]
    elif comp == "Men's T20I":
        m_ver = m_ver[m_ver["match_format"] == "T20I"]

    if season != "All Seasons":
        m_ver = m_ver[m_ver["year_str"] == str(season)]

    if team != "All Teams":
        m_ver = m_ver[(m_ver["home_team"] == team) | (m_ver["away_team"] == team)]

    trv_f = trv[trv["match_id"].isin(m_ver["match_id"].unique())]
    return trv_f, m_ver


def get_official_top10(
    df: pd.DataFrame,
    comp_flt: str = "All Competitions",
    team_pids: set | None = None,
    n: int = 10,
) -> pd.DataFrame:
    """
    Return the official V5.0 Top-N eligible players in exact rank_hp order.
    Preserves the 100/300/12 eligibility gate, deduplicates by player_id,
    and never modifies theta_main, delta_pressure, or theta_HP.
    """
    sub = df[df["eligible"] == True].copy()
    if comp_flt == "IPL (T20)" and "ipl_balls" in sub.columns:
        sub = sub[sub["ipl_balls"] > 0]
    elif comp_flt == "Men's T20I" and "t20i_balls" in sub.columns:
        sub = sub[sub["t20i_balls"] > 0]
    if team_pids is not None:
        sub = sub[sub["player_id"].isin(team_pids)]
    sub = sub.drop_duplicates(subset=["player_id"]).sort_values("rank_hp", ascending=True)
    return sub.head(n).reset_index(drop=True)


def _fmt_signed(val: Any) -> str:
    if pd.isna(val):
        return "N/A"
    v = float(val)
    clr = PBI_TEAL if v > 0 else (PBI_CORAL if v < 0 else PBI_MUTED)
    return f'<span style="color:{clr};font-weight:600;">{v:+.2f}</span>'


def _go_to_v50_player(pick_key: str, role_label: str) -> None:
    """Callback-safe navigation to Player Explorer."""
    st.session_state["v50_selected_player_name"] = st.session_state.get(pick_key, "")
    st.session_state["v50_pe_role"] = role_label
    st.session_state["v50_nav_page"] = "3. Player Explorer"


def _go_to_v50_pressure(role_label: str) -> None:
    """Callback-safe navigation to Pressure Analytics full leaderboard."""
    st.session_state["v50_disc"] = f"{role_label}s"
    st.session_state["v50_nav_page"] = "5. Pressure Analytics"


def _go_to_v50_match(match_map: dict, pick_key: str) -> None:
    """Callback-safe navigation to Match Explorer."""
    sel_ml = st.session_state.get(pick_key, "")
    if sel_ml in match_map:
        st.session_state["v50_selected_match_id"] = int(match_map[sel_ml])
    st.session_state["v50_nav_page"] = "4. Match Explorer"


def _render_top10_table(top_df: pd.DataFrame, role_label: str, key_prefix: str) -> None:
    """Render Power BI-styled ranked Top 10 leaderboard table with Player Explorer drill-down."""
    if len(top_df) == 0:
        st.warning(f"No eligible {role_label.lower()}s qualify under the current filters (100/300/12 gate).")
        return
    if len(top_df) < 10:
        st.info(f"Showing {len(top_df)} eligible {role_label.lower()}s (fewer than 10 pass the 100/300/12 gate under current filters).")

    rows_html = []
    for idx, r in top_df.iterrows():
        bg = "rgba(15, 35, 75, 0.72)" if idx % 2 == 0 else "rgba(10, 24, 54, 0.72)"
        rk = f"{int(r['rank_hp']):02d}" if pd.notna(r["rank_hp"]) else f"{idx + 1:02d}"
        ci_str = (
            f"[{r['ci_low_hp']:+.1f}, {r['ci_high_hp']:+.1f}]"
            if pd.notna(r["ci_low_hp"]) and pd.notna(r["ci_high_hp"])
            else "N/A"
        )
        hp_b = f"{int(r['n_hp_global']):,}" if pd.notna(r["n_hp_global"]) else "N/A"
        hp_m = f"{int(r['m_hp']):,}" if pd.notna(r["m_hp"]) else "N/A"
        arch = str(r["archetype"]).replace("UNCLASSIFIED / INSUFFICIENT EVIDENCE", "UNCLASSIFIED")
        rows_html.append(
            f'<tr style="background:{bg};border-bottom:1px solid rgba(148,163,184,0.14);">'
            f'<td style="padding:8px 10px;font-weight:700;color:{PBI_YELLOW};">{rk}</td>'
            f'<td style="padding:8px 10px;font-weight:700;color:{PBI_TEXT};">{r["player_name"]}</td>'
            f'<td style="padding:8px 10px;text-align:right;">{_fmt_signed(r["main_effect_per100"])}</td>'
            f'<td style="padding:8px 10px;text-align:right;">{_fmt_signed(r["pressure_interaction_per100"])}</td>'
            f'<td style="padding:8px 10px;text-align:right;font-weight:700;">{_fmt_signed(r["combined_hp_per100"])}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:{PBI_MUTED};font-size:12px;">{ci_str}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:{PBI_TEXT};">{hp_b}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:{PBI_TEXT};">{hp_m}</td>'
            f'<td style="padding:8px 10px;color:{PBI_BLUE};font-size:12px;">{arch}</td>'
            f'</tr>'
        )

    table_html = (
        '<div style="overflow-x:auto;border:1px solid rgba(148,163,184,0.24);border-radius:10px;margin-bottom:10px;">'
        '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        '<thead><tr style="background:rgba(7,20,46,0.92);color:#CBD5E1;text-align:left;border-bottom:2px solid #38BDF8;">'
        '<th style="padding:9px 10px;" title="Official V5.0 Rank (100/300/12 gate)">Rank</th>'
        '<th style="padding:9px 10px;">Player</th>'
        '<th style="padding:9px 10px;text-align:right;" title="Baseline Main RAPM Effect (theta_main, runs/100b)">Main Effect</th>'
        '<th style="padding:9px 10px;text-align:right;" title="Standalone Pressure Uplift (delta_pressure — EXPERIMENTAL)">Pressure Uplift <span style="color:#FACC15;font-size:10px;">[EXP]</span></th>'
        '<th style="padding:9px 10px;text-align:right;" title="Combined High-Pressure Effect (theta_HP = theta_main + delta_pressure; not pure clutch)">Combined HP</th>'
        '<th style="padding:9px 10px;text-align:right;" title="95% Paired Match-Cluster Bootstrap CI for Combined HP">95% CI</th>'
        '<th style="padding:9px 10px;text-align:right;" title="High-Pressure Deliveries (LI_global >= 1.50)">HP Balls</th>'
        '<th style="padding:9px 10px;text-align:right;" title="Distinct High-Pressure Matches">HP Matches</th>'
        '<th style="padding:9px 10px;">Archetype</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)

    c_sel, c_btn1, c_btn2 = st.columns([2.5, 1.3, 1.2])
    chosen = c_sel.selectbox(
        f"Select {role_label} to Inspect",
        top_df["player_name"].tolist(),
        key=f"{key_prefix}_pick",
    )
    c_btn1.button(
        f"Open {role_label} Profile ->",
        key=f"{key_prefix}_go_pe",
        on_click=_go_to_v50_player,
        args=(f"{key_prefix}_pick", role_label),
    )
    c_btn2.button(
        "View All Players ->",
        key=f"{key_prefix}_go_all",
        on_click=_go_to_v50_pressure,
        args=(role_label,),
    )


def build_player_justification(
    row: pd.Series,
    role_label: str,
    prev_row: pd.Series | None = None,
) -> str:
    """Generate a concise, evidence-based 2-3 sentence ranking justification from a V5.0 CSV row."""
    rk = int(row["rank_hp"]) if pd.notna(row["rank_hp"]) else 0
    main_v = float(row["main_effect_per100"])
    pres_v = float(row["pressure_interaction_per100"])
    hp_v = float(row["combined_hp_per100"])
    hp_b = int(row["n_hp_global"])
    hp_m = int(row["m_hp"])
    arch = str(row["archetype"])
    rel = str(row["reliability"])

    unit = "runs/100b" if role_label == "Batter" else "runs prevented/100b"
    if prev_row is not None and pd.notna(prev_row.get("combined_hp_per100")):
        diff = hp_v - float(prev_row["combined_hp_per100"])
        prev_rk = int(prev_row["rank_hp"])
        prev_nm = str(prev_row["player_name"])
        if abs(diff) < 0.005:
            diff_txt = f"equal to #{prev_rk} {prev_nm} (point estimate only)"
        elif diff > 0:
            diff_txt = f"{diff:.2f} higher than #{prev_rk} {prev_nm} (point estimate only)"
        else:
            diff_txt = f"{abs(diff):.2f} lower than #{prev_rk} {prev_nm} (point estimate only)"
        s1 = f"Ranked #{rk} among eligible {role_label.lower()}s with a combined HP estimate of {hp_v:+.2f} {unit} ({diff_txt})."
    else:
        s1 = f"Ranked #{rk} with the highest eligible {role_label.lower()} combined HP estimate ({hp_v:+.2f} {unit})."

    if pres_v > 0:
        pres_desc = f"increased by a {pres_v:+.2f} experimental pressure adjustment"
    elif pres_v < 0:
        pres_desc = f"reduced by a {pres_v:+.2f} experimental pressure adjustment"
    else:
        pres_desc = "unchanged by a +0.00 experimental pressure adjustment"
    s2 = f"Their baseline main effect is {main_v:+.2f}, {pres_desc}."

    if pd.notna(row.get("ci_low_hp")) and pd.notna(row.get("ci_high_hp")):
        c_lo, c_hi = float(row["ci_low_hp"]), float(row["ci_high_hp"])
        ci_txt = f"95% CI [{c_lo:+.2f}, {c_hi:+.2f}]"
        if c_lo <= 0:
            ci_note = f"{ci_txt} crosses zero, so this rank carries notable uncertainty"
        elif (c_hi - c_lo) > 35.0:
            ci_note = f"{ci_txt} is wide, indicating moderate estimation uncertainty"
        else:
            ci_note = f"{ci_txt} remains above zero"
    else:
        ci_note = "95% CI is N/A"

    s3 = f"Supported by {hp_b:,} high-pressure balls across {hp_m} matches ({rel} reliability, {arch}); {ci_note}."
    return f"{s1} {s2} {s3}"


def get_same_role_comparison_df(
    role_label: str,
    player_names: List[str],
    bat_df: pd.DataFrame,
    bowl_df: pd.DataFrame,
) -> pd.DataFrame:
    """Return eligible V5.0 rows for same-role multi-player comparison (rejects mixed/invalid roles)."""
    if role_label not in ("Batter", "Bowler"):
        raise ValueError(f"Mixed or invalid role '{role_label}'; only 'Batter' or 'Bowler' allowed.")
    src = bat_df if role_label == "Batter" else bowl_df
    el = src[src["eligible"] == True].copy()
    sub = el[el["player_name"].isin(player_names)].drop_duplicates(subset=["player_id"]).sort_values("rank_hp")
    return sub.reset_index(drop=True)


def _render_justifications_section(top10_bat: pd.DataFrame, top10_bowl: pd.DataFrame) -> None:
    """Section 3 of Overview: Expandable WHY THESE PLAYERS ARE TOP 10? explanations."""
    with st.expander("WHY THESE PLAYERS ARE TOP 10? (Evidence-Based Ranking Justifications)", expanded=False):
        st.caption(
            "Explanations are generated directly from V5.0 CSV metrics. Adjacent-rank differences reflect point estimates only; "
            "overlapping individual 95% CIs do not establish statistical superiority, and delta_pressure remains EXPERIMENTAL."
        )
        j_bat, j_bowl = st.tabs(["Batter Justifications", "Bowler Justifications"])
        with j_bat:
            for i, row in top10_bat.iterrows():
                prev_r = top10_bat.iloc[i - 1] if i > 0 else None
                st.markdown(f"**#{int(row['rank_hp']):02d} {row['player_name']}** — {build_player_justification(row, 'Batter', prev_r)}")
        with j_bowl:
            for i, row in top10_bowl.iterrows():
                prev_r = top10_bowl.iloc[i - 1] if i > 0 else None
                st.markdown(f"**#{int(row['rank_hp']):02d} {row['player_name']}** — {build_player_justification(row, 'Bowler', prev_r)}")


def _render_player_comparison(
    bat_df: pd.DataFrame,
    bowl_df: pd.DataFrame,
    comp_flt: str,
    tpids: set | None,
) -> None:
    """Section 5 of Overview: Interactive same-role multi-player comparison (2-5 players)."""
    st.markdown("### PLAYER COMPARISON — Multi-Player Side-by-Side Analysis")
    st.caption(
        "Compare 2 to 5 eligible players within the same role (100/300/12 gate). "
        "delta_pressure is EXPERIMENTAL; combined HP is not a pure clutch score, and point-estimate differences do not prove statistical significance."
    )
    cmp_role = st.radio("Comparison Role", ["Batter", "Bowler"], horizontal=True, key="v50_ov_cmp_role")
    pool = get_official_top10(bat_df if cmp_role == "Batter" else bowl_df, comp_flt, tpids, n=200)
    if len(pool) < 2:
        st.info(f"Fewer than 2 eligible {cmp_role.lower()}s match the current filters for comparison.")
        return

    opts = pool["player_name"].tolist()
    defaults = opts[:3] if len(opts) >= 3 else opts[:2]
    sel_players = st.multiselect(
        f"Select 2–5 Eligible {cmp_role}s",
        opts,
        default=defaults,
        max_selections=5,
        key=f"v50_ov_cmp_pick_{cmp_role}",
    )
    if len(sel_players) < 2:
        st.info("Select at least 2 players to display the side-by-side comparison.")
        return

    cdf = get_same_role_comparison_df(cmp_role, sel_players, bat_df, bowl_df)
    cmp_rows_html = []
    for idx, r in cdf.iterrows():
        bg = "rgba(15, 35, 75, 0.72)" if idx % 2 == 0 else "rgba(10, 24, 54, 0.72)"
        ci_str = (
            f"[{r['ci_low_hp']:+.2f}, {r['ci_high_hp']:+.2f}]"
            if pd.notna(r["ci_low_hp"]) and pd.notna(r["ci_high_hp"])
            else "N/A"
        )
        arch = str(r["archetype"]).replace("UNCLASSIFIED / INSUFFICIENT EVIDENCE", "UNCLASSIFIED")
        cmp_rows_html.append(
            f'<tr style="background:{bg};border-bottom:1px solid rgba(148,163,184,0.14);">'
            f'<td style="padding:8px 10px;font-weight:700;color:{PBI_TEXT};">{r["player_name"]}</td>'
            f'<td style="padding:8px 10px;text-align:right;">{_fmt_signed(r["main_effect_per100"])}</td>'
            f'<td style="padding:8px 10px;text-align:right;">{_fmt_signed(r["pressure_interaction_per100"])}</td>'
            f'<td style="padding:8px 10px;text-align:right;font-weight:700;">{_fmt_signed(r["combined_hp_per100"])}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:{PBI_MUTED};font-size:12px;">{ci_str}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:{PBI_TEXT};">{int(r["n_hp_global"]):,}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:{PBI_TEXT};">{int(r["m_hp"]):,}</td>'
            f'<td style="padding:8px 10px;color:{PBI_BLUE};font-size:12px;">{arch}</td>'
            f'</tr>'
        )
    cmp_table_html = (
        '<div style="overflow-x:auto;border:1px solid rgba(148,163,184,0.24);border-radius:10px;margin-bottom:12px;">'
        '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        '<thead><tr style="background:rgba(7,20,46,0.92);color:#CBD5E1;text-align:left;border-bottom:2px solid #38BDF8;">'
        '<th style="padding:9px 10px;">Player</th>'
        '<th style="padding:9px 10px;text-align:right;">Main Effect</th>'
        '<th style="padding:9px 10px;text-align:right;">Pressure Uplift <span style="color:#FACC15;font-size:10px;">[EXP]</span></th>'
        '<th style="padding:9px 10px;text-align:right;">Combined HP</th>'
        '<th style="padding:9px 10px;text-align:right;">95% CI</th>'
        '<th style="padding:9px 10px;text-align:right;">HP Balls</th>'
        '<th style="padding:9px 10px;text-align:right;">HP Matches</th>'
        '<th style="padding:9px 10px;">Archetype</th>'
        '</tr></thead>'
        f'<tbody>{"".join(cmp_rows_html)}</tbody>'
        '</table></div>'
    )
    st.markdown(cmp_table_html, unsafe_allow_html=True)

    c_left, c_right = st.columns(2)
    unit_lbl = "Runs / 100 Balls" if cmp_role == "Batter" else "Runs Prevented / 100 Balls"
    with c_left:
        f_grp = go.Figure()
        f_grp.add_trace(go.Bar(x=cdf["player_name"], y=cdf["main_effect_per100"], name="Main Effect (theta_main)", marker_color=PBI_BLUE))
        f_grp.add_trace(go.Bar(x=cdf["player_name"], y=cdf["pressure_interaction_per100"], name="Pressure Uplift [EXP] (delta_pressure)", marker_color=PBI_YELLOW))
        f_grp.add_trace(go.Bar(x=cdf["player_name"], y=cdf["combined_hp_per100"], name="Combined HP (theta_HP)", marker_color=PBI_CORAL))
        f_grp.update_layout(barmode="group")
        st.plotly_chart(style_pbi_figure(f_grp, "Decomposition: Main vs Pressure [EXP] vs Combined HP", "Player", unit_lbl, 340), use_container_width=True)

    with c_right:
        f_ci = go.Figure(
            go.Bar(
                x=cdf["player_name"],
                y=cdf["combined_hp_per100"],
                name="Combined HP",
                marker_color=PBI_TEAL,
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=(cdf["ci_high_hp"] - cdf["combined_hp_per100"]).fillna(0.0).values,
                    arrayminus=(cdf["combined_hp_per100"] - cdf["ci_low_hp"]).fillna(0.0).values,
                    color=PBI_YELLOW,
                ),
            )
        )
        st.plotly_chart(style_pbi_figure(f_ci, "Combined HP Estimate & Individual 95% CIs", "Player", unit_lbl, 340), use_container_width=True)

    # Compact exposure comparison
    f_exp = go.Figure()
    f_exp.add_trace(go.Bar(x=cdf["player_name"], y=cdf["n_hp_global"], name="HP Balls (LI_global >= 1.50)", marker_color=PBI_BLUE_DEEP))
    f_exp.add_trace(go.Scatter(x=cdf["player_name"], y=cdf["m_hp"], name="Distinct HP Matches", yaxis="y2", mode="lines+markers", line=dict(color=PBI_YELLOW, width=3)))
    f_exp.update_layout(yaxis2=dict(title="HP Matches", overlaying="y", side="right", showgrid=False))
    st.plotly_chart(style_pbi_figure(f_exp, "High-Pressure Exposure: HP Balls & Distinct HP Matches", "Player", "HP Balls", 270), use_container_width=True)


def _render_overview(D: Dict[str, Any], trv_f: pd.DataFrame, m_ver: pd.DataFrame, comp_flt: str, team_flt: str) -> None:
    """Phase 3: Storytelling Overview (KPIs -> Top 10 -> Justifications -> Top 10 Graphs -> Player Comparison -> Team/Season -> Competition/Archetypes)."""
    n_matches = int(m_ver["match_id"].nunique())
    n_players = int(pd.concat([trv_f["striker_id"], trv_f["bowler_id"]]).nunique())
    n_innings = int(trv_f.groupby(["match_id", "innings"]).ngroups)
    n_deliv = int(len(trv_f))

    # 1. Overview KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(render_kpi_card("Verified Matches (Track A)", f"{n_matches:,}", "Cricsheet 1-to-1 Reconciled"), unsafe_allow_html=True)
    c2.markdown(render_kpi_card("Active Players", f"{n_players:,}", "Batters & Bowlers in Scope"), unsafe_allow_html=True)
    c3.markdown(render_kpi_card("Verified Innings", f"{n_innings:,}", "1,471 / 1,652 Global (89.0%)"), unsafe_allow_html=True)
    c4.markdown(render_kpi_card("Verified Deliveries", f"{n_deliv:,}", "170,680 Global Track A"), unsafe_allow_html=True)

    if n_deliv == 0:
        st.warning("No verified Track A deliveries match the active filters.")
        return

    # 2. Official Top 10 Batters and Top 10 Bowlers tables
    tpids = (
        set(D["mapping"].loc[D["mapping"]["team_name"] == team_flt, "player_id"].unique())
        if team_flt != "All Teams"
        else None
    )
    bat_df = D["bat"]
    bowl_df = D["bowl"]
    top10_bat = get_official_top10(bat_df, comp_flt, tpids, n=10)
    top10_bowl = get_official_top10(bowl_df, comp_flt, tpids, n=10)

    st.markdown("### TOP 10 PLAYERS — Official V5.0 Pressure Leaderboards")
    st.caption(
        "Primary gate: n_HP >= 100, n_Total >= 300, m_HP >= 12. Combined HP (theta_HP = theta_main + delta_pressure) "
        "reflects baseline + pressure performance combined (not a pure clutch ranking); delta_pressure is EXPERIMENTAL."
    )
    t_bat, t_bowl = st.tabs(["TOP 10 BATTERS", "TOP 10 BOWLERS"])
    with t_bat:
        _render_top10_table(top10_bat, "Batter", "v50_ov_t10_bat")
    with t_bowl:
        _render_top10_table(top10_bowl, "Bowler", "v50_ov_t10_bowl")

    # 3. Why Each Player Is Ranked in the Top 10
    _render_justifications_section(top10_bat, top10_bowl)

    # 4. Top 10 Batter and Bowler graphs
    col_b, col_w = st.columns(2)
    with col_b:
        b_plot = top10_bat.iloc[::-1]
        fig2 = go.Figure(
            go.Bar(
                x=b_plot["combined_hp_per100"],
                y=b_plot["player_name"],
                orientation="h",
                marker_color=PBI_BLUE,
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=(b_plot["ci_high_hp"] - b_plot["combined_hp_per100"]).fillna(0.0).values,
                    arrayminus=(b_plot["combined_hp_per100"] - b_plot["ci_low_hp"]).fillna(0.0).values,
                    color=PBI_YELLOW,
                ),
            )
        )
        st.plotly_chart(style_pbi_figure(fig2, "Top Batters — Combined HP (theta_HP, 95% CI)", "Runs / 100 Balls", "Batter"), use_container_width=True)

    with col_w:
        w_plot = top10_bowl.iloc[::-1]
        fig3 = go.Figure(
            go.Bar(
                x=w_plot["combined_hp_per100"],
                y=w_plot["player_name"],
                orientation="h",
                marker_color=PBI_CORAL,
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=(w_plot["ci_high_hp"] - w_plot["combined_hp_per100"]).fillna(0.0).values,
                    arrayminus=(w_plot["combined_hp_per100"] - w_plot["ci_low_hp"]).fillna(0.0).values,
                    color=PBI_YELLOW,
                ),
            )
        )
        st.plotly_chart(style_pbi_figure(fig3, "Top Bowlers — Combined HP Prevention (95% CI)", "Runs Prevented / 100 Balls", "Bowler"), use_container_width=True)

    # 5. Interactive Player Comparison
    _render_player_comparison(bat_df, bowl_df, comp_flt, tpids)

    # 6. Team Performance and Season Trends
    col_l, col_r = st.columns(2)
    with col_l:
        home_m = m_ver[["match_id", "home_team", "home_team_id", "win_team_id"]].rename(columns={"home_team": "team", "home_team_id": "tid"})
        away_m = m_ver[["match_id", "away_team", "away_team_id", "win_team_id"]].rename(columns={"away_team": "team", "away_team_id": "tid"})
        tm = pd.concat([home_m, away_m], ignore_index=True)
        tm["won"] = (tm["tid"] == tm["win_team_id"]).astype(int)
        t_agg = tm.groupby("team", as_index=False).agg(matches=("match_id", "nunique"), wins=("won", "sum"))
        t_agg["win_pct"] = 100.0 * t_agg["wins"] / np.maximum(t_agg["matches"], 1)
        t_top = t_agg.sort_values(["wins", "win_pct"], ascending=[False, False]).head(12)

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=t_top["team"], y=t_top["wins"], name="Wins", marker_color=PBI_BLUE))
        fig1.add_trace(go.Scatter(x=t_top["team"], y=t_top["win_pct"], name="Win %", yaxis="y2", mode="lines+markers", line=dict(color=PBI_YELLOW, width=2.5)))
        fig1.update_layout(yaxis2=dict(title="Win %", overlaying="y", side="right", range=[0, 105], showgrid=False))
        st.plotly_chart(style_pbi_figure(fig1, "Team Performance Comparison (Top 12 by Wins)", "Team", "Wins (matches)"), use_container_width=True)

    with col_r:
        seas = trv_f.groupby("year", as_index=False).agg(
            runs=("actual_total_runs", "sum"),
            wickets=("wicket_inc", "sum"),
            balls=("legal_ball_inc", "sum"),
        ).sort_values("year")
        seas["run_rate"] = 6.0 * seas["runs"] / np.maximum(seas["balls"], 1)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(x=seas["year"].astype(str), y=seas["runs"], name="Total Runs", marker_color=PBI_BLUE_DEEP))
        fig4.add_trace(go.Scatter(x=seas["year"].astype(str), y=seas["run_rate"], name="Run Rate (RPO)", yaxis="y2", mode="lines+markers", line=dict(color=PBI_CORAL, width=3)))
        fig4.update_layout(yaxis2=dict(title="Runs / Over", overlaying="y", side="right", showgrid=False))
        st.plotly_chart(style_pbi_figure(fig4, "Runs & Scoring Rate Trends Across Seasons", "Season Year", "Total Runs"), use_container_width=True)

    # 7. Competition Distribution and Archetype Analysis
    col_c, col_p = st.columns(2)
    with col_c:
        comp_inn = trv_f.groupby(["match_id", "innings", "match_format"], as_index=False)["actual_total_runs"].sum()
        fig5 = go.Figure()
        for fmt, clr in [("T20", PBI_BLUE), ("T20I", PBI_CORAL)]:
            sub_c = comp_inn[comp_inn["match_format"] == fmt]
            if len(sub_c) > 0:
                fig5.add_trace(go.Box(y=sub_c["actual_total_runs"], name="IPL (T20)" if fmt == "T20" else "Men's T20I", marker_color=clr))
        st.plotly_chart(style_pbi_figure(fig5, "Competition-Level Innings Score Distribution", "Competition", "Innings Total Runs"), use_container_width=True)

    with col_p:
        arch_b = bat_df[bat_df["eligible"]]["archetype"].value_counts()
        arch_w = bowl_df[bowl_df["eligible"]]["archetype"].value_counts()
        all_a = sorted(set(arch_b.index) | set(arch_w.index))
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(x=all_a, y=[int(arch_b.get(a, 0)) for a in all_a], name="Batters (n=89)", marker_color=PBI_BLUE))
        fig6.add_trace(go.Bar(x=all_a, y=[int(arch_w.get(a, 0)) for a in all_a], name="Bowlers (n=82)", marker_color=PBI_CORAL))
        fig6.update_layout(barmode="group")
        st.plotly_chart(style_pbi_figure(fig6, "V5.0 Pressure Archetype Distribution", "Archetype", "Eligible Players"), use_container_width=True)


def _render_team_analysis(D: Dict[str, Any], comp: str, season: str) -> None:
    """Phase 4: Interactive Team & Squad Analysis with TEAM -> PLAYER drill-down."""
    mapping = D["mapping"]
    teams = sorted(mapping["team_name"].dropna().unique().tolist())
    default_idx = teams.index("Rajasthan Royals") if "Rajasthan Royals" in teams else 0
    sel_team = st.selectbox("Select Franchise / National Team", teams, index=default_idx, key="v50_team_page_sel")

    trv_t, m_t = _filter_trv_and_matches(D, comp, season, sel_team)
    if len(m_t) == 0:
        st.warning(f"No verified Track A matches found for {sel_team} under the active competition/season filters.")
        return

    team_ids = set(mapping.loc[mapping["team_name"] == sel_team, "team_id"].unique())
    wins = int(m_t["win_team_id"].isin(team_ids).sum())
    decided = int(m_t["win_team_id"].notna().sum())
    losses = max(decided - wins, 0)
    win_pct = 100.0 * wins / max(decided, 1)

    bat_team_rows = trv_t[trv_t["batting_team_id"].isin(team_ids)]
    bowl_team_rows = trv_t[trv_t["bowling_team_id"].isin(team_ids)]
    bat_val = float(bat_team_rows["delta_re_total"].mean()) * 100.0 if len(bat_team_rows) else np.nan
    bowl_val = float(bowl_team_rows["bowling_team_delta_re_total"].mean()) * 100.0 if len(bowl_team_rows) else np.nan

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(render_kpi_card("Verified Matches", f"{len(m_t):,}", f"{decided} decided"), unsafe_allow_html=True)
    k2.markdown(render_kpi_card("Wins / Losses", f"{wins} / {losses}", f"Win Rate: {win_pct:.1f}%"), unsafe_allow_html=True)
    k3.markdown(render_kpi_card("Team Batting DeltaRE", f"{bat_val:+.2f}" if pd.notna(bat_val) else "N/A", "Runs / 100 balls"), unsafe_allow_html=True)
    k4.markdown(render_kpi_card("Team Bowling DeltaRE", f"{bowl_val:+.2f}" if pd.notna(bowl_val) else "N/A", "Runs prevented / 100b"), unsafe_allow_html=True)
    squad_pids = set(mapping.loc[mapping["team_name"] == sel_team, "player_id"].unique())
    k5.markdown(render_kpi_card("Mapped Squad Pool", f"{len(squad_pids):,}", "Historical & Current"), unsafe_allow_html=True)

    # Charts 1 & 2: Season evolution & Batting vs Bowling contribution
    m_t["year"] = pd.to_datetime(m_t["match_date"], errors="coerce").dt.year.fillna(2024).astype(int)
    m_t["team_won"] = m_t["win_team_id"].isin(team_ids).astype(int)
    seas_m = m_t.groupby("year", as_index=False).agg(matches=("match_id", "nunique"), wins=("team_won", "sum"))

    c1, c2 = st.columns(2)
    with c1:
        f1 = go.Figure()
        f1.add_trace(go.Bar(x=seas_m["year"].astype(str), y=seas_m["matches"], name="Matches", marker_color=PBI_BLUE_DEEP))
        f1.add_trace(go.Bar(x=seas_m["year"].astype(str), y=seas_m["wins"], name="Wins", marker_color=PBI_BLUE))
        f1.update_layout(barmode="group")
        st.plotly_chart(style_pbi_figure(f1, "1. Team Performance Across Seasons", "Season", "Count"), use_container_width=True)

    with c2:
        b_s = bat_team_rows.groupby("year", as_index=False)["delta_re_total"].mean()
        w_s = bowl_team_rows.groupby("year", as_index=False)["bowling_team_delta_re_total"].mean()
        bw = b_s.merge(w_s, on="year", how="outer").sort_values("year")
        f2 = go.Figure()
        f2.add_trace(go.Scatter(x=bw["year"].astype(str), y=bw["delta_re_total"] * 100.0, name="Batting (runs/100b)", mode="lines+markers", line=dict(color=PBI_BLUE, width=3)))
        f2.add_trace(go.Scatter(x=bw["year"].astype(str), y=bw["bowling_team_delta_re_total"] * 100.0, name="Bowling (runs/100b)", mode="lines+markers", line=dict(color=PBI_CORAL, width=3)))
        st.plotly_chart(style_pbi_figure(f2, "2. Batting vs Bowling Contribution by Season", "Season", "DeltaRE / 100 Balls"), use_container_width=True)

    # Key Batters & Bowlers + TEAM -> PLAYER drill-down
    bat_sq = D["bat"][D["bat"]["player_id"].isin(squad_pids) & D["bat"]["eligible"]].head(10)
    bowl_sq = D["bowl"][D["bowl"]["player_id"].isin(squad_pids) & D["bowl"]["eligible"]].head(10)
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Key Eligible Batters (V5.0)")
        st.dataframe(bat_sq[["rank_hp", "player_name", "main_effect_per100", "combined_hp_per100", "archetype", "n_hp_global"]], use_container_width=True, hide_index=True)
    with c4:
        st.subheader("Key Eligible Bowlers (V5.0)")
        st.dataframe(bowl_sq[["rank_hp", "player_name", "main_effect_per100", "combined_hp_per100", "archetype", "n_hp_global"]], use_container_width=True, hide_index=True)

    # Drill-down selector
    sq_names = sorted(set(bat_sq["player_name"]).union(set(bowl_sq["player_name"])))
    if sq_names:
        st.markdown("---")
        d1, d2 = st.columns([3, 1])
        chosen_p = d1.selectbox("Drill Down: Explore Squad Player Profile", sq_names, key="v50_team_drill_p")
        d2.button(
            "Open in Player Explorer ->",
            key="v50_team_to_player_btn",
            on_click=_go_to_v50_player,
            args=("v50_team_drill_p", "Batter" if chosen_p in set(bat_sq["player_name"]) else "Bowler"),
        )


def _render_player_explorer(D: Dict[str, Any], comp: str, season: str, search_txt: str, role_flt: str) -> None:
    """Phase 5: Power BI-Style Player Profile & Match History (with PLAYER -> MATCH drill-down)."""
    trv_f, m_ver = _filter_trv_and_matches(D, comp, season, "All Teams")
    bat_df = D["bat"]
    bowl_df = D["bowl"]

    all_players = sorted(set(bat_df["player_name"].dropna()).union(set(bowl_df["player_name"].dropna())))
    if search_txt.strip():
        q = search_txt.strip().lower()
        filtered_p = [p for p in all_players if q in p.lower()]
        if filtered_p:
            all_players = filtered_p

    default_p = st.session_state.get("v50_selected_player_name", "Jos Buttler")
    if default_p not in all_players and all_players:
        default_p = all_players[0]

    col_left, col_main = st.columns([1, 3])
    with col_left:
        st.markdown('<div class="pbi-card"><b>Player Filter Panel</b></div>', unsafe_allow_html=True)
        t10_b_names = [f"Batter #{int(r['rank_hp']):02d}: {r['player_name']}" for _, r in get_official_top10(bat_df, comp, n=10).iterrows()]
        t10_w_names = [f"Bowler #{int(r['rank_hp']):02d}: {r['player_name']}" for _, r in get_official_top10(bowl_df, comp, n=10).iterrows()]
        quick_opts = ["(Manual Select)"] + t10_b_names + t10_w_names
        quick_pick = st.selectbox("Quick Jump: Official Top 10", quick_opts, key="v50_pe_quick_t10")
        if quick_pick != "(Manual Select)":
            q_role, q_name = quick_pick.split(": ", 1)
            default_p = q_name
            st.session_state["v50_selected_player_name"] = q_name
            st.session_state["v50_pe_role"] = "Batter" if q_role.startswith("Batter") else "Bowler"

        sel_player = st.selectbox("Player", all_players, index=all_players.index(default_p) if default_p in all_players else 0, key="v50_pe_player")
        st.session_state["v50_selected_player_name"] = sel_player

        b_row = bat_df[bat_df["player_name"] == sel_player]
        w_row = bowl_df[bowl_df["player_name"] == sel_player]
        avail_roles = []
        if len(b_row) > 0:
            avail_roles.append("Batter")
        if len(w_row) > 0:
            avail_roles.append("Bowler")
        if role_flt == "Batters" and "Batter" in avail_roles:
            avail_roles = ["Batter"]
        elif role_flt == "Bowlers" and "Bowler" in avail_roles:
            avail_roles = ["Bowler"]
        sel_role = st.radio("Profile View", avail_roles or ["Batter"], key="v50_pe_role")

        # Teams mapped
        pids = set(b_row["player_id"]).union(set(w_row["player_id"]))
        teams_p = sorted(D["mapping"].loc[D["mapping"]["player_id"].isin(pids), "team_name"].dropna().unique().tolist())
        st.markdown(
            f'<div class="pbi-card">'
            f'<div style="display:flex;align-items:center;">'
            f'<div class="pbi-avatar">{_initials(sel_player)}</div>'
            f'<div><div style="font-size:17px;font-weight:700;">{sel_player}</div>'
            f'<div style="font-size:12px;color:{PBI_MUTED};">{sel_role}</div></div>'
            f'</div>'
            f'<div style="margin-top:10px;font-size:12px;color:{PBI_MUTED};"><b>Teams:</b> {", ".join(teams_p[:5]) if teams_p else "N/A"}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_main:
        pid = int(b_row["player_id"].iloc[0]) if sel_role == "Batter" and len(b_row) else (int(w_row["player_id"].iloc[0]) if len(w_row) else -1)
        if sel_role == "Batter":
            p_deliv = trv_f[(trv_f["striker_id"] == pid) & (trv_f["is_ball_faced"] == True)].copy()
            v50_r = b_row.iloc[0] if len(b_row) else None
            # Role-aware Batter KPIs
            m_cnt = int(p_deliv["match_id"].nunique())
            inn_cnt = int(p_deliv.groupby(["match_id", "innings"]).ngroups)
            tot_runs = int(p_deliv["batter_runs"].sum())
            tot_balls = int(len(p_deliv))
            outs = int((p_deliv["dismissed_player_id"] == pid).sum()) if "dismissed_player_id" in p_deliv else 0
            bat_avg = f"{tot_runs / outs:.2f}" if outs > 0 else "N/A"
            sr = f"{100.0 * tot_runs / tot_balls:.1f}" if tot_balls > 0 else "N/A"
            inn_scores = p_deliv.groupby(["match_id", "innings"], as_index=False).agg(runs=("batter_runs", "sum"), balls=("batter_runs", "size"), year=("year", "first"), match_date=("match_date", "first"), match_format=("match_format", "first"))
            hs = f"{int(inn_scores['runs'].max())}" if len(inn_scores) else "N/A"
            f50 = int((inn_scores["runs"] >= 50).sum()) if len(inn_scores) else 0
            f100 = int((inn_scores["runs"] >= 100).sum()) if len(inn_scores) else 0

            k_r1 = st.columns(3)
            k_r1[0].markdown(render_kpi_card("Matches / Inn", f"{m_cnt} / {inn_cnt}"), unsafe_allow_html=True)
            k_r1[1].markdown(render_kpi_card("Runs (HS)", f"{tot_runs:,} ({hs})", f"50s/100s: {f50}/{f100}"), unsafe_allow_html=True)
            k_r1[2].markdown(render_kpi_card("Avg / SR", f"{bat_avg} / {sr}"), unsafe_allow_html=True)
            if v50_r is not None:
                k_r2 = st.columns(2)
                k_r2[0].markdown(render_kpi_card("V5.0 Combined HP", f"{v50_r['combined_hp_per100']:+.2f}", f"95% CI [{v50_r['ci_low_hp']:+.1f}, {v50_r['ci_high_hp']:+.1f}]"), unsafe_allow_html=True)
                k_r2[1].markdown(render_kpi_card("Archetype", str(v50_r["archetype"]).split("/")[0].strip(), f"HP Balls: {int(v50_r['n_hp_global'])}"), unsafe_allow_html=True)
        else:
            p_deliv = trv_f[trv_f["bowler_id"] == pid].copy()
            v50_r = w_row.iloc[0] if len(w_row) else None
            m_cnt = int(p_deliv["match_id"].nunique())
            legal_b = int(p_deliv["legal_ball_inc"].sum())
            overs_str = f"{legal_b // 6}.{legal_b % 6}"
            wkts = int(p_deliv["is_bowler_wicket"].sum())
            runs_c = int((p_deliv["batter_runs"] + p_deliv["bowler_chargeable_extras"]).sum())
            econ = f"{6.0 * runs_c / legal_b:.2f}" if legal_b > 0 else "N/A"
            b_avg = f"{runs_c / wkts:.2f}" if wkts > 0 else "N/A"
            b_sr = f"{legal_b / wkts:.1f}" if wkts > 0 else "N/A"
            inn_scores = p_deliv.groupby(["match_id", "innings"], as_index=False).agg(wkts=("is_bowler_wicket", "sum"), runs=("batter_runs", "sum"), balls=("legal_ball_inc", "sum"), year=("year", "first"), match_date=("match_date", "first"), match_format=("match_format", "first"))
            best_row = inn_scores.sort_values(["wkts", "runs"], ascending=[False, True]).head(1)
            bbf = f"{int(best_row['wkts'].iloc[0])}/{int(best_row['runs'].iloc[0])}" if len(best_row) else "N/A"

            k_r1 = st.columns(3)
            k_r1[0].markdown(render_kpi_card("Matches / Overs", f"{m_cnt} / {overs_str}"), unsafe_allow_html=True)
            k_r1[1].markdown(render_kpi_card("Wickets (Best)", f"{wkts} ({bbf})"), unsafe_allow_html=True)
            k_r1[2].markdown(render_kpi_card("Econ / Avg / SR", f"{econ} / {b_avg} / {b_sr}"), unsafe_allow_html=True)
            if v50_r is not None:
                k_r2 = st.columns(2)
                k_r2[0].markdown(render_kpi_card("V5.0 Combined HP", f"{v50_r['combined_hp_per100']:+.2f}", f"95% CI [{v50_r['ci_low_hp']:+.1f}, {v50_r['ci_high_hp']:+.1f}]"), unsafe_allow_html=True)
                k_r2[1].markdown(render_kpi_card("Archetype", str(v50_r["archetype"]).split("/")[0].strip(), f"HP Balls: {int(v50_r['n_hp_global'])}"), unsafe_allow_html=True)

        if len(p_deliv) == 0:
            st.info("No Track A deliveries found for this player under the active filters.")
            return

        # 6 Player Performance Charts (3 rows x 2 cols)
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            y_agg = inn_scores.groupby("year", as_index=False)["runs" if sel_role == "Batter" else "wkts"].sum()
            f_yr = go.Figure(go.Bar(x=y_agg["year"].astype(str), y=y_agg.iloc[:, 1], marker_color=PBI_BLUE))
            st.plotly_chart(style_pbi_figure(f_yr, "1. Year-by-Year Performance", "Year", "Runs" if sel_role == "Batter" else "Wickets", 300), use_container_width=True)
        with r1c2:
            inn_s = inn_scores.sort_values("match_date").reset_index(drop=True)
            inn_s["cum_val"] = inn_s["runs" if sel_role == "Batter" else "wkts"].cumsum()
            f_prog = go.Figure(go.Scatter(x=inn_s.index + 1, y=inn_s["cum_val"], mode="lines", line=dict(color=PBI_CORAL, width=2.5)))
            st.plotly_chart(style_pbi_figure(f_prog, "2. Career Cumulative Progression", "Innings #", "Cumulative " + ("Runs" if sel_role == "Batter" else "Wickets"), 300), use_container_width=True)

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            f_dist = go.Figure(go.Histogram(x=inn_scores["runs" if sel_role == "Batter" else "wkts"], nbinsx=15, marker_color=PBI_TEAL))
            st.plotly_chart(style_pbi_figure(f_dist, "3. Innings Performance Distribution", "Runs" if sel_role == "Batter" else "Wickets", "Innings Count", 300), use_container_width=True)
        with r2c2:
            c_agg = p_deliv.groupby("match_format", as_index=False)["delta_re_player_attrib"].mean()
            mult = 100.0 if sel_role == "Batter" else -100.0
            f_cmp = go.Figure(go.Bar(x=c_agg["match_format"], y=c_agg["delta_re_player_attrib"] * mult, marker_color=[PBI_BLUE, PBI_YELLOW][: len(c_agg)]))
            st.plotly_chart(style_pbi_figure(f_cmp, "4. Competition Comparison (Raw DeltaRE / 100b)", "Format", "DeltaRE / 100b", 300), use_container_width=True)

        r3c1, r3c2 = st.columns(2)
        with r3c1:
            p_deliv["tier"] = np.where(p_deliv["LI_global"] >= 1.50, "High Pressure (LI>=1.50)", "Normal (LI<1.50)")
            t_agg = p_deliv.groupby("tier", as_index=False)["delta_re_player_attrib"].mean()
            mult = 100.0 if sel_role == "Batter" else -100.0
            f_pr = go.Figure(go.Bar(x=t_agg["tier"], y=t_agg["delta_re_player_attrib"] * mult, marker_color=[PBI_CORAL, PBI_BLUE][: len(t_agg)]))
            st.plotly_chart(style_pbi_figure(f_pr, "5. Pressure vs Normal Performance (Unadjusted)", "Situation", "DeltaRE / 100b", 300), use_container_width=True)
        with r3c2:
            if v50_r is not None:
                lbls = ["Main (theta_main)", "Uplift (delta_pres)", "Combined HP (theta_HP)"]
                vals = [v50_r["main_effect_per100"], v50_r["pressure_interaction_per100"], v50_r["combined_hp_per100"]]
                hi = [v50_r["ci_high_main"] - vals[0], v50_r["ci_high_pres"] - vals[1], v50_r["ci_high_hp"] - vals[2]]
                lo = [vals[0] - v50_r["ci_low_main"], vals[1] - v50_r["ci_low_pres"], vals[2] - v50_r["ci_low_hp"]]
                f_ci = go.Figure(go.Bar(x=lbls, y=vals, marker_color=[PBI_BLUE, PBI_YELLOW, PBI_CORAL], error_y=dict(type="data", symmetric=False, array=hi, arrayminus=lo, color=PBI_TEXT)))
                st.plotly_chart(style_pbi_figure(f_ci, "6. V5.0 Effects & 95% Paired Bootstrap CIs", "Component", "Runs / 100b", 300), use_container_width=True)

        # Match History & PLAYER -> MATCH drill-down
        mh = inn_scores.merge(m_ver[["match_id", "home_team", "away_team", "result"]], on="match_id", how="left").sort_values("match_date", ascending=False)
        mh["match_label"] = mh["match_date"].astype(str) + " | " + mh["home_team"] + " vs " + mh["away_team"]
        st.subheader("Match History (Verified Track A)")
        st.dataframe(mh[["match_date", "match_format", "home_team", "away_team", "runs" if sel_role == "Batter" else "wkts", "balls", "result"]].head(25), use_container_width=True, hide_index=True)

        if len(mh) > 0:
            dm1, dm2 = st.columns([3, 1])
            sel_ml = dm1.selectbox("Drill Down: Inspect Match Details", mh["match_label"].unique().tolist(), key="v50_pe_match_sel")
            m_map = dict(zip(mh["match_label"], mh["match_id"]))
            dm2.button(
                "Open in Match Explorer ->",
                key="v50_player_to_match_btn",
                on_click=_go_to_v50_match,
                args=(m_map, "v50_pe_match_sel"),
            )


def _render_match_explorer(D: Dict[str, Any], comp: str, season: str, team: str) -> None:
    """Phase 6: Interactive Verified Match Explorer (Track A Only)."""
    st.info("Track A Governance: Only Cricsheet-verified score-aware matches (170,680 deliveries / 725 matches) are displayed. 181 unverified/blocked innings are excluded.")
    trv_f, m_ver = _filter_trv_and_matches(D, comp, season, team)
    if len(m_ver) == 0:
        st.warning("No verified Track A matches match the active filters.")
        return

    m_ver = m_ver.sort_values("match_date", ascending=False).copy()
    m_ver["label"] = m_ver["match_date"].astype(str) + " | " + m_ver["home_team"] + " vs " + m_ver["away_team"] + " (" + m_ver["match_format"] + ")"
    labels = m_ver["label"].tolist()
    pre_mid = st.session_state.get("v50_selected_match_id")
    def_idx = 0
    if pre_mid is not None and pre_mid in set(m_ver["match_id"]):
        def_idx = m_ver["match_id"].tolist().index(pre_mid)

    sel_label = st.selectbox("Select Verified Match", labels, index=def_idx, key="v50_me_sel")
    m_row = m_ver.iloc[labels.index(sel_label)]
    mid = int(m_row["match_id"])
    sub = trv_f[trv_f["match_id"] == mid].copy()

    inn_tots = sub.groupby("innings", as_index=False).agg(runs=("actual_total_runs", "sum"), wkts=("wicket_inc", "sum"), balls=("legal_ball_inc", "sum"))
    s1 = f"{int(inn_tots.loc[inn_tots['innings']==1, 'runs'].iloc[0])}/{int(inn_tots.loc[inn_tots['innings']==1, 'wkts'].iloc[0])}" if (inn_tots["innings"] == 1).any() else "N/A"
    s2 = f"{int(inn_tots.loc[inn_tots['innings']==2, 'runs'].iloc[0])}/{int(inn_tots.loc[inn_tots['innings']==2, 'wkts'].iloc[0])}" if (inn_tots["innings"] == 2).any() else "N/A"

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(render_kpi_card("Date & Format", str(m_row["match_date"]), str(m_row["match_format"])), unsafe_allow_html=True)
    k2.markdown(render_kpi_card("Venue Country", str(m_row["venue_country"])), unsafe_allow_html=True)
    k3.markdown(render_kpi_card("Scores (Inn 1 | Inn 2)", f"{s1} | {s2}"), unsafe_allow_html=True)
    k4.markdown(render_kpi_card("Result", str(m_row["result"])[:32]), unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_wp = go.Figure()
        for inn in sorted(sub["innings"].unique()):
            si = sub[sub["innings"] == inn]
            fig_wp.add_trace(go.Scatter(x=si["event_index_in_innings"], y=si["wp_inn1_team_oof"], mode="lines", name=f"Innings {inn} WP", line=dict(color=PBI_BLUE if inn == 1 else PBI_CORAL, width=2.5)))
        hi_pts = sub[sub["LI_global"] >= 1.50]
        fig_wp.add_trace(go.Scatter(x=hi_pts["event_index_in_innings"], y=hi_pts["wp_inn1_team_oof"], mode="markers", name="LI_global >= 1.50", marker=dict(color=PBI_YELLOW, size=6)))
        st.plotly_chart(style_pbi_figure(fig_wp, "Win Probability & High-Leverage Timeline", "Delivery Index", "P(Inn1 Team Wins)"), use_container_width=True)

    with c2:
        ph = sub.groupby(["innings", "innings_phase"], as_index=False).agg(runs=("actual_total_runs", "sum"), wkts=("wicket_inc", "sum"))
        ph["label"] = "Inn " + ph["innings"].astype(str) + " " + ph["innings_phase"].astype(str)
        f_ph = go.Figure(go.Bar(x=ph["label"], y=ph["runs"], marker_color=PBI_BLUE, text=ph["wkts"].astype(str) + "w", textposition="outside"))
        st.plotly_chart(style_pbi_figure(f_ph, "Phase-Level Runs & Wickets", "Innings Phase", "Runs"), use_container_width=True)

    b_col, w_col = st.columns(2)
    with b_col:
        st.subheader("Match Batting Contributions")
        bm = sub[sub["is_ball_faced"] == True].groupby("striker_name", as_index=False).agg(runs=("batter_runs", "sum"), balls=("batter_runs", "size"), delta_re=("delta_re_player_attrib", "sum")).sort_values("runs", ascending=False)
        st.dataframe(bm, use_container_width=True, hide_index=True)
    with w_col:
        st.subheader("Match Bowling Contributions")
        wm = sub.groupby("bowler_name", as_index=False).agg(balls=("legal_ball_inc", "sum"), wkts=("is_bowler_wicket", "sum"), runs_conceded=("actual_total_runs", "sum"), delta_re_prevented=("delta_re_player_attrib", lambda s: -float(s.sum()))).sort_values("delta_re_prevented", ascending=False)
        st.dataframe(wm, use_container_width=True, hide_index=True)


def _render_pressure_analytics(D: Dict[str, Any]) -> None:
    """Phase 7: Preserved 3-Tab V5.0 Pressure Analytics with Power BI styling & clear governance."""
    st.markdown(
        '<div class="pbi-card">'
        '<b>Estimand & Gate Governance:</b> V5.0 separates baseline <code>theta_main</code>, standalone pressure uplift <code>delta_pressure</code> '
        '(<b>EXPERIMENTAL</b>, weak split-half Spearman 0.2265/0.1768), and combined HP <code>theta_HP = theta_main + delta_pressure</code> '
        '(not a pure clutch ranking). Primary global gate: <code>100/300/12</code>; innings-split <code>40/150/5</code> is exploratory. '
        '<code>LI_global</code> (absolute match leverage) and <code>LI_innings</code> (within-innings relative leverage) are reported separately.'
        '</div>',
        unsafe_allow_html=True,
    )
    tab1, tab2, tab3 = st.tabs(
        [
            "1. Global T20 Pressure Leaderboard",
            "2. Match Pressure Analysis (Track A Verified)",
            "3. Optional Franchise / Squad View",
        ]
    )
    with tab1:
        disc = st.radio("Discipline", ["Batters", "Bowlers"], horizontal=True, key="v50_disc")
        df = D["bat"] if disc == "Batters" else D["bowl"]
        el = df[df["eligible"] == True].copy()
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(render_kpi_card("Eligible (100/300/12)", str(len(el))), unsafe_allow_html=True)
        c2.markdown(render_kpi_card("Elite Clutch", str(int((el["archetype"] == "ELITE CLUTCH PERFORMER").sum()))), unsafe_allow_html=True)
        c3.markdown(render_kpi_card("Crisis Specialists", str(int((el["archetype"] == "CRISIS / RESCUE SPECIALIST").sum()))), unsafe_allow_html=True)
        c4.markdown(render_kpi_card("Unclassified", str(int((el["archetype"] == "UNCLASSIFIED / INSUFFICIENT EVIDENCE").sum()))), unsafe_allow_html=True)

        cols_show = ["rank_hp", "player_name", "archetype", "main_effect_per100", "pressure_interaction_per100", "combined_hp_per100", "ci_low_hp", "ci_high_hp", "inn1_hp_effect", "inn2_hp_effect", "total_opportunities", "n_hp_global", "n_hp_innings", "m_hp", "reliability"]
        st.dataframe(el[cols_show].head(30), use_container_width=True, hide_index=True)

        fig_q = go.Figure()
        for arch, grp in el.groupby("archetype"):
            fig_q.add_trace(go.Scatter(x=grp["main_effect_per100"], y=grp["pressure_interaction_per100"], mode="markers", name=arch, marker=dict(size=np.clip(np.sqrt(grp["n_hp_global"]) * 0.85, 6, 17)), text=grp["player_name"], hoverinfo="text+x+y"))
        fig_q.add_hline(y=0, line_dash="dash", line_color="#94A3B8")
        fig_q.add_vline(x=0, line_dash="dash", line_color="#94A3B8")
        st.plotly_chart(style_pbi_figure(fig_q, f"{disc} Pressure Archetype Quadrant", "Main Effect (theta_main / 100b)", "Pressure Uplift (delta_pressure / 100b)", 440), use_container_width=True)

    with tab2:
        st.info("Showing ONLY Cricsheet-verified score-aware Track A matches (170,680 deliveries / 725 matches). Track B resource proxies are never shown here.")
        trv = D["trv"]
        m_df = D["matches"][D["matches"]["match_id"].isin(trv["match_id"].unique())].copy()
        m_df["label"] = m_df["match_date"].astype(str) + " | " + m_df["home_team"] + " vs " + m_df["away_team"] + " (" + m_df["match_format"] + ")"
        sel_label = st.selectbox("Select Verified Match", m_df["label"].tolist(), key="v50_match_sel")
        sel_mid = int(m_df.loc[m_df["label"] == sel_label, "match_id"].iloc[0])
        sub_m = trv[trv["match_id"] == sel_mid].copy()
        sub_m["cum_score"] = sub_m.groupby("innings")["actual_total_runs"].cumsum()
        hi_m = sub_m[sub_m["LI_global"] >= 1.50]
        st.subheader(f"High-Leverage Deliveries (LI_global >= 1.50): {len(hi_m)} balls")
        st.dataframe(hi_m[["innings", "overid", "striker_name", "bowler_name", "cum_score", "actual_total_runs", "wp_inn1_team_oof", "LI_global", "LI_innings", "delta_re_total"]].head(50), use_container_width=True, hide_index=True)

    with tab3:
        st.caption("Franchise & national-team filters operate strictly as post-hoc presentation views and never retrain or alter the global V5.0 engine.")
        mapping = D["mapping"]
        sel_comp = st.selectbox("Competition Filter", ["All Competitions", "IPL (T20)", "Men's T20I"], key="v50_pa_comp_flt")
        sel_team = st.selectbox("Team / Franchise Filter", ["All Teams"] + sorted(mapping["team_name"].dropna().unique().tolist()), key="v50_pa_team_flt")
        role_f = st.radio("Role", ["Batters", "Bowlers"], horizontal=True, key="v50_team_role")
        filt = (D["bat"] if role_f == "Batters" else D["bowl"])
        filt = filt[filt["eligible"] == True].copy()
        if sel_comp == "IPL (T20)":
            filt = filt[filt["ipl_balls"] > 0]
        elif sel_comp == "Men's T20I":
            filt = filt[filt["t20i_balls"] > 0]
        if sel_team != "All Teams":
            tpids = set(mapping.loc[mapping["team_name"] == sel_team, "player_id"].unique())
            filt = filt[filt["player_id"].isin(tpids)]
        st.dataframe(filt[["rank_hp", "player_name", "archetype", "main_effect_per100", "pressure_interaction_per100", "combined_hp_per100", "ci_low_hp", "ci_high_hp", "n_hp_global", "total_opportunities"]], use_container_width=True, hide_index=True)


def render_v50_dashboard() -> None:
    """Render the redesigned Power BI-inspired V5.0 Universal T20 Pressure Engine dashboard."""
    inject_v5_powerbi_theme()
    try:
        D = load_v50_dashboard_data()
    except Exception as exc:
        st.error(f"V5.0 outputs not found or incomplete: {exc}. Run `scripts/run_v5_0_pipeline.py` first.")
        return

    if "v50_nav_page" not in st.session_state:
        st.session_state["v50_nav_page"] = V50_NAV_PAGES[0]

    # Sidebar Navigation & Filters (Phase 2A)
    st.sidebar.markdown("---")
    nav_page = st.sidebar.radio("Navigation", V50_NAV_PAGES, key="v50_nav_page")
    st.sidebar.markdown("### Global Filters")
    comp_flt = st.sidebar.selectbox("Competition", ["All Competitions", "IPL (T20)", "Men's T20I"], key="v50_comp_flt")
    years_avail = sorted(D["trv"]["year"].unique().tolist(), reverse=True)
    season_flt = st.sidebar.selectbox("Season / Year", ["All Seasons"] + [str(y) for y in years_avail], key="v50_season_flt")
    teams_avail = ["All Teams"] + sorted(D["mapping"]["team_name"].dropna().unique().tolist())
    team_flt = st.sidebar.selectbox("Franchise / Team", teams_avail, key="v50_team_flt")
    role_flt = st.sidebar.selectbox("Role", ["All", "Batters", "Bowlers"], key="v50_role_flt")
    search_txt = st.sidebar.text_input("Player Search", value="", key="v50_player_search")
    st.sidebar.button("Reset Filters", on_click=_reset_v50_filters, key="v50_reset_btn")

    trv_f, m_ver = _filter_trv_and_matches(D, comp_flt, season_flt, team_flt)

    # Main Header (Phase 2B)
    st.markdown(
        f"""
        <div class="pbi-header">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>
                    <h1 style="margin:0; font-size:24px;">SupeRR Intelligence — Universal T20 Pressure Performance Analytics</h1>
                    <p style="margin:4px 0 0 0; color:{PBI_MUTED}; font-size:13px;">
                        Engine: <b>V5.0 Track A (Cricsheet Score-Aware)</b> &nbsp;|&nbsp;
                        Scope: <b>{comp_flt}</b> &bull; <b>{season_flt}</b> &bull; <b>{team_flt}</b> &nbsp;|&nbsp;
                        Coverage: <b>{len(m_ver):,}</b> matches &bull; <b>{len(trv_f):,}</b> deliveries
                    </p>
                </div>
                <span class="pbi-badge">V5.0 TRACK A — POWER BI EDITION</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if nav_page == "1. Overview":
        _render_overview(D, trv_f, m_ver, comp_flt, team_flt)
    elif nav_page == "2. Team Analysis":
        _render_team_analysis(D, comp_flt, season_flt)
    elif nav_page == "3. Player Explorer":
        _render_player_explorer(D, comp_flt, season_flt, search_txt, role_flt)
    elif nav_page == "4. Match Explorer":
        _render_match_explorer(D, comp_flt, season_flt, team_flt)
    else:
        _render_pressure_analytics(D)
