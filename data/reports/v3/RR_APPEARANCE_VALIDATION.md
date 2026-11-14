# Rajasthan Royals 2026 Player Appearance & Participation Audit

**Document:** `data/reports/v3/RR_APPEARANCE_VALIDATION.md`  
**Associated Artifact:** `data/outputs/v3/rr_2026_player_appearances.csv`  
**Execution Date:** 14 November 2026  
**Status:** **AUDITED & EMPIRICALLY VALIDATED (27 ROSTER PLAYERS)**

---

## 1. Audit Objective & Finding

The prompt highlighted an appearance discrepancy in the legacy pipeline:
> *"The current appearance output reports 16 appearances for many players, including Adam Milne. This must be checked against actual playing XI participation, impact-sub entries, verified substitute participation, and match-level participation."*

### Empirical Root Cause
In `data/playing_eleven_ipl_t20i.csv`, for every match that Rajasthan Royals played in IPL 2026 (16 matches: 14 league, Eliminator, Qualifier 2), **25 players** from the team roster were recorded in the sheet (400 total rows across 16 matches).
Legacy code performed:
```python
player_apps = rr_p11.groupby('player_id').agg(matches_selected=('match_id', 'nunique'))
```
This counted how many times a player was **listed in the match-day sheet** (`matches_selected = 16`), rather than whether the player actually entered the field of play.

---

## 2. Multi-Tier Appearance Taxonomy Defined

To ensure auditability, 6 distinct, verifiable fields were engineered from source records:

1. **`matches_selected`:** Number of matches where the player was listed in the official 25-player match squad sheet.
2. **`matches_starting_xi`:** Matches where the player started in the official Playing XI (`is_played == True` and `is_impact == 0` and `batting_order <= 11`).
3. **`matches_impact_sub`:** Matches where the player officially entered the match as a tactical Impact Player (`is_impact == 1`).
4. **`matches_played_overall`:** Total active match participation (`matches_starting_xi + matches_impact_sub`).
5. **`matches_batted`:** Matches where the player appeared at the crease as either striker or non-striker in `ball_by_ball_ipl_t20i.csv`.
6. **`matches_bowled`:** Matches where the player bowled at least 1 delivery in `ball_by_ball_ipl_t20i.csv`.

---

## 3. Verified RR 2026 Appearance Breakdown

| Canonical ID | Player Name | Squad Selected | Starting XI | Impact Sub | Matches Played Overall | Matches Batted | Matches Bowled | Audit Classification |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **6819** | Yashasvi Jaiswal | 16 | 16 | 0 | **16** | 16 | 0 | Regular Starting XI Opener |
| **7260** | Dhruv Jurel | 16 | 16 | 0 | **16** | 16 | 0 | Regular Starting XI Wicketkeeper |
| **3298** | Jofra Archer | 16 | 16 | 0 | **16** | 10 | 16 | Regular Starting XI Pace Spearhead |
| **50284** | Vaibhav Sooryavanshi | 16 | 12 | 4 | **16** | 16 | 0 | Top-Order Weapon (4x Impact Sub) |
| **8182** | Donovan Ferreira | 16 | 15 | 0 | **15** | 13 | 3 | Regular Starting XI Finisher |
| **152** | Ravindra Jadeja | 16 | 13 | 1 | **14** | 11 | 12 | Regular All-Rounder (1x Impact Sub) |
| **6423** | Riyan Parag | 16 | 14 | 0 | **14** | 14 | 4 | Captain & No. 4 Anchor |
| **7312** | Nandre Burger | 16 | 13 | 0 | **13** | 3 | 13 | Starting XI Pace Enforcer |
| **67036** | Brijesh Sharma | 16 | 13 | 0 | **13** | 2 | 13 | Starting XI Spin Control (Uncapped) |
| **7503** | Ravi Bishnoi | 16 | 6 | 3 | **9** | 2 | 9 | Rotational Leg-Spinner (7 games benched) |
| **3297** | Shimron Hetmyer | 16 | 8 | 0 | **8** | 7 | 0 | Middle Finisher (benched post-slump) |
| **41503** | Yash Punja | 16 | 7 | 1 | **8** | 0 | 8 | Squad Seamer Rotation |
| **2436** | Dasun Shanaka | 16 | 6 | 1 | **7** | 5 | 3 | Temporary Replacement for Sam Curran |
| **25139** | Shubham Dubey | 16 | 5 | 2 | **7** | 6 | 0 | Middle-Order Hitter Rotation |
| **6806** | Tushar Deshpande | 16 | 5 | 2 | **7** | 2 | 7 | Pacer Rotation |
| **2411** | Sandeep Sharma | 16 | 6 | 0 | **6** | 0 | 6 | Death Bowler (injured mid-season) |
| **7269** | Sushant Mishra | 16 | 1 | 1 | **2** | 1 | 2 | Backup Seamer |
| **43798** | Lhuan Pretorius | 16 | 2 | 0 | **2** | 2 | 0 | Overseas Development Batter |
| **1487** | **Adam Milne** | **16** | **1** | **0** | **1** | **1** | **1** | **Bench Reserve — Played Exactly 1 Match** |
| **60700** | Ravi Singh | 13 | 1 | 0 | **1** | 1 | 0 | Bench Reserve — Played 1 Match |
| **4409** | Sam Curran | 0 | 0 | 0 | **0** | 0 | 0 | Injured (Ruled out of season) |
| **7545** | Kuldeep Sen | 16 | 0 | 0 | **0** | 0 | 0 | Unplayed Squad Reserve |
| **8580** | Yudhvir Singh | 16 | 0 | 0 | **0** | 0 | 0 | Unplayed Squad Reserve |
| **26663** | Kwena Maphaka | 16 | 0 | 0 | **0** | 0 | 0 | Unplayed Overseas Reserve |
| **43965** | Emanjot Singh Chahal | 3 | 0 | 0 | **0** | 0 | 0 | Unplayed Squad Reserve |
| **47523** | Aman Rao Perala | 16 | 0 | 0 | **0** | 0 | 0 | Unplayed Squad Reserve |
| **48557** | Vignesh Puthur | 16 | 0 | 0 | **0** | 0 | 0 | Unplayed Squad Reserve |

---

## 4. Key Case Verifications

### 4.1 Adam Milne
- In match `50127`, Milne was in the squad list, but `is_played == False` and `batting_order` was NaN.
- In match `50133`, Milne played in the starting XI, bowled 3.2 overs (20 legal balls, 0 wickets, 3 dots), and faced 2 balls with the bat (2 runs, not out).
- Across all remaining 14 matches, Milne remained on the bench.
- **Audited Result:** `matches_selected = 16`, `matches_played_overall = 1`.

### 4.2 Vaibhav Sooryavanshi
- Started in the Playing XI in 12 matches (batting orders 1 or 2).
- Entered as a designated Impact Sub in 4 matches, batting in all 4 instances.
- **Audited Result:** `matches_selected = 16`, `matches_played_overall = 16`, `matches_batted = 16`.
