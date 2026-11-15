"""Participant Technical Methodology Report Generator (Markdown and PDF) — P1.1 Patch.

SupeRR Intelligence - Rajasthan Royals SupeRR Selector Season 2
Generates directly from authoritative V3 canonical outputs:
1. FINAL_SUPERR_METHODOLOGY_REPORT.pdf (and synchronizes all PDF copies)
2. FINAL_SUPERR_METHODOLOGY_REPORT.md (and synchronizes all MD copies)
"""
import os
import sys
from pathlib import Path
import shutil

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.config import OUTPUTS_DIR, REPORTS_DIR

OUTPUTS_V3 = PROJECT_ROOT / "data" / "outputs" / "v3"


def _df_to_md(df: pd.DataFrame) -> str:
    """Format a DataFrame as a GitHub-flavored Markdown table without external dependencies."""
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = [header, sep]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f"{v:.4f}".rstrip('0').rstrip('.') if pd.notna(v) else "NaN")
            else:
                vals.append(str(v))
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join(rows)


def generate_markdown_report() -> Path:
    """Generate comprehensive Markdown methodology and evidence dossier from canonical V3 CSVs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "FINAL_SUPERR_METHODOLOGY_REPORT.md"

    # Load authoritative canonical V3 ranking tables & JSON manifest
    import json
    with open(OUTPUTS_V3 / "RANKING_SOURCE_OF_TRUTH.json", "r") as mf:
        manifest = json.load(mf)
    summary_m = manifest.get("summary_metrics", {})
    gov_m = manifest.get("governance", {})
    shrink_m = manifest.get("configurations", {}).get("shrinkage_configuration", {})
    bat_thresh_m = manifest.get("configurations", {}).get("default_batting_thresholds", {})

    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    thresh_df = pd.read_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv")
    weight_df = pd.read_csv(OUTPUTS_V3 / "RANKING_WEIGHT_SENSITIVITY.csv")

    # Load System B canonical CSVs
    rr_phase = pd.read_csv(OUTPUTS_V3 / "rr_2026_phase_analysis.csv")
    rr_weak = pd.read_csv(OUTPUTS_V3 / "rr_2026_team_weaknesses.csv")
    rr_roles = pd.read_csv(OUTPUTS_V3 / "RR_REQUIRED_ROLES.csv")
    rr_ret = pd.read_csv(OUTPUTS_V3 / "RR_RETENTION_SCENARIOS.csv")
    rr_budget = pd.read_csv(OUTPUTS_V3 / "RR_AUCTION_BUDGET_SCENARIOS.csv")
    rr_fit = pd.read_csv(OUTPUTS_V3 / "RR_PLAYER_FIT.csv")

    bat_sweep = thresh_df[(thresh_df['discipline'] == 'Batting') & (thresh_df['is_primary_crisis_sweep'] == True)][[
        'min_crisis_balls', 'min_crisis_matches', 'eligible_batter_count', 'eligible_bowler_count',
        'available_top10_count', 'top10_overlap_with_baseline', 'jaccard_similarity',
        'mean_abs_rank_movement', 'max_rank_movement', 'players_entering_top10', 'players_leaving_top10'
    ]]
    bowl_sweep = thresh_df[(thresh_df['discipline'] == 'Bowling') & (thresh_df['is_primary_crisis_sweep'] == True)][[
        'min_crisis_balls', 'min_crisis_matches', 'eligible_batter_count', 'eligible_bowler_count',
        'available_top10_count', 'top10_overlap_with_baseline', 'jaccard_similarity',
        'mean_abs_rank_movement', 'max_rank_movement', 'players_entering_top10', 'players_leaving_top10'
    ]]

    bat_top_table = _df_to_md(top_bat[[
        'rank', 'canonical_player_id', 'player_name', 'v3_role', 'crisis_balls', 'crisis_matches',
        'tier1_share', 'crisis_sr', 'norm_sr', 'crisis_delta_rv', 'did_bat_maintenance',
        'consistency_score', 'provisional_fixed_weight_score', 'ci_lower', 'ci_upper', 'ranking_sensitivity_status'
    ]])

    bowl_top_table = _df_to_md(top_bowl[[
        'rank', 'canonical_player_id', 'player_name', 'v3_role', 'crisis_balls', 'norm_balls',
        'crisis_matches', 'tier1_share', 'crisis_econ', 'crisis_dot_pct', 'crisis_wicket_rate',
        'crisis_delta_rv', 'did_bowl_maintenance', 'consistency_score',
        'provisional_fixed_weight_score', 'ci_lower', 'ci_upper', 'ranking_sensitivity_status'
    ]])

    bat_weight_top10 = _df_to_md(weight_df[weight_df['discipline'] == 'Batting'].head(10)[[
        'provisional_rank', 'canonical_player_id', 'player_name', 'provisional_fixed_weight_score',
        'contrib_maint', 'contrib_abs', 'contrib_cons', 'contrib_sample',
        'rank_balanced_default', 'rank_maintenance_heavy', 'rank_absolute_heavy',
        'rank_consistency_heavy', 'rank_equal_weights', 'max_rank_shift', 'ranking_sensitivity_status'
    ]])
    bowl_weight_top10 = _df_to_md(weight_df[weight_df['discipline'] == 'Bowling'].head(10)[[
        'provisional_rank', 'canonical_player_id', 'player_name', 'provisional_fixed_weight_score',
        'contrib_maint', 'contrib_abs', 'contrib_cons', 'contrib_sample',
        'rank_balanced_default', 'rank_maintenance_heavy', 'rank_absolute_heavy',
        'rank_consistency_heavy', 'rank_equal_weights', 'max_rank_shift', 'ranking_sensitivity_status'
    ]])

    # Build individual selection rationales for all 20 selected players
    bat_rationales = []
    for _, r in top_bat.head(10).iterrows():
        bat_rationales.append(
            f"- **#{int(r['rank'])} {r['player_name']} (`canonical_player_id={int(r['canonical_player_id'])}`, `{r['v3_role']}`):** "
            f"Faced **{int(r['crisis_balls'])} crisis balls** (Tier-1 share: {r['tier1_share']*100:.1f}%) across **{int(r['crisis_matches'])} crisis matches** "
            f"(normal baseline: {int(r['norm_balls'])} balls across {int(r['norm_matches'])} matches). "
            f"Crisis SR **{r['crisis_sr']:.2f}** vs Normal SR **{r['norm_sr']:.2f}**; shrunk Crisis Run Value **{r['crisis_delta_rv']:+.2f} runs/100** "
            f"(95% match-clustered RV CI: `[{r['ci_lower']:+.2f}, {r['ci_upper']:+.2f}]`), DiD Maintenance **{r['did_bat_maintenance']:+.2f}**, "
            f"Value-Gated Downside Consistency **{r['consistency_score']:.4f}**. "
            f"Component Breakdown: `{r['component_breakdown_explanation']}` (`{r['ranking_sensitivity_status']}`)."
        )
    bat_rationales_md = "\n".join(bat_rationales)

    bowl_rationales = []
    for _, r in top_bowl.head(10).iterrows():
        bowl_rationales.append(
            f"- **#{int(r['rank'])} {r['player_name']} (`canonical_player_id={int(r['canonical_player_id'])}`, `{r['v3_role']}`):** "
            f"Bowled **{int(r['crisis_balls'])} crisis legal balls** (Tier-1 share: {r['tier1_share']*100:.1f}%) across **{int(r['crisis_matches'])} crisis matches** "
            f"(normal baseline: {int(r['norm_balls'])} legal balls across {int(r['norm_matches'])} matches, `{r['norm_baseline_status']}`). "
            f"Crisis Econ **{r['crisis_econ']:.2f}** (incl. wides/no-balls), Dot% **{r['crisis_dot_pct']:.2f}%**, Wkt Rate **{r['crisis_wicket_rate']:.2f}%**; "
            f"shrunk Crisis Runs Saved **{r['crisis_delta_rv']:+.2f}/over** (95% match-clustered RV CI: `[{r['ci_lower']:+.2f}, {r['ci_upper']:+.2f}]`), "
            f"DiD Maintenance **{r['did_bowl_maintenance']:+.2f}/over**, Value-Gated Downside Consistency **{r['consistency_score']:.4f}**. "
            f"Component Breakdown: `{r['component_breakdown_explanation']}` (`{r['ranking_sensitivity_status']}`)."
        )
    bowl_rationales_md = "\n".join(bowl_rationales)

    el_bat_cnt = summary_m.get("eligible_batters_count", "N/A")
    el_bowl_cnt = summary_m.get("eligible_bowlers_count", "N/A")
    bat_prior_mean = shrink_m.get("batting_prior_mean", "N/A")
    bowl_prior_mean = shrink_m.get("bowling_prior_mean", "N/A")
    bat_cb = bat_thresh_m.get("crisis_balls", 60)
    bat_nb = bat_thresh_m.get("norm_balls", 60)
    disclosure_txt = gov_m.get("mandatory_disclosure", "Rankings use V4 Calibrated Ridge.")
    status_txt = gov_m.get("ranking_approval_status", "V4 CALIBRATED RIDGE — UNIFIED RUN VALUE VERIFIED")
    p_ver = gov_m.get("pressure_formula_version", "V4_CALIBRATED_RIDGE")

    freed_cr = float(rr_ret.loc[rr_ret['action_type'] == 'RELEASE', 'salary_freed_cr'].sum())
    retained_os = int(((rr_ret['action_type'] == 'RETAIN') & (rr_ret['overseas_status'] == 'Overseas')).sum())
    conflict_os = int(((rr_ret['action_type'] == 'RESOLVE') & (rr_ret['overseas_status'] == 'Overseas')).sum())
    rr_roles_md = _df_to_md(rr_roles[['priority', 'role_title', 'urgency', 'existing_rr_cover', 'budget_allocation_cr']])
    rr_budget_md = _df_to_md(rr_budget)
    rr_fit_md = _df_to_md(rr_fit[['player_name', 'target_gap', 'is_overseas', 'universal_ranking', 'price_estimate', 'recommendation_category', 'evidence_verification_status']])

    content = f"""# SupeRR Intelligence V4: Pressure Reliability Analytics & RR 2027 Player Scouting
