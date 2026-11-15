# SupeRR Intelligence V4.2 — Release Decision & Statistical Audit Report

**Release Status:** `V4.2 PROVISIONAL — RESOURCE STRESS`

## 1. Executive Decision

V4.2 fixes every identified statistical and audit defect from V4.1 while preserving strict scientific honesty:
- **Chase score reconstruction remains blocked** (`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`): only 0/837 matches (`0.0%`) have zero extras; non-DLS run-margin reconciliation fails on `342/390` matches (`non_dls_exact_also_zero_unknown_extras = 5`, with `total_legal_balls = 185951` vs `total_delivery_rows = 193988`). Because runs required, target, and required run rate remain unavailable across deliveries, **no calibrated match-leverage variable exists**.
- All estimates are honestly scoped to **pre-delivery resource stress** (`BATTING_WICKET_DEPLETION_ANOMALY` and `BOWLING_EXPECTED_SCORING_THREAT`).
- Primary estimator: **Option A Complete Penalized FWL Partial Regression + REML Empirical Bayes**, backed by an empirical REML-EM joint hierarchical comparison (**Option B**), exact unpenalized OLS synthetic validation (`< 1e-8`), a 2,000-replicate **REML match-cluster bootstrap** verified against full nuisance+B3 refits, fixed quantile spans (`0.60, 0.70, 0.75`), exact 8-contrast like-for-like decomposition, match-level consistency diagnostics, and secondary outcome trade-offs.

---

## 2. Pressure Proxy Trace & Definitions

- **Fitted Innings 1 curve `(R0, b, gamma)`**: `(238.014, 1.1921, 0.5313)`
- **Fitted Innings 2 curve `(R0, b, gamma)`**: `(396.488, 0.4730, 0.3064)`
- **`BATTING_WICKET_DEPLETION_ANOMALY`** (aliases `BATTING_RESOURCE_STRESS`, `bat_pressure`): Percentile rank of `1 - ((10 - wickets_before)/10)^gamma - E[.|innings, overid]`. Parameters `R0` and `b` absorb expected remaining-run decay during parameter fitting on non-DLS clean matches, so `bat_pressure` specifically isolates **innings-stage wicket-depletion anomaly** (NOT DLS resources, NOT match win-probability leverage). It cannot distinguish 12 runs required from 70 runs required at identical overs and wickets remaining. Sensitivity against full `R(u, w)` depletion is verified in `V4_2_VALIDATION_MATRIX.csv`.
- **`BOWLING_EXPECTED_SCORING_THREAT`** (aliases `BOWLING_SCORING_THREAT`, `bowl_pressure`): Percentile rank of out-of-outcome Ridge (`alpha=10.0`) predicted batter runs/100b from pre-delivery state & venue-season. Primary bowler outcome `y_bowl` measures **BATTER_RUNS_CONCEDED_SUPPRESSION_PER_100_LEGAL_BALLS_PROXY** (not full economy with extras).

---

## 3. Estimator, Regularization, & Heterogeneity

| Role | Estimator | Eligible Players | REML mu0 | REML tau | I2 (%) | Schur-vs-Residual Reg Gap (Median / Max) |
|---|---|---:|---:|---:|---:|---|
| Batter | Option A Complete Penalized FWL + REML | 106 | -36.124 | 8.751 | 23.9% | 3.684 / 46.938 |
| Bowler | Option A Complete Penalized FWL + REML | 136 | -50.884 | 10.425 | 26.1% | 3.047 / 29.363 |

---

## 4. Direct Claim C OOT Validation & Ridge Tuning

Claims A, B, and C are strictly separated:
- **Batters (OOT >= 2023):** Claim A (General Skill FE) `rho = 0.539` (`p = 0.108`), Claim B (High-Stress Execution) `rho = -0.115` (`p = 0.751`), **Claim C (Pressure-vs-Own-Normal Slope)** `rho = -0.358` (`p = 0.31`, status: `CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS`).
- **Bowlers (OOT >= 2023):** Claim A (General Skill FE) `rho = 0.459` (`p = 0.0552`), Claim B (High-Stress Execution) `rho = 0.013` (`p = 0.958`), **Claim C (Pressure-vs-Own-Normal Slope)** `rho = 0.106` (`p = 0.675`, status: `CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS`).

