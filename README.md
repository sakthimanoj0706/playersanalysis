# SupeRR Intelligence V4 👑
### Rajasthan Royals SupeRR Selector Season 2 — Unified Calibrated-Ridge Pressure Intelligence & Auction Decision Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/pytest-65%20passed-success.svg)](tests/)
[![Dataset](https://img.shields.io/badge/data-IPL%20%2B%20T20I%20(2022--2026)-magenta.svg)](data/)
[![Ranking Status](https://img.shields.io/badge/status-V4%20CALIBRATED%20RIDGE%20%E2%80%94%20UNIFIED%20RUN%20VALUE%20VERIFIED-brightgreen.svg)](data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json)

**SupeRR Intelligence V4** is an audited, reproducible cricket analytics and decision-support platform engineered for the Rajasthan Royals (RR) SupeRR Selector Season 2 Hackathon. The platform delivers two independent, synchronized analytical systems backed by a comprehensive methodology dossier ([`FINAL_SUPERR_METHODOLOGY_REPORT.md`](FINAL_SUPERR_METHODOLOGY_REPORT.md) / [`FINAL_SUPERR_METHODOLOGY_REPORT.pdf`](FINAL_SUPERR_METHODOLOGY_REPORT.pdf)):

1. **System A — Universal Cricket Intelligence (`V4_CALIBRATED_RIDGE`):** Context-benchmarked evaluation across **853 matches** (193,988 regular deliveries + 26 super-over deliveries separated; IPL & T20I 2022–2026) with canonical identity resolution (`PLAYER_IDENTITY_CROSSWALK.csv`), 5-state mutually exclusive role gating (`0` leaderboard overlap), **pure ex-ante DLS-aware within-phase pressure stratification** (Top 30% High / 50–70% Moderate / Bottom 50% Normal per `(innings, innings_phase)`), **Competition-Tier weighting** (`T1_IPL=1.0, T1_FM_T20I=1.0, T2_MIXED=0.5, T3_ASSOC=0.2`, strict `tier1_share >= 0.60`), **Unified Run-Value Ridge opponent & match-par regression** (`lsqr`, `damp=12.0`), **Value-Gated Downside Match Consistency**, invariant `30% / 35% / 25% / 10%` PRI scoring, and **2,000-iteration match-clustered Run-Value bootstrap CIs**.
2. **System B — Rajasthan Royals Team Intelligence & 2027 Auction Strategy:** Squad-first audit of RR's 16-match 2026 IPL campaign (`3,788` balls, 3rd-place finish), diagnosing 4 quantified tactical deficiencies (`RR_REQUIRED_ROLES.csv`), explicit **retention / release & overseas slot arithmetic** (`RR_RETENTION_SCENARIOS.csv`, `RR_AUCTION_BUDGET_SCENARIOS.csv`), and an auction target evaluation matrix (`RR_PLAYER_FIT.csv`) **dynamically synchronized** with System A's V4 ranks.

> **Mandatory V4 Model Governance Disclosure (`RANKING_SOURCE_OF_TRUTH.json`):**
> "Rankings use V4 Calibrated Ridge state-conditional run values with Tier-1 weighting and within-phase quantile tiers. Batter ranks sensitive to scoring weights: #7; Bowler ranks sensitive to scoring weights: #7." (`9/10` batters and `9/10` bowlers are `ROBUST_ACROSS_WEIGHTS`).

---

## 🏆 Universal Top 10 Leaderboards Under Pressure (System A — Canonical Source of Truth)

All ranking tables below are generated directly from the authoritative CSVs (`data/outputs/v3/TOP_10_BATTERS.csv` and `data/outputs/v3/TOP_10_BOWLERS.csv`) registered in `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`. All 14 downstream copies are synchronized byte-for-byte via SHA-256 verification in `scripts/verify_v3_rankings.py`.

### 🏏 Universal Top 10 Batters (Gated: `BAT_SPECIALIST` & `BAT_PRIMARY_AR`)
*Eligibility (`156` qualified batters): `eff_crisis_balls >= 60`, `crisis_matches >= 6`, `eff_norm_balls >= 60`, `total_balls >= 200`, and `tier1_share >= 0.60`. Unified currency: Batting Run Value per 100 balls (`crisis_r_bat`, `V_WKT = 4.0 / 3.5 / 2.5` by phase) with Ridge opponent/match-par adjustment (`crisis_delta_rv`, dual-arm prior `k=90`, invariant PRI weights `30% Maint / 35% Abs / 25% Cons / 10% Sample`). 95% CIs reflect `CRISIS_RUN_VALUE_PER_100` via 2,000 match-clustered bootstrap iterations.*

| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls (Matches) | Tier-1 Share | Crisis SR | Normal SR ($\ge 60$b) | Crisis Run Val /100 (`crisis_delta_rv`) | DiD Maint | Match Consistency | V4 PRI Score | 95% Match-Cluster CI (RV/100) | Weight Sensitivity |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `3125` | **Nicholas Pooran** | `BAT_SPECIALIST` | 565 (64) | 1.000 | 155.93 | 171.94 | +40.53 (+34.96) | +23.96 | 0.2763 | **96.95** | [19.56, 59.84] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `6423` | **Riyan Parag** | `BAT_PRIMARY_AR` | 281 (34) | 1.000 | 158.36 | 157.70 | +40.67 (+30.81) | +26.74 | 0.2896 | **96.51** | [11.99, 65.44] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `4260` | **Heinrich Klaasen** | `BAT_SPECIALIST` | 437 (41) | 1.000 | 146.91 | 189.58 | +41.23 (+34.19) | +20.16 | 0.3602 | **94.94** | [25.17, 54.85] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `8101` | **Ashutosh Sharma** | `BAT_SPECIALIST` | 197 (17) | 1.000 | 162.44 | 163.64 | +44.39 (+30.47) | +30.24 | 0.2494 | **93.66** | [6.72, 74.91] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `6396` | **Tim David** | `BAT_SPECIALIST` | 432 (49) | 0.983 | 153.70 | 196.39 | +46.08 (+38.13) | +24.03 | 0.2208 | **93.07** | [18.95, 68.80] | `ROBUST_ACROSS_WEIGHTS` |
| **6** | `1318` | **Andre Russell** | `BAT_PRIMARY_AR` | 344 (38) | 1.000 | 160.17 | 202.36 | +44.97 (+35.64) | +23.71 | 0.2097 | **92.06** | [18.01, 67.68] | `ROBUST_ACROSS_WEIGHTS` |
| **7** | `6819` | **Yashasvi Jaiswal** | `BAT_SPECIALIST` | 118 (23) | 1.000 | 204.24 | 149.01 | +70.88 (+40.21) | +33.91 | 0.1693 | **89.85** | [25.18, 110.51] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **8** | `2756` | **Shashank Singh** | `BAT_PRIMARY_AR` | 260 (26) | 1.000 | 150.77 | 187.78 | +35.78 (+26.58) | +19.14 | 0.2816 | **88.65** | [8.29, 58.72] | `ROBUST_ACROSS_WEIGHTS` |
| **9** | `7897` | **Tilak Varma** | `BAT_PRIMARY_AR` | 727 (78) | 0.991 | 138.10 | 150.53 | +27.97 (+24.87) | +19.31 | 0.2579 | **86.52** | [13.58, 42.22] | `ROBUST_ACROSS_WEIGHTS` |
| **10** | `1077` | **David Miller** | `BAT_SPECIALIST` | 452 (44) | 1.000 | 151.55 | 158.13 | +30.50 (+25.43) | +20.59 | 0.2408 | **86.45** | [8.03, 47.36] | `ROBUST_ACROSS_WEIGHTS` |

- **Cohort & Stability Highlights:** Eligible cohort mean Crisis SR is **131.04**; all Top-10 batters clear the cohort mean (`0` anomaly flags), all 10 have `>= 98%` Tier-1 competition share, and **9/10** remain `ROBUST_ACROSS_WEIGHTS` across all 5 weight configurations (`#7 Yashasvi Jaiswal` is sensitivity-flagged).

---

### 🎯 Universal Top 10 Bowlers (Gated: `BOWL_SPECIALIST` & `BOWL_PRIMARY_AR`)
*Eligibility (`122` qualified bowlers): `eff_crisis_balls >= 120`, `crisis_matches >= 6`, `eff_norm_balls >= 100` (strict `VALID_NORMAL_BASELINE`), `total_legal_balls >= 250`, and `tier1_share >= 0.60`. Unified currency: Bowling Runs Saved per Over (`crisis_r_rv`, incorporating wide/no-ball penalty runs + `V_WKT_BOWL = 5.5 / 5.0 / 3.5` by phase) with Ridge opponent/match-par adjustment (`crisis_delta_rv`, dual-arm prior `k=150`, Beta-Binomial wicket shrinkage `k=100`, invariant PRI weights `30% / 35% / 25% / 10%`). 95% CIs reflect `CRISIS_RUNS_SAVED_PER_OVER`.*

| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls (Matches) | Normal Balls | Tier-1 Share | Crisis Econ / Dot % | Runs Saved/Ov (`crisis_delta_rv`) | DiD Maint | Consistency | V4 PRI Score | 95% Match-Cluster CI (RS/Ov) | Weight Sensitivity |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `781` | **Sunil Narine** | `BOWL_PRIMARY_AR` | 563 (40) | 653 | 1.000 | 7.35 / 36.94% | +2.35 (+1.86) | +1.13 | 0.4168 | **95.78** | [1.36, 3.39] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `4722` | **Rashid Khan** | `BOWL_PRIMARY_AR` | 825 (64) | 1,481 | 0.983 | 7.94 / 31.88% | +1.57 (+1.33) | +1.04 | 0.3077 | **87.36** | [0.66, 2.51] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `305` | **R Ashwin** | `BOWL_PRIMARY_AR` | 505 (38) | 613 | 1.000 | 7.91 / 30.50% | +1.44 (+1.11) | +0.99 | 0.3291 | **85.03** | [0.40, 2.52] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `2933` | **Jasprit Bumrah** | `BOWL_SPECIALIST` | 570 (48) | 916 | 0.990 | 7.91 / 37.72% | +1.74 (+1.38) | +0.71 | 0.3167 | **84.71** | [0.60, 2.92] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `4900` | **Wanindu Hasaranga** | `BOWL_PRIMARY_AR` | 580 (43) | 1,117 | 0.988 | 8.08 / 32.59% | +1.53 (+1.22) | +0.88 | 0.2968 | **83.60** | [0.50, 2.59] | `ROBUST_ACROSS_WEIGHTS` |
| **6** | `2687` | **Roston Chase** | `BOWL_PRIMARY_AR` | 171 (17) | 494 | 1.000 | 7.96 / 33.33% | +2.25 (+1.20) | +1.14 | 0.2665 | **82.71** | [-0.16, 4.51] | `ROBUST_ACROSS_WEIGHTS` |
| **7** | `722` | **Liam Dawson** | `BOWL_SPECIALIST` | 123 (14) | 221 | 1.000 | 7.41 / 36.59% | +2.15 (+0.97) | +0.85 | 0.3142 | **78.76** | [-0.13, 4.92] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **8** | `19316` | **Maheesh Theekshana** | `BOWL_SPECIALIST` | 576 (51) | 1,398 | 0.989 | 8.22 / 32.29% | +1.19 (+0.95) | +0.82 | 0.2804 | **78.76** | [0.25, 2.10] | `ROBUST_ACROSS_WEIGHTS` |
| **9** | `7920` | **Nathan Ellis** | `BOWL_SPECIALIST` | 343 (32) | 433 | 1.000 | 8.71 / 34.11% | +1.61 (+1.12) | +0.81 | 0.2573 | **78.66** | [0.33, 3.05] | `ROBUST_ACROSS_WEIGHTS` |
| **10** | `2315` | **Reece Topley** | `BOWL_SPECIALIST` | 231 (20) | 330 | 1.000 | 8.42 / 42.86% | +1.44 (+0.87) | +0.87 | 0.3075 | **78.38** | [-0.08, 3.28] | `ROBUST_ACROSS_WEIGHTS` |

- **Role & Quality Confirmation:** **354** bat-gated and **327** bowl-gated players have `0` overlap (**Intersection between Batting and Bowling Top 10 is 0**). All 10 bowlers satisfy strict `VALID_NORMAL_BASELINE` (`>= 100` normal balls), `>= 98%` Tier-1 share, positive `crisis_delta_rv`, and crisis-ball share `<= 55%` (preventing phase-skewed relabeling). **9/10** remain `ROBUST_ACROSS_WEIGHTS` (`#7 Liam Dawson` is sensitivity-flagged).

---

## 📊 Extended Crisis-Ball Threshold Sensitivity (`40..750`, `648` Grid Combinations)

Full multi-dimensional sensitivity results (`648` combinations across crisis balls, crisis matches `5..10`, normal balls, and total deliveries) are stored in `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`. Primary crisis-ball sweeps (`crisis_matches >= 6`, `tier1_share >= 0.60`, bat `norm>=60, total>=200`, bowl `norm>=100, total>=250`):

| Crisis Ball Cutoff | Eligible Batters | Avail. Bat Top-10 | Bat Overlap vs Baseline (`60`b) | Bat Jaccard | Bat Mean / Max Shift | Eligible Bowlers | Avail. Bowl Top-10 | Bowl Overlap vs Baseline (`120`b) | Bowl Jaccard | Bowl Mean / Max Shift |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **40** | 169 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 | 164 | 10 | 7 / 10 | 0.5385 | 1.0 / 3 |
| **60** *(Bat Baseline)* | **156** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 | 163 | 10 | 7 / 10 | 0.5385 | 1.0 / 3 |
| **80** | 141 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 | 149 | 10 | 7 / 10 | 0.5385 | 1.0 / 3 |
| **100** | 125 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 | 137 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **120** *(Bowl Baseline)* | — | — | — | — | — | **122** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 |
| **150** | 95 | 10 | 9 / 10 | 0.8182 | 0.4 / 1 | 101 | 10 | 9 / 10 | 0.8182 | 0.4 / 1 |
| **200** | 71 | 10 | 8 / 10 | 0.6667 | 1.3 / 3 | 77 | 10 | 8 / 10 | 0.6667 | 1.0 / 2 |
| **250** | 45 | 10 | 8 / 10 | 0.6667 | 1.3 / 3 | 62 | 10 | 7 / 10 | 0.5385 | 1.3 / 3 |
| **500** | 4 | 4 *(not forced)* | 2 / 10 | 0.1667 | 13.5 / 37 | 20 | 10 | 6 / 10 | 0.4286 | 3.3 / 11 |
| **750** | 0 | 0 | 0 / 10 | 0.0000 | 0.0 / 0 | 4 | 4 *(not forced)* | 1 / 10 | 0.0769 | 16.75 / 37 |

- **Stability Proof:** Across `40–100` crisis balls, the Batting Top 10 exhibits **10/10 overlap (Jaccard 1.00)** and retains **8/10 overlap** all the way through `250` crisis balls. When ultra-high cutoffs (`500` bat / `750` bowl) drop qualified pools below 10 (`4` eligible), the pipeline degrades gracefully (`available_top10_count = 4`) without ever forcing a Top-10.

---

## 🏰 Rajasthan Royals 2026 Empirical Audit & 2027 Auction Strategy (System B)

All **16 matches** (14 league games + Eliminator win + Qualifier 2 loss) and **3,788 deliveries** played by RR in IPL 2026 were reconciled (`Adam Milne` 16 squad sheets / 1 match played; `Dhruv Jurel` partner run-out attribution fixed to **36.79** average):

- **Core Performers:** **Vaibhav Sooryavanshi** (776 runs, 327b, SR 237.31, 72 sixes), **Dhruv Jurel** (515 runs, SR 154.65, avg 36.79), **Yashasvi Jaiswal** (427 runs, SR 152.50, #7 Universal V4 Batter), **Donovan Ferreira** (317 runs, SR 179.10), **Riyan Parag** (309 runs, #2 Universal V4 Batter), **Ravindra Jadeja** (266 runs, avg 66.50), **Jofra Archer** (60.0 overs, 25 bowler-creditable wickets).
- **Primary Squad Gaps (`RR_REQUIRED_ROLES.csv`):**
  1. **CRITICAL:** Indian Frontline Pacer (Powerplay/Death depth alongside Archer — e.g. `Prasidh Krishna`, `Avesh Khan`)
  2. **CRITICAL:** Overseas Death-Over Specialist (`Matheesha Pathirana` V4 #25 / `Nuwan Thushara` V4 #30)
  3. **IMPORTANT:** Economical Middle-Over Spinner complementing Bishnoi & Jadeja (`R Sai Kishore` V4 #60 / `Akeal Hosein` V4 #46)
  4. **IMPORTANT:** Domestic Lower-Order Finisher (`Ashutosh Sharma` V4 #4 — 93.66 score, replacing Hetmyer and freeing an overseas slot)

> **Auction Purse, Retention & Overseas Slot Disclosure (`USER_PROVIDED_UNVERIFIED`):**
> Contract values and Goa 2027 auction cap scenarios (`data/outputs/v3/RR_RETENTION_SCENARIOS.csv`, `RR_AUCTION_BUDGET_SCENARIOS.csv`) reflect user problem-brief scenario inputs: releasing Hetmyer (11.00 Cr, OS), Deshpande (6.50 Cr), Sandeep Sharma (4.00 Cr), Adam Milne (2.40 Cr, OS), Kuldeep Sen (0.75 Cr), and Lhuan-dre Pretorius (0.30 Cr, OS) frees **₹24.95 Cr** for a **₹27.60 Cr** base auction purse (+₹2.65 Cr carry-over). Core retentions hold **3 confirmed overseas players** (`Jofra Archer`, `Donovan Ferreira`, `Nandre Burger`) plus **1 `CONFLICTING_STATUS` contract** (`Sam Curran vs Dasun Shanaka`), leaving **4–5 squad overseas slots** and **1 Playing-XI overseas slot** open for a frontline overseas death bowler (`Matheesha Pathirana` / `Nuwan Thushara`). All System A ranks/blurbs in `RR_PLAYER_FIT.csv` are dynamically synchronized from `ALL_BATTER_METRICS.csv` and `ALL_BOWLER_METRICS.csv`.

---

## 🔬 Mathematical Models, Governance & Limitations Matrix

| Component | Implementation | Validation / Method | Audited Status & Notes | Governance Status | Used in Final Ranking? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **1. Innings & Pressure Engine** | `src/context_engine/innings_context.py`, `src/pressure_engine/v3_pressure_model.py` | Pure Ex-Ante + DLS + Within-Phase Quantiles | Zero post-delivery leakage; DLS-adjusted `legal_balls_remaining` & `clean_rrr_deficit`; Top 30% High / 50–70% Mod / Bottom 50% Normal per `(innings, phase)` | **`V4_CALIBRATED_RIDGE`** | **Yes (Pressure Tiers)** |
| **2. Competition & Ridge Baseline** | `scripts/compute_v3_rankings.py` | Sparse Weighted Ridge (`lsqr`, `damp=12.0`) | Tier weights `(1.0, 1.0, 0.5, 0.2)`; state-conditional `(comp_tier, innings, phase, wkt_bucket)` + opponent & match-par controls | **`V4_CALIBRATED_RIDGE`** | **Yes (Expected Baselines)** |
| **3. Role Classifier** | `src/classification/v3_role_classifier.py` | Multi-Season Workload | 354 bat-gated, 327 bowl-gated; 0 overlap between leaderboards | **`CANONICAL_ROLE_GATING_ACTIVE`** | **Yes (Eligibility Gate)** |
| **4. Unified RV Scoring (`PRI`)** | `scripts/compute_v3_rankings.py`, `src/ranking_engine/pressure_rankings.py` | Invariant `30/35/25/10` + 648 Threshold & 5 Weight Checks | Dual-arm Ridge shrinkage, Value-Gated Downside Consistency, strict normal baseline & `tier1_share >= 0.60` | **`V4_CALIBRATED_RIDGE_SCORE`** | **Yes (Primary Score)** |
| **5. Uncertainty Bootstrap** | `src/reliability/v3_reliability.py` | 2,000-Iter Match-Cluster Bootstrap | Direct Run-Value 95% CIs (`bat_rv100`, `bowl_rv` incl. extra-ball penalties); 0 fallback bounds | **`VERIFIED_CLUSTER_BOOTSTRAP`** | **Yes (CIs & Shrinkage)** |
| **6. Diagnostic Challengers** | `src/models/v3_wicket_hazard.py`, `v3_joint_performance.py`, `v3_lightgbm_challenger.py`, `v3_tail_risk.py` | Chronological Split / Quantile Diagnostics | Wicket Hazard AUC `0.572` (9.16x uncalibrated baseline); retained strictly for exploratory research | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |

---

## 🚀 Reproducible Execution & Verification

### 1. Recompute Authoritative V4 Rankings, System B Sync & Manifest
```powershell
.\.venv\Scripts\python.exe scripts/compute_v3_rankings.py
```

### 2. Regenerate Markdown & PDF Reports
```powershell
.\.venv\Scripts\python.exe src/reporting/report_generator.py
```

### 3. Run Independent Verification Gate (`verify_v3_rankings.py`)
```powershell
.\.venv\Scripts\python.exe scripts/verify_v3_rankings.py
```

### 4. Run Automated Test Suite (`65 passed`)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### 5. Launch Interactive Executive Dashboard
```powershell
.\.venv\Scripts\streamlit.exe run dashboard/app.py
```
App URL: `http://localhost:8501`
