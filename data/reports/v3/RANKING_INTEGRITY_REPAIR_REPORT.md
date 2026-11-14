# V3 Universal Player Ranking Integrity — Audit, Repair & Recompute Report

**Mission Reference:** `V3-RANKING-INTEGRITY-001`  
**Document Path:** `data/reports/v3/RANKING_INTEGRITY_REPAIR_REPORT.md`  
**Execution Date:** 14 November 2026  
**Git Branch:** `fix/v3-ranking-integrity-001`  
**Baseline Git Commit:** `537777c8436fd647a484a49cfbfa30b843c98a1c`  
**Final Release Decision:** **PASSED (ALL 16 RELEASE GATES SATISFIED)**

---

## 1. Executive Summary & Defect Remediation

An independent technical audit of the Universal Player Ranking pipeline identified several data science and data engineering integrity issues. All identified defects have been systematically audited, repaired, tested, and cryptographically verified on `fix/v3-ranking-integrity-001`.

| Priority Area | Pre-Repair Vulnerability | Repaired Implementation | Verification Status |
| :--- | :--- | :--- | :--- |
| **P1: Identity & Dedup** | Duplicate source IDs split player careers; misattributions in alias dictionaries (e.g., Donovan Ferreira 8182 mapped to Dunith Wellalage; Mohammad Ali split across IDs 3083 & 20229). | Canonical identity layer (`src/identity/player_identity.py`) resolves verified duplicates before aggregation; partitions same-name distinct players; enforces quarantine on conflict. | **VERIFIED** (0 duplicates in Top 10) |
| **P2: Pressure Schema** | Missing features silently imputed with constants (`fillna(0)` or `fillna(10.0)`), turning missing data into normal pressure. Cached parquet was out of sync. | Strict schema validation in `V3PressureModel`; missing features flagged as `PRESSURE_UNCLASSIFIED`; parity parquet regenerated from verified context. | **VERIFIED** (100% validity on clean context) |
| **P3: Shrinkage Prior** | Prior mean contaminated by zero-exposure records; $K=25$ claimed as EB without estimated variance components. | Explicit prior masking excludes zero-exposure and ineligible rows; zero-exposure records remain NaN; documented as `FIXED_K_NORMAL_SHRINKAGE`. | **VERIFIED** (Prior mean = 158.48 on eligible batters) |
| **P4: Bootstrap CI** | Arbitrary fixed-width fallbacks ($\pm 40, \pm 20, \pm 30$) when sample $<3$ matches. | Fixed fallbacks removed; match-clustered bootstrap resamples whole matches; returns explicit status `ESTIMATED_MATCH_CLUSTER_BOOTSTRAP` or `NOT_ESTIMATED`. | **VERIFIED** (0 fallback intervals) |
| **P5: Eligibility Thresholds** | Unverified heuristic cutoffs (40 crisis balls / 120 crisis balls). | Prespecified threshold grid sensitivity study (108 configurations per discipline) evaluated in `RANKING_THRESHOLD_SENSITIVITY.csv`. | **VERIFIED** (Baseline confirmed) |
| **P6: Score Transparency** | Fixed PRI weights unvalidated; score sensitivity undisclosed. | Component score contributions exposed; weight sensitivity study evaluated across 5 configurations in `RANKING_WEIGHT_SENSITIVITY.csv`. | **VERIFIED** (Sensitivity status tagged) |
| **P7: Aggregation Integrity** | Risk of non-exclusive pressure tiers, unverified deliveries, and non-deterministic sorting. | Mutually exclusive tiers enforced; normal baseline validity flagged; deterministic sorting with canonical ID tie-breaker. | **VERIFIED** (100% deterministic) |
| **P8: Single Source of Truth** | Competing root-level and v3 Top-10 files. | `data/outputs/v3/TOP_10_BATTERS.csv` and `TOP_10_BOWLERS.csv` established as sole authoritative source of truth with master JSON manifest. | **VERIFIED** (Legacy outputs preserved untouched) |

---

## 2. Changed Files Manifest

### Core Source Code
- `src/identity/player_identity.py`: Canonical identity resolution layer, duplicate consolidation, and entity partitioning.
- `src/identity/__init__.py`: Identity package initialization.
- `src/pressure_engine/v3_pressure_model.py`: Schema validation, missingness detection, and explicit pressure validity indicators.
- `src/reliability/v3_reliability.py`: Match-clustered bootstrap without fallbacks, fixed-K shrinkage with eligible population masking.
- `src/classification/v3_role_classifier.py`: Canonical ID integration and name mapping.
- `src/classification/role_classifier.py`: Canonical name dictionary corrections.
- `scripts/compute_v3_rankings.py`: Integrated ranking pipeline, sensitivity studies, and authoritative exports.
- `scripts/generate_v3_roles.py`: Standalone role generation with canonical ID resolution.
- `scripts/verify_v3_rankings.py`: Independent mathematical reconciliation script.

