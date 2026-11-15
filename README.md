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
> "Rankings are provisional. Batter ranks 5, 6, 9 and 10 are sensitive to scoring weights. The pressure classification remains heuristic and position-proxy based. The new score has not yet undergone independent out-of-time validation."

---

## 🏆 Universal Top 10 Leaderboards Under Pressure (System A — Canonical Source of Truth)

All ranking tables below are generated directly from the single authoritative source-of-truth CSVs (`data/outputs/v3/TOP_10_BATTERS.csv` and `data/outputs/v3/TOP_10_BOWLERS.csv`) registered in `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`. All downstream copies (`FINAL_TOP_10_*.csv`, `data/outputs/top_10_*.csv`) are synchronized byte-for-byte with these canonical files and verified by `scripts/verify_v3_rankings.py`.

### 🏏 Universal Top 10 Batters (Gated: `BAT_SPECIALIST` & `BAT_PRIMARY_AR`)
*Eligibility: $\ge 40$ crisis balls, $\ge 120$ total career balls, $\ge 5$ crisis matches, $\ge 30$ normal baseline balls (39 eligible frontline batters). Confidence intervals: 2,000-iteration match-clustered bootstrap (95% percentile).*

| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls (Matches) | Crisis SR | Normal SR ($\ge 30$b) | Raw / Capped Maint. (Capped?) | Shrunk Crisis SR | Match Consistency | Provisional Score (`PRI`) | 95% Match-Cluster CI | Weight Sensitivity & Flags |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `7897` | **Tilak Varma** | `BAT_PRIMARY_AR` | 60 (18) | 196.67 | 144.47 | 1.361x / 1.361x (No) | 180.06 | 0.5120 | **94.29** | [157.62, 251.16] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `796` | **Matthew Wade** | `BAT_SPECIALIST` | 50 (15) | 172.00 | 144.49 | 1.190x / 1.190x (No) | 161.40 | 0.5018 | **77.35** | [105.70, 213.93] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `4106` | **Daryl Mitchell** | `BAT_PRIMARY_AR` | 44 (12) | 177.27 | 147.10 | 1.205x / 1.205x (No) | 163.84 | 0.4266 | **72.55** | [117.22, 237.04] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `4391` | **Liam Livingstone** | `BAT_PRIMARY_AR` | 60 (14) | 175.00 | 161.29 | 1.085x / 1.085x (No) | 164.77 | 0.4376 | **68.92** | [106.81, 221.52] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `4773` | **Jaker Ali Anik** | `BAT_SPECIALIST` | 63 (15) | 139.68 | 122.38 | 1.141x / 1.141x (No) | 139.83 | 0.4874 | **65.13** | [100.00, 181.64] | `RANKING_SENSITIVE_TO_WEIGHTS`; `CRISIS_SR_BELOW_COHORT_MEAN` |
| **6** | `7446` | **Abdul Samad** | `BAT_SPECIALIST` | 69 (23) | 169.57 | 168.67 | 1.005x / 1.005x (No) | 161.76 | 0.4409 | **64.51** | [128.57, 206.50] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **7** | `1077` | **David Miller** | `BAT_SPECIALIST` | 56 (17) | 166.07 | 156.15 | 1.064x / 1.064x (No) | 158.09 | 0.4178 | **63.35** | [100.00, 218.65] | `ROBUST_ACROSS_WEIGHTS` |
| **8** | `8` | **MS Dhoni** | `BAT_SPECIALIST` | 133 (35) | 154.89 | 140.94 | 1.099x / 1.099x (No) | 152.56 | 0.3983 | **62.51** | [119.66, 187.59] | `ROBUST_ACROSS_WEIGHTS` |
| **9** | `3056` | **Iftikhar Ahmed** | `BAT_PRIMARY_AR` | 40 (11) | 127.50 | 120.96 | 1.054x / 1.054x (No) | 132.39 | 0.5497 | **62.38** | [92.72, 158.34] | `RANKING_SENSITIVE_TO_WEIGHTS`; `CRISIS_SR_BELOW_COHORT_MEAN` |
| **10** | `3916` | **Jitesh Sharma** | `BAT_SPECIALIST` | 51 (22) | 172.55 | 155.53 | 1.109x / 1.109x (No) | 161.91 | 0.3598 | **62.01** | [108.69, 236.85] | `RANKING_SENSITIVE_TO_WEIGHTS` |

