# SupeRR Intelligence V4.2 — Methodology Report

**Release Status:** **`V4.2 PROVISIONAL — RESOURCE STRESS`**  
**Target Branch:** `fix/v4-2-statistical-corrections-20261115`  
**Authoritative Shortlist:** [V4_2_FINAL_SHORTLIST.csv](data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv)  
**Individual Player Justifications:** [V4_2_PLAYER_JUSTIFICATIONS.md](data/reports/v4_2/V4_2_PLAYER_JUSTIFICATIONS.md)  
**Release Audit Memo:** [V4_2_RELEASE_DECISION.md](data/reports/v4_2/V4_2_RELEASE_DECISION.md)  
**Machine Provenance:** [V4_2_SOURCE_OF_TRUTH.json](data/outputs/v4_2/V4_2_SOURCE_OF_TRUTH.json)

---

## 1. Official Problem Statement

> *"Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels."*

Mandatory deliverables:
1. A separate ordered Top 10 list of batters who perform most consistently under pressure.
2. A separate ordered Top 10 list of bowlers who perform most consistently under pressure.
3. A methodology report explaining how pressure is defined, how players are rated, how pressure performance is compared with normal performance, and why the selected players belong in the Top 10.

Rajasthan Royals (RR) squad suitability/scouting in [dashboard/app.py](dashboard/app.py) is a **secondary application module** and never overrides or filters the universal Top 10 deliverables.

---

## 2. Dataset Scope & Reconciliation

- **Scoped Matches:** `837` IPL + T20I matches (2022–2026) containing ball-by-ball records (`1,652` regular innings, `193,988` regular delivery rows, `185,951` validated legal balls excluding wides and no-ball `Overstep` deliveries).
- **Super Over Isolation & Identity Resolution:** Super Overs are isolated from regular-innings analysis. Player identities are strictly keyed by canonical `player_id` (protecting duplicate names).
- **Legal-Ball Accounting:** `V4_2_SCORE_ENRICHMENT_AUDIT.csv` verifies `total_legal_balls = 185,951 <= total_delivery_rows = 193,988` across every match-innings row.

---

## 3. Why Complete Match-Pressure Reconstruction Is Blocked

- In the raw delivery feed, `extras1_runs` encodes a categorical extras codebook (values `1–7`, e.g., wide/no-ball/bye/leg-bye indicators) rather than exact extra runs conceded, and multi-run extras in `extras_2_runs` cannot be safely inferred across all matches.
- **Audit Result (`V4_2_SCORE_ENRICHMENT_AUDIT.csv`):**
  - `matches_zero_all_extras = 0 / 837` (`0.0%` verified score coverage).
  - Non-DLS run-margin reconciliation fails on **`342 / 390`** matches (`48` exact matches, of which only `5` also have zero unknown extras and `43` match by accidental cancellation).
  - External scorecard matching by stable match ID yields `0` enriched matches.
- **Scientific Consequence (`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`):** Because exact innings totals, chase targets, runs required, and required run rates cannot be reconstructed across deliveries, **no calibrated match-leverage or win-probability variable exists**. All V4.2 estimates are honestly scoped to **pre-delivery resource stress**.

---

## 4. Exact Resource-Stress Proxy Definitions

Both proxies use strictly pre-delivery state (zero post-delivery target leakage) and are **not** calibrated match-leverage indices:

1. **`BATTING_WICKET_DEPLETION_ANOMALY`** *(aliases: `BATTING_RESOURCE_STRESS`, `bat_pressure`)*:
   - **Formula:** `F_emp((1 - ((10 - wickets_before)/10)^gamma) - E[1 - ((10 - wickets_before)/10)^gamma | innings, overid])`
   - **Fitted Curve Parameters (non-DLS clean train matches):**
     - Innings 1: `(R0 = 238.014, b = 1.1921, gamma = 0.5313)`
     - Innings 2: `(R0 = 396.488, b = 0.4730, gamma = 0.3064)`
   - **Parameter Trace:** `R0` and `b` absorb expected remaining-run decay during parameter fitting on `R(u, w) = R0*(1 - exp(-b*u))*((10-w)/10)^gamma`; `gamma` enters the wicket-depletion anomaly directly.
   - **Limitation:** Measures excess wickets lost relative to a typical innings at `(innings, overid)`. It **cannot distinguish needing 12 runs from needing 70 runs** when overs and wickets remaining are identical. Sensitivity against full `R(u, w)` depletion (`BAT_DEPLETION_FULL_RUW`) yields Spearman `0.699` and `5/10` Top-10 overlap (`V4_2_VALIDATION_MATRIX.csv`).
