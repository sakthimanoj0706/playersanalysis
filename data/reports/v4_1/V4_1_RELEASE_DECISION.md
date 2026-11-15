# V4.1 RELEASE DECISION — SupeRR Intelligence V4.1

## Final Scientific Release Status
**`V4.1 PROVISIONAL — RESOURCE STRESS`**

> **Statistical Certainty Finding:** Across `110` precision-eligible batters and `135` precision-eligible bowlers, **ALL 95% Bayesian credible intervals and bootstrap 95% intervals cross zero (`0 RELIABLE`)**. No player has a statistically established positive pressure-vs-own-normal effect at 95% confidence. Below is the transparent **`PROVISIONAL`** candidate ordering by Empirical Bayes posterior mean (`empirical_bayes_delta`), alongside complete bootstrap rank uncertainty (`[boot_rank_ci_low, boot_rank_ci_high]`) and Top-10 membership probability (`prob_top_10`).

---

## 1. Decision Justification (Strict Section 11 Governance)
1. **Why NOT `V4.1 VALIDATED — MATCH PRESSURE`:**
   - Supplied data fails non-DLS run-margin reconstruction on `342 / 390` matches (`0 / 837` matches free of extras, `0` external scorecards matched by `match_id`). Targets, exact team scores, `RRR`, and Match Leverage remain blocked.
   - Claim C (`CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY`) remains weak/inconclusive across out-of-time single-season validation and even/odd match halves (`tau_bat=2.28`, `I2=5.8%`; `tau_bowl=3.60`, `I2=4.7%`).
2. **Why NOT `V4.1 NO-GO — RANKING INTEGRITY FAILURE`:**
   - Exact data reconciliation (`194,014 = 193,988 + 26`), DLS unit correction, identity resolution (`player_id`), Ridge context normalization (`(60,60,60)` chosen for lower OOT RMSE than `(35,30,35)`), canonical `span=0.75`, correlated ranking bootstrap (`B=1,000`), and deterministic verification all pass end-to-end.

---

## 2. Provisional Top 10 Batters (`PROVISIONAL_CI_CROSSES_ZERO`, `BATTER_RUNS_PER_100_BALLS`)
| provisional_rank | player_name | total_matches | n_hi | n_lo | raw_observed_delta | context_adjusted_delta | empirical_bayes_delta | lower_confidence_bound | upper_confidence_bound | probability_positive_effect | boot_rank_ci_low | boot_rank_ci_high | prob_top_10 | reliability_tier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Brian Bennett | 44 | 87 | 169 | 11.88 | 45.90 | 1.08 | -3.37 | 5.53 | 0.68 | 1.00 | 34.00 | 0.81 | PROVISIONAL_CI_CROSSES_ZERO |
| 2 | Virat Kohli | 92 | 79 | 1055 | -19.27 | 13.28 | 1.01 | -3.38 | 5.40 | 0.67 | 5.00 | 73.00 | 0.11 | PROVISIONAL_CI_CROSSES_ZERO |
| 3 | Salman Agha | 42 | 300 | 105 | -29.76 | 31.73 | 1.01 | -3.43 | 5.45 | 0.67 | 1.00 | 42.00 | 0.67 | PROVISIONAL_CI_CROSSES_ZERO |
| 4 | David Miller | 81 | 296 | 456 | -14.91 | 18.05 | 0.99 | -3.43 | 5.41 | 0.67 | 3.00 | 79.00 | 0.20 | PROVISIONAL_CI_CROSSES_ZERO |
| 5 | Nehal Wadhera | 37 | 231 | 98 | -15.03 | 32.35 | 0.96 | -3.49 | 5.41 | 0.66 | 1.00 | 61.00 | 0.40 | PROVISIONAL_CI_CROSSES_ZERO |
| 6 | Towhid Hridoy | 50 | 246 | 277 | -4.20 | 15.46 | 0.93 | -3.49 | 5.34 | 0.66 | 3.00 | 79.00 | 0.17 | PROVISIONAL_CI_CROSSES_ZERO |
| 7 | Nicholas Pooran | 115 | 367 | 660 | -27.30 | 14.36 | 0.92 | -3.50 | 5.33 | 0.66 | 4.00 | 84.00 | 0.12 | PROVISIONAL_CI_CROSSES_ZERO |
| 8 | Ibrahim Zadran | 47 | 211 | 415 | -7.10 | 13.59 | 0.91 | -3.50 | 5.32 | 0.66 | 5.00 | 76.00 | 0.11 | PROVISIONAL_CI_CROSSES_ZERO |
| 9 | Kamindu Mendis | 38 | 222 | 113 | -22.69 | 24.03 | 0.89 | -3.55 | 5.33 | 0.65 | 2.00 | 71.00 | 0.36 | PROVISIONAL_CI_CROSSES_ZERO |
| 10 | Faf du Plessis | 54 | 105 | 527 | -5.44 | 15.50 | 0.89 | -3.53 | 5.31 | 0.65 | 3.00 | 81.00 | 0.15 | PROVISIONAL_CI_CROSSES_ZERO |

