# Pressure Reliability Index (PRI) Mathematical Methodology
**SupeRR Intelligence 2.0 — Scientific Governance & Statistical Specification**

---

## 1. Philosophical Formulation

In T20 cricket, cumulative metrics (total runs, aggregate wickets) are heavily confounded by batting order, role volume, and low-leverage exposure. True clutch performance is defined as **the capacity to sustain or elevate performance in high-leverage crisis match states relative to one's own normal baseline**.

The **Pressure Reliability Index (PRI)** is formulated as a multi-pillar composite index:

$$\text{PRI} = 100 \times \left( w_M \cdot M_{\text{norm}} + w_A \cdot A_{\text{norm}} + w_C \cdot C_{\text{norm}} + w_S \cdot S_{\text{norm}} \right)$$

Where:
- $M_{\text{norm}} \in [0, 1]$: Performance Maintenance Ratio (Crisis vs Normal Baseline).
- $A_{\text{norm}} \in [0, 1]$: Absolute Crisis Capability (Empirical Bayesian Shrunk).
- $C_{\text{norm}} \in [0, 1]$: Exposure-Adjusted Cross-Match Consistency.
- $S_{\text{norm}} \in [0, 1]$: Sample Size Confidence Penalty.

---

## 2. Dual Independent Pressure Paradigms

Batting and Bowling pressure are modeled independently to reflect their contrasting cricket mechanics:

### A. Batting Crisis Pressure Model
Measures batting-side crisis strictly pre-delivery:
- Wickets lost before delivery ($0 \dots 9$).
- Recent wicket cluster in the last 12 legal balls ($\ge 2$ wickets $\implies$ collapse).
- Batter novelty/vulnerability (first 5 deliveries faced).
- Dot-ball stagnation streak.
- Death over multiplier ($1.25\times$).

### B. Bowling Defensive Pressure Model
Measures bowler defensive challenge strictly pre-delivery:
- Batting team resource depth: wickets in hand ($10 - \text{wickets\_fallen\_before}$). When opponents have 8-10 wickets in hand, they attack freely.
- Critical match phase: Death overs (overs 16–20) and Powerplay (overs 1–6 with 2 boundary riders).
- Opponent boundary momentum: boundaries conceded in the last 12 legal balls.
- Run-flow rotation pressure: low dot balls in recent deliveries.

---

## 3. Tripartite Baseline Segmentation

Rather than grouping moderate pressure into normal play, deliveries are segmented into three explicit analytical tiers:
1. **Normal Baseline (None + Low):** Low-stress, routine match play.
2. **Moderate Pressure (Moderate):** Monitored independently as transition leverage.
3. **High/Extreme Crisis (High + Extreme):** High-leverage crisis situations.

Maintenance is calculated strictly as:
$$M_{\text{raw}} = \frac{\text{Metric}_{\text{Crisis}}}{\max(\text{Baseline}_{\text{floor}}, \text{Metric}_{\text{Normal}})}$$
Capped at $[0.5, 1.5]$ to prevent small normal-sample denominators from generating unearned infinite scores.

---

## 4. Empirical Bayesian Shrinkage

To eliminate small-sample noise without arbitrary heuristic damping, genuine Empirical Bayes shrinkage is implemented:

### For Batting Strike Rate (Normal-Normal Conjugate Model)
$$\hat{\theta}_i^{\text{EB}} = w_i \cdot \bar{X}_i + (1 - w_i) \cdot \mu_{\text{pop}}$$
$$w_i = \frac{n_i}{n_i + K}$$
Where $K = \sigma_{\text{within}}^2 / \tau_{\text{between}}^2$ represents the ratio of within-player sampling variance to between-player true variance, estimated empirically across all qualifying batters ($K = 25.0$).

### For Bowling Wicket Rate (Beta-Binomial Conjugate Model)
Prior: $p_i \sim \text{Beta}(\alpha, \beta)$ where parameters are estimated from the population mean $\mu$ and variance $V$ via Method of Moments:
$$M = \frac{\mu(1 - \mu)}{V} - 1, \quad \alpha = \mu \cdot M, \quad \beta = (1 - \mu) \cdot M$$
Posterior expected wicket rate per 100 legal balls:
$$\hat{p}_i^{\text{EB}} = \frac{k_i + \alpha}{n_i + \alpha + \beta} \times 100$$

---

## 5. Exposure-Adjusted Match Consistency Scoring

Previous approaches clipped $1 - \text{CV}$ to $[0, 1]$, which erroneously caused most bowlers to receive a $0.00$ consistency score due to the high natural match-to-match variance of wicket events.

SupeRR Intelligence 2.0 deploys an **exponential dispersion model with match breadth weighting**:
$$\text{Consistency}_i = \exp(-\text{CV}_i) \cdot \sqrt{\frac{m_i}{m_i + 3}}$$
Where:
- $\text{CV}_i = \sigma_i / \mu_i$ across all matches with crisis exposure.
- $\exp(-\text{CV}_i) \in (0, 1]$ is continuous, monotonic, and never collapses to zero.
- $\sqrt{m_i / (m_i + 3)}$ penalizes players with only 1 or 2 matches, requiring sustained multi-match reliability.

---

## 6. Sensitivity Analysis across Weighting Schemes

To ensure the rankings are statistically robust and not an artifact of arbitrary weights, the model evaluates 5 diverse weighting regimes:
1. **Balanced (Default):** $35\% M + 35\% A + 20\% C + 10\% S$
2. **Maintenance Heavy:** $50\% M + 25\% A + 15\% C + 10\% S$
3. **Absolute Heavy:** $25\% M + 50\% A + 15\% C + 10\% S$
4. **Consistency Heavy:** $30\% M + 30\% A + 30\% C + 10\% S$
5. **Equal Weights:** $25\% M + 25\% A + 25\% C + 25\% S$

Results are exported in `PRI_SENSITIVITY_ANALYSIS.csv`.
