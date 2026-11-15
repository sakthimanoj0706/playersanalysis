# SupeRR Intelligence V3: Pressure Reliability Analytics & Player Scouting
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

$$\text{Score}_{\text{provisional}} = 100 \times \left( 0.35 M_{\text{norm}} + 0.35 A_{\text{norm}} + 0.20 C_{\text{norm}} + 0.10 S_{\text{norm}} \right)$$

1. **Performance Maintenance ($M$, 35%):**
   - Batting: $\text{SR}_{\text{crisis}} / \text{SR}_{\text{norm}}$ for batters with $\ge 30$ normal balls. Raw (`raw_sr_maintenance`) and capped (`capped_sr_maintenance` in $[0.50, 1.50]$) ratios are reported separately alongside `is_maintenance_capped`.
   - Bowling: $\text{Dot}_{\text{crisis}} / \text{Dot}_{\text{norm}}$ strictly for bowlers with $\ge 100$ normal balls (`MIN_NORMAL_BALLS = 100`). Bowlers with $< 100$ normal balls are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT`, receive `NaN` for `capped_dot_maintenance`, and are excluded from composite ranking.
2. **Absolute Pressure Performance ($A$, 35%):**
   - Batting: Fixed-$K$ Normal shrinkage ($K = 25.0$) toward the eligible batting cohort mean ($140.20$).
   - Bowling: Beta-Binomial Empirical Bayes shrinkage toward the eligible bowling cohort mean ($5.52\%$).
3. **Exposure-Adjusted Match Consistency ($C$, 20%):**
   $$\text{Consistency}_i = \exp(-\text{CV}_i) \cdot \sqrt{\frac{m_i}{m_i + 3}}$$
4. **Sample Size Confidence ($S$, 10%):**
   $$\text{Sample Confidence}_i = \min\left(1.0, \frac{\ln(1 + n_i)}{\ln(1 + 250)}\right)$$

*Validation Governance Note:* Legacy PRI hold-out Spearman correlations from earlier prototypes are **not** used as validation evidence for this V3 score. The V3 score remains explicitly provisional pending independent out-of-time validation.

---

## 4. Authoritative Top 10 Batters Under Crisis Pressure (`data/outputs/v3/TOP_10_BATTERS.csv`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | crisis_matches | crisis_sr | norm_sr | raw_sr_maintenance | sr_maintenance | is_maintenance_capped | shrunk_crisis_sr | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status | performance_anomaly_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 7897 | Tilak Varma | BAT_PRIMARY_AR | 60 | 18 | 196.6667 | 144.473 | 1.361 | 1.361 | False | 180.06 | 0.512 | 94.29 | 157.62 | 251.16 | ROBUST_ACROSS_WEIGHTS | NONE |
| 2 | 796 | Matthew Wade | BAT_SPECIALIST | 50 | 15 | 172 | 144.4915 | 1.19 | 1.19 | False | 161.4 | 0.5018 | 77.35 | 105.7 | 213.93 | ROBUST_ACROSS_WEIGHTS | NONE |
| 3 | 4106 | Daryl Mitchell | BAT_PRIMARY_AR | 44 | 12 | 177.2727 | 147.103 | 1.205 | 1.205 | False | 163.84 | 0.4266 | 72.55 | 117.22 | 237.04 | ROBUST_ACROSS_WEIGHTS | NONE |
| 4 | 4391 | Liam Livingstone | BAT_PRIMARY_AR | 60 | 14 | 175 | 161.295 | 1.085 | 1.085 | False | 164.77 | 0.4376 | 68.92 | 106.81 | 221.52 | ROBUST_ACROSS_WEIGHTS | NONE |
| 5 | 4773 | Jaker Ali Anik | BAT_SPECIALIST | 63 | 15 | 139.6825 | 122.3827 | 1.141 | 1.141 | False | 139.83 | 0.4874 | 65.13 | 100 | 181.64 | RANKING_SENSITIVE_TO_WEIGHTS | CRISIS_SR_BELOW_COHORT_MEAN |
| 6 | 7446 | Abdul Samad | BAT_SPECIALIST | 69 | 23 | 169.5652 | 168.6747 | 1.005 | 1.005 | False | 161.76 | 0.4409 | 64.51 | 128.57 | 206.5 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 7 | 1077 | David Miller | BAT_SPECIALIST | 56 | 17 | 166.0714 | 156.1462 | 1.064 | 1.064 | False | 158.09 | 0.4178 | 63.35 | 100 | 218.65 | ROBUST_ACROSS_WEIGHTS | NONE |
| 8 | 8 | MS Dhoni | BAT_SPECIALIST | 133 | 35 | 154.8872 | 140.9396 | 1.099 | 1.099 | False | 152.56 | 0.3983 | 62.51 | 119.66 | 187.59 | ROBUST_ACROSS_WEIGHTS | NONE |
| 9 | 3056 | Iftikhar Ahmed | BAT_PRIMARY_AR | 40 | 11 | 127.5 | 120.9622 | 1.054 | 1.054 | False | 132.39 | 0.5497 | 62.38 | 92.72 | 158.34 | RANKING_SENSITIVE_TO_WEIGHTS | CRISIS_SR_BELOW_COHORT_MEAN |
| 10 | 3916 | Jitesh Sharma | BAT_SPECIALIST | 51 | 22 | 172.549 | 155.5315 | 1.109 | 1.109 | False | 161.91 | 0.3598 | 62.01 | 108.69 | 236.85 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |

### Transparency & Iftikhar Ahmed (`canonical_player_id=3056`, Rank #9) Component Breakdown
- **Weight-Sensitive Batter Ranks:** Ranks **#5 Jaker Ali Anik**, **#6 Abdul Samad**, **#9 Iftikhar Ahmed**, and **#10 Jitesh Sharma** shift by $\ge 5$ places across the 5 weight configurations and are flagged `RANKING_SENSITIVE_TO_WEIGHTS`.
- **Iftikhar Ahmed (#9) Component Breakdown:**
  - Crisis Strike Rate: **127.50** (40 balls across 11 matches), which is **below the eligible cohort mean of 140.20** (flagged `CRISIS_SR_BELOW_COHORT_MEAN`).
  - Component Contributions: `contrib_maint = 20.95` (1.054x maintenance over 120.96 normal SR) + `contrib_abs = 14.71` (shrunk crisis SR 132.39) + `contrib_cons = 20.00` (match consistency 0.5497, #1 in eligible cohort) + `contrib_sample = 6.72` = **62.38**. His #9 rank is driven by top-of-cohort multi-match consistency and positive personal baseline maintenance offsetting low absolute strike rate.

---

## 5. Authoritative Top 10 Bowlers Under Defensive Pressure (`data/outputs/v3/TOP_10_BOWLERS.csv`, `MIN_NORMAL_BALLS = 100`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | crisis_matches | norm_balls | norm_baseline_status | crisis_dot_pct | norm_dot_pct | raw_dot_maintenance | capped_dot_maintenance | is_maintenance_capped | crisis_wicket_rate | shrunk_crisis_wr | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8661 | Matheesha Pathirana | BOWL_SPECIALIST | 578 | 49 | 122 | VALID_NORMAL_BASELINE | 36.5052 | 38.5246 | 0.948 | 0.948 | False | 8.4775 | 8.04 | 0.5785 | 84.45 | 32.03 | 40.96 | ROBUST_ACROSS_WEIGHTS |
| 2 | 1944 | Keshav Maharaj | BOWL_PRIMARY_AR | 225 | 26 | 112 | VALID_NORMAL_BASELINE | 33.3333 | 31.25 | 1.067 | 1.067 | False | 7.1111 | 6.62 | 0.4495 | 68.4 | 24.88 | 41.1 | ROBUST_ACROSS_WEIGHTS |
| 3 | 8380 | Mohammad Rishad Hossain | BOWL_PRIMARY_AR | 294 | 40 | 261 | VALID_NORMAL_BASELINE | 36.0544 | 42.5287 | 0.848 | 0.848 | False | 7.8231 | 7.24 | 0.5006 | 64.99 | 31.16 | 41.23 | ROBUST_ACROSS_WEIGHTS |
| 4 | 6464 | Arshdeep Singh | BOWL_PRIMARY_AR | 2069 | 141 | 149 | VALID_NORMAL_BASELINE | 36.9261 | 44.2953 | 0.834 | 0.834 | False | 5.9449 | 5.93 | 0.6475 | 64.66 | 34.55 | 39.25 | ROBUST_ACROSS_WEIGHTS |
| 5 | 7503 | Ravi Bishnoi | BOWL_PRIMARY_AR | 936 | 94 | 401 | VALID_NORMAL_BASELINE | 37.0726 | 38.404 | 0.965 | 0.965 | False | 5.5556 | 5.55 | 0.5641 | 62.4 | 33.6 | 40.67 | RANKING_SENSITIVE_TO_WEIGHTS |
| 6 | 2681 | Taskin Ahmed | BOWL_PRIMARY_AR | 552 | 46 | 100 | VALID_NORMAL_BASELINE | 41.6667 | 50 | 0.833 | 0.833 | False | 6.3406 | 6.21 | 0.5644 | 60.26 | 36.56 | 46.84 | ROBUST_ACROSS_WEIGHTS |
| 7 | 4900 | Wanindu Hasaranga | BOWL_PRIMARY_AR | 868 | 82 | 331 | VALID_NORMAL_BASELINE | 31.682 | 42.2961 | 0.749 | 0.749 | False | 7.1429 | 6.97 | 0.5403 | 59.88 | 28.49 | 34.92 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 3653 | Avesh Khan | BOWL_SPECIALIST | 1049 | 77 | 136 | VALID_NORMAL_BASELINE | 35.4623 | 41.1765 | 0.861 | 0.861 | False | 5.8151 | 5.79 | 0.5756 | 59.16 | 31.79 | 39.42 | ROBUST_ACROSS_WEIGHTS |
| 9 | 2526 | Ish Sodhi | BOWL_PRIMARY_AR | 404 | 46 | 249 | VALID_NORMAL_BASELINE | 30.9406 | 35.3414 | 0.875 | 0.875 | False | 7.1782 | 6.85 | 0.4459 | 58.71 | 26.1 | 36.39 | RANKING_SENSITIVE_TO_WEIGHTS |
| 10 | 3276 | Gudakesh Motie | BOWL_PRIMARY_AR | 315 | 32 | 100 | VALID_NORMAL_BASELINE | 33.9683 | 31 | 1.096 | 1.096 | False | 4.4444 | 4.7 | 0.4833 | 56.23 | 26.7 | 42.49 | RANKING_SENSITIVE_TO_WEIGHTS |

---

## 6. Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

### 6.1 Batting Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 30, total_balls >= 120`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 5 | 39 | 40 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 60 | 5 | 21 | 40 | 10 | 5 | 0.3333 | 3.7 | 8 | Ramandeep Singh, Marcus Stoinis, Rinku Singh, Rahul Tewatia, Shimron Hetmyer | Matthew Wade, Daryl Mitchell, David Miller, Iftikhar Ahmed, Jitesh Sharma |
| 80 | 5 | 11 | 40 | 10 | 1 | 0.0526 | 17.3 | 24 | Rinku Singh, Rahul Tewatia, Shimron Hetmyer, Washington Sundar, Dinesh Karthik, M Shahrukh Khan, Andre Russell, Rovman Powell, Dasun Shanaka | Tilak Varma, Matthew Wade, Daryl Mitchell, Liam Livingstone, Jaker Ali Anik, Abdul Samad, David Miller, Iftikhar Ahmed, Jitesh Sharma |
| 100 | 5 | 8 | 39 | 8 | 1 | 0.0588 | 20 | 30 | Rinku Singh, Rahul Tewatia, Dinesh Karthik, Andre Russell, Rovman Powell, Dasun Shanaka, Tim David | Tilak Varma, Matthew Wade, Daryl Mitchell, Liam Livingstone, Jaker Ali Anik, Abdul Samad, David Miller, Iftikhar Ahmed, Jitesh Sharma |
| 150 | 5 | 0 | 39 | 0 | 0 | 0 | 0 | 0 | NONE | Tilak Varma, Matthew Wade, Daryl Mitchell, Liam Livingstone, Jaker Ali Anik, Abdul Samad, David Miller, MS Dhoni, Iftikhar Ahmed, Jitesh Sharma |
| 200 | 5 | 0 | 39 | 0 | 0 | 0 | 0 | 0 | NONE | Tilak Varma, Matthew Wade, Daryl Mitchell, Liam Livingstone, Jaker Ali Anik, Abdul Samad, David Miller, MS Dhoni, Iftikhar Ahmed, Jitesh Sharma |
| 250 | 5 | 0 | 37 | 0 | 0 | 0 | 0 | 0 | NONE | Tilak Varma, Matthew Wade, Daryl Mitchell, Liam Livingstone, Jaker Ali Anik, Abdul Samad, David Miller, MS Dhoni, Iftikhar Ahmed, Jitesh Sharma |

