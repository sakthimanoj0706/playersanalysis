# V3 Pressure Feature Integrity Audit & Data Validation

**Audit Identifier:** `V3-RANKING-INTEGRITY-001 / PRIORITY 2`  
**Document Path:** `data/reports/v3/PRESSURE_FEATURE_INTEGRITY_AUDIT.md`  
**Execution Date:** 14 November 2026  
**Status:** **AUDITED & REPAIRED**

---

## 1. Executive Summary

An audit of the pressure engine (`src/pressure_engine/v3_pressure_model.py`) identified critical vulnerabilities in feature handling:
1. **Silent Fallbacks & Zero-Fill Defaults:** Missing columns or null values were silently imputed with arbitrary constants (`fillna(0)` for wickets and dots; `fillna(10.0)` for batter balls faced; `fillna(1.0)` for phase multiplier).
2. **False Normalization:** Incomplete or corrupted records were silently converted into low-pressure ("normal") match conditions instead of being flagged as missing/unclassified.
3. **Cached Parquet Invalidation:** The cached feature file `data/features/ball_by_ball_with_pressure.parquet` was generated using legacy V2 schemas, lacking canonical player IDs, V3 pressure formulas, and explicit validity indicators.

These defects have been repaired with explicit schema validation, strict missingness detection, mutual tier exclusivity, and feature regeneration.

---

## 2. Explicit Required Feature Schemas

### 2.1 Batting Crisis Pressure Schema
| Feature Name | Type | Allowed Values | Semantic Description |
| :--- | :--- | :--- | :--- |
| `wickets_fallen_before` | int / float | $[0, 10]$ | Cumulative wickets fallen in innings before delivery |
| `wickets_in_last_12_legal_balls` | int / float | $[0, 10]$ | Wickets fallen in previous 12 legal balls |
| `batter_balls_faced` | int / float | $[0, \infty)$ | Legal deliveries faced by the striker before delivery |
| `consecutive_dots` | int / float | $[0, \infty)$ | Consecutive dot deliveries faced by striker / team |
| `dots_in_last_12_legal_balls` | int / float | $[0, 12]$ | Dot deliveries in previous 12 legal balls |
| `innings_phase` | str | `{'powerplay', 'middle', 'death'}` | Pre-delivery innings match phase |

### 2.2 Bowling Defensive Pressure Schema
| Feature Name | Type | Allowed Values | Semantic Description |
| :--- | :--- | :--- | :--- |
| `batting_wickets_remaining` | int / float | $[0, 10]$ | Opponent wickets in hand ($10 - \text{wickets fallen}$) |
| `innings_phase` | str | `{'powerplay', 'middle', 'death'}` | Pre-delivery innings match phase |
| `boundaries_in_last_12_legal_balls` | int / float | $[0, 12]$ | Boundaries conceded in last 12 legal balls |
| `dots_in_last_12_legal_balls` | int / float | $[0, 12]$ | Dots bowled in last 12 legal balls |

---

## 3. Removal of Silent Defaults and Introduction of Pressure Validity

### 3.1 Behaviors Removed
- **Missing wickets:** Formerly converted to 0. Now: delivery marked `batting_pressure_data_valid = False`.
- **Missing wicket clusters:** Formerly converted to 0. Now: delivery marked `batting_pressure_data_valid = False`.
- **Missing striker exposure:** Formerly converted to 10.0. Now: delivery marked `batting_pressure_data_valid = False`.
- **Missing dot/boundary histories:** Formerly converted to 0. Now: delivery marked invalid.
- **Missing or unknown phase:** Formerly converted to neutral multiplier 1.0 without indication. Now: delivery marked invalid.

### 3.2 Explicit Data Validity Indicators
Every delivery now contains:
- `batting_pressure_data_valid` (bool): `True` only when all required batting features are present, non-null, and within valid domain bounds.
- `bowling_pressure_data_valid` (bool): `True` only when all required bowling features are present, non-null, and within valid domain bounds.
- `batting_pressure_missing_features` (str): Comma-separated list of missing feature names for diagnostic provenance.
- `bowling_pressure_missing_features` (str): Comma-separated list of missing bowling feature names.

### 3.3 Handling Incomplete Records
- Incomplete records are assigned tier `PRESSURE_UNCLASSIFIED`.
- Numeric scores (`batting_crisis_score`, `bowling_defensive_score`) are assigned `NaN`.
- Incomplete records are excluded from normal, moderate, and high pressure buckets (`is_batting_high_pressure = False`, `is_batting_moderate_pressure = False`, `is_batting_normal_pressure = False`).
- Normal-pressure eligibility strictly requires valid pressure classification.

---

## 4. Formula Governance & Provisional Approval

For the current repair iteration, the existing scoring equations are retained as provisional heuristics for reproducibility:
- **Batting Crisis Score:**
  $$\text{Score} = \min\left(10, \left(c_{\text{wkt}} + c_{\text{cluster}} + c_{\text{novelty}} + c_{\text{stagnation}}\right) \times \text{Phase Mult}\right)$$
- **Bowling Defensive Score:**
  $$\text{Score} = \min\left(10, c_{\text{resource}} + c_{\text{phase}} + c_{\text{momentum}} + c_{\text{rotation}}\right)$$

**Governance Notes:**
1. Component weights are hand-assigned provisional weights and are NOT claimed to be empirically estimated variance parameters.
2. Batting and bowling pressure models remain strictly independent.
3. Zero Target Leakage: Every input is established prior to ball release; no runs, dismissals, or match outcomes are ingested.
4. Unrelated batting-position or role proxies are strictly excluded from match-state pressure scores.

---

## 5. Parquet Dataset Validation & Regeneration

The master feature dataset `data/features/ball_by_ball_with_pressure.parquet` was validated and rebuilt from the verified context pipeline:
- **Total Deliveries:** 193,988
- **Schema Version:** `V3.1_CANONICAL`
- **Formula Version:** `V3_PROVISIONAL_HEURISTIC`
- **Batting Valid Deliveries:** 193,988 (100.0%)
- **Bowling Valid Deliveries:** 193,988 (100.0%)
- **Batting High Pressure Balls:** 15,464 (8.0%)
- **Batting Moderate Pressure Balls:** 30,760 (15.9%)
- **Batting Normal Pressure Balls:** 147,764 (76.2%)
- **Batting Unclassified Balls:** 0 (0.0%)
- **Bowling High Pressure Balls:** 101,935 (52.5%)
- **Bowling Moderate Pressure Balls:** 71,592 (36.9%)
- **Bowling Normal Pressure Balls:** 20,461 (10.5%)
- **Bowling Unclassified Balls:** 0 (0.0%)
- **Canonical ID Resolution:** Strikers and bowlers mapped through `PlayerIdentityResolver` (`canonical_striker_id`, `canonical_bowler_id`).
- **Legacy Backup:** Preserved at `data/features/ball_by_ball_with_pressure_legacy.parquet`.

All pressure integrity tests in `tests/test_v3_pressure_feature_integrity.py` pass.
