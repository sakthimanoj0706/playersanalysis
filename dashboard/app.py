"""SupeRR Intelligence V3 - Joint Performance, Pressure Intelligence & Rajasthan Royals Player-Fit Platform.

Rajasthan Royals SupeRR Selector Season 2 Hackathon
Professional Cricket Pressure Reliability Analytics & Squad Scouting Platform.
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── PAGE CONFIGURATION ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="SupeRR Intelligence V4.2 | Resource-Stress Consistency & RR Scouting",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PROFESSIONAL DESIGN SYSTEM (Navy & Royal Pink Palette) ──────────────────
st.markdown("""
<style>
    /* Global Container */
    .main {
        background-color: #FFFFFF;
        color: #0F172A;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header Banner */
    .rr-header {
        background: linear-gradient(135deg, #0B1B3D 0%, #15274D 100%);
        padding: 24px 28px;
        border-radius: 10px;
        color: white;
        margin-bottom: 22px;
        border-left: 6px solid #EA1A85;
        box-shadow: 0 4px 14px rgba(11, 27, 61, 0.08);
    }
    .rr-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin: 0;
    }
    .rr-subtitle {
        font-size: 1.0rem;
        font-weight: 400;
        color: #CBD5E1;
        margin-top: 5px;
    }
    .rr-badge {
        background-color: #EA1A85;
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 999px;
        display: inline-block;
        margin-top: 8px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    /* Executive Metric Cards */
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .metric-lbl {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .metric-val {
        font-size: 1.55rem;
        font-weight: 700;
        color: #0B1B3D;
        margin: 4px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #EA1A85;
        font-weight: 600;
    }
    
    /* Tag Styling */
    .tag-strong {
        background-color: #DCFCE7;
        color: #166534;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .tag-conditional {
        background-color: #FEF9C3;
        color: #854D0E;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .tag-low {
        background-color: #F1F5F9;
        color: #475569;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    
    /* Navigation Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 6px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ── DATA PATHS & CACHED LOADERS ─────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_V4_2 = DATA_DIR / "outputs" / "v4_2"
OUTPUTS_V4_1 = DATA_DIR / "outputs" / "v4_1"
OUTPUTS_V4 = DATA_DIR / "outputs" / "v4"
OUTPUTS_V3 = DATA_DIR / "outputs" / "v3"
REPORTS_V3 = DATA_DIR / "reports" / "v3"
REF_DIR = DATA_DIR / "reference"

@st.cache_data
def load_v42_data():
    """Load V4.2 universal complete-FWL resource-stress outputs plus secondary RR scouting data."""
    files = {}
    try:
        files['shortlist'] = pd.read_csv(OUTPUTS_V4_2 / "V4_2_FINAL_SHORTLIST.csv")
        files['rank_probs'] = pd.read_csv(OUTPUTS_V4_2 / "V4_2_RANK_PROBABILITIES.csv")
        files['decomp'] = pd.read_csv(OUTPUTS_V4_2 / "V4_2_RAW_ADJUSTED_DECOMPOSITION.csv")
        files['precision_sweep'] = pd.read_csv(OUTPUTS_V4_2 / "V4_2_ELIGIBILITY_PRECISION_ANALYSIS.csv")
        files['model_comp'] = pd.read_csv(OUTPUTS_V4_2 / "V4_2_MODEL_COMPARISON.csv")
        files['score_audit'] = pd.read_csv(OUTPUTS_V4_2 / "V4_2_SCORE_ENRICHMENT_AUDIT.csv")
        files['validation'] = pd.read_csv(OUTPUTS_V4_2 / "V4_2_VALIDATION_MATRIX.csv")
        files['reconciliation'] = pd.read_csv(OUTPUTS_V4 / "DATA_RECONCILIATION.csv")
        with open(OUTPUTS_V4_2 / "V4_2_SOURCE_OF_TRUTH.json", "r", encoding="utf-8") as f:
            files['sot'] = json.load(f)

        # Secondary RR 2026 Data (archived scouting module kept separate from Universal ranking)
        files['rr_matches'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_matches.csv")
        files['rr_bat'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_batting_stats.csv")
        files['rr_bowl'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_bowling_stats.csv")
        files['rr_phase'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_phase_analysis.csv")
        files['rr_contrib'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_player_contribution.csv")
        files['rr_strengths'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_team_strengths.csv")
        files['rr_weaknesses'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_team_weaknesses.csv")
        files['rr_provenance'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_data_provenance.csv")

        # Secondary RR Strategy
        files['rr_required_roles'] = pd.read_csv(OUTPUTS_V3 / "RR_REQUIRED_ROLES.csv")
        files['rr_player_fit'] = pd.read_csv(OUTPUTS_V3 / "RR_PLAYER_FIT.csv")
        files['rr_retention'] = pd.read_csv(OUTPUTS_V3 / "RR_RETENTION_SCENARIOS.csv")
        files['rr_budget'] = pd.read_csv(OUTPUTS_V3 / "RR_AUCTION_BUDGET_SCENARIOS.csv")
        files['crosswalk'] = pd.read_csv(OUTPUTS_V3 / "RR_PLAYER_ID_CROSSWALK.csv")
        files['apps'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_player_appearances.csv")

        # Reference
        files['user_brief'] = pd.read_csv(REF_DIR / "rr_2026_user_brief.csv")
        files['auction_assumptions'] = pd.read_csv(REF_DIR / "rr_2027_auction_assumptions.csv")
        files['cohort_manifest'] = pd.read_csv(REPORTS_V3 / "MATCH_COHORT_MANIFEST.csv")

        import json, hashlib
        manifest_path = OUTPUTS_V3 / "RANKING_SOURCE_OF_TRUTH.json"
        if manifest_path.exists():
            with open(manifest_path, "r") as mf:
                files['manifest'] = json.load(mf)
            # Hash-lock drift check against canonical CSVs
            for fname, expected_sha in files['manifest'].get('artifact_sha256', {}).items():
                fpath = OUTPUTS_V3 / fname
                if expected_sha and fpath.exists():
                    actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
                    if actual_sha != expected_sha:
                        st.error(f"STALE_ARTIFACT_ERROR: {fname} SHA-256 does not match RANKING_SOURCE_OF_TRUTH.json!")
    except Exception as e:
        st.error(f"Error loading V4.2 data files: {e}")
    return files

data = load_v42_data()
sot_meta = data.get('sot', {})
release_status = sot_meta.get('release_status', 'V4.2 PROVISIONAL — RESOURCE STRESS')
model_version = sot_meta.get('model_version', 'V4.2')
pressure_source_type = 'PRE_DELIVERY_RESOURCE_STRESS (BATTING_WICKET_DEPLETION_ANOMALY / BOWLING_EXPECTED_SCORING_THREAT)'

# ── TOP EXECUTIVE BANNER ────────────────────────────────────────────────────
st.markdown(f"""
<div class="rr-header">
    <div class="rr-title">SupeRR Intelligence V4.2</div>
    <div class="rr-subtitle">Within-Player Consistency Under Resource Stress (Complete Penalized FWL + REML Empirical Bayes) & Secondary RR Scouting</div>
    <div class="rr-badge">{release_status} • Model {model_version}</div>
</div>
""", unsafe_allow_html=True)

# ── 5-SECTION SIDEBAR NAVIGATION (STRICT ORDER) ─────────────────────────────
with st.sidebar:
    st.markdown("### 👑 Analytics Navigation")
    section = st.radio(
        "Select Analytical Section:",
        [
            "Section 1: Universal Player Intelligence",
            "Section 2: Rajasthan Royals 2026 Analysis",
            "Section 3: RR Team Requirements",
            "Section 4: RR Player Fit & Auction Strategy",
            "Section 5: Data & Model Transparency",
        ],
        index=0
    )
    st.markdown("---")
    st.markdown("### 📋 Platform Metadata")
    st.caption(f"**Framework:** {model_version}")
    st.caption(f"**Pressure Source:** {pressure_source_type}")
    st.caption("**Regular Deliveries:** 193,988 (26 SO separated)")
    st.caption("**Status:** " + release_status)
    st.markdown("---")
    st.caption("Round 1 Universal Leaderboard separated cleanly from RR Scouting")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — UNIVERSAL PLAYER INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════
if section == "Section 1: Universal Player Intelligence":
    st.markdown("## 🌐 Section 1: Universal Player Intelligence (V4.2)")
    st.info(
        f"**Classification Notice (`{release_status}`):** Exact chase score/target reconstruction fails on **342 / 390** non-DLS run-margin matches "
        "(`0 / 837` matches free of extras, `0` external scorecards matched by `match_id`, `CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`). "
        "Therefore V4.2 uses strictly pre-delivery resource-stress proxies (`BATTING_WICKET_DEPLETION_ANOMALY` / `BOWLING_EXPECTED_SCORING_THREAT`), which "
        "**cannot distinguish 12 runs required off 6 balls from 70 runs required off 6 balls** when balls and wickets remaining are equal. "
        "Rankings use **Option A Complete Penalized FWL + REML Empirical Bayes (`span=0.75`)** with B=2,000 REML match-cluster bootstrap intervals and explicit match consistency & secondary outcome trade-offs."
    )

    u_tab1, u_tab2, u_tab3, u_tab4, u_tab5, u_tab6 = st.tabs([
        "🏏 Top 10 Batters (Provisional)",
        "🎯 Top 10 Bowlers (Provisional)",
        "📊 Raw vs Adjusted 8-Contrast Bridge",
        "🏷️ Operational Precision Floor",
        "📐 Resource-Stress Trace & Score Audit",
        "🔬 Option A vs B vs V4.1 & Claim C Tuning"
    ])

    short_df = data.get('shortlist', pd.DataFrame())
    rp_df = data.get('rank_probs', pd.DataFrame())
    decomp_df = data.get('decomp', pd.DataFrame())

    # 1. Top 10 Batters
    with u_tab1:
        st.markdown("### 🏏 Universal Top 10 Batters Under Resource Stress (`PROVISIONAL`)")
        st.caption(
            "Ordered by Claim C REML `eb_delta` (units: `BATTER_RUNS_PER_100_LEGAL_BALLS`, complete FWL `span=0.75`). "
            "Includes both total `eb_delta` and excess above population stress slope (`eb_vs_pop_mean_delta`), 5 uncertainty measures, match-level consistency, and dismissal-risk trade-offs."
        )

        bat_s = short_df[short_df['role'] == 'batter'].copy() if not short_df.empty else pd.DataFrame()
        if not bat_s.empty:
            tb_disp = bat_s[[
                'shortlist_rank_display', 'eb_rank', 'player_name', 'total_matches', 'n_hi', 'n_lo', 'cs_matches',
                'raw_hi_perf', 'raw_lo_perf', 'delta_unshrunk', 'eb_delta', 'eb_vs_pop_mean_delta',
                'eb_cond_ci_low', 'eb_cond_ci_high', 'eb_boot_ci_low', 'eb_boot_ci_high',
                'prob_positive_effect', 'boot_rank_ci_low', 'boot_rank_ci_high', 'prob_top_10', 'mcse_prob_top_10',
                'within_match_spread_matches', 'between_match_delta_sd', 'share_matches_pos_delta_vs_normal',
                'dismissal_risk_delta_per_100b', 'secondary_tradeoff_flag'
            ]].copy()
            tb_disp.columns = [
                'Rank', 'Avg Rank', 'Player Name', 'Matches', 'High Balls', 'Low Balls', 'CS Matches',
                'Raw Hi SR', 'Raw Lo SR', 'FWL Δ', 'EB Δ', 'EB vs Pop μ0',
                'Cond CI Low', 'Cond CI High', 'Boot CI Low', 'Boot CI High',
                'P(Δ>0)', 'Rank CI Low', 'Rank CI High', 'P(Top10)', 'MCSE',
                'Spread Matches', 'Between-Match SD', 'Share + vs Own Normal',
                'Dismissal Δ/100b', 'Secondary Warning'
            ]
            st.dataframe(tb_disp, use_container_width=True, hide_index=True)
            b_het = sot_meta.get('heterogeneity', {}).get('batter_reml', {})
            st.caption(
                f"Source: V4_2_FINAL_SHORTLIST.csv • REML mu0={b_het.get('mu0', 0.0):.2f}, "
                f"tau={b_het.get('tau', 0.0):.2f} runs/100b, I2={100*b_het.get('I2', 0.0):.1f}%."
            )
        else:
            st.warning("V4.2 Top 10 Batters data not loaded.")

    # 2. Top 10 Bowlers
    with u_tab2:
        st.markdown("### 🎯 Universal Top 10 Bowlers Under Scoring Threat (`PROVISIONAL`)")
        st.caption(
            "Metric: `BATTER_RUNS_CONCEDED_SUPPRESSION_PER_100_LEGAL_BALLS_PROXY` (+ = fewer batter-credited runs conceded than expectation; "
            "not full economy with wides/byes/leg-byes). Ranked purely by Claim C REML `eb_delta` with secondary dot-ball % and wicket % effects shown side-by-side."
        )

        bowl_s = short_df[short_df['role'] == 'bowler'].copy() if not short_df.empty else pd.DataFrame()
        if not bowl_s.empty:
            tw_disp = bowl_s[[
                'shortlist_rank_display', 'eb_rank', 'player_name', 'total_matches', 'n_hi', 'n_lo', 'cs_matches',
                'raw_hi_perf', 'raw_lo_perf', 'delta_unshrunk', 'eb_delta', 'eb_vs_pop_mean_delta',
                'eb_cond_ci_low', 'eb_cond_ci_high', 'eb_boot_ci_low', 'eb_boot_ci_high',
                'prob_positive_effect', 'boot_rank_ci_low', 'boot_rank_ci_high', 'prob_top_10', 'mcse_prob_top_10',
                'within_match_spread_matches', 'between_match_delta_sd', 'share_matches_pos_delta_vs_normal',
                'sec_dot_ctrl_eb_delta', 'sec_wicket_eb_delta', 'secondary_tradeoff_flag'
            ]].copy()
            tw_disp.columns = [
                'Rank', 'Avg Rank', 'Player Name', 'Matches', 'High Balls', 'Low Balls', 'CS Matches',
                'Raw Hi Saved', 'Raw Lo Saved', 'FWL Δ', 'EB Δ', 'EB vs Pop μ0',
                'Cond CI Low', 'Cond CI High', 'Boot CI Low', 'Boot CI High',
                'P(Δ>0)', 'Rank CI Low', 'Rank CI High', 'P(Top10)', 'MCSE',
                'Spread Matches', 'Between-Match SD', 'Share + vs Own Normal',
                'Dot% EB Δ', 'Wkt% EB Δ', 'Secondary Warning'
            ]
            st.dataframe(tw_disp, use_container_width=True, hide_index=True)
            w_het = sot_meta.get('heterogeneity', {}).get('bowler_reml', {})
            st.caption(
                f"Source: V4_2_FINAL_SHORTLIST.csv • REML mu0={w_het.get('mu0', 0.0):.2f}, "
                f"tau={w_het.get('tau', 0.0):.2f} runs/100b, I2={100*w_het.get('I2', 0.0):.1f}%."
            )
        else:
            st.warning("V4.2 Top 10 Bowlers data not loaded.")

    # 3. Raw vs Adjusted Bridge
    with u_tab3:
        st.markdown("### 📊 Like-for-Like 8-Contrast Decomposition & Estimand Separation")
        st.markdown(
            "Separates raw high/low/all-non-high zones, discrete context-adjusted contrasts (`hi vs lo` & `hi vs all-non-high`), "
            "and the continuous P87.5-minus-P12.5 FWL slope (`bridge_identity_residual < 1e-12`)."
        )
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if not rp_df.empty:
                el_bat = rp_df[rp_df['role'] == 'batter'].copy()
                fig_b = px.scatter(
                    el_bat,
                    x='raw_hi_minus_lo_delta',
                    y='delta_unshrunk',
                    size='n_hi',
                    color='eb_delta',
                    hover_name='player_name',
                    hover_data=['total_matches', 'n_hi', 'prob_top_10', 'eb_cond_ci_low'],
                    title="Batters (Eligible): Raw Hi-Lo Δ vs Complete FWL Continuous Δ",
                    labels={'raw_hi_minus_lo_delta': 'Raw Hi - Low Δ (Runs/100b)', 'delta_unshrunk': 'Complete FWL Continuous Δ'},
                    height=440
                )
                fig_b.add_vline(x=0.0, line_dash='dash', line_color='#94A3B8')
                fig_b.add_hline(y=0.0, line_dash='dash', line_color='#94A3B8')
                st.plotly_chart(fig_b, use_container_width=True)

        with col_s2:
            if not rp_df.empty:
                el_bowl = rp_df[rp_df['role'] == 'bowler'].copy()
                fig_w = px.scatter(
                    el_bowl,
                    x='raw_hi_minus_lo_delta',
                    y='delta_unshrunk',
                    size='n_hi',
                    color='eb_delta',
                    hover_name='player_name',
                    hover_data=['total_matches', 'n_hi', 'prob_top_10', 'eb_cond_ci_low'],
                    title="Bowlers (Eligible): Raw Hi-Lo Δ vs Complete FWL Continuous Δ",
                    labels={'raw_hi_minus_lo_delta': 'Raw Hi - Low Δ (Runs Saved/100b)', 'delta_unshrunk': 'Complete FWL Continuous Δ'},
                    height=440
                )
                fig_w.add_vline(x=0.0, line_dash='dash', line_color='#94A3B8')
                fig_w.add_hline(y=0.0, line_dash='dash', line_color='#94A3B8')
                st.plotly_chart(fig_w, use_container_width=True)

        if not decomp_df.empty and not short_df.empty:
            st.markdown("#### Exact 8-Contrast & Nuisance/Estimand Shift Table (Top 10 Batters & Bowlers)")
            top_ids = short_df['player_id'].tolist()
            sub_dec = decomp_df[decomp_df['player_id'].isin(top_ids)][[
                'role', 'player_name', 'raw_high_performance', 'raw_low_performance',
                'raw_all_non_high_performance', 'raw_hi_minus_lo_delta', 'raw_hi_minus_all_non_high_delta',
                'discrete_context_adjusted_hi_minus_lo_delta', 'discrete_context_adjusted_hi_minus_all_non_high_delta',
                'continuous_p875_minus_p125_adjusted_delta', 'eb_delta'
            ]]
            st.dataframe(sub_dec, use_container_width=True, hide_index=True)

    # 4. Operational Precision Floor
    with u_tab4:
        st.markdown("### 🏷️ Operational Precision Floor Audit (`n_hi>=50, n_lo>=30, cs_matches>=8, se<=25`)")
        st.caption("Threshold documented strictly as an operational precision floor, NOT claimed empirically optimal.")
        if 'precision_sweep' in data and not data['precision_sweep'].empty:
            st.dataframe(data['precision_sweep'], use_container_width=True, hide_index=True)

    # 5. Resource-Stress Scope & Score Enrichment
    with u_tab5:
        st.markdown("### 📐 V4.2 Proxy Trace & Score Enrichment Audit")
        st.markdown("""
        - **`BATTING_WICKET_DEPLETION_ANOMALY` (aliases `BATTING_RESOURCE_STRESS`, `bat_pressure`):** Excess wicket depletion above empirical `(innings, overid)` stage expectation (`(R0, b)` normalize expected remaining runs during optimization; `gamma` drives wicket depletion). **Cannot distinguish 12 runs needed from 70 runs needed at identical balls/wickets remaining.**
        - **`BOWLING_EXPECTED_SCORING_THREAT` (aliases `BOWLING_SCORING_THREAT`, `bowl_pressure`):** Pre-delivery expected batter scoring rate Ridge quantile.
        - **Score Audit (`V4_2_SCORE_ENRICHMENT_AUDIT.csv`):** Sums validated `legal_balls` cleanly (`185,951 <= 193,988` delivery rows, excluding wides/no-balls); `342 / 390` non-DLS run-margin checks still fail (`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`).
        """)
        if 'score_audit' in data and not data['score_audit'].empty:
            st.markdown("#### Match-Level Score Audit Sample (Non-DLS Margin Failures)")
            st.dataframe(data['score_audit'][data['score_audit']['match_validation_status'] == 'NON_DLS_RUN_MARGIN_FAIL'].head(25), use_container_width=True, hide_index=True)

    # 6. Model Comparison & Claim C OOT Tuning
    with u_tab6:
        st.markdown("### 🔬 Option A Complete FWL vs Option B Hierarchical EM vs V4.1 & Claim C Ridge Tuning")
        if 'shortlist' in data and not short_df.empty:
            fig_ci = go.Figure()
            for _, r in short_df[short_df['role'] == 'batter'].iterrows():
                fig_ci.add_trace(go.Scatter(
                    x=[r['eb_boot_ci_low'], r['eb_delta'], r['eb_boot_ci_high']],
                    y=[r['player_name'], r['player_name'], r['player_name']],
                    mode='lines+markers',
                    marker=dict(size=[6, 11, 6], color=['#EA1A85', '#0B1B3D', '#EA1A85']),
                    line=dict(color='#0B1B3D', width=2),
                    showlegend=False
                ))
            fig_ci.add_vline(x=0.0, line_dash='dash', line_color='#64748B')
            fig_ci.update_layout(
                title="Top 10 Batters: REML EB Δ & B=2,000 Bootstrap 95% CI",
                xaxis_title="REML Empirical Bayes Pressure-vs-Normal Slope Δ (Runs/100 balls)",
                height=420
            )
            st.plotly_chart(fig_ci, use_container_width=True)
        if 'model_comp' in data and not data['model_comp'].empty:
            st.markdown("#### Estimator Comparison & Direct Claim C OOT Ridge Tuning (`V4_2_MODEL_COMPARISON.csv`)")
            st.dataframe(data['model_comp'], use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — RAJASTHAN ROYALS 2026 ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
elif section == "Section 2: Rajasthan Royals 2026 Analysis":
    st.markdown("## 🏰 Section 2: Rajasthan Royals IPL 2026 Season Analysis")
    st.markdown("""
    **Empirical Season Review:** Grounded in all 16 matches (14 league matches, Eliminator victory, Qualifier 2) and 3,788 ball-by-ball delivery records in IPL 2026.
    """)

    rr_tab1, rr_tab2, rr_tab3, rr_tab4, rr_tab5, rr_tab6, rr_tab7 = st.tabs([
        "🏆 RR Season Overview & Results",
        "🏏 RR Batting Performance",
        "🎯 RR Bowling Performance",
        "⚡ Phase-Wise Team Performance",
        "📋 Audited Player Appearances",
        "👥 Player Contribution Breakdown",
        "⚖️ Empirical Strengths & Weaknesses"
    ])

    with rr_tab1:
        st.markdown("### 🏆 Tournament Campaign Overview")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("""<div class="metric-card"><div class="metric-lbl">Overall Finish</div><div class="metric-val">3rd Place</div><div class="metric-sub">Playoff Qualifier</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="metric-card"><div class="metric-lbl">League Stage Record</div><div class="metric-val">8 Wins / 14 Matches</div><div class="metric-sub">4th in Standings</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class="metric-card"><div class="metric-lbl">Eliminator</div><div class="metric-val">Won by 47 runs</div><div class="metric-sub">vs Sunrisers Hyderabad</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown("""<div class="metric-card"><div class="metric-lbl">Qualifier 2</div><div class="metric-val">Lost by 7 wkts</div><div class="metric-sub">vs Gujarat Titans</div></div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 📅 Match-by-Match Results (16 Games)")
        if 'rr_matches' in data and not data['rr_matches'].empty:
            st.dataframe(data['rr_matches'], use_container_width=True, hide_index=True)

    with rr_tab2:
        st.markdown("### 🏏 RR Batting Aggregates (IPL 2026)")
        if 'rr_bat' in data and not data['rr_bat'].empty:
            b_disp = data['rr_bat'][[
                'player_name', 'matches_appeared', 'innings_batted', 'runs', 'balls_faced',
                'batting_average', 'strike_rate', 'sixes', 'pp_sr', 'middle_sr', 'death_sr'
            ]].copy()
            b_disp.columns = ['Player', 'Matches', 'Innings', 'Runs', 'Balls', 'Average', 'SR', 'Sixes', 'PP SR', 'Middle SR', 'Death SR']
            st.dataframe(
                b_disp.style.format({
                    'Average': lambda x: f"{x:.2f}" if pd.notna(x) else "—",
                    'SR': '{:.2f}',
                    'PP SR': '{:.2f}',
                    'Middle SR': '{:.2f}',
                    'Death SR': '{:.2f}',
                }),
                use_container_width=True,
                hide_index=True
            )

            st.info("""
            **Reconciliation Confirmation:**
            - **Vaibhav Sooryavanshi:** 776 runs, average 48.50, strike rate 237.31, 72 sixes (Orange Cap & MVP).
            - **Dhruv Jurel:** 515 runs, average 36.79 (14 dismissals, 2 not outs; partner run-outs excluded), strike rate 154.65.
            - **Yashasvi Jaiswal:** 427 runs, average 30.50, strike rate 152.50.
            - **Donovan Ferreira:** 317 runs, average 35.22, strike rate 179.10.
            - **Riyan Parag:** 309 runs, average 23.77, strike rate 157.65.
            - **Ravindra Jadeja:** 266 runs, average 66.50, strike rate 135.03.
            """)

    with rr_tab3:
        st.markdown("### 🎯 RR Bowling Aggregates (IPL 2026)")
        if 'rr_bowl' in data and not data['rr_bowl'].empty:
            bw_disp = data['rr_bowl'][[
                'player_name', 'matches_appeared', 'overs', 'bowler_creditable_wickets',
                'dot_balls', 'dot_ball_pct', 'bowling_strike_rate', 'pp_wickets', 'middle_wickets', 'death_wickets',
                'economy_rate_status'
            ]].copy()
            bw_disp.columns = ['Player', 'Matches', 'Overs', 'Wickets (Bowler)', 'Dots', 'Dot %', 'Strike Rate', 'PP Wkts', 'Mid Wkts', 'Death Wkts', 'Economy Status']
            st.dataframe(
                bw_disp.style.format({
                    'Dot %': '{:.1f}%',
                    'Strike Rate': lambda x: f"{x:.1f}" if pd.notna(x) else "—",
                }),
                use_container_width=True,
                hide_index=True
            )

            st.info("""
            **Reconciliation Confirmation (Bowler-Creditable Wickets):**
            - **Jofra Archer:** 25 wickets (3rd on Purple Cap leaderboard).
            - **Brijesh Sharma:** 14 wickets in 13 matches (uncapped breakthrough).
            - **Nandre Burger:** 14 wickets in 13 matches.
            - **Ravi Bishnoi:** 11 wickets in 9 matches.
            - **Ravindra Jadeja:** 10 wickets in 12 matches.
            - **Sandeep Sharma:** 5 wickets in 6 matches.
            - **Tushar Deshpande:** 4 wickets in 7 matches.
            - **Adam Milne:** 1 match appeared, 3.2 overs, 0 wickets.
            - *Note on Bowling Economy:* Quarantined from derived totals due to categorical extras representation; user-provided economy figures preserved under reference files.
            """)

    with rr_tab4:
        st.markdown("### ⚡ RR Phase-Wise Performance (IPL 2026)")
        st.markdown("""
        **Data Contract Compliance:** Runs represent audited `team_batter_runs` off the bat. Full team totals including extras are quarantined.
        """)
        if 'rr_phase' in data and not data['rr_phase'].empty:
            st.dataframe(data['rr_phase'], use_container_width=True, hide_index=True)

    with rr_tab5:
        st.markdown("### 📋 Audited Player Appearances (16 RR Matches)")
        st.markdown("""
        **Appearance Semantics:** Distinguishes matches listed in match squad sheet, starting XI, impact sub entries, matches with batting participation, and matches with bowling participation.
        """)
        if 'apps' in data and not data['apps'].empty:
            st.dataframe(data['apps'], use_container_width=True, hide_index=True)

    with rr_tab6:
        st.markdown("### 👥 Player Contribution Share & Salary Efficiency")
        if 'rr_contrib' in data and not data['rr_contrib'].empty:
            st.dataframe(data['rr_contrib'], use_container_width=True, hide_index=True)

    with rr_tab7:
        st.markdown("### ⚖️ Empirical Strengths & Weaknesses")
        col_st, col_wk = st.columns(2)
        with col_st:
            st.markdown("#### ✅ Validated Team Strengths")
            if 'rr_strengths' in data and not data['rr_strengths'].empty:
                st.dataframe(data['rr_strengths'], use_container_width=True, hide_index=True)
        with col_wk:
            st.markdown("#### ⚠️ Validated Team Weaknesses")
            if 'rr_weaknesses' in data and not data['rr_weaknesses'].empty:
                st.dataframe(data['rr_weaknesses'], use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — RR TEAM REQUIREMENTS
# ════════════════════════════════════════════════════════════════════════════
elif section == "Section 3: RR Team Requirements":
    st.markdown("## 🎯 Section 3: Rajasthan Royals Team Requirements & Squad Gaps")
    st.markdown("""
    **Governing Rule:** Derived *exclusively* from the Phase 12 empirical season analysis.
    Identifies the exact tactical deficiencies that RR must solve in the IPL 2027 recruitment window.
    """)

    if 'rr_required_roles' in data and not data['rr_required_roles'].empty:
        st.dataframe(data['rr_required_roles'], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 🔍 In-Depth Gap Evaluations")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            #### 1. Indian Frontline Fast Bowler (CRITICAL — Priority 1)
            - **Why Needed:** Tushar Deshpande and Sandeep Sharma managed only 9 wickets across 13 appearances, leaking high boundary rates.
            - **Current Cover:** Deshpande (₹6.5 Cr) and Sandeep (₹4.0 Cr).
            - **Target Allocation:** ₹10.0 – ₹13.0 Cr.
            - **Profile Required:** 140+ kph Indian pacer capable of taking the new ball and executing death overs.
            """)
            
            st.markdown("""
            #### 2. Overseas Death-Over Specialist (CRITICAL — Priority 2)
            - **Why Needed:** Nandre Burger is a new-ball enforcer; RR had no secondary death bowler to pair with Jofra Archer in overs 16–20.
            - **Current Cover:** Burger (₹3.5 Cr) and Adam Milne (₹2.4 Cr, 1 match).
            - **Target Allocation:** ₹8.0 – ₹11.0 Cr.
            - **Profile Required:** Elite slinger or yorker specialist with low CVaR tail risk.
            """)

        with c2:
            st.markdown("""
            #### 3. Economical Middle-Over Spinner (IMPORTANT — Priority 3)
            - **Why Needed:** Ravi Bishnoi was benched in 7 matches due to team balance; attack lacked an economical finger spinner to choke scoring rate.
            - **Current Cover:** Bishnoi (₹7.2 Cr) and Jadeja (₹14.0 Cr).
            - **Target Allocation:** ₹3.0 – ₹5.0 Cr.
            - **Profile Required:** Left-arm orthodox finger spinner or mystery spinner.
            """)

            st.markdown("""
            #### 4. Domestic Lower-Order Finisher (IMPORTANT — Priority 4)
            - **Why Needed:** Shimron Hetmyer scored only 78 runs in 8 matches (₹11.0 Cr). Signing a domestic finisher frees the overseas slot for an elite pacer.
            - **Current Cover:** Shubham Dubey (₹80 L) and Donovan Ferreira (overseas).
            - **Target Allocation:** ₹2.0 – ₹3.0 Cr.
            - **Profile Required:** Indian power hitter for overs 16–20 striking at 170+ SR.
            """)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — RR PLAYER FIT AND AUCTION STRATEGY
# ════════════════════════════════════════════════════════════════════════════
elif section == "Section 4: RR Player Fit & Auction Strategy":
    st.markdown("## 💰 Section 4: RR Player Fit & Auction Strategy (IPL 2027)")
    st.markdown("""
    **Governing Principle:** Candidate players are evaluated *strictly against the 4 verified squad requirements* established in Section 3.
    Universal rankings remain 100% separate from RR-specific fit suitability.
    """)

    af_tab1, af_tab2, af_tab3, af_tab4 = st.tabs([
        "🎯 Player Fit Evaluation Matrix",
        "⚖️ Candidate-by-Candidate Comparisons",
        "💼 Retention, Purse & Release Scenarios",
        "📋 Final Auction Game Plan & Strongest XI"
    ])

    with af_tab1:
        st.markdown("### 🎯 Watchlist Candidates Evaluated Against RR Gaps")
        if 'rr_player_fit' in data and not data['rr_player_fit'].empty:
            pf_disp = data['rr_player_fit'][[
                'player_name', 'target_gap', 'primary_role', 'is_overseas',
                'estimated_price_range', 'recommendation_category', 'fit_reasoning'
            ]].copy()
            st.dataframe(pf_disp, use_container_width=True, hide_index=True)

    with af_tab2:
        st.markdown("### ⚖️ Head-to-Head Candidate Comparisons by Role Gap")
        gap_choice = st.selectbox(
            "Select Target Role Gap to Inspect Candidates:",
            [
                "Indian Frontline Fast Bowler",
                "Overseas Death-Over Specialist",
                "Economical Middle-Over Spinner",
                "Domestic Lower-Order Finisher"
            ]
        )
        if 'rr_player_fit' in data and not data['rr_player_fit'].empty:
            sub_fit = data['rr_player_fit'][data['rr_player_fit']['target_gap'] == gap_choice]
            for _, cand in sub_fit.iterrows():
                with st.expander(f"{cand['player_name']} — {cand['recommendation_category']} ({cand['estimated_price_range']})"):
                    st.markdown(f"**Primary Role:** {cand['primary_role']} | **Overseas Slot:** {'Yes' if cand['is_overseas'] else 'No'}")
                    st.markdown(f"**Key Phase:** {cand['key_phase']}")
                    st.markdown(f"**Historical Evidence:** {cand['historical_evidence']}")
                    st.markdown(f"**Strengths:** {cand['strengths']}")
                    st.markdown(f"**Weaknesses & Injury Risk:** {cand['weaknesses']} (Risk: {cand['injury_risk']})")
                    st.markdown(f"**Expected Role in XI:** {cand['expected_role_xi']}")
                    st.markdown(f"**Tactical Fit Rationale:** {cand['fit_reasoning']}")

    with af_tab3:
        st.markdown("### 💼 Retention & Purse Arithmetic Scenarios")
        st.markdown("""
        **Purse Formula (Unverified Scenario Assumptions — Source: `data/reference/rr_2027_auction_assumptions.csv`, Checked Date: `2026-11-15`):**
        $$\\text{Available Purse} = \\text{Carried Purse (₹2.65 Cr)} + \\sum \\text{Freed Salaries (₹24.95 Cr)} + \\text{Cap Increase Scenario}$$
        *Provenance Note: All salary, purse, and cap figures represent user-brief scenario assumptions (`USER_BRIEF_SCENARIO_ASSUMPTION_UNVERIFIED`) rather than official BCCI/IPL audited financial disclosures.*
        """)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📋 Candidate Release Actions")
            if 'rr_retention' in data and not data['rr_retention'].empty:
                st.dataframe(data['rr_retention'], use_container_width=True, hide_index=True)
        with c2:
            st.markdown("#### 📊 Auction Budget Scenarios")
            if 'rr_budget' in data and not data['rr_budget'].empty:
                st.dataframe(data['rr_budget'], use_container_width=True, hide_index=True)

        st.warning("""
        **Contract Conflict Flag:** Dasun Shanaka was a temporary replacement for Sam Curran (groin injury). 
        RR management must clarify Curran's medical status before 17 November 2026. Curran and Shanaka cannot both be retained permanently under IPL regulations.
        """)

    with af_tab4:
        st.markdown("### 📋 Final Auction Strategy & Projected Strongest XI (2027)")
        
        col_strat, col_xi = st.columns(2)
        with col_strat:
            st.markdown("""
            #### 🎯 4-Step Auction Execution Strategy
            1. **Step 1 (Indian Pacer):** Aggressively pursue **Prasidh Krishna** or **Avesh Khan** up to ₹10.50 Cr. Securing an Indian frontline pacer to partner Archer is the primary prerequisite.
            2. **Step 2 (Overseas Death Bowler):** Bid for **Matheesha Pathirana** up to ₹9.50 Cr. If bidding exceeds ₹11.00 Cr, immediately pivot to **Nuwan Thushara** at ₹4.50–₹5.50 Cr.
            3. **Step 3 (Middle Spinner):** Secure **R Sai Kishore** at ₹3.50–₹4.50 Cr for elite left-arm finger spin control.
            4. **Step 4 (Domestic Finisher):** Sign **Ashutosh Sharma** at ₹2.50–₹3.50 Cr to cement the No. 6/7 finishing role, allowing the overseas slot to remain with Pathirana.
            """)

        with col_xi:
            st.markdown("""
            #### 👑 Projected Strongest Rajasthan Royals Playing XI (2027)
            1. **Yashasvi Jaiswal** (LHB, Top-Order)
            2. **Vaibhav Sooryavanshi** (LHB, Top-Order)
            3. **Dhruv Jurel** (RHB, Wicketkeeper)
            4. **Riyan Parag** (RHB, Captain)
            5. **Donovan Ferreira** ✈️ (RHB, Finisher)
            6. **Ashutosh Sharma** (RHB, Finisher)
            7. **Ravindra Jadeja** (LHB, Left-Arm Orthodox)
            8. **R Sai Kishore** / **Ravi Bishnoi** (Spin)
            9. **Jofra Archer** ✈️ (Right-Arm Fast)
            10. **Prasidh Krishna** / **Avesh Khan** (Right-Arm Fast)
            11. **Matheesha Pathirana** ✈️ / **Nuwan Thushara** ✈️ (Right-Arm Sling)
            *Tactical Impact Sub:* **Brijesh Sharma** (Spin) / **Nandre Burger** ✈️ (Pace)
            """)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 — DATA AND MODEL TRANSPARENCY
# ════════════════════════════════════════════════════════════════════════════
elif section == "Section 5: Data & Model Transparency":
    st.markdown("## 🛡️ Section 5: Data & Model Transparency (V4.2)")
    st.markdown(f"""
    **Governance Disclosure:** Status = **`{release_status}`** (`{model_version}`). Universal consistency modeling uses
    role-separated pre-delivery resource stress proxies (`BATTING_WICKET_DEPLETION_ANOMALY`, `BOWLING_EXPECTED_SCORING_THREAT`) cleanly segregated from archived V3 scouting outputs.
    """)

    dt_tab1, dt_tab2, dt_tab3, dt_tab4 = st.tabs([
        "📋 Data Reconciliation (194,014 -> 193,988)",
        "🏷️ Player ID Crosswalk & Identity Resolution",
        "✅ V4.2 Validation Matrix (Claims A/B/C)",
        "🚫 Quarantined Metrics & Known Limitations"
    ])

    with dt_tab1:
        st.markdown("### 📋 Exact V4 Data Reconciliation (Preserved)")
        if 'reconciliation' in data and not data['reconciliation'].empty:
            st.dataframe(data['reconciliation'], use_container_width=True, hide_index=True)
        if 'cohort_manifest' in data and not data['cohort_manifest'].empty:
            st.markdown("#### Match Cohort Manifest Preview")
            st.dataframe(data['cohort_manifest'].head(50), use_container_width=True, hide_index=True)

    with dt_tab2:
        st.markdown("### 🏷️ Verified Player Entity Crosswalk & ID-Keyed Joins")
        st.markdown("""
        **Resolution Standard:** Canonical `striker_id` / `bowler_id` keys are enforced globally to prevent name-collision
        errors across duplicate names (`Abdul Samad`, `Haider Ali`, `Mohammad Ali`).
        """)
        if 'crosswalk' in data and not data['crosswalk'].empty:
            st.dataframe(data['crosswalk'], use_container_width=True, hide_index=True)

    with dt_tab3:
        st.markdown("### ✅ V4.2 Validation Matrix (`V4_2_VALIDATION_MATRIX.csv`)")
        st.caption("Fixed quantile spans (0.60, 0.70, 0.75), full R(u,w) sensitivity, score-bootstrap vs full-refit proof, within-stratum placebo, Claims A/B/C OOT, and additive identities.")
        if 'validation' in data and not data['validation'].empty:
            st.dataframe(data['validation'], use_container_width=True, hide_index=True)

    with dt_tab4:
        st.markdown("### 🚫 Quarantined Metrics & Limitations")
        st.markdown("""
        1. **`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`:** `extras1_runs` encodes categorical `extras_type` codes (1–7), `extras_2_runs` (`35` rows) is undocumented, and `runs` excludes multi-run wides/byes/leg-byes/penalties; non-DLS run-margin checks fail on **342 / 390** matches (`0 / 837` matches free of extras, `0` external scorecards matched by `match_id`). Targets, RRR, and score-based WP Leverage $C_t$ remain quarantined.
        2. **`BATTER_RUNS_CONCEDED_PROXY` Disclosure:** Bowler run suppression measures batter-credited runs saved per 100 legal balls (`-100 * batter_runs/ball`), not true all-extras bowling economy. `legal_balls` (185,951) strictly excludes wides and Overstep no-balls (`delivery_rows` = 193,988).
        3. **Cannot Distinguish Chase Equation:** Under identical `(balls_rem, wkts_rem)`, `BATTING_WICKET_DEPLETION_ANOMALY` / `BOWLING_EXPECTED_SCORING_THREAT` cannot separate 12 runs required off 6 balls from 70 runs required off 6 balls.
        4. **Super Overs Separated:** Innings 3 & 4 (26 deliveries) are excluded from regular-innings leaderboard estimation.
        5. **Claim C Temporal Unpredictability:** Across all tested Ridge settings, Claim C OOT replication remains statistically inconclusive/unpredictable under resource-stress proxies (`CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS`), which is disclosed honestly alongside secondary outcome warnings.
        """)

# ── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"SupeRR Intelligence V4.2 ({release_status}) • Model {model_version} • Rajasthan Royals SupeRR Selector Season 2")
