# V3 Universal Ranking Sample Eligibility & Threshold Sensitivity Audit (P1.1 Updated)

**Audit Identifier:** `V3-RANKING-INTEGRITY-001 / P1.1-PRE-SUBMISSION-CONSISTENCY-001`  
**Document Path:** `data/reports/v3/RANKING_ELIGIBILITY_AUDIT.md`  
**Associated Artifact:** `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv` (270 Grid Combinations)  
**Execution Date:** 15 November 2026  
**Status:** **`P1.1 PATCH VERIFIED — PROVISIONAL MODEL`**

> **Mandatory Disclosure:**
> "Rankings are provisional. Batter ranks 5, 6, 9 and 10 are sensitive to scoring weights. The pressure classification remains heuristic and position-proxy based. The new score has not yet undergone independent out-of-time validation."

---

## 1. Executive Summary & Objective

In legacy implementations, sample threshold cutoffs were hard-coded heuristics without empirical sensitivity validation, and bowlers could qualify for composite rankings with small normal-pressure baselines ($<100$ normal legal balls), inflating their dot-ball maintenance ratios.

Under **P1.1**, we enforce two major structural upgrades:
1. **Separate Bowler Normal-Baseline Requirement (`MIN_NORMAL_BALLS = 100`):** Every bowler must have $\ge 100$ normal-pressure legal deliveries (`norm_balls >= 100`) in addition to $\ge 120$ high-pressure legal deliveries and $\ge 5$ crisis matches. Bowlers with $< 100$ normal balls are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT`, their capped maintenance ratio and composite score are set to `NaN` (never imputed), and they are excluded from composite ranking.
2. **Extended Crisis-Ball Threshold Grid (`40, 60, 80, 100, 150, 200, 250`):** Combined with match-count thresholds (`5, 8, 10`) and normal/total ball grids (270 total combinations in `data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv`), reporting eligible batter count, eligible bowler count, available Top-10 count (never forcing 10 when $<10$ qualify), Top-10 overlap with baseline, Jaccard similarity, rank movement, and players entering/leaving.

---

## 2. Prespecified Threshold Grid Architecture (270 Total Combinations)

### 2.1 Primary Extended Crisis-Ball Sweep (`40, 60, 80, 100, 150, 200, 250` $\times$ `5, 8, 10` Matches)
- **Crisis Ball Grid:** `40, 60, 80, 100, 150, 200, 250` (plus `90, 120` in full bowling grid)
- **Crisis Match Grid:** `5, 8, 10`
- **Batting Baseline Ancillary Cutoffs:** `norm_balls >= 30`, `total_balls >= 120`
- **Bowling Baseline Ancillary Cutoffs:** `norm_balls >= 100` (`MIN_NORMAL_BALLS = 100`), `total_legal_balls >= 120`

---

## 3. Extended Crisis-Ball Sensitivity Findings (Match Threshold = 5)

| Crisis Balls Threshold | Eligible Batters | Available Bat Top-10 | Bat Overlap vs Baseline (`40`b) | Bat Jaccard Similarity | Bat Mean / Max Rank Shift | Batters Entering / Leaving | Eligible Bowlers (`norm>=100`) | Available Bowl Top-10 | Bowl Overlap vs Baseline (`120`b) | Bowl Jaccard Similarity | Bowl Mean / Max Rank Shift |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **40** *(Bat Baseline)* | **39** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 | Baseline | 40 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **60** | 21 | 10 | 5 / 10 | 0.3333 | 3.7 / 8 | **In:** Ramandeep Singh, Marcus Stoinis, Rinku Singh, Rahul Tewatia, Shimron Hetmyer<br>**Out:** Matthew Wade, Daryl Mitchell, David Miller, Iftikhar Ahmed, Jitesh Sharma | 40 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **80** | 11 | 10 | 1 / 10 | 0.0526 | 17.3 / 24 | Only MS Dhoni remains from baseline Top 10 | 40 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **100** | 8 | **8** *(unforced)* | 1 / 10 | 0.0588 | 20.0 / 30 | Only 8 batters eligible (MS Dhoni + 7 high-volume batters) | 39 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **120** *(Bowl Baseline)* | 6 | **6** *(unforced)* | 1 / 10 | 0.0667 | 22.8 / 32 | Only 6 batters eligible | **39** | **10** | **10 / 10** | **1.0000** | 0.0 / 0 |
| **150** | 0 | **0** *(unforced)* | 0 / 10 | 0.0000 | 0.0 / 0 | 0 batters eligible (max batter crisis balls = 133, MS Dhoni) | 39 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **200** | 0 | **0** *(unforced)* | 0 / 10 | 0.0000 | 0.0 / 0 | 0 batters eligible | 39 | 10 | 10 / 10 | 1.0000 | 0.0 / 0 |
| **250** | 0 | **0** *(unforced)* | 0 / 10 | 0.0000 | 0.0 / 0 | 0 batters eligible | 37 | 10 | 9 / 10 | 0.8182 | 0.9 / 1 |

### 3.1 Critical Stability & Governance Observations
1. **Low-Threshold Overlap Is Not Proof of High-Threshold Stability:** A `10/10` overlap at `40` crisis balls for batters is a baseline identity and **must not** be interpreted as stability across higher thresholds. Because batting crisis states (`>= 5.5` score) represent only 7.97% of regular deliveries, batter eligibility drops from 39 at `40` balls to 21 at `60` balls (`5/10` overlap, Jaccard `0.3333`), 11 at `80` balls (`1/10` overlap), 8 at `100` balls, and 0 at `>= 150` balls.
2. **Unforced Available Top-10 Counts:** Whenever fewer than 10 players meet a threshold (e.g., 8 batters at `100` crisis balls, 0 batters at `150+` crisis balls), `available_top10_count` reports the exact eligible count (`8`, `6`, `0`) without forcing ineligible players into the list.
3. **Bowler Normal-Baseline Reliability (`MIN_NORMAL_BALLS = 100`):** Out of 596 bowlers in `ALL_BOWLER_METRICS.csv`, 549 have `< 100` normal balls and are flagged `BOWLER_NORMAL_BASELINE_INSUFFICIENT` (including Craig Young [36], Obed McCoy [46], Mark Wood [62], Trent Boult [64], and Mark Adair [82]). Exactly 39 frontline bowlers satisfy all four gates (`crisis_balls >= 120`, `crisis_matches >= 5`, `norm_balls >= 100`, `total_legal_balls >= 120`, eligible bowling role), and their Top-10 membership remains `10/10` stable from `40` to `200` crisis balls (`9/10` at `250` crisis balls, where Keshav Maharaj [225 crisis balls] exits and Maheesh Theekshana enters).
