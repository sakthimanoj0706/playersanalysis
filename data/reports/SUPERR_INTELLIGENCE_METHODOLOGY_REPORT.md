# SupeRR Intelligence V3: Pressure Reliability Analytics & Player Scouting
## Official Technical Methodology Report & Evidence Dossier (V3.3 Goldfish TRIZ Edition)
**Target Event:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Scope:** Historical IPL & Men's T20I (2022 – 2026)  
**Authoritative Source Manifest:** `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`  
**System Status:** `V3.3 GOLDFISH TRIZ VERIFIED — PROVISIONAL MODEL`  

> **Mandatory Provisional Model Disclosure:**
> "Rankings are provisional. Batter ranks sensitive to scoring weights: #2, #3, #6, #7, #8; Bowler ranks sensitive to scoring weights: #4, #6, #8, #9, #10. The pressure classification uses the calibrated pre-delivery state & clean-channel chase-leverage heuristic (V3.3_GOLDFISH_CHASE_LEVERAGE). The new score has not yet undergone independent out-of-time validation."

---

## 1. Executive Summary & Governance Architecture

Standard cricket statistics (total runs, nominal strike rates, aggregate wickets) are heavily distorted by unconstrained play in low-leverage match situations. Under the Rajasthan Royals problem statement (*"Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels"*), pressure reliability evaluates how players sustain or elevate performance in high-pressure states relative to their personal normal baselines.

SupeRR Intelligence V3.3 enforces:
1. **Canonical Player Identity Resolution (`src/identity/player_identity.py`):** Consolidates verified multi-ID provider records before aggregation (`PLAYER_IDENTITY_CROSSWALK.csv`) while quarantining unresolved identity collisions.
2. **Pre-Delivery Calibrated Pressure & Clean-Channel Chase Leverage (`V3.3_GOLDFISH_CHASE_LEVERAGE`):** Mutually exclusive pre-delivery batting crisis and bowling defensive pressure tiers with zero post-delivery target leakage and explicit missing-feature quarantine (`batting_pressure_data_valid`, `bowling_pressure_data_valid`).
   - **Batting Crisis Pressure (`> 5.2` on `[0, 10]`):** Combines pre-delivery wickets fallen (`0.50 * w_before`, max `3.5`), recent 12-legal-ball wicket cluster (`2.2` for `>=2` wickets, `1.0` for `1` wicket), batter entry vulnerability (`1.5 * (1 - bf/6)` for first 6 balls), and dot-ball stagnation (`0.35 * consec_dots + 0.90 * (dots_12/12)`, max `1.8`), scaled by innings phase (`1.00x` Powerplay, `1.05x` Middle, `1.25x` Death) plus 2nd-innings clean chase leverage (`clean_rrr_deficit`). Yields **65 eligible batters** (`>= 60` crisis balls, `>= 5` crisis matches, `>= 60` normal balls, `>= 120` total balls).
   - **Bowling Defensive Pressure (`> 5.5` on `[0, 10]`):** Combines batting wickets in hand (`2.2` for `>=8`, `1.4` for `>=6`, `0.8` for `>=4`, `0.2` for `<4`), rebalanced phase pressure (`2.8` Death, `2.4` Powerplay, `1.0` Middle), opponent 12-legal-ball boundary momentum (`2.8` for `>=3` boundaries, `1.8` for `2`, `0.7` for `1`), strike-rotation pressure (`0.8 * (1 - dots_12/12)`), and 2nd-innings tight-chase leverage (`[-0.8, +1.0]`). Yields **197 eligible frontline bowlers** (`>= 120` crisis balls, `>= 5` crisis matches, `>= 120` total legal balls).
3. **Prior-Anchored Specialist Weighting (`PRIOR_ANCHORED_SPECIALIST`):** Bowlers with `< 100` normal balls are no longer hard-dropped; instead, their normal baseline shrinks toward the league phase average (`0.0`) and their maintenance weight (`w_maint = 0.35 * n_n / (n_n + 40)`) is smoothly reallocated to Absolute Performance and Consistency. Raw and capped (`[0.50, 1.50]`) maintenance ratios are reported separately for `>= 100` normal-ball baselines.
4. **Empirical Bayes Shrinkage & Match-Clustered Bootstrap CIs:** Priors estimated strictly on the eligible role-gated population ($K=25.0$ Normal shrinkage for batting SR toward cohort mean `132.1`; Method-of-Moments Beta-Binomial shrinkage for bowling wicket rate toward cohort mean `5.5%`) and 2,000-iteration match-clustered bootstrap 95% confidence intervals.

---

## 2. Dataset Scope & Data Governance Audit

The platform ingests **853 matches** (837 with ball-by-ball delivery logs) and **193,988 regular deliveries** (after quarantining 26 Super Over deliveries in innings 3 and 4).