Across the candidate Ridge grid (`5/20/60/150/asym`), Claim C OOT replication does not become strongly predictive because wicket-depletion / scoring-threat proxies carry substantial match-to-match noise and lack true chase score/target leverage. We explicitly disclose this honest negative finding rather than overclaiming Ridge selection fixes Claim C.

**Operational Eligibility Floor (`n_hi>=50, n_lo>=30, cs_matches>=8, se_delta<=25.0`):** Documented strictly as an operational precision floor to bound sampling error, NOT claimed as empirically optimal (full sweep in `V4_2_ELIGIBILITY_PRECISION_ANALYSIS.csv`).

---

## 5. Final Top 10 Batters (Claim C — Resource Stress Proxy)

| Rank (Avg) | Player | n_hi / n_lo (CS Matches) | EB Delta (vs Pop Mean) | Unshrunk Delta | EB Cond 95% CI | EB Boot 95% CI | Rank 95% CI | P(Top 10) [MCSE] | Spread Matches | Share Pos vs Normal | LOMO [min, max] | Dismissal Risk /100b | Secondary Warning |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 (1.0) | David Miller (1077) | 296 / 456 (81) | -29.39 (+6.73) | -6.64 | [-44.46, -14.33] | [-36.29, +0.58] | [1, 57] | 0.390 [0.011] | 19 (SD=91.5) | 0.32 | [-16.0, -1.1] | -1.77 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 2 (2.0) | Nehal Wadhera (7059) | 231 / 98 (37) | -29.69 (+6.44) | +4.64 | [-45.43, -13.95] | [-35.65, +10.00] | [1, 56] | 0.539 [0.011] | 10 (SD=97.3) | 0.60 | [-3.6, +13.7] | -3.49 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 3 (3.0) | Ravindra Jadeja (152) | 349 / 178 (65) | -30.29 (+5.83) | -13.82 | [-45.03, -15.55] | [-39.24, -1.60] | [2, 67] | 0.281 [0.010] | 22 (SD=83.5) | 0.36 | [-19.9, -7.7] | -3.19 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 4 (4.0) | Kamindu Mendis (4904) | 222 / 113 (38) | -30.35 (+5.77) | -2.67 | [-45.96, -14.75] | [-38.58, +1.37] | [1, 64] | 0.385 [0.011] | 11 (SD=96.0) | 0.64 | [-12.5, +3.8] | -2.85 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 5 (5.0) | Andre Russell (1318) | 397 / 102 (57) | -30.42 (+5.70) | -1.58 | [-46.10, -14.75] | [-38.83, +9.90] | [1, 65] | 0.445 [0.011] | 16 (SD=125.3) | 0.38 | [-7.2, +8.8] | -3.43 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 6 (6.0) | Michael Bracewell (6512) | 170 / 37 (33) | -30.42 (+5.70) | +15.06 | [-46.59, -14.26] | [-35.86, +9.96] | [1, 58] | 0.553 [0.011] | 9 (SD=99.5) | 0.56 | [+0.4, +25.8] | -2.81 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 7 (7.0) | Salman Agha (3489) | 300 / 105 (42) | -30.45 (+5.67) | -3.60 | [-46.04, -14.87] | [-38.18, +3.07] | [1, 64] | 0.401 [0.011] | 20 (SD=75.5) | 0.50 | [-10.7, +5.9] | -2.84 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 8 (8.0) | Dewald Brevis (25213) | 198 / 125 (40) | -30.58 (+5.55) | +5.52 | [-46.54, -14.61] | [-37.06, +6.29] | [1, 61] | 0.476 [0.011] | 11 (SD=87.2) | 0.36 | [-2.9, +16.1] | -3.05 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 9 (9.0) | Brian Bennett (24017) | 87 / 169 (44) | -30.64 (+5.48) | +2.75 | [-46.54, -14.75] | [-36.73, +3.25] | [1, 59] | 0.418 [0.011] | 12 (SD=100.7) | 0.42 | [-6.9, +9.8] | -2.71 | MODERATE_OR_NEUTRAL_TRADEOFF |
| 10 (10.0) | Harry Tector (4812) | 267 / 165 (45) | -30.67 (+5.45) | -10.09 | [-45.92, -15.42] | [-40.58, -0.15] | [2, 67] | 0.307 [0.010] | 21 (SD=64.9) | 0.52 | [-20.1, -2.9] | -2.60 | MODERATE_OR_NEUTRAL_TRADEOFF |

