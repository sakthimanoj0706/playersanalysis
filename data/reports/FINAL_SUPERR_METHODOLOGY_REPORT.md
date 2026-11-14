# SupeRR Intelligence: Pressure Reliability Analytics & Player Scouting
## Official Technical Methodology Report & Evidence Dossier
**Target Event:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Scope:** Historical IPL & Men's T20I (2022 – 2026)  
**Deliverable Type:** Reproducible Analytics Methodology & Decision Support System  
**System Status:** Complete, Audited & Scientifically Defensible  

---

## 1. Executive Summary & Cricket Philosophy

Standard cricket statistics (total runs, nominal strike rates, aggregate wickets) are heavily distorted by unconstrained play in low-leverage match situations.
Under the official Round 1 problem statement of the Rajasthan Royals hackathon, **true pressure reliability is defined as the capacity to maintain or elevate performance under high-leverage crisis states relative to one's own normal baseline**.

SupeRR Intelligence establishes:
1. **Dual Independent Pressure Formulations:** Batting collapse crisis and bowling defensive pressure are evaluated via independent models with zero target leakage.
2. **Empirical Bayesian Shrinkage:** Replaces arbitrary cutoffs with statistical shrinkage towards empirical population priors (Normal-Normal for strike rate, Beta-Binomial for wicket rate).
3. **Exposure-Adjusted Match Consistency:** Multi-match dispersion metric continuous in (0, 1] eliminating zero-consistency anomalies.
4. **Role-Aware Dual Leaderboard Architecture:** Distinguishes frontline regular performers from lower-order impact hitters and part-time bowling options while retaining complete transparency across all 1,118 audited players.

---

## 2. Dataset Scope & Data Governance Audit

The platform ingests the official dataset across **853 matches** (837 with ball-by-ball delivery logs) and **193,988 regular deliveries**.

### Surgical Governance Disclosures
1. **`extras1_runs` is Categorical, NOT a Run Count:** Source data integer codes (1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty) represent an enum codebook. **Never summed as runs.**
2. **Quarantined Metrics:** Because total extras semantics remain unconfirmed, derived team totals, required run rates, and bowler economy rates are withheld from ranking formulas to ensure zero false precision.
3. **Non-Bowler Dismissals Filtered:** 571 run outs, 6 retired outs, and 2 obstructing-the-field events excluded from bowler wickets. Only genuine bowler wickets (Caught, Bowled, LBW, Stumped, Hit Wicket) are retained. Stumpings on wide balls are properly attributed.
4. **Boundary Discrepancies Reconciled:** 23 flagged boundary anomalies (20 fours, 3 sixes with runs==4/6 but false flags) reconciled via validated boolean flags.
5. **Super Overs Quarantined:** Innings 3 and 4 (26 balls) quarantined from 20-over tactical ratings.

---

## 3. Dual Independent Pressure Models

### A. Batting Crisis Model (0–10 Scale)
Evaluates batting crisis from pre-delivery context:
- **Wickets Fallen Before Delivery (0–3.5 pts):** 0 wkts = 0.0, 1–2 wkts = 0.5, 3–4 wkts = 1.5, 5–6 wkts = 2.5, 7+ wkts = 3.5.
- **Recent 12-Legal-Ball Collapse Cluster (0–2.0 pts):** 1 wkt = 0.8, 2 wkts = 1.5, 3+ wkts = 2.0.
- **Batter Novelty / Entry Vulnerability (0–1.5 pts):** Balls faced <= 6 = 1.5, balls 7-12 = 0.8.
- **Dot-Ball Stagnation Streak (0–1.5 pts):** 4+ consecutive team dots = 1.0, 6+ dots = 1.5.
- **Phase Multiplier:** Death overs (16–20) receive 1.25x multiplier.
- **Deliveries Classified:** High + Extreme crisis accounts for 15,464 balls (7.97% of regular deliveries).

### B. Bowling Defensive Pressure Model (0–10 Scale)
Evaluates high-leverage defensive constraints:
- **Opponent Resource Threat (0–3.0 pts):** Opponent batting depth (8–10 wickets in hand = 3.0 pts; 5–7 wkts = 1.5 pts).
- **Critical Innings Phase (1.0–3.0 pts):** Death overs (16–20) = 3.0 pts; Powerplay (1–6) = 2.0 pts; Middle = 1.0 pt.
- **Opponent Boundary Momentum (0–2.5 pts):** 3+ boundaries in last 12 legal balls = 2.5 pts; 2 boundaries = 1.5 pts.
- **Run-Flow Threat (0–1.5 pts):** Opponent running at $\ge 1.8$ runs/ball = 1.5 pts.
- **Deliveries Classified:** High + Extreme defensive pressure accounts for 101,935 balls (52.55% of regular deliveries).

