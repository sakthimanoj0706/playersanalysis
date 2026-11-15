"""SupeRR Intelligence V4 - Unified Calibrated-Ridge Pressure Intelligence & Rajasthan Royals Player-Fit Platform.

Rajasthan Royals SupeRR Selector Season 2 Hackathon
Professional Cricket Pressure Reliability Analytics & Squad Scouting Platform.
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── PAGE CONFIGURATION ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="SupeRR Intelligence V4 | Rajasthan Royals Analytics",
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
OUTPUTS_V3 = DATA_DIR / "outputs" / "v3"
REPORTS_V3 = DATA_DIR / "reports" / "v3"
REF_DIR = DATA_DIR / "reference"

@st.cache_data
def load_v3_data():
    """Load all V4 canonical outputs and reference datasets."""
    files = {}
    try:
        files['top_bat'] = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
        files['top_bowl'] = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
        files['all_bat'] = pd.read_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv")
        files['all_bowl'] = pd.read_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv")
        files['roles'] = pd.read_csv(OUTPUTS_V3 / "player_roles.csv")
        files['eligibility'] = pd.read_csv(OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv")
        
        # RR 2026 Data
        files['rr_matches'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_matches.csv")
        files['rr_bat'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_batting_stats.csv")
        files['rr_bowl'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_bowling_stats.csv")
        files['rr_phase'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_phase_analysis.csv")
        files['rr_contrib'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_player_contribution.csv")
        files['rr_strengths'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_team_strengths.csv")
        files['rr_weaknesses'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_team_weaknesses.csv")
        files['rr_provenance'] = pd.read_csv(OUTPUTS_V3 / "rr_2026_data_provenance.csv")
        
        # RR Strategy
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
        st.error(f"Error loading V4 data files: {e}")
    return files

data = load_v3_data()

# ── TOP EXECUTIVE BANNER ────────────────────────────────────────────────────
status_badge = data.get('manifest', {}).get('governance', {}).get('ranking_approval_status', 'V4 UNIFIED CALIBRATED RIDGE — SUBMISSION VERIFIED')
st.markdown(f"""
<div class="rr-header">
    <div class="rr-title">SupeRR Intelligence V4</div>
    <div class="rr-subtitle">Joint Performance, Pressure Intelligence & Rajasthan Royals Player-Fit Platform</div>
    <div class="rr-badge">Rajasthan Royals • SupeRR Selector Season 2 • {status_badge}</div>
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
    roles_cnt = f"{len(data['roles']):,}" if 'roles' in data and not data['roles'].empty else "1,117"
    st.caption("**Framework:** V4 Unified Calibrated Ridge")
    st.caption(f"**Universal Roster:** {roles_cnt} Players Classified")
    st.caption("**RR 2026 Data:** 16 Matches (3,788 Balls)")
    st.caption("**Auction Horizon:** IPL 2027 Mini-Auction")
    st.markdown("---")
    st.caption("Developed for Rajasthan Royals SupeRR Selector")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — UNIVERSAL PLAYER INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════
