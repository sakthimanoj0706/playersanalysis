"""SupeRR Intelligence - Professional Cricket Pressure Analytics Platform.

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
    page_title="SupeRR Intelligence | Rajasthan Royals Analytics",
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
OUTPUTS_DIR = DATA_DIR / "outputs"
REPORTS_DIR = DATA_DIR / "reports"

@st.cache_data
def load_all_analytics_data():
    """Load all computed rankings, classifications, and validation datasets."""
    top_bat = pd.read_csv(OUTPUTS_DIR / "FINAL_TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(OUTPUTS_DIR / "FINAL_TOP_10_BOWLERS.csv")
    all_bat = pd.read_csv(OUTPUTS_DIR / "ALL_BATTER_RANKINGS.csv")
    all_bowl = pd.read_csv(OUTPUTS_DIR / "ALL_BOWLER_RANKINGS.csv")
    low_bat = pd.read_csv(OUTPUTS_DIR / "LOWER_ORDER_PRESSURE_IMPACT.csv")
    em_bowl = pd.read_csv(OUTPUTS_DIR / "EMERGING_AND_PART_TIME_BOWLERS.csv")
    roles = pd.read_csv(OUTPUTS_DIR / "PLAYER_ROLE_CLASSIFICATION.csv")
    aliases = pd.read_csv(OUTPUTS_DIR / "PLAYER_NAME_ALIASES.csv")
    press_val = pd.read_csv(OUTPUTS_DIR / "PRESSURE_MODEL_VALIDATION.csv")
    sens_df = pd.read_csv(OUTPUTS_DIR / "PRI_SENSITIVITY_ANALYSIS.csv")
    elig_df = pd.read_csv(OUTPUTS_DIR / "PLAYER_ELIGIBILITY_REPORT.csv")
    cons_df = pd.read_csv(OUTPUTS_DIR / "match_consistency_analysis.csv")
    return {
        'top_bat': top_bat,
        'top_bowl': top_bowl,
        'all_bat': all_bat,
        'all_bowl': all_bowl,
        'low_bat': low_bat,
        'em_bowl': em_bowl,
        'roles': roles,
        'aliases': aliases,
        'press_val': press_val,
        'sens_df': sens_df,
        'elig_df': elig_df,
        'cons_df': cons_df,
    }

data = load_all_analytics_data()

# ── TOP EXECUTIVE BANNER ────────────────────────────────────────────────────
st.markdown("""
<div class="rr-header">
    <div class="rr-title">SupeRR Intelligence</div>
    <div class="rr-subtitle">Pressure Reliability Analytics & Evidence-Based Player Scouting Platform</div>
    <div class="rr-badge">Rajasthan Royals • SupeRR Selector Season 2 • Official Dossier</div>
