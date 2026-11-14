# SupeRR Intelligence 2.0 — Pressure Model Upgrade & Methodology Validation Report

**Rajasthan Royals SupeRR Selector Season 2 Hackathon**  
**Engineering Dossier: Architectural Redesign, Dual Pre-Delivery Pressure Engines & Statistical Reliability Audit**

---

## 1. What the Old Pressure Model Measured

The legacy Version 1.0 pressure model utilized a single, undifferentiated heuristic score for all deliveries:
- **Heuristic Drivers:** Cumulative wickets fallen, 2-wicket clusters in 12 balls, new-batter entry decay, and a flat $1.3\times$ death-overs multiplier.
- **Fundamental Flaw:** It primarily measured **batting-side collapse crisis**.
- **The Bowling Pressure Fallacy:** By applying batting crisis to bowlers, the legacy model assumed a bowler faced "maximum pressure" when the batting side had already collapsed (e.g., $30/5$). In real cricket, a bowler in that situation has massive cushion and is bowling with aggressive attacking fields. True bowling pressure occurs when defending against an opponent with wickets in hand (e.g. $170/2$ in the 18th over) or during rapid boundary streaks.
- **Baseline Conflation:** The legacy baseline compared High + Extreme pressure against None + Low + Moderate, contaminating the unconstrained baseline with transitional pressure situations.
- **Mathematical Limitations:** Used arbitrary linear shrinkage and a brittle $(1 - \text{CV})$ consistency metric that artificially collapsed bowler consistency scores to zero.

---

## 2. What the New Batting Pressure Model Measures (`BattingPressureEngine`)

The new **Batting Crisis Pressure Engine** is an independent pre-delivery model calibrated specifically to batting collapse and recovery states:
1. **Wicket Depletion ($0.0$ to $3.5$ pts):** Linear scaling with wickets lost before delivery ($\min(3.5, \text{wickets\_fallen\_before} \times 0.45)$).
2. **Cluster Collapse ($0.0$ to $2.0$ pts):** Detects recent traumatic shocks ($2+$ wickets in the preceding 12 legal balls adds $2.0$ pts; 1 wicket adds $0.75$ pts).
3. **Batter Entry Vulnerability ($0.0$ to $1.5$ pts):** Measures initial crease vulnerability, decaying over the batter's first 5 balls faced ($\max(0.0, 1.5 - \text{balls\_faced} \times 0.30)$).
4. **Scoring Stagnation ($0.0$ to $1.5$ pts):** Proportion of dots in the last 12 legal balls ($1.5 \times \text{dots\_in\_last\_12} / 12.0$).
5. **Phase Scaling ($P_{\text{phase}}$):** Death overs receive a $1.25\times$ multiplier; powerplays receive $0.95\times$.

---

## 3. What the New Bowling Pressure Model Measures (`BowlingPressureEngine`)

The new **Bowling Defensive Pressure Engine** measures opposition resource threat and defensive leverage:
1. **Batting Resource Threat ($0.0$ to $3.0$ pts):** Scales directly with opponent wickets in hand ($\text{batting\_wickets\_remaining}$):
   - $8–10$ wickets in hand: $3.0$ pts (opponent has maximum batting resources to attack).
   - $6–7$ wickets in hand: $2.0$ pts.
   - $4–5$ wickets in hand: $1.0$ pt.
   - $1–3$ wickets in hand: $0.2$ pts (cushioned situation).
2. **Critical Phase Base Leverage ($1.0$ to $3.0$ pts):** Death overs (overs 16–20) = $3.0$ pts; powerplay field restrictions (overs 1–6) = $2.0$ pts; middle overs = $1.0$ pt.
3. **Opponent Boundary Momentum ($0.0$ to $2.5$ pts):** Conceding $3+$ boundaries in the last 12 legal balls adds $2.5$ pts; 2 boundaries adds $1.6$ pts.
4. **Run-Flow / Strike Rotation Pressure ($0.0$ to $1.5$ pts):** Conceding scoring shots on consecutive deliveries ($1.5 \times (1.0 - \text{dots\_in\_last\_12} / 12.0)$).

---

## 4. How Normal, Moderate and High Pressure Differ (Tripartite Segmentation)

