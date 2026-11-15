# SupeRR Intelligence V3: Pressure Reliability Analytics & Player Scouting
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

$$\text{Score}_{\text{provisional}} = 100 \times \left( 0.35 M_{\text{norm}} + 0.35 A_{\text{norm}} + 0.20 C_{\text{norm}} + 0.10 S_{\text{norm}} \right)$$

1. **Performance Maintenance ($M$, 35%):**
   - Batting: $\text{SR}_{\text{crisis}} / \text{SR}_{\text{norm}}$ for batters with $\ge 30$ normal balls. Raw (`raw_sr_maintenance`) and capped (`capped_sr_maintenance` in $[0.50, 1.50]$) ratios are reported separately alongside `is_maintenance_capped`.
   - Bowling: $\text{Dot}_{\text{crisis}} / \text{Dot}_{\text{norm}}$ strictly for bowlers with $\ge 100$ normal balls (`MIN_NORMAL_BALLS = 100`). Bowlers with $< 100$ normal balls are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT`, receive `NaN` for `capped_dot_maintenance`, and are excluded from composite ranking.
2. **Absolute Pressure Performance ($A$, 35%):**
   - Batting: Fixed-$K$ Normal shrinkage ($K = 25.0$) toward the eligible batting cohort mean (`130.13` SR).
   - Bowling: Beta-Binomial Empirical Bayes shrinkage toward the eligible bowling cohort mean (`6.07%` wicket rate).
3. **Empirical Bayes Match-Shrunk Ball-Weighted Consistency ($C$, 20%):**
   - Each player's per-match crisis rate $r_{ij}$ (on $n_{ij}$ crisis balls in match $j$) is shrunk toward the player's overall crisis rate $\bar{r}_i$ via $w_{ij} = n_{ij} / (n_{ij} + 6)$: $\tilde{r}_{ij} = w_{ij} r_{ij} + (1 - w_{ij}) \bar{r}_i$.
   - Combining low ball-weighted coefficient of variation ($\exp(-\text{CV}_{\text{weighted}}( \tilde{r}_{ij} ))$) with ball-weighted match delivery success rate ($S_i$, fraction of crisis balls in matches achieving $\tilde{r}_{ij} \ge \max(125.0, 0.90 \cdot \text{SR}_{\text{norm}})$ for batters or $\tilde{r}_{ij} \ge \max(38.0\%, 0.92 \cdot \text{Dot}_{\text{norm}})$ for bowlers):
     $$\text{Consistency}_i = \left( \alpha \exp(-\text{CV}_{w,i}) + (1 - \alpha) S_i \right) \cdot \sqrt{\frac{m_i}{m_i + 3}}$$
     where $\alpha = 0.55$ for batters and $\alpha = 0.40$ for bowlers.
4. **Sample Size Confidence ($S$, 10%):**
   - Batting: $\min(1.0, \ln(1 + n_i) / \ln(1 + 250))$.
   - Bowling: $\min(1.0, \ln(1 + n_i) / \ln(1 + 600))$, preserving differentiation across frontline bowling crisis workloads from 120 to 600+ legal deliveries.

---

## 4. Authoritative Top 10 Batters Under Crisis Pressure (`data/outputs/v3/TOP_10_BATTERS.csv`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | crisis_matches | crisis_sr | norm_sr | raw_sr_maintenance | sr_maintenance | is_maintenance_capped | shrunk_crisis_sr | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status | performance_anomaly_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8101 | Ashutosh Sharma | BAT_SPECIALIST | 148 | 26 | 168.9189 | 125.5814 | 1.345 | 1.345 | False | 163.31 | 0.7457 | 93.88 | 126.66 | 213.61 | ROBUST_ACROSS_WEIGHTS | NONE |
| 2 | 20006 | Ramandeep Singh | BAT_PRIMARY_AR | 115 | 24 | 164.3478 | 125.641 | 1.308 | 1.308 | False | 158.24 | 0.6978 | 87.73 | 118.52 | 213.06 | ROBUST_ACROSS_WEIGHTS | NONE |
| 3 | 3647 | Shreyas Iyer | BAT_SPECIALIST | 65 | 29 | 170.7692 | 151.6106 | 1.126 | 1.126 | False | 159.48 | 0.874 | 86.82 | 142.18 | 205.17 | ROBUST_ACROSS_WEIGHTS | NONE |
| 4 | 6272 | William Jacks | BAT_PRIMARY_AR | 41 | 15 | 173.1707 | 150.1701 | 1.153 | 1.153 | False | 156.87 | 0.843 | 84.72 | 128.56 | 208.11 | ROBUST_ACROSS_WEIGHTS | NONE |
| 5 | 813 | Jos Buttler | BAT_SPECIALIST | 50 | 9 | 168 | 154.8622 | 1.085 | 1.085 | False | 155.38 | 0.8185 | 80.62 | 131.42 | 184.72 | ROBUST_ACROSS_WEIGHTS | NONE |
| 6 | 3056 | Iftikhar Ahmed | BAT_PRIMARY_AR | 92 | 23 | 147.8261 | 119.7368 | 1.235 | 1.235 | False | 144.05 | 0.7267 | 79.22 | 104.83 | 182.73 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 7 | 26906 | Angkrish Raghuvanshi | BAT_SPECIALIST | 40 | 8 | 167.5 | 145.9959 | 1.147 | 1.147 | False | 153.13 | 0.6987 | 76.97 | 107.31 | 218.04 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 8 | 8 | MS Dhoni | BAT_SPECIALIST | 239 | 46 | 149.3724 | 134.5238 | 1.11 | 1.11 | False | 147.55 | 0.6905 | 75.85 | 119.9 | 177.83 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 9 | 2003 | Bhanuka Rajapaksa | BAT_SPECIALIST | 49 | 14 | 153.0612 | 134.902 | 1.135 | 1.135 | False | 145.31 | 0.7594 | 75.84 | 102.07 | 201.92 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |
| 10 | 1699 | Suryakumar Yadav | BAT_SPECIALIST | 128 | 45 | 165.625 | 170.4941 | 0.971 | 0.971 | False | 159.83 | 0.7147 | 75.35 | 130.84 | 197.34 | RANKING_SENSITIVE_TO_WEIGHTS | NONE |

### 4.1 Individual Player Selection Rationales — Top 10 Batters (Deliverable 3f)
Every batter in the authoritative Top 10 exceeds the eligible cohort crisis strike rate mean (`130.13` SR, with all 10 between `147.83` and `173.17` Crisis SR):
- **#1 Ashutosh Sharma (`canonical_player_id=8101`, `BAT_SPECIALIST`):** Faced **148 crisis balls** across **26 crisis matches** (normal baseline: 43 balls across 13 matches). Recorded a **168.92 Crisis SR** vs **125.58 Normal SR**, achieving a **1.345x Strike-Rate Maintenance ratio** (raw: 1.345x), **163.31 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[126.66, 213.61]`), and **0.7457 Match Consistency Score**. Component Breakdown: `Maint(35%)=35.00 + Abs(35%)=35.00 + Cons(20%)=14.82 + Sample(10%)=9.06 = 93.88` (`ROBUST_ACROSS_WEIGHTS`).
- **#2 Ramandeep Singh (`canonical_player_id=20006`, `BAT_PRIMARY_AR`):** Faced **115 crisis balls** across **24 crisis matches** (normal baseline: 39 balls across 6 matches). Recorded a **164.35 Crisis SR** vs **125.64 Normal SR**, achieving a **1.308x Strike-Rate Maintenance ratio** (raw: 1.308x), **158.24 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[118.52, 213.06]`), and **0.6978 Match Consistency Score**. Component Breakdown: `Maint(35%)=33.47 + Abs(35%)=32.77 + Cons(20%)=12.89 + Sample(10%)=8.60 = 87.73` (`ROBUST_ACROSS_WEIGHTS`).
- **#3 Shreyas Iyer (`canonical_player_id=3647`, `BAT_SPECIALIST`):** Faced **65 crisis balls** across **29 crisis matches** (normal baseline: 1397 balls across 88 matches). Recorded a **170.77 Crisis SR** vs **151.61 Normal SR**, achieving a **1.126x Strike-Rate Maintenance ratio** (raw: 1.126x), **159.48 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[142.18, 205.17]`), and **0.8740 Match Consistency Score**. Component Breakdown: `Maint(35%)=25.93 + Abs(35%)=33.31 + Cons(20%)=20.00 + Sample(10%)=7.58 = 86.82` (`ROBUST_ACROSS_WEIGHTS`).
- **#4 William Jacks (`canonical_player_id=6272`, `BAT_PRIMARY_AR`):** Faced **41 crisis balls** across **15 crisis matches** (normal baseline: 588 balls across 45 matches). Recorded a **173.17 Crisis SR** vs **150.17 Normal SR**, achieving a **1.153x Strike-Rate Maintenance ratio** (raw: 1.153x), **156.87 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[128.56, 208.11]`), and **0.8430 Match Consistency Score**. Component Breakdown: `Maint(35%)=27.05 + Abs(35%)=32.16 + Cons(20%)=18.75 + Sample(10%)=6.76 = 84.72` (`ROBUST_ACROSS_WEIGHTS`).
- **#5 Jos Buttler (`canonical_player_id=813`, `BAT_SPECIALIST`):** Faced **50 crisis balls** across **9 crisis matches** (normal baseline: 2612 balls across 120 matches). Recorded a **168.00 Crisis SR** vs **154.86 Normal SR**, achieving a **1.085x Strike-Rate Maintenance ratio** (raw: 1.085x), **155.38 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[131.42, 184.72]`), and **0.8185 Match Consistency Score**. Component Breakdown: `Maint(35%)=24.23 + Abs(35%)=31.51 + Cons(20%)=17.76 + Sample(10%)=7.12 = 80.62` (`ROBUST_ACROSS_WEIGHTS`).
- **#6 Iftikhar Ahmed (`canonical_player_id=3056`, `BAT_PRIMARY_AR`):** Faced **92 crisis balls** across **23 crisis matches** (normal baseline: 228 balls across 23 matches). Recorded a **147.83 Crisis SR** vs **119.74 Normal SR**, achieving a **1.235x Strike-Rate Maintenance ratio** (raw: 1.235x), **144.05 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[104.83, 182.73]`), and **0.7267 Match Consistency Score**. Component Breakdown: `Maint(35%)=30.44 + Abs(35%)=26.52 + Cons(20%)=14.06 + Sample(10%)=8.20 = 79.22` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#7 Angkrish Raghuvanshi (`canonical_player_id=26906`, `BAT_SPECIALIST`):** Faced **40 crisis balls** across **8 crisis matches** (normal baseline: 487 balls across 26 matches). Recorded a **167.50 Crisis SR** vs **146.00 Normal SR**, achieving a **1.147x Strike-Rate Maintenance ratio** (raw: 1.147x), **153.13 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[107.31, 218.04]`), and **0.6987 Match Consistency Score**. Component Breakdown: `Maint(35%)=26.80 + Abs(35%)=30.52 + Cons(20%)=12.93 + Sample(10%)=6.72 = 76.97` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#8 MS Dhoni (`canonical_player_id=8`, `BAT_SPECIALIST`):** Faced **239 crisis balls** across **46 crisis matches** (normal baseline: 84 balls across 10 matches). Recorded a **149.37 Crisis SR** vs **134.52 Normal SR**, achieving a **1.110x Strike-Rate Maintenance ratio** (raw: 1.110x), **147.55 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[119.90, 177.83]`), and **0.6905 Match Consistency Score**. Component Breakdown: `Maint(35%)=25.27 + Abs(35%)=28.06 + Cons(20%)=12.60 + Sample(10%)=9.92 = 75.85` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#9 Bhanuka Rajapaksa (`canonical_player_id=2003`, `BAT_SPECIALIST`):** Faced **49 crisis balls** across **14 crisis matches** (normal baseline: 255 balls across 24 matches). Recorded a **153.06 Crisis SR** vs **134.90 Normal SR**, achieving a **1.135x Strike-Rate Maintenance ratio** (raw: 1.135x), **145.31 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[102.07, 201.92]`), and **0.7594 Match Consistency Score**. Component Breakdown: `Maint(35%)=26.30 + Abs(35%)=27.08 + Cons(20%)=15.38 + Sample(10%)=7.08 = 75.84` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#10 Suryakumar Yadav (`canonical_player_id=1699`, `BAT_SPECIALIST`):** Faced **128 crisis balls** across **45 crisis matches** (normal baseline: 2125 balls across 126 matches). Recorded a **165.62 Crisis SR** vs **170.49 Normal SR**, achieving a **0.971x Strike-Rate Maintenance ratio** (raw: 0.971x), **159.83 Empirical Bayes Shrunk Crisis SR** (95% match-clustered bootstrap CI: `[130.84, 197.34]`), and **0.7147 Match Consistency Score**. Component Breakdown: `Maint(35%)=19.51 + Abs(35%)=33.47 + Cons(20%)=13.57 + Sample(10%)=8.80 = 75.35` (`RANKING_SENSITIVE_TO_WEIGHTS`).

