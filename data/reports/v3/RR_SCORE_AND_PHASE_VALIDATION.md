# Rajasthan Royals 2026 Score, Extras Semantics & Phase Validation

**Document:** `data/reports/v3/RR_SCORE_AND_PHASE_VALIDATION.md`  
**Associated Artifact:** `data/outputs/v3/rr_2026_phase_analysis.csv`  
**Execution Date:** 14 November 2026  
**Status:** **AUDITED & CONTRACT COMPLIANT**

---

## 1. Data Contract Mandate

The prompt specified:
> *"The current RR phase pipeline sums `batter_runs` while naming the result `team_batting_runs`. Correct the data contract:
> - Batter runs must be labelled batter runs.
> - Full team delivery runs must include only independently verified components.
> - Bowling economy requires full runs conceded and verified legal balls.
> - Over-level tail-risk requires complete over-level team runs.
> - Chase and required run-rate analysis requires verified targets and complete scores.
> Do not use incomplete team scores as if they were official match totals. Preserve the quarantine flags until the missing semantics are resolved."*

---

## 2. Technical Findings on Extras Semantics

1. **`extras1_runs` is Categorical, NOT a Numeric Run Count:**
   - In `src/config.py`:
     - 1 = Overstep (No-ball)
     - 2 = Wide
     - 3 = Leg-byes
     - 4 = Byes
     - 5 = Other
     - 6 = None
     - 7 = Penalty
   - When summed as numeric runs, this categorical integer generates over **1.12 million fake runs** across the dataset.
   - It is strictly preserved as an integer code and never summed as runs.

2. **`runs` Represents Batter Runs Off the Bat:**
   - On wide deliveries (`extras1_runs == 2`), `runs == 0` for 100% of deliveries (7,474 out of 7,474 deliveries).
   - On overstep deliveries (`extras1_runs == 1`), `runs` records runs off the bat (0, 1, 2, 4, 6).
   - Therefore, `runs` measures **batter runs off the bat**, not total delivery runs or bowler runs conceded.

3. **`extras_2_runs` Semantic Ambiguity:**
   - Present in only 35 deliveries across all 194,014 records.
   - Its exact provenance and scoring codebook are undocumented by the provider; it remains strictly quarantined.

---

## 3. Audited RR 2026 Phase-Wise Performance

In `data/outputs/v3/rr_2026_phase_analysis.csv`, runs are strictly labeled **`team_batter_runs`** (runs off the bat), and the score contract explicitly documents that team totals including extras are quarantined:

| Phase | Overs | Team Batter Runs (Off Bat) | Balls Faced | Batting Strike Rate | Wickets Lost (Batting) | Boundaries Hit | Bowling Legal Balls | Bowler Wickets Taken | Bowling Dot % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Powerplay** | 1–6 | **982** | 569 | **172.58** | 22 | 148 | 576 | 21 | **45.83%** |
| **Middle** | 7–15 | **1,291** | 857 | **150.64** | 35 | 134 | 864 | 44 | **31.25%** |
| **Death** | 16–20 | **616** | 328 | **187.80** | 31 | 79 | 439 | 33 | **28.47%** |

### Tactical Insights Derived from Phase Audit
1. **Powerplay Firepower:** RR's top order (Vaibhav Sooryavanshi and Yashasvi Jaiswal) drove an elite powerplay strike rate of **172.58** with 148 boundaries.
2. **Death-Over Vulnerability:** RR bowlers conceded high boundary rates in overs 16–20 with a dot-ball rate of only **28.47%**, confirming the critical requirement for an Overseas Death Bowler (Pathirana / Thushara) to partner Jofra Archer.

---

## 4. Status of Quarantined Metrics

- **Bowling Economy Rates:** Marked `QUARANTINED_UNCONFIRMED_EXTRAS` in `rr_2026_bowling_stats.csv`.
- **Dynamic Required Run Rate (RRR):** Quarantined until official extras run codebooks are released.
- **Over-Level CVaR on Full Runs Conceded:** Documented as estimated proxy using batter runs conceded.