Matches are cleanly segmented into three distinct operational states:
- **Group 1 — Normal (None + Low tiers):** Unconstrained match play where standard tactical execution occurs. Represents $76.2\%$ of batting deliveries and $10.6\%$ of bowling deliveries.
- **Group 2 — Moderate (Moderate tier):** Transitional leverage situations kept isolated to avoid contaminating either baseline or high-leverage pools. Represents $15.9\%$ of batting deliveries and $36.9\%$ of bowling deliveries.
- **Group 3 — High Pressure (High + Extreme tiers):** True acute leverage where performance maintenance is rigorously tested. Represents $7.97\%$ of batting deliveries ($15,464$ balls) and $52.55\%$ of bowling deliveries ($101,935$ balls).

### Empirical Delivery Distribution & Behavioral Proof
| Tier | Batting Deliveries | Batting Share | Batting Runs/Ball | Batting Wkt % | Bowling Deliveries | Bowling Share | Bowling Runs/Ball | Bowling Bound % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **None** | 75,924 | 39.14% | 1.45 | 4.80% | 1,470 | 0.76% | 0.85 | 9.18% |
| **Low** | 71,840 | 37.03% | 1.34 | 5.16% | 18,991 | 9.79% | 1.08 | 11.59% |
| **Moderate** | 30,760 | 15.86% | 1.23 | 5.89% | 71,592 | 36.91% | 1.25 | 15.61% |
| **High** | 11,445 | 5.90% | 1.15 | 7.71% | 70,591 | 36.39% | 1.43 | 19.61% |
| **Extreme** | 4,019 | 2.07% | 0.99 | 10.72% | 31,344 | 16.16% | 1.57 | 24.54% |
| **Total** | **193,988** | **100.0%** | — | — | **193,988** | **100.0%** | — | — |

---

## 5. Exact Formulas Used

### Pressure Reliability Index (PRI)
$$\text{PRI} = 100 \times \left( 0.35 \cdot M_{\text{norm}} + 0.35 \cdot A_{\text{norm}} + 0.20 \cdot C_{\text{norm}} + 0.10 \cdot S_{\text{norm}} \right)$$

1. **Performance Maintenance ($M$):**
   - Batters: $M_{\text{bat}} = \min\left(1.50, \frac{\text{SR}_{\text{crisis}}}{\max(80.0, \text{SR}_{\text{norm}})}\right)$
   - Bowlers: $M_{\text{bowl}} = \min\left(1.50, \frac{\text{Dot\%}_{\text{crisis}}}{\max(25.0, \text{Dot\%}_{\text{norm}})}\right)$
2. **Absolute Performance with Empirical Bayes Shrinkage ($A$):**
   - Batters (Normal-Normal): $\hat{\mu}_i = \frac{n_i}{n_i + 25.0} \bar{X}_i + \frac{25.0}{n_i + 25.0} (129.5)$
   - Bowlers (Beta-Binomial): $\hat{p}_i = \frac{k_i + 5.0}{n_i + 5.0 + 86.2} \times 100$
3. **Cross-Match Consistency ($C$):**
   $$C = \exp(-\text{CV}) \cdot \sqrt{\frac{m}{m + 3}}$$
4. **Sample Size Confidence ($S$):**
   $$S = \min\left(1.0, \frac{\ln(1 + n_i)}{\ln(1 + 250)}\right)$$

---

## 6. Verified vs. Provisional Calculations

| Metric / Feature | Mathematical Status | Data Governance Status | Reason / Justification |
| :--- | :---: | :---: | :--- |
| **Batter Runs & Strike Rate** | 100% Verified | `ACTIVE` | Computed from `runs` and `is_ball_faced`. |
| **Bowler Wickets & Dot Ball %** | 100% Verified | `ACTIVE` | Run outs, retired outs, and obstruction excluded. |
| **Pre-Delivery Pressure Tiers** | 100% Verified | `ACTIVE` | Derived strictly from pre-delivery context (zero leakage). |
| **Empirical Bayes Shrinkage** | 100% Verified | `ACTIVE` | Conjugate Normal-Normal and Beta-Binomial models. |
| **Match Consistency ($C$)** | 100% Verified | `ACTIVE` | Exposure-adjusted exponential dispersion. |
| **Team Score Totals** | Blocked | `QUARANTINED` | `extras1_runs` is a categorical code (1–7), not run counts. |
| **Required Run Rate (RRR)** | Blocked | `QUARANTINED` | First-innings total unverified without extras codebook. |
| **Exact Bowler Economy Rate** | Blocked | `QUARANTINED` | Runs conceded cannot be determined on wide/no-ball events. |

---

## 7. How the PRI Changed

