# EGM Goldfish Independent Review Findings — SupeRR Intelligence V3

**Audit Identifier:** `EGM-GOLDFISH-FINDINGS-001`  
**Repository:** `d:\rrhackthon` (Branch: `fix/v3-pre-submission-consistency-001`, Commit: `3b18f48`)  
**Review Protocol:** Six fresh, isolated `research` subagents launched in parallel with **zero prior context from the Elephant builder**, provided only with the official hackathon problem statement, source code, data files, and outputs.  
**Audit Date:** 15 November 2026

---

## 1. Panel Roster & Independent Verdicts

| Reviewer # | Role | Subagent Conversation Link | Independent Verdict | Core Conclusion |
| :---: | :--- | :--- | :---: | :--- |
| **#1** | **Cricket Analytics Expert** *(Does the methodology measure pressure performance?)* | [Goldfish Cricket Analytics Expert](conversation://5ccddf4a-3007-4f93-a65f-395a6b11af67) | **FAIL / PARTIAL** | Batting crisis (`> 5.50`) is a lower-order entry filter (`0.24%–0.37%` for orders 1–3); bowling normal (`<= 4.50`) is `0.65%` in Powerplay and `4.96%` in Death, causing `MIN_NORMAL_BALLS=100` to disqualify 145 frontline bowlers (almost all pacers) and penalize Jasprit Bumrah (#27) via Simpson's Paradox. |
| **#2** | **Statistical Reviewer** *(Are thresholds, sample sizes, and uncertainty defensible?)* | [Goldfish Statistical Reviewer](conversation://8e5356e4-4da2-4f58-99eb-a32b2f503aad) | **FAIL** | Top-10 batter 95% CIs have a median width of `100.88` SR points (`65.62`–`128.16`), overlapping across 38 of 39 batters; batter pool collapses from `39` (40b) $\to$ `21` (60b, Jaccard `0.3333`) $\to$ `11` (80b, Jaccard `0.0526`, 9/10 gone) $\to$ `0` (150b); `47.0%` of crisis batter-matches are `1–2` balls; `K=25` under-shrinks vs empirical $K \ge 56.3–670.2$. |
| **#3** | **Ranking Reviewer** *(Are the Top 10 results mathematically justified?)* | [Goldfish Ranking Reviewer](conversation://7c203044-5838-47a8-b96e-b5f56fb4a66a) | **FAIL** | 8 of Top 10 bowlers have `raw_dot_maintenance < 1.0` (worse under pressure than normal); 3 of Top 10 (Arshdeep #4, Taskin #6, Avesh #8) degrade on BOTH dot % and wicket rate; min-max scaling on 39 players violates IIA (removing #39 Suyash Sharma jumps #10 Motie to #6 and flips #4/#5); `norm_sample` is unscaled (`9.81–10.00` for all 39 bowlers); sensitivity script fails to re-normalize scores. |
| **#4** | **Data Auditor** *(Are statistics and player identities correct?)* | [Goldfish Data Auditor](conversation://84ca3e3c-93b1-41fe-9c81-ff19174330df) | **PARTIAL / FAIL** | Identity deduplication is clean (`0` duplicates), and `extras1_runs` quarantine is justified, **but `V3RoleClassifier` has severe bugs**: 8 of Top 10 bowlers (including #11-order Arshdeep Singh and #9-order Ravi Bishnoi) are misclassified as `BOWL_PRIMARY_AR`; 32 bowlers (`bf < 60, m_order <= 7`, e.g. Fabian Allen 179 bowled / 48 faced) are misclassified as `BAT_SPECIALIST` and locked out of bowling; `generate_v3_roles.py` includes Super Overs and bench rows; `innings_context.py` skips 44 wickets and 126 boundaries on wides/no-balls. |
| **#5** | **Application Auditor** *(Do backend and frontend show the same results?)* | [Goldfish Application Auditor](conversation://c6880152-ef57-436a-851d-d8a89925ea57) | **PARTIAL / FAIL** | Fails Deliverable 3f (**11 of the 20 selected players have zero selection rationale** in the methodology report or dashboard); leaves **11 stale V2 files** in root and `data/outputs/` showing Mark Adair #1 bowler and Gudakesh Motie #3 batter; `ALL_BATTER_RANKINGS.csv` is unsorted (`striker_id` order); `dashboard/app.py` leaks 22 bowlers into `u_tab3` batter plot via `sample_eligible` and omits Bowler CIs in `u_tab6`. |
| **#6** | **Adversarial Reviewer** *(Try to disprove the methodology and ranking conclusions)* | [Goldfish Adversarial Reviewer](conversation://68ae5f03-0c6a-4b88-b995-8735515f429b) | **REJECT (DISPROVEN)** | Proved mathematically that Powerplay balls with 0–2 wickets down have `0.00%` probability of being "normal" (`3.0 + 2.0 = 5.0 > 4.50`), causing `MIN_NORMAL_BALLS=100` to purge **120 of 132 (90.91%) frontline fast bowlers**; proved that Iftikhar Ahmed (#9, `127.50` SR) never faced `>6` crisis balls in any match (`1(1), 1(1), 3(3)...`), gaming unweighted match-CV (`20/20` pts) while boundary-hitting finishers (Dhoni `7.34/20`, Rinku `9.13/20`, Jitesh `4.12/20`) are punished. |