---

## 5. Authoritative Top 10 Bowlers Under Defensive Pressure (`data/outputs/v3/TOP_10_BOWLERS.csv`, `MIN_NORMAL_BALLS = 100`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | crisis_matches | norm_balls | norm_baseline_status | crisis_dot_pct | norm_dot_pct | raw_dot_maintenance | capped_dot_maintenance | is_maintenance_capped | crisis_wicket_rate | shrunk_crisis_wr | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1566 | Mohammed Shami | BOWL_SPECIALIST | 875 | 57 | 121 | VALID_NORMAL_BASELINE | 45.8286 | 33.0579 | 1.386 | 1.386 | False | 5.7143 | 5.71 | 0.7721 | 75.31 | 41.93 | 49.64 | RANKING_SENSITIVE_TO_WEIGHTS |
| 2 | 4837 | Obed McCoy | BOWL_SPECIALIST | 385 | 31 | 123 | VALID_NORMAL_BASELINE | 38.7013 | 30.8943 | 1.253 | 1.253 | False | 7.5325 | 7.15 | 0.5786 | 73.15 | 33.03 | 44.21 | ROBUST_ACROSS_WEIGHTS |
| 3 | 4807 | Joshua Little | BOWL_SPECIALIST | 446 | 34 | 175 | VALID_NORMAL_BASELINE | 42.1525 | 36 | 1.171 | 1.171 | False | 6.7265 | 6.54 | 0.7199 | 70.58 | 37.17 | 47.12 | ROBUST_ACROSS_WEIGHTS |
| 4 | 2320 | Trent Boult | BOWL_SPECIALIST | 1131 | 70 | 144 | VALID_NORMAL_BASELINE | 42.7056 | 24.3056 | 1.757 | 1.5 | True | 4.6861 | 4.77 | 0.6965 | 69.31 | 39.82 | 45.93 | RANKING_SENSITIVE_TO_WEIGHTS |
| 5 | 7364 | Haris Rauf | BOWL_SPECIALIST | 692 | 47 | 169 | VALID_NORMAL_BASELINE | 41.3295 | 42.0118 | 0.984 | 0.984 | False | 7.5145 | 7.29 | 0.6729 | 67.48 | 37.41 | 45.1 | RANKING_SENSITIVE_TO_WEIGHTS |
| 6 | 278 | Tim Southee | BOWL_SPECIALIST | 531 | 36 | 135 | VALID_NORMAL_BASELINE | 42.1846 | 38.5185 | 1.095 | 1.095 | False | 6.7797 | 6.61 | 0.6998 | 67.42 | 38.59 | 46.26 | ROBUST_ACROSS_WEIGHTS |
| 7 | 3275 | Alzarri Joseph | BOWL_SPECIALIST | 780 | 52 | 165 | VALID_NORMAL_BASELINE | 40.641 | 32.7273 | 1.242 | 1.242 | False | 5.7692 | 5.76 | 0.6823 | 66.07 | 36.76 | 44.77 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 8380 | Mohammad Rishad Hossain | BOWL_PRIMARY_AR | 280 | 41 | 539 | VALID_NORMAL_BASELINE | 35 | 36.3636 | 0.962 | 0.962 | False | 8.9286 | 8.08 | 0.5223 | 65.84 | 29.92 | 40.25 | RANKING_SENSITIVE_TO_WEIGHTS |
| 9 | 4229 | George Linde | BOWL_PRIMARY_AR | 133 | 15 | 106 | VALID_NORMAL_BASELINE | 41.3534 | 33.0189 | 1.252 | 1.252 | False | 6.7669 | 6.31 | 0.6095 | 65.77 | 31.79 | 51.52 | RANKING_SENSITIVE_TO_WEIGHTS |
| 10 | 27960 | Mayank Yadav | BOWL_SPECIALIST | 276 | 22 | 146 | VALID_NORMAL_BASELINE | 48.1884 | 43.8356 | 1.099 | 1.099 | False | 6.1594 | 6.04 | 0.7806 | 65.1 | 42.23 | 54.55 | RANKING_SENSITIVE_TO_WEIGHTS |

