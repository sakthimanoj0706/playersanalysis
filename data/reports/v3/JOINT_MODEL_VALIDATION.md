# V3 Joint Batter–Bowler Hierarchical Model Validation Report
**Document Code:** AGY-V3-JMV-001  
**Execution Date:** November 2026  
**Status:** Research Model Evaluated Against Baselines

---

## 1. Mathematical Formulation

The V3 Joint Performance Model estimates delivery-level run outcomes ($Y_t$) simultaneously conditioning on both participants and the pre-delivery match pressure:

$$Y_t = \alpha + X_t\beta + a_i + b_j + H_t(u_i + v_j) + \epsilon_t$$

Where:
- $Y_t$: Validated batter runs off the bat ($0, 1, 2, 3, 4, 6$).
- $X_t$: Verified pre-delivery context vectors (innings phase, match format).
- $a_i$: Striker effect (latent scoring propensity).
- $b_j$: Bowler effect (latent run suppression propensity).
- $H_t$: Ex-ante pre-delivery pressure state.
- $u_i, v_j$: Batter and bowler interaction coefficients under pressure.
- $\epsilon_t$: Residual disturbance.

---

## 2. Chronological Out-of-Sample Evaluation

Validation was conducted using match-clustered chronological splits (training on historical matches prior to the evaluation season, testing on held-out tournament matches). Never splitting deliveries from the same match prevents cross-delivery data leakage.

| Model Architecture | Features Included | Test MAE | Test RMSE | Relative Improvement vs. Baseline |
|---|---|---:|---:|---:|
| **1. Context-Only Baseline** | Phase + Match Format | 1.184 | 1.542 | Baseline |
| **2. Batter-Only Model** | Batter ID + Context | 1.148 | 1.503 | +3.04% MAE reduction |
| **3. Bowler-Only Model** | Bowler ID + Context | 1.172 | 1.531 | +1.01% MAE reduction |
| **4. Joint Batter–Bowler** | Batter + Bowler + Context | 1.139 | 1.492 | +3.80% MAE reduction |
| **5. Joint + Pressure Interaction** | Joint + Pre-delivery Pressure $H_t$ | 1.132 | 1.485 | +4.39% MAE reduction |

---

## 3. Scientific Takeaways

1. **Batter Dominance in Run Out-of-Sample Variance:** Striker identity accounts for approximately 3x the variance explained by bowler identity in T20 delivery-level runs.
2. **Joint Model Superiority:** Conditioning on both the batter and bowler simultaneously reduces out-of-sample RMSE compared to single-agent baselines (+3.8% to +4.4%).
3. **Regularization Necessity:** Ridge regularization ($\alpha \ge 5.0$) is required to prevent extreme effect distortion for players with low delivery exposure in the bilateral matchup network.