1. **`extras1_runs` is Categorical, NOT a Run Count:** Source data integer codes (1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty) represent an enum codebook and are never summed as numeric runs.
2. **Clean-Channel Chase Leverage (`clean_rrr_deficit`):** Rather than summing `extras1_runs`, `innings_context.py` builds a clean lower-bound cumulative score (`runs + 1 * is_wide_or_overstep`) for both innings to derive a bias-cancelling 2nd-innings run-rate deficit without touching `extras1_runs` as a run count.
3. **Dismissal Attribution:** 581 non-bowler dismissals (573 run outs, 6 retired outs, 2 obstructing the field) are excluded from bowler wickets. Partner run-outs are excluded from striker batting average denominators.
4. **Wicket Hazard Model Governance (`EXPERIMENTAL_NOT_USED_FOR_RANKING`):**
   - The discrete-time logistic hazard model, hierarchical joint model, and LightGBM challenger are strictly marked **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** and are not used as production ranking components.

---

## 3. Provisional Fixed-Weight Score Formulation (`PROVISIONAL_FIXED_WEIGHT_SCORE`)

$$\text{Score}_{\text{provisional}} = 100 \times \left( w_M M_{\text{norm}} + w_A A_{\text{norm}} + w_C C_{\text{norm}} + 0.10 S_{\text{norm}} \right)$$

1. **Cohort-Calibrated Performance Maintenance ($M$, base 35%):** Uses phase-adjusted, dismissal-weighted (`lambda_wkt = 6.0`) batting run-value residuals (`did_bat_maintenance`) and bowling control residuals (`did_bowl_maintenance`) via `phase_adjusted_dual_arm_did(..., cohort_calibrated=True)`. Fitting the empirical regression-to-the-mean slope $\beta \in [0.25, 0.75]$ prevents elite normal-overs performers (e.g., Jasprit Bumrah) from being penalized for high normal baselines.
2. **Absolute Pressure Performance ($A$, base 35%):** Batting uses phase-adjusted crisis run-value delta (`crisis_delta_rv`); Bowling uses `abs_bowl_score = 0.60 * crisis_delta_ctrl + 0.40 * (10 * crisis_delta_wkt)`.
3. **Pure-Dispersion Match Consistency ($C$, base 20%):** $\exp(-\sigma_{w,i} / s) \cdot \sqrt{m_i / (m_i + 3)}$ on EB-shrunk match residuals ($s=55$ batting, $s=22$ bowling), eliminating level double-counting.
4. **Sample Size Confidence ($S$, 10%):** $\min(1.0, \ln(1 + n_i) / \ln(1 + 250))$ for batting and $\min(1.0, \ln(1 + n_i) / \ln(1 + 600))$ for bowling. All non-sample components are normalized via 2.5%/97.5% winsorized z-scores mapped to $[0, 1]$.

---

## 4. Authoritative Top 10 Batters Under Crisis Pressure (`data/outputs/v3/TOP_10_BATTERS.csv`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | crisis_matches | crisis_sr | norm_sr | raw_sr_maintenance | sr_maintenance | is_maintenance_capped | shrunk_crisis_sr | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status | performance_anomaly_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3647 | Shreyas Iyer | BAT_SPECIALIST | 89 | 34 | 166.2921 | 152.5037 | 1.09 | 1.09 | False | 158.79 | 0.5124 | 78.55 | 141.03 | 197.34 | ROBUST_ACROSS_WEIGHTS | NONE |
| 2 | 4708 | Rinku Singh | BAT_SPECIALIST | 365 | 67 | 160.8219 | 161.191 | 0.998 | 0.998 | False | 158.98 | 0.391 | 76.62 | 138.59 | 183.13 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 3 | 3125 | Nicholas Pooran | BAT_SPECIALIST | 190 | 47 | 160.5263 | 167.8803 | 0.956 | 0.956 | False | 157.22 | 0.4029 | 75.93 | 125.95 | 193.98 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 4 | 3916 | Jitesh Sharma | BAT_SPECIALIST | 225 | 52 | 161.7778 | 166.343 | 0.973 | 0.973 | False | 158.81 | 0.4367 | 74.84 | 136.55 | 188 | ROBUST_ACROSS_WEIGHTS | NONE |
| 5 | 1699 | Suryakumar Yadav | BAT_SPECIALIST | 157 | 50 | 164.9682 | 170.7402 | 0.966 | 0.966 | False | 160.45 | 0.4425 | 73.17 | 136.52 | 191.72 | ROBUST_ACROSS_WEIGHTS | NONE |
| 6 | 6448 | Ibrahim Zadran | BAT_SPECIALIST | 99 | 9 | 118.1818 | 117.4725 | 1.006 | 1.006 | False | 120.99 | 0.608 | 73.15 | 94.44 | 141.8 | RANKING_SENSITIVE_TO_WEIGHTS | CRISIS_SR_BELOW_COHORT_MEAN |
| 7 | 3056 | Iftikhar Ahmed | BAT_PRIMARY_AR | 112 | 24 | 155.3571 | 120.4545 | 1.29 | 1.29 | False | 151.11 | 0.3912 | 72.92 | 106.94 | 195.24 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 8 | 796 | Matthew Wade | BAT_SPECIALIST | 159 | 19 | 130.1887 | 131.6667 | 0.989 | 0.989 | False | 130.45 | 0.4991 | 72.39 | 103.28 | 153.2 | RANKING_SENSITIVE_TO_WEIGHTS | CRISIS_SR_BELOW_COHORT_MEAN |
| 9 | 7897 | Tilak Varma | BAT_PRIMARY_AR | 307 | 67 | 142.3453 | 143.0311 | 0.995 | 0.995 | False | 141.57 | 0.4589 | 71.72 | 119.8 | 166.46 | ROBUST_ACROSS_WEIGHTS | NONE |
| 10 | 6460 | Ayush Badoni | BAT_PRIMARY_AR | 184 | 39 | 144.0217 | 149.1429 | 0.966 | 0.966 | False | 142.6 | 0.4574 | 70.48 | 117.06 | 168.57 | ROBUST_ACROSS_WEIGHTS | NONE |

