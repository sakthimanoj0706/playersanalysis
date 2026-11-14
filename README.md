# SupeRR Intelligence 2.0 👑
### Rajasthan Royals SupeRR Selector Season 2 — Pressure Reliability & Squad Scouting Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/pytest-17%20passed-success.svg)](tests/)
[![Dataset](https://img.shields.io/badge/data-IPL%20%2B%20T20I%20(2022--2026)-magenta.svg)](data/)
[![Dashboard](https://img.shields.io/badge/streamlit-research--prototype-pink.svg)](dashboard/)

**SupeRR Intelligence 2.0** is an audited, scientifically defensible cricket pressure reliability analytics and tactical squad scouting platform engineered for Rajasthan Royals' SupeRR Selector Season 2 Hackathon.

---

## 📌 Core Hackathon Mandate & Deliverables

1. **Top 10 Batters Under Pressure:** Benchmarked strictly against each batter's own unconstrained normal baseline using the **Pressure Reliability Index (PRI)**.
2. **Top 10 Bowlers Under Pressure:** Evaluated on dot-ball retention and wicket-taking rate during high-leverage defensive match situations.
3. **Dual Pre-Delivery Pressure Models:** Independent observable proxies for **Batting Crisis Pressure** (wickets lost, collapse clusters, unfamiliar entry) and **Bowling Defensive Pressure** (surplus opponent wickets, death/powerplay defense, boundary momentum streaks) with strictly zero target leakage.
4. **Tripartite Baseline Segmentation:** Rigorous 3-way isolation of unconstrained conditions (None + Low, 76.2% batting), transitional leverage (Moderate, 15.9%), and true high-leverage crises (High + Extreme, 7.97%).
5. **Rajasthan Royals Tactical Squad Scouting:** Separate squad gap analysis evaluating explosive No. 4/5 middle-order power, experienced Indian pace, phase specialists, and complementary spin support for Ravindra Jadeja and Ravi Bishnoi.
6. **Interactive Analytics Dashboard:** Streamlit application with dynamic data-driven cards, dual pressure breakdowns, sensitivity analysis, and tactical dossiers.
7. **Participant Technical Methodology Report:** 3-page publication-grade PDF and comprehensive Markdown report detailing the mathematical formulation, Empirical Bayes derivations, and data governance audit.

---

## 🏆 Official Final Top 10 Rankings

### 🏏 Batters Under Pressure (High-Leverage Crisis)
*Eligibility: $\ge 40$ crisis balls, $\ge 120$ total balls, $\ge 5$ crisis matches, $\ge 30$ normal balls. Includes all eligible players regardless of nominal role.*

| Rank | Player Name | Tactical Role | Crisis Balls | Crisis Matches | Crisis SR | Normal SR | Maintenance Ratio | Match Consistency | Final Batting PRI |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Namboori Tilak Varma** | Middle-Order Batter | 60 | 18 | 196.7 | 144.5 | 1.36x | 0.51 | **91.30** |
| **2** | **Matthew Wade** | Finisher / All-Rounder | 50 | 15 | 172.0 | 144.5 | 1.19x | 0.50 | **74.76** |
| **3** | **Gudakesh Motie** | Lower-Order / Bowler | 47 | 16 | 170.2 | 117.1 | 1.45x | 0.37 | **74.59** |
| **4** | **Daryl Mitchell** | Middle-Order Batter | 44 | 12 | 177.3 | 147.1 | 1.20x | 0.43 | **70.26** |
| **5** | **Liam Livingstone** | Middle-Order Batter | 60 | 14 | 175.0 | 161.3 | 1.09x | 0.44 | **69.00** |
| **6** | **Akeal Hosein** | Lower-Order / Bowler | 114 | 29 | 136.0 | 113.9 | 1.19x | 0.48 | **68.23** |
| **7** | **Mahendra Singh Dhoni** | Finisher / All-Rounder | 133 | 35 | 154.9 | 140.9 | 1.10x | 0.40 | **66.20** |
| **8** | **Abdul Samad** | Finisher / All-Rounder | 69 | 23 | 169.6 | 168.7 | 1.01x | 0.44 | **65.78** |
| **9** | **Jaker Ali Anik** | Middle-Order Batter | 63 | 15 | 139.7 | 122.4 | 1.14x | 0.49 | **64.19** |
| **10** | **Ravindra Jadeja** | Finisher / All-Rounder | 94 | 33 | 150.0 | 138.7 | 1.08x | 0.43 | **63.77** |

---

### 🎯 Bowlers Under Pressure (High-Leverage Defensive Leverage)
*Eligibility: $\ge 40$ crisis balls, $\ge 120$ total balls, $\ge 5$ crisis matches, $\ge 30$ normal balls. Includes all eligible players regardless of nominal role.*

| Rank | Player Name | Tactical Role | Crisis Balls | Crisis Matches | Crisis Wkt Rate % | Normal Wkt Rate % | Dot Maintenance | Match Consistency | Final Bowling PRI |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Mark Adair** | Bowling All-Rounder | 483 | 40 | 6.6% | 4.9% | 1.48x | 0.59 | **86.16** |
| **2** | **Craig Young** | Specialist Bowler | 289 | 23 | 9.0% | 2.8% | 1.31x | 0.51 | **86.10** |
| **3** | **Harry Tector** | Batting All-Rounder / Part-Time | 54 | 10 | 9.3% | 0.0% | 1.50x | 0.53 | **86.00** |
| **4** | **Mark Wood** | Specialist Bowler | 156 | 13 | 9.6% | 3.2% | 1.08x | 0.51 | **77.94** |
| **5** | **Obed McCoy** | Specialist Bowler | 334 | 30 | 6.6% | 4.3% | 1.33x | 0.52 | **77.83** |
| **6** | **Trent Boult** | Bowling All-Rounder | 879 | 70 | 5.0% | 1.6% | 1.47x | 0.53 | **76.46** |
| **7** | **Gareth Delany** | Bowling All-Rounder | 178 | 24 | 6.7% | 0.0% | 1.50x | 0.34 | **76.18** |
| **8** | **Eshan Malinga** | Specialist Bowler | 572 | 39 | 6.3% | 2.2% | 1.14x | 0.61 | **73.67** |
| **9** | **Jacob Duffy** | Specialist Bowler | 486 | 39 | 7.8% | 9.2% | 0.98x | 0.58 | **73.13** |
| **10** | **Krishnappa Gowtham** | Bowling All-Rounder | 67 | 10 | 7.5% | 2.9% | 1.27x | 0.49 | **72.66** |
| **7** | **Jacob Duffy** | 486 | 39 | 7.8% | 9.2% | 0.98x | 0.58 | **72.16** |
| **8** | **Matheesha Pathirana** | 578 | 49 | 8.5% | 4.1% | 1.29x | 0.56 | **71.94** |
| **9** | **Eshan Malinga** | 572 | 39 | 6.3% | 2.2% | 1.14x | 0.61 | **71.78** |
| **10** | **Krishnappa Gowtham** | 67 | 10 | 7.5% | 2.9% | 1.27x | 0.49 | **71.00** |

---

## 🏰 Key Rajasthan Royals Scouting Insights

1. **Explosive No. 4/5 Batter:** **Rajat Patidar** (SR 171.6, 23.1% boundaries, 1,069 runs) is the premier Indian middle-order candidate. **Tim David** (SR 186.0) leads overseas finishers.
2. **Experienced Indian Fast Bowlers:** **Arshdeep Singh** (192 wickets, 37.9% dots) and **Bhuvneshwar Kumar** (115 wickets, 40.5% dots, 50.4% PP dots). **Prasidh Krishna** (69 wickets, 40.2% dots) provides high-pace domestic familiarity.
3. **Complementary Spin Support:** **Varun Chakravarthy** (135 wickets, SR 15.8) and **Kuldeep Yadav** (Left-arm chinaman, 118 wickets) form a complete multi-style spin trident alongside Ravi Bishnoi (leg break) and Ravindra Jadeja (orthodox).
4. **On-Field Batting Partnerships:** Official delivery logs confirm **Ravindra Jadeja & Donovan Ferreira** have batted together for **135 deliveries, scoring 210 runs at a combined SR of 155.56**, proving high tactical synergy at the death.

---

## 🔬 Mathematical Methodology

### Pressure Reliability Index (PRI)
$$\text{PRI} = 0.35 \cdot M_{\text{norm}} + 0.35 \cdot A_{\text{norm}} + 0.20 \cdot C_{\text{norm}} + 0.10 \cdot S_{\text{norm}}$$

- **Performance Maintenance ($M$):** Ratio of pressure output to unconstrained baseline:
  - Batters: $\min\left(1.50, \frac{\text{SR}_{\text{crisis}}}{\max(100.0, \text{SR}_{\text{norm}})}\right)$
  - Bowlers: $\min\left(1.50, \frac{\text{Dot\%}_{\text{crisis}}}{\max(20.0, \text{Dot\%}_{\text{norm}})}\right)$
- **Absolute Pressure Metric ($A$):** Genuine Empirical Bayesian shrinkage towards population priors:
  - Batters (Normal-Normal): $\hat{\mu}_i = \frac{n_i}{n_i + K} \cdot \bar{X}_i + \frac{K}{n_i + K} \cdot \mu_0$
  - Bowlers (Beta-Binomial): $\hat{p}_i = \frac{k_i + \alpha}{n_i + \alpha + \beta} \times 100$
- **Cross-Match Consistency ($C$):** Exposure-adjusted exponential dispersion score:
  $$C = \exp(-\text{CV}) \cdot \sqrt{\frac{m}{m + 3}}$$
  Guarantees strictly positive, bounded scores in $(0, 1]$ and eliminates zero-consistency clipping.
- **Sample Confidence ($S$):** Logarithmic scale score reflecting pressure delivery exposure:
  $$S = \min\left(1.0, \frac{\ln(1 + n_i)}{\ln(1 + 100)}\right)$$

---

## 🛡️ Data Quality Governance & Strict Disclosures

- **`extras1_runs` is Categorical:** Handled strictly as an enum (`1: Overstep, 2: wide, 3: legbyes, 4: byes, 5: other, 6: None, 7: Penalty`). Never summed as runs.
- **Score-Dependent Metrics Quarantined:** Team totals, required run rates (RRR), and bowler economy rates remain quarantined until Rajasthan Royals releases definitive extras run codebooks.
- **Reconciled Boundary Anomalies:** Audited and corrected 20 deliveries where runs scored were 4 but `is_four` was false, and 3 deliveries where runs scored were 6 but `is_six` was false.
- **Super Overs Quarantined:** Innings 3 & 4 (26 balls) are quarantined from regular 20-over tactical ratings.
- **Non-Bowler Dismissals Excluded:** Run outs (571), retired outs (6), and obstruction (2) are filtered out from bowler wicket tallies.
- **Stumpings on Wides Attributed:** 39 stumping wickets occurring on wide deliveries are correctly credited to bowlers without incrementing legal ball counts.

---

## 🚀 Quickstart & Execution Guide

### 1. Launch the Interactive Streamlit Dashboard
```powershell
streamlit run dashboard/app.py
```

### 2. Run the Full Analytical Pipeline
```powershell
# Phase 1: Ingestion and cleaning audit
python scripts/validate_phase1.py

# Phase 2: Match context and partnership reconstruction
python scripts/build_context.py

# Phase 3: Aggregated cricket intelligence features
python scripts/compute_cricket_stats.py

# Phase 4 & 5: Dual pressure models and PRI player rankings
python scripts/compute_rankings.py

# Phase 6: Rajasthan Royals squad scouting engine
python scripts/run_scouting.py

# Phase 7: Participant Technical Methodology Report (PDF & MD)
python src/reporting/report_generator.py
```

### 3. Run Automated Pytest Suite
```powershell
python -m pytest tests/ -v
```
*Result: 17 passed in 1.27s.*

---
*Developed for Rajasthan Royals • SupeRR Selector Season 2 Hackathon • Research Prototype*