#### Transparency Disclosure — Weight-Sensitive Batter Ranks & Iftikhar Ahmed (#9) Component Breakdown
- **Weight-Sensitive Ranks:** Across the 5 prespecified weight configurations (`RANKING_WEIGHT_SENSITIVITY.csv`), the top 4 batters (#1 Tilak Varma, #2 Matthew Wade, #3 Daryl Mitchell, #4 Liam Livingstone) as well as #7 David Miller and #8 MS Dhoni remain robust (`max_rank_shift < 5`), whereas **#5 Jaker Ali Anik** (ranks 5–13), **#6 Abdul Samad** (ranks 5–10), **#9 Iftikhar Ahmed** (ranks 5–18), and **#10 Jitesh Sharma** (ranks 6–15) are explicitly flagged `RANKING_SENSITIVE_TO_WEIGHTS`.
- **Iftikhar Ahmed (`canonical_player_id=3056`, Rank #9) Component-Level Breakdown:**
  - Observed Crisis SR: **127.50** (40 balls across 11 matches), which is **below the eligible cohort mean of 140.20** (`-12.70` SR diff; explicitly flagged `CRISIS_SR_BELOW_COHORT_MEAN`).
  - Why he ranks #9 under the provisional fixed-weight formula (`35% Maintenance + 35% Absolute + 20% Consistency + 10% Sample`):
    - **Consistency Contribution (`20%` weight):** **20.00 / 20.00 pts** (match consistency score `0.5497`, highest `#1` in the 39-player eligible batter cohort).
    - **Maintenance Contribution (`35%` weight):** **20.95 / 35.00 pts** (`1.054x` maintenance over his personal normal baseline SR of `120.96` across 291 normal balls).
    - **Absolute Crisis SR Contribution (`35%` weight):** **14.71 / 35.00 pts** (shrunk crisis SR `132.39`, reflecting low raw strike rate).
    - **Sample Confidence Contribution (`10%` weight):** **6.72 / 10.00 pts** (40 crisis balls).
    - **Total Provisional Score:** `20.95 + 14.71 + 20.00 + 6.72 = 62.38`. Under `absolute_heavy` weighting (50% Absolute), Iftikhar drops from #9 to #18. In accordance with governance rules, he is not manually removed or demoted; instead, this component breakdown and anomaly flag are exposed directly in `TOP_10_BATTERS.csv`.

---

### 🎯 Universal Top 10 Bowlers (Gated: `BOWL_SPECIALIST` & `BOWL_PRIMARY_AR`)
*Eligibility: $\ge 120$ high-pressure legal balls, $\ge 120$ total legal balls, $\ge 5$ crisis matches, and **$\ge 100$ normal-pressure legal balls** (`MIN_NORMAL_BALLS = 100`, separate from high-pressure eligibility; 39 eligible frontline bowlers). Bowlers with $< 100$ normal balls (549 of 596 bowlers, including Craig Young [36 norm balls], Mark Adair [82 norm balls], Mark Wood [62 norm balls], Obed McCoy [46 norm balls], and Trent Boult [64 norm balls]) are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT` and excluded from composite ranking so small-denominator normal baselines cannot inflate maintenance ratios.*

| Rank | Canonical ID | Player Name | V3 Role | High-Pressure Balls (Matches) | Normal Balls (`>=100`) | Normal Baseline Status | Crisis Dot % | Normal Dot % | Raw / Capped Dot Maint. (Capped?) | Crisis Wkt % (Shrunk) | Consistency | Provisional Score (`PRI`) | 95% Match-Cluster CI | Weight Sensitivity |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `8661` | **Matheesha Pathirana** | `BOWL_SPECIALIST` | 578 (49) | 122 | `VALID_NORMAL_BASELINE` | 36.51% | 38.52% | 0.948x / 0.948x (No) | 8.48% (8.04%) | 0.5785 | **84.45** | [32.03%, 40.96%] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `1944` | **Keshav Maharaj** | `BOWL_PRIMARY_AR` | 225 (26) | 112 | `VALID_NORMAL_BASELINE` | 33.33% | 31.25% | 1.067x / 1.067x (No) | 7.11% (6.62%) | 0.4495 | **68.40** | [24.88%, 41.10%] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `8380` | **Mohammad Rishad Hossain** | `BOWL_PRIMARY_AR` | 294 (40) | 261 | `VALID_NORMAL_BASELINE` | 36.05% | 42.53% | 0.848x / 0.848x (No) | 7.82% (7.24%) | 0.5006 | **64.99** | [31.16%, 41.23%] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `6464` | **Arshdeep Singh** | `BOWL_PRIMARY_AR` | 2069 (141) | 149 | `VALID_NORMAL_BASELINE` | 36.93% | 44.30% | 0.834x / 0.834x (No) | 5.94% (5.93%) | 0.6475 | **64.66** | [34.55%, 39.25%] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `7503` | **Ravi Bishnoi** | `BOWL_PRIMARY_AR` | 936 (94) | 401 | `VALID_NORMAL_BASELINE` | 37.07% | 38.40% | 0.965x / 0.965x (No) | 5.56% (5.55%) | 0.5641 | **62.40** | [33.60%, 40.67%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **6** | `2681` | **Taskin Ahmed** | `BOWL_PRIMARY_AR` | 552 (46) | 100 | `VALID_NORMAL_BASELINE` | 41.67% | 50.00% | 0.833x / 0.833x (No) | 6.34% (6.21%) | 0.5644 | **60.26** | [36.56%, 46.84%] | `ROBUST_ACROSS_WEIGHTS` |
| **7** | `4900` | **Wanindu Hasaranga** | `BOWL_PRIMARY_AR` | 868 (82) | 331 | `VALID_NORMAL_BASELINE` | 31.68% | 42.30% | 0.749x / 0.749x (No) | 7.14% (6.97%) | 0.5403 | **59.88** | [28.49%, 34.92%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **8** | `3653` | **Avesh Khan** | `BOWL_SPECIALIST` | 1049 (77) | 136 | `VALID_NORMAL_BASELINE` | 35.46% | 41.18% | 0.861x / 0.861x (No) | 5.82% (5.79%) | 0.5756 | **59.16** | [31.79%, 39.42%] | `ROBUST_ACROSS_WEIGHTS` |
| **9** | `2526` | **Ish Sodhi** | `BOWL_PRIMARY_AR` | 404 (46) | 249 | `VALID_NORMAL_BASELINE` | 30.94% | 35.34% | 0.875x / 0.875x (No) | 7.18% (6.85%) | 0.4459 | **58.71** | [26.10%, 36.39%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **10** | `3276` | **Gudakesh Motie** | `BOWL_PRIMARY_AR` | 315 (32) | 100 | `VALID_NORMAL_BASELINE` | 33.97% | 31.00% | 1.096x / 1.096x (No) | 4.44% (4.70%) | 0.4833 | **56.23** | [26.70%, 42.49%] | `RANKING_SENSITIVE_TO_WEIGHTS` |

*Role Governance Confirmation:* Harry Tector is classified as `BAT_PRIMARY_AR` and is excluded from the bowling leaderboard. **Intersection between Batting and Bowling Top 10 is exactly 0.**

---

## 📊 Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

Full multi-dimensional sensitivity results (270 combinations across crisis balls, match counts `5, 8, 10`, normal balls, and total deliveries) are saved in `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`. Below is the primary crisis-ball sweep holding ancillary thresholds at baseline (`crisis_matches >= 5`, `total_balls >= 120`, batter `norm_balls >= 30`, bowler `norm_balls >= 100`):

| Crisis Ball Threshold | Eligible Batters | Available Batter Top-10 | Batter Overlap vs Baseline (`40`b) | Batter Jaccard Similarity | Batter Mean / Max Rank Shift | Eligible Bowlers (`norm>=100`) | Available Bowler Top-10 | Bowler Overlap vs Baseline (`120`b) | Bowler Jaccard Similarity | Bowler Mean / Max Rank Shift |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **40** *(Bat Baseline)* | **39** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 | 40 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **60** | 21 | 10 | 5 / 10 | 0.3333 | 3.7 / 8 | 40 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **80** | 11 | 10 | 1 / 10 | 0.0526 | 17.3 / 24 | 40 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **100** | 8 | **8** *(unforced)* | 1 / 10 | 0.0588 | 20.0 / 30 | 39 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **120** *(Bowl Baseline)* | 6 | **6** *(unforced)* | 1 / 10 | 0.0667 | 22.8 / 32 | **39** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 |
| **150** | 0 | **0** *(unforced)* | 0 / 10 | 0.0000 | 0.0 / 0 | 39 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **200** | 0 | **0** *(unforced)* | 0 / 10 | 0.0000 | 0.0 / 0 | 39 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **250** | 0 | **0** *(unforced)* | 0 / 10 | 0.0000 | 0.0 / 0 | 37 | 10 | 9 / 10 | 0.8182 | 0.9 / 1 |

- **Critical Stability Disclosure:** A 10/10 overlap at the low baseline threshold (`40` crisis balls for batters) **is not proof of stability across higher thresholds**. Because batting crisis states (`>= 5.5` score) represent only 7.97% of regular deliveries, raising the minimum to `60` crisis balls drops batter Top-10 overlap to `5/10` (Jaccard `0.3333`; Matthew Wade, Daryl Mitchell, David Miller, Iftikhar Ahmed, and Jitesh Sharma exit; Ramandeep Singh, Marcus Stoinis, Rinku Singh, Rahul Tewatia, and Shimron Hetmyer enter), and at `100` crisis balls only **8 batters** qualify (Top-10 is never forced when fewer than 10 players are eligible).

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
| **2. Role Classifier** | `src/classification/v3_role_classifier.py` | Multi-Season Workload | 1,118 canonical players; 0 overlap between bat (382) and bowl (311) gates | **`CANONICAL_ROLE_GATING_ACTIVE`** | **Yes (Eligibility Gate)** |
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