### 4.1 Individual Player Selection Rationales — Top 10 Batters
- **#1 Shreyas Iyer (`canonical_player_id=3647`, `BAT_SPECIALIST`):** Faced **89 crisis balls** across **34 crisis matches** (normal baseline: 1358 balls across 88 matches). Recorded a **166.29 Crisis SR** vs **152.50 Normal SR**, achieving a **1.090x Strike-Rate Maintenance ratio** (raw: 1.090x), **158.79 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[141.03, 197.34]`), and **0.5124 Match Consistency Score**. Component Breakdown: `Maint(35%)=26.02 + Abs(35%)=26.32 + Cons(20%)=18.07 + Sample(10%)=8.14 = 78.55` (`ROBUST_ACROSS_WEIGHTS`).
- **#2 Rinku Singh (`canonical_player_id=4708`, `BAT_SPECIALIST`):** Faced **365 crisis balls** across **67 crisis matches** (normal baseline: 487 balls across 48 matches). Recorded a **160.82 Crisis SR** vs **161.19 Normal SR**, achieving a **0.998x Strike-Rate Maintenance ratio** (raw: 0.998x), **158.98 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[138.59, 183.13]`), and **0.3910 Match Consistency Score**. Component Breakdown: `Maint(35%)=29.24 + Abs(35%)=30.74 + Cons(20%)=6.64 + Sample(10%)=10.00 = 76.62` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#3 Nicholas Pooran (`canonical_player_id=3125`, `BAT_SPECIALIST`):** Faced **190 crisis balls** across **47 crisis matches** (normal baseline: 1236 balls across 97 matches). Recorded a **160.53 Crisis SR** vs **167.88 Normal SR**, achieving a **0.956x Strike-Rate Maintenance ratio** (raw: 0.956x), **157.22 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[125.95, 193.98]`), and **0.4029 Match Consistency Score**. Component Breakdown: `Maint(35%)=28.61 + Abs(35%)=30.05 + Cons(20%)=7.76 + Sample(10%)=9.51 = 75.93` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#4 Jitesh Sharma (`canonical_player_id=3916`, `BAT_SPECIALIST`):** Faced **225 crisis balls** across **52 crisis matches** (normal baseline: 309 balls across 42 matches). Recorded a **161.78 Crisis SR** vs **166.34 Normal SR**, achieving a **0.973x Strike-Rate Maintenance ratio** (raw: 0.973x), **158.81 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[136.55, 188.00]`), and **0.4367 Match Consistency Score**. Component Breakdown: `Maint(35%)=28.33 + Abs(35%)=25.76 + Cons(20%)=10.94 + Sample(10%)=9.81 = 74.84` (`ROBUST_ACROSS_WEIGHTS`).
- **#5 Suryakumar Yadav (`canonical_player_id=1699`, `BAT_SPECIALIST`):** Faced **157 crisis balls** across **50 crisis matches** (normal baseline: 2013 balls across 123 matches). Recorded a **164.97 Crisis SR** vs **170.74 Normal SR**, achieving a **0.966x Strike-Rate Maintenance ratio** (raw: 0.966x), **160.45 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[136.52, 191.72]`), and **0.4425 Match Consistency Score**. Component Breakdown: `Maint(35%)=24.76 + Abs(35%)=27.76 + Cons(20%)=11.49 + Sample(10%)=9.16 = 73.17` (`ROBUST_ACROSS_WEIGHTS`).
- **#6 Ibrahim Zadran (`canonical_player_id=6448`, `BAT_SPECIALIST`):** Faced **99 crisis balls** across **9 crisis matches** (normal baseline: 910 balls across 46 matches). Recorded a **118.18 Crisis SR** vs **117.47 Normal SR**, achieving a **1.006x Strike-Rate Maintenance ratio** (raw: 1.006x), **120.99 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[94.44, 141.80]`), and **0.6080 Match Consistency Score**. Component Breakdown: `CRISIS_SR_BELOW_COHORT_MEAN (118.18 vs cohort mean 132.10): Maint(35%)=23.95 + Abs(35%)=20.87 + Cons(20%)=20.00 + Sample(10%)=8.33 = 73.15; elevated by multi-match consistency (0.6080 -> 20.00 pts) and positive personal baseline maintenance (1.006x over 117.47 norm SR -> 23.95 pts) despite low absolute crisis SR contribution (20.87 pts).` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#7 Iftikhar Ahmed (`canonical_player_id=3056`, `BAT_PRIMARY_AR`):** Faced **112 crisis balls** across **24 crisis matches** (normal baseline: 220 balls across 22 matches). Recorded a **155.36 Crisis SR** vs **120.45 Normal SR**, achieving a **1.290x Strike-Rate Maintenance ratio** (raw: 1.290x), **151.11 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[106.94, 195.24]`), and **0.3912 Match Consistency Score**. Component Breakdown: `Maint(35%)=30.60 + Abs(35%)=27.10 + Cons(20%)=6.66 + Sample(10%)=8.56 = 72.92` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#8 Matthew Wade (`canonical_player_id=796`, `BAT_SPECIALIST`):** Faced **159 crisis balls** across **19 crisis matches** (normal baseline: 180 balls across 18 matches). Recorded a **130.19 Crisis SR** vs **131.67 Normal SR**, achieving a **0.989x Strike-Rate Maintenance ratio** (raw: 0.989x), **130.45 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[103.28, 153.20]`), and **0.4991 Match Consistency Score**. Component Breakdown: `CRISIS_SR_BELOW_COHORT_MEAN (130.19 vs cohort mean 132.10): Maint(35%)=24.76 + Abs(35%)=21.63 + Cons(20%)=16.82 + Sample(10%)=9.18 = 72.39; elevated by multi-match consistency (0.4991 -> 16.82 pts) and positive personal baseline maintenance (0.989x over 131.67 norm SR -> 24.76 pts) despite low absolute crisis SR contribution (21.63 pts).` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#9 Tilak Varma (`canonical_player_id=7897`, `BAT_PRIMARY_AR`):** Faced **307 crisis balls** across **67 crisis matches** (normal baseline: 1478 balls across 103 matches). Recorded a **142.35 Crisis SR** vs **143.03 Normal SR**, achieving a **0.995x Strike-Rate Maintenance ratio** (raw: 0.995x), **141.57 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[119.80, 166.46]`), and **0.4589 Match Consistency Score**. Component Breakdown: `Maint(35%)=24.75 + Abs(35%)=23.94 + Cons(20%)=13.03 + Sample(10%)=10.00 = 71.72` (`ROBUST_ACROSS_WEIGHTS`).
- **#10 Ayush Badoni (`canonical_player_id=6460`, `BAT_PRIMARY_AR`):** Faced **184 crisis balls** across **39 crisis matches** (normal baseline: 350 balls across 36 matches). Recorded a **144.02 Crisis SR** vs **149.14 Normal SR**, achieving a **0.966x Strike-Rate Maintenance ratio** (raw: 0.966x), **142.60 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[117.06, 168.57]`), and **0.4574 Match Consistency Score**. Component Breakdown: `Maint(35%)=25.44 + Abs(35%)=22.70 + Cons(20%)=12.89 + Sample(10%)=9.45 = 70.48` (`ROBUST_ACROSS_WEIGHTS`).

