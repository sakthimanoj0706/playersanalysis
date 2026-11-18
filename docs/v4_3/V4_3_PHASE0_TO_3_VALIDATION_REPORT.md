# SupeRR Intelligence V4.3 — Phases 0–3 Validation & Data-Quality Gate Report

**Repository Branch:** `feat/v5-final-audit-rr-redesign-20261116`  
**Observed Git HEAD:** `b0a852c4c4d3fc51931deea2ec25eb3dcda3832d` *(Note: prompt-referenced commit `d60635b239f7177d46581ea4463781ff7a98c798` is not in local git history)*  
**V4.2 Preservation:** Verified intact via `scripts/verify_v4_2_rankings.py` (`ALL V4.2 ARTIFACT & MATHEMATICAL VERIFICATIONS PASSED!`).  
**Status after Phases 0–3:** **`BLOCKED FOR SCORE-AWARE PRODUCTION WP / CONDITIONAL GO FOR OBSERVABLE-STATE & BATTER-RUNS MODELLING`**

---

## 1. Phase 0 — Repository & Data Audit (`V4_3_DATA_AUDIT.csv`)

- **Matches Table:** `853` matches (`837` with deliveries, `16` abandoned with 0 deliveries).
- **Regular Innings (`{1, 2}`):** `837` matches, `1,652` innings, `193,988` delivery rows, `185,951` legal deliveries.
- **Super Overs (`{3, 4}`):** `4` matches, `26` delivery rows — strictly isolated from regular innings.
- **Sequence & Identity Integrity:** `0` duplicate delivery rows, `0` duplicate `(match_id, innings, innings_ball_num)`, `0` missing `striker_id`/`non_striker_id`/`bowler_id`, `0` invalid `overid` outside `[1, 20]`, `0` innings-2-without-innings-1. `1` wicket row has blank `dismissed_player_id`; `playing_eleven` has repeated `(match_id, team_id, player_id)` keys.
- **Critical Extras Blocker:**
  - `extras1_runs` is 100% a 1-to-1 categorical codebook (`1=Overstep`, `2=wide`, `3=legbyes`, `4=byes`, `5=other`, `6=None`, `7=Penalty`) with `0` mismatches against `extras_type`. It is **not** numeric extra runs.
  - All `7,474` `wide` rows, `2,661` `legbyes` rows, `505` `byes` rows, and `1` `Penalty` row have `runs == 0` and `extras_2_runs == 0`.
  - `extras_2_runs` is nonzero on only `35 / 194,014` rows (`19` = `1`, `16` = `4`).

### Phase Gate Decisions

| Phase | Decision | Rationale |
|---|---|---|
| Phase 0 (Data Audit) | **GO** | Schema, IDs, sequences, and Super Over separation verified |
| Phase 1 (Score Reconstruction) | **CONDITIONAL GO WITH BLOCK** | Legal balls & batter runs verified; exact team totals blocked on 1,641/1,652 innings |
| Phase 2 (EB Par & `ER(B, W)`) | **CONDITIONAL GO (BATTER RUNS ONLY)** | Validated on `rem_batter_runs` (`T20` & `T20I`); total-runs par blocked |
| Phase 3 (Score-Aware WP) | **BLOCKED (DIAGNOSTIC ONLY)** | `0 / 837` matches have both-innings verified totals; run-only diagnostic reported |
| Phase 4 (Expected Leverage Index) | **BLOCKED BY PHASE 3** | Requires calibrated, verified score-aware WP for true match leverage |
| Phase 5 (`DeltaRE` on Batter Runs) | **CONDITIONAL GO (BATTER RUNS ONLY)** | Well-defined on `rem_batter_runs` + `ER(B, W)` |
| Phase 6 (Joint Ridge RAPM) | **CONDITIONAL GO (OBSERVABLE STATE)** | Can run on observable-state / `DeltaRE_batter` without fabricating chase targets |
| Phase 7 (Uncertainty & V4.2 Comparison) | **CONDITIONAL GO** | Match-cluster bootstrap & V4.2 comparison valid on observable/batter-runs scope |
| Phase 8 (Dashboard Integration) | **CONDITIONAL GO WITH WARNINGS** | Must display explicit data-quality warnings for unverified scores/targets |

---

## 2. Phase 1 — Score Reconstruction Audit (`V4_3_SCORE_RECONSTRUCTION_AUDIT.csv`)