---

## 3. Provisional Top 10 Bowlers (`PROVISIONAL_CI_CROSSES_ZERO`, `BATTER_RUNS_CONCEDED_PROXY_SAVED_PER_100_BALLS`)
> **Bowler Metric Warning:** `BATTER_RUNS_CONCEDED_PROXY` excludes multi-run wides/byes/leg-byes/penalties and is **NOT full bowling economy**. Positive values indicate fewer batter-credited runs conceded per 100 legal balls (`-100 * batter_runs/ball`).

| provisional_rank | player_name | total_matches | n_hi | n_lo | raw_observed_delta | context_adjusted_delta | empirical_bayes_delta | lower_confidence_bound | upper_confidence_bound | probability_positive_effect | boot_rank_ci_low | boot_rank_ci_high | prob_top_10 | reliability_tier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Maheesh Theekshana | 99 | 579 | 457 | -18.24 | 21.96 | 1.64 | -5.02 | 8.30 | 0.69 | 2.00 | 50.00 | 0.43 | PROVISIONAL_CI_CROSSES_ZERO |
| 2 | Haris Rauf | 48 | 273 | 213 | -5.03 | 36.12 | 1.43 | -5.41 | 8.26 | 0.66 | 1.00 | 42.00 | 0.72 | PROVISIONAL_CI_CROSSES_ZERO |
| 3 | Jasprit Bumrah | 75 | 612 | 314 | -19.69 | 23.37 | 1.34 | -5.39 | 8.07 | 0.65 | 1.00 | 56.00 | 0.42 | PROVISIONAL_CI_CROSSES_ZERO |
| 4 | Matheesha Pathirana | 54 | 515 | 170 | -14.96 | 29.04 | 0.94 | -5.90 | 7.78 | 0.61 | 1.00 | 55.00 | 0.54 | PROVISIONAL_CI_CROSSES_ZERO |
| 5 | Lungi Ngidi | 39 | 258 | 158 | -13.03 | 34.46 | 0.67 | -6.24 | 7.57 | 0.57 | 1.00 | 57.00 | 0.53 | PROVISIONAL_CI_CROSSES_ZERO |
| 6 | Alzarri Joseph | 53 | 349 | 189 | -7.00 | 23.53 | 0.65 | -6.19 | 7.49 | 0.57 | 1.00 | 67.00 | 0.36 | PROVISIONAL_CI_CROSSES_ZERO |
| 7 | Xavier Bartlett | 31 | 149 | 152 | -48.67 | 46.61 | 0.56 | -6.39 | 7.51 | 0.56 | 1.00 | 65.00 | 0.58 | PROVISIONAL_CI_CROSSES_ZERO |
| 8 | Gerald Coetzee | 29 | 192 | 102 | -16.04 | 38.75 | 0.54 | -6.39 | 7.47 | 0.56 | 1.00 | 47.00 | 0.71 | PROVISIONAL_CI_CROSSES_ZERO |
| 9 | Sam Curran | 73 | 474 | 208 | -20.47 | 19.82 | 0.54 | -6.28 | 7.35 | 0.56 | 2.00 | 84.00 | 0.26 | PROVISIONAL_CI_CROSSES_ZERO |
| 10 | Sunil Narine | 67 | 412 | 340 | -31.30 | 13.61 | 0.43 | -6.31 | 7.17 | 0.55 | 5.00 | 82.00 | 0.15 | PROVISIONAL_CI_CROSSES_ZERO |