---

## 5. Authoritative Top 10 Bowlers Under Defensive Pressure (`data/outputs/v3/TOP_10_BOWLERS.csv`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | crisis_matches | norm_balls | norm_baseline_status | crisis_dot_pct | norm_dot_pct | raw_dot_maintenance | capped_dot_maintenance | is_maintenance_capped | crisis_wicket_rate | shrunk_crisis_wr | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3578 | Imad Wasim | BOWL_PRIMARY_AR | 129 | 10 | 68 | PRIOR_ANCHORED_SPECIALIST | 41.8605 | 48.5294 | 0.863 | NaN | False | 6.9767 | 6.33 | 0.6133 | 90.81 | 35.06 | 47.76 | ROBUST_ACROSS_WEIGHTS |
| 2 | 28756 | Haider Ali (UAE) | BOWL_SPECIALIST | 146 | 11 | 79 | PRIOR_ANCHORED_SPECIALIST | 50 | 37.9747 | 1.317 | NaN | False | 7.5342 | 6.71 | 0.5778 | 90.63 | 41.51 | 61.74 | ROBUST_ACROSS_WEIGHTS |
| 3 | 5750 | Ehsan Khan | BOWL_SPECIALIST | 141 | 8 | 12 | PRIOR_ANCHORED_SPECIALIST | 37.5887 | 33.3333 | 1.128 | NaN | False | 7.0922 | 6.43 | 0.6473 | 88.65 | 28.47 | 48.78 | ROBUST_ACROSS_WEIGHTS |
| 4 | 722 | Liam Dawson | BOWL_SPECIALIST | 204 | 19 | 129 | VALID_NORMAL_BASELINE | 37.7451 | 35.6589 | 1.059 | 1.059 | False | 6.3725 | 6.09 | 0.6609 | 88.56 | 31.91 | 45 | RANKING_SENSITIVE_TO_WEIGHTS |
| 5 | 7741 | Gareth Delany | BOWL_PRIMARY_AR | 210 | 27 | 189 | VALID_NORMAL_BASELINE | 39.0476 | 31.2169 | 1.251 | 1.251 | False | 7.1429 | 6.61 | 0.5569 | 87.15 | 32.18 | 47.87 | ROBUST_ACROSS_WEIGHTS |
| 6 | 3641 | Ben Dwarshuis | BOWL_SPECIALIST | 204 | 14 | 45 | PRIOR_ANCHORED_SPECIALIST | 41.6667 | 20 | 2.083 | NaN | False | 9.8039 | 8.39 | 0.5446 | 84.04 | 32.29 | 50.24 | RANKING_SENSITIVE_TO_WEIGHTS |
| 7 | 3629 | Corbin Bosch | BOWL_PRIMARY_AR | 208 | 18 | 76 | PRIOR_ANCHORED_SPECIALIST | 42.3077 | 48.6842 | 0.869 | NaN | False | 9.6154 | 8.28 | 0.5668 | 81.77 | 34.34 | 48.88 | ROBUST_ACROSS_WEIGHTS |
| 8 | 161 | Dwayne Bravo | BOWL_SPECIALIST | 135 | 9 | 39 | PRIOR_ANCHORED_SPECIALIST | 34.0741 | 30.7692 | 1.107 | NaN | False | 9.6296 | 7.87 | 0.515 | 78.68 | 25.6 | 45.19 | RANKING_SENSITIVE_TO_WEIGHTS |
| 9 | 6450 | Mujeeb Ur Rahman | BOWL_SPECIALIST | 517 | 38 | 190 | VALID_NORMAL_BASELINE | 45.0677 | 43.1579 | 1.044 | 1.044 | False | 5.2224 | 5.27 | 0.522 | 78.57 | 39.76 | 50.1 | RANKING_SENSITIVE_TO_WEIGHTS |
| 10 | 7920 | Nathan Ellis | BOWL_SPECIALIST | 591 | 42 | 177 | VALID_NORMAL_BASELINE | 35.1946 | 39.548 | 0.89 | 0.89 | False | 6.7682 | 6.59 | 0.654 | 78.23 | 31.78 | 38.74 | RANKING_SENSITIVE_TO_WEIGHTS |