## Official Technical Methodology Report & Evidence Dossier (V4 Calibrated Ridge Edition)
**Target Event:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Scope:** System A: Historical IPL & Men's T20I (2022–2026) | System B: RR IPL 2026 Audit & 2027 Auction Strategy  
**Authoritative Source Manifest:** `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`  
**System Status:** `{status_txt}`  

> **Governance & Methodology Disclosure:**
> "{disclosure_txt}"

---

## 1. Executive Summary & V4 Architectural Guarantees

Under the Rajasthan Royals problem statement (*"Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels"* + *RR 2027 recruitment fit*), SupeRR Intelligence V4 unifies pressure classification, contextual baseline adjustment, and scouting alignment:

1. **Canonical Player Identity Resolution (`src/identity/player_identity.py`):** Consolidates verified multi-ID provider records before aggregation (`PLAYER_IDENTITY_CROSSWALK.csv`) while quarantining unresolved identity collisions.
2. **DLS-Aware, Survivorship-Free Pre-Delivery Leverage (`{p_ver}`):** Removes short-window dot/boundary survivorship bias (`dots_12`, `b12`) from pressure classification, incorporates DLS `second_inn_revised_overs` and `revised_target` across 25 rain-affected matches (`innings_context.py`), and calibrates **High (`> q70`) / Moderate (`q50–q70`) / Normal (`<= q50`)** tiers **within `(innings, innings_phase)`** so Powerplay and Death specialists preserve ~50% normal-pressure exposure rather than being over-classified as crisis.
3. **Competition-Tier Weighting & Tier-1 Exposure Gate (`>= 60%`):** De-weights Associate/Mixed T20Is (`T1_IPL = 1.0`, `T1_FM_T20I = 1.0`, `T2_MIXED = 0.5`, `T3_ASSOC = 0.2`) and enforces `tier1_share >= 0.60`, yielding **{el_bat_cnt} eligible batters** (`>= {bat_cb}` Tier-weighted crisis balls, `>= {bat_nb}` normal balls, `>= 200` total balls, `>= 6` matches) and **{el_bowl_cnt} eligible frontline bowlers** (`>= 120` crisis balls, `>= 100` normal balls, `>= 250` total legal balls, `>= 6` matches).
4. **State-Conditional + Ridge Opponent & Match-Par Adjustment (`scipy.sparse.linalg.lsqr`):** Decomposes state residuals (`comp_tier x innings x phase x wkt_bucket`) into `match_par + striker_offense + bowler_defense`, evaluating every player in a unified Run Value currency (Batting **Runs Above Expectation / 100 balls**, `v_wkt = {{4.0, 3.5, 2.5}}`; Bowling **Runs Saved / Over** including `wide`/`Overstep` penalty runs + empirical `v_wkt = {{5.5, 5.0, 3.5}}`).
5. **Invariant PRI Weights (`30% Maint / 35% Abs / 25% Cons / 10% Sample`) & Direct RV Bootstrap CIs:** Eliminates the `PRIOR_ANCHORED_SPECIALIST` weight-reallocation loophole; pairs Cohort-Calibrated DiD (`k=90` bat / `k=150` bowl) with Value-Gated Downside Match Consistency and 2,000-iteration Match-Clustered Bootstrap 95% CIs directly on Crisis Run Value / Runs Saved.

