# V3 Match Pressure Model Specification & Limitation Report (P1.1 Patch)
**Document Code:** AGY-V3-PMV-001  
**Execution Date:** 15 November 2026  
**Governance Status:** **`PROVISIONAL_POSITION_PROXY_HEURISTIC`** (Ex-Ante, Zero Target Leakage)

---

## 1. Executive Summary & Limitation Disclosure

The V3 Pressure Engine decouples match context into two logically distinct, pre-delivery heuristic scoring rules:
1. **Batting Crisis Pressure Model:** Quantifies pre-delivery collapse and stagnation state facing the batting side.
2. **Bowling Defensive Pressure Model:** Quantifies pre-delivery resource, phase, and momentum constraints on the bowling side.

Both models operate strictly on state observable *before* the bowler releases the ball (`0.0` target leakage) and quarantine any row with missing pre-delivery inputs (`batting_pressure_data_valid`, `bowling_pressure_data_valid`).

### Mandatory Pressure-Model Limitation Disclosure (`PROVISIONAL_POSITION_PROXY_HEURISTIC`)
- **Not a Calibrated Match-Leverage Model:** The current pressure model is a **position-proxy and pre-delivery state heuristic**, not an empirically fitted win-probability or match-leverage model.
- **Batting Position is a Proxy:** Modal batting position and wicket depletion serve as structural proxies for entry context, not direct calibrated evidence of match pressure.
- **Target, Required Run Rate (RRR), and Full Chase Leverage Not Yet Integrated:** Because `extras1_runs` in the raw dataset is a categorical codebook (codes 1–7) rather than numeric runs, reconstructed scoreboard totals, second-innings targets, and dynamic RRR remain quarantined.
- **Interpretation Constraint:** Current positional crisis distributions must **not** be presented as calibrated player-level crisis probabilities.

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

## 3. Empirical Distribution Across 193,988 Regular Deliveries

- **Batting Crisis Tiers (Mutually Exclusive):**
  - High & Extreme ($\ge 5.5$): 15,464 balls (7.97% of deliveries)
  - Moderate ($[3.5, 5.5)$): 30,760 balls (15.86%)
  - Normal / Low ($< 3.5$): 147,764 balls (76.17%)
  - Unclassified / Invalid Inputs: 0 balls (0.00%)
- **Bowling Defensive Tiers (Mutually Exclusive):**
  - High & Extreme ($\ge 6.5$): 101,935 balls (52.55% of deliveries)
  - Moderate ($[4.5, 6.5)$): 71,592 balls (36.91%)
  - Normal / Low ($< 4.5$): 20,461 balls (10.55%)
  - Unclassified / Invalid Inputs: 0 balls (0.00%)
  - *Impact on Bowler Normal Baseline:* Because only 10.55% of legal deliveries fall in the Normal/Low defensive tier ($< 4.5$), P1.1 enforces a separate **`MIN_NORMAL_BALLS = 100`** requirement for bowlers so that maintenance ratios are never computed on sparse normal baselines.

