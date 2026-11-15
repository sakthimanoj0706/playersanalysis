# V4.1 STATISTICAL CORRECTIONS — SupeRR Intelligence V4.1

## 1. Pressure Feature Terminology & Scope Documentation (Section 2)
Neither feature is a calibrated score-based win-probability Match Leverage Index ($C_t = |\partial WP / \partial \text{Run}|$). Both are strictly pre-delivery observable resource/threat proxies:

| V4 Name | Canonical V4.1 Name | What It Measures | Information Used | Information Missing | What It Cannot Distinguish | Applies To |
| --- | --- | --- | --- | --- | --- | --- |
| `bat_pressure` | `BATTING_RESOURCE_STRESS` | Excess wicket depletion relative to stage expectation under fitted monotone curve $R(u,w)=R_0(1-e^{-bu})((10-w)/10)^\gamma$ (`Inn1`: `[238.014, 1.192, 0.531]`, `Inn2`: `[396.488, 0.473, 0.306]`), empirical training CDF quantile in `[0,1]`. | `innings`, `overid`, `balls_rem_before` (DLS balls), `wkts_before`, `is_dl_method` (fit on non-DLS). | Team score, target, runs required, required run rate (`RRR`), non-striker identity, pitch par. | **Cannot distinguish 12 runs required off 6 balls from 70 runs required off 6 balls when balls remaining and wickets remaining are identical.** | Regular innings `1, 2` (`is_ball_faced == 1`), batter ranking & decomposition. |
| `bowl_pressure` | `BOWLING_SCORING_THREAT` | Pre-delivery expected batter scoring rate $\mathbb{E}[\text{batter\_runs} \mid \text{state}]$ from Ridge regression (`alpha=10.0`), empirical training CDF quantile in `[0,1]`. | `innings`, `phase`, `is_t20i`, `balls_rem_before`, `wkts_rem_before` and interactions. | Match target, chase equation, required run rate, batter-specific crease danger, exact extras. | **Cannot distinguish a dead-rubber death over (70 needed off 6) from a tight defense (12 needed off 6)** for identical phase/wickets. | Regular innings `1, 2` (`is_legal_ball == 1`), bowler ranking & decomposition. |

---

## 2. Score-Data Coverage & Enriched Match Audit (Section 3)
Audit output: `data/outputs/v4_1/V4_1_SCORE_ENRICHMENT_AUDIT.csv` (`837` matches, `1652` innings, keyed strictly by `(match_id, innings)`):
- **External Scorecard Enrichment Availability:** `0` verified external scorecards keyed by Rajasthan Royals' stable `match_id` exist in the supplied data pack (`revised_target` populated on `23 / 853` matches).
- **Exact Margin & Extras Audit:**
  - Matches with zero extras deliveries in both innings: **`0 / 837` (`0.00%`)**.
  - Matches with zero unknown-amount extras (`legbyes`, `byes`, `other`, `Penalty`): **`25 / 837`**.
  - Non-DLS `"by X runs"` check (`390` matches): **`342` fail**, `48` match stated margin, of which only **`5`** also lack `legbyes/byes/other/Penalty` (`43` matched purely via accidental cancellation of missing Innings 1 vs Innings 2 extras).
- **Conclusion:** Multi-run wides/oversteps and extras amounts are not inferred from categorical `extras1_runs` or undocumented `extras_2_runs` (`35` rows). `CHASE_SCORE_RECONSTRUCTION_BLOCKED = True` stands and resource-stress proxies are retained.

---