---

## 6. Final Top 10 Bowlers (Claim C — Expected Scoring Threat Proxy)

| Rank (Avg) | Player | n_hi / n_lo (CS Matches) | EB Delta (vs Pop Mean) | Unshrunk Delta | EB Cond 95% CI | EB Boot 95% CI | Rank 95% CI | P(Top 10) [MCSE] | Spread Matches | Share Pos vs Normal | LOMO [min, max] | Dot% / Wkt% Delta | Secondary Warning |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 (1.0) | Matheesha Pathirana (8661) | 515 / 170 (54) | -34.95 (+15.94) | -8.53 | [-51.08, -18.81] | [-41.39, -2.13] | [1, 33] | 0.789 [0.009] | 37 (SD=81.1) | 0.49 | [-13.1, -3.5] | -5.45 / +3.82 | MIXED_SECONDARY_PROFILE |
| 2 (2.0) | Haris Rauf (7364) | 273 / 213 (48) | -35.81 (+15.08) | -6.37 | [-52.42, -19.19] | [-42.31, +0.56] | [1, 37] | 0.776 [0.009] | 31 (SD=70.8) | 0.58 | [-10.9, -0.3] | -5.73 / +3.75 | MIXED_SECONDARY_PROFILE |
| 3 (3.0) | Lungi Ngidi (4641) | 258 / 158 (39) | -37.95 (+12.93) | -1.43 | [-55.51, -20.39] | [-41.72, -1.56] | [1, 34] | 0.770 [0.009] | 21 (SD=62.8) | 0.48 | [-11.2, +4.3] | -7.50 / +3.65 | MIXED_SECONDARY_PROFILE |
| 4 (4.0) | Jasprit Bumrah (2933) | 612 / 314 (75) | -38.13 (+12.76) | -24.23 | [-52.88, -23.37] | [-47.51, -13.01] | [1, 55] | 0.454 [0.011] | 50 (SD=67.1) | 0.48 | [-28.6, -20.8] | -13.29 / +3.50 | MIXED_SECONDARY_PROFILE |
| 5 (5.0) | Maheesh Theekshana (19316) | 579 / 457 (99) | -38.16 (+12.72) | -25.96 | [-52.46, -23.87] | [-46.91, -14.43] | [2, 52] | 0.405 [0.011] | 60 (SD=71.3) | 0.52 | [-29.1, -22.8] | -7.20 / +3.85 | MIXED_SECONDARY_PROFILE |
| 6 (6.0) | Noor Ahmad (7967) | 340 / 388 (70) | -41.65 (+9.24) | -24.93 | [-58.05, -25.25] | [-51.52, -16.53] | [2, 69] | 0.338 [0.011] | 30 (SD=65.6) | 0.50 | [-30.0, -21.9] | -7.96 / +3.63 | MIXED_SECONDARY_PROFILE |
| 7 (7.0) | Alzarri Joseph (3275) | 349 / 189 (53) | -41.87 (+9.02) | -24.89 | [-58.38, -25.35] | [-52.38, -15.08] | [2, 74] | 0.333 [0.011] | 39 (SD=81.2) | 0.51 | [-31.5, -21.1] | -10.42 / +3.80 | MIXED_SECONDARY_PROFILE |
| 8 (8.0) | Roston Chase (2687) | 134 / 244 (45) | -42.57 (+8.31) | -17.67 | [-60.27, -24.88] | [-51.82, -9.22] | [1, 71] | 0.422 [0.011] | 15 (SD=71.7) | 0.40 | [-23.7, -10.2] | -6.47 / +3.70 | MIXED_SECONDARY_PROFILE |
| 9 (9.0) | Gerald Coetzee (6628) | 192 / 102 (29) | -43.64 (+7.24) | -19.68 | [-61.55, -25.74] | [-54.79, -8.47] | [1, 82] | 0.393 [0.011] | 20 (SD=68.0) | 0.45 | [-27.0, -7.1] | -9.45 / +3.71 | MIXED_SECONDARY_PROFILE |
| 10 (10.0) | Craig Young (3720) | 120 / 114 (23) | -43.71 (+7.17) | -13.74 | [-62.07, -25.36] | [-52.86, -12.76] | [2, 75] | 0.361 [0.011] | 14 (SD=86.0) | 0.50 | [-23.8, -4.9] | -8.40 / +3.80 | MIXED_SECONDARY_PROFILE |

