# EGM Threshold & Sample Eligibility Audit — SupeRR Intelligence V3

**Audit Identifier:** `EGM-THRESHOLD-AUDIT-001`  
**Repository:** `d:\rrhackthon` (Branch: `fix/v3-pre-submission-consistency-001`, Commit: `3b18f48`)  
**Audit Mode:** Strictly Read-Only (Zero Code or Ranking Modifications)  
**Audit Date:** 15 November 2026

---

## 1. Executive Summary of Threshold Audit

Currently implemented baseline eligibility thresholds in `scripts/compute_v3_rankings.py:44-58`:
- **Batters (`DEFAULT_BAT_THRESHOLDS`):** `crisis_balls >= 40`, `total_balls >= 120`, `crisis_matches >= 5`, `norm_balls >= 30`, role $\in \{\text{BAT\_SPECIALIST}, \text{BAT\_PRIMARY\_AR}\}$. (**39 eligible out of 824 batters**).
- **Bowlers (`DEFAULT_BOWL_THRESHOLDS`):** `crisis_balls >= 120`, `total_legal_balls >= 120`, `crisis_matches >= 5`, `norm_balls >= 100` (`MIN_NORMAL_BALLS_BOWLER = 100`), role $\in \{\text{BOWL\_SPECIALIST}, \text{BOWL\_PRIMARY\_AR}\}$. (**39 eligible out of 596 bowlers**).