### 5.1 Individual Player Selection Rationales — Top 10 Bowlers (Deliverable 3f)
- **#1 Mohammed Shami (`canonical_player_id=1566`, `BOWL_SPECIALIST`):** Bowled **875 crisis legal balls** across **57 crisis matches** (normal baseline: 121 legal balls across 23 matches, `VALID_NORMAL_BASELINE`). Recorded a **45.83% Crisis Dot-Ball %** vs **33.06% Normal Dot-Ball %**, achieving a **1.386x Capped Dot-Ball Maintenance ratio** (raw: 1.386x), **5.71% Raw Crisis Wicket Rate** (**5.71% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[41.93%, 49.64%]`), and **0.7721 Match Consistency Score**. Component Breakdown: `Maint(35%)=30.21 + Abs(35%)=15.44 + Cons(20%)=19.66 + Sample(10%)=10.00 = 75.31` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#2 Obed McCoy (`canonical_player_id=4837`, `BOWL_SPECIALIST`):** Bowled **385 crisis legal balls** across **31 crisis matches** (normal baseline: 123 legal balls across 21 matches, `VALID_NORMAL_BASELINE`). Recorded a **38.70% Crisis Dot-Ball %** vs **30.89% Normal Dot-Ball %**, achieving a **1.253x Capped Dot-Ball Maintenance ratio** (raw: 1.253x), **7.53% Raw Crisis Wicket Rate** (**7.15% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[33.03%, 44.21%]`), and **0.5786 Match Consistency Score**. Component Breakdown: `Maint(35%)=24.62 + Abs(35%)=27.32 + Cons(20%)=11.90 + Sample(10%)=9.31 = 73.15` (`ROBUST_ACROSS_WEIGHTS`).
- **#3 Joshua Little (`canonical_player_id=4807`, `BOWL_SPECIALIST`):** Bowled **446 crisis legal balls** across **34 crisis matches** (normal baseline: 175 legal balls across 24 matches, `VALID_NORMAL_BASELINE`). Recorded a **42.15% Crisis Dot-Ball %** vs **36.00% Normal Dot-Ball %**, achieving a **1.171x Capped Dot-Ball Maintenance ratio** (raw: 1.171x), **6.73% Raw Crisis Wicket Rate** (**6.54% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[37.17%, 47.12%]`), and **0.7199 Match Consistency Score**. Component Breakdown: `Maint(35%)=21.18 + Abs(35%)=22.29 + Cons(20%)=17.57 + Sample(10%)=9.54 = 70.58` (`ROBUST_ACROSS_WEIGHTS`).
- **#4 Trent Boult (`canonical_player_id=2320`, `BOWL_SPECIALIST`):** Bowled **1131 crisis legal balls** across **70 crisis matches** (normal baseline: 144 legal balls across 28 matches, `VALID_NORMAL_BASELINE`). Recorded a **42.71% Crisis Dot-Ball %** vs **24.31% Normal Dot-Ball %**, achieving a **1.500x Capped Dot-Ball Maintenance ratio** (raw: 1.757x (winsorized from raw ratio)), **4.69% Raw Crisis Wicket Rate** (**4.77% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[39.82%, 45.93%]`), and **0.6965 Match Consistency Score**. Component Breakdown: `Maint(35%)=35.00 + Abs(35%)=7.68 + Cons(20%)=16.63 + Sample(10%)=10.00 = 69.31` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#5 Haris Rauf (`canonical_player_id=7364`, `BOWL_SPECIALIST`):** Bowled **692 crisis legal balls** across **47 crisis matches** (normal baseline: 169 legal balls across 32 matches, `VALID_NORMAL_BASELINE`). Recorded a **41.33% Crisis Dot-Ball %** vs **42.01% Normal Dot-Ball %**, achieving a **0.984x Capped Dot-Ball Maintenance ratio** (raw: 0.984x), **7.51% Raw Crisis Wicket Rate** (**7.29% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[37.41%, 45.10%]`), and **0.6729 Match Consistency Score**. Component Breakdown: `Maint(35%)=13.32 + Abs(35%)=28.48 + Cons(20%)=15.68 + Sample(10%)=10.00 = 67.48` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#6 Tim Southee (`canonical_player_id=278`, `BOWL_SPECIALIST`):** Bowled **531 crisis legal balls** across **36 crisis matches** (normal baseline: 135 legal balls across 24 matches, `VALID_NORMAL_BASELINE`). Recorded a **42.18% Crisis Dot-Ball %** vs **38.52% Normal Dot-Ball %**, achieving a **1.095x Capped Dot-Ball Maintenance ratio** (raw: 1.095x), **6.78% Raw Crisis Wicket Rate** (**6.61% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[38.59%, 46.26%]`), and **0.6998 Match Consistency Score**. Component Breakdown: `Maint(35%)=17.98 + Abs(35%)=22.87 + Cons(20%)=16.76 + Sample(10%)=9.81 = 67.42` (`ROBUST_ACROSS_WEIGHTS`).
- **#7 Alzarri Joseph (`canonical_player_id=3275`, `BOWL_SPECIALIST`):** Bowled **780 crisis legal balls** across **52 crisis matches** (normal baseline: 165 legal balls across 31 matches, `VALID_NORMAL_BASELINE`). Recorded a **40.64% Crisis Dot-Ball %** vs **32.73% Normal Dot-Ball %**, achieving a **1.242x Capped Dot-Ball Maintenance ratio** (raw: 1.242x), **5.77% Raw Crisis Wicket Rate** (**5.76% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[36.76%, 44.77%]`), and **0.6823 Match Consistency Score**. Component Breakdown: `Maint(35%)=24.16 + Abs(35%)=15.85 + Cons(20%)=16.06 + Sample(10%)=10.00 = 66.07` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#8 Mohammad Rishad Hossain (`canonical_player_id=8380`, `BOWL_PRIMARY_AR`):** Bowled **280 crisis legal balls** across **41 crisis matches** (normal baseline: 539 legal balls across 47 matches, `VALID_NORMAL_BASELINE`). Recorded a **35.00% Crisis Dot-Ball %** vs **36.36% Normal Dot-Ball %**, achieving a **0.962x Capped Dot-Ball Maintenance ratio** (raw: 0.962x), **8.93% Raw Crisis Wicket Rate** (**8.08% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[29.92%, 40.25%]`), and **0.5223 Match Consistency Score**. Component Breakdown: `Maint(35%)=12.39 + Abs(35%)=35.00 + Cons(20%)=9.64 + Sample(10%)=8.81 = 65.84` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#9 George Linde (`canonical_player_id=4229`, `BOWL_PRIMARY_AR`):** Bowled **133 crisis legal balls** across **15 crisis matches** (normal baseline: 106 legal balls across 13 matches, `VALID_NORMAL_BASELINE`). Recorded a **41.35% Crisis Dot-Ball %** vs **33.02% Normal Dot-Ball %**, achieving a **1.252x Capped Dot-Ball Maintenance ratio** (raw: 1.252x), **6.77% Raw Crisis Wicket Rate** (**6.31% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[31.79%, 51.52%]`), and **0.6095 Match Consistency Score**. Component Breakdown: `Maint(35%)=24.58 + Abs(35%)=20.39 + Cons(20%)=13.14 + Sample(10%)=7.66 = 65.77` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#10 Mayank Yadav (`canonical_player_id=27960`, `BOWL_SPECIALIST`):** Bowled **276 crisis legal balls** across **22 crisis matches** (normal baseline: 146 legal balls across 15 matches, `VALID_NORMAL_BASELINE`). Recorded a **48.19% Crisis Dot-Ball %** vs **43.84% Normal Dot-Ball %**, achieving a **1.099x Capped Dot-Ball Maintenance ratio** (raw: 1.099x), **6.16% Raw Crisis Wicket Rate** (**6.04% Beta-Binomial Shrunk Crisis WR**, 95% match-clustered bootstrap CI on crisis dot%: `[42.23%, 54.55%]`), and **0.7806 Match Consistency Score**. Component Breakdown: `Maint(35%)=18.15 + Abs(35%)=18.16 + Cons(20%)=20.00 + Sample(10%)=8.79 = 65.10` (`RANKING_SENSITIVE_TO_WEIGHTS`).