2. **`BOWLING_EXPECTED_SCORING_THREAT`** *(aliases: `BOWLING_SCORING_THREAT`, `bowl_pressure`)*:
   - **Formula:** `F_emp(Ridge(alpha=10.0) predicted expected batter runs per 100b from _bowl_design_matrix())`
   - **Design Matrix Terms (`src/v4/pressure_proxy.py`):** `pp`, `mid`, `death`, `inn2`, `fmt`, `wf`, `u`, `pp * wf`, `mid * wf`, `death * wf`, `death * (1 - wf)`, `inn2 * u`, `death * u` (where `pp/mid/death` are phase indicators, `inn2` is `innings == 2`, `fmt` is `is_t20i`, `wf = wkts_rem_before / 10`, and `u = balls_rem_before / 120`).
   - **Primary Bowler Outcome (`y_bowl`):** `BATTER_RUNS_CONCEDED_SUPPRESSION_PER_100_LEGAL_BALLS_PROXY` (`-100 * batter_runs / legal_ball`). It measures batter-credited run suppression, **not** full bowling economy with multi-run extras.
   - **Limitation:** Cannot distinguish defending a 10-run cushion in the final over from defending 35 runs.

---

## 5. Option A Complete Penalized FWL Model

To compare each player's performance under high resource stress against their **own usual performance level** after removing match/state/opponent confounders:

- **Full Nuisance Design:** $Z = [X_{\text{state}}, X_{\text{match}}, X_{\text{player}}, X_{\text{opp}}]$ (excluding the continuous pressure indicator from $X_{\text{state}}$ so continuous slope variation is preserved).
- **Common-Support Pressure Interaction:** $W$ interacts centered continuous pressure ($p - 0.5$) with player indicators on common-support rows (`cs_mask`, where players span both high and low stress).
- **Complete Penalized FWL Partial Regression (`src/v4_2/fwl_estimator.py`):** Residualizes **both** outcome $y$ ($\tilde{y} = y - Z\hat{\theta}_y$) **and** the full interaction matrix $W$ ($\tilde{W}$ via Schur-complement normal equations $G_{\text{schur}} = W^\top D_w W - B_W^\top \Theta_W$) against $Z$, guaranteeing exact equivalence to joint penalized regression.
  - Unpenalized synthetic OLS parity verified to `< 1e-8` (`tests/test_v4_2_methodology.py`).
  - Schur-complement vs residual-outcome regularization gap: Batter median `3.684` (max `46.938`); Bowler median `3.047` (max `29.363`).
- **Estimand Scale (`span = 0.75`):** Unshrunk FWL slope `delta_unshrunk = span * beta_fwl`, representing the context-adjusted change from the 12.5th percentile (low stress) to the 87.5th percentile (high stress) of the proxy.
- **Cluster-Robust Variance:** Player-specific match-cluster sandwich SE (`se_delta`) with $M_i/(M_i - 1)$ DOF and a `naive_se` Fisher floor.
- **Benchmark Agreement (Option B Joint REML-EM):** Spearman `r = 0.9919` (`9/10` Top-10 overlap) for batters; `r = 0.9957` (`8/10` Top-10 overlap) for bowlers (`V4_2_MODEL_COMPARISON.csv`).

---

## 6. REML Empirical-Bayes Estimation

Over the well-identified REML estimation pool (`n_hi >= 30`, `n_lo >= 30`, `cs_matches >= 5`, `se_delta <= 30.0`), restricted maximum likelihood (`estimate_heterogeneity(..., method="reml")`) estimates pooled mean $\mu_0$ and true between-player heterogeneity $\tau^2$:
- **Batters:** $\mu_0 = -36.1238231044$ runs/100b, $\tau = 8.751$, $I^2 = 23.9\%$.
- **Bowlers:** $\mu_0 = -50.8837912303$ proxy units/100b, $\tau = 10.425$, $I^2 = 26.1\%$.
- **Shrinkage:** $w_i = \tau^2 / (\tau^2 + \text{SE}_i^2)$ pulls noisy low-exposure estimates toward $\mu_0$:
  $$\text{EB }\Delta_i = w_i\,\hat{\Delta}_i + (1 - w_i)\,\mu_0$$

---

## 7. Match-Cluster Bootstrap & Tie-Aware Ranks