---

## 2. Detailed Synthesis of Goldfish Reviewer Findings (With Exact Evidence)

### 2.1 Reviewer #1 — Cricket Analytics Expert
- **Finding CA-1 (`GROUP A`): Batting Crisis (`> 5.50`) Is a Lower-Order Entry Filter.**
  - *Evidence (`src/pressure_engine/v3_pressure_model.py:149-183`, `ball_by_ball_with_pressure.parquet`):* Crisis exposure by `batting_order`: Order 1 = `0.26%` (`84 / 31,795`), Order 2 = `0.24%` (`76 / 32,260`), Order 3 = `0.37%` (`106 / 28,944`), Order 4 = `0.87%` (`243 / 27,808`), Order 5 = `3.21%` (`719 / 22,365`), Order 6 = `10.07%`, Order 7 = `23.87%`, Orders 8–11 = `45.82%–91.61%`. Excludes Nicholas Pooran (`39b`, `210.26` SR), Tristan Stubbs (`39b`), Hardik Pandya (`38b`), Glenn Phillips (`34b`, `238.24` SR), Jos Buttler (`15b`), Heinrich Klaasen (`15b`), Suryakumar Yadav (`13b`, `238.46` SR), and Virat Kohli (`9b`).
- **Finding CA-2 (`GROUP A`): Bowling Pressure Calibration + `MIN_NORMAL_BALLS = 100` Creates Spin Bias & Phase Confounding (The Jasprit Bumrah Paradox).**
  - *Evidence (`src/pressure_engine/v3_pressure_model.py:221-254`, `ALL_BOWLER_METRICS.csv`):* Spinners have `16.20%` normal balls (`11,634 / 71,830`), whereas Pacers have only `7.17%` normal balls (`8,182 / 114,121`). `MIN_NORMAL_BALLS = 100` disqualifies 145 frontline bowlers (`>= 120` crisis balls). Jasprit Bumrah (`2933`) has `1,094` crisis balls (`42.32%` dot rate—higher than 9 of the Top 10!) and `121` normal balls (bowled in low-leverage middle overs against collapsed batting orders, yielding `59.50%` dot rate), resulting in `dot_maintenance = 0.711x` and **Rank #27 out of 39**!
- **Finding CA-3 (`GROUP B`): Omission of Verified `batter_runs` / Boundaries Conceded in Bowling & Dismissal Survival in Batting.**
  - *Evidence (`scripts/compute_v3_rankings.py:149-164, 438-458`):* Even with `extras1_runs` quarantined, `batter_runs`, `is_four_validated`, `is_six_validated`, and `extras_category.isin({'wide', 'Overstep'})` are 100% verified on every ball. Ignoring runs/boundaries off the bat treats a single and a six as identical non-dot balls.

### 2.2 Reviewer #2 — Statistical Reviewer
- **Finding STAT-1 (`GROUP A`): Extreme Small-Sample Uncertainty (`100.88` SR Median CI Width in Top 10 Batters) & Complete Pool Collapse at `>= 80–150` Balls.**
  - *Evidence (`TOP_10_BATTERS.csv`, `RANKING_THRESHOLD_SENSITIVITY.csv`):* Top-10 batter 95% CIs span `65.62` to `128.16` SR points; for 7 of the Top 10 batters, their 95% CI contains the point estimates of 35–36 of the 39 eligible batters. Moving from `40` to `60` balls cuts the pool from `39` to `21` (`5/10` Top-10 overlap, Jaccard `0.3333`); at `80` balls only `11` remain (`1/10` overlap, Jaccard `0.0526`); at `100` balls only `8` remain; at `150+` balls `0` remain.
