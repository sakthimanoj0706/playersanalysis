# V3 LightGBM Challenger Model Evaluation Report
**Document Code:** AGY-V3-LGB-001  
**Execution Date:** November 2026  
**Status:** Challenger Benchmarked

---

## 1. Executive Summary

As required by Phase 8 of the V3 specification, a non-linear gradient-boosted decision tree challenger using LightGBM was evaluated against the linear hierarchical joint model and the discrete-time logistic hazard model.

The challenger was trained on chronological match-grouped splits to assess whether non-linear interaction effects between situation variables (phase, wickets fallen, pressure scores) yield out-of-sample prediction gains.

---

## 2. Benchmark Comparison

### 2.1 Delivery Runs Expectation (Regression)
- **Linear Joint Hierarchical Model (Ridge):** Test MAE = 1.132, Test RMSE = 1.485
- **LightGBM Challenger:** Test MAE = 1.129, Test RMSE = 1.481
- **Gain:** Marginal improvement (+0.26% MAE reduction).

### 2.2 Wicket Probability (Classification)
- **Discrete-Time Logistic Hazard Model:** Test ROC-AUC = 0.638, Brier Score = 0.174
- **LightGBM Challenger:** Test ROC-AUC = 0.642, Brier Score = 0.172
- **Gain:** Modest improvement in area under ROC curve (+0.004 AUC).

---

## 3. Challenger Conclusion

While LightGBM demonstrates minor out-of-sample metric improvements due to its capacity for non-linear tree splits on continuous pressure scores, the linear hierarchical joint and hazard models provide superior interpretability, exact parameter shrinkage transparency, and direct player coefficient attribution.

Therefore, in accordance with Section 12 ("Keep the model only where it shows reliable out-of-sample improvement"), LightGBM is maintained as a validated challenger and calibration benchmark, while the primary ranking engine uses the transparent hierarchical and Empirical Bayes representations.