1. **Elimination of Zero-Consistency Bug:** Bowler wicket rates per match naturally have high variance ($\text{CV} \ge 1.0$). The legacy formula clipped $(1 - \text{CV})$ at zero, artificially assigning $0.00$ consistency to world-class bowlers like Trent Boult and Kuldeep Yadav. The new exponential metric $\exp(-\text{CV}) \cdot \sqrt{m/(m+3)}$ produces smooth, strictly positive scores in $[0.34, 0.61]$.
2. **Conjugate Empirical Bayes Shrinkage:** Replaced arbitrary heuristic dampeners with rigorous statistical shrinkage toward population priors.
3. **Tripartite Normal Baseline:** Maintenance is benchmarked against genuine unconstrained play ($\text{None} + \text{Low}$), eliminating distortion from transitional moderate situations.
4. **Cohort Normalization:** Components are normalized across the eligible cohort before weighting, preventing high-variance metrics from dominating the index.

---

## 8. Previous vs. New Top 10 Side-by-Side

### 🏏 Batters Under Pressure: Legacy vs. Upgraded PRI
| Rank | Legacy Model (v1.0) | Legacy PRI | Upgraded Model (v2.0) | Tactical Role | Upgraded PRI | Movement & Reason |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| **1** | Mukul Choudhary | 81.77 | **Namboori Tilak Varma** | Middle-Order Batter | **91.30** | Elevated: Elite crisis SR (196.7), 18 matches, 1.36x maint. |
| **2** | Ramandeep Singh | 80.03 | **Matthew Wade** | Finisher / All-Rounder | **74.76** | Elevated: High clutch SR (172.0), 15 matches, 0.50 consistency. |
| **3** | Jos Buttler | 77.59 | **Gudakesh Motie** | Lower-Order / Bowler | **74.59** | Proven crisis elevation (170.2 SR vs 117.1 norm). |
| **4** | George Linde | 76.41 | **Daryl Mitchell** | Middle-Order Batter | **70.26** | Stable: 177.3 crisis SR across 12 high-leverage matches. |
| **5** | Ashutosh Sharma | 76.40 | **Liam Livingstone** | Middle-Order Batter | **69.00** | Sustained: 175.0 crisis SR across 14 high-leverage matches. |
| **6** | Yasir Ali Chowdhury | 75.52 | **Akeal Hosein** | Lower-Order / Bowler | **68.23** | Deep sample (114 crisis balls, 29 matches, 1.19x maint). |
| **7** | Rinku Singh | 75.23 | **Mahendra Singh Dhoni** | Finisher / All-Rounder | **66.20** | Deepest crisis sample (133 crisis balls, 35 matches). |
| **8** | Jaker Ali Anik | 73.39 | **Abdul Samad** | Finisher / All-Rounder | **65.78** | Consistent execution (169.6 crisis SR across 23 matches). |
| **9** | Corbin Bosch | 73.28 | **Jaker Ali Anik** | Middle-Order Batter | **64.19** | Sustained presence: 139.7 crisis SR, 1.14x maint. |
| **10** | Harpreet Brar | 72.01 | **Ravindra Jadeja** | Finisher / All-Rounder | **63.77** | Proven veteran: 94 crisis balls across 33 matches. |

### 🎯 Bowlers Under Pressure: Legacy vs. Upgraded PRI
| Rank | Legacy Model (v1.0) | Legacy PRI | Upgraded Model (v2.0) | Tactical Role | Upgraded PRI | Movement & Reason |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| **1** | Sufiyan Muqeem | 75.77 | **Mark Adair** | Bowling All-Rounder | **86.16** | Unlocked: 483 crisis balls, 40 matches, 1.48x dot maint. |
| **2** | Kuldeep Yadav | 73.51 | **Craig Young** | Specialist Bowler | **86.10** | Unlocked: 289 crisis balls, 23 matches, 9.0% wkt rate. |
| **3** | Gurjapneet Singh | 72.87 | **Harry Tector** | Batting All-Rounder / Part-Time | **86.00** | Clutch arm: 9.3% wkt rate, 50.0% crisis dots. |
| **4** | Mitchell Starc | 72.81 | **Mark Wood** | Specialist Bowler | **77.94** | Express pace: 9.6% wkt rate, 41.7% dots. |
| **5** | Matthew Humphreys | 71.73 | **Obed McCoy** | Specialist Bowler | **77.83** | Death specialist: 334 crisis balls, 30 matches, 6.6% wkt rate. |
| **6** | Adam Zampa | 67.49 | **Trent Boult** | Bowling All-Rounder | **76.46** | Consistency fix: 879 crisis balls, 70 matches, 0.53 consistency. |
| **7** | Kane Richardson | 65.79 | **Gareth Delany** | Bowling All-Rounder | **76.18** | High control: 178 crisis balls, 24 matches, 1.50x dot maint. |
| **8** | Dasun Shanaka | 65.57 | **Eshan Malinga** | Specialist Bowler | **73.67** | High volume: 572 crisis balls, 39 matches, 0.61 consistency. |
| **9** | Jaydev Unadkat | 65.28 | **Jacob Duffy** | Specialist Bowler | **73.13** | Strike weapon: 486 crisis balls, 39 matches, 7.8% wkt rate. |
| **10** | Ben Dwarshuis | 64.90 | **Krishnappa Gowtham** | Bowling All-Rounder | **72.66** | Off-spin control: 67 crisis balls, 10 matches, 44.8% dots. |

