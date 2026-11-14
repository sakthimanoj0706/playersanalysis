# V3 Universal Ranking Sample Eligibility & Threshold Sensitivity Audit

**Audit Identifier:** `V3-RANKING-INTEGRITY-001 / PRIORITY 5`  
**Document Path:** `data/reports/v3/RANKING_ELIGIBILITY_AUDIT.md`  
**Associated Artifact:** `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`  
**Execution Date:** 14 November 2026  
**Status:** **AUDITED & VALIDATED (PROVISIONAL ELIGIBILITY CONFIRMED)**

---

## 1. Executive Summary & Objective

In legacy implementations, sample threshold cutoffs (e.g. 40 crisis balls for batters, 120 crisis balls for bowlers) were hard-coded heuristics without empirical sensitivity validation.

To establish scientific defensibility, this audit evaluates prespecified multi-dimensional threshold grids (108 candidate combinations for batting and 108 candidate combinations for bowling) against:
1. **Sample Exposure Depth:** Distinct match cluster counts and legal delivery exposure.
2. **Uncertainty Width:** Median and maximum bootstrap 95% confidence interval width.
3. **Ordering Stability:** Top-10 membership stability and rank preservation.
4. **Independent Pool Sufficiency:** Ensuring leaderboards reflect competitive depth rather than arbitrary quota fulfillment.

---

## 2. Prespecified Threshold Grid Architecture

### 2.1 Batting Candidate Grid (108 Configurations)
- **High-Pressure Balls Faced:** 40, 60, 80, 100
- **High-Pressure Distinct Matches:** 5, 8, 10
- **Normal Baseline Balls Faced:** 30, 50, 75
- **Total Deliveries Faced:** 120, 200, 300

### 2.2 Bowling Candidate Grid (108 Configurations)
- **High-Pressure Legal Balls Bowled:** 60, 90, 120, 150
- **High-Pressure Distinct Matches:** 5, 8, 10
- **Normal Baseline Legal Balls:** 30, 50, 75
- **Total Legal Deliveries Bowled:** 120, 200, 300

---

## 3. Key Sensitivity Findings

### 3.1 Batting Sensitivity Behavior
| Configuration ($\text{Crisis B} / \text{Matches} / \text{Norm B} / \text{Total B}$) | Eligible Batters | Top-10 Overlap with Baseline | Median 95% CI Width | Max CI Width | Unestimated CIs |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **40 / 5 / 30 / 120 (Current Baseline)** | **39** | **10 / 10 (100%)** | **83.84** | **123.64** | **0** |
| 60 / 5 / 30 / 120 | 25 | 7 / 10 (70%) | 78.42 | 114.20 | 0 |
| 60 / 8 / 50 / 200 | 22 | 6 / 10 (60%) | 76.50 | 112.10 | 0 |
| 80 / 8 / 50 / 200 | 15 | 4 / 10 (40%) | 72.10 | 108.50 | 0 |
| 100 / 10 / 75 / 300 (Ultra-Conservative) | 8 | 3 / 10 (30%) | 65.40 | 98.20 | 0 |

**Observations:**
- At the baseline cutoff (40 balls / 5 matches / 30 norm / 120 total), 39 specialist and primary all-rounder batters qualify, providing sufficient candidate depth.
- Increasing crisis ball minimums to $\ge 80$ or matches $\ge 10$ severely constrains the pool ($<15$ candidates), excluding established finishers like Abdul Samad, Jaker Ali Anik, and David Miller who have high impact across concentrated match situations.
- Median uncertainty width decreases from 83.84 to 65.40 as thresholds tighten, demonstrating that larger crisis samples yield tighter intervals, but at the cost of excluding critical specialist finishers.

### 3.2 Bowling Sensitivity Behavior
| Configuration ($\text{Crisis B} / \text{Matches} / \text{Norm B} / \text{Total B}$) | Eligible Bowlers | Top-10 Overlap with Baseline | Median 95% CI Width | Max CI Width | Unestimated CIs |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 60 / 5 / 30 / 120 (Relaxed) | 162 | 9 / 10 (90%) | 10.29 | 24.62 | 0 |
| 90 / 5 / 30 / 120 (Intermediate) | 145 | 9 / 10 (90%) | 9.85 | 22.10 | 0 |
| **120 / 5 / 30 / 120 (Current Frontline)** | **130** | **10 / 10 (100%)** | **8.86** | **19.82** | **0** |
| 150 / 8 / 50 / 200 (Conservative) | 98 | 8 / 10 (80%) | 8.12 | 18.40 | 0 |
| 150 / 10 / 75 / 300 (Ultra-Conservative) | 72 | 7 / 10 (70%) | 7.64 | 16.90 | 0 |

**Observations:**
- Frontline bowling sample depth is substantial: 130 bowlers satisfy the baseline threshold ($\ge 120$ crisis legal balls, $\ge 5$ matches, $\ge 30$ normal balls, $\ge 120$ total legal balls).
- The bowling confidence interval widths are remarkably tight (median 8.86 percentage points), indicating robust estimation of defensive dot ball rates across match clusters.

---

## 4. Threshold Governance Decision

1. **Retain Provisional Baseline Thresholds:**
   - **Batters:** Crisis balls $\ge 40$, Total balls $\ge 120$, Crisis matches $\ge 5$, Normal balls $\ge 30$.
   - **Bowlers:** Crisis balls $\ge 120$, Total legal balls $\ge 120$, Crisis matches $\ge 5$, Normal balls $\ge 30$.
2. **Scientific Justification:**
   - Yields adequate match-cluster exposure ($n \ge 5$ distinct match clusters for 100% of ranked players).
   - Zero unestimated confidence intervals (`ESTIMATED_MATCH_CLUSTER_BOOTSTRAP` for 100% of top candidates).
   - Retains sufficient candidate depth (39 batters, 130 bowlers).
   - Prevents artificial compression of specialist roles.
3. **Governance Label:**
   - The authoritative rankings are designated `PROVISIONAL_ELIGIBILITY_CONFIRMED`.
   - Any future threshold shift must reference the matrix in `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`.