### Regression Tests (All Passing)
- `tests/test_v3_ranking_identity_integrity.py`: Entity deduplication and partition tests (5 tests).
- `tests/test_v3_pressure_feature_integrity.py`: Pressure schema completeness and parquet validation (4 tests).
- `tests/test_v3_ranking_pressure_integrity.py`: Ranking pressure baseline and normal exposure tests (3 tests).
- `tests/test_v3_ranking_shrinkage_integrity.py`: Prior population masking and weight tests (3 tests).
- `tests/test_v3_ranking_ci_integrity.py`: Clustered bootstrap reproducibility and fallback removal tests (4 tests).
- `tests/test_v3_ranking_eligibility.py`: Threshold sensitivity and exclusion reason tests (4 tests).
- `tests/test_v3_ranking_determinism.py`: Determinism and authoritative reconciliation tests (3 tests).
- `tests/test_v3_wicket_hazard.py`: Seeded deterministic hazard test (1 test).

### Generated Authoritative Artifacts
- `data/outputs/v3/TOP_10_BATTERS.csv`
- `data/outputs/v3/TOP_10_BOWLERS.csv`
- `data/outputs/v3/ALL_BATTER_METRICS.csv`
- `data/outputs/v3/ALL_BOWLER_METRICS.csv`
- `data/outputs/v3/PLAYER_ELIGIBILITY.csv`
- `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`
- `data/outputs/v3/RANKING_WEIGHT_SENSITIVITY.csv`
- `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`
- `data/outputs/v3/PLAYER_IDENTITY_CROSSWALK.csv`
- `data/outputs/v3/player_roles.csv`
- `data/features/ball_by_ball_with_pressure.parquet` (rebuilt V3.1)
- `data/baseline_artifacts/` (immutable backup of baseline ranking files and hashes)

---

## 3. Detailed Identity Resolution & Deduplication Audit

The canonical identity crosswalk (`data/outputs/v3/PLAYER_IDENTITY_CROSSWALK.csv`) audits all 1,118 source player records:

1. **Mohammad Ali Consolidation:**
   - Source ID `20229` (Pakistan in England & NZ, 2024–2025) consolidated into canonical ID `3083` (Pakistan vs NZ, April 2024).
   - Method: `VERIFIED_DUPLICATE_CONSOLIDATION`. Career stats merged before role classification and ranking aggregation.
2. **Abdul Samad Partitioning:**
   - Source ID `7446` (Abdul Samad, India / SRH / LSG) partitioned from Source ID `6922` (Abdul Samad, Pakistan national team).
   - Method: `SAME_NAME_DIFFERENT_PLAYER_PARTITION`. Prevented false entity merger between distinct international players.
3. **Haider Ali Partitioning:**
   - Source ID `7338` (Haider Ali, Pakistan national team) partitioned from Source ID `28756` (Haider Ali, UAE national team).
   - Method: `SAME_NAME_DIFFERENT_PLAYER_PARTITION`.
4. **Donovan Ferreira vs Dunith Wellalage Correction:**
   - Source ID `8182` corrected to `Donovan Ferreira` (South African / RR batter-keeper).
   - Source ID `7052` maintained as `Dunith Wellalage` (Sri Lanka all-rounder).
   - Method: `CORRECTED_MISATTRIBUTION`. Eliminated duplicate appearance of Dunith Wellalage across conflicting roles.
5. **Ambiguous Conflict Quarantine:**
   - Zero unresolved identity collisions remain in the active dataset. Any synthetic conflict ID is routed to `IDENTITY_CONFLICT` status and quarantined from leaderboards.

---

## 4. Prior Population and Shrinkage Transparency

### 4.1 Batting Fixed-K Normal Shrinkage
- **Method Name:** `FIXED_K_NORMAL_SHRINKAGE`
- **Prior Strength:** $K = 25.0$ (explicit fixed assumption, not empirically estimated variance ratio)
- **Prior Population Mask:** Valid canonical ID, positive pressure exposure ($\text{crisis balls} > 0$), finite rate, sample-eligible ($\ge 40$ crisis balls, $\ge 120$ total balls, $\ge 5$ matches, $\ge 30$ normal balls), role-eligible (`BAT_SPECIALIST` or `BAT_PRIMARY_AR`), non-quarantined.
- **Eligible Prior Population Size:** 39 players
- **Prior Mean:** $\mu_0 = 158.48$
- **Zero-Exposure Handling:** Shrunk rate remains `NaN` (never filled with synthetic values).

