# SupeRR Intelligence V3 — Pre-Submission Consistency & Release Readiness Report (P1.1)

**Project:** SupeRR Intelligence V3  
**Organization:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Horizon:** IPL 2027 Mini-Auction (Goa)  
**Branch:** `fix/v3-pre-submission-consistency-001`  
**Execution Date:** 15 November 2026  
**System Status:** **`P1.1 PATCH VERIFIED — PROVISIONAL MODEL`**

> **Mandatory Disclosure:**
> "Rankings are provisional. Batter ranks 5, 6, 9 and 10 are sensitive to scoring weights. The pressure classification remains heuristic and position-proxy based. The new score has not yet undergone independent out-of-time validation."

---

## 1. Executive Summary & Verification Sign-Off

The **SupeRR Intelligence V3** platform has completed the **P1.1 Pre-Submission Consistency & Ranking Reliability Patch** (`fix/v3-pre-submission-consistency-001`), resolving stale documentation, synchronizing all Top-10 ranking files to a single canonical source of truth, enforcing `MIN_NORMAL_BALLS = 100` for bowlers, extending threshold sensitivity across `40, 60, 80, 100, 150, 200, 250` crisis balls, exposing component-level breakdowns for weight-sensitive ranks (including Iftikhar Ahmed #9), and reclassifying experimental models (`EXPERIMENTAL_NOT_USED_FOR_RANKING`).

---

## 2. Master Verification Checklist & Compliance Matrix

| Priority / Gate | Description | Key Artifact | Status | Audit Verification Evidence |
| :--- | :--- | :--- | :---: | :--- |
| **P0: Authoritative Ranking Source** | Canonical `TOP_10_BATTERS.csv` & `TOP_10_BOWLERS.csv` synchronized byte-for-byte across all 14 copies | `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json` | **PASSED** | `scripts/verify_v3_rankings.py` Gate 6 verifies SHA-256 parity across all root and `data/outputs/` copies. |
| **P0: Hazard Model Governance** | Reclassify hazard, joint, and LightGBM models as `EXPERIMENTAL_NOT_USED_FOR_RANKING`; report actual wicket mismatch | `data/reports/v3/WICKET_HAZARD_VALIDATION.md` | **PASSED** | AUC: `0.572`, Log-Loss: `0.692`, Expected Wickets: `26,843` vs Actual: `2,931` (`9.16x` inflation from `class_weight='balanced'`). |
| **P1: Bowler Normal Baseline (`>=100`)** | Enforce `MIN_NORMAL_BALLS = 100` for bowlers; flag `<100` as `BOWLER_NORMAL_BASELINE_INSUFFICIENT` | `data/outputs/v3/ALL_BOWLER_METRICS.csv`<br>`TOP_10_BOWLERS.csv` | **PASSED** | 549 bowlers with `<100` normal balls flagged and excluded from composite score; 39 eligible frontline bowlers ranked. |
| **P1: Extended Threshold Sensitivity** | Crisis-ball sweep `40, 60, 80, 100, 150, 200, 250` $\times$ `5, 8, 10` matches | `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv` | **PASSED** | 270 grid combinations with unforced `available_top10_count`, Jaccard similarity, rank shifts, and entering/leaving players. |
| **P1: Ranking Transparency** | Flag weight-sensitive batter ranks (#5, #6, #9, #10) and expose #9 Iftikhar Ahmed component breakdown | `data/outputs/v3/TOP_10_BATTERS.csv` | **PASSED** | Iftikhar Ahmed (`3056`) flagged `CRISIS_SR_BELOW_COHORT_MEAN` (127.50 vs 140.20 cohort mean); components `20.95 + 14.71 + 20.00 + 6.72 = 62.38`. |
| **P1: Pressure Model Limitations** | Document position-proxy heuristic and missing chase leverage (`PROVISIONAL_POSITION_PROXY_HEURISTIC`) | `data/reports/v3/PRESSURE_MODEL_VALIDATION.md` | **PASSED** | Explicitly documented across README, methodology reports, PDF summaries, and dashboard. |
| **P1: RR Audited Entities & Purse Provenance** | Canonical ID crosswalk, Dhruv Jurel avg `36.79`, Adam Milne `1` match played, purse assumptions labelled | `data/reference/rr_2027_auction_assumptions.csv` | **PASSED** | Purse figures (`₹2.65 Cr`, `₹24.95 Cr`, `₹27.60 Cr`, `₹32.60 Cr`) labelled `UNVERIFIED_USER_BRIEF_SCENARIO` with checked date `2026-11-15`. |
| **P1: Automated Tests & Determinism** | Full pytest suite + 2-run SHA-256 determinism check | `tests/` (17 test files) | **PASSED** | **64 passed in 4.07s** (`0 failed`); two consecutive runs produce identical SHA-256 hashes. |

---

## 3. Authoritative Universal Top 10 Leaderboards (`data/outputs/v3/TOP_10_*.csv`)

### 3.1 Authoritative Top 10 Batters Under Pressure (`TOP_10_BATTERS.csv`)
| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls (Matches) | Crisis SR | Normal SR ($\ge 30$b) | Raw / Capped Maint. (Capped?) | Provisional Score (`PRI`) | 95% Match-Cluster CI | Sensitivity & Flags |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `7897` | **Tilak Varma** | `BAT_PRIMARY_AR` | 60 (18) | 196.67 | 144.47 | 1.361x / 1.361x (No) | **94.29** | [157.62, 251.16] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `796` | **Matthew Wade** | `BAT_SPECIALIST` | 50 (15) | 172.00 | 144.49 | 1.190x / 1.190x (No) | **77.35** | [105.70, 213.93] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `4106` | **Daryl Mitchell** | `BAT_PRIMARY_AR` | 44 (12) | 177.27 | 147.10 | 1.205x / 1.205x (No) | **72.55** | [117.22, 237.04] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `4391` | **Liam Livingstone** | `BAT_PRIMARY_AR` | 60 (14) | 175.00 | 161.29 | 1.085x / 1.085x (No) | **68.92** | [106.81, 221.52] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `4773` | **Jaker Ali Anik** | `BAT_SPECIALIST` | 63 (15) | 139.68 | 122.38 | 1.141x / 1.141x (No) | **65.13** | [100.00, 181.64] | `RANKING_SENSITIVE_TO_WEIGHTS`; `CRISIS_SR_BELOW_COHORT_MEAN` |
| **6** | `7446` | **Abdul Samad** | `BAT_SPECIALIST` | 69 (23) | 169.57 | 168.67 | 1.005x / 1.005x (No) | **64.51** | [128.57, 206.50] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **7** | `1077` | **David Miller** | `BAT_SPECIALIST` | 56 (17) | 166.07 | 156.15 | 1.064x / 1.064x (No) | **63.35** | [100.00, 218.65] | `ROBUST_ACROSS_WEIGHTS` |
| **8** | `8` | **MS Dhoni** | `BAT_SPECIALIST` | 133 (35) | 154.89 | 140.94 | 1.099x / 1.099x (No) | **62.51** | [119.66, 187.59] | `ROBUST_ACROSS_WEIGHTS` |
| **9** | `3056` | **Iftikhar Ahmed** | `BAT_PRIMARY_AR` | 40 (11) | 127.50 | 120.96 | 1.054x / 1.054x (No) | **62.38** | [92.72, 158.34] | `RANKING_SENSITIVE_TO_WEIGHTS`; `CRISIS_SR_BELOW_COHORT_MEAN` |
| **10** | `3916` | **Jitesh Sharma** | `BAT_SPECIALIST` | 51 (22) | 172.55 | 155.53 | 1.109x / 1.109x (No) | **62.01** | [108.69, 236.85] | `RANKING_SENSITIVE_TO_WEIGHTS` |

### 3.2 Authoritative Top 10 Bowlers Under Pressure (`TOP_10_BOWLERS.csv`, `MIN_NORMAL_BALLS = 100`)
| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls (Matches) | Normal Balls (`>=100`) | Normal Baseline Status | Crisis Dot % | Normal Dot % | Raw / Capped Dot Maint. (Capped?) | Provisional Score (`PRI`) | 95% Match-Cluster CI | Weight Sensitivity |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `8661` | **Matheesha Pathirana** | `BOWL_SPECIALIST` | 578 (49) | 122 | `VALID_NORMAL_BASELINE` | 36.51% | 38.52% | 0.948x / 0.948x (No) | **84.45** | [32.03%, 40.96%] | `ROBUST_ACROSS_WEIGHTS` |
| **2** | `1944` | **Keshav Maharaj** | `BOWL_PRIMARY_AR` | 225 (26) | 112 | `VALID_NORMAL_BASELINE` | 33.33% | 31.25% | 1.067x / 1.067x (No) | **68.40** | [24.88%, 41.10%] | `ROBUST_ACROSS_WEIGHTS` |
| **3** | `8380` | **Mohammad Rishad Hossain** | `BOWL_PRIMARY_AR` | 294 (40) | 261 | `VALID_NORMAL_BASELINE` | 36.05% | 42.53% | 0.848x / 0.848x (No) | **64.99** | [31.16%, 41.23%] | `ROBUST_ACROSS_WEIGHTS` |
| **4** | `6464` | **Arshdeep Singh** | `BOWL_PRIMARY_AR` | 2069 (141) | 149 | `VALID_NORMAL_BASELINE` | 36.93% | 44.30% | 0.834x / 0.834x (No) | **64.66** | [34.55%, 39.25%] | `ROBUST_ACROSS_WEIGHTS` |
| **5** | `7503` | **Ravi Bishnoi** | `BOWL_PRIMARY_AR` | 936 (94) | 401 | `VALID_NORMAL_BASELINE` | 37.07% | 38.40% | 0.965x / 0.965x (No) | **62.40** | [33.60%, 40.67%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **6** | `2681` | **Taskin Ahmed** | `BOWL_PRIMARY_AR` | 552 (46) | 100 | `VALID_NORMAL_BASELINE` | 41.67% | 50.00% | 0.833x / 0.833x (No) | **60.26** | [36.56%, 46.84%] | `ROBUST_ACROSS_WEIGHTS` |
| **7** | `4900` | **Wanindu Hasaranga** | `BOWL_PRIMARY_AR` | 868 (82) | 331 | `VALID_NORMAL_BASELINE` | 31.68% | 42.30% | 0.749x / 0.749x (No) | **59.88** | [28.49%, 34.92%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **8** | `3653` | **Avesh Khan** | `BOWL_SPECIALIST` | 1049 (77) | 136 | `VALID_NORMAL_BASELINE` | 35.46% | 41.18% | 0.861x / 0.861x (No) | **59.16** | [31.79%, 39.42%] | `ROBUST_ACROSS_WEIGHTS` |
| **9** | `2526` | **Ish Sodhi** | `BOWL_PRIMARY_AR` | 404 (46) | 249 | `VALID_NORMAL_BASELINE` | 30.94% | 35.34% | 0.875x / 0.875x (No) | **58.71** | [26.10%, 36.39%] | `RANKING_SENSITIVE_TO_WEIGHTS` |
| **10** | `3276` | **Gudakesh Motie** | `BOWL_PRIMARY_AR` | 315 (32) | 100 | `VALID_NORMAL_BASELINE` | 33.97% | 31.00% | 1.096x / 1.096x (No) | **56.23** | [26.70%, 42.49%] | `RANKING_SENSITIVE_TO_WEIGHTS` |

---

## 4. Formal Governance Sign-Off

- **Sign-Off Status:** **`P1.1 PATCH VERIFIED — PROVISIONAL MODEL`**  
- **Date:** 15 November 2026
