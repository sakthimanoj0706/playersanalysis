# SupeRR Intelligence V5.0 — Governance & Validation Report

**Branch:** `feat/v5-final-audit-rr-redesign-20261116`  
**Git HEAD:** `b0a852c4c4d3fc51931deea2ec25eb3dcda3832d`  
**Preservation:** V4.2 (`scripts/verify_v4_2_rankings.py` passed), V4.3, and V4.4 artifacts remain intact and unmodified.

---

## 1. Final Governance Classification

| Component | Classification | Scope / Evidence |
|---|---|---|
| Phase 0: Data Audit & Track A/B Separation | **VERIFIED** | `170,680` Track A deliveries (`725` matches); `193,988` Track B deliveries (`837` matches); `1,471` verified innings, `181` blocked innings |
| Phase 2: Two Pressure Scales (`LI_global`, `LI_innings`) | **VERIFIED** | `mean_raw_global = 0.015371`; Inn 1 mean `0.010288`, Inn 2 mean `0.021000`; exact counts exported |
| Phase 1 & 4: Asymmetric Block-Penalized Ridge & Paired HP Model | **CONDITIONALLY VALIDATED** | 5-fold CV + 1-SE rule selected `alpha_main = 250.0, alpha_int = 4000.0` (`pooled_oof_mse = 4.955498`); OOT `MSE = 5.239541`; paired 200-boot CIs |
| Phase 3: Separate Innings Pressure Performance | **CONDITIONALLY VALIDATED** | Separate Inn 1 & Inn 2 models under `LI_global` & `LI_innings`, gated at `(40, 150, 5)` |
| Phase 5: Four Pressure Archetypes | **CONDITIONALLY VALIDATED** | Mutually exclusive 95%-CI classification; `50/89` batters and `56/82` bowlers remain `UNCLASSIFIED / INSUFFICIENT EVIDENCE` |
| Phase 6 & 7: Global Leaderboards & `100/300/12` Gate | **CONDITIONALLY VALIDATED** | `89` batters (`is_ball_faced`) & `82` bowlers (all delivery events); Track A & B kept strictly separate |
| Phase 9: Dashboard Integration | **VERIFIED** | Extended `dashboard/app.py` with engine selector (`V4.2` default preserved; `V5.0` 3-tab view) |
| Individual Pressure-Slope Ranking (`delta_pressure` alone) | **EXPERIMENTAL** | 50-split-half Spearman `0.2265` (batters), `0.1768` (bowlers) — noisy due to finite HP sample sizes |
| Unmatched / Mismatched Innings (`181 / 1,652`) | **BLOCKED (FROM TRACK A)** | Excluded from Track A score-aware modelling |

---

## 2. Key Empirical Metrics

- **Alpha Selection (1-SE Rule):** `alpha_main = 250.0`, `alpha_int = 4000.0`, `alpha_context = 250.0` (`pooled_oof_mse = 4.955498`, `oof_rmse = 2.226095`, `fold_mse_se = 0.050550`).
- **50-Split Reliability (Eligible Pool):**
  - Batters (`n = 89`): `main_spearman = 0.2751`, `pres_spearman = 0.2265`, `hp_spearman = 0.2790`, `top10_overlap = 5.48`, `top20_overlap = 8.98`.
  - Bowlers (`n = 82`): `main_spearman = 0.3523`, `pres_spearman = 0.1768`, `hp_spearman = 0.3631`, `top10_overlap = 3.64`, `top20_overlap = 8.68`.
- **Archetype Distribution (Eligible):**
  - Batters: `37` Elite Clutch Performer, `2` Crisis / Rescue Specialist, `50` Unclassified / Insufficient Evidence.
  - Bowlers: `19` Elite Clutch Performer, `4` Crisis / Rescue Specialist, `3` Below-Average Under Pressure, `56` Unclassified / Insufficient Evidence.