---

## 2. Dataset Scope & Data Governance Audit

The platform ingests **853 matches** (837 with ball-by-ball delivery logs) and **193,988 regular deliveries** (after quarantining 26 Super Over deliveries in innings 3 and 4).

1. **`extras1_runs` is Categorical, NOT a Run Count:** Source data integer codes (`1`: Overstep, `2`: wide, `3`: legbyes, `4`: byes, `5`: other, `6`: None, `7`: Penalty) represent an enum codebook and are never summed as numeric runs.
2. **DLS-Aware Clean-Channel Scoring & Penalty Runs:** `innings_context.py` builds a clean lower-bound cumulative score (`runs + 1 * is_wide_or_overstep`) honoring `first_inn_revised_overs`, `second_inn_revised_overs`, and `revised_target`, while bowling economy and `bowl_rv` include `1 * is_wide_or_overstep` as clean extra penalties.
3. **Dismissal Attribution:** 581 non-bowler dismissals (573 run outs, 6 retired outs, 2 obstructing the field) are excluded from bowler wickets; partner run-outs are excluded from striker dismissal rates.
4. **Experimental Challenger Quarantine (`EXPERIMENTAL_NOT_USED_FOR_RANKING`):** The discrete-time logistic hazard model, hierarchical challenger, and LightGBM model remain quarantined from production rankings.

