# SupeRR Intelligence: Complete Project Forensic Audit
**Project:** SupeRR Intelligence — Rajasthan Royals SupeRR Selector Season 2 Hackathon  
**Audit Conducted By:** Independent Multidisciplinary Research Team  
**Evaluation Scope:** Codebase, Data Pipelines, Statistical Models, Ranking Engines, and Outputs  
**Repository Location:** `D:\rrhackthon\`  
**Date:** November 12, 2026  
**Status:** Forensic Audit Complete (Read-Only Analysis)  

---

## 1. Executive Forensic Summary

This forensic audit represents an independent, critical inspection of the entire SupeRR Intelligence codebase, data pipelines, statistical formulations, and generated deliverables.
While the project exhibits high software engineering hygiene (modular directory structures, clean code formatting, unit test coverage, and ReportLab PDF compilation), our forensic investigation reveals **critical conceptual, statistical, and domain-level flaws** that undermine the scientific defensibility of its player rankings.

### Primary Forensic Findings:
1. **The Batting Crisis Model is a Wicket-Depletion / Tailender Proxy, NOT Match Pressure:**
   Empirical audit of the 193,988 regular deliveries demonstrates that **60.57% of all "batting crisis" deliveries occur when batting positions 8–11 are at the crease**, while top-order batters (positions 1–3) experience crisis on only **0.29% of their balls** (accounting for just 1.79% of all crisis deliveries in the dataset). Top-order batters in tight chases are systematically deprived of pressure observations, while tailenders batting in hopeless blowouts are marked as facing extreme pressure.
2. **Innings 1 and Innings 2 are Formulated Identically Without Chase Dynamics:**
   The pressure models do not incorporate target scores, runs required, balls remaining, or Required Run Rate (RRR). Innings 1 (setting a target) and Innings 2 (chasing) exhibit nearly identical crisis rates (7.49% vs 8.51%), ignoring that T20 pressure is fundamentally driven by chase leverage.
3. **Delivery-Level Score Reconstruction Incurs a $\pm 8.0$ Run Standard Deviation:**
   Because `extras1_runs` is an enumeration codebook (1: Overstep, 2: wide, 3: legbyes, etc.) and `runs` is strictly off-the-bat, individual extra run counts (e.g. 5 wides or boundary leg-byes) are unrecorded. Testing reconstructed scores against official victory margins reveals that **only 31.8% of matches match exactly**, with a standard deviation of 8.0 runs.
4. **Bowling "Normal Baseline" is Severely Sample-Starved:**
   Because the Bowling Defensive Pressure model classifies 52.55% of deliveries as High/Extreme and 36.91% as Moderate, only **10.55% of all deliveries remain in the "Normal" baseline**. Elite frontline bowlers (e.g., Mark Adair with 483 crisis balls vs 41 normal balls; Trent Boult with 879 crisis balls vs 64 normal balls) have tiny, volatile baseline samples, causing erratic maintenance ratios.
5. **The Claimed "Empirical Bayes" Normal-Normal Shrinkage is Heuristic:**
   In `src/ranking_engine/pressure_rankings.py`, the shrinkage parameter $K$ is **hardcoded as a constant $25.0$** (`prior_k = 25.0`), and the computed population variance `pop_var` is never referenced. The shrinkage of the strike rate is a fixed pseudo-sample weighting rather than a true conjugate empirical Bayes fit.
6. **The Performance Maintenance Metric (35% Weight) is Completely Unshrunk:**
   The Performance Maintenance ratio ($M = \text{Crisis SR} / \text{Normal SR}$) receives 35% of the composite PRI score but undergoes **no Bayesian shrinkage whatsoever**. It is merely clamped to $[0.5, 1.5]$, leaving rankings highly sensitive to small baseline denominator noise.

---

## 2. End-to-End Pipeline Execution Trace

The actual execution flow of SupeRR Intelligence was traced across all 11 stages:

```
[Raw CSVs in data/]
   ├── ball_by_ball_ipl_t20i.csv (194,014 rows)
   ├── matches_ipl_t20i.csv (853 matches)
   └── playing_eleven_ipl_t20i.csv (27,393 rows)
         │
         ▼ (src/preprocessing/cleaner.py)
[Preprocessing: extras mapped to categorical enum, 26 Super Over balls quarantined]
         │
         ▼ (src/context_engine/)
[Match Context: cumulative wickets fallen, 12-ball rolling windows, batter balls faced]
         │
         ▼ (src/pressure_engine/pressure_model.py)