- **Finding STAT-2 (`GROUP A`): 47.0% of Crisis Batter-Matches Are 1 or 2 Balls, Corrupting Unweighted Match-Level `CV`.**
  - *Evidence (`scripts/compute_v3_rankings.py:329-338`, `ball_by_ball_with_pressure.parquet`):* Out of `4,385` crisis batter-match appearances, `1,158` (`26.4%`) are `1` ball and `2,060` (`47.0%`) are $\le 2$ balls (including 11 of Tilak Varma's 18 matches and 14 of Jitesh Sharma's 22 matches).
- **Finding STAT-3 (`GROUP A`): Under-Shrunk Batter Prior (`K = 25.0` vs Empirical $K \ge 56.3–670.2$) & Clipped Bowler Prior (`m_sum = 100.0` vs `397.56`).**
  - *Evidence (`src/reliability/v3_reliability.py:247-371`):* Batter within-delivery variance is $\sigma^2 = 32,208.54$, between-batter variance is $\hat{\tau}^2 = 48.06$ ($\text{Var}(Y_i) = 572.56$), implying $K = 670.2$ (or $56.3$ unadjusted) vs hardcoded `K = 25.0`. Bowler Beta-Binomial `m_sum = 397.56` hits `np.clip(..., 5.0, 100.0)` at `100.0`. Maintenance ratios (`35%` weight) bypass shrinkage completely.

