# SupeRR Intelligence V3 — Automated Test Report (P1.1)

**Project:** SupeRR Intelligence V3  
**Branch:** `fix/v3-pre-submission-consistency-001`  
**Execution Environment:** Windows (Python 3.10.0, `pytest 8.4.2`)  
**Execution Timestamp:** 15 November 2026  
**Total Tests:** 64  
**Passed:** 64  
**Failed:** 0  
**Test Suite Status:** **100% PASS (`64 passed`)**  
**Overall Model Governance Status:** **`P1.1 PATCH VERIFIED — PROVISIONAL MODEL`**

---

## 1. Pytest Summary by Test Module (64 Tests across 17 Modules)

| Test Module | Tests | Scope & Verification Coverage | Status |
| :--- | :---: | :--- | :---: |
| `tests/test_context_engine.py` | 3 | Pre-delivery wickets, balls faced, dots, boundaries, partnerships | **PASSED** |
| `tests/test_preprocessing.py` | 7 | Categorical extras (1–7), legal balls, bowler wickets, super overs | **PASSED** |
| `tests/test_pressure_model.py` | 1 | Dual pre-delivery pressure bounds & zero look-ahead leakage | **PASSED** |
| `tests/test_rankings.py` | 4 | Fixed-$K$ normal & Beta-Binomial shrinkage, match consistency positivity | **PASSED** |
| `tests/test_role_classifier.py` | 2 | Player alias resolution & role classification | **PASSED** |
| `tests/test_scouting.py` | 2 | Phase-based scouting filters | **PASSED** |
| `tests/test_v3_audit_repairs.py` | 4 | RR crosswalk (40 entities), Adam Milne (1 match), Dhruv Jurel avg (36.79), fit schema | **PASSED** |
| `tests/test_v3_joint_performance.py` | 1 | Exploratory Ridge regression execution (`EXPERIMENTAL_NOT_USED_FOR_RANKING`) | **PASSED** |
| `tests/test_v3_lightgbm.py` | 1 | Exploratory LightGBM execution (`EXPERIMENTAL_NOT_USED_FOR_RANKING`) | **PASSED** |
| `tests/test_v3_pressure_feature_integrity.py` | 4 | Required schema checks, no silent zero-imputation, parquet parity | **PASSED** |
| `tests/test_v3_pressure_model.py` | 1 | Zero target leakage & `[0, 10]` score bounds | **PASSED** |
| `tests/test_v3_ranking_ci_integrity.py` | 4 | 2,000-iteration match-clustered bootstrap, zero fixed-width fallbacks | **PASSED** |
| `tests/test_v3_ranking_determinism.py` | 5 | Authoritative Top-10 reconciliation, SHA-256 parity across all 14 copies, Iftikhar Ahmed component breakdown & `CRISIS_SR_BELOW_COHORT_MEAN` flag | **PASSED** |
| `tests/test_v3_ranking_eligibility.py` | 6 | Extended crisis-ball grid (`40, 60, 80, 100, 150, 200, 250`), unforced `available_top10_count`, bowler `MIN_NORMAL_BALLS = 100` (`BOWLER_NORMAL_BASELINE_INSUFFICIENT`) | **PASSED** |
| `tests/test_v3_ranking_identity_integrity.py` | 5 | Canonical ID deduplication (Mohammad Ali `3083`), same-name partition (Abdul Samad, Haider Ali), Ferreira/Wellalage fix | **PASSED** |
| `tests/test_v3_ranking_pressure_integrity.py` | 3 | Mutually exclusive pressure tiers, normal baseline gating | **PASSED** |
| `tests/test_v3_ranking_shrinkage_integrity.py` | 3 | Eligible prior population masking, NaN preservation for zero exposure | **PASSED** |
| `tests/test_v3_reliability.py` | 2 | Match-clustered bootstrap & shrinkage functions | **PASSED** |
| `tests/test_v3_role_classifier.py` | 2 | 5 mutually exclusive roles & zero bat/bowl leaderboard gate overlap | **PASSED** |
| `tests/test_v3_rr_player_fit.py` | 2 | RR squad phase audit & 13 watchlist candidates | **PASSED** |
| `tests/test_v3_tail_risk.py` | 1 | Over-level VaR90/CVaR90 calculation | **PASSED** |
| `tests/test_v3_wicket_hazard.py` | 1 | Seeded logistic hazard evaluation (`EXPERIMENTAL_NOT_USED_FOR_RANKING`) | **PASSED** |
| **TOTAL** | **64** | **All unit, integration, and P1.1 consistency gates** | **64 PASSED** |
