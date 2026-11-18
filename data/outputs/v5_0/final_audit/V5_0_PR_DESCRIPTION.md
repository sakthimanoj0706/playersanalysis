# Pull Request: SupeRR Intelligence V5.0 — Universal T20 Pressure Performance Engine

## Overview
Introduces **V5.0** (alongside V4.3 and V4.4) as a competition-independent T20 pressure analytics engine built on Cricsheet-verified IPL and Men's T20I data, while preserving all V4.2, V4.3, and V4.4 artifacts.

## Key Improvements
1. **Data & Extras Reconciliation (V4.4 → V5.0):** Resolves the raw feed's categorical `extras1_runs` blocker across `1,471 / 1,652` innings (`170,680` deliveries) via strict 1-to-1 Cricsheet JSON matching.
2. **Score-Aware WP & Dual Leverage Scales:** Two-innings WP (`Inn 2 AUC = 0.8946`, `Brier_eq = 0.1257`) powering `LI_global` (absolute match leverage) and `LI_innings` (within-innings relative leverage).
3. **Asymmetric Block-Penalized Ridge & Paired CIs:** 5-fold match-grouped CV + 1-SE rule (`alpha_main = 250`, `alpha_int = 4000`) and paired bootstrap CIs for `theta_HP = theta_main + delta_pressure`.
4. **Dashboard Integration:** Extends `dashboard/app.py` with a sidebar engine selector (`V4.2` default unchanged; `V5.0` adds Global Leaderboard, Verified Match Pressure, and Franchise/Squad views).

## Verification Checklist
- [x] `pytest tests/test_ui_governance.py -v` (`2 passed`, covering 17 UI governance contracts)
- [x] `pytest tests/test_v5_0/ -v` (`3 passed`)
- [x] `pytest tests/test_v4_4/ tests/test_v4_3/ -v` (`8 passed`: 3 in V4.4, 5 in V4.3)
- [x] `python scripts/verify_v4_2_rankings.py` (`ALL V4.2 ARTIFACT & MATHEMATICAL VERIFICATIONS PASSED!`)
- [x] `.gitignore` updated to exclude raw downloadable `data/external/cricsheet/*.zip` archives (`18.93 MB` total)
