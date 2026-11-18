# SupeRR Intelligence — Universal T20 Pressure Performance Engine (V5.0)

## 1. Project Overview
SupeRR Intelligence is a research-grade cricket analytics platform for evaluating T20 batter and bowler performance after controlling for match context, opposition quality, innings state, venue/format par, and match leverage. **V5.0** provides a competition-independent T20 pressure engine across IPL and Men's T20I matches (2022–2026), while preserving **V4.2**, **V4.3**, and **V4.4** pipelines and artifacts.

## 2. Research Problem
Evaluate player performance under high-pressure match situations relative to baseline performance without confounding by phase, venue, innings, team strength, or opposition quality — and without fabricating missing extras or targets.

## 3. Evolution: V4.2 to V5.0
- **V4.2 (Provisional — Resource Stress):** Identified that raw `extras1_runs` is a categorical codebook (`1–7`), blocking score-aware WP; implemented Complete Penalized FWL + REML Empirical-Bayes on pre-delivery resource stress.
- **V4.3 (Observable-State & Batter-Run RAPM):** Formalized Phase 0–3 data-quality gates, Hierarchical EB venue/format par, cross-fitted `ER_batter(B, W)`, `DeltaRE_batter`, and joint batter–bowler Ridge RAPM (`alpha = 150.0`).
- **V4.4 (Cricsheet Reconciliation & Track A/B):** Reconciled `1,471 / 1,652` innings (`89.04%`) via 1-to-1 Cricsheet JSON matching; built score-aware Two-Innings WP, 12-outcome Expected Leverage Index (`LI`), `DeltaRE_total`, and Track B observable resource-pressure bridge.
- **V5.0 (Universal T20 Pressure Engine):** Introduced Asymmetric Block-Penalized Joint Ridge (`alpha_main = 250.0`, `alpha_int = 4000.0` via 1-SE rule), dual pressure scales (`LI_global`, `LI_innings`), paired bootstrap intervals for `theta_HP = theta_main + delta_pressure`, four mutually exclusive archetypes, and a 3-tab dashboard extension.

## 4. Data Sources & Coverage
- **Source Pack:** `853` matches (`837` with deliveries, `16` abandoned), `1,652` regular innings, `193,988` regular delivery rows (`185,951` legal deliveries), `4` Super Over matches (`26` rows isolated).
- **Cricsheet JSON Reconciliation (Track A):** `758 / 853` exact 1-to-1 match joins; **`1,471 / 1,652` verified innings** (`170,680` verified deliveries across `725` decided matches); **`181` blocked innings** excluded from Track A.

## 5. Track A vs Track B Distinction
- **Track A (Score-Aware Total-Run Target):** Uses Cricsheet-verified runs, targets, `LI_global`, `LI_innings`, and `DeltaRE_total` (separating non-bowler extras and non-bowler dismissals).
- **Track B (Observable Resource-State, Batter-Run-Only):** Covers all `193,988` regular deliveries using score-blind WP and `DeltaRE_batter`. Track A and Track B player coefficients are never merged.

## 6. Mathematical Methodology
- **Score-Aware WP:** Separate Innings 1 (`ProjectedFinalScore = CurrentScore + ER_total(B, W)`) and Innings 2 (`RunsRequired`, `RRR`, `CRR`, `wkts_rem`, `balls_rem`) dynamic logistic models in unified perspective `P(inn1_batting_team_wins)`.
- **Total-Run Value:** `DeltaRE_total = actual_total_runs + ER_total_after - ER_total_before`; player attribution removes `non_bowler_extras` (byes, leg-byes, delivery penalties) and separates `non_bowler_dismissal` events.

## 7. Two Leverage Scales
- **`LI_global = RawL_t / Mean(RawL_all_valid)`:** Absolute match win-probability leverage (`mean_raw_global = 0.015371`). Primary threshold: `LI_global >= 1.50` (`17.99%` of deliveries; `1.58%` in Inn 1, `36.18%` in Inn 2).
- **`LI_innings = RawL_t / Mean(RawL_same_innings)`:** Relative within-innings leverage (`mean_raw_inn1 = 0.010288`, `mean_raw_inn2 = 0.021000`).

## 8. Asymmetric Ridge Formulation
Minimizes `||y - X_main*theta - X_pressure*delta - X_context*gamma - b0||^2 + alpha_main*||theta||^2 + alpha_int*||delta||^2 + alpha_context*||gamma||^2` with training-fold-only standardization and 5-fold match-grouped CV + 1-SE selection (`alpha_main = 250.0`, `alpha_int = 4000.0`, `alpha_context = 250.0`). This separates the baseline main effect (`theta_main`), standalone pressure interaction (`delta_pressure`, experimental), and combined high-pressure performance (`theta_HP = theta_main + delta_pressure`, which correlates at `Spearman = 0.9909` with `theta_main` for batters and is therefore a combined performance score rather than a pure clutch ranking).

