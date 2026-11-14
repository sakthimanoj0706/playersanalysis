# V3 Formula & Derivation Document: SupeRR Intelligence Platform
**Document Code:** AGY-V3-FORMULA-001  
**Project:** SupeRR Intelligence 2.0 -> V3  
**Target:** Rajasthan Royals SupeRR Selector Season 2 Hackathon  
**Release Version:** V3.0-Production Readiness  
**Date:** November 2026

---

## 1. Document Scope and Governance

This document provides the definitive mathematical definitions, derivations, assumptions, variable dictionaries, edge cases, and validation methods for every approved formula in SupeRR Intelligence V3.

In accordance with strict hackathon scientific standards:
- No formula is deemed approved merely because it executes without crashing.
- Every formula states its exact lineage, data fields used, numerical edge cases, and limitations.

---

## 2. Formula 1: Pre-Delivery Batting Crisis Pressure ($P_{\text{bat}}$)

### Purpose
Quantifies the ex-ante risk of a batting collapse facing the striker *before* the delivery is bowled.

### Mathematical Definition
$$P_{\text{bat}} = \min\left(10.0, \, (C_{\text{wkt}} + C_{\text{cluster}} + C_{\text{novelty}} + C_{\text{stagnation}}) \times M_{\text{phase}}\right)$$

Where:
- **$C_{\text{wkt}} = \min(3.5, \, 0.45 \times W_{\text{before}})$**: Wickets fallen in the innings before the delivery.
- **$C_{\text{cluster}}$**: Recent cluster collapse in the last 12 legal balls:
  $$C_{\text{cluster}} = \begin{cases} 2.0 & \text{if } W_{12} \ge 2 \\ 0.75 & \text{if } W_{12} = 1 \\ 0.0 & \text{otherwise} \end{cases}$$
- **$C_{\text{novelty}}$**: Striker entry vulnerability in first 5 balls faced:
  $$C_{\text{novelty}} = \begin{cases} 1.5 \times (1 - \text{BF}/5) & \text{if } \text{BF} < 5 \\ 0.0 & \text{if } \text{BF} \ge 5 \end{cases}$$
- **$C_{\text{stagnation}} = \min\left(1.5, \, 0.3 \times \text{Dots}_{\text{consec}} + 0.6 \times \frac{\text{Dots}_{12}}{12}\right)$**: Dot-ball pressure buildup.
- **$M_{\text{phase}}$**: Phase leverage multiplier: Death ($16-20$) = $1.25$, Middle ($7-15$) = $1.00$, Powerplay ($1-6$) = $0.95$.

### Variable Definitions
- $W_{\text{before}} \in \{0, 1, \dots, 9\}$: Cumulative dismissals before the active ball.
- $W_{12} \in \{0, 1, \dots\}$: Dismissals within the last 12 legal balls.
- $\text{BF} \in \{0, 1, \dots\}$: Balls faced by the active striker prior to this ball.
- $\text{Dots}_{\text{consec}}$: Consecutive dot balls in the innings immediately prior.
- $\text{Dots}_{12}$: Dot balls occurred within the preceding 12 legal deliveries.

### Edge Cases
- First delivery of the match: $W=0, W_{12}=0, \text{BF}=0, \text{Dots}=0 \implies (0 + 0 + 1.5 + 0) \times 0.95 = 1.425$ (None/Low pressure).
- 5 wickets down at Over 17.1 with a new batter: $W=5 (2.25), W_{12}=2 (2.0), \text{BF}=0 (1.5), \text{Dots}=4 (0.2) \implies (2.25+2.0+1.5+0.2)\times 1.25 = 7.4375$ (High/Extreme pressure).

---

## 3. Formula 2: Pre-Delivery Bowling Defensive Pressure ($P_{\text{bowl}}$)

### Purpose
Quantifies the ex-ante defensive challenge facing the bowler to suppress boundaries and defend match resources.

### Mathematical Definition
$$P_{\text{bowl}} = \min\left(10.0, \, C_{\text{resource}} + C_{\text{phase}} + C_{\text{momentum}} + C_{\text{rotation}}\right)$$

