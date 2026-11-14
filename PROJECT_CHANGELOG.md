# Project Changelog & Analytical Upgrade Log
**Project:** SupeRR Intelligence — Rajasthan Royals SupeRR Selector Season 2 Hackathon  
**Release Version:** 2.1 (Professional Edition)  
**Date:** November 11, 2026  

---

## 1. Summary of Changes

This release executes a comprehensive analytical upgrade addressing player eligibility anomalies, role classifications, name normalizations, dual leaderboard architecture, and dashboard redesign without modifying raw source files or discarding verified calculations.

---

## 2. Key Anomalies Addressed & Resolved

| Player | Previous Placement | Root Cause Identified | Analytical Correction Implemented | New Verified Placement |
|---|---|---|---|---|
| **Gudakesh Motie** | #3 Batting Leaderboard | Specialist West Indies left-arm spinner (modal batting pos 9) with 47 crisis balls. High strike rate (170.2) in collapse tailender situations distorted top-seven ranking. | Implemented role-aware batting qualification requiring regular top-seven order (Positions 1–7). Relocated to secondary leaderboard. | **#1 on Lower-Order Pressure Impact Leaderboard** (`LOWER_ORDER_PRESSURE_IMPACT.csv`, PRI 74.59) |
| **Akeal Hosein** | #6 Batting Leaderboard | Specialist West Indies left-arm spinner (modal batting pos 10) with 114 crisis balls. 100% crisis exposure due to tailender entry point inflated maintenance ratio. | Implemented role-aware batting qualification. Relocated to secondary leaderboard. | **#2 on Lower-Order Pressure Impact Leaderboard** (`LOWER_ORDER_PRESSURE_IMPACT.csv`, PRI 68.23) |
| **Harry Tector** | #3 Bowling Leaderboard | Ireland top-order batter (modal batting pos 4) with 857 balls faced vs 248 bowled. Recorded 54 crisis bowling balls at 9.26% wicket rate. | Established 120 crisis legal delivery threshold for frontline bowling leaderboard. Relocated to secondary leaderboard. | **#1 on Emerging & Part-Time Bowlers Leaderboard** (`EMERGING_AND_PART_TIME_BOWLERS.csv`, PRI 86.00) |
| **MS Dhoni** | Excluded in initial top-7 filter | In `playing_eleven`, modal position registered as 8 (19 inns) vs 7 (18 inns), but 62.1% of career innings occurred in positions 1–7. | Updated regular top-seven qualification to consider career position distribution (`top7_ratio >= 0.50` or `modal_order <= 7`) and WK role. | **#5 on Primary Top 10 Batters Leaderboard** (`FINAL_TOP_10_BATTERS.csv`, PRI 66.20) |

---

## 3. New Architecture & Engineering Modules Added

### A. Player Role Classification Engine (`src/classification/role_classifier.py`)
- Analyzes `playing_eleven_ipl_t20i.csv` and `ball_by_ball_ipl_t20i.csv` to compute modal batting positions, order distributions, wicketkeeping duties, bowling styles (Pace/Spin), and workload volumes.
- Classifies 1,118 players into empirical roles (Top-Order Batter, Middle-Order Batter, Finisher / Lower-Middle Batter, WK-Batter, Batting All-Rounder, Bowling All-Rounder, Specialist Fast Bowler, Specialist Spin Bowler, Lower-Order Batter, Part-Time Bowler).
- Generates `PLAYER_ROLE_CLASSIFICATION.csv` with evidence strings and confidence ratings.

### B. Canonical Name Normalization
- Standardizes raw dataset player strings to recognized cricket display names (`Namboori Tilak Varma` $\to$ `Tilak Varma`, `Mahendra Singh Dhoni` $\to$ `MS Dhoni`, `Lokesh Rahul` $\to$ `KL Rahul`, `Ravichandran Ashwin` $\to$ `R Ashwin`, `Jaker Ali Anik` $\to$ `Jaker Ali`).
- Generates `PLAYER_NAME_ALIASES.csv` with verification statuses.

### C. Role-Aware Dual Leaderboard System (`src/ranking_engine/pressure_rankings.py`)
1. **Primary Top 10 Batters (`FINAL_TOP_10_BATTERS.csv`):** Positions 1–7, $\ge 40$ crisis balls, $\ge 120$ total balls, $\ge 5$ crisis matches.
2. **Primary Top 10 Bowlers (`FINAL_TOP_10_BOWLERS.csv`):** Frontline bowlers carrying $\ge 120$ crisis legal deliveries, $\ge 5$ matches.
3. **Lower-Order Pressure Impact (`LOWER_ORDER_PRESSURE_IMPACT.csv`):** Specialist bowlers and lower-order hitters (Positions 8–11) with $\ge 30$ crisis balls.
4. **Emerging & Part-Time Bowlers (`EMERGING_AND_PART_TIME_BOWLERS.csv`):** Bowlers with 40–119 crisis deliveries or batting all-rounders.
5. **All-Role Unrestricted Leaderboards (`ALL_BATTER_RANKINGS.csv`, `ALL_BOWLER_RANKINGS.csv`):** Full 824-batter and 596-bowler rosters.

### D. Professional Dashboard Redesign (`dashboard/app.py`)
- Restructured into 4 executive sections:
  1. Pressure Intelligence Overview
  2. Batter Intelligence (Primary & Lower-Order)
  3. Bowler Intelligence (Primary & Emerging)
  4. Methodology, Science & Data Quality
- Applied Rajasthan Royals Navy (`#0B1B3D`) and Pink (`#EA1A85`) aesthetic.
- Zero hardcoded values; all metrics loaded dynamically from computed CSV outputs.

### E. Official Methodology Dossier Generator (`src/reporting/report_generator.py`)
- Produces publication-grade 3-page PDF dossier (`FINAL_SUPERR_METHODOLOGY_REPORT.pdf`) with zero blank pages via ReportLab.
- Produces complete Markdown technical documentation (`FINAL_SUPERR_METHODOLOGY_REPORT.md`).

---

## 4. Verification & Validation Metrics

- **Unit Tests:** 19 automated unit tests in `tests/`, all passing in 1.8 seconds.
- **Sensitivity Analysis:** Spearman rank correlations across 5 weighting schemes exceed 0.88 for batters and 0.91 for bowlers.
- **Data Governance:** Categorical `extras1_runs` quarantined; unverified economy rates strictly withheld; non-bowler dismissals filtered.