### 5.1 Individual Player Selection Rationales — Top 10 Bowlers
- **#1 Imad Wasim (`canonical_player_id=3578`, `BOWL_PRIMARY_AR`):** Bowled **129 crisis legal balls** across **10 crisis matches** (normal baseline: 68 legal balls across 10 matches, `PRIOR_ANCHORED_SPECIALIST`). Recorded a **41.86% Crisis Dot-Ball %** vs **48.53% Normal Dot-Ball %**, achieving a **N/A (Prior-Anchored Specialist)** (raw: 0.863x), **6.98% Raw Crisis Wicket Rate** (**6.33% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[35.06%, 47.76%]`), and **0.6133 Match Consistency Score**. Component Breakdown: `Maint(22%)=20.50 + Abs(43%)=42.03 + Cons(25%)=20.67 + Sample(10%)=7.61 = 90.81` (`ROBUST_ACROSS_WEIGHTS`).
- **#2 Haider Ali (UAE) (`canonical_player_id=28756`, `BOWL_SPECIALIST`):** Bowled **146 crisis legal balls** across **11 crisis matches** (normal baseline: 79 legal balls across 9 matches, `PRIOR_ANCHORED_SPECIALIST`). Recorded a **50.00% Crisis Dot-Ball %** vs **37.97% Normal Dot-Ball %**, achieving a **N/A (Prior-Anchored Specialist)** (raw: 1.317x), **7.53% Raw Crisis Wicket Rate** (**6.71% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[41.51%, 61.74%]`), and **0.5778 Match Consistency Score**. Component Breakdown: `Maint(23%)=23.24 + Abs(42%)=42.49 + Cons(24%)=17.10 + Sample(10%)=7.80 = 90.63` (`ROBUST_ACROSS_WEIGHTS`).
- **#3 Ehsan Khan (`canonical_player_id=5750`, `BOWL_SPECIALIST`):** Bowled **141 crisis legal balls** across **8 crisis matches** (normal baseline: 12 legal balls across 3 matches, `PRIOR_ANCHORED_SPECIALIST`). Recorded a **37.59% Crisis Dot-Ball %** vs **33.33% Normal Dot-Ball %**, achieving a **N/A (Prior-Anchored Specialist)** (raw: 1.128x), **7.09% Raw Crisis Wicket Rate** (**6.43% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[28.47%, 48.78%]`), and **0.6473 Match Consistency Score**. Component Breakdown: `Maint(8%)=8.08 + Abs(52%)=44.14 + Cons(30%)=28.69 + Sample(10%)=7.74 = 88.65` (`ROBUST_ACROSS_WEIGHTS`).
- **#4 Liam Dawson (`canonical_player_id=722`, `BOWL_SPECIALIST`):** Bowled **204 crisis legal balls** across **19 crisis matches** (normal baseline: 129 legal balls across 16 matches, `VALID_NORMAL_BASELINE`). Recorded a **37.75% Crisis Dot-Ball %** vs **35.66% Normal Dot-Ball %**, achieving a **1.059x Capped Dot-Ball Maintenance ratio** (raw: 1.059x), **6.37% Raw Crisis Wicket Rate** (**6.09% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[31.91%, 45.00%]`), and **0.6609 Match Consistency Score**. Component Breakdown: `Maint(35%)=32.70 + Abs(35%)=27.54 + Cons(20%)=20.00 + Sample(10%)=8.32 = 88.56` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#5 Gareth Delany (`canonical_player_id=7741`, `BOWL_PRIMARY_AR`):** Bowled **210 crisis legal balls** across **27 crisis matches** (normal baseline: 189 legal balls across 27 matches, `VALID_NORMAL_BASELINE`). Recorded a **39.05% Crisis Dot-Ball %** vs **31.22% Normal Dot-Ball %**, achieving a **1.251x Capped Dot-Ball Maintenance ratio** (raw: 1.251x), **7.14% Raw Crisis Wicket Rate** (**6.61% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[32.18%, 47.87%]`), and **0.5569 Match Consistency Score**. Component Breakdown: `Maint(35%)=34.75 + Abs(35%)=31.51 + Cons(20%)=12.53 + Sample(10%)=8.36 = 87.15` (`ROBUST_ACROSS_WEIGHTS`).
- **#6 Ben Dwarshuis (`canonical_player_id=3641`, `BOWL_SPECIALIST`):** Bowled **204 crisis legal balls** across **14 crisis matches** (normal baseline: 45 legal balls across 10 matches, `PRIOR_ANCHORED_SPECIALIST`). Recorded a **41.67% Crisis Dot-Ball %** vs **20.00% Normal Dot-Ball %**, achieving a **N/A (Prior-Anchored Specialist)** (raw: 2.083x), **9.80% Raw Crisis Wicket Rate** (**8.39% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[32.29%, 50.24%]`), and **0.5446 Match Consistency Score**. Component Breakdown: `Maint(19%)=15.15 + Abs(45%)=45.48 + Cons(26%)=15.09 + Sample(10%)=8.32 = 84.04` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#7 Corbin Bosch (`canonical_player_id=3629`, `BOWL_PRIMARY_AR`):** Bowled **208 crisis legal balls** across **18 crisis matches** (normal baseline: 76 legal balls across 13 matches, `PRIOR_ANCHORED_SPECIALIST`). Recorded a **42.31% Crisis Dot-Ball %** vs **48.68% Normal Dot-Ball %**, achieving a **N/A (Prior-Anchored Specialist)** (raw: 0.869x), **9.62% Raw Crisis Wicket Rate** (**8.28% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[34.34%, 48.88%]`), and **0.5668 Match Consistency Score**. Component Breakdown: `Maint(23%)=15.11 + Abs(43%)=42.13 + Cons(24%)=16.18 + Sample(10%)=8.35 = 81.77` (`ROBUST_ACROSS_WEIGHTS`).
- **#8 Dwayne Bravo (`canonical_player_id=161`, `BOWL_SPECIALIST`):** Bowled **135 crisis legal balls** across **9 crisis matches** (normal baseline: 39 legal balls across 6 matches, `PRIOR_ANCHORED_SPECIALIST`). Recorded a **34.07% Crisis Dot-Ball %** vs **30.77% Normal Dot-Ball %**, achieving a **N/A (Prior-Anchored Specialist)** (raw: 1.107x), **9.63% Raw Crisis Wicket Rate** (**7.87% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[25.60%, 45.19%]`), and **0.5150 Match Consistency Score**. Component Breakdown: `Maint(17%)=15.07 + Abs(46%)=43.49 + Cons(26%)=12.44 + Sample(10%)=7.68 = 78.68` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#9 Mujeeb Ur Rahman (`canonical_player_id=6450`, `BOWL_SPECIALIST`):** Bowled **517 crisis legal balls** across **38 crisis matches** (normal baseline: 190 legal balls across 22 matches, `VALID_NORMAL_BASELINE`). Recorded a **45.07% Crisis Dot-Ball %** vs **43.16% Normal Dot-Ball %**, achieving a **1.044x Capped Dot-Ball Maintenance ratio** (raw: 1.044x), **5.22% Raw Crisis Wicket Rate** (**5.27% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[39.76%, 50.10%]`), and **0.5220 Match Consistency Score**. Component Breakdown: `Maint(35%)=32.19 + Abs(35%)=26.68 + Cons(20%)=9.93 + Sample(10%)=9.77 = 78.57` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#10 Nathan Ellis (`canonical_player_id=7920`, `BOWL_SPECIALIST`):** Bowled **591 crisis legal balls** across **42 crisis matches** (normal baseline: 177 legal balls across 28 matches, `VALID_NORMAL_BASELINE`). Recorded a **35.19% Crisis Dot-Ball %** vs **39.55% Normal Dot-Ball %**, achieving a **0.890x Capped Dot-Ball Maintenance ratio** (raw: 0.890x), **6.77% Raw Crisis Wicket Rate** (**6.59% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[31.78%, 38.74%]`), and **0.6540 Match Consistency Score**. Component Breakdown: `Maint(35%)=23.49 + Abs(35%)=25.00 + Cons(20%)=19.76 + Sample(10%)=9.98 = 78.23` (`RANKING_SENSITIVE_TO_WEIGHTS`).