[Dual Pressure: compute_batting_pressure() & compute_bowling_pressure()]
         │
         ▼ (data/features/ball_by_ball_with_pressure.parquet)
[Feature Store: 193,988 regular deliveries annotated with tiers]
         │
         ▼ (src/classification/role_classifier.py)
[Role Classification & Aliases: 1,118 players classified via modal batting order & workload]
         │
         ▼ (src/ranking_engine/pressure_rankings.py)
[Player Baselines & PRI Calculation: Tripartite aggregation, EB shrinkage, Consistency score]
         │
         ▼ (src/ranking_engine/pressure_rankings.py)
[Dual Leaderboards: Positions 1-7 primary filter, 120+ crisis balls frontline bowler filter]
         │
         ▼ (data/outputs/ & D:\rrhackthon\)
[CSV Exports: 10 CSV deliverables written to outputs/ and root]
         │
         ▼ (dashboard/app.py & src/reporting/report_generator.py)
[Presentation Layer: Streamlit 4-section UI & ReportLab 3-page PDF dossier]
```

---

## 3. Detailed Forensic Findings by Component

### Finding A: Batting Crisis Model is a Batting-Order / Tailender Proxy
- **Source File:** `src/pressure_engine/pressure_model.py`, Lines 40–86.
- **Severity:** **CRITICAL (Architectural Flaw)**.
- **Mechanism:**
  Batting pressure score is computed as:
  $$\text{Score} = (c_{\text{wkt}} + c_{\text{cluster}} + c_{\text{novelty}} + c_{\text{stagnation}}) \times \text{Phase Multiplier}$$
  Where:
  - $c_{\text{wkt}} = \min(3.5, \text{wickets\_fallen\_before} \times 0.45)$
  - $c_{\text{cluster}} = 2.0$ if 2+ wickets in last 12 legal balls, $0.75$ if 1 wicket, else $0.0$
  - $c_{\text{novelty}} = 1.5 \times (1 - \text{balls\_faced} / 5)$ for $\text{balls\_faced} < 5$, else $0.0$
  - $c_{\text{stagnation}} = \min(1.5, \text{consec\_dots} \times 0.3 + (\text{dots}_{12}/12) \times 0.6)$
  - $\text{Phase Multiplier} = 1.25$ (Death), $1.0$ (Middle), $0.95$ (Powerplay)
  - Deliveries with $\text{Score} \ge 5.5$ are labeled High/Extreme Pressure.

- **Forensic Verification & Empirical Evidence:**
  Evaluating all 193,988 deliveries in `ball_by_ball_with_pressure.parquet`:
  
  | Batting Position Group | Total Deliveries Faced | Crisis Deliveries ($\ge 5.5$) | Crisis % of Group | Share of All Dataset Crisis Deliveries |
  |---|:---:|:---:|:---:|:---:|
  | **Positions 1–3 (Top Order)** | 96,514 | 276 | **0.29%** | **1.79%** |
  | **Positions 4–5 (Middle Order)** | 52,148 | 1,029 | **1.97%** | **6.66%** |
  | **Positions 6–7 (Lower-Middle)** | 30,184 | 4,791 | **15.87%** | **30.99%** |
  | **Positions 8–11 (Tailenders)** | 15,139 | 9,365 | **61.86%** | **60.57%** |

- **Exact Breakdown by Position:**
  - Position 1: 32,971 balls, 86 crisis balls (0.26%)
  - Position 2: 33,515 balls, 80 crisis balls (0.24%)
  - Position 3: 30,028 balls, 110 crisis balls (0.37%)
  - Position 4: 28,863 balls, 258 crisis balls (0.89%)
  - Position 5: 23,285 balls, 771 crisis balls (3.31%)
  - Position 6: 17,588 balls, 1,789 crisis balls (10.17%)
  - Position 7: 12,596 balls, 3,002 crisis balls (23.83%)
  - Position 8: 7,293 balls, 3,353 crisis balls (45.98%)
  - Position 9: 4,285 balls, 2,970 crisis balls (69.31%)
  - Position 10: 2,487 balls, 2,057 crisis balls (82.71%)
  - Position 11: 1,074 balls, 985 crisis balls (91.71%)

- **Domain Impact:**
  A top-order batter (e.g. Virat Kohli or Jos Buttler) who faces 50 balls chasing 190 in a critical knockout game receives almost ZERO crisis balls unless their team is 5 or 6 down.
  Conversely, a tailender (e.g. Gudakesh Motie or Akeal Hosein) walking in at 65/7 in a hopeless blowout receives 80% to 90% crisis balls.
  **Conclusion:** The metric does not measure match pressure; it measures *collapse exposure*. The system penalized top-order batters for batting at the top of the order and rewarded tailenders for batting at the end of a collapse.

---

### Finding B: Score and Match-State Reconstruction Inherent Error
- **Source Files:** `data/ball_by_ball_ipl_t20i.csv`, `src/preprocessing/cleaner.py`.
- **Severity:** **MAJOR (Data Engineering Constraint)**.
- **Mechanism:**
  `extras1_runs` in the raw data contains categorical integer codes:
  `1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty`.
  The `runs` column records strictly runs off the batter's bat.
  For all 7,474 wide deliveries, `runs == 0` and `extras_2_runs == 0`.
  For all 2,661 legbyes deliveries, `runs == 0` and `extras_2_runs == 0`.
  For all 505 byes deliveries, `runs == 0` and `extras_2_runs == 0`.
  Therefore, multi-run extras (such as 4 byes, 4 leg-byes, or 5 wides) are not recorded in any numeric column.

- **Empirical Reconstruction Experiment:**
  We implemented an optimal heuristic reconstruction:
  $$\text{Extra Runs} = \begin{cases} 1 & \text{if wide} \\ 1 + \text{extras\_2\_runs} & \text{if Overstep or other} \\ 1 & \text{if byes or legbyes} \\ 0 & \text{otherwise} \end{cases}$$
  We aggregated innings totals for all 396 matches won by a run margin and compared $\text{Total}_{\text{Inn1}} - \text{Total}_{\text{Inn2}}$ against the official match victory margin (`matches['result']`):
  - **Exact Matches ($\text{Error} = 0$):** 126 out of 396 matches (**31.8%**).
  - **Error Distribution:** Mean = $+0.48$ runs, Standard Deviation = **$7.99$ runs**, 25th percentile = $-2.0$ runs, 75th percentile = $+1.0$ run, Max Error = $104$ runs (due to Duckworth-Lewis rain-reduced targets).
  - **Error in Uninterrupted Matches:** Standard deviation is approximately $\pm 2.8$ runs per match.

- **Domain Impact:**
  An uncertainty of $\pm 3$ runs in an over alters the Required Run Rate by $3.0$ runs per over. While insufficient for penny-perfect ball-by-ball scoreboards, this margin of error is **sufficiently accurate ($\pm 1.5$ runs per innings on average) to compute an Approximate Required Run Rate and Chase Pressure Index**, which is vastly superior to ignoring chase context entirely.

---

### Finding C: Bowling Defensive Pressure Model Starves the Normal Baseline
- **Source File:** `src/pressure_engine/pressure_model.py`, Lines 105–165.
- **Severity:** **CRITICAL (Statistical Modeling Flaw)**.
- **Mechanism:**
  Bowling defensive pressure is computed as:
  $$\text{Score} = c_{\text{resource}} + c_{\text{phase}} + c_{\text{momentum}} + c_{\text{rotation}}$$
  Where:
  - $c_{\text{resource}} = 3.0$ if batting team has 8–10 wickets in hand; $2.0$ if 6–7 wkts; $1.0$ if 4–5 wkts.
  - $c_{\text{phase}} = 3.0$ (Death), $2.0$ (Powerplay), $1.0$ (Middle).
  - $c_{\text{momentum}} = 2.5$ if 3+ boundaries in last 12 balls; $1.6$ if 2 boundaries; $0.8$ if 1 boundary.
  - $c_{\text{rotation}} = 1.5 \times (1 - \text{dots}_{12}/12)$.
  - Deliveries with $\text{Score} \ge 6.5$ are labeled High/Extreme Pressure; scores $< 4.5$ are Normal Baseline.

- **Forensic Verification:**
  - **High + Extreme Defensive Pressure:** 101,935 deliveries (**52.55%** of all deliveries).
  - **Moderate Pressure:** 71,592 deliveries (**36.91%** of all deliveries).
  - **Normal Baseline (None + Low):** 20,461 deliveries (**10.55%** of all deliveries).
  
  Because over 89.4% of deliveries are labeled Moderate, High, or Extreme, frontline bowlers who bowl 2 overs in the Powerplay (phase score 2.0 + wickets in hand 3.0 = 5.0) and 2 overs at the Death (phase score 3.0 + wickets in hand = 4.0–6.0) have **almost zero deliveries in the Normal baseline**:
  - Trent Boult: 879 crisis balls vs **64 normal balls** (out of 943 legal balls).
  - Mark Adair: 483 crisis balls vs **41 normal balls**.
  - Craig Young: 289 crisis balls vs **36 normal balls**.
  - Mark Wood: 156 crisis balls vs **31 normal balls**.
  - Deepak Chahar: 510 crisis balls vs **46 normal balls**.

- **Statistical Impact:**
  Because the normal baseline has only 30–60 balls per bowler, the baseline metric (`norm_dot_pct`) has extreme variance. A bowler conceding 4 boundaries in 35 normal balls has an artificially low `norm_dot_pct`, which inflates their `dot_maintenance` ratio ($M = \text{crisis\_dot\_pct} / \text{norm\_dot\_pct}$) to the maximum cap of 1.50x.

---

### Finding D: Empirical Bayes Implementation Audit
- **Source File:** `src/ranking_engine/pressure_rankings.py`, Lines 56–70.
- **Severity:** **MAJOR (Methodological Misrepresentation)**.
- **Code Inspection:**
  ```python
  def empirical_bayes_normal_shrink(observed_vals: pd.Series, sample_sizes: pd.Series,
                                    prior_k: float = 30.0) -> pd.Series:
      pop_mean = observed_vals.mean()
      pop_var = max(0.1, observed_vals.var())
      k = max(10.0, min(60.0, prior_k))
      weights = sample_sizes / (sample_sizes + k)
      return weights * observed_vals + (1.0 - weights) * pop_mean
  ```
- **Forensic Discrepancy:**
  1. In `rank_batters_comprehensive()`, line 248 passes `prior_k = 25.0`.
  2. The function calculates `pop_var = max(0.1, observed_vals.var())` on line 65, but `pop_var` is **never used in any calculation**.
  3. In rigorous Empirical Bayes theory (Efron & Morris 1975, Gelman et al. 2013), the shrinkage parameter $K$ is the ratio of within-player sampling variance to between-player variance:
     $$K = \frac{\sigma^2}{\tau^2}$$
     Where $\tau^2 = \max(0, s^2_{\text{observed}} - \bar{\sigma}^2)$.
  4. Here, $K$ is fixed at $25.0$ regardless of the empirical dispersion of the dataset.
  5. The method is therefore a **heuristic sample-weighted average**, not a fully estimated Empirical Bayes shrinkage model.

---

### Finding E: Performance Maintenance Metric is Completely Unshrunk
- **Source File:** `src/ranking_engine/pressure_rankings.py`, Lines 242–245 and Lines 457–460.
- **Severity:** **MAJOR (Statistical Flaw)**.
- **Code Inspection:**
  ```python
  norm_sr_safe = np.maximum(80.0, stats_df['norm_sr'].values)
  raw_maint = stats_df['crisis_sr'].values / norm_sr_safe
  stats_df['sr_maintenance'] = np.clip(raw_maint, 0.5, 1.5).round(3)
  ```
- **Forensic Discrepancy:**
  - $M$ is computed as the raw ratio of sample means: $\text{Crisis SR} / \text{Normal SR}$.
  - While `crisis_sr` is shrunk via `shrunk_crisis_sr` for Component 2 ($A$), the ratio $M$ used in Component 1 uses the **unshrunk observed crisis strike rate**.
  - For small sample sizes (e.g. 40–50 crisis balls), the raw strike rate has a sampling standard deviation of $\pm 25\text{--}35$ points.
  - Because $M$ carries **35% of the total PRI score**, 35% of each player's ranking is governed by an unshrunk, volatile ratio of two noisy estimates.

---

### Finding F: Dual Leaderboard Exclusion Mechanism is a Rule-Based Filter
- **Source File:** `src/ranking_engine/pressure_rankings.py`, Lines 318–333 and Lines 523–531.
- **Severity:** **MODERATE (Governance & Methodological Limitation)**.
- **Mechanism:**
  - In response to earlier anomalies (Motie #3 batter, Hosein #6 batter, Tector #3 bowler), the project implemented:
    - Batting primary mask: `modal_batting_position <= 7` or `is_regular_top7 == True`.
    - Bowling primary mask: `crisis_balls >= 120` and `primary_role != 'Top-Order Batter'`.
  - While this post-hoc role filter successfully sanitized the Primary Top 10 from displaying specialist spin bowlers in batting and top-order batters in frontline bowling, it is an **administrative post-processing patch** rather than a principled model correction.
  - The underlying pressure model still produces inflated raw PRI values for Motie (74.59) and Tector (86.00); the code simply routes them to secondary CSV files (`LOWER_ORDER_PRESSURE_IMPACT.csv` and `EMERGING_AND_PART_TIME_BOWLERS.csv`).

---

### Finding G: File Duplication, Stale Outputs & Codebase Hygiene
- **Source Files:** Root directory vs `data/outputs/`.
- **Severity:** **MINOR (Hygiene & Auditability)**.
- **Discrepancies Identified:**
  1. **Redundant Duplicate CSVs:** Every generated CSV file is saved twice (once in `data/outputs/` and once in project root `D:\rrhackthon\`), e.g., `FINAL_TOP_10_BATTERS.csv`, `top_10_batters.csv`, `ALL_BATTER_RANKINGS.csv`, `all_batter_rankings.csv`.
  2. **Backup Folder Disparity:** `data/outputs_backup_v2/` contains 29 files from an earlier computation where Motie and Hosein were ranked #3 and #6 in the primary batting list.
  3. **Test Count Discrepancy:** Previous markdown reports refer to 17 unit tests, whereas the active test suite contains 19 tests (all passing).

---

## 4. Comprehensive Forensic Audit Matrix

| Component | Code Claim | Actual Implementation | Statistical Validity | Cricket Validity | Severity |
|---|---|---|:---:|:---:|:---:|
| **Batting Pressure** | Measures crisis pressure across all innings | Wicket count depletion + collapse window | Flawed (biased towards tailenders) | Flawed (ignores chase RRR & match state) | **CRITICAL** |
| **Innings Dynamics** | Accounts for chase pressure | Identical formula for Innings 1 and 2 | Invalid (no chase context) | Invalid (chasing is fundamentally different) | **CRITICAL** |
| **Bowling Pressure** | Measures defensive pressure | Phase weights + wickets in hand + boundaries | Skewed (89.5% balls are pressure) | Flawed (starves normal baseline sample) | **CRITICAL** |
| **Score Tracking** | Reconstructs match state | Quarantined due to unconfirmed extras | Conservative (avoids false precision) | Sound caution, but forfeits RRR chase modeling | **MAJOR** |
| **EB Shrinkage** | Empirical Bayes conjugate shrinkage | Heuristic weighted average ($K=25.0$ fixed) | Incomplete Empirical Bayes | Acceptable heuristic, but mislabeled | **MAJOR** |
| **Maintenance Ratio** | Compares pressure to normal baseline | Unshrunk ratio of two noisy sample means | High variance on small samples | Sound concept, but noisy execution | **MAJOR** |
| **Consistency Metric** | Match-level exposure consistency | $\exp(-\text{CV}) \cdot \sqrt{m/(m+3)}$ | Strictly positive, continuous in $(0, 1]$ | Sound, rewards multi-match breadth | **SOUND** |
| **Role Separation** | Separates frontline from lower-order | Hard threshold filters (Pos 1–7, 120 balls) | Post-hoc heuristic filtering | Practical fix, but masks root pressure flaw | **MODERATE** |
| **Canonical Names** | Standardizes player display names | Exact mapping dictionary in `role_classifier.py` | Deterministic and verified | Excellent domain accuracy | **SOUND** |
| **Reproducibility** | Automated, test-backed pipeline | Fully reproducible via `compute_rankings.py` | 100% reproducible | High software engineering standard | **SOUND** |

---

## 5. Audit Conclusions & Directives for Research

1. **Do not merely patch the PRI weights:** Changing weights (e.g. 40/30/20/10) cannot resolve the fundamental problem that 60.57% of batting crisis deliveries belong to tailenders and that chase pressure is completely absent.
2. **A true match-state pressure model is mandatory:** Pressure must be derived from **Leverage Index (LI)** or **Win Probability Added (WPA)**, where high leverage is determined by game tension (balls remaining, runs required, wickets in hand), NOT merely batting order.
3. **Normal baseline must be statistically meaningful:** Both batting and bowling baselines must have sufficient sample sizes across all phases.
4. **Bayesian shrinkage must apply to the differential:** Rather than shrinking raw strike rate in isolation, statistical shrinkage must apply directly to the **pressure-minus-normal performance difference** ($\Delta_i = \theta_{i,\text{pressure}} - \theta_{i,\text{normal}}$).