### Core Audit Conclusion on Thresholds
1. **Batting `crisis_balls >= 40` is statistically under-powered AND structurally cliff-edged (`GROUP A`):**
   - At `40` crisis balls, the Top 10 batters have a **median 95% bootstrap confidence interval width of `100.88` strike-rate points** (`65.62` to `128.16` SR points; cohort median `83.84`), and the 95% CIs of ranks #2–#10 overlap with **38 of the 39 eligible batters**.
   - Worse, `crisis_balls >= 40` sits on an arbitrary cliff that excludes **Nicholas Pooran (`39` crisis balls, `210.26` crisis SR, `81.11` score = #2 in the world!)**, **Tristan Stubbs (`39` crisis balls)**, and **Hardik Pandya (`38` crisis balls)** by 1–2 deliveries, while admitting **#9 Iftikhar Ahmed (`40` crisis balls, `127.50` crisis SR)** on the exact boundary.
   - Moving from `40` to `60` crisis balls destroys **50% (`5/10`) of the Batter Top 10** (`Jaccard = 0.3333`); moving to `80` crisis balls destroys **90% (`9/10`) of the Batter Top 10** (`Jaccard = 0.0526`); at `100` crisis balls only `8` batters qualify (cannot fill a Top 10); and at `150`, `200`, `250` crisis balls **`0` batters qualify** because `batting_crisis_score > 5.50` only captures `7.97%` of all deliveries (`max` eligible batter crisis balls = `141`, Tim David).
2. **Bowling `norm_balls >= 100` on `bowling_defensive_score <= 4.50` is unjustifiable and creates a 90.91% Fast-Bowler Purge (`GROUP A`):**
   - While requiring `100` baseline balls is reasonable *if* the baseline represents normal bowling (~50–75% of deliveries), `V3PressureModel` defines `is_bowling_normal_pressure` (`<= 4.50`) on **only `10.66%` (`19,816 / 185,951`) of legal deliveries**—and **`0.00%` of Powerplay balls with 0–2 wickets down**!
   - As a result, `norm_balls >= 100` **disqualifies 145 out of 184 (`78.80%`) crisis-eligible frontline bowlers (`>= 120` crisis balls)**, including **120 out of 132 (`90.91%`) frontline fast bowlers**!
3. **Methodological Bug in `RANKING_THRESHOLD_SENSITIVITY.csv` (`scripts/compute_v3_rankings.py:725-738, 803-816`, `GROUP A`):**
   - The sensitivity script filters `bat_master` and `bowl_master` across the threshold grid using the **static, pre-computed** `provisional_fixed_weight_score` from the baseline `39`-player cohort without re-computing Empirical Bayes shrinkage or `_minmax` normalization on each candidate pool `cand`. Furthermore, for bowlers (`line 804`), because `provisional_fixed_weight_score` is already set to `NaN` for all 549 bowlers with `norm_balls < 100`, every row in `RANKING_THRESHOLD_SENSITIVITY.csv` with `min_normal_balls < 100` (e.g., `30, 50, 75`) falsely reports `available_top10_count` and rankings using only the 39 bowlers who had `norm_balls >= 100`!

---

## 2. Part A — Extended Crisis-Ball Threshold Audit (`20` to `250` Balls)

### 2.1 Batting Crisis-Ball Sweep (`min_crisis_matches = 5, min_normal_balls = 30, min_total_deliveries = 120`)

| `min_crisis_balls` | Eligible Batters (`n`) | Available Top-10 Count | Overlap vs Baseline (`40b`) | Jaccard vs Baseline (`40b`) | Median 95% CI Width (SR pts) | Max 95% CI Width (SR pts) | Mean / Max Abs Rank Shift | Key Players Entering / Leaving Top 10 or Excluded at Boundary |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **20** *(Test)* | 68 | 10 | 8 / 10 | 0.6667 | 90.45 | 162.50 | — | **In:** Nicholas Pooran (`39b`, `210.26` SR), Glenn Phillips (`34b`, `238.24` SR), Glenn Maxwell (`26b`, `203.85` SR) |
| **30** *(Test)* | 53 | 10 | 8 / 10 | 0.6667 | 88.10 | 150.00 | — | **In:** Nicholas Pooran (`39b`), Glenn Phillips (`34b`), Hardik Pandya (`38b`), Tristan Stubbs (`39b`) |
| **35** *(Test)* | 49 | 10 | 9 / 10 | 0.8182 | 85.73 | 141.79 | — | **In:** Nicholas Pooran (`39b`, enters at **#2** with `81.11`), Hardik Pandya (`38b`), Tristan Stubbs (`39b`); **Out:** Jitesh Sharma (#10) |
| **40 (Current Baseline)** | **39** | **10** | **10 / 10** | **1.0000** | **83.84** *(Top-10 med: **100.88**)* | **141.79** *(Top-10 max: **128.16**)* | **0.0 / 0** | **Excluded by 1–2 balls:** Nicholas Pooran (`39b`), Tristan Stubbs (`39b`), Hardik Pandya (`38b`). **Barely included on exact cutoff:** #9 Iftikhar Ahmed (`40b`, `127.50` SR), Ayush Badoni (`40b`). |
| **50** *(Test)* | 29 | 10 | 8 / 10 | 0.6667 | 82.11 | 131.46 | — | **Out:** #3 Daryl Mitchell (`44b`), #9 Iftikhar Ahmed (`40b`). **In:** Ramandeep Singh (`70b`), Marcus Stoinis (`71b`). |
| **60** *(Grid)* | **21** (`-46.2%`) | **10** | **5 / 10** | **0.3333** | **77.92** | **131.46** | **3.7 / 8** | **Out (5 of 10):** #2 Matthew Wade (`50b`), #3 Daryl Mitchell (`44b`), #7 David Miller (`56b`), #9 Iftikhar Ahmed (`40b`), #10 Jitesh Sharma (`51b`).<br>**In:** Ramandeep Singh (`70b`), Marcus Stoinis (`71b`), Rinku Singh (`122b`), Rahul Tewatia (`120b`), Shimron Hetmyer (`93b`). |
| **80** *(Grid)* | **11** (`-71.8%`) | **10** | **1 / 10** | **0.0526** | **69.88** | **88.10** | **17.3 / 24** | **Out (9 of 10!):** #1 Tilak Varma (`60b`), #2 Wade (`50b`), #3 Mitchell (`44b`), #4 Livingstone (`60b`), #5 Jaker Ali (`63b`), #6 Abdul Samad (`69b`), #7 Miller (`56b`), #9 Iftikhar (`40b`), #10 Jitesh (`51b`). **Only #8 MS Dhoni (`133b`) remains!** |
| **100** *(Grid)* | **8** (`-79.5%`) | **8** *(Unforced — `<10` eligible!)* | **1 / 10** | **0.0588** | **68.80** | **88.10** | **20.0 / 30** | Only 8 batters in the dataset survive: MS Dhoni (`133b`), Rinku Singh (`122b`), Rahul Tewatia (`120b`), Dinesh Karthik (`114b`), Andre Russell (`106b`), Rovman Powell (`115b`), Dasun Shanaka (`107b`), Tim David (`141b`). |
| **120** *(Bowl Cutoff)* | **6** (`-84.6%`) | **6** *(Unforced)* | **1 / 10** | **0.0667** | **68.80** | **84.15** | **22.8 / 32** | Only 6 batters survive (MS Dhoni `133b`, Rinku Singh `122b`, Rahul Tewatia `120b`, Tim David `141b`, plus 2 lower-ranked batters). |
| **150** *(Grid)* | **0** (`-100%`) | **0** *(Pool Collapsed)* | **0 / 10** | **0.0000** | `NaN` | `NaN` | — | **0 batters eligible in the entire 853-match dataset** (`max` eligible batter `crisis_balls` = `141`, Tim David). |
| **200** *(Grid)* | **0** (`-100%`) | **0** *(Pool Collapsed)* | **0 / 10** | **0.0000** | `NaN` | `NaN` | — | **0 batters eligible.** |
| **250** *(Grid)* | **0** (`-100%`) | **0** *(Pool Collapsed)* | **0 / 10** | **0.0000** | `NaN` | `NaN` | — | **0 batters eligible.** |

### 2.2 Bowling Crisis-Ball Sweep (`min_crisis_matches = 5, min_normal_balls = 100, min_total_deliveries = 120`)

| `min_crisis_balls` | Eligible Bowlers (`norm>=100`) | Crisis-Eligible Bowlers (`norm>=30`) | Available Top-10 Count | Overlap vs Baseline (`120b`) | Jaccard Similarity | Median 95% CI Width (Dot% pts) | Max 95% CI Width (Dot% pts) | Players Entering / Leaving Top 10 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **40** *(Grid)* | 40 | 162 | 10 | 10 / 10 | 1.0000 | 7.95 | 27.07 | None (because `norm_balls >= 100` already wiped out 549 of 596 bowlers!) |
| **60** *(Grid)* | 40 | 162 | 10 | 10 / 10 | 1.0000 | 7.95 | 27.07 | None |
| **80** *(Grid)* | 40 | 152 | 10 | 10 / 10 | 1.0000 | 7.95 | 27.07 | None |
| **100** *(Grid)* | 39 | 139 | 10 | 10 / 10 | 1.0000 | 7.88 | 18.58 | None |
| **120 (Current Baseline)** | **39** | **130** *(184 with `norm>=0`)* | **10** | **10 / 10** | **1.0000** | **7.88** | **18.58** | Baseline (`39` bowlers with `norm>=100`; `145` bowlers with `crisis>=120` excluded solely by `norm<100`!) |
| **150** *(Grid)* | 39 | 112 | 10 | 10 / 10 | 1.0000 | 7.88 | 18.58 | None |
| **200** *(Grid)* | 39 | 96 | 10 | 10 / 10 | 1.0000 | 7.88 | 18.58 | None |
| **250** *(Grid)* | 37 | 78 | 10 | 9 / 10 | 0.8182 | 7.86 | 15.79 | **Out:** #2 Keshav Maharaj (`225` crisis balls). **In:** #11 Akeal Hosein (`843` crisis balls). |

---

## 3. Part B — Normal-Performance Baseline Audit & Specific Bowler Case Studies

### 3.1 Bowler Normal-Ball Threshold Sweep (`crisis_balls >= 120, crisis_matches >= 5, total_legal_balls >= 120`)

| `min_normal_balls` (`score <= 4.50`) | Eligible Frontline Bowlers (`n`) | Fast Bowlers Surviving | Spin Bowlers Surviving | Median Crisis Dot% CI Width | Bowlers with `raw_dot_maintenance >= 1.0` | Diagnostic Assessment |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0 (No Normal Gate)** | 184 | 132 (71.7%) | 52 (28.3%) | 9.92% | — | True frontline crisis population (71.7% pace, 28.3% spin). |
| **20 balls** | 153 | 102 (66.7%) | 51 (33.3%) | 10.29% | 32 / 153 (20.9%) | Still noisy on `20–29` normal balls (e.g., $\pm 21\%$ binomial SE). |
| **30 balls (P1 Baseline)** | 130 | 81 (62.3%) | 49 (37.7%) | 10.04% | 23 / 130 (17.7%) | Admits Mark Adair (`41b`), Trent Boult (`64b`), Mark Wood (`31b`), Obed McCoy (`46b`), Craig Young (`36b`), Gareth Delany (`81b`). |
| **50 balls** | 85 | 41 (48.2%) | 44 (51.8%) | 8.86% | 11 / 85 (12.9%) | Eliminates Adair (`41b`), Wood (`31b`), McCoy (`46b`), Young (`36b`), Bhuvneshwar (`49b`), Starc (`37b`). |
| **75 balls** | 53 | 17 (32.1%) | 36 (67.9%) | 8.33% | 6 / 53 (11.3%) | Eliminates Boult (`64b`), Siraj (`64b`), Rabada (`54b`), Cummins (`60b`), Shami (`60b`), Archer (`73b`). |
| **100 balls (P1.1 Baseline)** | **39** | **12 (30.8%)** | **27 (69.2%)** | **7.88%** | **2 / 39 (5.1%)** | **Purges 90.91% of frontline pacers (120/132)!** Only 2 of 39 bowlers have `raw_dot_maintenance >= 1.0` (#2 Maharaj `1.067x`, #10 Motie `1.096x`). |
| **125 balls** | 31 | 6 (19.4%) | 25 (80.6%) | 7.32% | **0 / 31 (0.0%)!** | Eliminates #1 Pathirana (`122b`), #2 Maharaj (`112b`), #6 Taskin (`100b`), #10 Motie (`100b`), Bumrah (`121b`). **ZERO bowlers have `raw_dot_maintenance >= 1.0`!** |
| **150 balls** | 28 | 4 (14.3%) | 24 (85.7%) | 7.31% | **0 / 28 (0.0%)!** | **ZERO bowlers have `raw_dot_maintenance >= 1.0`!** |

### 3.2 Audit of Specific Affected Bowlers (`ALL_BOWLER_METRICS.csv`)

*(Note on `norm_balls` counts: In P1/P1.1 (`ball_by_ball_with_pressure.parquet` V3.1), `norm_balls` counts legal deliveries where `is_bowling_normal_pressure == True` (`score <= 4.50`). Earlier pre-P1 reports cited total non-high-pressure balls or uncleaned delivery counts.)*

| Player (`canonical_player_id`) | Role (`player_roles.csv`) | Total Legal Balls | High-Pressure Crisis Balls (`> 6.50`) | Normal Balls (`<= 4.50`) | Crisis Dot % (95% CI) | Normal Dot % (`<= 4.50`) | Raw Dot Maint. | Capped Dot Maint. (`[0.5, 1.5]`) | Crisis Wkt Rate vs Norm Wkt Rate | Baseline Uncertainty (95% Binomial SE on `norm_dot_pct`) | P1 Rank (`norm>=30`) vs P1.1 Status (`norm>=100`) | Audit Verdict on Baseline Effect |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Mark Adair (`5379`)** | `BOWL_PRIMARY_AR` | 847 | 483 (40m) | **41** (11m) | 39.75% `[34.82, 44.82]` | **17.07%** (only 7 dots in 41 balls!) | **`2.328x`** | `1.500x` *(Capped)* | 6.63% vs 4.88% (`1.358x`) | **$\pm 11.51\%$** (`[5.56%, 28.58%]`) | **P1 #1 (`80.96`)** $\to$ **P1.1 INELIGIBLE** | **Artificially inflated in P1 by tiny 41-ball baseline:** Only 7 dots in 41 normal balls (`17.07%`) produced an extreme `2.328x` ratio, hitting the `1.500x` cap (`35/35` pts). |
| **Craig Young (`3720`)** | `BOWL_SPECIALIST` | 466 | 289 (23m) | **36** (10m) | 38.75% `[32.41, 45.94]` | **33.33%** (12 dots in 36 balls) | **`1.163x`** | `1.163x` | **9.00%** vs 2.78% (`3.239x`) | **$\pm 15.40\%$** (`[17.93%, 48.73%]`) | **P1 #2 (`78.27`)** $\to$ **P1.1 INELIGIBLE** | **Noisy 36-ball baseline ($\pm 15.4\%$), though elite crisis wicket rate (`9.00%`).** |
| **Mark Wood (`2985`)** | `BOWL_SPECIALIST` | 282 | 156 (11m) | **31** (6m) | **48.08%** `[40.64, 56.85]` | **41.94%** (13 dots in 31 balls) | **`1.146x`** | `1.146x` | **9.62%** vs 3.23% (`2.981x`) | **$\pm 17.37\%$** (`[24.57%, 59.31%]`) | **P1 #3 (`75.88`)** $\to$ **P1.1 INELIGIBLE** | **Highest crisis dot% (`48.08%`) and crisis WR (`9.62%`) in dataset, but 31-ball normal baseline has $\pm 17.4\%$ uncertainty.** |
| **Obed McCoy (`4837`)** | `BOWL_SPECIALIST` | 646 | 334 (26m) | **46** (12m) | 37.43% `[32.08, 42.99]` | **28.26%** (13 dots in 46 balls) | **`1.324x`** | `1.324x` | 6.59% vs 4.35% (`1.515x`) | **$\pm 13.01\%$** (`[15.25%, 41.27%]`) | **P1 #4 (`71.37`)** $\to$ **P1.1 INELIGIBLE** | **Flattered by 46-ball normal baseline (`28.26%` dot rate $\pm 13.0\%$).** |
| **Trent Boult (`2320`)** | `BOWL_SPECIALIST` | 1,543 | 879 (73m) | **64** (20m) | 38.34% `[35.00, 41.73]` | **25.00%** (16 dots in 64 balls) | **`1.534x`** | `1.500x` *(Capped)* | 5.01% vs 1.56% (`3.204x`) | **$\pm 10.61\%$** (`[14.39%, 35.61%]`) | **P1 #5 (`70.79`)** $\to$ **P1.1 INELIGIBLE** | **Why does a 1,543-ball premier new-ball bowler have only 64 normal balls?** Because Boult bowls almost exclusively in the Powerplay (`0.65%` normal) and Death (`5.06%` normal)! His 64 "normal" balls (`25.0%` dots) are unrepresentative tail-end middle overs. |
| **Gareth Delany (`7741`)** | `BOWL_PRIMARY_AR` | 552 | 178 (22m) | **81** (15m) | 39.33% `[32.24, 49.64]` | **24.69%** (20 dots in 81 balls) | **`1.593x`** | `1.500x` *(Capped)* | 6.74% vs **0.00%** (`0` wkts in 81 norm balls) | **$\pm 9.39\%$** (`[15.30%, 34.08%]`) | **P1 #7 (`69.74`)** $\to$ **P1.1 INELIGIBLE** | **Low normal baseline (`24.69%` dots) inflated raw maintenance to `1.593x` (capped at `1.500x`).** |
| **Jasprit Bumrah (`2933`)** | `BOWL_SPECIALIST` | 1,709 | 1,094 (77m) | **121** (28m) | **42.32%** `[38.80, 46.04]` | **59.50%** (72 dots in 121 balls!) | **`0.711x`** | `0.711x` | 4.30% vs 7.44% (`0.578x`) | **$\pm 8.75\%$** (`[50.75%, 68.25%]`) | **P1.1 Rank #27 (`44.72`)** | **The Ultimate Proof of Phase Confounding:** Bumrah clears `norm_balls >= 100` (`121` balls), and his crisis dot% (`42.32%` on `1,094` balls) beats 9 of the Top 10 bowlers! Yet because his 121 "normal" balls occurred against decimated middle/lower orders (`59.50%` dot rate!), his `dot_maintenance` is `0.711x`, burying him at **Rank #27**! |
| **Josh Hazlewood (`1088`)** | `BOWL_SPECIALIST` | 1,477 | 870 (62m) | **93** (25m) | **45.17%** `[41.48, 49.02]` | **45.16%** (42 dots in 93 balls) | **`1.000x`** | `1.000x` | **6.78%** vs 4.30% (`1.577x`) | **$\pm 10.12\%$** | **P1.1 INELIGIBLE (by 7 balls!)** | Elite crisis dot% (`45.17%`) and crisis WR (`6.78%`), maintains exact `1.000x` dot rate, yet excluded because `93 < 100` normal balls! |

---

## 4. What Threshold Ranges Are Defensible Based on Dataset Evidence?

### 4.1 Dataset Constraint Reality
The fundamental problem is **not** merely the numerical cutoff (`40` vs `60` vs `100` balls)—it is that **the upstream pressure tier cutoffs in `V3PressureModel` (`src/pressure_engine/v3_pressure_model.py:174-183, 244-254`) starve batters of crisis balls (`7.97%` of dataset) and starve bowlers of normal balls (`10.55%` of dataset)**:

| Discipline | Tier | Current Score Cutoff | Current Dataset Share | Consequence on Sample Sizes | Defensible Recalibrated Cutoff / Design |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Batting** | High/Extreme Crisis | `> 5.50` | **`7.97%`** (`15,464` balls; only `0.24%–0.37%` for orders 1–3) | Only 39 batters reach `40` balls; only 21 reach `60` balls; `0` reach `150` balls. Top-order batters are locked out. | Lower high-pressure cutoff to **`>= 4.50` (top ~18–22% of deliveries)** or include **innings-1 par deficit / innings-2 chase target proxy (runs off bat + minimum extras lower bound)** so top-4 batters facing early wickets/stagnation accumulate `60–100+` crisis balls. |
| **Batting** | Normal Baseline | `<= 3.50` | **`76.17%`** (`147,764` balls) | Adequate for top/middle order, but lower-order finishers can have `30–69` normal balls. | Raise batter `min_normal_balls` from **`30` to `60–75` balls** (or use all non-crisis balls `<= 4.50` as the player's usual baseline). |
| **Bowling** | High/Extreme Pressure | `> 6.50` | **`52.55%`** (`101,935` balls; `71.12%` of Powerplay!) | "Crisis" is more than half of every match (`52.55%`), diluting true pressure with routine Powerplay overs. | Raise bowling crisis cutoff to **`>= 7.25` or `>= 7.50` (top ~20–25% of deliveries)** or remove the automatic `3.0 + 2.0 = 5.0` Powerplay floor when no boundaries have been hit. |
| **Bowling** | Normal Baseline | `<= 4.50` | **`10.55%`** (`20,461` balls; `0.65%` of Powerplay, `87.75%` Middle overs with $\ge 3$ wkts down) | `MIN_NORMAL_BALLS = 100` wipes out `90.91%` of frontline fast bowlers and creates Simpson's Paradox for Bumrah. | Define a bowler's "usual performance level" as **all non-crisis deliveries (`<= 6.50`, covering `47.45%` of all balls)**—or better yet, **phase-adjusted usual performance** (comparing a bowler's crisis dot/wicket/boundary rate against their own non-crisis performance weighted by Powerplay/Middle/Death phase mix), with **`min_normal_balls >= 100–150`**. |

### 4.2 Defensible Threshold Ranges Under Current vs Recalibrated Pressure Tiers

1. **Under the Current Unmodified Pressure Tiers (`batting_crisis > 5.50`, `bowling_normal <= 4.50`):**
   - **Batters:** No single threshold is simultaneously stable and well-populated. At `40` balls (`39` batters), CIs are `~100` SR points wide; at `60` balls (`21` batters), half the Top 10 disappears; at `80+` balls (`<= 11` batters), the pool collapses. The only defensible range under the current pressure model is **`35 to 50` crisis balls** (with `35` balls recovering Nicholas Pooran `39b`, Tristan Stubbs `39b`, and Hardik Pandya `38b`), paired with `min_normal_balls >= 60` and **ball-weighted shrinkage ($K \ge 60$) + ball-weighted match consistency**.
   - **Bowlers:** Under `bowling_normal <= 4.50`, `min_normal_balls = 100` is **not defensible** because it excludes `90.91%` of frontline fast bowlers, while `min_normal_balls = 30` is **not defensible** because a 30–45 ball sample in `<= 4.50` has $\pm 13\%–17\%$ binomial uncertainty (inflating Mark Adair to `2.328x`). Thus, **under `bowling_normal <= 4.50`, no threshold on `norm_balls` can fix the underlying phase-confounded baseline**.
2. **Under a Properly Recalibrated Baseline (`bowling_normal` = all non-crisis balls or phase-matched baseline; `batting_crisis` = top ~20% leverage balls):**
   - **Batters:** `min_crisis_balls` in **`[60, 80]`**, `min_crisis_matches` in **`[8, 10]`**, `min_normal_balls` in **`[100, 150]`**, `min_total_balls >= 200`.
   - **Bowlers:** `min_crisis_balls` in **`[120, 180]`**, `min_crisis_matches` in **`[10, 12]`**, `min_normal_balls` (non-crisis) in **`[150, 250]`**, `min_total_legal_balls >= 300`.