### 4.2 Bowling Beta-Binomial Shrinkage
- **Method Name:** `BETA_BINOMIAL_EMPIRICAL_BAYES`
- **Prior Population Mask:** Valid trials ($\ge 10$ crisis balls), eligible role, non-quarantined.
- **Prior Parameters:** $\alpha = 1.0$, $\beta = 19.0$ ($\mu_0 = 5.0\%$)
- **Prior Population Size:** 130 frontline bowlers
- **Zero-Trial Handling:** Shrunk rate remains `NaN`.

---

## 5. Confidence Interval Integrity & Uncertainty Widths

All artificial fallbacks ($\pm 40, \pm 20, \pm 30, \text{fixed width } 80, 40$) have been excised.
- **Bootstrap Method:** Match-clustered non-parametric bootstrap resampling whole `match_id` clusters with replacement.
- **Replications:** 2,000 iterations for final authoritative rankings.
- **Coverage:** 95% two-sided intervals $[2.5\%, 97.5\%]$.
- **Status Accounting:**
  - 100% of ranked Top-10 batters and bowlers have status `ESTIMATED_MATCH_CLUSTER_BOOTSTRAP`.
  - Players with $<3$ match clusters receive status `NOT_ESTIMATED_INSUFFICIENT_MATCH_CLUSTERS` and `NaN` bounds.

---

## 6. Authoritative Top-10 Comparison (Before vs. After)

### 6.1 Authoritative Top 10 Batters Under Pressure (V3)
| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls | Crisis SR | Maint Ratio | Prov PRI Score | 95% CI Status | CI [Low, High] |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 7897 | Tilak Varma | BAT_PRIMARY_AR | 60 | 196.67 | 1.361 | **94.29** | ESTIMATED | [133.33, 260.00] |
| **2** | 796 | Matthew Wade | BAT_SPECIALIST | 50 | 172.00 | 1.190 | **77.35** | ESTIMATED | [100.00, 240.00] |
| **3** | 4106 | Daryl Mitchell | BAT_PRIMARY_AR | 44 | 177.27 | 1.205 | **72.55** | ESTIMATED | [94.12, 255.56] |
| **4** | 4391 | Liam Livingstone | BAT_PRIMARY_AR | 60 | 175.00 | 1.085 | **68.92** | ESTIMATED | [93.75, 250.00] |
| **5** | 4773 | Jaker Ali Anik | BAT_SPECIALIST | 63 | 139.68 | 1.141 | **65.13** | ESTIMATED | [88.89, 186.67] |
| **6** | 7446 | Abdul Samad | BAT_SPECIALIST | 69 | 169.57 | 1.005 | **64.51** | ESTIMATED | [100.00, 237.50] |
| **7** | 1077 | David Miller | BAT_SPECIALIST | 56 | 166.07 | 1.064 | **63.35** | ESTIMATED | [100.00, 233.33] |
| **8** | 8 | MS Dhoni | BAT_SPECIALIST | 133 | 154.89 | 1.099 | **62.51** | ESTIMATED | [104.76, 203.45] |
| **9** | 3056 | Iftikhar Ahmed | BAT_PRIMARY_AR | 40 | 127.50 | 1.054 | **62.38** | ESTIMATED | [76.92, 175.00] |
| **10** | 3916 | Jitesh Sharma | BAT_SPECIALIST | 51 | 172.55 | 1.109 | **62.01** | ESTIMATED | [100.00, 236.36] |

**Key Batting Changes:**
- Rinku Singh dropped from Rank 9 (score 62.78) to Rank 13 (score 60.15) due to lower maintenance ratio under cleaned normal baseline.
- Iftikhar Ahmed (Rank 9, score 62.38) and Jitesh Sharma (Rank 10, score 62.01) entered the Top 10 with verified canonical roles and high crisis consistency.
- Ramandeep Singh moved from Rank 10 to Rank 11 (score 61.20).
- Abdul Samad (ID 7446) consolidated career records strictly from SRH/LSG, verified at Rank 6 (score 64.51).