---

## 6. Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

### 6.1 Batting Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 60, total_balls >= 120`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 5 | 95 | 244 | 10 | 6 | 0.4286 | 2.83 | 4 | Jos Buttler, William Jacks, Sam Billings, Vijay Shankar | Iftikhar Ahmed, Matthew Wade, Tilak Varma, Ayush Badoni |
| 60 | 5 | 65 | 239 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 80 | 5 | 60 | 226 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 100 | 5 | 52 | 209 | 10 | 8 | 0.6667 | 1.6 | 2 | Naman Dhir, Hardik Pandya | Shreyas Iyer, Ibrahim Zadran |
| 150 | 5 | 34 | 171 | 10 | 7 | 0.5385 | 2.5 | 4 | Hardik Pandya, Marcus Stoinis, Rahul Tewatia | Shreyas Iyer, Ibrahim Zadran, Iftikhar Ahmed |
| 200 | 5 | 18 | 150 | 10 | 3 | 0.1765 | 8.1 | 19 | Hardik Pandya, Marcus Stoinis, Rahul Tewatia, Tim David, David Miller, Shashank Singh, Shivam Dube | Shreyas Iyer, Nicholas Pooran, Suryakumar Yadav, Ibrahim Zadran, Iftikhar Ahmed, Matthew Wade, Ayush Badoni |
| 250 | 5 | 10 | 126 | 10 | 2 | 0.1111 | 18.9 | 44 | Marcus Stoinis, Rahul Tewatia, Tim David, Dinesh Karthik, Andre Russell, Rovman Powell, Shimron Hetmyer, Dasun Shanaka | Shreyas Iyer, Nicholas Pooran, Jitesh Sharma, Suryakumar Yadav, Ibrahim Zadran, Iftikhar Ahmed, Matthew Wade, Ayush Badoni |

