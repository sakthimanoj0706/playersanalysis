# SupeRR Intelligence V4.3 — Methodology & Validation Report (Phases 3.5, 5, 6, 7 & Scorecard Diagnostic)

**Branch:** `feat/v5-final-audit-rr-redesign-20261116`  
**Base HEAD:** `b0a852c4c4d3fc51931deea2ec25eb3dcda3832d`  
**Governing Data-Quality Record:** [V4_3_PHASE0_TO_3_VALIDATION_REPORT.md](V4_3_PHASE0_TO_3_VALIDATION_REPORT.md) *(preserved untouched)*  
**V4.2 Preservation:** Verified intact via `scripts/verify_v4_2_rankings.py`.

---

## Governance Classification

| Component | Status | Notes |
|---|---|---|
| Phase 0–1 Data Audit & Score Reconstruction | **Verified** | 837 regular matches, 1,652 innings, 193,988 rows, 185,951 legal balls; 1,641/1,652 innings blocked on exact totals due to categorical `extras1_runs` |
| Phase 3.5 Observable-State WP Audit | **Research Baseline** | Score-blind; beats Elo-only baseline on equal-match-weighted Brier & LogLoss in both innings & OOT |
| Phase 5 `ER_batter(B, W)` & `DeltaRE_batter` | **Conditionally Validated** | Strictly scoped to `batter_runs` (excludes unquantified extras); cross-fitted 5-fold OOF & OOT |
| Phase 6 Joint Batter–Bowler Ridge RAPM | **Experimental** | Target `DeltaRE_batter`; tuned `alpha=150.0`; no `LI >= 1.50` pressure interactions |
| Phase 7 Uncertainty & V4.2 Comparison | **Conditionally Validated** | 200 match-cluster bootstrap refits, 10 split-half tests, threshold sensitivity (`150/300/500/750`) |
| Score-Aware Production WP & True WP Leverage | **Blocked** | 0/837 verified full matches; 0 independent scorecards in repository |

---

## Key Empirical Results

### Phase 3.5: Observable-State WP vs Elo-Only Baseline (Equal-Match-Weighted)
- **Innings 1 (5-Fold CV, 793 matches):** `OBSERVABLE_STATE_WP` Brier `0.2310` [0.2230, 0.2388], LogLoss `0.6534` [0.6359, 0.6700] vs `ELO_ONLY_BASELINE` Brier `0.2450` [0.2397, 0.2503], LogLoss `0.6832` [0.6722, 0.6944].
- **Innings 2 (5-Fold CV, 793 matches):** `OBSERVABLE_STATE_WP` Brier `0.1930` [0.1826, 0.2047], LogLoss `0.5668` [0.5417, 0.5947] vs `ELO_ONLY_BASELINE` Brier `0.2439` [0.2389, 0.2490], LogLoss `0.6806` [0.6704, 0.6913].

### Phase 5: `ER_batter(B, W)` & `DeltaRE_batter`
- **5-Fold Match-Grouped OOF (818 non-DLS matches, 190,480 deliveries):** `ER_batter_BW_EB_Par` achieves `MAE = 17.2077`, `RMSE = 23.6316` vs `Historical_Rate_Baseline` `MAE = 18.7569`, `RMSE = 25.7630`.
- **Chronological OOT (`> 2024`, 333 matches, 75,990 deliveries):** `MAE = 17.8741`, `RMSE = 24.7149` vs baseline `MAE = 19.2847`, `RMSE = 26.4974`.

### Phase 6: Experimental Joint Batter–Bowler Ridge RAPM
- **Tuned `alpha = 150.0`** (5-fold match-grouped CV `MSE = 4.570330`, `RMSE = 2.137833`; beats `alpha = 250.0` at `MSE = 4.571859`).
- Includes all `824` batters and `596` bowlers; separates `is_non_bowler_dismissal_sep` and `is_unresolved_wicket_sep`.
- **Attribution Limit:** Measures batter-run value only; does **not** represent total runs conceded, extras, complete bowling economy, fielding contribution, or complete player value.

### Phase 7: Uncertainty & V4.2 Comparison
- **Match-Cluster Bootstrap (`B = 200`, `>= 300` legal balls):** Batters (`n = 169`) median SE `6.9521` runs/100b, median 95% rank CI width `102.13`; Bowlers (`n = 180`) median SE `6.8376` runs/100b, median 95% rank CI width `112.05`.
- **Split-Half Reliability (10 splits):** Batters mean Spearman `0.2798` (Pearson `0.3847`); Bowlers mean Spearman `0.3278` (Pearson `0.3321`).
- **V4.2 vs V4.3 (Common Eligible Pool):** Strong agreement with V4.2 General Skill FE (`Claim A`: Batters `r = 0.8515`, `8/10` Top-10 overlap; Bowlers `r = 0.8969`, `5/10` Top-10 overlap), and expected divergence from V4.2 Pressure Slope (`EB Delta`: Batters `r = -0.4556`; Bowlers `r = 0.1828`), as V4.3 RAPM here estimates overall batter-run value without pressure interactions.

### Task 5: Scorecard Recovery Diagnostic
- `0` external scorecard files found in repository.
- `1,618 / 1,652` innings remain `UNRESOLVED_NO_INDEPENDENT_SCORECARD`, `23` have only `revised_target` (innings 2 DLS), and `11` have zero extras.