</div>
""", unsafe_allow_html=True)

# ── 4-SECTION SIDEBAR NAVIGATION ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 👑 Analytics Navigation")
    section = st.radio(
        "Select Analytical Section:",
        [
            "1. Pressure Intelligence Overview",
            "2. Batter Intelligence (Primary & Lower-Order)",
            "3. Bowler Intelligence (Primary & Emerging)",
            "4. Methodology, Science & Data Quality",
        ],
        index=0
    )
    st.markdown("---")
    st.markdown("### 📋 Dataset Scope")
    st.caption("**Scope:** IPL & Men's T20I (2022–2026)")
    st.caption("**Deliveries:** 193,988 regular deliveries")
    st.caption("**Matches:** 853 (837 with ball-by-ball)")
    st.caption("**Super Overs:** Quarantined (26 deliveries)")
    st.caption("**Extras Codebook:** Categorical enum (Codes 1–7)")
    st.markdown("---")
    st.caption("Rajasthan Royals Hackathon Analytics Suite")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1: PRESSURE INTELLIGENCE OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
if section == "1. Pressure Intelligence Overview":
    st.markdown("## 📊 Pressure Intelligence Overview")
    st.markdown("""
    **Executive Mandate:** Build a data-driven system that measures how batters and bowlers perform in high-pressure match situations compared with their usual performance levels, identifying the players who deliver most consistently when it matters.
    """)

    # Key Headline Statistics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Total Deliveries Audited</div>
            <div class="metric-val">193,988</div>
            <div class="metric-sub">837 T20 Matches Audited</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Batting Crisis Balls</div>
            <div class="metric-val">15,464</div>
            <div class="metric-sub">7.97% High/Extreme Pressure</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Bowling Defensive Balls</div>
            <div class="metric-val">101,935</div>
            <div class="metric-sub">52.55% High/Extreme Pressure</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Audited Player Roster</div>
            <div class="metric-val">1,118</div>
            <div class="metric-sub">Classified by Empirical Role</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Top 5 Batters & Top 5 Bowlers Executive Comparison
    st.markdown("### 🏆 Top 5 Pressure Reliability Leaders")
    col_bat, col_bowl = st.columns(2)

    with col_bat:
        st.markdown("#### 🏏 Top 5 Batters (Positions 1–7)")
        top5_bat = data['top_bat'].head(5)[['rank', 'canonical_display_name', 'primary_role', 'crisis_sr', 'sr_maintenance', 'batting_pri']]
        top5_bat.columns = ['Rank', 'Player Name', 'Role', 'Crisis SR', 'Maint.', 'Batting PRI']
        st.dataframe(top5_bat.style.format({'Crisis SR': '{:.1f}', 'Maint.': '{:.2f}x', 'Batting PRI': '{:.2f}'}), use_container_width=True, hide_index=True)

    with col_bowl:
        st.markdown("#### 🎯 Top 5 Bowlers (Frontline, 120+ Balls)")
        top5_bowl = data['top_bowl'].head(5)[['rank', 'canonical_display_name', 'primary_role', 'crisis_wicket_rate', 'crisis_dot_pct', 'bowling_pri']]
        top5_bowl.columns = ['Rank', 'Player Name', 'Role', 'Crisis WR%', 'Crisis Dot%', 'Bowling PRI']
        st.dataframe(top5_bowl.style.format({'Crisis WR%': '{:.1f}%', 'Crisis Dot%': '{:.1f}%', 'Bowling PRI': '{:.2f}'}), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Plotly Overview Chart: PRI Distribution of Top 10 Batters & Bowlers
    st.markdown("### 📈 PRI Benchmark Comparison (Top 10 Batters vs Top 10 Bowlers)")
    
    chart_bat = data['top_bat'].head(10)[['canonical_display_name', 'batting_pri']].rename(
        columns={'canonical_display_name': 'Player', 'batting_pri': 'PRI'}
    ).assign(Discipline='Batting (Crisis)')
    
    chart_bowl = data['top_bowl'].head(10)[['canonical_display_name', 'bowling_pri']].rename(
        columns={'canonical_display_name': 'Player', 'bowling_pri': 'PRI'}
    ).assign(Discipline='Bowling (Defensive)')
    
    combined_chart = pd.concat([chart_bat, chart_bowl], ignore_index=True)

    fig = px.bar(
        combined_chart,
        x='Player',
        y='PRI',
        color='Discipline',
        barmode='group',
        color_discrete_map={'Batting (Crisis)': '#EA1A85', 'Bowling (Defensive)': '#0B1B3D'},
        title="Top 10 Pressure Reliability Index (PRI) by Discipline",
        height=400,
    )
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="sans-serif", size=12, color="#0F172A"),
        xaxis=dict(tickangle=-30),
        yaxis=dict(range=[50, 100], title="PRI (0 to 100)"),
        margin=dict(l=40, r=40, t=50, b=80),
    )
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2: BATTER INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════
elif section == "2. Batter Intelligence (Primary & Lower-Order)":
    st.markdown("## 🏏 Batter Pressure Intelligence")
    st.markdown("""
    **Analytical Framework:** Evaluates batting crisis performance (wickets fallen, cluster collapse, new batter vulnerability, death overs) against each batter's own normal baseline.
    Separates regular top/middle-order batters (Positions 1–7) from lower-order impact contributors (Positions 8–11).
    """)

    b_tab1, b_tab2, b_tab3, b_tab4 = st.tabs([
        "🏆 Primary Top 10 Batters (Positions 1–7)",
        "⚡ Lower-Order Pressure Impact (Specialist Bowlers/Tail)",
        "📋 All-Role Batting Leaderboard (Full Transparency)",
        "🔍 Batter Deep-Dive Profile & Scatter Analysis"
    ])

    with b_tab1:
        st.markdown("### 🏆 Official Primary Top 10 Batters Under Crisis Pressure")
        st.caption("Criteria: Minimum 40 crisis balls, 120 total balls, 5 crisis matches, and regular batting order (Positions 1–7).")
        
        disp_bat = data['top_bat'][[
            'rank', 'canonical_display_name', 'primary_role', 'modal_batting_position',
            'crisis_balls', 'crisis_matches', 'crisis_sr', 'norm_sr', 'sr_maintenance',
            'consistency_score', 'batting_pri'
        ]].copy()
        disp_bat.columns = ['Rank', 'Player Name', 'Role', 'Modal Pos', 'Crisis Balls', 'Matches', 'Crisis SR', 'Normal SR', 'Maint. Ratio', 'Consistency', 'Batting PRI']
        
        st.dataframe(
            disp_bat.style.format({
                'Crisis SR': '{:.1f}',
                'Normal SR': '{:.1f}',
                'Maint. Ratio': '{:.2f}x',
                'Consistency': '{:.2f}',
                'Batting PRI': '{:.2f}',
                'Crisis Balls': '{:.0f}',
                'Matches': '{:.0f}',
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("""
        **Key Insights:**
        - **Tilak Varma (#1, PRI 91.30):** Outstanding crisis strike rate of 196.7 vs normal 144.5 (1.36x maintenance ratio) across 18 crisis matches.
        - **Matthew Wade (#2, PRI 74.76):** Reliable finisher with 172.0 crisis strike rate across 15 high-pressure innings.
        - **MS Dhoni (#5, PRI 66.20):** Deepest crisis sample in the cohort (133 crisis balls across 35 matches), striking at 154.9 under collapse conditions.
        """)

    with b_tab2:
        st.markdown("### ⚡ Lower-Order Pressure Impact Leaderboard")
        st.caption("Specialist bowlers and lower-order batters (modal position 8–11) who deliver clutch boundary hitting under collapse.")
        
        low_disp = data['low_bat'].head(15)[[
            'lower_order_rank', 'canonical_display_name', 'primary_role', 'modal_batting_position',
            'crisis_balls', 'crisis_sr', 'norm_sr', 'sr_maintenance', 'batting_pri', 'eligibility_status'
        ]].copy()
        low_disp.columns = ['Rank', 'Player Name', 'Primary Role', 'Modal Pos', 'Crisis Balls', 'Crisis SR', 'Norm SR', 'Maint.', 'Batting PRI', 'Status']
        
        st.dataframe(
            low_disp.style.format({
                'Crisis SR': '{:.1f}',
                'Norm SR': '{:.1f}',
                'Maint.': '{:.2f}x',
                'Batting PRI': '{:.2f}',
                'Crisis Balls': '{:.0f}',
            }),
            use_container_width=True,
            hide_index=True
        )

        st.info("""
        **Methodology Note:**
        Specialist bowlers like **Gudakesh Motie** (modal pos 9, 47 crisis balls, 170.2 SR) and **Akeal Hosein** (modal pos 10, 114 crisis balls, 136.0 SR) are tracked here. 
        Because tailenders only bat when earlier wickets have fallen, their exposure is 100% crisis-skewed; separating them preserves statistical fairness for frontline top-seven batters while honoring their clutch hitting.
        """)

    with b_tab3:
        st.markdown("### 📋 All-Role Batting Leaderboard (Unrestricted)")
        st.caption("All 824 evaluated batters across all roles. Use filters to inspect full data transparency.")

        all_b_filter = data['all_bat'].copy()
        role_opts = ['All'] + sorted(all_b_filter['primary_role'].dropna().unique().tolist())
        selected_role = st.selectbox("Filter by Role:", role_opts, key="bat_role_sel")
        
        if selected_role != 'All':
            all_b_filter = all_b_filter[all_b_filter['primary_role'] == selected_role]

        st.dataframe(
            all_b_filter[[
                'overall_rank', 'canonical_display_name', 'primary_role', 'modal_batting_position',
                'total_balls', 'crisis_balls', 'crisis_sr', 'norm_sr', 'sr_maintenance', 'batting_pri', 'eligibility_status'
            ]].rename(columns={
                'overall_rank': 'Rank',
                'canonical_display_name': 'Player',
                'primary_role': 'Role',
                'modal_batting_position': 'Pos',
                'total_balls': 'Total Balls',
                'crisis_balls': 'Crisis Balls',
                'crisis_sr': 'Crisis SR',
                'norm_sr': 'Norm SR',
                'sr_maintenance': 'Maint.',
                'batting_pri': 'Batting PRI',
                'eligibility_status': 'Status'
            }).head(50),
            use_container_width=True,
            hide_index=True
        )

    with b_tab4:
        st.markdown("### 🔍 Batter Deep-Dive: Crisis vs Normal Maintenance")
        
        el_bat = data['all_bat'][data['all_bat']['eligibility_status'] == 'ELIGIBLE'].copy()
        
        fig_scatter = px.scatter(
            el_bat,
            x='norm_sr',
            y='crisis_sr',
            size='crisis_balls',
            color='primary_role',
            hover_name='canonical_display_name',
            hover_data=['modal_batting_position', 'batting_pri', 'sr_maintenance'],
            title="Crisis Strike Rate vs Normal Strike Rate (Eligible Batters, Bubble Size = Crisis Balls)",
            labels={'norm_sr': 'Normal Baseline Strike Rate', 'crisis_sr': 'Crisis Pressure Strike Rate'},
            height=500,
        )
        # Add 1.0 parity diagonal
        fig_scatter.add_shape(
            type="line", line=dict(dash='dash', color='#94A3B8', width=1.5),
            x0=80, y0=80, x1=210, y1=210
        )
        fig_scatter.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(family="sans-serif", size=12, color="#0F172A"),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Dotted line indicates parity (1.0x maintenance). Players above the line elevate their scoring rate under pressure.")


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3: BOWLER INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════
elif section == "3. Bowler Intelligence (Primary & Emerging)":
    st.markdown("## 🎯 Bowler Defensive Pressure Intelligence")
    st.markdown("""
    **Analytical Framework:** Evaluates defensive bowling pressure (opponent having wickets in hand, death overs, powerplay field restrictions, opponent boundary momentum) on dot retention and Empirical Bayes shrunk wicket probability.
    Separates frontline regular bowlers (min 120 crisis balls) from part-time and emerging bowlers.
    """)

    bw_tab1, bw_tab2, bw_tab3, bw_tab4 = st.tabs([
        "🏆 Primary Top 10 Bowlers (Frontline, 120+ Balls)",
        "⚡ Emerging & Part-Time Bowlers (Sub-120 Balls)",
        "📋 All-Role Bowling Leaderboard (Full Transparency)",
        "🔍 Bowler Deep-Dive: Control & Wicket Rate Analysis"
    ])

    with bw_tab1:
        st.markdown("### 🏆 Official Primary Top 10 Bowlers Under Defensive Pressure")
        st.caption("Criteria: Minimum 120 crisis legal deliveries, 5 crisis matches, and frontline bowling profile.")
        
        disp_bowl = data['top_bowl'][[
            'rank', 'canonical_display_name', 'primary_role', 'crisis_balls',
            'crisis_matches', 'crisis_wicket_rate', 'norm_wicket_rate', 'crisis_dot_pct',
            'consistency_score', 'bowling_pri'
        ]].copy()
        disp_bowl.columns = ['Rank', 'Player Name', 'Role', 'Crisis Balls', 'Matches', 'Crisis WR%', 'Norm WR%', 'Crisis Dot%', 'Consistency', 'Bowling PRI']
        
        st.dataframe(
            disp_bowl.style.format({
                'Crisis WR%': '{:.1f}%',
                'Norm WR%': '{:.1f}%',
                'Crisis Dot%': '{:.1f}%',
                'Consistency': '{:.2f}',
                'Bowling PRI': '{:.2f}',
                'Crisis Balls': '{:.0f}',
                'Matches': '{:.0f}',
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("""
        **Key Insights:**
        - **Mark Adair (#1, PRI 86.16):** Massive workload of 483 defensive pressure deliveries across 40 matches with 6.6% crisis wicket rate and 37.1% dot ball retention.
        - **Craig Young (#2, PRI 86.10):** Exceptional crisis wicket-taking capability (9.0% crisis WR) across 289 high-pressure balls.
        - **Trent Boult (#5, PRI 76.46):** Premier tournament workhorse with 879 defensive pressure deliveries across 70 matches, maintaining 36.7% dot balls.
        """)

    with bw_tab2:
        st.markdown("### ⚡ Emerging & Part-Time Bowlers Leaderboard")
        st.caption("Bowlers with 40–119 defensive crisis deliveries or batting all-rounders who bowl in high-leverage situations.")
        
        em_disp = data['em_bowl'].head(15)[[
            'emerging_rank', 'canonical_display_name', 'primary_role', 'crisis_balls',
            'crisis_wicket_rate', 'norm_wicket_rate', 'crisis_dot_pct', 'bowling_pri', 'eligibility_status'
        ]].copy()
        em_disp.columns = ['Rank', 'Player Name', 'Role', 'Crisis Balls', 'Crisis WR%', 'Norm WR%', 'Crisis Dot%', 'Bowling PRI', 'Status']
        
        st.dataframe(
            em_disp.style.format({
                'Crisis WR%': '{:.1f}%',
                'Norm WR%': '{:.1f}%',
                'Crisis Dot%': '{:.1f}%',
                'Bowling PRI': '{:.2f}',
                'Crisis Balls': '{:.0f}',
            }),
            use_container_width=True,
            hide_index=True
        )

        st.info("""
        **Methodology Note:**
        Players like **Harry Tector** (Ireland middle-order batter / part-time spin bowler, 54 crisis balls, 9.3% WR) and **Krishnappa Gowtham** (67 crisis balls, 7.5% WR) are tracked here.
        Setting the frontline threshold to 120 crisis legal deliveries guarantees that the Primary Top 10 consists strictly of genuine frontline bowlers who carry substantial tactical workloads.
        """)

    with bw_tab3:
        st.markdown("### 📋 All-Role Bowling Leaderboard (Unrestricted)")
        st.caption("All 596 evaluated bowlers. Use filters to inspect complete ranking data.")

        all_bw_filter = data['all_bowl'].copy()
        bw_role_opts = ['All'] + sorted(all_bw_filter['primary_role'].dropna().unique().tolist())
        selected_bw_role = st.selectbox("Filter by Role:", bw_role_opts, key="bw_role_sel")
        
        if selected_bw_role != 'All':
            all_bw_filter = all_bw_filter[all_bw_filter['primary_role'] == selected_bw_role]

        st.dataframe(
            all_bw_filter[[
                'overall_rank', 'canonical_display_name', 'primary_role', 'total_legal_balls',
                'crisis_balls', 'crisis_wicket_rate', 'crisis_dot_pct', 'bowling_pri', 'eligibility_status'
            ]].rename(columns={
                'overall_rank': 'Rank',
                'canonical_display_name': 'Player',
                'primary_role': 'Role',
                'total_legal_balls': 'Total Balls',
                'crisis_balls': 'Crisis Balls',
                'crisis_wicket_rate': 'Crisis WR%',
                'crisis_dot_pct': 'Crisis Dot%',
                'bowling_pri': 'Bowling PRI',
                'eligibility_status': 'Status'
            }).head(50),
            use_container_width=True,
            hide_index=True
        )

    with bw_tab4:
        st.markdown("### 🔍 Bowler Deep-Dive: Dot Retention vs Wicket Threat")
        
        el_bowl = data['all_bowl'][data['all_bowl']['eligibility_status'] == 'ELIGIBLE'].copy()
        
        fig_bw_scatter = px.scatter(
            el_bowl,
            x='crisis_dot_pct',
            y='crisis_wicket_rate',
            size='crisis_balls',
            color='primary_role',
            hover_name='canonical_display_name',
            hover_data=['crisis_matches', 'bowling_pri'],
            title="Crisis Wicket Rate vs Crisis Dot Ball % (Eligible Bowlers, Bubble Size = Crisis Balls)",
            labels={'crisis_dot_pct': 'Crisis Dot Ball %', 'crisis_wicket_rate': 'Crisis Wicket Rate (%)'},
            height=500,
        )
        fig_bw_scatter.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(family="sans-serif", size=12, color="#0F172A"),
        )
        st.plotly_chart(fig_bw_scatter, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4: METHODOLOGY, SCIENCE & DATA QUALITY
# ════════════════════════════════════════════════════════════════════════════
elif section == "4. Methodology, Science & Data Quality":
    st.markdown("## 🧠 Methodology, Scientific Modeling & Data Governance")
    st.markdown("""
    **Core Objective:** Complete reproducibility, statistical rigor, and defensible cricket engineering for the Rajasthan Royals hackathon.
    """)

    m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs([
        "📐 Dual Pressure Formulation",
        "🧮 PRI Formula & Empirical Bayes",
        "⚖️ Sensitivity Analysis (5 Weight Configs)",
        "🛡️ Data Governance & Quarantines"
    ])

    with m_tab1:
        st.markdown("### 📐 Dual Independent Pressure Models")
        st.markdown("""
        In professional cricket analytics, **batting crisis and bowling pressure are fundamentally different tactical states**:
        - **Batting Crisis (0–10 scale):** Wickets fallen before delivery (0–3.5), recent 12-ball cluster collapse (0–2.0), batter entry vulnerability (0–1.5), dot stagnation (0–1.5), multiplied by death-over leverage (1.25x).
        - **Bowling Defensive Pressure (0–10 scale):** Opponent resource depth (wickets in hand: 8–10 wkts = 3.0), innings phase (Death = 3.0, Powerplay = 2.0), opponent boundary momentum in last 12 legal balls (0–2.5), low dot pressure (0–1.5).
        
        Both models operate strictly on **pre-delivery context** to guarantee zero target leakage.
        """)

        st.dataframe(data['press_val'], use_container_width=True, hide_index=True)

    with m_tab2:
        st.markdown("### 🧮 Pressure Reliability Index (PRI) Formulation")
        st.latex(r"\text{PRI} = 100 \times \left( 0.35 M_{\text{norm}} + 0.35 A_{\text{norm}} + 0.20 C_{\text{norm}} + 0.10 S_{\text{norm}} \right)")
        
        st.markdown("""
        1. **Performance Maintenance ($M$, 35%):** Ratio of pressure performance to unconstrained normal baseline ($\text{SR}_{\text{crisis}}/\text{SR}_{\text{norm}}$ for batters; $\text{Dot}_{\text{crisis}}/\text{Dot}_{\text{norm}}$ for bowlers). Capped at [0.5, 1.5] to prevent small-sample anomalies.
        2. **Absolute Pressure Capability ($A$, 35%):** Shrunk via **Empirical Bayes**:
           - **Batting:** Normal-Normal conjugate shrinkage ($K=25.0$) shrinking individual strike rates towards the population mean based on delivery volume.
           - **Bowling:** Beta-Binomial conjugate shrinkage with Method-of-Moments prior estimation for event rates (wicket rate).
        3. **Exposure-Adjusted Consistency ($C$, 20%):** Exponential dispersion formula:
        """)
        st.latex(r"\text{Consistency}_i = \exp(-\text{CV}_i) \cdot \sqrt{\frac{m_i}{m_i + 3}}")
        st.markdown("""
        Continuous in $(0, 1]$, non-zero, and rewards sustained multi-match reliability.
        4. **Sample Confidence ($S$, 10%):** Logarithmic exposure score: $\min(1.0, \ln(1+n)/\ln(1+250))$.
        """)

    with m_tab3:
        st.markdown("### ⚖️ Sensitivity Analysis Across 5 Weight Configurations")
        st.markdown("""
        To prove mathematical robustness, rankings were recomputed across 5 distinct weighting schemes:
        - **Balanced Default:** 35% M, 35% A, 20% C, 10% S
        - **Maintenance Heavy:** 50% M, 25% A, 15% C, 10% S
        - **Absolute Heavy:** 25% M, 50% A, 15% C, 10% S
        - **Consistency Heavy:** 30% M, 30% A, 30% C, 10% S
        - **Equal Weights:** 25% M, 25% A, 25% C, 25% S
        """)
        
        st.dataframe(data['sens_df'].head(20), use_container_width=True, hide_index=True)
        st.caption("Spearman rank correlations across configurations exceed 0.88 for batters and 0.91 for bowlers, demonstrating high stability.")

    with m_tab4:
        st.markdown("### 🛡️ Data Governance & Engineering Audits")
        st.markdown("""
        1. **`extras1_runs` is Categorical, NOT a Run Count:** Integer codes (1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty) represent an enumeration codebook. **Never summed as runs.**
        2. **Score-Dependent Metrics Quarantined:** Because total extras semantics remain unconfirmed, derived team scores, required run rates, and bowler economy rates are quarantined to maintain 100% scientific defensibility.
        3. **Dismissal Attribution:** 571 run outs, 6 retired outs, and 2 obstructing-the-field events excluded from bowler wickets. Stumpings on wide balls are properly attributed.
        4. **Boundary Reconciliation:** 23 flagged boundary discrepancies reconciled via verified boolean flags.
        5. **Super Overs Quarantined:** 26 deliveries across Innings 3 & 4 quarantined from 20-over tactical ratings.
        """)

        st.markdown("#### 📋 Player Eligibility Audit Table")
        st.dataframe(data['elig_df'].head(30), use_container_width=True, hide_index=True)

# ── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("SupeRR Intelligence • Rajasthan Royals SupeRR Selector Season 2 • Built with Statistical Rigor & Scientific Defensibility")
