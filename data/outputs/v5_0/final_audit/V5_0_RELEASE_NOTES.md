# SupeRR Intelligence V5.0 — Release Notes

**Release:** `V5.0 — Universal T20 Pressure Performance Engine`  
**Branch:** `feat/v5-final-audit-rr-redesign-20261116`

## Summary of Changes
- **Track A (Cricsheet Score-Aware Pipeline):** 1-to-1 Cricsheet JSON crosswalk (`1,471 / 1,652` innings verified, `170,680` deliveries across `725` matches), score-aware Two-Innings Win Probability (`Inn 1 AUC=0.6986`, `Inn 2 AUC=0.8946`), 12-outcome Expected Leverage Index (`LI_global` & `LI_innings`), and total-run context-adjusted value (`DeltaRE_total`) separating non-bowler extras and non-bowler dismissals.
- **V5.0 Asymmetric Block-Penalized Joint Ridge RAPM:** Separate regularization for main skill (`alpha_main = 250.0`), pressure interaction (`alpha_int = 4000.0` via 1-SE rule), and context (`alpha_context = 250.0`), with paired match-cluster bootstrap (`B = 200` & `B = 1,000` audit) for `theta_HP = theta_main + delta_pressure`. Explicitly separates `theta_main`, `delta_pressure` (experimental), and `theta_HP` (combined HP, not a pure clutch ranking).
- **Dual Pressure Scales:** `LI_global` (absolute match leverage) and `LI_innings` (relative within-innings leverage) are tracked separately and never treated as interchangeable.
- **Four Mutually Exclusive Pressure Archetypes:** `ELITE CLUTCH PERFORMER`, `CRISIS / RESCUE SPECIALIST`, `PRESSURE-SENSITIVE GENERAL PERFORMER`, `BELOW-AVERAGE UNDER PRESSURE`, plus `UNCLASSIFIED / INSUFFICIENT EVIDENCE`.
- **Dashboard Extension:** Extended `dashboard/app.py` with a sidebar engine selector (`V4.2` default preserved; `V5.0` 3-tab view with Global Leaderboard, Track A Match Pressure Analysis, and Optional Franchise/Squad filter).

## Known Limitations
- `181 / 1,652` innings lack Cricsheet match/delivery reconciliation and remain excluded from Track A.
- Standalone pressure-uplift slopes (`delta_pressure`) exhibit high split-half variance (`Spearman = 0.2265` batters, `0.1768` bowlers), so `50/89` batters and `56/82` bowlers remain `UNCLASSIFIED / INSUFFICIENT EVIDENCE`.
- Innings-split (`40/150/5`) rankings are strictly exploratory; under `LI_global >= 1.50`, only `5` batters and `6` bowlers qualify in Innings 1.
