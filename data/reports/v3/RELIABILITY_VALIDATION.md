# V3 Reliability & Uncertainty Validation Report
**Document Code:** AGY-V3-REL-001  
**Execution Date:** November 2026  
**Status:** Validated, Match-Clustered Resampling & Empirical Bayes

---

## 1. Executive Summary

A critical flaw in naive cricket analytics is treating deliveries as independent identically distributed (i.i.d.) observations. Deliveries within a single match share strong latent covariates: pitch conditions, ground dimensions, weather, scoreboard pressure, and opponent bowling lineups.

The V3 Reliability Engine resolves this using:
1. **Match-Clustered Bootstrap Resampling:** Resampling entire matches rather than isolated balls, preserving within-match clustering and serial autocorrelation.
2. **Empirical Bayesian Shrinkage:** Shrinking observed individual estimates towards empirical population distributions with shrinkage weights proportional to exposure.

---

## 2. Match-Clustered Bootstrap Methodology

For a player with delivery records across $M$ distinct matches:
1. Resample $M$ match IDs with replacement $B = 1,000$ times.
2. For each bootstrap iteration $b$, concatenate all delivery outcomes from the sampled matches and compute the summary statistic $\hat{\theta}^{*b}$.
3. Construct non-parametric 95% confidence intervals from the 2.5th and 97.5th percentiles of $\{\hat{\theta}^{*b}\}_{b=1}^B$:
   $$\text{CI}_{95\%} = \left[ q_{0.025}, \, q_{0.975} \right]$$

---

## 3. Empirical Bayes Shrinkage Formulations

### 3.1 Normal-Normal Conjugate Shrinkage (Batting Strike Rate)
$$\hat{\mu}_i = w_i \bar{Y}_i + (1 - w_i) \mu_0$$
Where:
$$w_i = \frac{n_i}{n_i + K_{\text{prior}}}$$
With prior strength $K_{\text{prior}} = 25.0$ derived from the empirical ratio of within-player to between-player variance $\sigma_w^2 / \tau^2$.

### 3.2 Beta-Binomial Conjugate Shrinkage (Bowling Event Rates)
$$\hat{p}_i = \frac{k_i + \alpha}{n_i + \alpha + \beta} \times 100$$
Where hyperparameters $(\alpha, \beta)$ are estimated via method-of-moments on non-sparse historical cohorts:
$$\alpha = \mu_0 \left( \frac{\mu_0 (1 - \mu_0)}{\sigma_0^2} - 1 \right), \quad \beta = (1 - \mu_0) \left( \frac{\mu_0 (1 - \mu_0)}{\sigma_0^2} - 1 \right)$$
