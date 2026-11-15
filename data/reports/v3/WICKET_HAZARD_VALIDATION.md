# V3 Discrete-Time Wicket Hazard Model Diagnostic & Governance Report
**Document Code:** AGY-V3-WHV-001 (P1.1 Governance Patch)  
**Execution Date:** 15 November 2026  
**Governance Status:** **`EXPERIMENTAL_NOT_USED_FOR_RANKING`**

---

## 1. Executive Summary & Governance Mandate

Wickets in T20 cricket are rare events (~5.1% of legal deliveries). `src/models/v3_wicket_hazard.py` implements an exploratory discrete-time conditional logistic regression model:
$$P(W_{ijt} = 1 \mid X_t, \text{Phase}_t, \text{Crisis}_t)$$

**Critical Governance Mandate (`EXPERIMENTAL_NOT_USED_FOR_RANKING`):**
- This model is strictly designated **`EXPERIMENTAL_NOT_USED_FOR_RANKING`**.
- It is **not** calibrated, **not** production-ready, and **never** used as an input to the Universal Top-10 Batter or Bowler rankings (`data/outputs/v3/TOP_10_BATTERS.csv` and `TOP_10_BOWLERS.csv`).
- Neither the hazard model, the hierarchical joint model (`v3_joint_performance.py`), nor the LightGBM challenger (`v3_lightgbm_challenger.py`) is used as a validated production ranking component.

---

## 2. Methodology & Class-Weighting Specification

1. **Dismissal Filtering:**
   - Evaluates bowler-creditable dismissals (Caught, Bowled, LBW, Stumped, Hit Wicket).
   - Excludes non-bowler dismissals: Run Out (573), Retired Out (6), Obstructing the field (2).
2. **Pre-Delivery Situational Covariates:**
   - Innings Phase (`Powerplay`, `Middle`, `Death`), Match Format (`IPL` vs `T20I`), `wickets_fallen_before`, and pre-delivery `batting_crisis_score`.
3. **Estimation & Class Weighting:**
   - Regularized logistic regression (`C = 0.5`) fitted with `class_weight='balanced'` on chronological training deliveries (`match_date < 2025-06-01`) and evaluated on held-out test deliveries (`match_date >= 2025-06-01`).
   - In accordance with P1.1 governance rules, `class_weight='balanced'` is retained as-is without ad-hoc removal, and its severe probability miscalibration is transparently documented below.

---

## 3. Audited Out-of-Sample Diagnostic Metrics (`src/models/v3_wicket_hazard.py`)

| Diagnostic Metric | Held-Out Test Value | Governance Interpretation |
|---|---:|---|
| **ROC-AUC** | **0.572** (`0.5718`) | Weak discrimination only modestly above random (`0.500`) |
| **Log-Loss** | **0.692** (`0.6921`) | High cross-entropy loss near uninformative `ln(2) = 0.693` due to balanced class weights |
| **Brier Score** | **0.246** (`0.2461`) | Large mean squared probability error caused by probability inflation |
| **Expected Wickets (Sum of Predicted Probabilities)** | **26,843** (`26,843.2`) | Severe over-prediction caused by `class_weight='balanced'` shifting base hazard toward ~0.50 |
| **Actual Wickets (Held-Out Test Cohort)** | **2,931** | True bowler-creditable wickets in held-out test matches |
| **Expected / Actual Calibration Ratio** | **9.16x** (`9.158x`) | **Uncalibrated** (over-predicts total wickets by more than 9x) |

---

## 4. Expected-Wicket Mismatch Explanation & Remediation Requirements

- **Why Expected Wickets (26,843) Exceed Actual Wickets (2,931) by 9.16x:**
  - Because `LogisticRegression(class_weight='balanced')` up-weights the minority wicket class (~5.1% base rate) by ~10x during maximum-likelihood estimation without subsequent Platt scaling or isotonic probability calibration, the raw `predict_proba` outputs are centered near `0.48–0.50` per delivery instead of the true ~`0.051` empirical hazard rate.
  - Summing uncalibrated balanced-weight probabilities across ~55,400 held-out legal deliveries yields `26,843` expected wickets compared to `2,931` observed wickets.
- **Governance Rule:**
  - Do not present this model as calibrated or `PRODUCTION_VALIDATED`.
  - Any future promotion of the hazard model out of `EXPERIMENTAL_NOT_USED_FOR_RANKING` requires probability recalibration (e.g., isotonic/Platt calibration on a dedicated validation split) and out-of-time calibration verification.