---

## 9. Why Individual Rankings Changed

1. **Tilak Varma (#1 Batter):** Dominates absolute crisis capability ($196.7$ strike rate under acute collapse) while sustaining a $1.36\times$ elevation over his $144.5$ normal baseline across 18 distinct matches.
2. **Trent Boult (#6 Bowler):** Previously received $0.00$ consistency under the legacy $(1 - \text{CV})$ formula. The exposure-adjusted exponential formulation restores his true consistency ($0.53$), correctly recognizing his unmatched sample depth ($879$ crisis balls across 70 matches).
3. **Mark Adair & Craig Young (#1 & #2 Bowlers):** In the legacy model, bowling pressure was conflated with batting collapses. Under true defensive pressure (opponents holding 8-10 wickets in hand in death overs and powerplays), Adair and Young maintain extraordinary dot retention ($37.1\%$ and $36.3\%$) and strike rates ($6.6\%$ and $9.0\%$) across 40 and 23 matches.
4. **Tailenders & Part-Timers:** In accordance with the official hackathon rules, all players meeting sample criteria are ranked without arbitrary role exclusion. However, each player's tactical role (e.g., Lower-Order / Bowler for Motie and Hosein; Batting All-Rounder / Part-Time for Tector) is transparently displayed and documented.

---

## 10. Ranking Stability (Sensitivity Analysis)

Rankings were evaluated across 5 distinct tactical weighting schemes:
- **Spearman Rank Correlation:** Exceeds **0.88** across all configurations for batters and **0.91** for bowlers.
- **Top Tier Invariance:** Tilak Varma remains the unanimous #1 clutch batter across every weighting scheme. Adair and Young remain the top bowling tier across all configurations.

---

## 11. Test Suite Verification

The automated test suite (`pytest tests/ -v`) executes **17 unit and integration tests with a 100% pass rate** in $1.54$ seconds:
- `test_innings_context_wickets_and_balls_faced`: PASSED
- `test_delivery_context_dots_and_boundaries`: PASSED
- `test_partnership_tracker`: PASSED
- `test_classify_extras`: PASSED
- `test_identify_balls_faced`: PASSED
- `test_identify_legal_balls`: PASSED
- `test_classify_bowler_wickets`: PASSED
- `test_validate_boundaries`: PASSED
- `test_add_innings_phase`: PASSED
- `test_separate_super_overs`: PASSED
- `test_dual_pressure_models_and_zero_leakage`: PASSED
- `test_empirical_bayes_normal_shrink`: PASSED
- `test_empirical_bayes_beta_binomial`: PASSED
- `test_calculate_bowler_match_consistency_strictly_positive`: PASSED
- `test_calculate_batter_match_consistency_strictly_positive`: PASSED
- `test_scout_explosive_middle_order`: PASSED
- `test_scout_phase_bowlers`: PASSED

---

## 12. Remaining Data Limitations

1. **Extras Semantics Unconfirmed by RR:** `extras1_runs` is verified as categorical codes ($1–7$), not run amounts. Deriving exact team totals, required run rates, or bowling economy remains quarantined to preserve scientific integrity.
2. **Super Overs Quarantined:** Super Over deliveries ($26$ balls across innings 3 and 4) are quarantined from regular 20-over tactical ratings due to distinct tactical incentives.
3. **Playing-XI Deduplication:** Resolved key collisions across matches 13613, 21176, and 28962 by taking the lower batting order entry.
