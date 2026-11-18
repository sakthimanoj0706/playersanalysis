"""SupeRR Intelligence V5.0 — Universal T20 Pressure Engine Dashboard Extension."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
V50_DIR = ROOT / "data" / "outputs" / "v5_0"
V44_DIR = ROOT / "data" / "outputs" / "v4_4"
DATA_DIR = ROOT / "data"


@st.cache_data(show_spinner=False)
def load_v50_dashboard_data() -> dict:
    """Load V5.0 Track A leaderboards, innings splits, scales, and verified match moments."""
    bat = pd.read_csv(V50_DIR / "V5_0_GLOBAL_BATTER_PRESSURE.csv")
    bowl = pd.read_csv(V50_DIR / "V5_0_GLOBAL_BOWLER_PRESSURE.csv")
    inn = pd.read_csv(V50_DIR / "V5_0_INNINGS_SPLIT_RANKINGS.csv")
    scales = pd.read_csv(V50_DIR / "V5_0_PRESSURE_SCALES_SUMMARY.csv")
    stab = pd.read_csv(V50_DIR / "V5_0_RANKING_STABILITY.csv")
    trv = pd.read_parquet(V44_DIR / "V4_4_TOTAL_RUN_VALUE.parquet")
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


def _quadrant_fig(df: pd.DataFrame, role: str) -> go.Figure:
    el = df[df["eligible"] == True].copy()
    colors = {
        "ELITE CLUTCH PERFORMER": "#0F766E",
        "CRISIS / RESCUE SPECIALIST": "#2563EB",
        "PRESSURE-SENSITIVE GENERAL PERFORMER": "#D97706",
        "BELOW-AVERAGE UNDER PRESSURE": "#DC2626",
        "UNCLASSIFIED / INSUFFICIENT EVIDENCE": "#64748B",
    }
    fig = go.Figure()
    for arch, grp in el.groupby("archetype"):
        fig.add_trace(
            go.Scatter(
                x=grp["main_effect_per100"],
                y=grp["pressure_interaction_per100"],
                mode="markers",
                name=arch,
                marker=dict(
                    size=np.clip(np.sqrt(grp["n_hp_global"]) * 0.85, 6, 17),
                    color=colors.get(arch, "#64748B"),
                    opacity=0.85,
                ),
                text=grp["player_name"] + "<br>HP balls: " + grp["n_hp_global"].astype(str),
                hoverinfo="text",
            )
        )
    fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8")
    fig.add_vline(x=0, line_dash="dash", line_color="#94A3B8")
    fig.update_layout(
        title=f"{role.title()} Pressure Archetype Quadrant (n={len(el)} eligible)",
        xaxis_title="Main Contribution (runs / 100 deliveries)",
        yaxis_title="Pressure Uplift (LI_global >= 1.50, runs / 100)",
        template="plotly_white",
        height=460,
    )
    return fig


def render_v50_dashboard() -> None:
    """Render the 3-tab V5.0 Universal T20 Pressure Engine dashboard."""
    st.markdown(
        """
        <div class="superr-header">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>
                    <h1 style="margin:0; font-size:24px; color:#0B1B3D;">SupeRR Intelligence V5.0 — Universal T20 Pressure Engine</h1>
                    <p style="margin:4px 0 0 0; color:#475569; font-size:13.5px;">
                        Competition-independent Track A Cricsheet-verified score-aware WP, Global &amp; Innings Leverage Index, and Asymmetric Block-Penalized Ridge RAPM.
                    </p>
                </div>
                <span class="superr-badge">V5.0 TRACK A — SCORE-AWARE VERIFIED</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        D = load_v50_dashboard_data()
    except Exception as exc:
        st.error(f"V5.0 outputs not found or incomplete: {exc}. Run `scripts/run_v5_0_pipeline.py` first.")
        return

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
        c1.metric("Eligible Players (100/300/12)", len(el))
        c2.metric("Elite Clutch", int((el["archetype"] == "ELITE CLUTCH PERFORMER").sum()))
        c3.metric("Crisis Specialists", int((el["archetype"] == "CRISIS / RESCUE SPECIALIST").sum()))
        c4.metric("Unclassified / Uncertain", int((el["archetype"] == "UNCLASSIFIED / INSUFFICIENT EVIDENCE").sum()))

        cols_show = [
            "rank_hp",
            "player_name",
            "archetype",
            "archetype_subtype",
            "main_effect_per100",
            "pressure_interaction_per100",
            "combined_hp_per100",
            "ci_low_hp",
            "ci_high_hp",
            "inn1_hp_effect",
            "inn2_hp_effect",
            "total_opportunities",
            "n_hp_global",
            "n_hp_innings",
            "m_hp",
            "reliability",
        ]
        st.dataframe(el[cols_show].head(30), use_container_width=True, hide_index=True)
        st.plotly_chart(_quadrant_fig(df, "batter" if disc == "Batters" else "bowler"), use_container_width=True)

    with tab2:
        st.info("Showing ONLY Cricsheet-verified score-aware Track A matches (170,680 deliveries / 725 matches). Track B resource proxies are never shown here.")
        trv = D["trv"]
        m_df = D["matches"][D["matches"]["match_id"].isin(trv["match_id"].unique())].copy()
        m_df["label"] = m_df["match_date"].astype(str) + " | " + m_df["home_team"] + " vs " + m_df["away_team"] + " (" + m_df["match_format"] + ")"
        sel_label = st.selectbox("Select Verified Match", m_df["label"].tolist(), key="v50_match_sel")
        sel_mid = int(m_df.loc[m_df["label"] == sel_label, "match_id"].iloc[0])

        sub_m = trv[trv["match_id"] == sel_mid].copy()
        mean_raw = float(trv["raw_expected_wp_swing"].mean())
        sub_m["LI_global"] = sub_m["raw_expected_wp_swing"] / max(mean_raw, 1e-9)
        inn_means = trv.groupby("innings")["raw_expected_wp_swing"].transform("mean")
        sub_m["LI_innings"] = sub_m["raw_expected_wp_swing"] / np.maximum(
            sub_m["innings"].map(trv.groupby("innings")["raw_expected_wp_swing"].mean()), 1e-9
        )
        sub_m["cum_score"] = sub_m.groupby("innings")["actual_total_runs"].cumsum()

        fig_wp = go.Figure()
        for inn in sorted(sub_m["innings"].unique()):
            si = sub_m[sub_m["innings"] == inn]
            fig_wp.add_trace(go.Scatter(x=si["event_index_in_innings"], y=si["wp_inn1_team_oof"], mode="lines", name=f"Innings {inn} WP (Inn1 Team)"))
        fig_wp.update_layout(title="Match Win Probability Progression (Verified Cricsheet Score State)", xaxis_title="Ball Sequence in Innings", yaxis_title="P(Inn1 Team Wins)", template="plotly_white", height=360)
        st.plotly_chart(fig_wp, use_container_width=True)

        hi_m = sub_m[sub_m["LI_global"] >= 1.50]
        st.subheader(f"High-Leverage Deliveries (LI_global >= 1.50): {len(hi_m)} balls")
        st.dataframe(
            hi_m[["innings", "overid", "striker_name", "bowler_name", "cum_score", "actual_total_runs", "wp_inn1_team_oof", "LI_global", "LI_innings", "delta_re_total"]].head(50),
            use_container_width=True,
            hide_index=True,
        )

    with tab3:
        st.caption("Franchise & national-team filters operate strictly as post-hoc presentation views and never retrain or alter the global V5.0 engine.")
        mapping = D["mapping"]
        comp_opts = ["All Competitions", "IPL (T20)", "Men's T20I"]
        sel_comp = st.selectbox("Competition Filter", comp_opts, key="v50_comp_flt")

        team_list = ["All Teams"] + sorted(mapping["team_name"].dropna().unique().tolist())
        sel_team = st.selectbox("Team / Franchise Filter", team_list, index=0, key="v50_team_flt")

        role_f = st.radio("Role", ["Batters", "Bowlers"], horizontal=True, key="v50_team_role")
        base_tbl = D["bat"] if role_f == "Batters" else D["bowl"]
        filt = base_tbl[base_tbl["eligible"] == True].copy()

        if sel_comp == "IPL (T20)":
            filt = filt[filt["ipl_balls"] > 0]
        elif sel_comp == "Men's T20I":
            filt = filt[filt["t20i_balls"] > 0]

        if sel_team != "All Teams":
            team_pids = set(mapping.loc[mapping["team_name"] == sel_team, "player_id"].unique())
            filt = filt[filt["player_id"].isin(team_pids)]

        st.dataframe(
            filt[["rank_hp", "player_name", "archetype", "main_effect_per100", "pressure_interaction_per100", "combined_hp_per100", "ci_low_hp", "ci_high_hp", "n_hp_global", "total_opportunities"]],
            use_container_width=True,
            hide_index=True,
        )