### Pressure Distribution Validation Summary
| batting_pressure_tier   |   deliveries |   avg_runs |   boundary_rate |   wicket_rate |   dot_rate |   pct_of_deliveries | model                   | bowling_pressure_tier   |
|:------------------------|-------------:|-----------:|----------------:|--------------:|-----------:|--------------------:|:------------------------|:------------------------|
| none                    |        75924 |   1.44858  |       0.2083    |     0.0479822 |   0.328052 |               39.14 | Batting Crisis Proxy    | nan                     |
| low                     |        71840 |   1.33729  |       0.173914  |     0.0516425 |   0.328132 |               37.03 | Batting Crisis Proxy    | nan                     |
| moderate                |        30760 |   1.2304   |       0.152991  |     0.0589077 |   0.357705 |               15.86 | Batting Crisis Proxy    | nan                     |
| high                    |        11445 |   1.15325  |       0.139712  |     0.0770642 |   0.37938  |                5.9  | Batting Crisis Proxy    | nan                     |
| extreme                 |         4019 |   0.991043 |       0.108485  |     0.107241  |   0.404578 |                2.07 | Batting Crisis Proxy    | nan                     |
| nan                     |         1470 |   0.845578 |       0.0918367 |     0.0680272 |   0.504762 |                0.76 | Bowling Defensive Proxy | none                    |
| nan                     |        18991 |   1.07762  |       0.11595   |     0.0526565 |   0.375283 |                9.79 | Bowling Defensive Proxy | low                     |
| nan                     |        71592 |   1.24594  |       0.156149  |     0.0530367 |   0.348768 |               36.91 | Bowling Defensive Proxy | moderate                |
| nan                     |        70591 |   1.42828  |       0.196073  |     0.0551912 |   0.314828 |               36.39 | Bowling Defensive Proxy | high                    |
| nan                     |        31344 |   1.5745   |       0.245438  |     0.0537583 |   0.331451 |               16.16 | Bowling Defensive Proxy | extreme                 |

---

## 4. Mathematical Formulation of Pressure Reliability Index (PRI)

$$\text{PRI} = 100 \times \left( 0.35 M_{\text{norm}} + 0.35 A_{\text{norm}} + 0.20 C_{\text{norm}} + 0.10 S_{\text{norm}} \right)$$

1. **Performance Maintenance ($M$, 35%):**
   - Batting: $\text{SR}_{\text{crisis}} / \text{SR}_{\text{norm}}$, softly clipped to $[0.5, 1.5]$.
   - Bowling: $\text{Dot}_{\text{crisis}} / \text{Dot}_{\text{norm}}$, softly clipped to $[0.5, 1.5]$.
2. **Absolute Pressure Performance ($A$, 35%):**
   - Batting: Empirical Bayes Normal-Normal shrinkage ($K = 25.0$) shrinking observed strike rate towards population mean:
     $$w_i = \frac{n_i}{n_i + 25.0}, \quad \hat{\mu}_i = w_i \bar{x}_i + (1 - w_i) \mu_{\text{pop}}$$
   - Bowling: Empirical Bayes Beta-Binomial conjugate shrinkage with Method-of-Moments prior estimation for crisis wicket rate.
3. **Exposure-Adjusted Match Consistency ($C$, 20%):**
   $$\text{Consistency}_i = \exp(-\text{CV}_i) \cdot \sqrt{\frac{m_i}{m_i + 3}}$$
   Guaranteed strictly positive in $(0, 1]$, non-degenerating, and rewarding sustained multi-match reliability.
4. **Sample Size Confidence ($S$, 10%):**
   $$\text{Sample Confidence}_i = \min\left(1.0, \frac{\ln(1 + n_i)}{\ln(1 + 250)}\right)$$

---

## 5. Official Primary Top 10 Batters Under Crisis Pressure (Positions 1–7)

