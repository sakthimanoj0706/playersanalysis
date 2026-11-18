# V4 RELEASE READINESS — SupeRR Intelligence V4

## Final Scientific Sign-Off
**`V4 PROVISIONAL — RESOURCE STRESS PROXY`**

## Decision Basis
1. **Why NOT `V4 VALIDATED — MATCH LEVERAGE MODEL`**:
   - Scoped data audit proves `CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`: non-DLS run-margin reconstruction fails on **`342 / 390`** matches because `extras1_runs` is a categorical code and `runs` excludes multi-run wides/byes/leg-byes/penalties. Exact target, score deficit, `RRR`, and win-probability derivative leverage `C_t` cannot be reconstructed without fabrication.
   - Chronological score-blind `WP_obs` lacks run/target context and miscalibrates, so win-probability leverage is quarantined.
2. **Why `V4 PROVISIONAL — RESOURCE STRESS PROXY` (and NOT `NO-GO`)**:
   - **Data Integrity Fixed**: Exact `194,014 = 193,988 regular + 26 Super Over` reconciliation verified; DLS `revised_overs` unit bug (values `30..114` already in balls, never `*6`) fixed; strict `player_id` aggregation enforced across duplicate names (`Abdul Samad`, `Haider Ali`, `Mohammad Ali`); pure pre-delivery B3 `RESOURCE_STRESS_PROXY` passes outcome-permutation leakage invariance and shuffled-pressure placebo (`tau -> 0`), and passes synthetic `+60 SR` signal recovery.
   - **Honest Uncertainty & Empirical Bayes Shrinkage**: Low-sample normal-baseline artifacts (such as V3's Mark Wood 31b and Mark Adair 41b outliers) are eliminated via coverage + common-support + cluster-robust SEs + 2,000-iter match-clustered bootstrap + DL/REML EB shrinkage + dual-gate non-collapse verification (`eb_hi_perf > 0`).
   - **Provisional Caveat Explicitly Disclosed**: Pure within-player pressure interaction heterogeneity (`tau`) is small (`I2 < 10%`), resulting in `0` strict `RELIABLE` badges and modest chronological `delta_eb_r`, so Top-10 rankings are transparently labeled **`PROVISIONAL`** and secondary RR squad scouting remains completely separate from Universal rankings.

## Artifact Checklist
- `data/outputs/v4/TOP_10_BATTERS_V4.csv`
- `data/outputs/v4/TOP_10_BOWLERS_V4.csv`
- `data/outputs/v4/ALL_BATTER_METRICS_V4.csv`
- `data/outputs/v4/ALL_BOWLER_METRICS_V4.csv`
- `data/outputs/v4/PLAYER_ELIGIBILITY_V4.csv`
- `data/outputs/v4/PLAYER_PRESSURE_EVIDENCE_V4.csv`
- `data/outputs/v4/PRESSURE_INDEX_DELIVERIES_V4.parquet`
- `data/outputs/v4/RANKING_SENSITIVITY_V4.csv`
- `data/outputs/v4/DATA_RECONCILIATION.csv`
- `data/outputs/v4/MODEL_VALIDATION_V4.csv`
- `data/outputs/v4/RANKING_SOURCE_OF_TRUTH_V4.json`
- `data/reports/v4/DATA_AUDIT_V4.md`, `PRESSURE_METHODOLOGY_V4.md`, `PLAYER_RELATIVE_PERFORMANCE_V4.md`, `VALIDATION_REPORT_V4.md`, `FINAL_TOP_10_JUSTIFICATION_V4.md`, `V4_RELEASE_READINESS.md`
