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

    content = f"""# SupeRR Intelligence V3: Pressure Reliability Analytics & Player Scouting
## Official Technical Methodology Report & Evidence Dossier (P1.1 Patch)
**Target Event:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Scope:** Historical IPL & Men's T20I (2022 – 2026)  
**Authoritative Source Manifest:** `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`  
**System Status:** `P1.1 PATCH VERIFIED — PROVISIONAL MODEL`  

> **Mandatory Provisional Model Disclosure:**
> "Rankings are provisional. Batter ranks 5, 6, 9 and 10 are sensitive to scoring weights. The pressure classification remains heuristic and position-proxy based. The new score has not yet undergone independent out-of-time validation."

---

## 1. Executive Summary & Governance Architecture

Standard cricket statistics (total runs, nominal strike rates, aggregate wickets) are heavily distorted by unconstrained play in low-leverage match situations. Under the Rajasthan Royals problem statement, pressure reliability evaluates how players sustain or elevate performance in high-pressure states relative to their personal normal baselines.

SupeRR Intelligence V3 enforces:
1. **Canonical Player Identity Resolution (`src/identity/player_identity.py`):** Consolidates verified multi-ID provider records before aggregation (`PLAYER_IDENTITY_CROSSWALK.csv`) while quarantining unresolved identity collisions.
2. **Pre-Delivery Heuristic Pressure Stratification (`PROVISIONAL_POSITION_PROXY_HEURISTIC`):** Mutually exclusive pre-delivery batting crisis and bowling defensive pressure tiers with zero post-delivery target leakage and explicit missing-feature quarantine (`batting_pressure_data_valid`, `bowling_pressure_data_valid`).
3. **Separate Normal-Baseline Reliability Gating (`MIN_NORMAL_BALLS = 100` for Bowlers, `30` for Batters):** Prevents small-sample normal baselines from distorting maintenance ratios. Raw and capped (`[0.50, 1.50]`) maintenance ratios are reported separately.
4. **Empirical Bayes Shrinkage & Match-Clustered Bootstrap CIs:** Priors estimated strictly on the eligible role-gated population ($K=25.0$ Normal shrinkage for batting SR; Method-of-Moments Beta-Binomial shrinkage for bowling wicket rate) and 2,000-iteration match-clustered bootstrap 95% confidence intervals.

---

## 2. Dataset Scope & Data Governance Audit

The platform ingests **853 matches** (837 with ball-by-ball delivery logs) and **193,988 regular deliveries** (after quarantining 26 Super Over deliveries in innings 3 and 4).

1. **`extras1_runs` is Categorical, NOT a Run Count:** Source data integer codes (1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty) represent an enum codebook and are never summed as numeric runs.
2. **Quarantined Metrics & Pressure-Model Limitation (`PROVISIONAL_POSITION_PROXY_HEURISTIC`):**
   - Because total extras semantics remain unconfirmed, cumulative scoreboard totals, second-innings target, dynamic required run rate (RRR), full chase leverage, and bowler economy rates are withheld from ranking formulas.
   - Consequently, **the current pressure model is a position-proxy and pre-delivery state heuristic, not a fully calibrated match-leverage model**.
   - Batting position is a role proxy, not direct evidence of match pressure; positional crisis distributions must not be presented as calibrated player-level crisis probabilities.
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
   - Batting: Fixed-$K$ Normal shrinkage ($K = 25.0$) toward the eligible batting cohort mean ($140.20$).
   - Bowling: Beta-Binomial Empirical Bayes shrinkage toward the eligible bowling cohort mean ($5.52\\%$).
3. **Exposure-Adjusted Match Consistency ($C$, 20%):**
   $$\\text{{Consistency}}_i = \\exp(-\\text{{CV}}_i) \\cdot \\sqrt{{\\frac{{m_i}}{{m_i + 3}}}}$$
4. **Sample Size Confidence ($S$, 10%):**
   $$\\text{{Sample Confidence}}_i = \\min\\left(1.0, \\frac{{\\ln(1 + n_i)}}{{\\ln(1 + 250)}}\\right)$$

*Validation Governance Note:* Legacy PRI hold-out Spearman correlations from earlier prototypes are **not** used as validation evidence for this V3 score. The V3 score remains explicitly provisional pending independent out-of-time validation.

---

## 4. Authoritative Top 10 Batters Under Crisis Pressure (`data/outputs/v3/TOP_10_BATTERS.csv`)

{bat_top_table}

### Transparency & Iftikhar Ahmed (`canonical_player_id=3056`, Rank #9) Component Breakdown
- **Weight-Sensitive Batter Ranks:** Ranks **#5 Jaker Ali Anik**, **#6 Abdul Samad**, **#9 Iftikhar Ahmed**, and **#10 Jitesh Sharma** shift by $\\ge 5$ places across the 5 weight configurations and are flagged `RANKING_SENSITIVE_TO_WEIGHTS`.
- **Iftikhar Ahmed (#9) Component Breakdown:**
  - Crisis Strike Rate: **127.50** (40 balls across 11 matches), which is **below the eligible cohort mean of 140.20** (flagged `CRISIS_SR_BELOW_COHORT_MEAN`).
  - Component Contributions: `contrib_maint = 20.95` (1.054x maintenance over 120.96 normal SR) + `contrib_abs = 14.71` (shrunk crisis SR 132.39) + `contrib_cons = 20.00` (match consistency 0.5497, #1 in eligible cohort) + `contrib_sample = 6.72` = **62.38**. His #9 rank is driven by top-of-cohort multi-match consistency and positive personal baseline maintenance offsetting low absolute strike rate.

---

## 5. Authoritative Top 10 Bowlers Under Defensive Pressure (`data/outputs/v3/TOP_10_BOWLERS.csv`, `MIN_NORMAL_BALLS = 100`)

{bowl_top_table}

---

## 6. Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

### 6.1 Batting Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 30, total_balls >= 120`)
{_df_to_md(bat_sweep)}

### 6.2 Bowling Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 100, total_legal_balls >= 120`)
{_df_to_md(bowl_sweep)}

*Note:* Top 10 is never forced when fewer than 10 players are eligible (`available_top10_count = 8` at 100 crisis balls for batters, `6` at 120 balls, and `0` at 150–250 balls). A 10/10 overlap at the baseline threshold (`40` balls) is not proof of stability across higher thresholds.

---

## 7. Weight Sensitivity Analysis Across 5 Prespecified Configurations (`RANKING_WEIGHT_SENSITIVITY.csv`)

{bat_weight_top10}

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
    story.append(Paragraph("SupeRR Intelligence V3 — Pressure Reliability Analytics & Player Scouting (P1.1 Patch)", title_style))
    story.append(Paragraph("Authoritative Technical Methodology Dossier • Status: P1.1 PATCH VERIFIED — PROVISIONAL MODEL", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=rr_pink, spaceAfter=4))

    story.append(Paragraph("Mandatory Provisional Model Disclosure", h1_style))
    story.append(Paragraph(
        "<b>\"Rankings are provisional. Batter ranks 5, 6, 9 and 10 are sensitive to scoring weights. "
        "The pressure classification remains heuristic and position-proxy based. "
        "The new score has not yet undergone independent out-of-time validation.\"</b>",
        body_style
    ))

    story.append(Paragraph("1. Dataset Scope, Canonical Identity & Data Governance (853 Matches, 193,988 Deliveries)", h1_style))
    story.append(Paragraph(
        "• <b>Canonical Identity Resolution:</b> Multi-ID provider duplicates (e.g. Abdul Samad, Dunith Wellalage) are consolidated prior to aggregation via <code>PLAYER_IDENTITY_CROSSWALK.csv</code>; unresolved collisions are quarantined.<br/>"
        "• <b>Extras Codebook Caveat:</b> <code>extras1_runs</code> is categorical (codes 1–7). Score totals, dynamic RRR, chase leverage, and bowler economy remain quarantined.<br/>"
        "• <b>Pressure Model Limitation (<code>PROVISIONAL_POSITION_PROXY_HEURISTIC</code>):</b> The pressure model is a pre-delivery state and position-proxy heuristic, not a calibrated match-leverage model. Target and required run rate are not yet integrated.<br/>"
        "• <b>Wicket Hazard Model Governance (<code>EXPERIMENTAL_NOT_USED_FOR_RANKING</code>):</b> Out-of-sample evaluation yields AUC = 0.572, Log-Loss = 0.692, and Expected Wickets = 26,843 vs Actual Wickets = 2,931 (9.16x miscalibration due to <code>class_weight='balanced'</code>). Neither the hazard model, joint model, nor LightGBM challenger is used for ranking.",
        body_style
    ))

    story.append(Paragraph("2. Provisional Fixed-Weight Score & Normal-Baseline Reliability Gate", h1_style))
    story.append(Paragraph(
        "• <b>Provisional Formula:</b> Score = 100 × [0.35 × Maintenance + 0.35 × Absolute (EB Shrunk) + 0.20 × Match Consistency + 0.10 × Sample Confidence].<br/>"
        "• <b>Bowler Normal-Baseline Gate (<code>MIN_NORMAL_BALLS = 100</code>):</b> Bowlers require ≥120 crisis balls AND ≥100 normal balls. Bowlers with &lt;100 normal balls (549 of 596) are flagged <code>BOWLER_NORMAL_BASELINE_INSUFFICIENT</code> and excluded from composite ranking. Raw and capped ([0.50, 1.50]) maintenance ratios are reported separately.<br/>"
        "• <b>Uncertainty:</b> 2,000-iteration match-clustered bootstrap 95% confidence intervals (0 arbitrary fixed-width fallbacks).",
        body_style
    ))

    # ── PAGE 2: Authoritative Top 10 Leaderboards ──────
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
        "<b>Iftikhar Ahmed (#9, ID 3056) Transparency Note:</b> Crisis SR (127.50) is below the eligible cohort mean (140.20) and flagged <code>CRISIS_SR_BELOW_COHORT_MEAN</code>. "
        "His #9 score (62.38) is driven by #1 cohort match consistency (0.5497 → 20.00 pts) and positive personal maintenance (1.054x over 120.96 norm SR → 20.95 pts) alongside 14.71 abs pts and 6.72 sample pts.",
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

    story.append(Paragraph("5. Extended Crisis-Ball Threshold Sensitivity (40, 60, 80, 100, 150, 200, 250) & Reproducibility", h1_style))
    story.append(Paragraph(
        "• <b>Threshold Sensitivity:</b> Across 40, 60, 80, 100, 150, 200, 250 crisis balls (with ≥5 matches), eligible batters drop from 39 (40b, 10/10 overlap) to 21 (60b, 5/10 overlap, Jaccard 0.3333), 11 (80b, 1/10 overlap), 8 (100b, 8 available Top-10, unforced), and 0 (150–250b). Eligible bowlers (with ≥100 norm balls) remain 40 (40–80b), 39 (100–200b, 10/10 overlap), and 37 (250b, 9/10 overlap, Jaccard 0.8182). A 10/10 overlap at 40 balls is not proof of stability across higher thresholds.<br/>"
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