### 6.2 Bowling Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 100, total_legal_balls >= 120`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 5 | 39 | 40 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 60 | 5 | 21 | 40 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 80 | 5 | 11 | 40 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 100 | 5 | 8 | 39 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 120 | 5 | 6 | 39 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 150 | 5 | 0 | 39 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 200 | 5 | 0 | 39 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 250 | 5 | 0 | 37 | 10 | 9 | 0.8182 | 0.9 | 1 | Akeal Hosein | Keshav Maharaj |

*Note:* Top 10 is never forced when fewer than 10 players are eligible (`available_top10_count = 8` at 100 crisis balls for batters, `6` at 120 balls, and `0` at 150–250 balls). A 10/10 overlap at the baseline threshold (`40` balls) is not proof of stability across higher thresholds.

---

## 7. Weight Sensitivity Analysis Across 5 Prespecified Configurations (`RANKING_WEIGHT_SENSITIVITY.csv`)

| provisional_rank | canonical_player_id | player_name | provisional_fixed_weight_score | contrib_maint | contrib_abs | contrib_cons | contrib_sample | rank_balanced_default | rank_maintenance_heavy | rank_absolute_heavy | rank_consistency_heavy | rank_equal_weights | max_rank_shift | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 7897 | Tilak Varma | 94.29 | 35 | 35 | 16.85 | 7.44 | 1 | 1 | 1 | 1 | 1 | 0 | ROBUST_ACROSS_WEIGHTS |
| 2 | 796 | Matthew Wade | 77.35 | 27.18 | 27.06 | 15.99 | 7.12 | 2 | 2 | 2 | 2 | 2 | 0 | ROBUST_ACROSS_WEIGHTS |
| 3 | 4106 | Daryl Mitchell | 72.55 | 27.86 | 28.1 | 9.7 | 6.89 | 3 | 3 | 3 | 3 | 3 | 0 | ROBUST_ACROSS_WEIGHTS |
| 4 | 4391 | Liam Livingstone | 68.92 | 22.37 | 28.49 | 10.62 | 7.44 | 4 | 4 | 4 | 5 | 4 | 1 | ROBUST_ACROSS_WEIGHTS |
| 5 | 4773 | Jaker Ali Anik | 65.13 | 24.93 | 17.88 | 14.79 | 7.53 | 5 | 5 | 11 | 6 | 5 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |
| 6 | 7446 | Abdul Samad | 64.51 | 18.71 | 27.21 | 10.9 | 7.69 | 6 | 11 | 5 | 7 | 7 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |
| 7 | 1077 | David Miller | 63.35 | 21.41 | 25.65 | 8.97 | 7.32 | 7 | 9 | 6 | 8 | 9 | 3 | ROBUST_ACROSS_WEIGHTS |
| 8 | 8 | MS Dhoni | 62.51 | 23.01 | 23.3 | 7.34 | 8.86 | 8 | 7 | 8 | 9 | 8 | 2 | ROBUST_ACROSS_WEIGHTS |
| 9 | 3056 | Iftikhar Ahmed | 62.38 | 20.95 | 14.71 | 20 | 6.72 | 9 | 10 | 14 | 4 | 6 | 10 | RANKING_SENSITIVE_TO_WEIGHTS |
| 10 | 3916 | Jitesh Sharma | 62.01 | 23.47 | 27.27 | 4.12 | 7.15 | 10 | 8 | 7 | 12 | 14 | 7 | RANKING_SENSITIVE_TO_WEIGHTS |

---

## 8. Reproducibility & Verification Gates

- Pipeline execution: `.venv\Scripts\python scripts/compute_v3_rankings.py`
- Independent verification: `.venv\Scripts\python scripts/verify_v3_rankings.py`
- Automated test suite: `.venv\Scripts\python -m pytest tests/ -v` (**64 passed**)
