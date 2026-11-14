# SupeRR Intelligence 2.0: Pressure Reliability Analytics & Squad Scouting
## Participant Technical Methodology Report & Evidentiary Dossier
**Prepared for:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Scope:** Historical IPL & Men's T20I (2022 – 2026)  
**Deliverable Type:** Reproducible Analytics Methodology & Scouting System  
**System Status:** Research Prototype (Scientifically Defensible & Validated)

---

## 1. Dataset Scope & Data Governance Audit

The platform ingests the validated IPL and T20I dataset covering **853 matches** (837 with ball-by-ball delivery logs) and **193,988 regular deliveries** (26 Super Over balls quarantined).

### Key Data Limitations & Surgical Mitigations
1. **`extras1_runs` is Categorical, NOT a Run Count:** Integer codes (1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty) are mapped strictly as an enum. **Never summed as runs.**
2. **Score-Dependent Features are Quarantined:** Because total extras semantics remain unconfirmed by RR, derived team totals, required run rates, and bowler economy rates are withheld from primary ranking formulas to ensure zero false precision.
3. **Non-Bowler Dismissals are Filtered:** Run outs (571), retired outs (6), and obstructing the field (2) are strictly excluded from bowler wicket tallies. Only dismissals credited to bowler skill (Caught, Bowled, LBW, Stumped, Hit Wicket) are retained. Wickets occurring on wide deliveries (stumpings) are accurately attributed.
4. **Boundary Discrepancies Reconciled:** 23 flagged boundary anomalies (20 fours, 3 sixes) where `is_four`/`is_six` was false despite runs==4/6 off the bat have been audited and reconciled.
5. **Super Overs Quarantined:** Innings 3 and 4 (26 balls) are quarantined to prevent distortion of 20-over tactical ratings.

---

## 2. Dual Pressure Methodology

Batting crisis and bowling defensive pressure are fundamentally different cricket situations:
- **Batting Crisis Pressure:** High wickets lost before delivery, recent collapses, new batter entry vulnerability, dot-ball stagnation, and death-over leverage.
- **Bowling Defensive Pressure:** Opponent having wickets in hand (high resources), critical phase (death overs and powerplay field restrictions), and opponent boundary momentum in the last 12 balls.

All pressure indicators are calculated strictly from pre-delivery context to guarantee zero target leakage.

---

## 3. Tripartite Baseline Definitions

Rather than grouping moderate pressure into normal play, deliveries are segmented into three explicit analytical tiers:
1. **Normal Baseline (None + Low):** Routine, low-stress match play.
2. **Moderate Pressure (Moderate):** Transition leverage monitored independently.
3. **High/Extreme Crisis (High + Extreme):** High-leverage crisis situations.

---

## 4. Statistical Rating Mathematics & Empirical Bayes Shrinkage

$$\text{PRI} = 100 \times \left( 0.35 M_{\text{norm}} + 0.35 A_{\text{norm}} + 0.20 C_{\text{norm}} + 0.10 S_{\text{norm}} \right)$$

### Empirical Bayesian Shrinkage
- **Batting Strike Rate:** Normal-Normal conjugate Empirical Bayes model with between-player variance estimation ($K = 25.0$).
- **Bowling Wicket Rate:** Beta-Binomial conjugate Empirical Bayes model with Method-of-Moments prior estimation:
  $$\hat{p}_i^{\text{EB}} = \frac{k_i + \alpha}{n_i + \alpha + \beta} \times 100$$

### Exposure-Adjusted Match Consistency
$$\text{Consistency}_i = \exp(-\text{CV}_i) \cdot \sqrt{\frac{m_i}{m_i + 3}}$$
Continuous in $(0, 1]$, non-zero, and rewards sustained multi-match reliability.

---

## 5. Player Eligibility Criteria

- **Batters:** $\ge 40$ crisis balls, $\ge 120$ total balls, $\ge 5$ crisis matches, $\ge 30$ normal balls.
- **Bowlers:** $\ge 40$ crisis legal balls, $\ge 120$ total legal balls, $\ge 5$ crisis matches, $\ge 30$ normal legal balls.
Candidates falling below these thresholds are designated as `PROVISIONAL_SAMPLE` or `INSUFFICIENT_SAMPLE`.

---

## 6. Official Top 10 Batters Under Pressure

|   rank | player_name          |   crisis_balls |   crisis_matches |   crisis_sr |   norm_sr |   sr_maintenance |   consistency_score |   batting_pri |
|-------:|:---------------------|---------------:|-----------------:|------------:|----------:|-----------------:|--------------------:|--------------:|
|      1 | Namboori Tilak Varma |             60 |               18 |     196.667 |   144.473 |            1.361 |              0.512  |         91.3  |
|      2 | Matthew Wade         |             50 |               15 |     172     |   144.492 |            1.19  |              0.5018 |         74.76 |
|      3 | Gudakesh Motie       |             47 |               16 |     170.213 |   117.143 |            1.453 |              0.3703 |         74.59 |
|      4 | Daryl Mitchell       |             44 |               12 |     177.273 |   147.103 |            1.205 |              0.4266 |         70.26 |
|      5 | Liam Livingstone     |             60 |               14 |     175     |   161.295 |            1.085 |              0.4376 |         69    |
|      6 | Akeal Hosein         |            114 |               29 |     135.965 |   113.889 |            1.194 |              0.4847 |         68.23 |
|      7 | Mahendra Singh Dhoni |            133 |               35 |     154.887 |   140.94  |            1.099 |              0.3983 |         66.2  |
|      8 | Abdul Samad          |             69 |               23 |     169.565 |   168.675 |            1.005 |              0.4409 |         65.78 |
|      9 | Jaker Ali Anik       |             63 |               15 |     139.683 |   122.383 |            1.141 |              0.4874 |         64.19 |
|     10 | Ravindra Jadeja      |             94 |               33 |     150     |   138.728 |            1.081 |              0.4285 |         63.77 |