## 3. Canonical Span Correction & Elimination of Cutoffs / Dual-Gate Traps (Sections 4, 6, 7)
1. **FWL Span Correction (`0.625` $\to$ `0.75`):** V4 accidentally computed `span = hi_thr - 0.5*lo_thr = 0.625` instead of canonical `0.75` (`0.875 - 0.125`; empirical median `mean_p_hi - mean_p_lo = 0.73–0.74`). V4.1 restores `span = 0.75`.
2. **Removal of Arbitrary 6-Cutoff Cliff:** V4's `n_hi>=100, n_lo>=60, hi_m>=10, lo_m>=10, cs_m>=10, tot_m>=15` excluded precision-qualified batters such as **Virat Kohli** (`n_hi=79, n_lo=1055, cs_matches=92`) and **Brian Bennett** (`n_hi=87, n_lo=169, cs_matches=44`). V4.1 uses an **uncertainty/precision floor** (`se_delta <= 25.0`, plus minimal FWL operational stability `n_hi>=50, n_lo>=30, cs_matches>=8`), analyzed continuously across `V4_1_ELIGIBILITY_PRECISION_ANALYSIS.csv`.
3. **Removal of Absolute Level Gate (`eb_hi_perf > 0`) & Pure Relative Ranking Target:** V4 excluded `3` coverage-eligible bowlers who improved relative to their own normal baseline (`raw_fwl_delta > 0`: **Andre Russell** `+8.60`, **Shahbaz Ahmed** `+19.21`, **Romario Shepherd** `+1.09`) solely because their high-pressure execution level fell below population par. V4.1 removes the absolute gate and orders candidates strictly by **posterior mean relative contrast `empirical_bayes_delta`** (`mu0` + shrinkage `w_i * (Delta_i - mu0)`), rather than `lcb95_delta` (which penalized moderate-sample improvers twice and placed negative-EB bowlers in V4's Top 10).
4. **Why `K_eff` Is Not Universal:** Comparing DL vs REML on identical FWL (`span=0.75`, Ridge `alpha=60`) contrasts shifts implied `K_eff = median(se^2) / tau^2` from `18.1` (DL) to `63.9` (REML, $\tau=2.28$) for batters, and from `24.5` (DL) to `27.3` (REML, $\tau=3.60$) for bowlers (compared with V4 legacy `DL span=0.625 Ridge=35`: `22.7` bat / `26.5` bowl). `K_eff` is strictly model-, metric-, and sample-dependent.
5. **Correlated Complete-Ranking Match Bootstrap (`B = 1000`):** Eligible players share an average of `4.6` matches (batters, mean $|r|=0.0173$) and `2.72` matches (bowlers, mean $|r|=0.0171$). Resampling `match_id` clusters globally yields genuine **Bootstrap Rank Intervals** and **Top-10 Membership Probabilities**.

---

## 4. Raw-vs-Adjusted Discrepancy Bridge & Composition Decomposition (Section 5)
Why do shortlisted batters and bowlers exhibit **negative `raw_observed_delta`** yet **positive `context_adjusted_delta`**?
- **Batters (`BATTING_RESOURCE_STRESS >= 0.75`):** High batting stress captures deliveries where early/middle wickets fell or tail/rebuilding partnerships operate (`alpha_state` and wicket-depletion state par is `-25` to `-40` SR lower than low-stress balls). Subtracting exact state par (`delta_shift_pressure_wkt_state` + `delta_shift_phase_fmt_season`) + `u_match` + `psi_opp` isolates performance *above* what average batters score in the same depleted state.
- **Bowlers (`BOWLING_SCORING_THREAT >= 0.75`):** High bowling scoring threat selects death overs (overs `16–20`), where league-wide scoring surges `+40` to `+55` runs/100b higher than normal overs (`raw_observed_delta < 0`). Removing `delta_shift_phase_fmt_season` + `delta_shift_pressure_wkt_state` isolates whether the bowler concedes fewer batter runs than death-over par relative to their normal-over par.

### Top 10 Batters — Mandatory 10-Column Breakdown & Exact Sequential Decomposition (`BATTER_RUNS_PER_100_BALLS`)
| player_name | raw_high_performance | raw_normal_performance | raw_observed_delta | context_adjusted_high_performance | context_adjusted_normal_performance | context_adjusted_delta | empirical_bayes_delta | lower_confidence_bound | upper_confidence_bound | probability_positive_effect |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Brian Bennett | 139.08 | 127.20 | 11.88 | 38.98 | 4.40 | 45.90 | 1.08 | -3.37 | 5.53 | 0.68 |
| Virat Kohli | 126.58 | 145.86 | -19.27 | 6.32 | 8.61 | 13.28 | 1.01 | -3.38 | 5.40 | 0.67 |
| Salman Agha | 105.67 | 135.43 | -29.76 | 4.39 | 2.95 | 31.73 | 1.01 | -3.43 | 5.45 | 0.67 |
| David Miller | 137.84 | 152.74 | -14.91 | 22.08 | 10.38 | 18.05 | 0.99 | -3.43 | 5.41 | 0.67 |
| Nehal Wadhera | 131.17 | 146.20 | -15.03 | 31.65 | 14.96 | 32.35 | 0.96 | -3.49 | 5.41 | 0.66 |
| Towhid Hridoy | 122.76 | 126.97 | -4.20 | 15.45 | -3.75 | 15.46 | 0.93 | -3.49 | 5.34 | 0.66 |
| Nicholas Pooran | 134.88 | 162.18 | -27.30 | 29.21 | 29.34 | 14.36 | 0.92 | -3.50 | 5.33 | 0.66 |
| Ibrahim Zadran | 111.37 | 118.47 | -7.10 | -0.87 | -14.53 | 13.59 | 0.91 | -3.50 | 5.32 | 0.66 |
| Kamindu Mendis | 115.32 | 138.01 | -22.69 | 5.64 | 6.23 | 24.03 | 0.89 | -3.55 | 5.33 | 0.65 |
| Faf du Plessis | 139.05 | 144.49 | -5.44 | 26.21 | 11.15 | 15.50 | 0.89 | -3.53 | 5.31 | 0.65 |

#### Top 10 Batters — Exact Sequential Composition Shifts (`raw_observed_delta + sum(shifts) == context_adjusted_delta`)
| player_name | raw_observed_delta | delta_shift_phase_fmt_season | delta_shift_pressure_wkt_state | delta_shift_match_par | delta_shift_opponent_quality | delta_shift_continuous_fwl_vs_discrete | total_context_adjustment_shift | context_adjusted_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Brian Bennett | 11.88 | 0.38 | 22.20 | 0.71 | -0.59 | 11.32 | 34.02 | 45.90 |
| Virat Kohli | -19.27 | -0.19 | 23.09 | -5.51 | -0.40 | 15.56 | 32.55 | 13.28 |
| Salman Agha | -29.76 | 5.37 | 20.40 | 5.69 | -0.26 | 30.29 | 61.49 | 31.73 |
| David Miller | -14.91 | 15.41 | 20.69 | -7.13 | -2.36 | 6.35 | 32.95 | 18.05 |
| Nehal Wadhera | -15.03 | 5.75 | 15.85 | 10.67 | -0.54 | 15.66 | 47.39 | 32.35 |
| Towhid Hridoy | -4.20 | -2.33 | 24.12 | 2.73 | -1.12 | -3.74 | 19.66 | 15.46 |
| Nicholas Pooran | -27.30 | 6.19 | 21.21 | -1.19 | 0.96 | 14.49 | 41.66 | 14.36 |
| Ibrahim Zadran | -7.10 | -0.81 | 27.13 | -2.94 | -2.63 | -0.06 | 20.69 | 13.59 |
| Kamindu Mendis | -22.69 | 2.93 | 15.84 | 4.31 | -0.98 | 24.62 | 46.72 | 24.03 |
| Faf du Plessis | -5.44 | 2.69 | 25.95 | -6.56 | -1.58 | 0.45 | 20.95 | 15.50 |

### Top 10 Bowlers — Mandatory 10-Column Breakdown (`BATTER_RUNS_CONCEDED_PROXY_SAVED_PER_100_BALLS`)
| player_name | raw_high_performance | raw_normal_performance | raw_observed_delta | context_adjusted_high_performance | context_adjusted_normal_performance | context_adjusted_delta | empirical_bayes_delta | lower_confidence_bound | upper_confidence_bound | probability_positive_effect |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Maheesh Theekshana | -139.72 | -121.48 | -18.24 | 31.25 | 14.76 | 21.96 | 1.64 | -5.02 | 8.30 | 0.69 |
| Haris Rauf | -143.22 | -138.20 | -5.03 | 29.41 | -1.38 | 36.12 | 1.43 | -5.41 | 8.26 | 0.66 |
| Jasprit Bumrah | -126.80 | -107.11 | -19.69 | 58.98 | 36.87 | 23.37 | 1.34 | -5.39 | 8.07 | 0.65 |
| Matheesha Pathirana | -137.86 | -122.90 | -14.96 | 43.06 | 17.93 | 29.04 | 0.94 | -5.90 | 7.78 | 0.61 |
| Lungi Ngidi | -152.33 | -139.30 | -13.03 | 35.75 | 9.69 | 34.46 | 0.67 | -6.24 | 7.57 | 0.57 |
| Alzarri Joseph | -158.74 | -151.74 | -7.00 | 20.01 | -9.99 | 23.53 | 0.65 | -6.19 | 7.49 | 0.57 |
| Xavier Bartlett | -187.25 | -138.57 | -48.67 | 1.42 | 3.80 | 46.61 | 0.56 | -6.39 | 7.51 | 0.56 |
| Gerald Coetzee | -158.33 | -142.29 | -16.04 | 28.13 | 1.29 | 38.75 | 0.54 | -6.39 | 7.47 | 0.56 |
| Sam Curran | -167.51 | -147.05 | -20.47 | 14.68 | -1.71 | 19.82 | 0.54 | -6.28 | 7.35 | 0.56 |
| Sunil Narine | -135.68 | -104.38 | -31.30 | 47.92 | 38.50 | 13.61 | 0.43 | -6.31 | 7.17 | 0.55 |

#### Top 10 Bowlers — Exact Sequential Composition Shifts (`raw_observed_delta + sum(shifts) == context_adjusted_delta`)
| player_name | raw_observed_delta | delta_shift_phase_fmt_season | delta_shift_pressure_wkt_state | delta_shift_match_par | delta_shift_opponent_quality | delta_shift_continuous_fwl_vs_discrete | total_context_adjustment_shift | context_adjusted_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Maheesh Theekshana | -18.24 | 10.73 | 20.61 | -0.70 | 4.09 | 5.47 | 40.20 | 21.96 |
| Haris Rauf | -5.03 | 20.47 | 12.06 | 1.11 | 2.18 | 5.33 | 41.15 | 36.12 |
| Jasprit Bumrah | -19.69 | 13.63 | 24.76 | -0.12 | 3.52 | 1.26 | 43.05 | 23.37 |
| Matheesha Pathirana | -14.96 | 17.56 | 19.06 | -0.21 | 3.69 | 3.91 | 44.00 | 29.04 |
| Lungi Ngidi | -13.03 | 20.96 | 18.40 | -1.65 | 1.39 | 8.40 | 47.49 | 34.46 |
| Alzarri Joseph | -7.00 | 21.15 | 13.68 | 2.53 | -0.36 | -6.47 | 30.53 | 23.53 |
| Xavier Bartlett | -48.67 | 22.47 | 24.06 | 0.31 | -0.55 | 49.00 | 95.29 | 46.61 |
| Gerald Coetzee | -16.04 | 20.78 | 20.19 | 4.34 | -2.43 | 11.91 | 54.79 | 38.75 |
| Sam Curran | -20.47 | 18.28 | 19.49 | -1.57 | 0.66 | 3.43 | 40.28 | 19.82 |
| Sunil Narine | -31.30 | 6.57 | 28.64 | 1.67 | 3.83 | 4.20 | 44.90 | 13.61 |

---

## 5. Model Comparison & Ridge Regularization Sensitivity (`V4_1_MODEL_COMPARISON.csv`)
| role | model_variant | eb_method | contrast_span | ridge_lambdas | eligible_count | reliable_count | tau | oot_2025_2026_rmse | top10_overlap_vs_v41 | spearman_rho_vs_v41 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| batter | V4_1_Base_TwoStage_FWL_REML_60 | REML | 0.750 | 60/60/60 | 110 | 0 | 2.284 | 178.122 | 10 | 1.000 |
| batter | V4_Legacy_TwoStage_DL_35_span0625 | DL | 0.625 | 35/30/35 | 44 | 0 | 3.423 | 178.170 | 7 | 0.967 |
| batter | TwoStage_FWL_DL_60_span075 | DL | 0.750 | 60/60/60 | 110 | 0 | 4.287 | 178.122 | 9 | 1.000 |
| batter | TwoStage_REML_With_AbsGate_ebHi>0 | REML | 0.750 | 60/60/60 | 62 | 0 | 2.284 | 178.122 | 10 | 1.000 |
| batter | TwoStage_REML_OrderBy_LCB95 | REML | 0.750 | 60/60/60 | 110 | 0 | 2.284 | 178.122 | 9 | 0.997 |
| batter | Ridge_Light_15_REML | REML | 0.750 | 15/15/15 | 110 | 0 | 1.255 | 178.281 | 9 | 0.992 |
| batter | Ridge_Default_35_REML | REML | 0.750 | 35/30/35 | 110 | 0 | 1.774 | 178.170 | 9 | 0.998 |
| batter | Ridge_Heavy_120_REML | REML | 0.750 | 120/120/120 | 110 | 0 | 3.043 | 178.100 | 9 | 0.997 |
| batter | Ridge_VeryHeavy_250_REML | REML | 0.750 | 250/250/250 | 110 | 0 | 3.608 | 178.113 | 8 | 0.985 |
| batter | Joint_Hierarchical_Slope_lam3500 | JOINT_RIDGE | 0.750 | 60/60/60 | 110 | 0 | 0.319 | 178.122 | 6 | 0.975 |
| batter | Joint_Hierarchical_Slope_lam500 | JOINT_RIDGE | 0.750 | 60/60/60 | 110 | 0 | 1.942 | 178.122 | 6 | 0.975 |
| bowler | V4_1_Base_TwoStage_FWL_REML_60 | REML | 0.750 | 60/60/60 | 135 | 0 | 3.599 | 178.136 | 10 | 1.000 |
| bowler | V4_Legacy_TwoStage_DL_35_span0625 | DL | 0.625 | 35/30/35 | 45 | 0 | 3.276 | 178.191 | 10 | 0.969 |
| bowler | TwoStage_FWL_DL_60_span075 | DL | 0.750 | 60/60/60 | 135 | 0 | 3.795 | 178.136 | 10 | 1.000 |
| bowler | TwoStage_REML_With_AbsGate_ebHi>0 | REML | 0.750 | 60/60/60 | 60 | 0 | 3.599 | 178.136 | 10 | 1.000 |
| bowler | TwoStage_REML_OrderBy_LCB95 | REML | 0.750 | 60/60/60 | 135 | 0 | 3.599 | 178.136 | 10 | 0.988 |
| bowler | Ridge_Light_15_REML | REML | 0.750 | 15/15/15 | 137 | 0 | 3.746 | 178.292 | 10 | 0.997 |
| bowler | Ridge_Default_35_REML | REML | 0.750 | 35/30/35 | 135 | 0 | 3.647 | 178.191 | 10 | 0.999 |
| bowler | Ridge_Heavy_120_REML | REML | 0.750 | 120/120/120 | 135 | 0 | 3.699 | 178.114 | 10 | 0.998 |
| bowler | Ridge_VeryHeavy_250_REML | REML | 0.750 | 250/250/250 | 132 | 0 | 4.107 | 178.130 | 10 | 0.991 |
| bowler | Joint_Hierarchical_Slope_lam3500 | JOINT_RIDGE | 0.750 | 60/60/60 | 135 | 0 | 0.344 | 178.136 | 7 | 0.961 |
| bowler | Joint_Hierarchical_Slope_lam500 | JOINT_RIDGE | 0.750 | 60/60/60 | 135 | 0 | 2.101 | 178.136 | 7 | 0.963 |