- **Regular Innings Audited:** `1,652`
- **Verified Exact Innings (`any_extra_events == 0`):** `11 / 1,652` (`0.67%`)
- **Verified Exact Full Matches:** `0 / 837` (`0.00%`)
- **Blocked Innings:** `1,641 / 1,652` (`99.33%`) — `reconstructed_innings_total` kept as `NaN` (never fabricated); `min_reconstructed_score` (`batter_runs + 1*(wide or Overstep)`) exported strictly as an unverified lower bound.
- **Non-DLS Run-Margin Cross-Check:** `48 / 390` exact (`342` fail), and most of those `48` match by accidental cancellation rather than zero unknown extras.

---

## 3. Phase 2 — Hierarchical EB Venue/Format/Season Par & `ER(B, W)`

Scoped strictly to `rem_batter_runs` on non-DLS regular innings (`818` matches, `190,480` deliveries):

| Split | Subgroup | Deliveries | Matches | MAE | RMSE | Mean Residual |
|---|---|---:|---:|---:|---:|---:|
| Match-Grouped 5-Fold CV | All Non-DLS | 190,480 | 818 | 17.2883 | 23.7557 | +0.6962 |
| Chronological OOT (`> 2024`) | All Non-DLS | 75,990 | 333 | 17.8741 | 24.7149 | +1.2773 |
| 5-Fold CV (Subgroup) | Innings 1 | 100,044 | 818 | 16.5427 | 23.3572 | +0.8636 |
| 5-Fold CV (Subgroup) | Innings 2 | 90,436 | 796 | 18.1131 | 24.1888 | +0.5110 |
| 5-Fold CV (Subgroup) | Format `T20` (IPL) | 86,750 | 363 | 16.7782 | 22.7545 | +0.6447 |
| 5-Fold CV (Subgroup) | Format `T20I` | 103,730 | 455 | 17.7148 | 24.5617 | +0.7393 |

---

## 4. Phase 3 — Two-Innings Win Probability Engine

All models use unified perspective `P(inn1_batting_team_wins)` and strictly pre-match Elo (`compute_pre_match_elo`) + fold-isolated `ER(B, W)` & EB par:

| Innings | Model Family | Split | ROC-AUC | Brier | LogLoss | Cal Intercept | Cal Slope | Governance Status |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | `OBSERVABLE_STATE_WP` | 5-Fold CV | 0.6526 | 0.2319 | 0.6553 | +0.0092 | 0.8492 | `VALIDATED_SCORE_BLIND_BASELINE` |
| 1 | `OBSERVABLE_STATE_WP` | OOT `> 2024` | 0.6826 | 0.2244 | 0.6389 | -0.1450 | 1.0940 | `VALIDATED_SCORE_BLIND_BASELINE` |
| 1 | `LOWER_BOUND_SCORE_WP_DIAGNOSTIC` | 5-Fold CV | 0.6978 | 0.2205 | 0.6315 | +0.0058 | 0.8920 | `BLOCKED_FOR_PRODUCTION_UNVERIFIED_EXTRAS` |
| 1 | `LOWER_BOUND_SCORE_WP_DIAGNOSTIC` | OOT `> 2024` | 0.7128 | 0.2217 | 0.6367 | -0.3416 | 0.8604 | `BLOCKED_FOR_PRODUCTION_UNVERIFIED_EXTRAS` |
| 2 | `OBSERVABLE_STATE_WP` | 5-Fold CV | 0.7656 | 0.1963 | 0.5744 | +0.0124 | 0.9242 | `VALIDATED_SCORE_BLIND_BASELINE` |
| 2 | `OBSERVABLE_STATE_WP` | OOT `> 2024` | 0.7650 | 0.1986 | 0.5805 | -0.1899 | 0.8822 | `VALIDATED_SCORE_BLIND_BASELINE` |
| 2 | `LOWER_BOUND_SCORE_WP_DIAGNOSTIC` | 5-Fold CV | 0.8885 | 0.1358 | 0.4180 | +0.0018 | 0.9285 | `BLOCKED_FOR_PRODUCTION_UNVERIFIED_EXTRAS` |
| 2 | `LOWER_BOUND_SCORE_WP_DIAGNOSTIC` | OOT `> 2024` | 0.9065 | 0.1272 | 0.3915 | -0.3676 | 1.0352 | `BLOCKED_FOR_PRODUCTION_UNVERIFIED_EXTRAS` |

Calibration curves saved to `data/outputs/v4_3/plots/wp_first_innings_calibration.html` and `wp_second_innings_calibration.html`.
