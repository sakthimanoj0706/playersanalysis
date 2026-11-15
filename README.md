# SupeRR Intelligence V3 👑
### Rajasthan Royals SupeRR Selector Season 2 — Joint Performance, Pressure Intelligence & Player-Fit Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/pytest-64%20passed-success.svg)](tests/)
[![Dataset](https://img.shields.io/badge/data-IPL%20%2B%20T20I%20(2022--2026)-magenta.svg)](data/)
[![Ranking Status](https://img.shields.io/badge/status-P1.1%20PATCH%20VERIFIED%20%E2%80%94%20PROVISIONAL%20MODEL-orange.svg)](data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json)

**SupeRR Intelligence V3** is an audited, reproducible cricket analytics and decision-support platform engineered for the Rajasthan Royals (RR) SupeRR Selector Season 2 Hackathon. The platform delivers two independent, decoupled analytical systems:

1. **System A — Universal Cricket Intelligence:** Context-benchmarked performance evaluation across 837 matches (IPL & T20I 2022–2026, 193,988 regular deliveries) with canonical player identity resolution (`PLAYER_IDENTITY_CROSSWALK.csv`), 5-state mutually exclusive role gating, Empirical Bayes shrinkage, and 2,000-iteration match-clustered bootstrap confidence intervals.
2. **System B — Rajasthan Royals Team Intelligence:** Squad-first empirical analysis of RR's 16-match 2026 IPL campaign (3,788 balls, 3rd place overall finish), identifying 4 verified tactical deficiencies and evaluating 13 watchlist candidates under constraint-aware multi-criteria optimization.

> **Mandatory Provisional Model Disclosure:**
> "Rankings are provisional. Batter ranks 1–5 are robust across all 5 weight configurations, while batter ranks 6–10 are sensitive to scoring weights. The pressure classification uses the calibrated pre-delivery state heuristic (`V3.2_EGM_CALIBRATED_HEURISTIC`). The new score has not yet undergone independent out-of-time validation."

---

## 🏆 Universal Top 10 Leaderboards Under Pressure (System A — Canonical Source of Truth)

All ranking tables below are generated directly from the single authoritative source-of-truth CSVs (`data/outputs/v3/TOP_10_BATTERS.csv` and `data/outputs/v3/TOP_10_BOWLERS.csv`) registered in `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`. All downstream copies (`FINAL_TOP_10_*.csv`, `data/outputs/top_10_*.csv`) are synchronized byte-for-byte with these canonical files and verified by `scripts/verify_v3_rankings.py`.

### 🏏 Universal Top 10 Batters (Gated: `BAT_SPECIALIST` & `BAT_PRIMARY_AR`)
*Eligibility: $\ge 40$ crisis balls, $\ge 120$ total career balls, $\ge 5$ crisis matches, $\ge 30$ normal baseline balls (92 eligible frontline batters). Confidence intervals: 2,000-iteration match-clustered bootstrap (95% percentile).*

| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls (Matches) | Crisis SR | Normal SR ($\ge 30$b) | Raw / Capped Maint. (Capped?) | Shrunk Crisis SR | Match Consistency | Provisional Score (`PRI`) | 95% Match-Cluster CI | Weight Sensitivity & Flags |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `8101` | **Ashutosh Sharma** | `BAT_SPECIALIST` | 148 (26) | 168.92 | 125.58 | 1.345x / 1.345x (No) | 163.31 | 0.7457 | **93.88** | [126.66, 213.61] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `20006` | **Ramandeep Singh** | `BAT_PRIMARY_AR` | 115 (24) | 164.35 | 125.64 | 1.308x / 1.308x (No) | 158.24 | 0.6978 | **87.73** | [118.52, 213.06] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `3647` | **Shreyas Iyer** | `BAT_SPECIALIST` | 65 (29) | 170.77 | 151.61 | 1.126x / 1.126x (No) | 159.48 | 0.8740 | **86.82** | [142.18, 205.17] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `6272` | **William Jacks** | `BAT_PRIMARY_AR` | 41 (15) | 173.17 | 150.17 | 1.153x / 1.153x (No) | 156.87 | 0.8430 | **84.72** | [128.56, 208.11] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `813` | **Jos Buttler** | `BAT_SPECIALIST` | 50 (9) | 168.00 | 154.86 | 1.085x / 1.085x (No) | 155.38 | 0.8185 | **80.62** | [131.42, 184.72] | `ROBUST_ACROSS_WEIGHTS` |
| **6** | `3056` | **Iftikhar Ahmed** | `BAT_PRIMARY_AR` | 92 (23) | 147.83 | 119.74 | 1.235x / 1.235x (No) | 144.05 | 0.7267 | **79.22** | [104.83, 182.73] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **7** | `26906` | **Angkrish Raghuvanshi** | `BAT_SPECIALIST` | 40 (8) | 167.50 | 146.00 | 1.147x / 1.147x (No) | 153.13 | 0.6987 | **76.97** | [107.31, 218.04] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **8** | `8` | **MS Dhoni** | `BAT_SPECIALIST` | 239 (46) | 149.37 | 134.52 | 1.110x / 1.110x (No) | 147.55 | 0.6905 | **75.85** | [119.90, 177.83] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **9** | `2003` | **Bhanuka Rajapaksa** | `BAT_SPECIALIST` | 49 (14) | 153.06 | 134.90 | 1.135x / 1.135x (No) | 145.31 | 0.7594 | **75.84** | [102.07, 201.92] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **10** | `1699` | **Suryakumar Yadav** | `BAT_SPECIALIST` | 128 (45) | 165.62 | 170.49 | 0.971x / 0.971x (No) | 159.83 | 0.7147 | **75.35** | [130.84, 197.34] | `RANKING_SENSITIVE_TO_WEIGHTS` |

#### Transparency Disclosure — Cohort Quality & Weight-Sensitive Batter Ranks
- **100% Above-Mean Crisis Strike Rate:** Every batter in the authoritative Top 10 records a Crisis Strike Rate between **147.83** and **173.17**, well above the 92-player eligible cohort mean of **130.13** (`0` anomaly flags in the Top 10).
- **Weight-Sensitive Ranks:** Across the 5 prespecified weight configurations (`RANKING_WEIGHT_SENSITIVITY.csv`), the top 5 batters (#1 Ashutosh Sharma, #2 Ramandeep Singh, #3 Shreyas Iyer, #4 William Jacks, #5 Jos Buttler) remain strictly robust (`max_rank_shift <= 2`), whereas ranks **#6–#10** (`Iftikhar Ahmed`, `Angkrish Raghuvanshi`, `MS Dhoni`, `Bhanuka Rajapaksa`, `Suryakumar Yadav`) shift by $\ge 5$ places and are explicitly flagged `RANKING_SENSITIVE_TO_WEIGHTS`.

---

### 🎯 Universal Top 10 Bowlers (Gated: `BOWL_SPECIALIST` & `BOWL_PRIMARY_AR`)
*Eligibility: $\ge 120$ high-pressure legal balls, $\ge 120$ total legal balls, $\ge 5$ crisis matches, and **$\ge 100$ normal-pressure legal balls** (`MIN_NORMAL_BALLS = 100`, separate from high-pressure eligibility; 99 eligible frontline bowlers). Bowlers with $< 100$ normal balls (464 of 596 bowlers) are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT` and excluded from composite ranking so small-denominator normal baselines cannot inflate maintenance ratios.*

| Rank | Canonical ID | Player Name | V3 Role | High-Pressure Balls (Matches) | Normal Balls (`>=100`) | Normal Baseline Status | Crisis Dot % | Normal Dot % | Raw / Capped Dot Maint. (Capped?) | Crisis Wkt % (Shrunk) | Consistency | Provisional Score (`PRI`) | 95% Match-Cluster CI | Weight Sensitivity |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `1566` | **Mohammed Shami** | `BOWL_SPECIALIST` | 875 (57) | 121 | `VALID_NORMAL_BASELINE` | 45.83% | 33.06% | 1.386x / 1.386x (No) | 5.71% (5.71%) | 0.7721 | **75.31** | [41.93%, 49.64%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **2** | `4837` | **Obed McCoy** | `BOWL_SPECIALIST` | 385 (31) | 123 | `VALID_NORMAL_BASELINE` | 38.70% | 30.89% | 1.253x / 1.253x (No) | 7.53% (7.15%) | 0.5786 | **73.15** | [33.03%, 44.21%] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `4807` | **Joshua Little** | `BOWL_SPECIALIST` | 446 (34) | 175 | `VALID_NORMAL_BASELINE` | 42.15% | 36.00% | 1.171x / 1.171x (No) | 6.73% (6.54%) | 0.7199 | **70.58** | [37.17%, 47.12%] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `2320` | **Trent Boult** | `BOWL_SPECIALIST` | 1131 (70) | 144 | `VALID_NORMAL_BASELINE` | 42.71% | 24.31% | 1.757x / 1.500x (Yes) | 4.69% (4.77%) | 0.6965 | **69.31** | [39.82%, 45.93%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **5** | `7364` | **Haris Rauf** | `BOWL_SPECIALIST` | 692 (47) | 169 | `VALID_NORMAL_BASELINE` | 41.33% | 42.01% | 0.984x / 0.984x (No) | 7.51% (7.29%) | 0.6729 | **67.48** | [37.41%, 45.10%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **6** | `278` | **Tim Southee** | `BOWL_SPECIALIST` | 531 (36) | 135 | `VALID_NORMAL_BASELINE` | 42.18% | 38.52% | 1.095x / 1.095x (No) | 6.78% (6.61%) | 0.6998 | **67.42** | [38.59%, 46.26%] | `ROBUST_ACROSS_WEIGHTS` |
| **7** | `3275` | **Alzarri Joseph** | `BOWL_SPECIALIST` | 780 (52) | 165 | `VALID_NORMAL_BASELINE` | 40.64% | 32.73% | 1.242x / 1.242x (No) | 5.77% (5.76%) | 0.6823 | **66.07** | [36.76%, 44.77%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **8** | `8380` | **Mohammad Rishad Hossain** | `BOWL_PRIMARY_AR` | 280 (41) | 539 | `VALID_NORMAL_BASELINE` | 35.00% | 36.36% | 0.962x / 0.962x (No) | 8.93% (8.08%) | 0.5223 | **65.84** | [29.92%, 40.25%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **9** | `4229` | **George Linde** | `BOWL_PRIMARY_AR` | 133 (15) | 106 | `VALID_NORMAL_BASELINE` | 41.35% | 33.02% | 1.252x / 1.252x (No) | 6.77% (6.31%) | 0.6095 | **65.77** | [31.79%, 51.52%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **10** | `27960` | **Mayank Yadav** | `BOWL_SPECIALIST` | 276 (22) | 146 | `VALID_NORMAL_BASELINE` | 48.19% | 43.84% | 1.099x / 1.099x (No) | 6.16% (6.04%) | 0.7806 | **65.10** | [42.23%, 54.55%] | `RANKING_SENSITIVE_TO_WEIGHTS` |

*Role Governance Confirmation:* Harry Tector is classified as `BAT_PRIMARY_AR` and is excluded from the bowling leaderboard. **Intersection between Batting and Bowling Top 10 is exactly 0.**

---

## 📊 Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

Full multi-dimensional sensitivity results (270 combinations across crisis balls, match counts `5, 8, 10`, normal balls, and total deliveries) are saved in `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`. Below is the primary crisis-ball sweep holding ancillary thresholds at baseline (`crisis_matches >= 5`, `total_balls >= 120`, batter `norm_balls >= 30`, bowler `norm_balls >= 100`):

| Crisis Ball Threshold | Eligible Batters | Available Batter Top-10 | Batter Overlap vs Baseline (`40`b) | Batter Jaccard Similarity | Batter Mean / Max Rank Shift | Eligible Bowlers (`norm>=100`) | Available Bowler Top-10 | Bowler Overlap vs Baseline (`120`b) | Bowler Jaccard Similarity | Bowler Mean / Max Rank Shift |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **40** *(Bat Baseline)* | **92** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 | 103 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **60** | 71 | 10 | 6 / 10 | 0.4286 | 2.5 / 4 | 102 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **80** | 60 | 10 | 5 / 10 | 0.3333 | 4.2 / 6 | 101 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **100** | 50 | 10 | 4 / 10 | 0.2500 | 5.3 / 7 | 100 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **120** *(Bowl Baseline)* | 39 | 10 | 4 / 10 | 0.2500 | 6.8 / 10 | **99** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 |
| **150** | 25 | 10 | 1 / 10 | 0.0526 | 11.1 / 13 | 96 | 10 | 9 / 10 | 0.8182 | 0.2 / 1 |
| **200** | 11 | 10 | 1 / 10 | 0.0526 | 27.6 / 57 | 89 | 10 | 9 / 10 | 0.8182 | 0.4 / 3 |
| **250** | 7 | **7** *(unforced)* | 0 / 10 | 0.0000 | 34.6 / 70 | 84 | 10 | 9 / 10 | 0.8182 | 0.4 / 3 |

- **Threshold Stability Analysis:** Under the calibrated pre-delivery pressure model (`15.35%` of balls faced classified as High/Extreme Crisis Pressure), **92 batters** qualify at the `40`-ball baseline, **71** at `60` balls (`6/10` Top-10 overlap, retaining Ashutosh Sharma, Ramandeep Singh, Shreyas Iyer, Iftikhar Ahmed, MS Dhoni, and Suryakumar Yadav), **60** at `80` balls (`5/10` overlap), **50** at `100` balls, **25** at `150` balls, **11** at `200` balls, and **7** at `250` balls (`available_top10_count = 7`, never forcing a Top 10 when `<10` players qualify). For bowlers, **99 frontline bowlers** qualify at the `120`-ball baseline (`9/10` Top-10 overlap even at `250` crisis balls).

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
| **Indian Frontline Pacer** | **CRITICAL** | **Prasidh Krishna** | **Avesh Khan** | Mukesh Kumar / Akash Deep | **₹9.0 – ₹11.0 Cr** *(scenario)* |
| **Overseas Death Bowler** | **CRITICAL** | **Matheesha Pathirana** | **Nuwan Thushara** | Gerald Coetzee | **₹8.0 – ₹10.0 Cr** *(scenario)* |
| **Middle Finger Spinner** | **IMPORTANT** | **R Sai Kishore** | **Manav Suthar** | Swapnil Singh | **₹3.0 – ₹4.5 Cr** *(scenario)* |
| **Domestic Finisher** | **IMPORTANT** | **Ashutosh Sharma** | **Abhinav Manohar** | Sameer Rizvi | **₹2.5 – ₹3.5 Cr** *(scenario)* |

### Simulated Purse Arithmetic (`data/reference/rr_2027_auction_assumptions.csv`, checked `2026-11-15`, Status: `UNVERIFIED_USER_BRIEF_ASSUMPTION`)
- **Carried Unspent Purse (Brief Assumption):** `₹2.65 Cr`
- **Simulated Releases (Hetmyer ₹11.00 Cr, Deshpande ₹6.50 Cr, Sandeep ₹4.00 Cr, Milne ₹2.40 Cr, Kuldeep Sen ₹0.75 Cr, Pretorius ₹0.30 Cr):** `₹24.95 Cr`
- **Simulated Base Available Purse:** `₹27.60 Cr` (or `₹32.60 Cr` under hypothetical `+₹5.00 Cr` cap expansion).
- **Regulatory Advisory:** Dasun Shanaka was signed as a temporary injury replacement for Sam Curran; both cannot be retained permanently without resolving Curran's medical status.

---

## 🔬 Mathematical Models, Governance & Limitations Matrix

| Component | Implementation | Validation Split | Actual Audited Diagnostic Metrics | Governance Status | Used in Final Ranking? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **1. Pressure Model** | `src/pressure_engine/v3_pressure_model.py` | Ex-Ante Rule Audit | Zero post-delivery leakage; bounded in $[0, 10]$; position/state heuristic | **`PROVISIONAL_POSITION_PROXY_HEURISTIC`** | **Yes (Tier Stratification)** |
| **2. Role Classifier** | `src/classification/v3_role_classifier.py` | Multi-Season Workload | 1,100 canonical players; 0 overlap between bat (360) and bowl (332) gates | **`CANONICAL_ROLE_GATING_ACTIVE`** | **Yes (Eligibility Gate)** |
| **3. Ranking Score (`PRI`)** | `scripts/compute_v3_rankings.py` | Sensitivity Grid (5 Weight Sets, 270 Thresholds) | Fixed weights (35/35/20/10); not yet validated out-of-time | **`PROVISIONAL_FIXED_WEIGHT_SCORE`** | **Yes (Primary Score)** |
| **4. Uncertainty & Shrinkage** | `src/reliability/v3_reliability.py` | 2,000-Iter Cluster Bootstrap | Match-clustered 95% CIs; Fixed-$K$ ($K=25$) & Beta-Binomial priors on eligible pool | **`VERIFIED_CLUSTER_BOOTSTRAP`** | **Yes (Shrinkage & CIs)** |
| **5. Wicket Hazard Model** | `src/models/v3_wicket_hazard.py` | Chronological Split (`2025-06-01`) | **AUC: 0.572, Log-Loss: 0.692, Expected Wickets: 26,843 vs Actual: 2,931 (9.16x miscalibration)** | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **6. Joint Ridge Model** | `src/models/v3_joint_performance.py` | Chronological Split | Exploratory hierarchical Ridge regression | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **7. LightGBM Challenger** | `src/models/v3_lightgbm_challenger.py` | Chronological Split | Exploratory non-linear tree benchmark | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **8. Tail-Risk (CVaR90)** | `src/models/v3_tail_risk.py` | Over-Level Empirical Quantiles | Exploratory over-concession tail metric | **`EXPLORATORY_ANALYTICS_ONLY`** | **No (Excluded)** |

### Critical Model Limitations & Governance Disclosures
1. **Pressure Model Limitation (`PROVISIONAL_POSITION_PROXY_HEURISTIC`):**
   - The current pressure model is a **position-proxy and pre-delivery state heuristic**, not a fully calibrated match-leverage or win-probability-added (WPA) model.
   - Batting position is a role/entry proxy, not direct evidence of match pressure; positional crisis distributions must **not** be interpreted as calibrated player-level crisis probabilities.
   - Second-innings target, required run rate (RRR), and full chase leverage are **not yet integrated** because `extras1_runs` is a categorical codebook (1–7), quarantining reconstructed scoreboard totals.
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

### 3. Run the Full Automated Test Suite (64 Passed Tests)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### 4. Launch Interactive Executive Dashboard
```powershell
.\.venv\Scripts\streamlit.exe run dashboard/app.py
```
App URL: `http://localhost:8501`

