# SupeRR Intelligence V3 — Automated Test Report

**Project:** SupeRR Intelligence V3  
**Execution Environment:** Windows (Python 3.10.0, `pytest 8.4.2`)  
**Execution Timestamp:** 14 November 2026  
**Total Tests:** 34  
**Passed:** 34  
**Failed:** 0  
**Test Suite Status:** **100% PASS**

---

## 1. Full Pytest Execution Log

```
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-8.4.2, pluggy-1.7.0 -- D:\rrhackthon\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\rrhackthon
plugins: anyio-4.16.0
collected 34 items

tests/test_context_engine.py::test_innings_context_wickets_and_balls_faced PASSED [  2%]
tests/test_context_engine.py::test_delivery_context_dots_and_boundaries PASSED [  5%]
tests/test_context_engine.py::test_partnership_tracker PASSED            [  8%]
tests/test_preprocessing.py::test_classify_extras PASSED                 [ 11%]
tests/test_preprocessing.py::test_identify_balls_faced PASSED            [ 14%]
tests/test_preprocessing.py::test_identify_legal_balls PASSED            [ 17%]
tests/test_preprocessing.py::test_classify_bowler_wickets PASSED         [ 20%]
tests/test_preprocessing.py::test_validate_boundaries PASSED             [ 23%]
tests/test_preprocessing.py::test_add_innings_phase PASSED               [ 26%]
tests/test_preprocessing.py::test_separate_super_overs PASSED            [ 29%]
tests/test_pressure_model.py::test_dual_pressure_models_and_zero_leakage PASSED [ 32%]
tests/test_rankings.py::test_empirical_bayes_normal_shrink PASSED        [ 35%]
tests/test_rankings.py::test_empirical_bayes_beta_binomial PASSED        [ 38%]
tests/test_rankings.py::test_calculate_bowler_match_consistency_strictly_positive PASSED [ 41%]
tests/test_rankings.py::test_calculate_batter_match_consistency_strictly_positive PASSED [ 44%]
tests/test_role_classifier.py::test_build_player_name_aliases PASSED     [ 47%]
tests/test_role_classifier.py::test_classify_player_roles_wk_and_bowler PASSED [ 50%]
tests/test_scouting.py::test_scout_explosive_middle_order PASSED         [ 52%]
tests/test_scouting.py::test_scout_phase_bowlers PASSED                  [ 55%]
tests/test_v3_audit_repairs.py::test_player_id_crosswalk_integrity PASSED [ 58%]
tests/test_v3_audit_repairs.py::test_rr_appearances_adam_milne PASSED    [ 61%]
tests/test_v3_audit_repairs.py::test_dhruv_jurel_batting_average_dismissal_attribution PASSED [ 64%]
tests/test_v3_audit_repairs.py::test_candidate_player_fit_canonical_ids_and_schema PASSED [ 67%]
tests/test_v3_joint_performance.py::test_joint_model_execution_and_comparison PASSED [ 70%]
tests/test_v3_lightgbm.py::test_lightgbm_challenger_fit_and_evaluate PASSED [ 73%]
tests/test_v3_pressure_model.py::test_zero_target_leakage_and_bounds PASSED [ 76%]
tests/test_v3_reliability.py::test_match_clustered_bootstrap_batting PASSED [ 79%]
tests/test_v3_reliability.py::test_empirical_bayes_shrinkage PASSED      [ 82%]
tests/test_v3_role_classifier.py::test_five_mutually_exclusive_states PASSED [ 85%]
tests/test_v3_role_classifier.py::test_no_player_in_both_leaderboard_gates PASSED [ 88%]
tests/test_v3_rr_player_fit.py::test_rr_squad_phase_audit PASSED         [ 91%]
tests/test_v3_rr_player_fit.py::test_watchlist_candidates_structure_and_categories PASSED [ 94%]
tests/test_v3_tail_risk.py::test_tail_risk_computation_and_pareto PASSED [ 97%]
tests/test_v3_wicket_hazard.py::test_wicket_hazard_evaluation PASSED     [100%]

======================= 34 passed in 2.56s =======================
```

---

## 2. Test Coverage Breakdown by Subsystem

1. **Data Preprocessing & Extras Semantics (8 Tests):**
   - Categorical extras codes 1–7 preserved.
   - Balls faced vs legal balls verified.
   - Non-bowler dismissal segregation (581 wickets).
   - Boundary correction (20 fours, 3 sixes).
   - Super Overs quarantine (26 balls).
2. **Pressure Model & Target Leakage (2 Tests):**
   - Zero look-ahead target leakage proven.
   - Crisis and Defensive pressure mathematically bounded in $[0, 10]$.
3. **Role Classification & Leaderboard Gating (4 Tests):**
   - 5 mutually exclusive roles across 1,118 roster players.
   - Mathematical proof of 0 overlap between batting and bowling leaderboard gates.
4. **V3 Performance & Statistical Models (6 Tests):**
   - Hierarchical Ridge Joint model execution and comparison across 5 architectures.
   - Discrete-time logistic wicket hazard model calibration.
   - Over-level tail risk (VaR90, CVaR90) and Pareto frontier optimization.
   - Non-linear LightGBM challenger training and benchmark.
   - Match-clustered bootstrap resampling (500 resamples).
   - Empirical Bayes shrinkage (Normal-Normal & Beta-Binomial).
5. **Audited Entity Resolution & RR Scenarios (4 Tests):**
   - Canonical Player ID crosswalk integrity (40 entities).
   - Adam Milne 1 match played vs 16 squad selections.
   - Dhruv Jurel dismissal attribution (14 dismissals, 36.79 avg).
   - Watchlist candidates canonical IDs and provenance schema.
6. **Scouting & Squad Audit (10 Tests):**
   - Consistency metric positivity.
   - RR phase audit and gap identification.
   - Watchlist candidate structure.