---

## 6. Extended Crisis-Ball Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

### 6.1 Batting Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 30, total_balls >= 120`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 5 | 92 | 103 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 60 | 5 | 71 | 102 | 10 | 6 | 0.4286 | 2.5 | 4 | Ibrahim Zadran, Rahul Tewatia, Jaker Ali Anik, Nicholas Pooran | William Jacks, Jos Buttler, Angkrish Raghuvanshi, Bhanuka Rajapaksa |
| 80 | 5 | 60 | 101 | 10 | 5 | 0.3333 | 4.2 | 6 | Rahul Tewatia, Jaker Ali Anik, Nicholas Pooran, Jitesh Sharma, Rinku Singh | Shreyas Iyer, William Jacks, Jos Buttler, Angkrish Raghuvanshi, Bhanuka Rajapaksa |
| 100 | 5 | 50 | 100 | 10 | 4 | 0.25 | 5.3 | 7 | Rahul Tewatia, Jaker Ali Anik, Nicholas Pooran, Jitesh Sharma, Rinku Singh, Naman Dhir | Shreyas Iyer, William Jacks, Jos Buttler, Iftikhar Ahmed, Angkrish Raghuvanshi, Bhanuka Rajapaksa |
| 150 | 5 | 25 | 96 | 10 | 1 | 0.0526 | 11.1 | 13 | Rahul Tewatia, Jaker Ali Anik, Jitesh Sharma, Rinku Singh, Hardik Pandya, Ayush Badoni, George Dockrell, Tilak Varma, Washington Sundar | Ashutosh Sharma, Ramandeep Singh, Shreyas Iyer, William Jacks, Jos Buttler, Iftikhar Ahmed, Angkrish Raghuvanshi, Bhanuka Rajapaksa, Suryakumar Yadav |
| 200 | 5 | 11 | 89 | 10 | 1 | 0.0526 | 27.6 | 57 | Rahul Tewatia, Rinku Singh, Tilak Varma, Marcus Stoinis, Tim David, Dasun Shanaka, Andre Russell, Dinesh Karthik, Rovman Powell | Ashutosh Sharma, Ramandeep Singh, Shreyas Iyer, William Jacks, Jos Buttler, Iftikhar Ahmed, Angkrish Raghuvanshi, Bhanuka Rajapaksa, Suryakumar Yadav |
| 250 | 5 | 7 | 84 | 7 | 0 | 0 | 34.57 | 70 | Rahul Tewatia, Rinku Singh, Tilak Varma, Tim David, Andre Russell, Rovman Powell, Shimron Hetmyer | Ashutosh Sharma, Ramandeep Singh, Shreyas Iyer, William Jacks, Jos Buttler, Iftikhar Ahmed, Angkrish Raghuvanshi, MS Dhoni, Bhanuka Rajapaksa, Suryakumar Yadav |