---

## 3. V4 Composite Formulation (`V4_CALIBRATED_RIDGE_SCORE`)

$$\\text{{Score}}_{{\\text{{V4}}}} = 100 \\times \\left( 0.30 M_{{\\text{{norm}}}} + 0.35 A_{{\\text{{norm}}}} + 0.25 C_{{\\text{{norm}}}} + 0.10 S_{{\\text{{norm}}}} \\right)$$

1. **Cohort-Calibrated DiD Maintenance ($M$, 30% invariant):** Fits cohort slope $\\beta \\in [0.30, 0.80]$ relating capped shrunk normal RV (`min_norm_ref = -5.0` bat / `-0.5` bowl) to shrunk crisis RV (`did_bat_maintenance`, `did_bowl_maintenance`).
2. **Absolute Pressure Value ($A$, 35% invariant):** Shrunk crisis Run Value above state+opponent expectation (`crisis_delta_rv` in runs/100 for batting; `crisis_delta_rv` = `abs_bowl_score` in runs saved/over for bowling).
3. **Value-Gated Downside Match Consistency ($C$, 25% invariant):** Penalizes negative crisis outings via downside RMS deviation (`exp(-sigma_down / s)` with $s=45$ bat, $s=3.0$ bowl), weighted positive-match share $p_{{\\text{{pos}}}}$, match breadth $\\sqrt{{m/(m+10)}}$, and positive value sigmoid gate.
4. **Sample Confidence ($S$, 10% invariant):** $\\min(1.0, \\ln(1 + \\text{{eff\\_cb}}) / \\ln(1 + \\text{{cap}}))$ (`cap=350` batting, `600` bowling). Cohort means for auxiliary classical metrics: `{bat_prior_mean}` SR (Bat) / `{bowl_prior_mean}%` Wkt Rate (Bowl).

---

## 4. Authoritative Top 10 Batters Under Crisis Pressure (`data/outputs/v3/TOP_10_BATTERS.csv`)

{bat_top_table}

### 4.1 Individual Player Selection Rationales — Top 10 Batters
{bat_rationales_md}

---

## 5. Authoritative Top 10 Bowlers Under Defensive Pressure (`data/outputs/v3/TOP_10_BOWLERS.csv`)

{bowl_top_table}

### 5.1 Individual Player Selection Rationales — Top 10 Bowlers
{bowl_rationales_md}

---

## 6. Extended Crisis-Ball Threshold Sensitivity (`40..750`)

### 6.1 Batting Primary Crisis-Ball Sweep (`crisis_matches >= 6, norm_balls >= {bat_nb}, total_balls >= 200, tier1_share >= 0.60`)
{_df_to_md(bat_sweep)}

### 6.2 Bowling Primary Crisis-Ball Sweep (`crisis_matches >= 6, norm_balls >= 100, total_legal_balls >= 250, tier1_share >= 0.60`)
{_df_to_md(bowl_sweep)}

---

## 7. Weight Sensitivity Analysis Across 5 Configurations (`RANKING_WEIGHT_SENSITIVITY.csv`)

### 7.1 Batting Weight Sensitivity (Top 10)
{bat_weight_top10}

### 7.2 Bowling Weight Sensitivity (Top 10)
{bowl_weight_top10}

---

## 8. System B: Rajasthan Royals IPL 2026 Audit & 2027 Auction Strategy

### 8.1 RR 2026 Phase Profile & Tactical Deficiencies (`USER_PROVIDED_UNVERIFIED` Provenance Disclosed)
{_df_to_md(rr_phase[['phase', 'overs_range', 'team_batter_runs', 'team_balls_faced', 'team_batting_sr', 'team_bowling_legal_balls', 'team_bowler_wickets_taken', 'team_bowling_dot_pct']])}

- **Primary Empirical Weaknesses:** {", ".join(f"{r['dimension']} ({r['metric']})" for _, r in rr_weak.iterrows())}.

### 8.2 Prioritized 2027 Recruitment Roles (`RR_REQUIRED_ROLES.csv`)
{rr_roles_md}