- **Resampling (`B = 2,000`):** Nuisance-orthogonalized match-cluster score bootstrap re-running REML (`mu0`, `tau2`) in **every** replicate (`run_v42_match_cluster_bootstrap`).
- **Full-Refit Proof:** Validated against $K = 25$ full nuisance + B3 refits across all players (`median replicate r = 0.9199`, SE ratio `1.066` for batters; `r = 0.9326`, SE ratio `1.058` for bowlers).
- **Tie-Aware Ranking:** Eligible players are ranked using `scipy.stats.rankdata(..., method="average")` (rounded to `1e-10`) with **fractional Top-10 membership** (`prob_top_10` and `mcse_prob_top_10`), never breaking ties by `player_id`. All five uncertainty metrics (`eb_cond_ci_*`, `eb_boot_ci_*`, `unshrunk_boot_ci_*`, `boot_rank_ci_*`, `prob_top_10` + `mcse_prob_top_10`) are exported.

---

## 8. Raw vs Adjusted Effects (Exact 8-Contrast Decomposition)

`V4_2_RAW_ADJUSTED_DECOMPOSITION.csv` decomposes each player's contrast across eight exact quantities separating context adjustment from discrete-vs-continuous estimand shift (`max nuisance identity err <= 8.53e-14`, `max bridge identity err <= 2.84e-14`):
1. Raw High (`raw_hi_perf`), Raw Low (`raw_lo_perf`), Raw All-Non-High (`raw_nonhi_perf`).
2. Raw High-minus-Low (`raw_hi_minus_lo_delta`) and Raw High-minus-All-Non-High (`raw_hi_minus_all_non_high_delta`).
3. Context-adjusted discrete contrasts (`hi vs lo` and `hi vs all-non-high`) via nuisance-residualized means.
4. Continuous P87.5-minus-P12.5 FWL slope (`delta_unshrunk`).

---

## 9. `EB Δ` vs `EB vs Pop μ₀` (Critical Judge Interpretation Guide)

The calculation linking absolute and pooled-relative performance is:

$$\text{EB vs Pop }\mu_0 = \text{EB }\Delta - \mu_0$$