### 6.2 Bowling Primary Crisis-Ball Sweep (`crisis_matches >= 5, norm_balls >= 100, total_legal_balls >= 120`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 5 | 92 | 103 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 60 | 5 | 71 | 102 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 80 | 5 | 60 | 101 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 100 | 5 | 50 | 100 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 120 | 5 | 39 | 99 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 150 | 5 | 25 | 96 | 10 | 9 | 0.8182 | 0.2 | 1 | Liam Dawson | George Linde |
| 200 | 5 | 11 | 89 | 10 | 9 | 0.8182 | 0.4 | 3 | Matheesha Pathirana | George Linde |
| 250 | 5 | 7 | 84 | 10 | 9 | 0.8182 | 0.4 | 3 | Matheesha Pathirana | George Linde |

*Note:* Under the calibrated pressure model, **92 batters** qualify at the `40`-ball baseline, **71** at `60` balls, **60** at `80` balls, **50** at `100` balls, **39** at `120` balls, **25** at `150` balls, **11** at `200` balls, and **7** at `250` balls (where `available_top10_count = 7`, never forcing a Top 10 when fewer than 10 players qualify). For bowlers, **99 frontline bowlers** qualify at the `120`-ball baseline (`100` at `100` balls, `96` at `150` balls, `89` at `200` balls, and `84` at `250` balls with `9/10` Top-10 overlap).

