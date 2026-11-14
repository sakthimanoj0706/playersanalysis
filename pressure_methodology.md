# Cricket Pressure Methodology & Classification Framework

**Rajasthan Royals SupeRR Selector Season 2 Hackathon**  
**Methodological Foundation: Independent Dual Pre-Delivery Pressure Models**

---

## 1. Philosophical Grounding: Batting vs. Bowling Pressure Dichotomy

A central flaw in conventional cricket analysis is treating "pressure" as a single symmetric match attribute. In reality, batting pressure and bowling pressure are distinct, often inverse cricket situations:

- **Batting Pressure (Crisis Situations):**  
  Occurs when the batting side experiences wicket depletion, rapid collapse clusters, or requires new batters to enter under acute adversity. The batting side has limited resources, forcing survival alongside run production.
  
- **Bowling Pressure (Defensive Situations):**  
  Occurs when the opposing team holds surplus wickets in hand (8–10 wickets remaining) with the freedom to attack, in high-scoring match phases (death overs and powerplay field restrictions), or during boundary momentum streaks.

> [!IMPORTANT]
> A bowler operating when the batting side has already collapsed to $30/5$ in the 6th over is operating in a comfortable attacking situation with massive cushion, NOT under intense defensive pressure. Conversely, defending against an opponent at $170/2$ in the 18th over represents extreme defensive leverage.

---

## 2. Model 1: Batting Crisis Pressure Engine (`BattingPressureEngine`)

Calculates a pre-delivery crisis score ($0.0$ to $10.0$):
$$\text{Crisis Score} = (W_{\text{depletion}} + W_{\text{cluster}} + V_{\text{entry}} + S_{\text{stagnation}}) \times P_{\text{phase}}$$

1. **Wicket Depletion ($0.0$ to $3.5$ pts):**  
   Linear scaling with wickets lost before delivery: $\min(3.5, \text{wickets\_fallen\_before} \times 0.45)$.
2. **Wicket Cluster Collapse ($0.0$ to $2.0$ pts):**  
   Evaluates wickets lost in the preceding 12 legal balls:
   - $2+$ wickets in last 12 balls: $+2.0$ pts (collapse state).
   - $1$ wicket in last 12 balls: $+0.75$ pts.
3. **Batter Entry Vulnerability ($0.0$ to $1.5$ pts):**  
   Decaying vulnerability curve over the batter's first 5 balls faced: $\max(0.0, 1.5 - \text{balls\_faced} \times 0.30)$.
4. **Scoring Stagnation ($0.0$ to $1.5$ pts):**  
   Proportion of dot balls faced in the last 12 legal deliveries: $1.5 \times (\text{dots\_in\_last\_12} / 12.0)$.
5. **Phase Multiplier ($P_{\text{phase}}$):**  
   - Death Overs (Overs 16–20): $1.25\times$
   - Middle Overs (Overs 7–15): $1.00\times$
   - Powerplay (Overs 1–6): $0.95\times$

---

## 3. Model 2: Bowling Defensive Pressure Engine (`BowlingPressureEngine`)

Calculates a pre-delivery defensive leverage score ($0.0$ to $10.0$):
$$\text{Defensive Score} = R_{\text{resource}} + P_{\text{phase\_base}} + M_{\text{momentum}} + R_{\text{runflow}}$$

1. **Batting Resource Threat ($0.0$ to $3.0$ pts):**  
   Evaluates opponent wickets in hand ($\text{batting\_wickets\_remaining}$):
   - $8–10$ wickets in hand: $3.0$ pts (opponent has maximum batting resources).
   - $6–7$ wickets in hand: $2.0$ pts.
   - $4–5$ wickets in hand: $1.0$ pt.
   - $1–3$ wickets in hand: $0.2$ pts (cushioned situation).
2. **Phase Base Leverage ($1.0$ to $3.0$ pts):**  
   - Death overs (Overs 16–20): $3.0$ pts.
   - Powerplay overs (Overs 1–6, field restrictions): $2.0$ pts.
   - Middle overs (Overs 7–15): $1.0$ pt.
3. **Opponent Boundary Momentum ($0.0$ to $2.5$ pts):**  
   Boundaries conceded in the last 12 legal deliveries:
   - $3+$ boundaries: $2.5$ pts.
   - $2$ boundaries: $1.6$ pts.
   - $1$ boundary: $0.8$ pts.
4. **Run-Flow / Strike Rotation Pressure ($0.0$ to $1.5$ pts):**  
   Absence of dot balls in the preceding 12 legal balls: $1.5 \times (1.0 - \text{dots\_in\_last\_12} / 12.0)$.

---

## 4. Pre-Delivery Integrity: Zero Target Leakage

Every feature in both models is computed strictly prior to the delivery being bowled:
- Current ball runs, boundaries, dot ball outcome, and dismissal flags are **never** utilized to determine pre-delivery pressure.
- This ensures rigorous mathematical integrity and prevents circular target leakage.

---

## 5. Tripartite Baseline Segmentation

Matches are segmented into three distinct operational states:
1. **Normal Baseline (None + Low tiers):** Unconstrained conditions where players execute standard tactics.
2. **Moderate Pressure (Moderate tier):** Transitional leverage situations kept isolated to avoid contaminating either baseline or high-leverage pools.
3. **High Pressure (High + Extreme tiers):** Acute high-leverage situations where true reliability is tested.

### Empirical Validation Distribution
| Tier | Batting Deliveries | Batting Share | Batting Avg Runs | Batting Wkt % | Bowling Deliveries | Bowling Share | Bowling Avg Runs | Bowling Bound % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **None** | 75,924 | 39.1% | 1.45 | 4.80% | 1,470 | 0.8% | 0.85 | 9.18% |
| **Low** | 71,840 | 37.0% | 1.34 | 5.16% | 18,991 | 9.8% | 1.08 | 11.59% |
| **Moderate** | 30,760 | 15.9% | 1.23 | 5.89% | 71,592 | 36.9% | 1.25 | 15.61% |
| **High** | 11,445 | 5.9% | 1.15 | 7.71% | 70,591 | 36.4% | 1.43 | 19.61% |
| **Extreme** | 4,019 | 2.1% | 0.99 | 10.72% | 31,344 | 16.2% | 1.57 | 24.54% |
| **Total** | **193,988** | **100.0%** | — | — | **193,988** | **100.0%** | — | — |

**Behavioral Proof:**  
As Batting Crisis escalates from None to Extreme, run scoring drops from $1.45$ to $0.99$ runs/ball while wicket probability more than doubles from $4.80\%$ to $10.72\%$. Conversely, as Bowling Defensive Pressure escalates from None to Extreme, opponent scoring accelerates from $0.85$ to $1.57$ runs/ball and boundary rate climbs from $9.18\%$ to $24.54\%$.