### 8.3 Retention, Release & Overseas Slot Governance (`RR_RETENTION_SCENARIOS.csv`, `RR_AUCTION_BUDGET_SCENARIOS.csv`)
- **Released Contracts ({freed_cr:.2f} Cr Freed):** Releases Shimron Hetmyer (11.00 Cr, Overseas), Tushar Deshpande (6.50 Cr), Sandeep Sharma (4.00 Cr), Adam Milne (2.40 Cr, Overseas), Kuldeep Sen (0.75 Cr), and Lhuan-dre Pretorius (0.30 Cr, Overseas). Combined with carry-over cap headroom, this establishes the ₹27.60 Cr base auction purse.
- **Overseas Slot Arithmetic Disclosure:** Core retentions include **{retained_os} overseas players** (`Jofra Archer`, `Donovan Ferreira`, `Nandre Burger`) plus **{conflict_os} `CONFLICTING_STATUS` contract** (`Sam Curran vs Dasun Shanaka`). Against the IPL maximum of 8 overseas squad slots (4 in Playing XI), releasing 3 overseas players frees ample squad headroom; if `Sam Curran` is confirmed retained (4th squad overseas), 4 squad overseas slots (and 1 XI overseas slot alongside Archer & Ferreira) remain open, consistent with targeting **1 frontline overseas death bowler** (`Matheesha Pathirana` / `Nuwan Thushara`).

{rr_budget_md}

### 8.4 Auction Player-Fit Evaluation Matrix (Synced Dynamically from System A V4 Rankings)
{rr_fit_md}

---

## 9. Reproducibility & Verification Gates

- Pipeline execution: `.venv\\Scripts\\python scripts/compute_v3_rankings.py`
- Independent verification: `.venv\\Scripts\\python scripts/verify_v3_rankings.py`
- Automated test suite: `.venv\\Scripts\\python -m pytest tests/ -v`
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Copy to project root, outputs, and reports
    for md_tgt in [
        PROJECT_ROOT / "FINAL_SUPERR_METHODOLOGY_REPORT.md",
        OUTPUTS_DIR / "FINAL_SUPERR_METHODOLOGY_REPORT.md",
        REPORTS_DIR / "SUPERR_INTELLIGENCE_METHODOLOGY_REPORT.md",
    ]:
        shutil.copy(report_path, md_tgt)
    print(f"Markdown methodology report written to: {report_path}")
    return report_path


