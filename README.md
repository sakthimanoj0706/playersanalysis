# SupeRR Intelligence V3 👑
### Rajasthan Royals SupeRR Selector Season 2 — Joint Performance, Pressure Intelligence & Player-Fit Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/pytest-65%20passed-success.svg)](tests/)
[![Dataset](https://img.shields.io/badge/data-IPL%20%2B%20T20I%20(2022--2026)-magenta.svg)](data/)
[![Ranking Status](https://img.shields.io/badge/status-V3.3%20GOLDFISH%20TRIZ%20VERIFIED%20%E2%80%94%20PROVISIONAL%20MODEL-orange.svg)](data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json)

**SupeRR Intelligence V3** is an audited, reproducible cricket analytics and decision-support platform engineered for the Rajasthan Royals (RR) SupeRR Selector Season 2 Hackathon. The platform delivers two independent, decoupled analytical systems:

1. **System A — Universal Cricket Intelligence:** Context-benchmarked performance evaluation across 837 matches (IPL & T20I 2022–2026, 193,988 regular deliveries) with canonical player identity resolution (`PLAYER_IDENTITY_CROSSWALK.csv`), 5-state mutually exclusive role gating, cohort-calibrated Empirical Bayes DiD (`V3ReliabilityEngine`), prior-anchored specialist weighting, and 2,000-iteration match-clustered bootstrap confidence intervals.
2. **System B — Rajasthan Royals Team Intelligence:** Squad-first empirical analysis of RR's 16-match 2026 IPL campaign (3,788 balls, 3rd place overall finish), identifying 4 verified tactical deficiencies and evaluating 13 watchlist candidates under constraint-aware multi-criteria optimization.

> **Mandatory Provisional Model Disclosure:**
> "Rankings are provisional. Batter ranks sensitive to scoring weights: #2, #3, #6, #7, #8; Bowler ranks sensitive to scoring weights: #4, #6, #8, #9, #10. The pressure classification uses the calibrated pre-delivery state & clean-channel chase-leverage heuristic (`V3.3_GOLDFISH_CHASE_LEVERAGE`). The new score has not yet undergone independent out-of-time validation."

---

## 🏆 Universal Top 10 Leaderboards Under Pressure (System A — Canonical Source of Truth)

All ranking tables below are generated directly from the single authoritative source-of-truth CSVs (`data/outputs/v3/TOP_10_BATTERS.csv` and `data/outputs/v3/TOP_10_BOWLERS.csv`) registered in `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`. All downstream copies (`FINAL_TOP_10_*.csv`, `data/outputs/top_10_*.csv`) are synchronized byte-for-byte with these canonical files and verified by `scripts/verify_v3_rankings.py`.

### 🏏 Universal Top 10 Batters (Gated: `BAT_SPECIALIST` & `BAT_PRIMARY_AR`)
*Eligibility: $\ge 60$ crisis balls, $\ge 120$ total balls, $\ge 5$ crisis matches, $\ge 60$ normal baseline balls (65 eligible frontline batters). Scoring uses phase-adjusted, dismissal-weighted (`lambda_wkt = 6.0`) cohort-calibrated Empirical Bayes DiD (`did_bat_maintenance`) with 2.5%/97.5% winsorized z-score normalization. Confidence intervals: 2,000-iteration match-clustered bootstrap (95% percentile).*

| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls (Matches) | Crisis SR | Normal SR ($\ge 60$b) | Raw / Capped Maint. (Capped?) | Shrunk Crisis SR | Match Consistency | Provisional Score (`PRI`) | 95% Match-Cluster CI | Weight Sensitivity & Flags |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `3647` | **Shreyas Iyer** | `BAT_SPECIALIST` | 89 (34) | 166.29 | 152.50 | 1.090x / 1.090x (No) | 158.79 | 0.5124 | **78.55** | [141.03, 197.34] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `4708` | **Rinku Singh** | `BAT_SPECIALIST` | 365 (67) | 160.82 | 161.19 | 0.998x / 0.998x (No) | 158.98 | 0.3910 | **76.62** | [138.59, 183.13] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **3** | `3125` | **Nicholas Pooran** | `BAT_SPECIALIST` | 190 (47) | 160.53 | 167.88 | 0.956x / 0.956x (No) | 157.22 | 0.4029 | **75.93** | [125.95, 193.98] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **4** | `3916` | **Jitesh Sharma** | `BAT_SPECIALIST` | 225 (52) | 161.78 | 166.34 | 0.973x / 0.973x (No) | 158.81 | 0.4367 | **74.84** | [136.55, 188.00] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `1699` | **Suryakumar Yadav** | `BAT_SPECIALIST` | 157 (50) | 164.97 | 170.74 | 0.966x / 0.966x (No) | 160.45 | 0.4425 | **73.17** | [136.52, 191.72] | `ROBUST_ACROSS_WEIGHTS` |
| **6** | `6448` | **Ibrahim Zadran** | `BAT_SPECIALIST` | 99 (9) | 118.18 | 117.47 | 1.006x / 1.006x (No) | 120.99 | 0.6080 | **73.15** | [94.44, 141.80] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **7** | `3056` | **Iftikhar Ahmed** | `BAT_PRIMARY_AR` | 112 (24) | 155.36 | 120.45 | 1.290x / 1.290x (No) | 151.11 | 0.3912 | **72.92** | [106.94, 195.24] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **8** | `796` | **Matthew Wade** | `BAT_SPECIALIST` | 159 (19) | 130.19 | 131.67 | 0.989x / 0.989x (No) | 130.45 | 0.4991 | **72.39** | [103.28, 153.20] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **9** | `7897` | **Tilak Varma** | `BAT_PRIMARY_AR` | 307 (67) | 142.35 | 143.03 | 0.995x / 0.995x (No) | 141.57 | 0.4589 | **71.72** | [119.80, 166.46] | `ROBUST_ACROSS_WEIGHTS` |
| **10** | `6460` | **Ayush Badoni** | `BAT_PRIMARY_AR` | 184 (39) | 144.02 | 149.14 | 0.966x / 0.966x (No) | 142.60 | 0.4574 | **70.48** | [117.06, 168.57] | `ROBUST_ACROSS_WEIGHTS` |

#### Transparency Disclosure — Cohort Quality & Weight-Sensitive Batter Ranks
- **Below-Mean Transparency Flagging:** Eligible cohort mean Crisis SR is **132.10**; high-survival batters #6 (`Ibrahim Zadran`, 118.18 SR) and #8 (`Matthew Wade`, 130.19 SR) are explicitly flagged `CRISIS_SR_BELOW_COHORT_MEAN`.
- **Weight-Sensitive Ranks:** Across the 5 prespecified weight configurations (`RANKING_WEIGHT_SENSITIVITY.csv`), ranks **#1, #4, #5, #9, #10** remain `ROBUST_ACROSS_WEIGHTS`, whereas **#2, #3, #6, #7, #8** are flagged `RANKING_SENSITIVE_TO_WEIGHTS`.

---

### 🎯 Universal Top 10 Bowlers (Gated: `BOWL_SPECIALIST` & `BOWL_PRIMARY_AR`)
*Eligibility: $\ge 120$ high-pressure legal balls, $\ge 120$ total legal balls, $\ge 5$ crisis matches (197 eligible frontline bowlers). Uses cohort-calibrated `did_bowl_maintenance` + `abs_bowl_score` with 2.5%/97.5% winsorized z-score normalization. Bowlers with $< 100$ normal balls are retained as `PRIOR_ANCHORED_SPECIALIST` with reliability-attenuated maintenance weights (`effective_w_maint`).*

| Rank | Canonical ID | Player Name | V3 Role | High-Pressure Balls (Matches) | Normal Balls | Normal Baseline Status | Crisis Dot % | Normal Dot % | Raw / Capped Dot Maint. (Capped?) | Crisis Wkt % (Shrunk) | Consistency | Provisional Score (`PRI`) | 95% Match-Cluster CI | Weight Sensitivity |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `3578` | **Imad Wasim** | `BOWL_PRIMARY_AR` | 129 (10) | 68 | `PRIOR_ANCHORED_SPECIALIST` | 41.86% | 48.53% | 0.863x / N/A (No) | 6.98% (6.33%) | 0.6133 | **90.81** | [35.06%, 47.76%] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `28756` | **Haider Ali (UAE)** | `BOWL_SPECIALIST` | 146 (11) | 79 | `PRIOR_ANCHORED_SPECIALIST` | 50.00% | 37.97% | 1.317x / N/A (No) | 7.53% (6.71%) | 0.5778 | **90.63** | [41.51%, 61.74%] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `5750` | **Ehsan Khan** | `BOWL_SPECIALIST` | 141 (8) | 12 | `PRIOR_ANCHORED_SPECIALIST` | 37.59% | 33.33% | 1.128x / N/A (No) | 7.09% (6.43%) | 0.6473 | **88.65** | [28.47%, 48.78%] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `722` | **Liam Dawson** | `BOWL_SPECIALIST` | 204 (19) | 129 | `VALID_NORMAL_BASELINE` | 37.75% | 35.66% | 1.059x / 1.059x (No) | 6.37% (6.09%) | 0.6609 | **88.56** | [31.91%, 45.00%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **5** | `7741` | **Gareth Delany** | `BOWL_PRIMARY_AR` | 210 (27) | 189 | `VALID_NORMAL_BASELINE` | 39.05% | 31.22% | 1.251x / 1.251x (No) | 7.14% (6.61%) | 0.5569 | **87.15** | [32.18%, 47.87%] | `ROBUST_ACROSS_WEIGHTS` |
| **6** | `3641` | **Ben Dwarshuis** | `BOWL_SPECIALIST` | 204 (14) | 45 | `PRIOR_ANCHORED_SPECIALIST` | 41.67% | 20.00% | 2.083x / N/A (No) | 9.80% (8.39%) | 0.5446 | **84.04** | [32.29%, 50.24%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **7** | `3629` | **Corbin Bosch** | `BOWL_PRIMARY_AR` | 208 (18) | 76 | `PRIOR_ANCHORED_SPECIALIST` | 42.31% | 48.68% | 0.869x / N/A (No) | 9.62% (8.28%) | 0.5668 | **81.77** | [34.34%, 48.88%] | `ROBUST_ACROSS_WEIGHTS` |
| **8** | `161` | **Dwayne Bravo** | `BOWL_SPECIALIST` | 135 (9) | 39 | `PRIOR_ANCHORED_SPECIALIST` | 34.07% | 30.77% | 1.107x / N/A (No) | 9.63% (7.87%) | 0.5150 | **78.68** | [25.60%, 45.19%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **9** | `6450` | **Mujeeb Ur Rahman** | `BOWL_SPECIALIST` | 517 (38) | 190 | `VALID_NORMAL_BASELINE` | 45.07% | 43.16% | 1.044x / 1.044x (No) | 5.22% (5.27%) | 0.5220 | **78.57** | [39.76%, 50.10%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **10** | `7920` | **Nathan Ellis** | `BOWL_SPECIALIST` | 591 (42) | 177 | `VALID_NORMAL_BASELINE` | 35.19% | 39.55% | 0.890x / 0.890x (No) | 6.77% (6.59%) | 0.6540 | **78.23** | [31.78%, 38.74%] | `RANKING_SENSITIVE_TO_WEIGHTS` |

*Role Governance Confirmation:* Harry Tector is classified as `BAT_PRIMARY_AR` and is excluded from the bowling leaderboard. **Intersection between Batting and Bowling Top 10 is exactly 0.**

---

## 📊 Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

Full multi-dimensional sensitivity results (312 combinations across crisis balls, match counts `5, 8, 10`, normal balls, and total deliveries) are saved in `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`. Below is the primary crisis-ball sweep holding ancillary thresholds at baseline (`crisis_matches >= 5`, `total_balls >= 120`, batter `norm_balls >= 60`, bowler `norm_balls >= 100`):

| Crisis Ball Threshold | Eligible Batters | Available Batter Top-10 | Batter Overlap vs Baseline (`60`b) | Batter Jaccard Similarity | Batter Mean / Max Rank Shift | Eligible Bowlers (`norm>=100` sweep) | Available Bowler Top-10 | Bowler Overlap vs Baseline (`120`b, incl. specialists) | Bowler Jaccard Similarity | Bowler Mean / Max Rank Shift |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **40** | 95 | 10 | 6 / 10 | 0.4286 | 2.8 / 4 | 95 | 10 | 4 / 10 | 0.2500 | 7.0 / 14 |
| **60** *(Bat Baseline)* | **65** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 | 95 | 10 | 4 / 10 | 0.2500 | 7.0 / 14 |
| **80** | 60 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 | 95 | 10 | 4 / 10 | 0.2500 | 7.0 / 14 |
| **100** | 52 | 10 | 8 / 10 | 0.6667 | 1.6 / 2 | 94 | 10 | 4 / 10 | 0.2500 | 7.0 / 14 |
| **150** | 34 | 10 | 7 / 10 | 0.5385 | 2.5 / 4 | 94 | 10 | 4 / 10 | 0.2500 | 7.0 / 14 |
| **200** | 18 | 10 | 3 / 10 | 0.1765 | 8.1 / 19 | 90 | 10 | 4 / 10 | 0.2500 | 7.0 / 14 |
| **250** | 10 | 10 | 2 / 10 | 0.1111 | 18.9 / 44 | 85 | 10 | 2 / 10 | 0.1111 | 11.7 / 19 |

- **Threshold Stability Analysis:** Under `V3.3_GOLDFISH_CHASE_LEVERAGE` (`crisis_balls >= 60`, `norm_balls >= 60`), **65 batters** qualify at the `60`-ball baseline (`10/10` overlap at `80` balls, `8/10` at `100` balls, `7/10` at `150` balls, `3/10` at `200` balls, and `2/10` at `250` balls). For bowlers, **197 frontline bowlers** qualify under the prior-anchored specialist baseline (`>=120` crisis balls), while the `norm>=100` sweep spans `95` (`40–80b`) to `85` (`250b`).

---

## 🏰 Rajasthan Royals 2026 Empirical Audit (System B)

All 16 matches (14 league games + Eliminator win + Qualifier 2 loss) and 3,788 deliveries played by RR in IPL 2026 were ingested and reconciled:

- **Orange Cap & Tournament MVP:** **Vaibhav Sooryavanshi** — 16 matches (12 Starting XI + 4 Impact Sub), 776 runs, 327 balls, SR 237.31, avg 48.50, 72 sixes.
- **Top Batting Contributors:**
  - **Dhruv Jurel:** 16 matches, 515 runs, 333 balls, SR 154.65, **average 36.79** (14 dismissals, 2 not outs, resolving partner run-out misattributions).
  - **Yashasvi Jaiswal:** 16 matches, 427 runs, 280 balls, SR 152.50, avg 30.50.
  - **Donovan Ferreira:** 13 inns, 317 runs, 177 balls, SR 179.10, avg 35.22, 23 sixes.
  - **Riyan Parag:** 14 matches, 309 runs, 196 balls, SR 157.65, avg 23.77.
  - **Ravindra Jadeja:** 11 inns, 266 runs, 197 balls, SR 135.03, avg 66.50 (7 not outs).
- **Bowling Leadership:**
  - **Jofra Archer:** 16 matches, 60.0 overs, 158 dot balls, **25 bowler-creditable wickets** (29 total wickets in over).
  - **Brijesh Sharma:** 13 matches, 14 bowler-creditable wickets.
  - **Nandre Burger:** 13 matches, 14 bowler-creditable wickets.
  - **Ravi Bishnoi:** 9 matches, 11 bowler-creditable wickets (benched for 7 games).
  - **Adam Milne:** Selected in 16 squad sheets, but played **exactly 1 match** (3.2 overs, 0 wickets).

---

## 🎯 Tactical Squad Gaps & Scenario-Based Auction Strategy (Goa 2027)

> **Auction Purse & Salary Provenance Disclosure (`UNVERIFIED_USER_BRIEF_SCENARIO`):**
> The IPL 2026 player contract values, carried purse figures, and 2027 cap-increase scenarios below are **not present in the raw ball-by-ball CSVs**. They are scenario-modeling inputs sourced from the user problem brief (`data/reference/rr_2026_user_brief.csv` and `data/reference/rr_2027_auction_assumptions.csv`, last verified against repository reference tables on `2026-11-15`) and must be treated as **unverified external scenario assumptions** for strategic simulation rather than audited official BCCI financial records.

| Tactical Gap | Priority | Target Candidate 1 | Target Candidate 2 | Contingency Backup | Simulated Allocation Scenario |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **Indian Frontline Pacer** | **CRITICAL** | **Prasidh Krishna** | **Avesh Khan** | Mukesh Kumar / Akash Deep | **₹10.0 – ₹13.0 Cr** *(scenario)* |
| **Overseas Death Bowler** | **CRITICAL** | **Matheesha Pathirana** | **Nuwan Thushara** | Gerald Coetzee | **₹8.0 – ₹11.0 Cr** *(scenario)* |
| **Middle Finger Spinner** | **IMPORTANT** | **R Sai Kishore** | **Akeal Hosein** | Rahul Chahar | **₹3.0 – ₹5.0 Cr** *(scenario)* |
| **Domestic Finisher** | **IMPORTANT** | **Ashutosh Sharma** | **Abhinav Manohar** | Sameer Rizvi | **₹2.0 – ₹3.0 Cr** *(scenario)* |

### Simulated Purse Arithmetic (`data/reference/rr_2027_auction_assumptions.csv`, checked `2026-11-15`, Status: `UNVERIFIED_USER_BRIEF_ASSUMPTION`)
- **Carried Unspent Purse (Brief Assumption):** `₹2.65 Cr`
- **Simulated Releases (Hetmyer ₹11.00 Cr, Deshpande ₹6.50 Cr, Sandeep ₹4.00 Cr, Milne ₹2.40 Cr, Kuldeep Sen ₹0.75 Cr, Pretorius ₹0.30 Cr):** `₹24.95 Cr`
- **Simulated Base Available Purse:** `₹27.60 Cr` (or `₹32.60 Cr` under hypothetical `+₹5.00 Cr` cap expansion).
- **Regulatory Advisory:** Dasun Shanaka was signed as a temporary injury replacement for Sam Curran; both cannot be retained permanently without resolving Curran's medical status.

---

## 🔬 Mathematical Models, Governance & Limitations Matrix

| Component | Implementation | Validation Split | Actual Audited Diagnostic Metrics | Governance Status | Used in Final Ranking? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **1. Pressure Model** | `src/pressure_engine/v3_pressure_model.py` | Ex-Ante Rule Audit | Zero post-delivery leakage; bounded in $[0, 10]$; pre-delivery state + clean chase leverage | **`V3.3_GOLDFISH_CHASE_LEVERAGE`** | **Yes (Tier Stratification)** |
| **2. Role Classifier** | `src/classification/v3_role_classifier.py` | Multi-Season Workload | 1,100 canonical players; 0 overlap between bat (360) and bowl (332) gates | **`CANONICAL_ROLE_GATING_ACTIVE`** | **Yes (Eligibility Gate)** |
| **3. Ranking Score (`PRI`)** | `scripts/compute_v3_rankings.py` | Sensitivity Grid (5 Weight Sets, 312 Thresholds) | Fixed weights (35/35/20/10, prior-anchored for `<100`b bowlers); not yet validated out-of-time | **`PROVISIONAL_FIXED_WEIGHT_SCORE`** | **Yes (Primary Score)** |
| **4. Uncertainty & Shrinkage** | `src/reliability/v3_reliability.py` | 2,000-Iter Cluster Bootstrap | Match-clustered 95% CIs; Fixed-$K$ ($K=25$) & Beta-Binomial priors on eligible pool | **`VERIFIED_CLUSTER_BOOTSTRAP`** | **Yes (Shrinkage & CIs)** |
| **5. Wicket Hazard Model** | `src/models/v3_wicket_hazard.py` | Chronological Split (`2025-06-01`) | **AUC: 0.572, Log-Loss: 0.692, Expected Wickets: 26,843 vs Actual: 2,931 (9.16x miscalibration)** | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **6. Joint Ridge Model** | `src/models/v3_joint_performance.py` | Chronological Split | Exploratory hierarchical Ridge regression | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **7. LightGBM Challenger** | `src/models/v3_lightgbm_challenger.py` | Chronological Split | Exploratory non-linear tree benchmark | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **8. Tail-Risk (CVaR90)** | `src/models/v3_tail_risk.py` | Over-Level Empirical Quantiles | Exploratory over-concession tail metric | **`EXPLORATORY_ANALYTICS_ONLY`** | **No (Excluded)** |

### Critical Model Limitations & Governance Disclosures
1. **Pressure Model Limitation (`V3.3_GOLDFISH_CHASE_LEVERAGE`):**
   - The current pressure model is a **pre-delivery state & clean-channel chase-leverage heuristic**, not a fully calibrated win-probability-added (WPA) model.
   - Because `extras1_runs` is a categorical codebook (1–7), full reconstructed scoreboard totals remain quarantined; instead, `clean_rrr_deficit` provides a lower-bound, non-DLS-adjusted 2nd-innings chase proxy using `runs + 1 * is_wide_or_overstep`.
2. **Wicket Hazard Model Governance (`EXPERIMENTAL_NOT_USED_FOR_RANKING`):**
   - On the chronological held-out evaluation split (`src/models/v3_wicket_hazard.py`), the logistic hazard model with `class_weight='balanced'` yields **ROC-AUC = 0.572**, **Log-Loss = 0.692**, and **Brier Score = 0.246**, while predicting **26,843 expected wickets against 2,931 actual wickets** (a **9.16x over-prediction** caused by uncalibrated balanced class weights inflating rare-event probabilities toward ~0.50).
   - This model is strictly designated **`EXPERIMENTAL_NOT_USED_FOR_RANKING`**. It is never presented as calibrated or production-ready, and neither the hazard model, the joint model, nor the LightGBM challenger is used in computing the Universal Top-10 rankings.

---

## 🚀 Reproducible Execution & Verification

### 1. Recompute Authoritative Rankings & Synchronized Copies
```powershell
.\.venv\Scripts\python.exe scripts/compute_v3_rankings.py
```

### 2. Run Independent Verification Gate (`verify_v3_rankings.py`)
```powershell
.\.venv\Scripts\python.exe scripts/verify_v3_rankings.py
```

### 3. Run the Full Automated Test Suite (65 Passed Tests)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### 4. Launch Interactive Executive Dashboard
```powershell
.\.venv\Scripts\streamlit.exe run dashboard/app.py
```
App URL: `http://localhost:8501`