---

## 7. Weight Sensitivity Analysis Across 5 Prespecified Configurations (`RANKING_WEIGHT_SENSITIVITY.csv`)

### 7.1 Batting Weight Sensitivity (Top 10)
| provisional_rank | canonical_player_id | player_name | provisional_fixed_weight_score | contrib_maint | contrib_abs | contrib_cons | contrib_sample | rank_balanced_default | rank_maintenance_heavy | rank_absolute_heavy | rank_consistency_heavy | rank_equal_weights | max_rank_shift | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8101 | Ashutosh Sharma | 93.88 | 35 | 35 | 14.82 | 9.06 | 1 | 1 | 1 | 1 | 1 | 0 | ROBUST_ACROSS_WEIGHTS |
| 2 | 20006 | Ramandeep Singh | 87.73 | 33.47 | 32.77 | 12.89 | 8.6 | 2 | 2 | 2 | 4 | 3 | 2 | ROBUST_ACROSS_WEIGHTS |
| 3 | 3647 | Shreyas Iyer | 86.82 | 25.93 | 33.31 | 20 | 7.58 | 3 | 3 | 3 | 2 | 2 | 1 | ROBUST_ACROSS_WEIGHTS |
| 4 | 6272 | William Jacks | 84.72 | 27.05 | 32.16 | 18.75 | 6.76 | 4 | 4 | 4 | 3 | 4 | 1 | ROBUST_ACROSS_WEIGHTS |
| 5 | 813 | Jos Buttler | 80.62 | 24.23 | 31.51 | 17.76 | 7.12 | 5 | 6 | 5 | 5 | 5 | 1 | ROBUST_ACROSS_WEIGHTS |
| 6 | 3056 | Iftikhar Ahmed | 79.22 | 30.44 | 26.52 | 14.06 | 8.2 | 6 | 5 | 10 | 6 | 6 | 5 | RANKING_SENSITIVE_TO_WEIGHTS |
| 7 | 26906 | Angkrish Raghuvanshi | 76.97 | 26.8 | 30.52 | 12.93 | 6.72 | 7 | 8 | 7 | 8 | 15 | 8 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 8 | MS Dhoni | 75.85 | 25.27 | 28.06 | 12.6 | 9.92 | 8 | 10 | 12 | 10 | 7 | 5 | RANKING_SENSITIVE_TO_WEIGHTS |
| 9 | 2003 | Bhanuka Rajapaksa | 75.84 | 26.3 | 27.08 | 15.38 | 7.08 | 9 | 9 | 13 | 7 | 13 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |
| 10 | 1699 | Suryakumar Yadav | 75.35 | 19.51 | 33.47 | 13.57 | 8.8 | 10 | 12 | 6 | 9 | 9 | 6 | RANKING_SENSITIVE_TO_WEIGHTS |