Where:
- **$C_{\text{resource}}$**: Batting side resources in hand ($W_{\text{rem}} = 10 - W_{\text{before}}$):
  $$C_{\text{resource}} = \begin{cases} 3.0 & \text{if } W_{\text{rem}} \ge 8 \\ 2.0 & \text{if } W_{\text{rem}} \in \{6, 7\} \\ 1.0 & \text{if } W_{\text{rem}} \in \{4, 5\} \\ 0.2 & \text{if } W_{\text{rem}} \le 3 \end{cases}$$
- **$C_{\text{phase}}$**: Fielding restriction and phase leverage: Death = $3.0$, Powerplay = $2.0$, Middle = $1.0$.
- **$C_{\text{momentum}}$**: Opponent boundaries in last 12 legal balls:
  $$C_{\text{momentum}} = \begin{cases} 2.5 & \text{if } B_{12} \ge 3 \\ 1.6 & \text{if } B_{12} = 2 \\ 0.8 & \text{if } B_{12} = 1 \\ 0.0 & \text{otherwise} \end{cases}$$
- **$C_{\text{rotation}} = \min\left(1.5, \, 1.5 \times (1 - \text{Dots}_{12}/12)\right)$**: Strike-rotation pressure.

---

## 4. Formula 3: Normal-Normal Empirical Bayes Shrinkage (Batting Strike Rate)

### Purpose
Shrinks individual sample strike rates towards empirical population means to prevent small-sample distortion.

### Mathematical Definition
$$\hat{\mu}_i = w_i \bar{Y}_i + (1 - w_i) \mu_0$$
Where:
$$w_i = \frac{n_i}{n_i + K_{\text{prior}}}$$
With prior strength parameter:
$$K_{\text{prior}} = \frac{\sigma_{\text{within}}^2}{\tau_{\text{between}}^2}$$
Estimated on historical training cohorts ($K_{\text{prior}} = 25.0$).

---

## 5. Formula 4: Beta-Binomial Empirical Bayes Shrinkage (Bowling Event Rates)

### Purpose
Shrinks rare binary event rates (wicket rate, dot rate) towards the empirical Beta prior.

### Mathematical Definition
$$\hat{p}_i = \frac{k_i + \alpha}{n_i + \alpha + \beta} \times 100$$
Where hyperparameters $\alpha, \beta$ are estimated via method-of-moments:
$$\mu_0 = \mathbb{E}[p], \quad \sigma_0^2 = \text{Var}(p)$$
$$M = \frac{\mu_0 (1 - \mu_0)}{\sigma_0^2} - 1$$
$$\alpha = \mu_0 M, \quad \beta = (1 - \mu_0) M$$

---

## 6. Formula 5: Exposure-Adjusted Match Consistency ($C$)

### Purpose
Scores multi-match reliability without clipping zero-consistency anomalies.

### Mathematical Definition
$$C_i = \exp(-\text{CV}_i) \cdot \sqrt{\frac{m_i}{m_i + 3.0}}$$
Where:
- $\text{CV}_i = \sigma_{\text{match}, i} / \mu_{\text{match}, i}$ is the coefficient of variation across matches.
- $m_i$ is the number of distinct matches in which the player faced pressure.

### Properties
- Strictly positive and bounded in $(0, 1]$.
- Penalizes erratic performances while rewarding sustained multi-match breadth.

---

## 7. Formula 6: Bowling Tail-Risk & Expected Shortfall ($\text{CVaR}_{90}$)

### Purpose
Measures extreme downside run leakage in catastrophic over spells.

### Mathematical Definition
$$\text{VaR}_{90}(Y) = \inf \left\{ y \in \mathbb{R} : P(Y \le y) \ge 0.90 \right\}$$
$$\text{CVaR}_{90}(Y) = \mathbb{E}\left[ Y \mid Y \ge \text{VaR}_{90}(Y) \right]$$
Where $Y$ is the verified batter runs conceded off the bat in a complete 6-ball legal over.

---

## 8. Formula 7: Discrete-Time Wicket Hazard Model

### Purpose
Estimates the conditional hazard of a bowler-creditable dismissal on delivery $t$.

### Mathematical Definition
$$\text{logit}(P(W_t = 1 \mid X_t)) = \beta_0 + \sum_{k} \beta_k X_{kt}$$
Where $X_t$ includes categorical phase indicators, format indicators, wickets fallen before, and pre-delivery crisis scores.
Excludes Run Outs, Retired Outs, and Obstructing the field.