---

## 4. Separated Validation Matrix — Claims A, B, C & Engineering Diagnostics
| claim_category | validation_family | role | metric | split | n_eval | pearson_r | spearman_rho | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2023 -> 2024 | 62 | 0.348 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2023 -> 2024 | 62 | 0.091 | nan | LOW_OR_MIXED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2023 -> 2024 | 62 | -0.007 | -0.020 | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | batter | batter_runs | raw_delta <= 2023 -> 2024 | 62 | -0.042 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2023 -> 2024 | 92 | 0.251 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2023 -> 2024 | 92 | 0.015 | nan | LOW_OR_MIXED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2023 -> 2024 | 92 | -0.119 | -0.135 | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | bowler | batter_runs | raw_delta <= 2023 -> 2024 | 92 | -0.107 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2023 -> 2024 | 92 | 0.311 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2023 -> 2024 | 92 | -0.049 | nan | LOW_OR_MIXED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2023 -> 2024 | 92 | nan | nan | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | bowler | is_ctrl_ball | raw_delta <= 2023 -> 2024 | 92 | 0.203 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2024 -> 2025 | 74 | 0.383 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2024 -> 2025 | 74 | 0.071 | nan | LOW_OR_MIXED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2024 -> 2025 | 74 | 0.078 | 0.041 | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | batter | batter_runs | raw_delta <= 2024 -> 2025 | 74 | 0.007 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2024 -> 2025 | 101 | 0.389 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2024 -> 2025 | 101 | 0.230 | nan | REPLICATED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2024 -> 2025 | 101 | nan | nan | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | bowler | batter_runs | raw_delta <= 2024 -> 2025 | 101 | 0.196 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2024 -> 2025 | 101 | 0.446 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2024 -> 2025 | 101 | 0.168 | nan | REPLICATED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2024 -> 2025 | 101 | 0.041 | 0.029 | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | bowler | is_ctrl_ball | raw_delta <= 2024 -> 2025 | 101 | 0.180 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2025 -> 2026 | 70 | 0.354 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2025 -> 2026 | 70 | -0.214 | nan | LOW_OR_MIXED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | batter | batter_runs | <=2025 -> 2026 | 70 | -0.093 | -0.107 | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | batter | batter_runs | raw_delta <= 2025 -> 2026 | 70 | -0.085 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2025 -> 2026 | 91 | 0.392 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2025 -> 2026 | 91 | 0.147 | nan | LOW_OR_MIXED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | batter_runs | <=2025 -> 2026 | 91 | -0.082 | -0.105 | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | bowler | batter_runs | raw_delta <= 2025 -> 2026 | 91 | -0.011 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2025 -> 2026 | 91 | 0.503 | nan | REPEATABLE_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2025 -> 2026 | 91 | 0.123 | nan | LOW_OR_MIXED |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | ROLLING_ORIGIN_TEMPORAL | bowler | is_ctrl_ball | <=2025 -> 2026 | 91 | -0.062 | -0.088 | INCONCLUSIVE_WEAK_TEMPORAL_DELTA |
| CLAIM_C_DECOMPOSITION_STABILITY | UNADJUSTED_VS_ADJUSTED_TEMPORAL | bowler | is_ctrl_ball | raw_delta <= 2025 -> 2026 | 91 | 0.129 | nan | UNADJUSTED_BASELINE_TRACKED |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | EVEN_ODD_SPLIT_HALF | batter | batter_runs | even_vs_odd_matches | 90 | 0.463 | nan | SPLIT_HALF_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | EVEN_ODD_SPLIT_HALF | batter | batter_runs | even_vs_odd_matches | 90 | -0.022 | nan | SPLIT_HALF_HIGH_STRESS |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | EVEN_ODD_SPLIT_HALF | batter | batter_runs | even_vs_odd_matches | 90 | 0.067 | 0.071 | INCONCLUSIVE_LOW_SPLIT_HALF_DELTA |
| CLAIM_A_GENERAL_SKILL_REPEATABILITY | EVEN_ODD_SPLIT_HALF | bowler | batter_runs | even_vs_odd_matches | 132 | 0.535 | nan | SPLIT_HALF_GENERAL_SKILL |
| CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY | EVEN_ODD_SPLIT_HALF | bowler | batter_runs | even_vs_odd_matches | 132 | 0.429 | nan | SPLIT_HALF_HIGH_STRESS |
| CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY | EVEN_ODD_SPLIT_HALF | bowler | batter_runs | even_vs_odd_matches | 132 | 0.037 | -0.020 | INCONCLUSIVE_LOW_SPLIT_HALF_DELTA |
| CLAIM_C_RESOURCE_STRESS_SPEC_SENSITIVITY | PROXY_SPEC_SENSITIVITY | batter | batter_runs | BAT_STRESS_NONPARAM_WKT | 110 | nan | nan | SPECIFICATION_SENSITIVITY_LOGGED |
| CLAIM_C_RESOURCE_STRESS_SPEC_SENSITIVITY | PROXY_SPEC_SENSITIVITY | bowler | batter_runs | BOWL_THREAT_CELL_MEAN | 135 | 0.464 | 0.445 | SPECIFICATION_SENSITIVITY_LOGGED |
| CLAIM_C_QUANTILE_SENSITIVITY | PRESSURE_QUANTILE_CUTOFFS | batter | batter_runs | P80_vs_P20 | 110 | 0.990 | 0.986 | QUANTILE_SENSITIVITY_LOGGED |
| CLAIM_C_QUANTILE_SENSITIVITY | PRESSURE_QUANTILE_CUTOFFS | bowler | batter_runs | P80_vs_P20 | 135 | 1.000 | 0.999 | QUANTILE_SENSITIVITY_LOGGED |
| CLAIM_C_QUANTILE_SENSITIVITY | PRESSURE_QUANTILE_CUTOFFS | batter | batter_runs | P85_vs_P15 | 110 | nan | nan | QUANTILE_SENSITIVITY_LOGGED |
| CLAIM_C_QUANTILE_SENSITIVITY | PRESSURE_QUANTILE_CUTOFFS | bowler | batter_runs | P85_vs_P15 | 135 | 0.998 | 0.996 | QUANTILE_SENSITIVITY_LOGGED |
| ENGINEERING_DIAGNOSTIC_ONLY | SHUFFLED_PRESSURE_PLACEBO_NULL | batter | batter_runs | permuted_pressure_null | 186 | nan | nan | DIAGNOSTIC_PASS_NULL (Q=192.6/185, z=+0.39) |
| ENGINEERING_DIAGNOSTIC_ONLY | SHUFFLED_PRESSURE_PLACEBO_NULL | bowler | batter_runs | permuted_pressure_null | 192 | nan | nan | DIAGNOSTIC_PASS_NULL (Q=161.9/191, z=-1.49) |
| ENGINEERING_DIAGNOSTIC_ONLY | SYNTHETIC_SIGNAL_RECOVERY | batter | batter_runs (+60 SR injected) | 10_injected_eligible | 10 | nan | 0.600 | DIAGNOSTIC_RECOVERY_6_OF_10_IN_TOP15 |

---

## 5. Artifact Manifest (`data/outputs/v4_1/` & `data/reports/v4_1/`)
- `data/outputs/v4_1/V4_1_RAW_ADJUSTED_DECOMPOSITION.csv`
- `data/outputs/v4_1/V4_1_ELIGIBILITY_PRECISION_ANALYSIS.csv`
- `data/outputs/v4_1/V4_1_RANK_PROBABILITIES.csv`
- `data/outputs/v4_1/V4_1_MODEL_COMPARISON.csv`
- `data/outputs/v4_1/V4_1_FINAL_SHORTLIST.csv`
- `data/outputs/v4_1/V4_1_SCORE_ENRICHMENT_AUDIT.csv`
- `data/outputs/v4_1/V4_1_VALIDATION_MATRIX.csv`
- `data/outputs/v4_1/V4_1_SOURCE_OF_TRUTH.json`
- `data/reports/v4_1/V4_1_STATISTICAL_CORRECTIONS.md`
- `data/reports/v4_1/V4_1_RELEASE_DECISION.md`