- **Why $\mu_0$ is strongly negative:** Under high `BATTING_WICKET_DEPLETION_ANOMALY` (excess wickets already fallen), surviving batters consolidate and lower-order batters are exposed, producing a pooled population scoring drop of **$\mu_0 = -36.1238231044$ runs per 100 legal balls**. Under high `BOWLING_EXPECTED_SCORING_THREAT` (attacking phase/resource environment), batter scoring rises sharply, producing a pooled suppression-proxy deterioration of **$\mu_0 = -50.8837912303$ proxy units per 100 legal balls**.
- **Worked Example 1 — David Miller (#1 Batter):**
  - `EB Δ = -29.39`, `μ₀ = -36.12`, `EB vs Pop μ₀ = +6.73`.
  - **Interpretation:** David Miller's estimated scoring-rate deterioration under the batting resource-stress proxy is smaller than the pooled eligible-batter average by approximately `6.73` runs per 100 legal balls. **His absolute effect remains negative (`-29.39`).** Do **not** claim he improves his strike rate under actual match pressure.
- **Worked Example 2 — Matheesha Pathirana (#1 Bowler):**
  - `EB Δ = -34.95`, `μ₀ = -50.88`, `EB vs Pop μ₀ = +15.94`.
  - **Interpretation:** Matheesha Pathirana's estimated batter-run suppression deterioration under the bowling scoring-threat proxy is smaller than the pooled eligible-bowler deterioration by approximately `15.94` proxy units per 100 legal balls. **His absolute effect remains negative (`-34.95`).** Do **not** claim he reduces runs under actual match pressure.
- **Distinguishing the Three Measures:**
  1. **`EB Δ`:** Absolute estimated player-specific proxy-stress effect.
  2. **`EB vs Pop μ₀`:** Estimated effect relative to the pooled eligible-player stress effect (`EB Δ − μ₀`).
  3. **`P(Top 10)`:** Probability of appearing in the Top 10 candidate group across the `2,000` bootstrap rankings.
  - **`P(Δ > 0)`** is the probability of a positive absolute player effect (`< 0.001` for all 20 shortlisted players) and must **not** be confused with `P(Top 10)`. A player can rank highly relative to other candidates while having a negative absolute pressure effect; **never** describe these candidates as "positive pressure performers."

---

## 10. Eligibility & Precision Floor

- **Operational Precision Floor (`n_hi >= 50`, `n_lo >= 30`, `cs_matches >= 8`, `se_delta <= 25.0`):** Yields `106` eligible batters and `136` eligible bowlers (`V4_2_ELIGIBILITY_PRECISION_ANALYSIS.csv`).
- **Honest Framing:** Documented strictly as an operational precision floor to bound sampling error, **not** claimed as empirically optimal. Sensitivity across Strict (`100/60/10/20`), Operational (`50/30/8/25`), Relaxed (`30/20/5/30`), and Minimal (`15/15/3/40`) floors shows `6/10` (batters) and `9/10` (bowlers) overlap between Strict and Operational floors.

---

## 11. Claim A / B / C Out-of-Time Validation (`>= 2023`)

Claims are strictly separated (`V4_2_VALIDATION_MATRIX.csv`, `V4_2_MODEL_COMPARISON.csv`):
- **Claim A (General Skill FE):** Batters `rho = 0.539 (p = 0.108, n = 10)`; Bowlers `rho = 0.459 (p = 0.0552, n = 18)`.
- **Claim B (High-Stress Residual Execution):** Batters `rho = -0.115 (p = 0.751, n = 10)`; Bowlers `rho = 0.013 (p = 0.958, n = 18)`.
- **Claim C (Pressure-vs-Normal Slope):** Batters `rho = -0.358 (p = 0.310, n = 10)`; Bowlers `rho = +0.106 (p = 0.675, n = 18)` -> **`CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS`** across all 5 tested Ridge configurations (`5/20/60/150/asym`). This reflects both underpowered OOT sample sizes (`n = 10` / `18`) and missing chase-target/RRR state.
- **Within-Stratum Permutation Placebo:** Passes (`tau = 0.000, I2 = 0.0%, share(|z|>1.96) = 0.053` batters; `tau = 5.461, I2 = 7.2%, share(|z|>1.96) = 0.075` bowlers).

---

## 12. Secondary Outcomes & Trade-Offs

Secondary outcomes are estimated via the same Option A FWL+REML pipeline with **no arbitrary composite weighting**:
- **Batters:** Dismissal-risk delta per 100b (`-1.77` to `-3.49`, `MODERATE_OR_NEUTRAL_TRADEOFF`).
- **Bowlers:** Dot-ball % delta (`-5.45` to `-13.29` pp) alongside creditable wicket % delta (`+3.50` to `+3.85` pp), flagged `MIXED_SECONDARY_PROFILE`.

---

## 13. Final Provisional Top 10 Batters (`BATTING_WICKET_DEPLETION_ANOMALY`)

*(Source: [V4_2_FINAL_SHORTLIST.csv](data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv); `μ₀ = -36.12`, eligible `n = 106`)*

| Rank | ID | Player | Matches (`CS`) | `n_hi / n_lo` | Raw Hi−Lo | Unshrunk Δ | `EB Δ` | `EB vs Pop μ₀` | Boot 95% CI | Rank 95% CI | `P(Top 10)` [MCSE] |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---|---|
| 1 | `1077` | David Miller | 81 (`81`) | 296 / 456 | -21.81 | -6.64 | **-29.39** | **+6.73** | [-36.29, +0.58] | [1, 57] | 0.390 [0.011] |
| 2 | `7059` | Nehal Wadhera | 37 (`37`) | 231 / 98 | -2.50 | +4.64 | **-29.69** | **+6.44** | [-35.65, +10.00] | [1, 56] | 0.540 [0.011] |
| 3 | `152` | Ravindra Jadeja | 65 (`65`) | 349 / 178 | -48.69 | -13.82 | **-30.29** | **+5.83** | [-39.24, -1.60] | [2, 67] | 0.281 [0.010] |
| 4 | `4904` | Kamindu Mendis | 38 (`38`) | 222 / 113 | -20.08 | -2.67 | **-30.35** | **+5.77** | [-38.58, +1.37] | [1, 64] | 0.385 [0.011] |
| 5 | `1318` | Andre Russell | 57 (`57`) | 397 / 102 | -30.67 | -1.58 | **-30.42** | **+5.70** | [-38.83, +9.90] | [1, 65] | 0.445 [0.011] |
| 6 | `6512` | Michael Bracewell | 33 (`33`) | 170 / 37 | +16.60 | +15.06 | **-30.42** | **+5.70** | [-35.86, +9.96] | [1, 58] | 0.553 [0.011] |
| 7 | `3489` | Salman Agha | 42 (`42`) | 300 / 105 | -21.00 | -3.60 | **-30.45** | **+5.67** | [-38.18, +3.07] | [1, 64] | 0.401 [0.011] |
| 8 | `25213` | Dewald Brevis | 40 (`40`) | 198 / 125 | -5.32 | +5.52 | **-30.58** | **+5.55** | [-37.06, +6.29] | [1, 61] | 0.476 [0.011] |
| 9 | `24017` | Brian Bennett | 44 (`44`) | 87 / 169 | +8.90 | +2.75 | **-30.64** | **+5.48** | [-36.73, +3.25] | [1, 59] | 0.419 [0.011] |
| 10 | `4812` | Harry Tector | 45 (`45`) | 267 / 165 | -19.51 | -10.09 | **-30.67** | **+5.45** | [-40.58, -0.15] | [2, 67] | 0.308 [0.010] |

---

## 14. Final Provisional Top 10 Bowlers (`BOWLING_EXPECTED_SCORING_THREAT`)

*(Source: [V4_2_FINAL_SHORTLIST.csv](data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv); `μ₀ = -50.88`, eligible `n = 136`)*

| Rank | ID | Player | Matches (`CS`) | `n_hi / n_lo` | Raw Hi−Lo | Unshrunk Δ | `EB Δ` | `EB vs Pop μ₀` | Boot 95% CI | Rank 95% CI | `P(Top 10)` [MCSE] |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---|---|
| 1 | `8661` | Matheesha Pathirana | 54 (`54`) | 515 / 170 | -22.57 | -8.53 | **-34.95** | **+15.94** | [-41.39, -2.13] | [1, 33] | 0.790 [0.009] |
| 2 | `7364` | Haris Rauf | 48 (`48`) | 273 / 213 | -20.69 | -6.37 | **-35.81** | **+15.08** | [-42.31, +0.56] | [1, 37] | 0.776 [0.009] |
| 3 | `4641` | Lungi Ngidi | 39 (`39`) | 258 / 158 | -13.09 | -1.43 | **-37.95** | **+12.93** | [-41.72, -1.56] | [1, 34] | 0.771 [0.009] |
| 4 | `2933` | Jasprit Bumrah | 75 (`75`) | 612 / 314 | -30.94 | -24.23 | **-38.13** | **+12.76** | [-47.51, -13.01] | [1, 55] | 0.454 [0.011] |
| 5 | `19316` | Maheesh Theekshana | 99 (`99`) | 579 / 457 | -41.47 | -25.96 | **-38.16** | **+12.72** | [-46.91, -14.43] | [2, 52] | 0.405 [0.011] |
| 6 | `7967` | Noor Ahmad | 70 (`70`) | 340 / 388 | -29.18 | -24.93 | **-41.65** | **+9.24** | [-51.52, -16.53] | [2, 69] | 0.338 [0.011] |
| 7 | `3275` | Alzarri Joseph | 53 (`53`) | 349 / 189 | -32.81 | -24.89 | **-41.87** | **+9.02** | [-52.38, -15.08] | [2, 74] | 0.333 [0.011] |
| 8 | `2687` | Roston Chase | 45 (`45`) | 134 / 244 | -15.73 | -17.67 | **-42.57** | **+8.31** | [-51.82, -9.22] | [1, 71] | 0.422 [0.011] |
| 9 | `6628` | Gerald Coetzee | 29 (`29`) | 192 / 102 | -29.90 | -19.68 | **-43.64** | **+7.24** | [-54.79, -8.47] | [1, 82] | 0.393 [0.011] |
| 10 | `3720` | Craig Young | 23 (`23`) | 120 / 114 | -10.96 | -13.74 | **-43.71** | **+7.17** | [-52.86, -12.76] | [2, 75] | 0.362 [0.011] |

---

## 15. Individual Player Justification Links

Complete 20-point evidence sheets and mandatory caveats for all 10 batters and all 10 bowlers are published in:
- [V4_2_PLAYER_JUSTIFICATIONS.md](data/reports/v4_2/V4_2_PLAYER_JUSTIFICATIONS.md)

---

## 16. Limitations & Final Release Decision

- **Release Status:** **`V4.2 PROVISIONAL — RESOURCE STRESS`** (cannot be upgraded to calibrated match leverage while `CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`).
- **Key Limitations:** (1) No chase targets/RRR across `837` matches; (2) Bowler outcome excludes multi-run extras; (3) Claim C OOT slope replication is inconclusive (`CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS`); (4) Wide rank CIs mean the Top 10 should be treated as a **relative candidate shortlist** rather than deterministic 1–10 tiers.
- **Archived Historical Artifacts:** V3 (`data/outputs/v3/`), V4 (`data/outputs/v4/`), and V4.1 (`data/outputs/v4_1/`) remain preserved intact as archived comparison baselines.