### 2.3 Reviewer #3 — Ranking Reviewer
- **Finding RANK-1 (`GROUP A`): Bowler Construct Mismatch & Negative-Maintenance Top 10.**
  - *Evidence (`scripts/compute_v3_rankings.py:488-662`, `TOP_10_BOWLERS.csv`):* 8 of the Top 10 bowlers (and 37 of 39 eligible bowlers, `94.87%`) have `raw_dot_maintenance < 1.0`. Arshdeep Singh (#4), Taskin Ahmed (#6), and Avesh Khan (#8) perform worse under pressure on **both** dot % and wicket rate than in normal conditions.
- **Finding RANK-2 (`GROUP A`): Min-Max Normalization Violates IIA & Renders Bowler Sample Weight a Dead Constant.**
  - *Evidence (`scripts/compute_v3_rankings.py:372-383, 647-650`):* Removing #39 outlier Suyash Sharma (`dot_maintenance = 0.517`) jumps #10 Gudakesh Motie to #6 and flips #4 Arshdeep Singh and #5 Ravi Bishnoi. Adding 39-ball Nicholas Pooran flips #8 MS Dhoni and #9 Iftikhar Ahmed. Because `norm_sample` is not min-max scaled, 37 of 39 bowlers get `10.00 / 10.00` pts (`range = [9.81, 10.00]`).
- **Finding RANK-3 (`GROUP A`): Threshold Sensitivity Loop Fails to Re-Compute Shrinkage or Min-Max Normalization.**
  - *Evidence (`scripts/compute_v3_rankings.py:725-738, 803-816`):* `RANKING_THRESHOLD_SENSITIVITY.csv` slices pre-computed `provisional_fixed_weight_score` without re-normalizing on each candidate cohort `cand`.

### 2.4 Reviewer #4 — Data Auditor
- **Finding DATA-1 (`GROUP A`): Severe Role Misclassification in `V3RoleClassifier` (`src/classification/v3_role_classifier.py:170-220`).**
  - *Evidence (`player_roles.csv`, `TOP_10_BOWLERS.csv`, `TOP_10_BATTERS.csv`):*
    - **8 of the Top 10 Bowlers** (including #11-order Arshdeep Singh `top7_ratio = 0.0`, #9-order Ravi Bishnoi `top7_ratio = 0.0`, #10-order Taskin Ahmed, #9-order Ish Sodhi, #9-order Keshav Maharaj, #9-order Gudakesh Motie) and **29 of 75 `BOWL_PRIMARY_AR` players** are pure #9–#11 tailender bowlers misclassified as All-Rounders because `bb >= 100 and bf >= 80` uses unnormalized career balls faced (<1–2 balls/match).
    - **32 bowling-dominant players** (`m_order <= 7` and `bf < 60`, e.g., Fabian Allen `179` bowled / `48` faced; Rishi Dhawan `174` bowled / `52` faced; Andile Phehlukwayo `144` bowled / `41` faced; Logan van Beek `132` bowled / `32` faced) fall into the `else:` branch of `if top7_r >= 0.50 or m_order <= 7:` and are misclassified as **`BAT_SPECIALIST`**, locking them out of the bowling leaderboard!
    - **#1 Tilak Varma (`61` balls bowled in `138` matches)** and **#3 Daryl Mitchell (`80` balls bowled in `77` matches)** are misclassified as `BAT_PRIMARY_AR` because `bb >= 40` is unnormalized.
- **Finding DATA-2 (`GROUP A`): Super Over Contamination & Unfiltered Bench Matches in `scripts/generate_v3_roles.py` and `v3_role_classifier.py`.**
  - *Evidence (`scripts/generate_v3_roles.py:25-33`, `src/classification/v3_role_classifier.py:70-75`):* `generate_v3_roles.py` does not call `separate_cohorts()` (causing `player_roles.csv` and `TOP_10_BOWLERS.csv` to disagree on Arshdeep Singh's balls `3,209` vs `3,204` and wickets `194` vs `192`), and `v3_role_classifier.py` counts `8,339` `is_played == False` bench rows in `total_matches`.
- **Finding DATA-3 (`GROUP A`): Rolling Window (`last_12_legal_balls`) Skips 44 Wickets and 126 Boundaries on Illegal Deliveries.**
  - *Evidence (`src/context_engine/innings_context.py:121-131`):* `recent_legal = legal_indices[-12:]` only sums over `is_legal == True`, ignoring run-outs/stumpings on wides/no-balls (44 wickets) and boundaries off no-balls (126 boundaries).

### 2.5 Reviewer #5 — Application Auditor
- **Finding APP-1 (`GROUP A`): Deliverable 3f Failure (11 of 20 Selected Players Lack Individual Selection Rationale).**
  - *Evidence (`FINAL_SUPERR_METHODOLOGY_REPORT.md:60-97`, `src/reporting/report_generator.py:152-167`, `dashboard/app.py:281-330`):* Only #9 Iftikhar Ahmed has a dedicated rationale in the methodology report; 0 of the 10 bowlers have individual selection rationales in the methodology report.
- **Finding APP-2 (`GROUP A`): 11 Stale V2 Leaderboard Files & Unsorted `ALL_BATTER_RANKINGS.csv` / `ALL_BOWLER_RANKINGS.csv`.**
  - *Evidence:* Root `PRI_SENSITIVITY_ANALYSIS.csv`, `batting_pri_details.csv`, `bowling_pri_details.csv`, `*.parquet`, `RR_SQUAD_SCOUTING_REPORT.csv`, and `DASHBOARD_VALIDATION_REPORT.md` show old V2 rankings; `ALL_BATTER_RANKINGS.csv` and `ALL_BOWLER_RANKINGS.csv` are exported in `striker_id` / `bowler_id` order without a `rank` column.
- **Finding APP-3 (`GROUP B`): `dashboard/app.py` Role-Gating Leak in `u_tab3` (`sample_eligible`) & Missing Bowler CIs in `u_tab6`.**
  - *Evidence (`dashboard/app.py:338, 355, 421-437`):* `sample_eligible == True` plots 22 `BOWL_PRIMARY_AR` bowlers on the batter scatter chart and 7 `BAT_PRIMARY_AR` batters on the bowler scatter chart; `u_tab6` says `500 bootstrap iterations` instead of `2,000` and omits Bowler CIs.

### 2.6 Reviewer #6 — Adversarial Reviewer
- **Finding ADV-1 (`GROUP A`): Mathematical Theorem of Fast-Bowler Exclusion.**
  - *Evidence (`src/pressure_engine/v3_pressure_model.py:222-254`):* Proved that $\text{Score}_{\min}(\text{Powerplay}, \le 2\text{ wkts}) = 3.0 + 2.0 = 5.00 > 4.50$, so `0.00%` of early Powerplay balls can ever be "Normal", causing `MIN_NORMAL_BALLS = 100` to purge **120 of 132 (`90.91%`) frontline fast bowlers**.
- **Finding ADV-2 (`GROUP A`): Exact Match-Level Proof of Iftikhar Ahmed's (#9) Micro-Cameo Gaming.**
  - *Evidence (`ball_by_ball_with_pressure.parquet`):* Across all 11 crisis matches (`40` balls total), Iftikhar Ahmed never faced more than 6 crisis balls in any match (`2(1), 1(1), 1(1), 0(2), 3(3), 5(4), 7(5), 7(5), 12(6), 4(6), 9(6)`), earning `20.00 / 20.00` consistency points while boundary-hitting finishers (MS Dhoni `7.34/20`, Rinku Singh `9.13/20`, Jitesh Sharma `4.12/20`) are penalized for `6(1)=600 SR` cameos.