## 9. Player Archetypes
Mutually exclusive classification using paired 95% bootstrap CIs and `100/300/12` eligibility:
1. `ELITE CLUTCH PERFORMER` (`37` batters, `19` bowlers)
2. `CRISIS / RESCUE SPECIALIST` (`2` batters, `4` bowlers)
3. `PRESSURE-SENSITIVE GENERAL PERFORMER` (`0` batters, `0` bowlers)
4. `BELOW-AVERAGE UNDER PRESSURE` (`0` batters, `3` bowlers)
5. `UNCLASSIFIED / INSUFFICIENT EVIDENCE` (`50` batters, `56` bowlers + all ineligible players)

## 10. Eligibility Rules
Post-fit primary global gate: `n_HP >= 100`, `n_Total >= 300` (`is_ball_faced` for batters; all delivery events for bowlers), `m_HP >= 12` distinct HP matches (`89` batters, `82` bowlers eligible). Innings-split gate `(40, 150, 5)` is strictly exploratory.

## 11. Validation Methodology
5-fold match-grouped CV, chronological OOT (`> 2024`), `B = 200` paired match-cluster bootstrap (plus `B = 1,000` audit), `50` repeated match-level split-half tests, and V4.2/V4.3/V4.4 preservation checks.

## 12. Actual Measured Results
- **WP (Track A 5-Fold CV):** Inn 1 `AUC = 0.6986`, `Brier_eq = 0.2202`; Inn 2 `AUC = 0.8946`, `Brier_eq = 0.1257` (OOT `AUC = 0.9103`).
- **V5.0 Asymmetric Ridge:** 5-fold CV `MSE = 4.955498` (`RMSE = 2.226095`); OOT `MSE = 5.239541` (`RMSE = 2.289004`).
- **50-Split Stability:** Batters `hp_spearman = 0.2790`, `pres_spearman = 0.2265`, `top10_overlap = 5.48`; Bowlers `hp_spearman = 0.3631`, `pres_spearman = 0.1768`, `top10_overlap = 3.64`.

## 13. Statistical Limitations (Experimental Components)
- Standalone pressure-uplift slopes (`delta_pressure`) are **EXPERIMENTAL** due to finite high-pressure sample sizes (`50-split Spearman = 0.2265` batters, `0.1768` bowlers).
- `181 / 1,652` innings remain excluded from Track A due to missing/mismatched Cricsheet coverage.
- Out-of-sample future player-ranking prediction is not claimed beyond the tested OOT delivery MSE and split-half reliability metrics.

## 14. Installation
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 15. Dashboard Execution
```powershell
.venv\Scripts\streamlit.exe run dashboard/app.py
```
Use the sidebar **Analytics Engine** selector to switch between `V4.2 Provisional (Resource Stress)` (default) and `V5.0 Universal T20 Pressure Engine (Track A)`.

## 16. Pipeline Reproduction Commands
```powershell
.venv\Scripts\python.exe scripts/run_v4_3_phases_0_to_3.py
.venv\Scripts\python.exe scripts/run_v4_3_phases_3_5_to_7.py
.venv\Scripts\python.exe scripts/run_v4_4_pipeline.py
.venv\Scripts\python.exe scripts/run_v5_0_pipeline.py
.venv\Scripts\python.exe -m pytest tests/test_v5_0/ tests/test_ui_governance.py tests/test_v4_4/ tests/test_v4_3/ -v
.venv\Scripts\python.exe scripts/verify_v4_2_rankings.py
```

## 17. Directory Structure
- `src/v4_2/`, `src/v4_3/`, `src/v4_4/`, `src/v5_0/` — Versioned analytics engines
- `data/outputs/v4_2/`, `v4_3/`, `v4_4/`, `v5_0/` — Versioned outputs & audit artifacts
- `dashboard/` — Streamlit UI (`app.py`, `v5_0_panel.py`, `charts.py`, `data_loader.py`)
- `tests/` — Automated invariant, governance, and UI tests

## 18. References
- Brooker & Hogan (2012) — WASP; Asif & McHale (2016) — Dynamic Logistic WP; Davis, Perera & Swartz (2015) — T20 Run Differential; Sill (2010) — Ridge RAPM; Bhattacharjee & Lemmer (2016); Bandyopadhyay & Bhattacharjee (2025, arXiv:2505.01849); Cricsheet JSON open cricket data (`https://cricsheet.org/`).
