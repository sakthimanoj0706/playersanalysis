# P1.1 — Pre-Submission Consistency & Ranking Reliability Patch Audit Report

**Patch Identifier:** `P1.1-PRE-SUBMISSION-CONSISTENCY-001`  
**Repository:** `https://github.com/sakthimanoj0706/playersanalysis.git`  
**Active Branch:** `fix/v3-pre-submission-consistency-001` (branched from `fix/v3-ranking-integrity-001` commit `e03abf1`, baseline `main` `537777c8436fd647a484a49cfbfa30b843c98a1c`)  
**Execution Date:** 15 November 2026  
**Final Governance Status:** **`P1.1 PATCH VERIFIED — PROVISIONAL MODEL`**

> **Mandatory Disclosure:**
> "Rankings are provisional. Batter ranks 5, 6, 9 and 10 are sensitive to scoring weights. The pressure classification remains heuristic and position-proxy based. The new score has not yet undergone independent out-of-time validation."

---

## 1. P0 — Authoritative Ranking Source & Synchronization

1. **Authoritative Source of Truth (`data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`):**
   - `data/outputs/v3/TOP_10_BATTERS.csv`
   - `data/outputs/v3/TOP_10_BOWLERS.csv`
2. **Synchronized Downstream Copies (14 Files Verified Byte-for-Byte via SHA-256 in `scripts/verify_v3_rankings.py`):**
   - Batter Top-10 copies: `FINAL_TOP_10_BATTERS.csv`, `data/outputs/FINAL_TOP_10_BATTERS.csv`, `data/outputs/top_10_batters.csv`, `data/outputs/top_10_batters_v2.csv`, `data/outputs/v3/top_10_batters.csv`
   - Bowler Top-10 copies: `FINAL_TOP_10_BOWLERS.csv`, `data/outputs/FINAL_TOP_10_BOWLERS.csv`, `data/outputs/top_10_bowlers.csv`, `data/outputs/top_10_bowlers_v2.csv`, `data/outputs/v3/top_10_bowlers.csv`
   - Full leaderboard & eligibility copies: `ALL_BATTER_RANKINGS.csv`, `data/outputs/ALL_BATTER_RANKINGS.csv`, `ALL_BOWLER_RANKINGS.csv`, `data/outputs/ALL_BOWLER_RANKINGS.csv`, `PLAYER_ELIGIBILITY_REPORT.csv`, `data/outputs/PLAYER_ELIGIBILITY_REPORT.csv`

---

## 2. P0 — README, Methodology Report, and Hazard Model Governance

1. **Wicket Hazard Model (`src/models/v3_wicket_hazard.py`, `data/reports/v3/WICKET_HAZARD_VALIDATION.md`):**
   - Status downgraded from `PRODUCTION_VALIDATED` to **`EXPERIMENTAL_NOT_USED_FOR_RANKING`**.
   - Actual held-out chronological diagnostics reported transparently:
     - **ROC-AUC:** `0.572`
     - **Log-Loss:** `0.692`
     - **Brier Score:** `0.246`
     - **Expected Wickets vs Actual Wickets:** `26,843` expected vs `2,931` actual (`9.16x` over-prediction caused by un-recalibrated `class_weight='balanced'` probabilities).
   - `class_weight='balanced'` was not blindly removed; the miscalibration is documented and the model is excluded from ranking calculations.
2. **Auction Purse Provenance (`data/reference/rr_2027_auction_assumptions.csv`):**
   - Carried purse (`₹2.65 Cr`), freed releases (`₹24.95 Cr`), base purse (`₹27.60 Cr`), and expanded purse (`₹32.60 Cr`) are explicitly labelled **`UNVERIFIED_USER_BRIEF_SCENARIO`** with traceable source path and checked date (`2026-11-15`).

---

## 3. P1 — Bowler Normal-Baseline Reliability (`MIN_NORMAL_BALLS = 100`)

- Enforced `MIN_NORMAL_BALLS_BOWLER = 100` (`DEFAULT_BOWL_THRESHOLDS['norm_balls'] = 100` in `scripts/compute_v3_rankings.py`).
- Every bowler row reports: `crisis_balls`, `norm_balls`, `norm_baseline_eligible`, `norm_baseline_status`, `raw_dot_maintenance`, `capped_dot_maintenance`, `is_maintenance_capped`, and `final_eligibility`.
- Out of 596 bowlers:
  - **549 bowlers** have `norm_balls < 100` and are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT` (including Mark Adair [82], Trent Boult [64], Mark Wood [62], Obed McCoy [46], and Craig Young [36]). Their `capped_dot_maintenance` and composite score are `NaN` (never imputed).
  - **47 bowlers** satisfy `norm_balls >= 100`, and **39 frontline bowlers** meet full eligibility (`crisis_balls >= 120`, `crisis_matches >= 5`, `norm_balls >= 100`, `total_legal_balls >= 120`, eligible role).

---

## 4. P1 — Extended Threshold Sensitivity (`40, 60, 80, 100, 150, 200, 250`)

- `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv` expanded to **270 combinations** covering crisis-ball cutoffs `40, 60, 80, 100, 150, 200, 250` across match minimums `5, 8, 10`.
- Reports `eligible_batter_count`, `eligible_bowler_count`, `available_top10_count` (never forcing 10 when `< 10` qualify), `top10_overlap_with_baseline`, `jaccard_similarity`, `mean_rank_shift`, `max_rank_shift`, `players_entering_top10`, and `players_leaving_top10`.

---

## 5. P1 — Ranking Transparency & Iftikhar Ahmed (#9) Component Breakdown

- Weight-sensitive batter ranks explicitly flagged (`RANKING_SENSITIVE_TO_WEIGHTS`): **#5 Jaker Ali Anik**, **#6 Abdul Samad**, **#9 Iftikhar Ahmed**, and **#10 Jitesh Sharma**.
- **Iftikhar Ahmed (`canonical_player_id=3056`, Rank #9):**
  - Crisis SR: `127.50` vs eligible cohort mean `140.20` (`-12.70`), flagged `CRISIS_SR_BELOW_COHORT_MEAN`.
  - Component breakdown (`component_breakdown_explanation`): `Maint(35%)=20.95 + Abs(35%)=14.71 + Cons(20%)=20.00 + Sample(10%)=6.72 = 62.38`. Elevated by #1 cohort match consistency (`0.5497 -> 20.00 pts`) and positive personal baseline maintenance (`1.054x` over `120.96` normal SR `-> 20.95 pts`) despite low absolute crisis SR contribution (`14.71 pts`).
- In accordance with governance rules, no player was manually removed or promoted.