if section == "Section 1: Universal Player Intelligence":
    st.markdown("## 🌐 Section 1: Universal Player Intelligence")
    st.markdown("""
    **Analytical Framework:** Universal performance modeling across all 837 matches (IPL & T20I 2022–2026).
    Evaluates individual player performance under pre-delivery pressure benchmarked against unconstrained normal baselines.
    Features **strict role gating**: batters are limited to `BAT_SPECIALIST` and `BAT_PRIMARY_AR`; bowlers are limited to `BOWL_SPECIALIST` and `BOWL_PRIMARY_AR`.
    """)

    u_tab1, u_tab2, u_tab3, u_tab4, u_tab5, u_tab6 = st.tabs([
        "🏏 Top 10 Batters Under Pressure",
        "🎯 Top 10 Bowlers Under Pressure",
        "📊 Player Performance Breakdown",
        "🏷️ Role Classification & Eligibility",
        "📐 Pressure Methodology & Models",
        "🔬 Reliability & Uncertainty (Bootstrap CIs)"
    ])

    # 1. Top 10 Batters
    with u_tab1:
        st.markdown("### 🏏 Universal Top 10 Batters Under Pressure (V4 Calibrated Ridge)")
        bat_thresh = data.get('manifest', {}).get('configurations', {}).get('default_batting_thresholds', {})
        st.caption(
            f"Eligibility: ≥{bat_thresh.get('crisis_balls', 60)} Tier-weighted crisis balls, "
            f"≥{bat_thresh.get('total_balls', 200)} total balls, "
            f"≥{bat_thresh.get('crisis_matches', 6)} crisis matches, "
            f"≥{bat_thresh.get('norm_balls', 60)} Tier-weighted normal balls, ≥60% Tier-1 exposure. Role: BAT_SPECIALIST or BAT_PRIMARY_AR."
        )
        
        if 'top_bat' in data and not data['top_bat'].empty:
            tb_disp = data['top_bat'][[
                'rank', 'player_name', 'v3_role', 'crisis_balls', 'crisis_matches',
                'crisis_sr', 'norm_sr', 'crisis_delta_rv', 'did_bat_maintenance',
                'consistency_score', 'ci_lower', 'ci_upper', 'batting_pri'
            ]].copy()
            tb_disp.columns = [
                'Rank', 'Player Name', 'Role', 'Crisis Balls', 'Matches',
                'Crisis SR', 'Norm SR', 'Crisis RV/100', 'DiD Maint.',
                'Consistency', '95% RV CI Lo', '95% RV CI Hi', 'V4 PRI Score'
            ]
            st.dataframe(
                tb_disp.style.format({
                    'Crisis SR': '{:.1f}',
                    'Norm SR': '{:.1f}',
                    'Crisis RV/100': '{:+.2f}',
                    'DiD Maint.': '{:+.2f}',
                    'Consistency': '{:.3f}',
                    '95% RV CI Lo': '{:+.1f}',
                    '95% RV CI Hi': '{:+.1f}',
                    'V4 PRI Score': '{:.2f}',
                    'Crisis Balls': '{:.0f}',
                    'Matches': '{:.0f}',
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Top 10 Batters data not loaded.")

        disclosure = data.get('manifest', {}).get('governance', {}).get(
            'mandatory_disclosure',
            "Rankings use V4 Calibrated Ridge state-conditional run values with Tier-1 weighting."
        )
        st.markdown(f"> **Governance Disclosure:** *{disclosure}*")

        if 'top_bat' in data and not data['top_bat'].empty:
            st.markdown("**Key Insights (Live from Canonical `TOP_10_BATTERS.csv`):**")
            for _, r in data['top_bat'].head(4).iterrows():
                st.markdown(
                    f"- **#{int(r['rank'])} {r['player_name']} (`ID={int(r['canonical_player_id'])}`, Score {r['batting_pri']:.2f}):** "
                    f"Crisis SR **{r['crisis_sr']:.2f}** vs **{r['norm_sr']:.2f}** normal, **{r['crisis_delta_rv']:+.2f}** shrunk RV/100 "
                    f"(95% RV CI `[{r['ci_lower']:+.1f}, {r['ci_upper']:+.1f}]`, DiD **{r['did_bat_maintenance']:+.2f}**) "
                    f"across {int(r['crisis_balls'])} crisis balls / {int(r['crisis_matches'])} matches."
                )
        if 'top_bat' in data and not data['top_bat'].empty and 'component_breakdown_explanation' in data['top_bat'].columns:
            with st.expander("🔍 Individual Selection Rationales — Top 10 Batters"):
                for _, r in data['top_bat'].head(10).iterrows():
                    st.markdown(f"- **#{int(r['rank'])} {r['player_name']} (`ID={int(r['canonical_player_id'])}`, `{r['v3_role']}`):** `{r['component_breakdown_explanation']}` (`{r['ranking_sensitivity_status']}`)")

    # 2. Top 10 Bowlers
    with u_tab2:
        st.markdown("### 🎯 Universal Top 10 Bowlers Under Pressure (V4 Calibrated Ridge)")
        st.caption("Eligibility: ≥120 Tier-weighted defensive crisis balls, ≥250 total legal balls, ≥6 crisis matches, ≥100 Tier-weighted normal balls, ≥60% Tier-1 exposure. Invariant V4 weights (30% Maint / 35% Abs / 25% Cons / 10% Sample).")
        
        if 'top_bowl' in data and not data['top_bowl'].empty:
            tw_disp = data['top_bowl'][[
                'rank', 'player_name', 'v3_role', 'crisis_balls', 'norm_balls', 'crisis_matches',
                'crisis_econ', 'crisis_dot_pct', 'crisis_delta_rv', 'did_bowl_maintenance',
                'consistency_score', 'ci_lower', 'ci_upper', 'provisional_fixed_weight_score'
            ]].copy()
            tw_disp.columns = [
                'Rank', 'Player Name', 'Role', 'Crisis Balls', 'Norm Balls', 'Matches',
                'Crisis Econ', 'Crisis Dot%', 'Runs Saved/Ov', 'DiD Maint.',
                'Consistency', '95% RV CI Lo', '95% RV CI Hi', 'V4 PRI Score'
            ]
            st.dataframe(
                tw_disp.style.format({
                    'Crisis Econ': '{:.2f}',
                    'Crisis Dot%': '{:.1f}%',
                    'Runs Saved/Ov': '{:+.2f}',
                    'DiD Maint.': '{:+.2f}',
                    'Consistency': '{:.3f}',
                    '95% RV CI Lo': '{:+.2f}',
                    '95% RV CI Hi': '{:+.2f}',
                    'V4 PRI Score': '{:.2f}',
                    'Crisis Balls': '{:.0f}',
                    'Norm Balls': '{:.0f}',
                    'Matches': '{:.0f}',
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Top 10 Bowlers data not loaded.")

        if 'top_bowl' in data and not data['top_bowl'].empty:
            st.markdown("**Key Insights (Live from Canonical `TOP_10_BOWLERS.csv`):**")
            for _, r in data['top_bowl'].head(4).iterrows():
                st.markdown(
                    f"- **#{int(r['rank'])} {r['player_name']} (`ID={int(r['canonical_player_id'])}`, Score {r['provisional_fixed_weight_score']:.2f}):** "
                    f"**{int(r['crisis_balls'])}** crisis balls, **{int(r['norm_balls'])}** normal balls (`{r['norm_baseline_status']}`), "
                    f"**{r['crisis_econ']:.2f}** econ, **{r['crisis_delta_rv']:+.2f}** runs saved/ov, "
                    f"shrunk WR **{r['shrunk_crisis_wr']:.2f}%**, 95% RV CI `[{r['ci_lower']:+.2f}, {r['ci_upper']:+.2f}]` runs/ov."
                )
        if 'top_bowl' in data and not data['top_bowl'].empty and 'component_breakdown_explanation' in data['top_bowl'].columns:
            with st.expander("🔍 Individual Selection Rationales — Top 10 Bowlers"):
                for _, r in data['top_bowl'].head(10).iterrows():
                    st.markdown(f"- **#{int(r['rank'])} {r['player_name']} (`ID={int(r['canonical_player_id'])}`, `{r['v3_role']}`):** `{r['component_breakdown_explanation']}` (`{r['ranking_sensitivity_status']}`)")

    # 3. Performance Breakdown
    with u_tab3:
        st.markdown("### 📊 Player Performance Deep-Dive")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if 'all_bat' in data and not data['all_bat'].empty:
                el_bat = data['all_bat'][data['all_bat']['final_eligibility'] == 'ELIGIBLE'].copy()
                fig_b = px.scatter(
                    el_bat,
                    x='norm_sr',
                    y='crisis_sr',
                    size='crisis_balls',
                    color='v3_role',
                    hover_name='player_name',
                    hover_data=['crisis_matches', 'provisional_fixed_weight_score'],
                    title="Batters: Crisis Strike Rate vs Normal Baseline (Eligible Cohort)",
                    labels={'norm_sr': 'Normal Baseline Strike Rate', 'crisis_sr': 'Crisis Strike Rate'},
                    height=450
                )
                fig_b.add_shape(type="line", line=dict(dash='dash', color='#94A3B8'), x0=80, y0=80, x1=210, y1=210)
                st.plotly_chart(fig_b, use_container_width=True)

        with col_s2:
            if 'all_bowl' in data and not data['all_bowl'].empty:
                el_bowl = data['all_bowl'][data['all_bowl']['final_eligibility'] == 'ELIGIBLE'].copy()
                fig_w = px.scatter(
                    el_bowl,
                    x='norm_dot_pct',
                    y='crisis_dot_pct',
                    size='crisis_balls',
                    color='v3_role',
                    hover_name='player_name',
                    hover_data=['crisis_matches', 'provisional_fixed_weight_score'],
                    title="Bowlers: Crisis Dot% vs Normal Baseline (Eligible Cohort)",
                    labels={'norm_dot_pct': 'Normal Baseline Dot %', 'crisis_dot_pct': 'Crisis Dot %'},
                    height=450
                )
                fig_w.add_shape(type="line", line=dict(dash='dash', color='#94A3B8'), x0=15, y0=15, x1=55, y1=55)
                st.plotly_chart(fig_w, use_container_width=True)

    # 4. Role Classification & Eligibility
    with u_tab4:
        st.markdown("### 🏷️ Five-State Role Classification & Eligibility Audit")
        if 'roles' in data and not data['roles'].empty:
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                st.metric("Total Players Classified", f"{len(data['roles']):,}")
            with rc2:
                st.metric("Eligible for Bat Leaderboard", f"{data['roles']['eligible_for_bat_leaderboard'].sum():,}")
            with rc3:
                st.metric("Eligible for Bowl Leaderboard", f"{data['roles']['eligible_for_bowl_leaderboard'].sum():,}")

            role_dist = data['roles']['v3_role'].value_counts().reset_index()
            role_dist.columns = ['V3 Role', 'Player Count']
            fig_r = px.bar(role_dist, x='V3 Role', y='Player Count', color='V3 Role', title="Roster Distribution Across 5 Mutually Exclusive Roles")
            st.plotly_chart(fig_r, use_container_width=True)

            st.dataframe(data['roles'].head(25), use_container_width=True, hide_index=True)

    # 5. Pressure Methodology
    with u_tab5:
        st.markdown("### 📐 Dual Pre-Delivery Pressure & Ridge Run-Value Architecture (`V4_CALIBRATED_RIDGE`)")
        st.markdown("""
        **Zero Target Leakage Guarantee:** All situational features are observable strictly *before* the delivery is bowled, with DLS-revised overs and targets integrated (`25` DLS matches).

        - **Pure Ex-Ante State Leverage (No Last-12 Dot/Boundary Survivorship Bias):**
          - **Batting:** Pre-delivery wickets fallen, stage-relative wicket shock, 12-legal-ball wicket clusters, and monotonic 2nd-innings chase / 1st-innings scoring-lag demand.
          - **Bowling:** Opponent wickets in hand, live-game chase closeness (peak ~9.5 RPO; dead-rubber taper >15.5 or <5.0 RPO) / 1st-innings tempo, and live-death squeeze.
        - **Within-`(innings, innings_phase)` Quantile Tiers:** High (`> q70`), Moderate (`q50–q70`), Normal (`<= q50`) — guaranteeing ~50% Normal exposure across Powerplay, Middle, and Death specialists.
        - **Competition-Tier Weighting & Ridge Opponent Adjustment:** `T1_IPL` & `T1_FM_T20I = 1.0`, `T2_MIXED = 0.5`, `T3_ASSOC = 0.2` (`>= 60%` Tier-1 share required). Weighted Ridge (`lsqr`) decomposes state residuals into `match_par + striker_offense + bowler_defense`.
        - **Unified Value & Invariant Weights (`30% Maint / 35% Abs / 25% Cons / 10% Sample`):** Batting Run Value/100 balls and Bowling Runs Saved/Over (including `wide`/`Overstep` penalty runs), paired with Value-Gated Downside Consistency and strict Normal-Baseline gates (`>= 60` bat / `>= 100` bowl Tier-weighted balls).
        """)

    # 6. Reliability & Uncertainty
    with u_tab6:
        st.markdown("### 🔬 Statistical Reliability & Bootstrap Uncertainty")
        st.markdown("""
        **Match-Clustered Resampling:** 2,000 bootstrap iterations per player resampling entire match clusters (`random_state=42`) directly on **V4 Crisis Run Value / 100 (Batters)** and **Crisis Runs Saved / Over (Bowlers)**.
        """)
        col_ci1, col_ci2 = st.columns(2)
        with col_ci1:
            if 'top_bat' in data and not data['top_bat'].empty:
                st.markdown("#### Top 10 Batters: 95% CI (Crisis Run Value / 100)")
                fig_ci = go.Figure()
                for _, r in data['top_bat'].head(10).iterrows():
                    pt = r['crisis_r_bat'] if 'crisis_r_bat' in r and pd.notna(r['crisis_r_bat']) else (r['ci_lower'] + r['ci_upper']) / 2.0
                    fig_ci.add_trace(go.Scatter(
                        x=[r['ci_lower'], pt, r['ci_upper']],
                        y=[r['player_name'], r['player_name'], r['player_name']],
                        mode='lines+markers',
                        marker=dict(size=[6, 12, 6], color=['#EA1A85', '#0B1B3D', '#EA1A85']),
                        line=dict(color='#0B1B3D', width=2),
                        name=r['player_name'],
                        showlegend=False
                    ))
                fig_ci.update_layout(title="Top 10 Batters: Point Estimate & 95% Match-Clustered Bootstrap CI", xaxis_title="Crisis Run Value Above Expectation per 100 Balls", height=420)
                st.plotly_chart(fig_ci, use_container_width=True)
        with col_ci2:
            if 'top_bowl' in data and not data['top_bowl'].empty:
                st.markdown("#### Top 10 Bowlers: 95% CI (Crisis Runs Saved / Over)")
                fig_ci_b = go.Figure()
                for _, r in data['top_bowl'].head(10).iterrows():
                    pt_b = r['crisis_r_rv'] if 'crisis_r_rv' in r and pd.notna(r['crisis_r_rv']) else (r['ci_lower'] + r['ci_upper']) / 2.0
                    fig_ci_b.add_trace(go.Scatter(
                        x=[r['ci_lower'], pt_b, r['ci_upper']],
                        y=[r['player_name'], r['player_name'], r['player_name']],
                        mode='lines+markers',
                        marker=dict(size=[6, 12, 6], color=['#EA1A85', '#0B1B3D', '#EA1A85']),
                        line=dict(color='#0B1B3D', width=2),
                        name=r['player_name'],
                        showlegend=False
                    ))
                fig_ci_b.update_layout(title="Top 10 Bowlers: Point Estimate & 95% Match-Clustered Bootstrap CI", xaxis_title="Crisis Runs Saved Above Expectation per Over", height=420)
                st.plotly_chart(fig_ci_b, use_container_width=True)


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
                'player_name', 'target_gap', 'primary_role', 'universal_ranking', 'is_overseas',
                'estimated_price_range', 'evidence_verification_status', 'recommendation_category', 'fit_reasoning'
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
                    st.markdown(f"**Primary Role:** {cand['primary_role']} | **System A V4 Rank:** {cand['universal_ranking']} (`{cand['evidence_verification_status']}`) | **Overseas Slot:** {'Yes' if cand['is_overseas'] else 'No'}")
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
    st.markdown("## 🛡️ Section 5: Data & Model Transparency")
    st.markdown("""
    **Governance Disclosure:** Full data provenance, model validation status, and strict quarantine documentation.
    """)

    dt_tab1, dt_tab2, dt_tab3, dt_tab4 = st.tabs([
        "📋 Match Cohort & Provenance",
        "🏷️ Player ID Crosswalk & Resolution",
        "✅ Model Validation Status",
        "🚫 Quarantined Metrics & Known Limitations"
    ])

    with dt_tab1:
        st.markdown("### 📋 Match Cohort Manifest (853 Matches Audited)")
        if 'cohort_manifest' in data and not data['cohort_manifest'].empty:
            cm = data['cohort_manifest']
            st.metric("Total Source Matches", f"{len(cm)}")
            st.caption("Included (with BBB & non-abandoned): 790 matches | Excluded (no BBB): 16 matches | Quarantined Abandoned: 24 | Flagged DLS Target: 23 (25 2nd-inn revised-overs)")
            st.dataframe(cm.head(50), use_container_width=True, hide_index=True)

    with dt_tab2:
        st.markdown("### 🏷️ Verified Player Entity Crosswalk (40 Resolved Entities)")
        st.markdown("""
        **Resolution Standard:** Canonical dataset player IDs are used for all database and model joins. 
        Resolves historical reference ID discrepancies (e.g. Sooryavanshi 50284 vs 281699; Jurel 7260 vs 7825; Archer 3298 vs 3262) and eliminates candidate misattributions.
        """)
        if 'crosswalk' in data and not data['crosswalk'].empty:
            st.dataframe(data['crosswalk'], use_container_width=True, hide_index=True)

    with dt_tab3:
        st.markdown("### ✅ V4 Model Validation & Governance Status Matrix")
        model_matrix = [
            {'Model': 'V4 Calibrated Ridge Pressure & Run-Value Engine', 'Type': 'Ex-Ante State Quantiles + Tiered Ridge', 'Validation Split': 'Match & Tier-1 Gated', 'Leakage': 'Zero', 'Status': 'V4_CALIBRATED_RIDGE'},
            {'Model': 'Five-State Role Classifier', 'Type': 'Empirical Classification', 'Validation Split': 'Multi-Season Workload', 'Leakage': 'Zero', 'Status': 'VERIFIED_ROLE_GATING'},
            {'Model': 'Hierarchical Joint Model', 'Type': 'Ridge Regression', 'Validation Split': 'Chronological Match', 'Leakage': 'Zero', 'Status': 'EXPERIMENTAL_NOT_USED_FOR_RANKING'},
            {'Model': 'Discrete-Time Hazard Model (AUC 0.572, Log-Loss 0.692, Exp Wkts 26,843 vs Act 2,931)', 'Type': 'Un-recalibrated Balanced Logistic', 'Validation Split': 'Chronological Match', 'Leakage': 'Zero', 'Status': 'EXPERIMENTAL_NOT_USED_FOR_RANKING'},
            {'Model': 'Bowling Tail-Risk / CVaR', 'Type': 'Extreme Value Theory', 'Validation Split': 'Over-Level Distribution', 'Leakage': 'Zero', 'Status': 'DESCRIPTIVE_SUPPLEMENT'},
            {'Model': 'LightGBM Challenger', 'Type': 'Gradient Boosted Trees', 'Validation Split': 'Chronological Match', 'Leakage': 'Zero', 'Status': 'EXPERIMENTAL_NOT_USED_FOR_RANKING'},
            {'Model': 'Match-Clustered Bootstrap (2,000 iter)', 'Type': 'Non-Parametric Resampling', 'Validation Split': 'Cluster Match Bootstrap', 'Leakage': 'Zero', 'Status': 'ESTIMATED_MATCH_CLUSTER_BOOTSTRAP'},
        ]
        st.dataframe(pd.DataFrame(model_matrix), use_container_width=True, hide_index=True)

    with dt_tab4:
        st.markdown("### 🚫 Quarantined Metrics & Limitations")
        st.markdown("""
        1. **`extras1_runs` is Categorical (Codes 1–7):** Never summed as runs. Bowler economy and run values include `1 * is_wide_or_overstep` as clean penalty runs (clean lower bound excluding byes/leg-byes and multi-run wides).
        2. **DLS-Aware Clean-Channel RRR (`clean_rrr_deficit`):** Uses `first_inn_revised_overs`, `second_inn_revised_overs`, and `revised_target` (25 2nd-innings revised-overs / 23 DLS target matches) without touching categorical `extras1_runs`.
        3. **Weighted Ridge Regression (`lsqr`, `damp=12.0`):** Controls for `(comp_tier, innings, phase, wkt_bucket)`, match pitch par, and opponent strength across Tier-1 (`1.0`), Mixed (`0.5`), and Associate (`0.2`) fixtures.
        4. **Super Overs Quarantined:** Innings 3 & 4 (26 balls) segregated from standard 20-over tactical ratings.
        5. **Non-Bowler Dismissals Excluded:** 581 non-bowler dismissals (Run Outs, Retired Outs, Obstructing the field) excluded from bowler wicket tallies.
        """)

# ── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("SupeRR Intelligence V4 • Rajasthan Royals SupeRR Selector Season 2 • Built with Statistical Rigor & Scientific Defensibility")