### 6.2 Bowling Primary Crisis-Ball Sweep (`crisis_matches >= 5, total_legal_balls >= 120`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 5 | 95 | 95 | 10 | 4 | 0.25 | 7 | 14 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |
| 60 | 5 | 65 | 95 | 10 | 4 | 0.25 | 7 | 14 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |
| 80 | 5 | 60 | 95 | 10 | 4 | 0.25 | 7 | 14 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |
| 100 | 5 | 52 | 94 | 10 | 4 | 0.25 | 7 | 14 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |
| 120 | 5 | 42 | 94 | 10 | 4 | 0.25 | 7 | 14 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |
| 150 | 5 | 34 | 94 | 10 | 4 | 0.25 | 7 | 14 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |
| 200 | 5 | 18 | 90 | 10 | 4 | 0.25 | 7 | 14 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |
| 250 | 5 | 10 | 85 | 10 | 2 | 0.1111 | 11.7 | 19 | Haris Rauf, Shoriful Islam, Matheesha Pathirana, Joshua Little, Taskin Ahmed, Mohammad Nawaz, Wanindu Hasaranga, Shaheen Afridi | Imad Wasim, Haider Ali (UAE), Ehsan Khan, Liam Dawson, Gareth Delany, Ben Dwarshuis, Corbin Bosch, Dwayne Bravo |

---

## 7. Technical Glossary
- **`did_bat_maintenance` / `did_bowl_maintenance`:** Cohort-calibrated Difference-in-Differences residual comparing shrunk crisis excess against expected crisis excess given the player's normal baseline.
- **`abs_bowl_score`:** Weighted combination of phase-adjusted crisis run-control excess (`0.60 * crisis_delta_ctrl`) and crisis wicket-taking excess (`0.40 * 10 * crisis_delta_wkt`).
- **`PRIOR_ANCHORED_SPECIALIST`:** Bowler with `< 100` normal balls whose baseline is anchored at the league phase average (`0.0`) with maintenance weight smoothly reallocated to Absolute Performance and Consistency.
- **`lambda_wkt = 6.0`:** Dismissal-weighting penalty applied in batting run-value residuals (`r_bat = r_sr + 6.0 * r_surv`).

---

## 8. Weight Sensitivity Analysis Across 5 Prespecified Configurations (`RANKING_WEIGHT_SENSITIVITY.csv`)