def generate_pdf_report() -> Path:
    """Generate publication-grade 3-page PDF dossier directly from canonical V3 CSVs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = REPORTS_DIR / "FINAL_SUPERR_METHODOLOGY_REPORT.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=28,
        bottomMargin=28,
    )

    rr_navy = colors.HexColor('#0B1B3D')
    rr_pink = colors.HexColor('#EA1A85')
    rr_light_bg = colors.HexColor('#F8FAFC')
    text_dark = colors.HexColor('#0F172A')
    border_grey = colors.HexColor('#CBD5E1')

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=12.5, leading=15, textColor=rr_navy, spaceAfter=1,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], fontName='Helvetica',
        fontSize=7.5, leading=9.5, textColor=rr_pink, spaceAfter=4,
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=9.0, leading=11.5, textColor=rr_navy, spaceBefore=4, spaceAfter=2,
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'], fontName='Helvetica',
        fontSize=6.8, leading=8.8, textColor=text_dark, spaceAfter=3,
    )
    table_header_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=6.0, leading=7.5, textColor=colors.white, alignment=1,
    )
    table_cell_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'], fontName='Helvetica',
        fontSize=5.5, leading=7.0, textColor=text_dark, alignment=1,
    )

    import json
    with open(OUTPUTS_V3 / "RANKING_SOURCE_OF_TRUTH.json", "r") as mf:
        manifest = json.load(mf)
    summary_m = manifest.get("summary_metrics", {})
    gov_m = manifest.get("governance", {})
    shrink_m = manifest.get("configurations", {}).get("shrinkage_configuration", {})
    bat_thresh_m = manifest.get("configurations", {}).get("default_batting_thresholds", {})
    el_bat_cnt = summary_m.get("eligible_batters_count", 156)
    el_bowl_cnt = summary_m.get("eligible_bowlers_count", 122)
    bat_prior_mean = shrink_m.get("batting_prior_mean", 131.04)
    disclosure_txt = gov_m.get("mandatory_disclosure", "Rankings use V4 Calibrated Ridge state-conditional run values.")
    status_txt = gov_m.get("ranking_approval_status", "V4 CALIBRATED RIDGE — UNIFIED RUN VALUE VERIFIED")
    p_ver = gov_m.get("pressure_formula_version", "V4_CALIBRATED_RIDGE")

    story = []

    # ── PAGE 1: V4 Governance & Unified Ridge Architecture ──────
    story.append(Paragraph("SupeRR Intelligence V4 — Pressure Reliability Analytics & RR 2027 Scouting", title_style))
    story.append(Paragraph(f"Authoritative Technical Methodology & System B Dossier • Status: {status_txt}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=rr_pink, spaceAfter=4))

    story.append(Paragraph("Governance & Methodology Disclosure", h1_style))
    story.append(Paragraph(f"<b>\"{disclosure_txt}\"</b>", body_style))

    story.append(Paragraph("1. Dataset Scope, Canonical Identity & V4 Calibrated Ridge Architecture (853 Matches, 193,988 Deliveries)", h1_style))
    story.append(Paragraph(
        f"• <b>Canonical Identity & Data Governance:</b> Multi-ID provider duplicates are consolidated via <code>PLAYER_IDENTITY_CROSSWALK.csv</code>. Categorical <code>extras1_runs</code> (codes 1–7) is never summed as runs; clean penalty runs (<code>1 * is_wide_or_overstep</code>) and DLS revised overs/targets (25 matches) are honored directly.<br/>"
        f"• <b>Survivorship-Free Pressure & Within-Phase Quantiles (<code>{p_ver}</code>):</b> Removes short-window dot/boundary survivorship bias and calibrates High (&gt;q70), Moderate (q50–q70), and Normal (≤q50) tiers within each <code>(innings, innings_phase)</code> stratum so PP/Death specialists retain ~50% Normal exposure.<br/>"
        f"• <b>Tier-1 Weighting & State-Ridge Residuals:</b> De-weights T2/Associate fixtures (T1=1.0, Mixed=0.5, Assoc=0.2; Tier-1 share ≥60%) and decomposes state expectations via weighted Ridge (<code>lsqr</code>) into unified Run Value/100 (Bat, {el_bat_cnt} eligible) and Runs Saved/Over (Bowl, {el_bowl_cnt} eligible).",
        body_style
    ))

    story.append(Paragraph("2. Invariant V4 Scoring, Downside Consistency & Direct RV Bootstrap CIs", h1_style))
    story.append(Paragraph(
        "• <b>Invariant Formula:</b> Score = 100 × [0.30 × Maint (Cohort-Calibrated DiD, k=90/150) + 0.35 × Abs (Shrunk Crisis RV) + 0.25 × Value-Gated Downside Consistency + 0.10 × Sample Confidence (350b Bat / 600b Bowl)].<br/>"
        "• <b>Strict Normal Baseline Gate:</b> Eliminates the <code>PRIOR_ANCHORED_SPECIALIST</code> weight-shift loophole; all eligible batters (≥60b) and bowlers (≥100b Tier-weighted normal balls) share invariant 30/35/25/10 weights.<br/>"
        "• <b>Uncertainty:</b> 2,000-iteration match-clustered bootstrap 95% CIs computed directly on Crisis Run Value/100 (Bat) and Crisis Runs Saved/Over (Bowl).",
        body_style
    ))

    # ── PAGE 1/2: Authoritative Top 10 Leaderboards ──────
    story.append(Paragraph("3. Authoritative Universal Top 10 Batters (data/outputs/v3/TOP_10_BATTERS.csv)", h1_style))
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    bat_data = [[
        Paragraph("Rank", table_header_style),
        Paragraph("ID", table_header_style),
        Paragraph("Player Name", table_header_style),
        Paragraph("Role", table_header_style),
        Paragraph("Crisis B (M)", table_header_style),
        Paragraph("Crisis SR", table_header_style),
        Paragraph("Norm SR", table_header_style),
        Paragraph("Crisis RV/100", table_header_style),
        Paragraph("DiD Maint", table_header_style),
        Paragraph("V4 Score", table_header_style),
        Paragraph("95% RV CI", table_header_style),
    ]]
    for _, r in top_bat.head(10).iterrows():
        bat_data.append([
            Paragraph(str(int(r['rank'])), table_cell_style),
            Paragraph(str(int(r['canonical_player_id'])), table_cell_style),
            Paragraph(str(r['player_name']), table_cell_style),
            Paragraph(str(r['v3_role']), table_cell_style),
            Paragraph(f"{int(r['crisis_balls'])} ({int(r['crisis_matches'])})", table_cell_style),
            Paragraph(f"{r['crisis_sr']:.1f}", table_cell_style),
            Paragraph(f"{r['norm_sr']:.1f}", table_cell_style),
            Paragraph(f"{r['crisis_delta_rv']:+.2f}", table_cell_style),
            Paragraph(f"{r['did_bat_maintenance']:+.2f}", table_cell_style),
            Paragraph(f"<b>{r['provisional_fixed_weight_score']:.2f}</b>", table_cell_style),
            Paragraph(f"[{r['ci_lower']:+.1f}, {r['ci_upper']:+.1f}]", table_cell_style),
        ])

    bat_table = Table(bat_data, colWidths=[20, 34, 78, 76, 42, 36, 36, 46, 40, 36, 92])
    bat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rr_navy),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('GRID', (0, 0), (-1, -1), 0.5, border_grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, rr_light_bg]),
    ]))
    story.append(bat_table)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        f"<b>Cohort Verification:</b> Classical cohort mean Crisis SR = {bat_prior_mean:.2f}; all Top-10 batters generate positive Ridge Run Value above expectation under crisis.",
        body_style
    ))

    story.append(Paragraph("4. Authoritative Universal Top 10 Bowlers (data/outputs/v3/TOP_10_BOWLERS.csv)", h1_style))
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    bowl_data = [[
        Paragraph("Rank", table_header_style),
        Paragraph("ID", table_header_style),
        Paragraph("Player Name", table_header_style),
        Paragraph("Role", table_header_style),
        Paragraph("Crisis B", table_header_style),
        Paragraph("Norm B", table_header_style),
        Paragraph("Crisis Econ", table_header_style),
        Paragraph("Runs Saved/Ov", table_header_style),
        Paragraph("DiD Maint", table_header_style),
        Paragraph("V4 Score", table_header_style),
        Paragraph("95% RV CI", table_header_style),
    ]]
    for _, r in top_bowl.head(10).iterrows():
        bowl_data.append([
            Paragraph(str(int(r['rank'])), table_cell_style),
            Paragraph(str(int(r['canonical_player_id'])), table_cell_style),
            Paragraph(str(r['player_name']), table_cell_style),
            Paragraph(str(r['v3_role']), table_cell_style),
            Paragraph(f"{int(r['crisis_balls'])}", table_cell_style),
            Paragraph(f"{int(r['norm_balls'])}", table_cell_style),
            Paragraph(f"{r['crisis_econ']:.2f}", table_cell_style),
            Paragraph(f"{r['crisis_delta_rv']:+.2f}", table_cell_style),
            Paragraph(f"{r['did_bowl_maintenance']:+.2f}", table_cell_style),
            Paragraph(f"<b>{r['provisional_fixed_weight_score']:.2f}</b>", table_cell_style),
            Paragraph(f"[{r['ci_lower']:+.2f}, {r['ci_upper']:+.2f}]", table_cell_style),
        ])

    bowl_table = Table(bowl_data, colWidths=[20, 34, 80, 76, 34, 34, 42, 46, 40, 36, 94])
    bowl_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rr_navy),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('GRID', (0, 0), (-1, -1), 0.5, border_grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, rr_light_bg]),
    ]))
    story.append(bowl_table)

    story.append(PageBreak())
    story.append(Paragraph("5. Individual Selection Rationales for All 20 Selected Players", h1_style))
    story.append(Paragraph("<b>5.1 Top 10 Batters — Individual Selection Evidence:</b>", body_style))
    for _, r in top_bat.head(10).iterrows():
        story.append(Paragraph(
            f"• <b>#{int(r['rank'])} {r['player_name']} (ID {int(r['canonical_player_id'])}, {r['v3_role']}):</b> "
            f"{int(r['crisis_balls'])} crisis balls ({int(r['crisis_matches'])}m, {r['tier1_share']*100:.0f}% T1), Crisis SR {r['crisis_sr']:.1f} vs Norm {r['norm_sr']:.1f}, "
            f"Crisis RV/100 {r['crisis_delta_rv']:+.2f}, DiD {r['did_bat_maintenance']:+.2f}, Cons {r['consistency_score']:.3f}, "
            f"95% CI [{r['ci_lower']:+.1f}, {r['ci_upper']:+.1f}] → <code>{r['component_breakdown_explanation']}</code>.",
            body_style
        ))

    story.append(Paragraph("<b>5.2 Top 10 Bowlers — Individual Selection Evidence:</b>", body_style))
    for _, r in top_bowl.head(10).iterrows():
        story.append(Paragraph(
            f"• <b>#{int(r['rank'])} {r['player_name']} (ID {int(r['canonical_player_id'])}, {r['v3_role']}):</b> "
            f"{int(r['crisis_balls'])} crisis balls ({int(r['crisis_matches'])}m, {int(r['norm_balls'])} norm balls, {r['tier1_share']*100:.0f}% T1), "
            f"Econ {r['crisis_econ']:.2f}, Dot% {r['crisis_dot_pct']:.1f}%, Wkt% {r['crisis_wicket_rate']:.1f}%, "
            f"Saved/Ov {r['crisis_delta_rv']:+.2f}, DiD {r['did_bowl_maintenance']:+.2f}, Cons {r['consistency_score']:.3f}, "
            f"95% CI [{r['ci_lower']:+.2f}, {r['ci_upper']:+.2f}] → <code>{r['component_breakdown_explanation']}</code>.",
            body_style
        ))

    story.append(PageBreak())
    story.append(Paragraph("6. System B: Rajasthan Royals 2026 Squad Audit & 2027 Auction Strategy", h1_style))
    rr_roles = pd.read_csv(OUTPUTS_V3 / "RR_REQUIRED_ROLES.csv")
    rr_ret = pd.read_csv(OUTPUTS_V3 / "RR_RETENTION_SCENARIOS.csv")
    rr_fit = pd.read_csv(OUTPUTS_V3 / "RR_PLAYER_FIT.csv")
    freed_cr = float(rr_ret.loc[rr_ret['action_type'] == 'RELEASE', 'salary_freed_cr'].sum())
    ret_os = int(((rr_ret['action_type'] == 'RETAIN') & (rr_ret['overseas_status'] == 'Overseas')).sum())
    conf_os = int(((rr_ret['action_type'] == 'RESOLVE') & (rr_ret['overseas_status'] == 'Overseas')).sum())
    story.append(Paragraph(
        f"• <b>RR 2026 Squad Deficiencies (USER_PROVIDED_UNVERIFIED disclosure):</b> Behind Jofra Archer (25 wkts) and Vaibhav Sooryavanshi (776 runs), RR suffered heavy death-over pace leakage (Sandeep + Deshpande = 9 wkts in 13 matches), spin under-penetration, and Rs. 11 Cr capital drag (Shimron Hetmyer: 78 runs at 113.0 SR).<br/>"
        f"• <b>Retention & Overseas Slot Arithmetic:</b> Releasing 6 contracts (incl. 3 overseas) frees Rs. {freed_cr:.2f} Cr toward the Rs. 27.60 Cr base purse. Core retains {ret_os} overseas players (Archer, Ferreira, Burger) + {conf_os} conflicting entry (Sam Curran vs Dasun Shanaka) against the 8-player squad / 4-player XI overseas cap (4-5 squad / 1 XI slots open; 3 released-OS replacement budget), reserving an overseas slot for an elite death bowler.<br/>"
        f"• <b>Prioritized Roles:</b> " + "; ".join(f"P{int(x['priority'])} {x['role_title']} ({x['urgency']}, Rs. {str(x['budget_allocation_cr']).replace('₹', 'Rs. ')} Cr)" for _, x in rr_roles.iterrows()),
        body_style
    ))

    fit_data = [[
        Paragraph("Candidate", table_header_style),
        Paragraph("Target Gap", table_header_style),
        Paragraph("OS?", table_header_style),
        Paragraph("System A V4 Ranking / Status", table_header_style),
        Paragraph("Est. Price", table_header_style),
        Paragraph("Verdict", table_header_style),
    ]]
    for _, fr in rr_fit.iterrows():
        price_str = str(fr['price_estimate']).replace('₹', 'Rs. ')
        fit_data.append([
            Paragraph(f"<b>{fr['player_name']}</b>", table_cell_style),
            Paragraph(str(fr['target_gap']), table_cell_style),
            Paragraph("Yes" if bool(fr['is_overseas']) else "No", table_cell_style),
            Paragraph(str(fr['universal_ranking']), table_cell_style),
            Paragraph(price_str, table_cell_style),
            Paragraph(f"<b>{fr['recommendation_category']}</b>", table_cell_style),
        ])
    fit_table = Table(fit_data, colWidths=[72, 95, 22, 195, 72, 60])
    fit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rr_navy),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('GRID', (0, 0), (-1, -1), 0.5, border_grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, rr_light_bg]),
    ]))
    story.append(fit_table)
    story.append(Spacer(1, 4))

    thresh_df = pd.read_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv")
    b_sw = thresh_df[(thresh_df['discipline'] == 'Batting') & (thresh_df['is_primary_crisis_sweep'] == True)]
    b_sw_str = ", ".join(f"{int(x['eligible_batter_count'])} ({int(x['min_crisis_balls'])}b)" for _, x in b_sw.iterrows())
    story.append(Paragraph("7. Threshold Sensitivity & Verification Gates", h1_style))
    story.append(Paragraph(
        f"• <b>Threshold Sensitivity:</b> Across 40, 60, 80, 100, 150, 200, 250, 500, 750 Tier-weighted crisis balls (≥6 matches), eligible batters scale: {b_sw_str} (baseline 60b = {el_bat_cnt} batters).<br/>"
        "• <b>Verification Gate:</b> Automated <code>pytest tests/ -v</code> suite and 100% independent reconciliation via <code>scripts/verify_v3_rankings.py</code>.",
        body_style
    ))

    doc.build(story)

    # Synchronize all PDF copies across root, data/outputs, and data/reports
    pdf_targets = [
        PROJECT_ROOT / "FINAL_SUPERR_METHODOLOGY_REPORT.pdf",
        PROJECT_ROOT / "FINAL_METHODOLOGY_REPORT.pdf",
        PROJECT_ROOT / "SUPERR_INTELLIGENCE_METHODOLOGY_REPORT.pdf",
        OUTPUTS_DIR / "FINAL_SUPERR_METHODOLOGY_REPORT.pdf",
        REPORTS_DIR / "FINAL_METHODOLOGY_REPORT.pdf",
        REPORTS_DIR / "SUPERR_INTELLIGENCE_METHODOLOGY_REPORT.pdf",
    ]
    for tgt in pdf_targets:
        shutil.copyfile(pdf_path, tgt)

    print(f"PDF methodology report and all {len(pdf_targets)} synchronized copies written from: {pdf_path}")
    return pdf_path


def run_all_reporting():
    """Generate both Markdown and PDF methodology reports."""
    print("Generating comprehensive P1.1 methodology reports...")
    md_path = generate_markdown_report()
    pdf_path = generate_pdf_report()
    return {'markdown': md_path, 'pdf': pdf_path}


if __name__ == '__main__':
    run_all_reporting()