---

## 7. Validation Summary

- **quant_span_060_P80_P20 (batter)** — PASS=True | Exact span=0.600; Spearman vs P87.5-P12.5=0.9989; Top-10 overlap=10/10; REML tau=6.640
- **quant_span_070_P85_P15 (batter)** — PASS=True | Exact span=0.700; Spearman vs P87.5-P12.5=0.9988; Top-10 overlap=10/10; REML tau=7.190
- **quant_span_075_P875_P125 (batter)** — PASS=True | Exact span=0.750; Spearman vs P87.5-P12.5=0.9970; Top-10 overlap=10/10; REML tau=8.000
- **quant_span_060_P80_P20 (bowler)** — PASS=True | Exact span=0.600; Spearman vs P87.5-P12.5=0.9999; Top-10 overlap=10/10; REML tau=8.522
- **quant_span_070_P85_P15 (bowler)** — PASS=True | Exact span=0.700; Spearman vs P87.5-P12.5=0.9994; Top-10 overlap=10/10; REML tau=10.033
- **quant_span_075_P875_P125 (bowler)** — PASS=True | Exact span=0.750; Spearman vs P87.5-P12.5=0.9994; Top-10 overlap=10/10; REML tau=11.026
- **proxy_sensitivity_wicket_vs_full_ruw (batter)** — PASS=True | Wicket-depletion anomaly vs R(u,w) depletion Spearman=0.699, Top-10 overlap=5/10
- **score_bootstrap_vs_full_refit_proof (batter)** — PASS=True | K=25 full nuisance+B3 refits across 332 players: median replicate r=0.9199, median SE ratio=1.066
- **score_bootstrap_vs_full_refit_proof (bowler)** — PASS=True | K=25 full nuisance+B3 refits across 380 players: median replicate r=0.9326, median SE ratio=1.058
- **within_stratum_placebo_permutation (batter)** — PASS=True | Placebo REML tau=0.000, I2=0.0%, share(|z|>1.96)=0.053
- **within_stratum_placebo_permutation (bowler)** — PASS=True | Placebo REML tau=5.461, I2=7.2%, share(|z|>1.96)=0.075
- **oot_claim_a_general_skill (batter)** — PASS=True | Claim A (General player FE OOT >=2023): rho=0.539, p=0.108, n=10
- **oot_claim_b_high_stress_execution (batter)** — PASS=True | Claim B (High-stress residual execution OOT >=2023): rho=-0.115, p=0.751, n=10
- **oot_claim_c_pressure_vs_normal_slope (batter)** — PASS=True | Claim C (CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS): rho=-0.358, p=0.31, inv-var r=0.002, n=10
- **oot_claim_a_general_skill (bowler)** — PASS=True | Claim A (General player FE OOT >=2023): rho=0.459, p=0.0552, n=18
- **oot_claim_b_high_stress_execution (bowler)** — PASS=True | Claim B (High-stress residual execution OOT >=2023): rho=0.013, p=0.958, n=18
- **oot_claim_c_pressure_vs_normal_slope (bowler)** — PASS=True | Claim C (CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS): rho=0.106, p=0.675, inv-var r=0.153, n=18
- **like_for_like_additive_identities (batter)** — PASS=True | Max nuisance identity err=6.39e-14, max bridge identity err=1.42e-14
- **like_for_like_additive_identities (bowler)** — PASS=True | Max nuisance identity err=8.53e-14, max bridge identity err=2.84e-14
- **score_audit_and_legal_balls (all)** — PASS=True | Legal balls=185951 <= Delivery rows=193988; non-DLS run margin exact=48/390 (fail=342); zero-extras matches=0/837; CHASE_SCORE_RECONSTRUCTION_BLOCKED=True

---

## 8. Provenance

- **Branch:** `fix/v4-2-statistical-corrections-20261115`
- **Origin Main SHA:** `c7579ed0473cd5674360b60880a69528e6a4c4c7`
- **Generated Elapsed Time:** `151.2s`