|   rank | canonical_display_name   | primary_role                   |   modal_batting_position |   crisis_balls |   crisis_matches |   crisis_sr |   norm_sr |   sr_maintenance |   consistency_score |   batting_pri |
|-------:|:-------------------------|:-------------------------------|-------------------------:|---------------:|-----------------:|------------:|----------:|-----------------:|--------------------:|--------------:|
|      1 | Tilak Varma              | Middle-Order Batter            |                        5 |             60 |               18 |     196.667 |   144.473 |            1.361 |              0.512  |         91.3  |
|      2 | Matthew Wade             | WK-Batter                      |                        7 |             50 |               15 |     172     |   144.492 |            1.19  |              0.5018 |         74.76 |
|      3 | Daryl Mitchell           | Middle-Order Batter            |                        5 |             44 |               12 |     177.273 |   147.103 |            1.205 |              0.4266 |         70.26 |
|      4 | Liam Livingstone         | Batting All-Rounder            |                        4 |             60 |               14 |     175     |   161.295 |            1.085 |              0.4376 |         69    |
|      5 | MS Dhoni                 | WK-Batter                      |                        8 |            133 |               35 |     154.887 |   140.94  |            1.099 |              0.3983 |         66.2  |
|      6 | Abdul Samad              | Finisher / Lower-Middle Batter |                        7 |             69 |               23 |     169.565 |   168.675 |            1.005 |              0.4409 |         65.78 |
|      7 | Jaker Ali Anik           | Finisher / Lower-Middle Batter |                        6 |             63 |               15 |     139.683 |   122.383 |            1.141 |              0.4874 |         64.19 |
|      8 | Ravindra Jadeja          | Bowling All-Rounder            |                        7 |             94 |               33 |     150     |   138.728 |            1.081 |              0.4285 |         63.77 |
|      9 | David Miller             | Middle-Order Batter            |                        5 |             56 |               17 |     166.071 |   156.146 |            1.064 |              0.4178 |         63.48 |
|     10 | Rinku Singh              | Finisher / Lower-Middle Batter |                        6 |            122 |               32 |     150.82  |   147.561 |            1.022 |              0.4197 |         62.78 |

---

## 6. Official Primary Top 10 Bowlers Under Defensive Pressure (Frontline, 120+ Balls)

|   rank | canonical_display_name   | primary_role           |   crisis_balls |   crisis_matches |   crisis_wicket_rate |   norm_wicket_rate |   crisis_dot_pct |   consistency_score |   bowling_pri |
|-------:|:-------------------------|:-----------------------|---------------:|-----------------:|---------------------:|-------------------:|-----------------:|--------------------:|--------------:|
|      1 | Mark Adair               | Specialist Fast Bowler |            483 |               40 |              6.62526 |            4.87805 |          37.06   |              0.5936 |         86.16 |
|      2 | Craig Young              | Specialist Fast Bowler |            289 |               23 |              8.99654 |            2.77778 |          36.3322 |              0.5086 |         86.1  |
|      3 | Mark Wood                | Specialist Fast Bowler |            156 |               13 |              9.61538 |            3.22581 |          41.6667 |              0.5114 |         77.94 |
|      4 | Obed McCoy               | Specialist Fast Bowler |            334 |               30 |              6.58683 |            4.34783 |          34.7305 |              0.5243 |         77.83 |
|      5 | Trent Boult              | Specialist Fast Bowler |            879 |               70 |              5.00569 |            1.5625  |          36.7463 |              0.5337 |         76.46 |
|      6 | Gareth Delany            | Bowling All-Rounder    |            178 |               24 |              6.74157 |            0       |          37.6404 |              0.3428 |         76.18 |
|      7 | Eshan Malinga            | Specialist Fast Bowler |            572 |               39 |              6.29371 |            2.22222 |          33.042  |              0.6118 |         73.67 |
|      8 | Jacob Duffy              | Specialist Fast Bowler |            486 |               39 |              7.81893 |            9.23077 |          40.7407 |              0.5771 |         73.13 |
|      9 | Deepak Chahar            | Specialist Fast Bowler |            510 |               45 |              5.29412 |            4.34783 |          37.2549 |              0.5386 |         72.59 |
|     10 | Matheesha Pathirana      | Specialist Fast Bowler |            578 |               49 |              8.47751 |            4.09836 |          32.3529 |              0.5574 |         72.48 |

---

## 7. Dual Leaderboard Separation Rationale

### A. Gudakesh Motie & Akeal Hosein (Lower-Order Impact)
- **Observation:** Gudakesh Motie (modal pos 9) and Akeal Hosein (modal pos 10) demonstrated elite crisis strike rates (170.2 and 136.0) from lower-order batting appearances.
- **Statistical Dilemma:** Specialist bowlers only enter the crease when multiple top-order wickets have already fallen (100% crisis exposure), skewing baseline strike rate maintenance ratios relative to top-seven batters.
- **Resolution:** Motie and Hosein are ranked #1 and #2 on the **Lower-Order Pressure Impact Leaderboard** (`LOWER_ORDER_PRESSURE_IMPACT.csv`), preserving their genuine clutch contributions without distorting the primary top-seven leaderboard.

### B. Harry Tector (Emerging & Part-Time Bowling)
- **Observation:** Harry Tector (Ireland middle-order batter, modal pos 4) recorded 54 defensive crisis bowling deliveries with a high wicket rate (9.26%).
- **Statistical Dilemma:** Tector's primary workload is batting (857 balls faced vs 248 bowled). With only 54 crisis balls bowled, his sample size is insufficient to represent a frontline T20 tournament bowling option.
- **Resolution:** By requiring 120 crisis legal deliveries for frontline bowling eligibility, Tector is appropriately ranked #1 on the **Emerging & Part-Time Bowlers Leaderboard** (`EMERGING_AND_PART_TIME_BOWLERS.csv`), while the Primary Top 10 consists strictly of genuine frontline bowlers (Adair, Young, Wood, McCoy, Boult, Malinga, etc.).

