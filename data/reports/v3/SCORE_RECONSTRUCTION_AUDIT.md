# Score Reconstruction Audit & Quarantine Policy
**Document Code:** AGY-V3-SRA-001  
**Status:** Quarantined for Unverified Runs  
**Date:** November 2026

---

## 1. Objective and Scope

This audit evaluates the mathematical feasibility of reconstructing complete innings scores, target progressions, chase requirements (RRR), bowler economy rates, and over-level run totals from the delivery records in `ball_by_ball_ipl_t20i.csv`.

---

## 2. Findings on Run Semantics

### 2.1 The `runs` Column
The raw column `runs` records the runs attributed to the striker off the bat:
- Over 7,474 wide deliveries, `runs == 0` for 100% of deliveries.
- Over 565 no-balls (Overstep), `runs` varies from 0 to 6 representing batter runs off the no-ball delivery.
- On byes and legbyes, `runs` records 0.

### 2.2 Extras Representation
- `extras1_runs` is an integer category code (`1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty`).
- It does **not** specify how many runs were scored on the extra. For instance, code `2` indicates a wide was bowled, but does not indicate whether it was 1 wide run, 2 wide runs (wide + single), or 5 wide runs (wide + boundary).
- Similarly, code `1` denotes an overstep, but does not state whether the penalty run is recorded in a separate table.
- `extras_2_runs` contains non-zero entries in only 35 deliveries out of 194,014, and its exact meaning is unverified in official provider documentation.

---

## 3. Mathematical Implications

Because the exact number of extras runs per delivery cannot be inferred from categorical codes alone without external official scorecards:

1. **Innings Total Runs:**
   $$\text{Innings Total} = \sum \text{batter\_runs} + \sum \text{actual\_extras\_runs}$$
   Since $\text{actual\_extras\_runs}$ is unavailable, calculating innings totals by adding `runs + extras1_runs` results in massive error (over 1 million extra runs).
2. **Bowler Economy Rate:**
   $$\text{Economy} = \frac{\text{Runs Conceded}}{\text{Legal Overs Bowled}}$$
   Runs conceded by a bowler must include wides and no-balls, but exclude legbyes and byes. Without verified wide run counts, reconstructed bowling economy is scientifically unverified.
3. **Required Run Rate (RRR) & Win Probability in Chases:**
   Calculating required run rate requires:
   $$\text{RRR}_t = \frac{\text{Target} - \text{Current Team Score}_t}{\text{Overs Remaining}_t}$$
   Without verified cumulative team scores, dynamic RRR cannot be accurately computed.

---

## 4. Formal Quarantine Policy for V3

In accordance with strict hackathon governance and Section 5 of the specification:

1. **Quarantined Metrics:**
   - Dynamically derived Bowler Economy Rate from delivery logs.
   - Dynamically derived Required Run Rate (RRR).
   - Dynamically derived Team Chase Win Probability dependent on reconstructed scores.
   - Over-level 15+ run tail-risk definitions that rely on summing unverified extras.
2. **Permitted Score-Independent Metrics:**
   - Batter runs scored, balls faced, strike rate, boundaries, boundary percentage.
   - Bowler legal balls bowled, dot ball percentage, boundary percentage conceded.
   - Bowler-creditable wickets, wicket rates, phase exposure.
   - Batting crisis pressure (resource depletion, cluster collapse, stagnation, novelty).
   - Bowling defensive pressure (batting resource depth, field restrictions, boundary momentum, dot pressure).
3. **User-Provided Reference Figures:**
   - Where Rajasthan Royals or tournament organisers supply official season summary figures (e.g., Archer 25 wickets, economy 9.31), these figures are stored under `data/reference/` and explicitly labeled `USER_PROVIDED_REFERENCE`.
   - They are never combined with derived metrics without explicit provenance labels.