### 6.2 Authoritative Top 10 Bowlers Under Defensive Pressure (V3)
| Rank | Canonical ID | Player Name | V3 Role | Crisis Balls | Crisis Dot % | Dot Maint | Prov PRI Score | 95% CI Status | CI [Low, High] |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 5379 | Mark Adair | BOWL_PRIMARY_AR | 483 | 39.75% | 1.500 | **80.96** | ESTIMATED | [35.29, 44.20] |
| **2** | 3720 | Craig Young | BOWL_SPECIALIST | 289 | 38.75% | 1.163 | **78.27** | ESTIMATED | [33.33, 44.44] |
| **3** | 2985 | Mark Wood | BOWL_SPECIALIST | 156 | 48.08% | 1.146 | **75.88** | ESTIMATED | [39.13, 57.14] |
| **4** | 4837 | Obed McCoy | BOWL_SPECIALIST | 334 | 37.43% | 1.324 | **71.37** | ESTIMATED | [31.58, 43.14] |
| **5** | 2320 | Trent Boult | BOWL_SPECIALIST | 879 | 38.34% | 1.500 | **70.79** | ESTIMATED | [34.78, 41.86] |
| **6** | 8661 | Matheesha Pathirana | BOWL_SPECIALIST | 578 | 36.51% | 0.948 | **69.87** | ESTIMATED | [32.14, 40.82] |
| **7** | 7741 | Gareth Delany | BOWL_PRIMARY_AR | 178 | 39.33% | 1.500 | **69.74** | ESTIMATED | [31.58, 47.37] |
| **8** | 3629 | Corbin Bosch | BOWL_PRIMARY_AR | 164 | 39.63% | 0.829 | **69.61** | ESTIMATED | [31.82, 47.62] |
| **9** | 22920 | Jacob Duffy | BOWL_SPECIALIST | 486 | 42.59% | 0.923 | **68.97** | ESTIMATED | [37.78, 47.62] |
| **10** | 1487 | Adam Milne | BOWL_SPECIALIST | 362 | 43.09% | 1.065 | **67.03** | ESTIMATED | [37.50, 48.72] |

**Key Bowling Changes:**
- Matheesha Pathirana (Rank 6, score 69.87), Corbin Bosch (Rank 8, score 69.61), and Adam Milne (Rank 10, score 67.03) entered the Top 10 with verified legal delivery counts and bowler-creditable dismissals.
- Deepak Chahar (moved to Rank 12, score 66.85) and Eshan Malinga (Rank 14, score 65.40) adjusted under verified legal deliveries and unclassified exclusions.
- Dunith Wellalage is verified as sole canonical ID 7052 (Rank 38 in bowling, score 56.42), completely separated from Donovan Ferreira (Rank 17 in batting, score 57.10).

---

## 7. Weight Sensitivity Audit Findings

Evaluating the 5 prespecified configurations (`balanced_default`, `maintenance_heavy`, `absolute_heavy`, `consistency_heavy`, `equal_weights`) from `src/ranking_engine/pressure_rankings.py`:
- **Batters:**
  - 24 / 39 (61.5%) eligible batters are `ROBUST_ACROSS_WEIGHTS` (max rank shift $<5$).
  - 15 / 39 (38.5%) eligible batters are `RANKING_SENSITIVE_TO_WEIGHTS`.
  - Tilak Varma (Rank 1) and Matthew Wade (Rank 2) are 100% robust, holding Rank 1 and Rank 2 across all 5 configurations!
- **Bowlers:**
  - 14 / 130 (10.8%) eligible bowlers are `ROBUST_ACROSS_WEIGHTS`.
  - 116 / 130 (89.2%) eligible bowlers are `RANKING_SENSITIVE_TO_WEIGHTS`.
  - The bowler leaderboard is highly sensitive to the balance between defensive dot maintenance (economy) versus absolute crisis wicket rate (strike rate).
  - Mark Adair, Craig Young, and Mark Wood consistently occupy Top 4 positions across all configurations.

---

## 8. Reproducibility & Cryptographic Determinism Hashes

Two independent end-to-end runs of the pipeline from identical inputs produced identical SHA-256 hashes across all 7 generated artifacts:

| Authoritative Output File | Run 1 SHA-256 Hash | Run 2 SHA-256 Hash | Cryptographic Match |
| :--- | :--- | :--- | :---: |
| `TOP_10_BATTERS.csv` | `9282e0428cc8c2bbd87ec9196270dbe4398c43cca413e16f00058fad1d0bb382` | `9282e0428cc8c2bbd87ec9196270dbe4398c43cca413e16f00058fad1d0bb382` | **MATCH (100%)** |
| `TOP_10_BOWLERS.csv` | `38156c564055b5cf4b8a797deb90b33f8ef12dea01ba21c5db80e7ba4f2e8696` | `38156c564055b5cf4b8a797deb90b33f8ef12dea01ba21c5db80e7ba4f2e8696` | **MATCH (100%)** |
| `ALL_BATTER_METRICS.csv` | `6063e59806a47ef07d7f46ff10a48d0a2dad0ed3b2f6ade23ec2cefaed74acb1` | `6063e59806a47ef07d7f46ff10a48d0a2dad0ed3b2f6ade23ec2cefaed74acb1` | **MATCH (100%)** |
| `ALL_BOWLER_METRICS.csv` | `281b93d087e1be16a152e44e58af4899eb71b4d7c516b36261315efcd1dabbd9` | `281b93d087e1be16a152e44e58af4899eb71b4d7c516b36261315efcd1dabbd9` | **MATCH (100%)** |
| `PLAYER_ELIGIBILITY.csv` | `6669114fc0e682d7608ddf8423bbe95ef65f73da171a4c95e13a2d92a66a2079` | `6669114fc0e682d7608ddf8423bbe95ef65f73da171a4c95e13a2d92a66a2079` | **MATCH (100%)** |
| `RANKING_THRESHOLD_SENSITIVITY.csv` | `f2ee6417b2008082a3d871e0ae34f0891c14b8d104e668a2ad1d1d53213bd396` | `f2ee6417b2008082a3d871e0ae34f0891c14b8d104e668a2ad1d1d53213bd396` | **MATCH (100%)** |
| `RANKING_WEIGHT_SENSITIVITY.csv` | `b3c09e5592e105d6f0d1a953211faabe01c5677f243e98c73fb00ca5686848c2` | `b3c09e5592e105d6f0d1a953211faabe01c5677f243e98c73fb00ca5686848c2` | **MATCH (100%)** |

---

## 9. Final Release Gate Verification Checklist

| Gate # | Integrity Verification Criterion | Result | Evidence |
| :---: | :--- | :---: | :--- |
| **1** | Canonical player identity resolved / conflicts quarantined | **PASSED** | `PLAYER_IDENTITY_CROSSWALK.csv` (1,118 rows audited) |
| **2** | Duplicate player ranking rows eliminated | **PASSED** | Top 10 unique IDs confirmed; 0 duplicate entities |
| **3** | Pressure data completeness enforced | **PASSED** | Strict schema validation; `tests/test_v3_pressure_feature_integrity.py` |
| **4** | Missing pressure states do not become normal conditions | **PASSED** | Explicit `PRESSURE_UNCLASSIFIED` tier; mutually exclusive |
| **5** | Shrinkage prior population valid and documented | **PASSED** | Masked on positive-exposure eligible cohort ($\mu_0 = 158.48$) |
| **6** | $K=25$ honestly labelled as fixed assumption | **PASSED** | Labelled `FIXED_K_NORMAL_SHRINKAGE` / `FIXED_K_ASSUMPTION` |
| **7** | Arbitrary confidence interval fallbacks removed | **PASSED** | Zero $\pm 40 / \pm 20$ fallbacks; NaN bounds on low clusters |
| **8** | Confidence intervals include explicit status & cluster evidence | **PASSED** | `ESTIMATED_MATCH_CLUSTER_BOOTSTRAP` with match/delivery counts |
| **9** | Eligibility threshold sensitivity study completed | **PASSED** | `RANKING_THRESHOLD_SENSITIVITY.csv` (216 grid runs) |
| **10** | Score sensitivity study completed | **PASSED** | `RANKING_WEIGHT_SENSITIVITY.csv` (169 eligible players $\times$ 5 configs) |
| **11** | Exactly one authoritative batter Top-10 CSV exists | **PASSED** | `data/outputs/v3/TOP_10_BATTERS.csv` |
| **12** | Exactly one authoritative bowler Top-10 CSV exists | **PASSED** | `data/outputs/v3/TOP_10_BOWLERS.csv` |
| **13** | Independent verification reconciles every Top-10 row | **PASSED** | `scripts/verify_v3_rankings.py` passed 100% |
| **14** | Full test suite passes | **PASSED** | 60 passed in 4.03s (0 failures, 0 errors) |
| **15** | Two ranking runs are cryptographically deterministic | **PASSED** | 7 of 7 SHA-256 hashes matched identically |
| **16** | Source data and legacy outputs preserved untouched | **PASSED** | `data/baseline_artifacts/` immutable backup intact |

---

## 10. Final Decision: PASSED

All sixteen mandatory release criteria have been satisfied. Universal Player Ranking Integrity for Priority 1 through Priority 10 is officially **PASSED**.

Per mission guidelines:
- No README, dashboard, PDF report, or RR player-fit files were modified during this task.
- Ready for owner review and subsequent downstream report synchronization.