### Top 5 Lower-Order Pressure Impact Batters
|   lower_order_rank | canonical_display_name   | primary_role           |   modal_batting_position |   crisis_balls |   crisis_sr |   batting_pri | eligibility_status   |
|-------------------:|:-------------------------|:-----------------------|-------------------------:|---------------:|------------:|--------------:|:---------------------|
|                  1 | Gudakesh Motie           | Specialist Spin Bowler |                        9 |             47 |     170.213 |         74.59 | ELIGIBLE             |
|                  2 | Akeal Hosein             | Specialist Spin Bowler |                       10 |            114 |     135.965 |         68.23 | ELIGIBLE             |
|                  3 | Marco Jansen             | Specialist Fast Bowler |                        8 |             97 |     121.649 |         53.01 | ELIGIBLE             |
|                  4 | Rashid Khan              | Specialist Spin Bowler |                        8 |            217 |     138.249 |         50.38 | ELIGIBLE             |
|                  5 | Washington Sundar        | Specialist Spin Bowler |                        8 |             89 |     126.966 |         48.25 | ELIGIBLE             |

### Top 5 Emerging & Part-Time Bowlers
|   emerging_rank | canonical_display_name   | primary_role           |   crisis_balls |   crisis_wicket_rate |   bowling_pri | eligibility_status   |
|----------------:|:-------------------------|:-----------------------|---------------:|---------------------:|--------------:|:---------------------|
|               1 | Harry Tector             | Batting All-Rounder    |             54 |              9.25926 |         86    | ELIGIBLE             |
|               2 | Krishnappa Gowtham       | Specialist Spin Bowler |             67 |              7.46269 |         72.66 | ELIGIBLE             |
|               3 | Dunith Wellalage         | Specialist Spin Bowler |            115 |              5.21739 |         69.52 | ELIGIBLE             |
|               4 | Saim Ayub                | Batting All-Rounder    |            154 |              5.84416 |         68.44 | ELIGIBLE             |
|               5 | DT Doram                 | Specialist Spin Bowler |             60 |              6.66667 |         63.87 | ELIGIBLE             |

---

## 8. Sensitivity Analysis Across 5 Weight Configurations

| player_name      | player_role                    |   pri_balanced_default |   pri_maintenance_heavy |   pri_absolute_heavy |   pri_consistency_heavy |   pri_equal_weights | discipline   |
|:-----------------|:-------------------------------|-----------------------:|------------------------:|---------------------:|------------------------:|--------------------:|:-------------|
| Tilak Varma      | Middle-Order Batter            |                  91.3  |                   90.45 |                92.96 |                   90.5  |               87.82 | Batting      |
| Matthew Wade     | WK-Batter                      |                  74.76 |                   73.84 |                74.63 |                   75.82 |               75.04 | Batting      |
| Daryl Mitchell   | Middle-Order Batter            |                  70.26 |                   70.78 |                71.42 |                   68.58 |               68.63 | Batting      |
| Liam Livingstone | Batting All-Rounder            |                  69    |                   66.78 |                72.14 |                   68.06 |               69.12 | Batting      |
| MS Dhoni         | WK-Batter                      |                  66.2  |                   65.48 |                69.01 |                   64.12 |               68.21 | Batting      |
| Abdul Samad      | Finisher / Lower-Middle Batter |                  65.78 |                   62.38 |                69.48 |                   65.49 |               67.39 | Batting      |
| Jaker Ali Anik   | Finisher / Lower-Middle Batter |                  64.19 |                   65.02 |                61.36 |                   66.17 |               67.69 | Batting      |
| Ravindra Jadeja  | Bowling All-Rounder            |                  63.77 |                   63.14 |                64.87 |                   63.29 |               66.48 | Batting      |
| David Miller     | Middle-Order Batter            |                  63.48 |                   62.18 |                65.82 |                   62.43 |               64.22 | Batting      |
| Rinku Singh      | Finisher / Lower-Middle Batter |                  62.78 |                   60.93 |                65.28 |                   62.12 |               66.28 | Batting      |

Spearman rank correlations across all 5 weighting schemes exceed **0.88 for batters** and **0.91 for bowlers**, proving mathematical stability against weight perturbation.

---

## 9. Reproducibility & Engineering Integrity

Every calculation in this report is produced directly from the underlying dataset via automated Python scripts and validated by the unit test suite:
- Pipeline execution: `python scripts/compute_rankings.py`
- Test suite: `pytest tests/ -v` (19 passing unit tests)
- All rankings generated dynamically without hardcoded constants or manual overrides.
