# SupeRR Intelligence V4.4 — Validation & Governance Report

**Branch:** `feat/v5-final-audit-rr-redesign-20261116`  
**Preservation:** V4.2 (`scripts/verify_v4_2_rankings.py` passed) and V4.3 (`data/outputs/v4_3/`, `docs/v4_3/`) remain intact and unmodified.

---

## 1. Phase-by-Phase Governance Table

| Component | Status | Scope / Coverage | Rationale |
|---|---|---|---|
| 1. Match Crosswalk (`V4_4_MATCH_CROSSWALK.csv`) | **VERIFIED** | `758 / 853` exact 1-to-1 (`95` missing, `0` ambiguous) | Strict `(date, normalized_team_pair)` join; zero forced joins |
| 2. Delivery & Extras Reconciliation (`V4_4_EXTRAS_RECONCILIATION.csv`) | **VERIFIED** | `1,471 / 1,652` innings (`89.04%`: `1,442` non-DLS + `29` DLS) | `total_runs == batter_runs + total_extras` & categorized extras sum verified |
| 3. Unmatched / Mismatched Innings | **BLOCKED (EXCLUDED FROM TRACK A)** | `181 / 1,652` innings (`157` missing match + `24` delivery/score mismatch) | Excluded from Track A score-aware modelling; routed to Track B |
| 4. Score-Aware Two-Innings WP (Track A) | **CONDITIONALLY VALIDATED** | `170,680` verified deliveries (`725` Inn-1 / `715` Inn-2 matches) | Inn-2 5-fold CV `AUC=0.8946`, `Brier_eq=0.1257`, `CalSlope=0.9526` |
| 5. True Expected Leverage Index (Track A) | **CONDITIONALLY VALIDATED** | `170,680` verified deliveries (12-outcome state transition) | Reference mean `LI=1.0000`; monotonic realized WP swing across thresholds |
| 6. Total-Run Value `DeltaRE_total` (Track A) | **CONDITIONALLY VALIDATED** | `170,680` verified deliveries | Separates `non_bowler_extras` and `non_bowler_dismissal` |
| 7. Pressure-Interaction Joint RAPM (Track A) | **EXPERIMENTAL** | `96` batters / `95` bowlers (`100/300/12` post-fit gate) | Main RAPM `r=0.959`/`0.956` vs V4.3; pressure-slope split-half `r=0.115`/`0.246` |
| 8. Observable Resource Pressure (Track B) | **EXPERIMENTAL** | All `193,988` regular deliveries (`OBSERVABLE_RESOURCE_PRESSURE_RAPM_BATTER_RUNS_ONLY`) | Score-blind bridge; does not capture run-state or RRR |
| 9. V4.2 Preservation | **VERIFIED** | `ALL V4.2 ARTIFACT & MATHEMATICAL VERIFICATIONS PASSED!` | Zero V4.2 files altered |

---

## 2. Key Empirical Metrics

### Track A: Score-Aware WP vs V4.3 Observable-State WP
- **Innings 1 (5-Fold CV):** `ROC-AUC = 0.6986`, `brier_equal_match = 0.2202`, `logloss_equal_match = 0.6304`, `cal_intercept = -0.0009`, `cal_slope = 0.9377` (OOT `> 2024`: `AUC = 0.7105`, `brier_eq = 0.2289`).
- **Innings 2 (5-Fold CV):** `ROC-AUC = 0.8946`, `brier_equal_match = 0.1257`, `logloss_equal_match = 0.3905`, `cal_intercept = +0.0042`, `cal_slope = 0.9526` (OOT `> 2024`: `AUC = 0.9103`, `brier_eq = 0.1221`, `cal_slope = 1.0723`).

### Track A: Expected Leverage Index & Threshold Sensitivity
- **Overall Reference:** `mean_raw_wp_swing = 0.015371`, `mean_li = 1.0000`, `median_li = 0.6922`, `p75_li = 1.1470`, `p90_li = 1.8848`.
- **Innings Split:** Innings 1 mean `LI = 0.6693` (`1.58%` >= 1.50); Innings 2 mean `LI = 1.3662` (`36.18%` >= 1.50).
- **Threshold Monotonicity:** Realized next-ball WP swing rises from `0.03107` (`LI >= 1.00`) to `0.03832` (`LI >= 1.50`) to `0.05299` (`LI >= 2.00`); wicket rate rises from `5.088%` to `6.002%`.

### Track A: Pressure-Interaction Joint RAPM (`alpha = 250.0`)
- **Continuous LI vs Binary `LI >= 1.50` Pressure Slope:** `Spearman = 0.7981` (batters), `0.7678` (bowlers).
- **Split-Half Reliability (10 splits):** Main effect `0.2945` (batters), `0.3106` (bowlers); Pressure slope `0.1146` (batters), `0.2456` (bowlers).
- **Comparison:** V4.4 Main RAPM vs V4.3 Main RAPM `Spearman = 0.9590` (batters), `0.9564` (bowlers); vs V4.2 General Skill FE (`Claim A`) `0.8156` (batters), `0.8173` (bowlers).