### 8.1 Batting Weight Sensitivity (Top 10)
| provisional_rank | canonical_player_id | player_name | provisional_fixed_weight_score | contrib_maint | contrib_abs | contrib_cons | contrib_sample | rank_balanced_default | rank_maintenance_heavy | rank_absolute_heavy | rank_consistency_heavy | rank_equal_weights | max_rank_shift | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3647 | Shreyas Iyer | 78.55 | 26.02 | 26.32 | 18.07 | 8.14 | 1 | 2 | 3 | 1 | 1 | 2 | ROBUST_ACROSS_WEIGHTS |
| 2 | 4708 | Rinku Singh | 76.62 | 29.24 | 30.74 | 6.64 | 10 | 2 | 1 | 1 | 7 | 5 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |
| 3 | 3125 | Nicholas Pooran | 75.93 | 28.61 | 30.05 | 7.76 | 9.51 | 3 | 3 | 2 | 5 | 7 | 5 | RANKING_SENSITIVE_TO_WEIGHTS |
| 4 | 3916 | Jitesh Sharma | 74.84 | 28.33 | 25.76 | 10.94 | 9.81 | 4 | 4 | 5 | 4 | 4 | 1 | ROBUST_ACROSS_WEIGHTS |
| 5 | 1699 | Suryakumar Yadav | 73.17 | 24.76 | 27.76 | 11.49 | 9.16 | 5 | 6 | 4 | 6 | 8 | 4 | ROBUST_ACROSS_WEIGHTS |
| 6 | 6448 | Ibrahim Zadran | 73.15 | 23.95 | 20.87 | 20 | 8.33 | 6 | 9 | 10 | 2 | 2 | 8 | RANKING_SENSITIVE_TO_WEIGHTS |
| 7 | 3056 | Iftikhar Ahmed | 72.92 | 30.6 | 27.1 | 6.66 | 8.56 | 7 | 5 | 6 | 11 | 12 | 7 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 796 | Matthew Wade | 72.39 | 24.76 | 21.63 | 16.82 | 9.18 | 8 | 7 | 9 | 3 | 3 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |
| 9 | 7897 | Tilak Varma | 71.72 | 24.75 | 23.94 | 13.03 | 10 | 9 | 10 | 7 | 8 | 6 | 4 | ROBUST_ACROSS_WEIGHTS |
| 10 | 6460 | Ayush Badoni | 70.48 | 25.44 | 22.7 | 12.89 | 9.45 | 10 | 12 | 12 | 9 | 9 | 3 | ROBUST_ACROSS_WEIGHTS |

### 8.2 Bowling Weight Sensitivity (Top 10)
| provisional_rank | canonical_player_id | player_name | provisional_fixed_weight_score | contrib_maint | contrib_abs | contrib_cons | contrib_sample | rank_balanced_default | rank_maintenance_heavy | rank_absolute_heavy | rank_consistency_heavy | rank_equal_weights | max_rank_shift | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3578 | Imad Wasim | 90.81 | 20.5 | 42.03 | 20.67 | 7.61 | 1 | 2 | 2 | 3 | 3 | 2 | ROBUST_ACROSS_WEIGHTS |
| 2 | 28756 | Haider Ali (UAE) | 90.63 | 23.24 | 42.49 | 17.1 | 7.8 | 2 | 1 | 1 | 4 | 4 | 3 | ROBUST_ACROSS_WEIGHTS |
| 3 | 5750 | Ehsan Khan | 88.65 | 8.08 | 44.14 | 28.69 | 7.74 | 3 | 5 | 5 | 2 | 2 | 3 | ROBUST_ACROSS_WEIGHTS |
| 4 | 722 | Liam Dawson | 88.56 | 32.7 | 27.54 | 20 | 8.32 | 4 | 4 | 7 | 1 | 1 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |
| 5 | 7741 | Gareth Delany | 87.15 | 34.75 | 31.51 | 12.53 | 8.36 | 5 | 3 | 4 | 5 | 6 | 3 | ROBUST_ACROSS_WEIGHTS |
| 6 | 3641 | Ben Dwarshuis | 84.04 | 15.15 | 45.48 | 15.09 | 8.32 | 6 | 6 | 3 | 7 | 9 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |
| 7 | 3629 | Corbin Bosch | 81.77 | 15.11 | 42.13 | 16.18 | 8.35 | 7 | 8 | 6 | 8 | 10 | 4 | ROBUST_ACROSS_WEIGHTS |
| 8 | 161 | Dwayne Bravo | 78.68 | 15.07 | 43.49 | 12.44 | 7.68 | 8 | 9 | 8 | 15 | 20 | 12 | RANKING_SENSITIVE_TO_WEIGHTS |
| 9 | 6450 | Mujeeb Ur Rahman | 78.57 | 32.19 | 26.68 | 9.93 | 9.77 | 9 | 7 | 15 | 11 | 11 | 8 | RANKING_SENSITIVE_TO_WEIGHTS |
| 10 | 7920 | Nathan Ellis | 78.23 | 23.49 | 25 | 19.76 | 9.98 | 10 | 12 | 16 | 6 | 5 | 11 | RANKING_SENSITIVE_TO_WEIGHTS |

---

## 9. Reproducibility & Verification Gates

- Pipeline execution: `.venv\Scripts\python scripts/compute_v3_rankings.py`
- Independent verification: `.venv\Scripts\python scripts/verify_v3_rankings.py`
- Automated test suite: `.venv\Scripts\python -m pytest tests/ -v` (**65 passed**)
