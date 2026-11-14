# V3 Data Quality Audit & Semantics Report
**Document Code:** AGY-V3-DQA-001  
**Dataset Scope:** IPL & T20I (2022–2026)  
**Execution Date:** November 2026

---

## 1. Executive Summary

This audit establishes the empirical baseline for all 194,014 delivery records, 853 matches, 27,393 playing-eleven entries, and 6,086 player-mapping rows in the official dataset.

All numbers in this report are dynamically computed from the raw CSV source tables.

---

## 2. Match Cohort Accounting

| Metric | Empirical Count | Verification Note |
|---|---|---|
| **Total Source Matches** | 853 | All matches listed in `matches_ipl_t20i.csv` |
| **IPL Matches** | 371 | Filtered by `match_format == 'T20'` across IPL 2022–2026 |
| **T20I Matches** | 482 | Filtered by `match_format == 'T20I'` across international bilaterals/tournaments |
| **Matches with Ball-by-Ball Data** | 837 | Matches with $\ge 1$ delivery in `ball_by_ball_ipl_t20i.csv` |
| **Matches Missing Ball-by-Ball Data** | 16 | Match IDs: 31281, 31284, 31288, 32610, 32612, 32622, 36210, 36564, 38797, 40761, 41502, 41503, 42030, 46008, 48513, 50189 |
| **DLS / Revised Target Matches** | 23 | Matches where `revised_target > 0` |
| **Abandoned / No-Result Matches** | 24 | Matches where `result` is abandoned/no-result or `win_team_id` is null |
| **Super Over Matches** | 1 | Matches featuring Innings 3 or 4 deliveries |

---

## 3. Delivery-Level Semantics & Extras Audit

### 3.1 Delivery Volume Breakdown
- **Total Deliveries:** 194,014
- **Regular Innings (Innings 1 & 2):** 193,988
- **Super Over Deliveries (Innings 3 & 4):** 26 (quarantined from standard 20-over tactical ratings)

### 3.2 Extras Categorical Mapping (`extras1_runs`)
The field `extras1_runs` represents an integer enumeration code, not an integer run count:

| Code | Label (`EXTRAS_TYPE_MAP`) | Frequency | % of Deliveries | Mathematical Treatment |
|---|---|---:|---:|---|
| **1** | Overstep (No-Ball) | 565 | 0.29% | Ball faced by batter = True; Legal ball for bowler = False |
| **2** | Wide | 7,474 | 3.85% | Ball faced by batter = False; Legal ball for bowler = False |
| **3** | Legbyes | 2,661 | 1.37% | Ball faced by batter = True; Legal ball for bowler = True |
| **4** | Byes | 505 | 0.26% | Ball faced by batter = True; Legal ball for bowler = True |
| **5** | Other | 260 | 0.13% | Ball faced by batter = True; Legal ball for bowler = True |
| **6** | None (Normal Delivery) | 182,548 | 94.09% | Ball faced by batter = True; Legal ball for bowler = True |
| **7** | Penalty | 1 | <0.01% | Special administrative penalty event |

> [!CAUTION]
> Summing `extras1_runs` as numeric runs yields an absurd sum of 1,122,234 runs. It must strictly be processed as a categorical codebook.

### 3.3 Mystery Column: `extras_2_runs`
- Value `0`: 193,979 rows (99.982%)
- Value `1`: 19 rows (0.010%)
- Value `4`: 16 rows (0.008%)
- Total non-zero rows: 35 out of 194,014.
- **Audit Decision:** The documentation does not establish what these 35 non-zero entries represent (whether secondary penalty runs or miscoded overthrows). In accordance with Phase 1.1, all non-zero `extras_2_runs` records are quarantined.

### 3.4 `runs` Column Semantics
Cross-tabulation of `runs` against delivery types reveals:
- When `extras1_runs == 2` (Wide), `runs` is **strictly 0 across all 7,474 deliveries**.
- When `extras1_runs == 1` (Overstep), `runs` takes values `[0: 236, 1: 168, 4: 81, 6: 45, 2: 33, 3: 2]`, representing runs scored off the bat.
- **Definitive Finding:** The `runs` column records **batter runs off the bat**, not total delivery runs or bowler runs conceded. Total runs conceded cannot be derived by simply adding `runs` and `extras1_runs`.

---

## 4. Boundary Flag Discrepancies

An exhaustive check against `runs` and bat contact reveals:
- Deliveries where `runs == 4` but `is_four == False`: **20 occurrences**.
- Deliveries where `runs == 6` but `is_six == False`: **3 occurrences**.
- All 23 discrepancies occur on legitimate bat hits where `extras_category` is 'None' or 'Overstep'.
- **Remediation:** Derived fields `is_four_validated`, `is_six_validated`, and `boundary_validated` reconcile these occurrences while preserving original source columns untouched.

---

## 5. Dismissal & Wicket Attribution Audit

Total dismissals recorded (`is_wicket == True`): **10,486**.

| Dismissal Type | Raw Count | Credited to Bowler? | Tactical Treatment |
|---|---:|:---:|---|
| **Caught** | 7,332 | Yes | Bowler wicket |
| **Bowled** | 1,690 | Yes | Bowler wicket |
| **LBW** | 666 | Yes | Bowler wicket |
| **RunOut** | 573 | **No** | Non-bowler dismissal (fielding unit event) |
| **Stump** | 200 | Yes | Bowler wicket |
| **Hit Wicket** | 17 | Yes | Bowler wicket |
| **Retire Out** | 6 | **No** | Non-bowler dismissal (tactical substitution) |
| **Obstructing the field** | 1 | **No** | Non-bowler dismissal |
| **Obstracting the field (typo)** | 1 | **No** | Non-bowler dismissal |
| **Total Bowler Wickets** | **9,905** | — | Evaluated in bowling performance & hazard models |
| **Total Non-Bowler Dismissals**| **581** | — | Excluded from bowler wicket metrics |

- **Missing Player Attribution:** Exactly 1 delivery with `is_wicket == True` has a null `dismissed_player_id`.

---

## 6. Playing Eleven Conflicts

- Total rows in `playing_eleven_ipl_t20i.csv`: 27,393.
- Duplicate `(match_id, team_id, player_id)` combinations: **35 instances** across 3 matches (Match IDs 13613, 21176, 28962).
- **Resolution Rule:** Sorted by `batting_order` ascending and deduplicated keeping first (`keep='first'`), yielding 27,358 unique playing-XI entries.

---

## 7. Cohort Manifest Summary

The cohort manifest is generated at `data/reports/v3/MATCH_COHORT_MANIFEST.csv` and contains all 853 matches categorized as:
- `INCLUDED`: 790 matches
- `EXCLUDED` (Missing ball-by-ball): 16 matches
- `QUARANTINED_ABANDONED`: 24 matches
- `FLAGGED_DLS`: 23 matches
