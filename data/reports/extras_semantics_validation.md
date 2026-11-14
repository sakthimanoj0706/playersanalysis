# Extras Semantics & Score Reconstruction Validation Report

**Rajasthan Royals SupeRR Selector Season 2 Hackathon**  
**Engineering Audit: Delivery Fields, Extras Encodings & Score Reconstruction Feasibility**

---

## 1. Executive Summary

This audit investigates the delivery-level dataset to evaluate whether complete innings team scores, match targets, required run rates (RRR), and exact bowler economy rates can be reconstructed from the supplied files without unverified assumptions.

**Core Audit Finding:**  
`extras1_runs` is **categorically encoded** as an integer enum representing the type of extra, NOT the number of runs scored. Furthermore, the `runs` column records only off-the-bat runs scored by the striker and is strictly `0` on wide deliveries, byes, and legbyes. Consequently, the actual numeric run amounts resulting from extras (e.g. 1-run wide penalties, 4-run overthrows on wides, legbye boundary runs) are absent from the dataset.

Any calculation attempting to sum `extras1_runs` or infer exact team score totals would inject massive false precision. Therefore, score-dependent metrics are quarantined, and the platform relies strictly on verified observable proxies.

---

## 2. Empirical Verification of Delivery Fields

Across all **193,988 regular deliveries** analyzed:

### A. The Categorical Encoding of `extras1_runs`
Cross-tabulation of `extras1_runs` against `extras_type` confirms an exact 1-to-1 categorical mapping:

| `extras1_runs` Integer Code | `extras_type` String Label | Total Deliveries in Scope | Share of Dataset | Cricket Meaning |
| :---: | :--- | :---: | :---: | :--- |
| **1** | `Overstep` | 565 | 0.29% | No-ball overstep |
| **2** | `wide` | 7,472 | 3.85% | Wide delivery |
| **3** | `legbyes` | 2,661 | 1.37% | Leg-byes |
| **4** | `byes` | 505 | 0.26% | Byes |
| **5** | `other` | 259 | 0.13% | Other extras |
| **6** | `None` | 182,525 | 94.09% | Clean delivery (no extras) |
| **7** | `Penalty` | 1 | 0.00% | Penalty runs event |

> [!CAUTION]
> If a pipeline blindly sums `extras1_runs` assuming it represents runs scored, it adds $6 \text{ runs} \times 182,525 = 1,095,150$ phantom runs to clean deliveries alone!

### B. Behavior of `runs` on Extras Deliveries
- **Wide Deliveries ($N = 7,472$):** Exactly $100.0\%$ have $\text{runs} = 0$.
- **Bye Deliveries ($N = 505$):** Exactly $100.0\%$ have $\text{runs} = 0$.
- **Leg-Bye Deliveries ($N = 2,661$):** Exactly $100.0\%$ have $\text{runs} = 0$.

This demonstrates that `runs` is strictly **batter runs off the bat**, and team extras runs were never tabulated into `runs`.

### C. Undocumented Status of `extras_2_runs`
- In $193,953$ deliveries ($99.98\%$), `extras_2_runs` is `0`.
- In 19 deliveries, it is `1`. In 16 deliveries, it is `4`.
- It lacks documentation in `DATA_DICTIONARY_AND_AUDIT.md` and cannot serve as a reliable source of total extras.

---

## 3. Score Reconstruction Feasibility & Quarantine

| Metric | Reconstruction Feasibility | Audit Status | Mitigation / Strategy |
| :--- | :---: | :---: | :--- |
| **Batter Runs & Strike Rate** | 100% Verified | `APPROVED` | Computed directly from `runs` and `is_ball_faced`. |
| **Bowler Wickets & Dot Ball %** | 100% Verified | `APPROVED` | Computed from bowler-attributed dismissals and dot ball flags. |
| **Cumulative Innings Team Score** | Infeasible | `QUARANTINED` | Cannot determine wide/bye/no-ball run values without RR codebook. |
| **Required Run Rate (RRR)** | Infeasible | `QUARANTINED` | Target cannot be verified without complete first-innings score. |
| **Exact Bowler Economy Rate** | Infeasible | `QUARANTINED` | Runs conceded cannot be determined on wide/no-ball deliveries. |

---

## 4. Architectural Mitigation: Observable Pre-Delivery Proxies

Rather than inventing missing extras or fabricating required run rates, **SupeRR Intelligence 2.0** uses observable pre-delivery match context:
1. **Batting Crisis Pressure Proxy:** Measures wickets lost before delivery, 12-legal-ball wicket clusters, unfamiliar entry vulnerability, wicket recency, and death-overs urgency.
2. **Bowling Defensive Pressure Proxy:** Measures opponent wickets in hand (8-10 wickets remaining), critical phase defense (powerplay/death), opponent boundary momentum in the last 12 legal balls, and bowler spell fatigue.

These observable match states are $100\%$ verified from the raw records with zero target leakage.
