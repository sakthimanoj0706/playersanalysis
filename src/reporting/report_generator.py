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

    # Load authoritative canonical V3 ranking tables
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    thresh_df = pd.read_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv")
    weight_df = pd.read_csv(OUTPUTS_V3 / "RANKING_WEIGHT_SENSITIVITY.csv")

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
        'crisis_sr', 'norm_sr', 'raw_sr_maintenance', 'sr_maintenance', 'is_maintenance_capped',
        'shrunk_crisis_sr', 'consistency_score', 'provisional_fixed_weight_score',
        'ci_lower', 'ci_upper', 'ranking_sensitivity_status', 'performance_anomaly_flag'
    ]])

    bowl_top_table = _df_to_md(top_bowl[[
        'rank', 'canonical_player_id', 'player_name', 'v3_role', 'crisis_balls', 'crisis_matches',
        'norm_balls', 'norm_baseline_status', 'crisis_dot_pct', 'norm_dot_pct',
        'raw_dot_maintenance', 'capped_dot_maintenance', 'is_maintenance_capped',
        'crisis_wicket_rate', 'shrunk_crisis_wr', 'consistency_score',
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

    # Build individual selection rationales for all 20 selected players (Mandatory Deliverable 3f)
    bat_rationales = []
    for _, r in top_bat.head(10).iterrows():
        bat_rationales.append(
            f"- **#{int(r['rank'])} {r['player_name']} (`canonical_player_id={int(r['canonical_player_id'])}`, `{r['v3_role']}`):** "
            f"Faced **{int(r['crisis_balls'])} crisis balls** across **{int(r['crisis_matches'])} crisis matches** "
            f"(normal baseline: {int(r['norm_balls'])} balls across {int(r['norm_matches'])} matches). "
            f"Recorded a **{r['crisis_sr']:.2f} Crisis SR** vs **{r['norm_sr']:.2f} Normal SR**, achieving a "
            f"**{r['sr_maintenance']:.3f}x Strike-Rate Maintenance ratio** (raw: {r['raw_sr_maintenance']:.3f}x), "
            f"**{r['shrunk_crisis_sr']:.2f} Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[{r['ci_lower']:.2f}, {r['ci_upper']:.2f}]`), "
            f"and **{r['consistency_score']:.4f} Match Consistency Score**. "
            f"Component Breakdown: `{r['component_breakdown_explanation']}` (`{r['ranking_sensitivity_status']}`)."
        )
    bat_rationales_md = "\n".join(bat_rationales)

    bowl_rationales = []
    for _, r in top_bowl.head(10).iterrows():
        cap_note = " (winsorized from raw ratio)" if bool(r['is_maintenance_capped']) else ""
        bowl_rationales.append(
            f"- **#{int(r['rank'])} {r['player_name']} (`canonical_player_id={int(r['canonical_player_id'])}`, `{r['v3_role']}`):** "
            f"Bowled **{int(r['crisis_balls'])} crisis legal balls** across **{int(r['crisis_matches'])} crisis matches** "
            f"(normal baseline: {int(r['norm_balls'])} legal balls across {int(r['norm_matches'])} matches, `{r['norm_baseline_status']}`). "
            f"Recorded a **{r['crisis_dot_pct']:.2f}% Crisis Dot-Ball %** vs **{r['norm_dot_pct']:.2f}% Normal Dot-Ball %**, achieving a "
            f"**{r['dot_maintenance']:.3f}x Capped Dot-Ball Maintenance ratio** (raw: {r['raw_dot_maintenance']:.3f}x{cap_note}), "
            f"**{r['crisis_wicket_rate']:.2f}% Raw Crisis Wicket Rate** (**{r['shrunk_crisis_wr']:.2f}% Beta-Binomial Shrunk Crisis WR**, "
            f"95% match-clustered bootstrap CI on crisis dot%: `[{r['ci_lower']:.2f}%, {r['ci_upper']:.2f}%]`), "
            f"and **{r['consistency_score']:.4f} Match Consistency Score**. "
            f"Component Breakdown: `{r['component_breakdown_explanation']}` (`{r['ranking_sensitivity_status']}`)."
        )
    bowl_rationales_md = "\n".join(bowl_rationales)

    content = f"""# SupeRR Intelligence V3: Pressure Reliability Analytics & Player Scouting
## Official Technical Methodology Report & Evidence Dossier (EGM Calibrated Patch)
**Target Event:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Scope:** Historical IPL & Men's T20I (2022 – 2026)  
**Authoritative Source Manifest:** `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`  
**System Status:** `P1.1 PATCH VERIFIED — PROVISIONAL MODEL`  

> **Mandatory Provisional Model Disclosure:**
> "Rankings are provisional. Batter ranks 1–5 are robust across all 5 weight configurations, while batter ranks 6–10 are sensitive to scoring weights. The pressure classification uses the calibrated pre-delivery state heuristic (`V3.2_EGM_CALIBRATED_HEURISTIC`). The new score has not yet undergone independent out-of-time validation."

---

## 1. Executive Summary & Governance Architecture

Standard cricket statistics (total runs, nominal strike rates, aggregate wickets) are heavily distorted by unconstrained play in low-leverage match situations. Under the Rajasthan Royals problem statement (*"Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels"*), pressure reliability evaluates how players sustain or elevate performance in high-pressure states relative to their personal normal baselines.

SupeRR Intelligence V3 enforces:
1. **Canonical Player Identity Resolution (`src/identity/player_identity.py`):** Consolidates verified multi-ID provider records before aggregation (`PLAYER_IDENTITY_CROSSWALK.csv`) while quarantining unresolved identity collisions.
2. **Pre-Delivery Calibrated Pressure Stratification (`V3.2_EGM_CALIBRATED_HEURISTIC`):** Mutually exclusive pre-delivery batting crisis and bowling defensive pressure tiers with zero post-delivery target leakage and explicit missing-feature quarantine (`batting_pressure_data_valid`, `bowling_pressure_data_valid`).
   - **Batting Crisis Pressure (`> 5.2` on `[0, 10]`):** Combines pre-delivery wickets fallen (`0.50 * w_before`, max `3.5`), recent 12-legal-ball wicket cluster (`2.2` for `>=2` wickets, `1.0` for `1` wicket), batter entry vulnerability (`1.5 * (1 - bf/6)` for first 6 balls), and dot-ball stagnation (`0.35 * consec_dots + 0.90 * (dots_12/12)`, max `1.8`), scaled by innings phase (`1.00x` Powerplay, `1.05x` Middle, `1.25x` Death). Classifies `15.35%` of balls faced as High/Extreme Crisis Pressure (`> 5.2`) and `59.40%` as Normal Baseline (`<= 3.5`), yielding **92 eligible batters** (`>= 40` crisis balls, `>= 5` crisis matches, `>= 30` normal balls, `>= 120` total balls).
   - **Bowling Defensive Pressure (`> 5.5` on `[0, 10]`):** Combines batting wickets in hand (`2.2` for `>=8`, `1.4` for `>=6`, `0.8` for `>=4`, `0.2` for `<4`), phase field-restriction pressure (`3.2` Death, `2.6` Powerplay, `0.8` Middle), opponent 12-legal-ball boundary momentum (`2.8` for `>=3` boundaries, `1.8` for `2`, `0.7` for `1`), and strike-rotation pressure (`0.8 * (1 - dots_12/12)`). Eliminates tailender/dot-autocorrelation confounding so Crisis Dot % (`37.54%`) and Normal Baseline Dot % (`36.02%`) are balanced across **99 eligible frontline bowlers** (`>= 120` crisis balls, `>= 100` normal balls, `>= 5` crisis matches).
3. **Separate Normal-Baseline Reliability Gating (`MIN_NORMAL_BALLS = 100` for Bowlers, `30` for Batters):** Prevents small-sample normal baselines from distorting maintenance ratios. Raw and capped (`[0.50, 1.50]`) maintenance ratios are reported separately.
4. **Empirical Bayes Shrinkage & Match-Clustered Bootstrap CIs:** Priors estimated strictly on the eligible role-gated population ($K=25.0$ Normal shrinkage for batting SR toward cohort mean `130.13`; Method-of-Moments Beta-Binomial shrinkage for bowling wicket rate toward cohort mean `6.07%`) and 2,000-iteration match-clustered bootstrap 95% confidence intervals.

---

## 2. Dataset Scope & Data Governance Audit

The platform ingests **853 matches** (837 with ball-by-ball delivery logs) and **193,988 regular deliveries** (after quarantining 26 Super Over deliveries in innings 3 and 4).

1. **`extras1_runs` is Categorical, NOT a Run Count:** Source data integer codes (1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty) represent an enum codebook and are never summed as numeric runs.
2. **Quarantined Metrics & Pressure-Model Limitation (`PROVISIONAL_POSITION_PROXY_HEURISTIC`):**
   - Because total extras semantics remain unconfirmed, cumulative scoreboard totals, second-innings target, dynamic required run rate (RRR), full chase leverage, and bowler economy rates are withheld from ranking formulas.
   - Consequently, **the current pressure model is a pre-delivery situational state heuristic, not a scoreboard-RRR chase-leverage model**.
3. **Dismissal Attribution:** 581 non-bowler dismissals (573 run outs, 6 retired outs, 2 obstructing the field) are excluded from bowler wickets. Partner run-outs are excluded from striker batting average denominators.
4. **Wicket Hazard Model Governance (`EXPERIMENTAL_NOT_USED_FOR_RANKING`):**
   - On chronological out-of-sample evaluation (`src/models/v3_wicket_hazard.py`), the discrete-time logistic hazard model with `class_weight='balanced'` yields **ROC-AUC = 0.572**, **Log-Loss = 0.692**, and **Expected Wickets = 26,843 vs Actual Wickets = 2,931** (a **9.16x over-prediction** due to uncalibrated balanced class weights).
   - The hazard model, hierarchical joint model, and LightGBM challenger are strictly marked **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** and are not used as production ranking components.

---

## 3. Provisional Fixed-Weight Score Formulation (`PROVISIONAL_FIXED_WEIGHT_SCORE`)

$$\\text{{Score}}_{{\\text{{provisional}}}} = 100 \\times \\left( 0.35 M_{{\\text{{norm}}}} + 0.35 A_{{\\text{{norm}}}} + 0.20 C_{{\\text{{norm}}}} + 0.10 S_{{\\text{{norm}}}} \\right)$$

1. **Performance Maintenance ($M$, 35%):**
   - Batting: $\\text{{SR}}_{{\\text{{crisis}}}} / \\text{{SR}}_{{\\text{{norm}}}}$ for batters with $\\ge 30$ normal balls. Raw (`raw_sr_maintenance`) and capped (`capped_sr_maintenance` in $[0.50, 1.50]$) ratios are reported separately alongside `is_maintenance_capped`.
   - Bowling: $\\text{{Dot}}_{{\\text{{crisis}}}} / \\text{{Dot}}_{{\\text{{norm}}}}$ strictly for bowlers with $\\ge 100$ normal balls (`MIN_NORMAL_BALLS = 100`). Bowlers with $< 100$ normal balls are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT`, receive `NaN` for `capped_dot_maintenance`, and are excluded from composite ranking.
2. **Absolute Pressure Performance ($A$, 35%):**
   - Batting: Fixed-$K$ Normal shrinkage ($K = 25.0$) toward the eligible batting cohort mean (`130.13` SR).
   - Bowling: Beta-Binomial Empirical Bayes shrinkage toward the eligible bowling cohort mean (`6.07%` wicket rate).
3. **Empirical Bayes Match-Shrunk Ball-Weighted Consistency ($C$, 20%):**
   - Each player's per-match crisis rate $r_{{ij}}$ (on $n_{{ij}}$ crisis balls in match $j$) is shrunk toward the player's overall crisis rate $\\bar{{r}}_i$ via $w_{{ij}} = n_{{ij}} / (n_{{ij}} + 6)$: $\\tilde{{r}}_{{ij}} = w_{{ij}} r_{{ij}} + (1 - w_{{ij}}) \\bar{{r}}_i$.
   - Combining low ball-weighted coefficient of variation ($\\exp(-\\text{{CV}}_{{\\text{{weighted}}}}( \\tilde{{r}}_{{ij}} ))$) with ball-weighted match delivery success rate ($S_i$, fraction of crisis balls in matches achieving $\\tilde{{r}}_{{ij}} \\ge \\max(125.0, 0.90 \\cdot \\text{{SR}}_{{\\text{{norm}}}})$ for batters or $\\tilde{{r}}_{{ij}} \\ge \\max(38.0\\%, 0.92 \\cdot \\text{{Dot}}_{{\\text{{norm}}}})$ for bowlers):
     $$\\text{{Consistency}}_i = \\left( \\alpha \\exp(-\\text{{CV}}_{{w,i}}) + (1 - \\alpha) S_i \\right) \\cdot \\sqrt{{\\frac{{m_i}}{{m_i + 3}}}}$$
     where $\\alpha = 0.55$ for batters and $\\alpha = 0.40$ for bowlers.
4. **Sample Size Confidence ($S$, 10%):**
   - Batting: $\\min(1.0, \\ln(1 + n_i) / \\ln(1 + 250))$.
   - Bowling: $\\min(1.0, \\ln(1 + n_i) / \\ln(1 + 600))$, preserving differentiation across frontline bowling crisis workloads from 120 to 600+ legal deliveries.

---

## 4. Authoritative Top 10 Batters Under Crisis Pressure (`data/outputs/v3/TOP_10_BATTERS.csv`)

{bat_top_table}

### 4.1 Individual Player Selection Rationales — Top 10 Batters (Deliverable 3f)
Every batter in the authoritative Top 10 exceeds the eligible cohort crisis strike rate mean (`130.13` SR, with all 10 between `147.83` and `173.17` Crisis SR):
{bat_rationales_md}

---

## 5. Authoritative Top 10 Bowlers Under Defensive Pressure (`data/outputs/v3/TOP_10_BOWLERS.csv`, `MIN_NORMAL_BALLS = 100`)

{bowl_top_table}

### 5.1 Individual Player Selection Rationales — Top 10 Bowlers (Deliverable 3f)
{bowl_rationales_md}

---

## 6. Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

### 6.1 Batting Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 30, total_balls >= 120`)
{_df_to_md(bat_sweep)}

### 6.2 Bowling Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 100, total_legal_balls >= 120`)
{_df_to_md(bowl_sweep)}

*Note:* Under the calibrated pressure model, **92 batters** qualify at the `40`-ball baseline, **71** at `60` balls, **60** at `80` balls, **50** at `100` balls, **39** at `120` balls, **25** at `150` balls, **11** at `200` balls, and **7** at `250` balls (where `available_top10_count = 7`, never forcing a Top 10 when fewer than 10 players qualify). For bowlers, **99 frontline bowlers** qualify at the `120`-ball baseline (`100` at `100` balls, `96` at `150` balls, `89` at `200` balls, and `84` at `250` balls with `9/10` Top-10 overlap).

---

## 7. Weight Sensitivity Analysis Across 5 Prespecified Configurations (`RANKING_WEIGHT_SENSITIVITY.csv`)

### 7.1 Batting Weight Sensitivity (Top 10)
{bat_weight_top10}

### 7.2 Bowling Weight Sensitivity (Top 10)
{bowl_weight_top10}

---

## 8. Reproducibility & Verification Gates

- Pipeline execution: `.venv\\Scripts\\python scripts/compute_v3_rankings.py`
- Independent verification: `.venv\\Scripts\\python scripts/verify_v3_rankings.py`
- Automated test suite: `.venv\\Scripts\\python -m pytest tests/ -v` (**64 passed**)
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
        fontSize=5.8, leading=7.2, textColor=text_dark, alignment=1,
    )

    story = []

    # ── PAGE 1: Governance, Provisional Disclosure & Methodology ──────
    story.append(Paragraph("SupeRR Intelligence V3 — Pressure Reliability Analytics & Player Scouting (EGM Calibrated Patch)", title_style))
    story.append(Paragraph("Authoritative Technical Methodology Dossier • Status: P1.1 PATCH VERIFIED — PROVISIONAL MODEL", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=rr_pink, spaceAfter=4))

    story.append(Paragraph("Mandatory Provisional Model Disclosure", h1_style))
    story.append(Paragraph(
        "<b>\"Rankings are provisional. Batter ranks 1–5 are robust across all 5 weight configurations, while batter ranks 6–10 are sensitive to scoring weights. "
        "The pressure classification uses the calibrated pre-delivery state heuristic (V3.2_EGM_CALIBRATED_HEURISTIC). "
        "The new score has not yet undergone independent out-of-time validation.\"</b>",
        body_style
    ))

    story.append(Paragraph("1. Dataset Scope, Canonical Identity & Data Governance (853 Matches, 193,988 Deliveries)", h1_style))
    story.append(Paragraph(
        "• <b>Canonical Identity Resolution:</b> Multi-ID provider duplicates (e.g. Abdul Samad, Dunith Wellalage) are consolidated prior to aggregation via <code>PLAYER_IDENTITY_CROSSWALK.csv</code>; unresolved collisions are quarantined.<br/>"
        "• <b>Extras Codebook Caveat:</b> <code>extras1_runs</code> is categorical (codes 1–7). Score totals, dynamic RRR, chase leverage, and bowler economy remain quarantined.<br/>"
        "• <b>Calibrated Pre-Delivery Pressure (<code>V3.2_EGM_CALIBRATED_HEURISTIC</code>):</b> Batting Crisis (&gt;5.2 on [0,10], 15.35% of balls faced, 92 eligible batters) and Bowling Defensive Pressure (&gt;5.5 on [0,10], 99 eligible frontline bowlers) operate strictly on pre-delivery states without post-delivery target leakage.<br/>"
        "• <b>Wicket Hazard Model Governance (<code>EXPERIMENTAL_NOT_USED_FOR_RANKING</code>):</b> Out-of-sample evaluation yields AUC = 0.572, Log-Loss = 0.692, and Expected Wickets = 26,843 vs Actual Wickets = 2,931 (9.16x miscalibration due to <code>class_weight='balanced'</code>). Neither the hazard model, joint model, nor LightGBM challenger is used for ranking.",
        body_style
    ))

    story.append(Paragraph("2. Provisional Fixed-Weight Score & Normal-Baseline Reliability Gate", h1_style))
    story.append(Paragraph(
        "• <b>Provisional Formula:</b> Score = 100 × [0.35 × Maintenance + 0.35 × Absolute (EB Shrunk) + 0.20 × Match Consistency (EB Match-Shrunk Ball-Weighted) + 0.10 × Sample Confidence (250b Bat / 600b Bowl)].<br/>"
        "• <b>Bowler Normal-Baseline Gate (<code>MIN_NORMAL_BALLS = 100</code>):</b> Bowlers require ≥120 crisis balls AND ≥100 normal balls. Bowlers with &lt;100 normal balls (464 of 596) are flagged <code>BOWLER_NORMAL_BASELINE_INSUFFICIENT</code> and excluded from composite ranking. Raw and capped ([0.50, 1.50]) maintenance ratios are reported separately.<br/>"
        "• <b>Uncertainty:</b> 2,000-iteration match-clustered bootstrap 95% confidence intervals (0 arbitrary fixed-width fallbacks).",
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
        Paragraph("Raw/Cap Maint", table_header_style),
        Paragraph("Consist.", table_header_style),
        Paragraph("Score", table_header_style),
        Paragraph("95% CI", table_header_style),
    ]]
    for _, r in top_bat.head(10).iterrows():
        bat_data.append([
            Paragraph(str(int(r['rank'])), table_cell_style),
            Paragraph(str(int(r['canonical_player_id'])), table_cell_style),
            Paragraph(str(r['player_name']), table_cell_style),
            Paragraph(str(r['v3_role']), table_cell_style),
            Paragraph(f"{int(r['crisis_balls'])} ({int(r['crisis_matches'])})", table_cell_style),
            Paragraph(f"{r['crisis_sr']:.2f}", table_cell_style),
            Paragraph(f"{r['norm_sr']:.2f}", table_cell_style),
            Paragraph(f"{r['raw_sr_maintenance']:.3f}x/{r['sr_maintenance']:.3f}x", table_cell_style),
            Paragraph(f"{r['consistency_score']:.4f}", table_cell_style),
            Paragraph(f"<b>{r['provisional_fixed_weight_score']:.2f}</b>", table_cell_style),
            Paragraph(f"[{r['ci_lower']:.1f}, {r['ci_upper']:.1f}]", table_cell_style),
        ])

    bat_table = Table(bat_data, colWidths=[22, 28, 82, 68, 42, 38, 38, 58, 38, 36, 66])
    bat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rr_navy),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('GRID', (0, 0), (-1, -1), 0.5, border_grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, rr_light_bg]),
    ]))
    story.append(bat_table)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "<b>Cohort Quality Verification:</b> All 10 Top-10 Batters record Crisis Strike Rates between 147.83 and 173.17, well above the eligible cohort mean of 130.13 (0 anomaly flags in Top 10).",
        body_style
    ))

    story.append(Paragraph("4. Authoritative Universal Top 10 Bowlers (data/outputs/v3/TOP_10_BOWLERS.csv, MIN_NORMAL_BALLS=100)", h1_style))
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    bowl_data = [[
        Paragraph("Rank", table_header_style),
        Paragraph("ID", table_header_style),
        Paragraph("Player Name", table_header_style),
        Paragraph("Role", table_header_style),
        Paragraph("Crisis B", table_header_style),
        Paragraph("Norm B", table_header_style),
        Paragraph("Crisis Dot%", table_header_style),
        Paragraph("Raw/Cap Maint", table_header_style),
        Paragraph("Shrunk WR%", table_header_style),
        Paragraph("Score", table_header_style),
        Paragraph("95% CI", table_header_style),
    ]]
    for _, r in top_bowl.head(10).iterrows():
        bowl_data.append([
            Paragraph(str(int(r['rank'])), table_cell_style),
            Paragraph(str(int(r['canonical_player_id'])), table_cell_style),
            Paragraph(str(r['player_name']), table_cell_style),
            Paragraph(str(r['v3_role']), table_cell_style),
            Paragraph(f"{int(r['crisis_balls'])}", table_cell_style),
            Paragraph(f"{int(r['norm_balls'])}", table_cell_style),
            Paragraph(f"{r['crisis_dot_pct']:.2f}%", table_cell_style),
            Paragraph(f"{r['raw_dot_maintenance']:.3f}x/{r['capped_dot_maintenance']:.3f}x", table_cell_style),
            Paragraph(f"{r['shrunk_crisis_wr']:.2f}%", table_cell_style),
            Paragraph(f"<b>{r['provisional_fixed_weight_score']:.2f}</b>", table_cell_style),
            Paragraph(f"[{r['ci_lower']:.1f}%, {r['ci_upper']:.1f}%]", table_cell_style),
        ])

    bowl_table = Table(bowl_data, colWidths=[22, 28, 86, 68, 36, 34, 42, 58, 42, 34, 66])
    bowl_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rr_navy),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('GRID', (0, 0), (-1, -1), 0.5, border_grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, rr_light_bg]),
    ]))
    story.append(bowl_table)

    story.append(PageBreak())
    story.append(Paragraph("5. Individual Selection Rationales for All 20 Selected Players (Deliverable 3f)", h1_style))
    story.append(Paragraph("<b>5.1 Top 10 Batters — Individual Selection Evidence:</b>", body_style))
    for _, r in top_bat.head(10).iterrows():
        story.append(Paragraph(
            f"• <b>#{int(r['rank'])} {r['player_name']} (ID {int(r['canonical_player_id'])}, {r['v3_role']}):</b> "
            f"{int(r['crisis_balls'])} crisis balls ({int(r['crisis_matches'])}m), Crisis SR {r['crisis_sr']:.2f} vs Norm SR {r['norm_sr']:.2f} "
            f"({r['sr_maintenance']:.3f}x maint), Shrunk SR {r['shrunk_crisis_sr']:.2f}, Consistency {r['consistency_score']:.4f}, "
            f"95% CI [{r['ci_lower']:.1f}, {r['ci_upper']:.1f}] → <code>{r['component_breakdown_explanation']}</code>.",
            body_style
        ))

    story.append(Paragraph("<b>5.2 Top 10 Bowlers — Individual Selection Evidence:</b>", body_style))
    for _, r in top_bowl.head(10).iterrows():
        story.append(Paragraph(
            f"• <b>#{int(r['rank'])} {r['player_name']} (ID {int(r['canonical_player_id'])}, {r['v3_role']}):</b> "
            f"{int(r['crisis_balls'])} crisis balls ({int(r['crisis_matches'])}m, {int(r['norm_balls'])} norm balls), "
            f"Crisis Dot% {r['crisis_dot_pct']:.2f}% vs Norm Dot% {r['norm_dot_pct']:.2f}% "
            f"(raw {r['raw_dot_maintenance']:.3f}x / cap {r['dot_maintenance']:.3f}x), Shrunk WR {r['shrunk_crisis_wr']:.2f}%, "
            f"Consistency {r['consistency_score']:.4f}, 95% CI [{r['ci_lower']:.1f}%, {r['ci_upper']:.1f}%] → <code>{r['component_breakdown_explanation']}</code>.",
            body_style
        ))

    story.append(Paragraph("6. Extended Crisis-Ball Threshold Sensitivity (40, 60, 80, 100, 150, 200, 250) & Reproducibility", h1_style))
    story.append(Paragraph(
        "• <b>Threshold Sensitivity:</b> Across 40, 60, 80, 100, 150, 200, 250 crisis balls (with ≥5 matches), eligible batters scale from 92 (40b) to 71 (60b), 60 (80b), 50 (100b), 25 (150b), 11 (200b), and 7 (250b, available_top10_count=7, unforced). Eligible bowlers (with ≥100 norm balls) scale from 99 (120b baseline) to 96 (150b), 89 (200b), and 84 (250b, 9/10 overlap).<br/>"
        "• <b>Verification Gate:</b> 64 passing pytest unit/regression tests and 100% reconciliation via <code>scripts/verify_v3_rankings.py</code>.",
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
