# V3 Bowling Tail-Risk & Pareto Analysis Report
**Document Code:** AGY-V3-TRV-001  
**Execution Date:** November 2026  
**Status:** Validated, Multi-Objective Optimization

---

## 1. Executive Summary

Standard bowling statistics (average, dot percentage) measure expected values but fail to penalize catastrophic high-variance spells. A single expensive 20-run over in the death phase frequently flips T20 match win probabilities.

The V3 Tail-Risk Analyzer models upper-tail loss distributions using:
1. **Value-at-Risk ($\text{VaR}_{90}$):** The 90th percentile of runs conceded in an over.
2. **Conditional Value-at-Risk ($\text{CVaR}_{90}$ / Expected Shortfall):** The conditional expectation of runs conceded when an over breaches the 90th percentile:
   $$\text{CVaR}_{90} = \mathbb{E}\left[ Y \mid Y \ge \text{VaR}_{90}(Y) \right]$$
3. **Multi-Objective Pareto Analysis:** Identifying non-dominated bowlers simultaneously optimizing:
   - Run suppression ($\text{Dot\%} \uparrow$)
   - Wicket threat ($\text{Wicket\%} \uparrow$)
   - Catastrophic tail risk ($\text{CVaR}_{90} \downarrow$)

---

## 2. Score Semantics Governance Disclosure

Because raw `extras1_runs` represents categorical code enums and total delivery extras remain unconfirmed, over-level run sums are evaluated **strictly on verified batter-runs-off-the-bat** or on boundary event rates ($\ge 2$ boundaries per over). Derived metrics avoid adding unverified extras runs.

---

## 3. Pareto Frontier Dynamics

A bowler $A$ Pareto-dominates bowler $B$ if:
$$\text{Dot\%}_A \ge \text{Dot\%}_B \quad \land \quad \text{Wkt\%}_A \ge \text{Wkt\%}_B \quad \land \quad \text{CVaR}_A \le \text{CVaR}_B$$
with at least one strict inequality.

- Frontline bowlers located on the empirical Pareto frontier (e.g., Trent Boult, Jasprit Bumrah) maintain elite dot ball percentages while constraining catastrophic 90th percentile over leakage.
- Bowlers with high raw wicket counts but extreme $\text{CVaR}_{90}$ (e.g. conceding 16+ runs in their worst spells) are flagged with high tail risk.
