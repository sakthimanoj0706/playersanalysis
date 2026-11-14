# V3 Match Pressure Model Validation Report
**Document Code:** AGY-V3-PMV-001  
**Execution Date:** November 2026  
**Status:** Validated, Ex-Ante, Zero Target Leakage

---

## 1. Executive Summary

The V3 Pressure Engine decouples the match context into two logically distinct, pre-delivery leverage models:
1. **Batting Crisis Pressure Model:** Quantifies the ex-ante risk of an innings collapse facing the batting side.
2. **Bowling Defensive Pressure Model:** Quantifies the ex-ante defensive pressure on the bowling side to suppress boundaries and defend against opponent resources.

Both models operate strictly on state observable *before* the bowler releases the ball, satisfying the zero target leakage requirement.

---

## 2. Mathematical Formulations

### 2.1 Batting Crisis Pressure ($P_{\text{bat}} \in [0, 10]$)
$$P_{\text{bat}} = \min\left(10.0, \, (C_{\text{wkt}} + C_{\text{cluster}} + C_{\text{novelty}} + C_{\text{stagnation}}) \times M_{\text{phase}}\right)$$

Where:
- **$C_{\text{wkt}} \in [0, 3.5]$:** Wicket depletion: $\min(3.5, 0.45 \times W_{\text{before}})$.
- **$C_{\text{cluster}} \in \{0.0, 0.75, 2.0\}$:** Recent collapse: $2.0$ if $\ge 2$ wickets in last 12 legal balls; $0.75$ if 1 wicket; else $0.0$.
- **$C_{\text{novelty}} \in [0, 1.5]$:** Entry vulnerability: $1.5 \times (1 - \text{BF}/5)$ for $\text{BF} < 5$; else $0.0$.
- **$C_{\text{stagnation}} \in [0, 1.5]$:** Dot ball accumulation: $\min(1.5, 0.3 \times \text{Dots}_{\text{consec}} + 0.6 \times \frac{\text{Dots}_{12}}{12})$.
- **$M_{\text{phase}}$:** Innings phase multiplier: Death = $1.25$, Middle = $1.00$, Powerplay = $0.95$.

### 2.2 Bowling Defensive Pressure ($P_{\text{bowl}} \in [0, 10]$)
$$P_{\text{bowl}} = \min\left(10.0, \, C_{\text{resource}} + C_{\text{phase}} + C_{\text{momentum}} + C_{\text{rotation}}\right)$$

Where:
- **$C_{\text{resource}} \in [0.2, 3.0]$:** Opponent wickets in hand: $3.0$ if $\ge 8$ wickets in hand; $2.0$ if 6–7; $1.0$ if 4–5; $0.2$ if 1–3.
- **$C_{\text{phase}} \in [1.0, 3.0]$:** Phase leverage: Death = $3.0$, Powerplay (field restrictions) = $2.0$, Middle = $1.0$.
- **$C_{\text{momentum}} \in [0.0, 2.5]$:** Opponent boundary momentum: $2.5$ if $\ge 3$ boundaries in last 12 balls; $1.6$ if 2; $0.8$ if 1; $0.0$ if 0.
- **$C_{\text{rotation}} \in [0.0, 1.5]$:** Strike-rotation pressure: $1.5 \times (1 - \frac{\text{Dots}_{12}}{12})$.

---

## 3. Empirical Distribution and Baseline Calibration

Across 193,988 regular deliveries:
- **Batting Crisis Tiers:**
  - High & Extreme ($\ge 5.5$): 15,464 balls (7.97% of deliveries)
  - Moderate ($[3.5, 5.5)$): 30,844 balls (15.90%)
  - Normal / Low ($< 3.5$): 147,680 balls (76.13%)
- **Bowling Defensive Tiers:**
  - High & Extreme ($\ge 6.5$): 101,935 balls (52.55% of deliveries)
  - Moderate ($[4.5, 6.5)$): 55,286 balls (28.50%)
  - Normal / Low ($< 4.5$): 36,767 balls (18.95%)

---

## 4. Verification and Leakage Audit
- **Pre-delivery Guarantee:** Every input feature is derived exclusively from historical balls prior to the active delivery sequence.
- **Independence Test:** Perturbing future balls, runs scored, or dismissal flags results in an identical pre-delivery pressure score ($0.0$ difference).
- **Target Leakage:** None detected.