### 7.2 Bowling Weight Sensitivity (Top 10)
| provisional_rank | canonical_player_id | player_name | provisional_fixed_weight_score | contrib_maint | contrib_abs | contrib_cons | contrib_sample | rank_balanced_default | rank_maintenance_heavy | rank_absolute_heavy | rank_consistency_heavy | rank_equal_weights | max_rank_shift | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1566 | Mohammed Shami | 75.31 | 30.21 | 15.44 | 19.66 | 10 | 1 | 1 | 6 | 1 | 1 | 5 | RANKING_SENSITIVE_TO_WEIGHTS |
| 2 | 4837 | Obed McCoy | 73.15 | 24.62 | 27.32 | 11.9 | 9.31 | 2 | 4 | 2 | 3 | 4 | 2 | ROBUST_ACROSS_WEIGHTS |
| 3 | 4807 | Joshua Little | 70.58 | 21.18 | 22.29 | 17.57 | 9.54 | 3 | 5 | 5 | 2 | 2 | 3 | ROBUST_ACROSS_WEIGHTS |
| 4 | 2320 | Trent Boult | 69.31 | 35 | 7.68 | 16.63 | 10 | 4 | 2 | 23 | 4 | 3 | 21 | RANKING_SENSITIVE_TO_WEIGHTS |
| 5 | 7364 | Haris Rauf | 67.48 | 13.32 | 28.48 | 15.68 | 10 | 5 | 12 | 4 | 7 | 6 | 8 | RANKING_SENSITIVE_TO_WEIGHTS |
| 6 | 278 | Tim Southee | 67.42 | 17.98 | 22.87 | 16.76 | 9.81 | 6 | 8 | 7 | 5 | 5 | 3 | ROBUST_ACROSS_WEIGHTS |
| 7 | 3275 | Alzarri Joseph | 66.07 | 24.16 | 15.85 | 16.06 | 10 | 7 | 6 | 18 | 8 | 7 | 12 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 8380 | Mohammad Rishad Hossain | 65.84 | 12.39 | 35 | 9.64 | 8.81 | 8 | 19 | 1 | 17 | 18 | 18 | RANKING_SENSITIVE_TO_WEIGHTS |
| 9 | 4229 | George Linde | 65.77 | 24.58 | 20.39 | 13.14 | 7.66 | 9 | 7 | 12 | 9 | 19 | 12 | RANKING_SENSITIVE_TO_WEIGHTS |
| 10 | 27960 | Mayank Yadav | 65.1 | 18.15 | 18.16 | 20 | 8.79 | 10 | 10 | 16 | 6 | 8 | 10 | RANKING_SENSITIVE_TO_WEIGHTS |

---

## 8. Reproducibility & Verification Gates

- Pipeline execution: `.venv\Scripts\python scripts/compute_v3_rankings.py`
- Independent verification: `.venv\Scripts\python scripts/verify_v3_rankings.py`
- Automated test suite: `.venv\Scripts\python -m pytest tests/ -v` (**64 passed**)
