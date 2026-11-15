# PLAYER RELATIVE PERFORMANCE V4 — Baseline & Contrast Estimator

## 1. Context-Adjusted Normal Performance Baseline (Phase C)
V4 computes **both** unadjusted normal baselines (`unadj_norm_mean` for `p < 0.75`, `unadj_hi_mean` for `p >= 0.75`) and a **simultaneous sparse Ridge context-adjusted model**:
$$y_{ijm} = \alpha_{\text{state}(t)} + u_{\text{match}(m)} + \theta_i^{\text{norm}} + \psi_{\text{opp}(j)} + r_{ijm}$$
- **`alpha_state(t)`**: `(innings, phase, match_format, season, pressure_decile)` fixed effects with minimal L2 (`0.01`), ensuring global scoring suppression/inflation across pressure levels is removed cleanly without specialist selection attenuation bias.
- **`u_match`, `theta_i^norm`, `psi_opp`**: Match par, player usual skill, and opponent quality Ridge effects (`lambda_m=35, lambda_p=30, lambda_opp=35`).

## 2. Common-Support Within-Player Contrast `Delta_i` & Empirical-Bayes (Phase D)
For each player $i$ within common-support `match_format` strata (containing $\ge 1$ high-pressure and $\ge 1$ low-pressure delivery), we estimate the Frisch-Waugh-Lovell (FWL) within-stratum pressure slope scaled over the `0.75` pressure contrast span (`Delta_i`):
- **Variance Estimation**: Guarded match-clustered sandwich standard error `se_delta = max(cluster_se * sqrt(M / (M - 1)), naive_se)` **plus 2,000-iteration match-clustered bootstrap** (`boot_se`, `boot_ci_low`, `boot_lcb95`, `boot_ci_high`).
- **Derived Empirical-Bayes Heterogeneity (Zero Hardcoded K)**:
  - **Batters Primary (`batter_runs` per 100b)**: `n_pool=176`, `mu0=-0.10`, `Q=178.0 (df=175)`, `I2=1.7%`, `tau=2.03`, implied `K_eff=68.2`.
  - **Batters Secondary (`is_striker_out` avoidance per 100b)**: `mu0=+0.05`, `Q=195.4 (df=175)`, `I2=10.5%`, `tau=0.67`.
  - **Bowlers Primary (`BATTER_RUNS_CONCEDED_PROXY` saved per 100b)**: `n_pool=216`, `mu0=-0.75`, `Q=218.0 (df=215)`, `I2=1.4%`, `tau=1.80`, implied `K_eff=95.6`.
  - **Bowlers Secondaries**: Dot/control % (`tau=0.84`, `Q=223.7/215`) and Wicket % (`tau=0.00`, `Q=213.2/215`).
- **Key Scientific Finding**: Between-player heterogeneity (`tau`) in the pure within-player *interaction slope* `Delta_i` is modest (`I2 < 10%` for runs), meaning empirical Bayes strongly shrinks extreme low-sample spikes toward `mu0` while preserving precision-weighted positive contrast (`lcb95_delta = eb_delta - 1.96 * post_sd`).
- **Dual Requirement**: Top-10 eligibility requires **BOTH** `raw_fwl_delta > 0` (positive pressure maintenance/improvement vs own normal baseline) **AND** `eb_hi_perf > 0` (above-average context-adjusted execution under pressure, plus non-collapsed dismissal/control secondary checks).

## 3. Reliability & Coverage Separation (Phase E)
- **Coverage Gate**: `n_hi >= 100` balls, `n_lo >= 60` balls, `hi_matches >= 10`, `lo_matches >= 10`, `cs_matches >= 10`, `total_matches >= 15`.
- **Batter Pool**: `824` total -> `84` coverage eligible -> `44` passed dual gate (`RELIABLE=0`, `PROVISIONAL=44`).
- **Bowler Pool**: `596` total -> `106` coverage eligible -> `45` passed dual gate (`RELIABLE=0`, `PROVISIONAL=45`).
- Because `tau` of pure `Delta_i` is modest relative to T20 match sampling variance (`eb_weight < 0.30` and `lcb95_delta <= 0`), **zero players meet strict `RELIABLE` significance on `Delta_i` alone** — we preserve strict thresholds (`0 RELIABLE`) rather than weakening them to manufacture certainty.