### Evidentiary Breakdown
1. **Namboori Tilak Varma (PRI 91.30):** Outstanding crisis accelerator (196.7 crisis SR vs 144.5 normal, 1.36x maintenance across 18 matches).
2. **Matthew Wade (PRI 74.76):** High-impact clutch finisher (172.0 crisis SR vs 144.5 normal across 15 matches).
3. **Gudakesh Motie (PRI 74.59):** Exceptional crisis striking (170.2 crisis SR vs 117.1 normal, 1.45x maintenance).
4. **Daryl Mitchell (PRI 70.26):** Consistent middle-order crisis weapon (177.3 crisis SR vs 147.1 normal).
5. **Mahendra Singh Dhoni (PRI 66.20):** Elite sample-backed finishing master (133 crisis balls across 35 matches, 154.9 crisis SR).
6. **Ravindra Jadeja (PRI 63.77):** Proven big-match crisis stabilizer (94 crisis balls, 150.0 crisis SR across 33 matches).

---

## 7. Official Top 10 Bowlers Under Pressure

|   rank | player_name        |   crisis_balls |   crisis_matches |   crisis_wicket_rate |   norm_wicket_rate |   crisis_dot_pct |   consistency_score |   bowling_pri |
|-------:|:-------------------|---------------:|-----------------:|---------------------:|-------------------:|-----------------:|--------------------:|--------------:|
|      1 | Mark Adair         |            483 |               40 |              6.62526 |            4.87805 |          37.06   |              0.5936 |         86.16 |
|      2 | Craig Young        |            289 |               23 |              8.99654 |            2.77778 |          36.3322 |              0.5086 |         86.1  |
|      3 | Harry Tector       |             54 |               10 |              9.25926 |            0       |          50      |              0.5315 |         86    |
|      4 | Mark Wood          |            156 |               13 |              9.61538 |            3.22581 |          41.6667 |              0.5114 |         77.94 |
|      5 | Obed McCoy         |            334 |               30 |              6.58683 |            4.34783 |          34.7305 |              0.5243 |         77.83 |
|      6 | Trent Boult        |            879 |               70 |              5.00569 |            1.5625  |          36.7463 |              0.5337 |         76.46 |
|      7 | Gareth Delany      |            178 |               24 |              6.74157 |            0       |          37.6404 |              0.3428 |         76.18 |
|      8 | Eshan Malinga      |            572 |               39 |              6.29371 |            2.22222 |          33.042  |              0.6118 |         73.67 |
|      9 | Jacob Duffy        |            486 |               39 |              7.81893 |            9.23077 |          40.7407 |              0.5771 |         73.13 |
|     10 | Krishnappa Gowtham |             67 |               10 |              7.46269 |            2.94118 |          44.7761 |              0.4922 |         72.66 |

### Evidentiary Breakdown
1. **Mark Adair (PRI 86.16):** Premier defensive crisis control (483 crisis balls, 37.1% dots, 0.59 consistency across 40 matches).
2. **Craig Young (PRI 86.10):** Exceptional crisis strike rate (9.0% crisis wicket rate vs 2.8% normal across 23 matches).
3. **Mark Wood (PRI 77.94):** Extreme high-pace strike weapon under crisis (9.6% crisis wicket rate, 41.7% dots).
4. **Obed McCoy (PRI 77.83):** Proven death-overs variation specialist (334 crisis balls, 34.7% dots, 6.6% wicket rate across 30 matches).
5. **Trent Boult (PRI 76.46):** Premier international opening and death weapon (879 crisis balls across 70 matches, 36.7% dots, 0.53 consistency).
6. **Jacob Duffy (PRI 73.13):** High-volume crisis workhorse (486 crisis balls, 40.7% dots across 39 matches).

---

## 8. Ranking Sensitivity Analysis
Rankings were evaluated across 5 diverse weighting regimes (Balanced, Maintenance Heavy, Absolute Heavy, Consistency Heavy, Equal Weights). Correlation among eligible players exceeds $r = 0.88$, demonstrating high mathematical stability.

---

## 9. Rajasthan Royals Tactical Squad Scouting

### Key Recommendations
- **Explosive No. 4/5 Batter:** **Rajat Patidar** (SR 171.6, 23.1% boundaries, 1,069 runs) is the premier Indian candidate. **Tim David** (SR 186.0) leads overseas finishers.
- **Experienced Indian Fast Bowlers:** **Arshdeep Singh** (192 wickets, 37.9% dots), **Bhuvneshwar Kumar** (115 wickets, 40.5% dots), and **Prasidh Krishna** (69 wickets, 40.2% dots).
- **Phase Specialists:** Bhuvneshwar Kumar (50.4% powerplay dots) and Arshdeep Singh (86 death wickets).
- **Spin Support for Jadeja & Bishnoi:** **Varun Chakravarthy** (135 wickets, SR 15.8) and **Kuldeep Yadav** (Left-arm chinaman) create a multi-dimensional spin trident.
- **Batting Combinations:** Verified delivery records confirm **Ravindra Jadeja & Donovan Ferreira** have batted together for **135 deliveries, scoring 210 runs at a combined SR of 155.56**, proving high tactical synergy at the death.

---

## 10. Reproducibility Instructions
```powershell
# 1. Run unit tests
python -m pytest tests/ -v

# 2. Recompute full pipeline
python scripts/build_context.py
python scripts/compute_cricket_stats.py
python scripts/compute_rankings.py
python scripts/run_scouting.py
python src/reporting/report_generator.py

# 3. Launch Dashboard
streamlit run dashboard/app.py
```
