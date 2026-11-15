# SupeRR Intelligence V3 — Model Governance, Diagnostic & Limitation Report (P1.1 Patch)

**Document:** `data/reports/v3/V3_MODEL_REVALIDATION.md`  
**Execution Date:** 15 November 2026  
**System Status:** **`P1.1 PATCH VERIFIED — PROVISIONAL MODEL`**

> **Mandatory Provisional Model Disclosure:**
> "Rankings are provisional. Batter ranks 5, 6, 9 and 10 are sensitive to scoring weights. The pressure classification remains heuristic and position-proxy based. The new score has not yet undergone independent out-of-time validation."

---

## 1. Model Governance & Diagnostic Matrix

Every model component in the V3 repository has been audited against actual execution outputs and assigned an explicit governance status. No exploratory model is claimed as `PRODUCTION_VALIDATED`.

| Component | Model Implementation | Formal Objective | Evaluation Strategy | Audited Diagnostic Metrics | Governance Status | Used in Ranking? |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1. Pressure Proxy** | `src/pressure_engine/v3_pressure_model.py` | Pre-delivery heuristic state indices bounded in $[0, 10]$ | Ex-Ante Rule & Leakage Audit | 0.0 post-delivery leakage; bounded in $[0, 10]$; position/state proxy | **`PROVISIONAL_POSITION_PROXY_HEURISTIC`** | **Yes (Tier Stratification)** |
| **2. Role Classifier** | `src/classification/v3_role_classifier.py` | 5-state mutually exclusive taxonomy (`BAT_SPECIALIST`, `BOWL_SPECIALIST`, `BAT_PRIMARY_AR`, `BOWL_PRIMARY_AR`, `UNRESOLVED`) | Canonical Career Workload & Modal Batting Order | 1,118 classified; intersection between bat gate (382) and bowl gate (311) is **0** | **`CANONICAL_ROLE_GATING_ACTIVE`** | **Yes (Eligibility Gate)** |
| **3. Ranking Score (`PRI`)** | `scripts/compute_v3_rankings.py` | Fixed-weight composite score (35/35/20/10) with `MIN_NORMAL_BALLS = 100` for bowlers | Weight Sensitivity (5 configs) & Threshold Grid (270 configs) | Batter ranks 5, 6, 9, 10 weight-sensitive; not yet validated out-of-time | **`PROVISIONAL_FIXED_WEIGHT_SCORE`** | **Yes (Primary Score)** |
| **4. Reliability & CIs** | `src/reliability/v3_reliability.py` | Match-clustered bootstrap (95% CI, 2,000 iter) and Empirical Bayes shrinkage | Cluster Match Bootstrap (2,000 resamples) | Preserves intra-match serial correlation; eligible-pool priors ($K=25$ & Beta-Binomial) | **`VERIFIED_CLUSTER_BOOTSTRAP`** | **Yes (Shrinkage & CIs)** |
| **5. Wicket Hazard** | `src/models/v3_wicket_hazard.py` | Discrete-time logistic hazard model (`class_weight='balanced'`) | Chronological Split (`2025-06-01`) | **AUC: 0.572, Log-Loss: 0.692, Expected Wickets: 26,843 vs Actual: 2,931 (9.16x over-prediction)** | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **6. Joint Model** | `src/models/v3_joint_performance.py` | Hierarchical Ridge model: $Y_t = \alpha + X_t\beta + a_i + b_j + H_t(u_i + v_j) + \epsilon_t$ | Chronological Match Split | Exploratory linear additive benchmark | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **7. Challenger Model** | `src/models/v3_lightgbm_challenger.py` | Non-linear tree-boosted runs and wicket benchmark | Chronological Match Split | Exploratory non-linear feature benchmark | **`EXPERIMENTAL_NOT_USED_FOR_RANKING`** | **No (Excluded)** |
| **8. Tail-Risk Engine** | `src/models/v3_tail_risk.py` | Over-level VaR90, CVaR90, and Pareto Frontier | Over-Level Concession Distribution | Exploratory empirical quantiles | **`EXPLORATORY_ANALYTICS_ONLY`** | **No (Excluded)** |

---

## 2. Governance & Limitation Verification Notes

1. **Wicket Hazard Governance (`EXPERIMENTAL_NOT_USED_FOR_RANKING`):**
   - Because `LogisticRegression(class_weight='balanced')` up-weights rare wicket events without post-hoc probability calibration, the held-out evaluation produces **AUC = 0.572**, **Log-Loss = 0.692**, and **26,843 expected wickets vs 2,931 actual wickets** (9.16x miscalibration).
   - It is never claimed as calibrated or production-ready and is excluded from all ranking calculations.
2. **Pressure Model Limitation (`PROVISIONAL_POSITION_PROXY_HEURISTIC`):**
   - Batting position is a proxy for entry role rather than direct evidence of match leverage.
   - Target, required run rate, and full second-innings chase leverage are not yet integrated due to categorical extras codebook quarantine.
   - Positional crisis distributions must not be presented as calibrated player-level crisis probabilities.
3. **Role Gating Disjointness Proof:**
   - Batting gate: `v3_role.isin(['BAT_SPECIALIST', 'BAT_PRIMARY_AR'])`
   - Bowling gate: `v3_role.isin(['BOWL_SPECIALIST', 'BOWL_PRIMARY_AR'])`
   - Verified by automated test: `test_no_player_in_both_leaderboard_gates`.

