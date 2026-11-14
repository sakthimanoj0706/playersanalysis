# SupeRR Intelligence V3 👑
### Rajasthan Royals SupeRR Selector Season 2 — Joint Performance, Pressure Intelligence & Player-Fit Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/pytest-30%20passed-success.svg)](tests/)
[![Dataset](https://img.shields.io/badge/data-IPL%20%2B%20T20I%20(2022--2026)-magenta.svg)](data/)
[![Dashboard](https://img.shields.io/badge/streamlit-production--v3-pink.svg)](dashboard/)

**SupeRR Intelligence V3** is an audited, mathematically verified, and scientifically defensible cricket intelligence platform engineered for the Rajasthan Royals (RR) SupeRR Selector Season 2 Hackathon. The platform delivers two independent, decoupled analytical systems:

1. **System A — Universal Cricket Intelligence:** Context-benchmarked performance modeling across 837 matches (IPL & T20I 2022–2026), evaluating individual player performance under pre-delivery pressure with 5-state mutually exclusive role gating, discrete-time wicket hazard modeling, bowling tail-risk (CVaR90), and match-clustered bootstrap uncertainty.
2. **System B — Rajasthan Royals Team Intelligence:** Squad-first empirical analysis of RR's 16-match 2026 IPL campaign (3,788 balls, 3rd place overall finish), identifying 4 verified tactical deficiencies, evaluating 13 watchlist candidates under constraint-aware multi-criteria optimization, and calculating exact retention and auction purse scenarios for the 2027 mini-auction in Goa.

---

## 🏆 Universal Top 10 Leaderboards Under Pressure (System A)

### 🏏 Universal Top 10 Batters (Gated: `BAT_SPECIALIST` & `BAT_PRIMARY_AR`)
*Eligibility: $\ge 40$ crisis balls, $\ge 120$ career balls, $\ge 5$ matches, $\ge 30$ normal balls. Gated by 5-state empirical role taxonomy.*

| Rank | Player Name | V3 Role | Crisis Balls Faced | Crisis SR | Normal SR | Maintenance Ratio | Match Consistency | 95% Confidence Interval |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Tilak Varma** | BAT_SPECIALIST | 48 | 179.2 | 144.1 | 1.24x | 1.22 | [168.0, 192.5] |
| **2** | **Matthew Wade** | BAT_SPECIALIST | 43 | 162.8 | 134.6 | 1.21x | 1.15 | [149.2, 178.4] |
| **3** | **Daryl Mitchell** | BAT_SPECIALIST | 84 | 158.3 | 139.8 | 1.13x | 1.34 | [146.5, 171.0] |
| **4** | **Liam Livingstone** | BAT_PRIMARY_AR | 48 | 154.2 | 145.0 | 1.06x | 1.08 | [141.0, 169.5] |
| **5** | **MS Dhoni** | BAT_SPECIALIST | 50 | 152.0 | 155.0 | 0.98x | 1.45 | [138.5, 167.2] |
| **6** | **Abdul Samad** | BAT_PRIMARY_AR | 48 | 150.0 | 152.0 | 0.99x | 1.02 | [135.0, 166.0] |
| **7** | **Jaker Ali Anik** | BAT_SPECIALIST | 46 | 147.8 | 132.5 | 1.12x | 1.10 | [133.2, 163.5] |
| **8** | **David Miller** | BAT_SPECIALIST | 91 | 147.3 | 141.2 | 1.04x | 1.28 | [135.8, 159.4] |
| **9** | **Rinku Singh** | BAT_SPECIALIST | 74 | 145.9 | 146.8 | 0.99x | 1.31 | [134.0, 158.6] |
| **10** | **Ramandeep Singh** | BAT_PRIMARY_AR | 40 | 145.0 | 160.0 | 0.91x | 0.95 | [130.0, 162.0] |

*Role Governance Confirmation:* Gudakesh Motie and Akeal Hosein are classified as `BOWL_SPECIALIST` and are cleanly excluded from the batting leaderboard.

---

### 🎯 Universal Top 10 Bowlers (Gated: `BOWL_SPECIALIST` & `BOWL_PRIMARY_AR`)
*Eligibility: $\ge 40$ defensive balls, $\ge 120$ career balls, $\ge 5$ matches, $\ge 30$ normal balls. Gated by 5-state empirical role taxonomy.*

| Rank | Player Name | V3 Role | Defensive Balls Bowled | Dot Ball % | Wickets Taken | Dot Maintenance | Match Consistency | 95% Confidence Interval |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Craig Young** | BOWL_SPECIALIST | 57 | 45.6% | 7 | 1.08x | 1.18 | [39.0%, 53.0%] |
| **2** | **Mark Adair** | BOWL_PRIMARY_AR | 57 | 42.1% | 8 | 1.04x | 1.24 | [35.5%, 49.0%] |
| **3** | **Gareth Delany** | BOWL_PRIMARY_AR | 44 | 40.9% | 5 | 1.02x | 1.05 | [33.0%, 49.5%] |
| **4** | **Mark Wood** | BOWL_SPECIALIST | 52 | 40.4% | 5 | 0.98x | 1.12 | [32.5%, 48.8%] |
| **5** | **Trent Boult** | BOWL_SPECIALIST | 185 | 39.5% | 12 | 0.95x | 1.42 | [34.8%, 44.5%] |
| **6** | **Obed McCoy** | BOWL_SPECIALIST | 46 | 39.1% | 5 | 0.96x | 1.01 | [31.0%, 48.0%] |
| **7** | **Jacob Duffy** | BOWL_SPECIALIST | 47 | 38.3% | 4 | 0.94x | 0.98 | [30.2%, 47.1%] |
| **8** | **Deepak Chahar** | BOWL_SPECIALIST | 68 | 38.2% | 5 | 0.93x | 1.15 | [31.5%, 45.8%] |
| **9** | **Eshan Malinga** | BOWL_SPECIALIST | 42 | 38.1% | 3 | 0.92x | 0.92 | [29.5%, 47.5%] |
| **10** | **Lungi Ngidi** | BOWL_SPECIALIST | 42 | 38.1% | 4 | 0.92x | 0.95 | [29.5%, 47.5%] |

*Role Governance Confirmation:* Harry Tector is classified as `BAT_PRIMARY_AR` and is cleanly excluded from the bowling leaderboard. **Intersection between Batting and Bowling Top 10 is exactly 0.**

---

## 🏰 Rajasthan Royals 2026 Empirical Audit (System B)

All 16 matches (14 league games + Eliminator win + Qualifier 2 loss) and 3,788 deliveries played by RR in IPL 2026 were ingested and reconciled:

- **Orange Cap & Tournament MVP:** **Vaibhav Sooryavanshi** — 16 matches (12 Starting XI + 4 Impact Sub), 776 runs, 327 balls, SR 237.31, avg 48.50, 72 sixes.
- **Top Batting Contributors:**
  - **Dhruv Jurel:** 16 matches, 515 runs, 333 balls, SR 154.65, **average 36.79** (14 dismissals, 2 not outs, resolving partner run-out misattributions).
  - **Yashasvi Jaiswal:** 16 matches, 427 runs, 280 balls, SR 152.50, avg 30.50.
  - **Donovan Ferreira:** 13 inns, 317 runs, 177 balls, SR 179.10, avg 35.22, 23 sixes.
  - **Riyan Parag:** 14 matches, 309 runs, 196 balls, SR 157.65, avg 23.77.
  - **Ravindra Jadeja:** 11 inns, 266 runs, 197 balls, SR 135.03, avg 66.50 (7 not outs).
- **Bowling Leadership:**
  - **Jofra Archer:** 16 matches, 60.0 overs, 158 dot balls, **25 bowler-creditable wickets** (29 total wickets in over).
  - **Brijesh Sharma:** 13 matches, 14 bowler-creditable wickets (₹30 Lakh uncapped find).
  - **Nandre Burger:** 13 matches, 14 bowler-creditable wickets.
  - **Ravi Bishnoi:** 9 matches, 11 bowler-creditable wickets (tactically benched for 7 games).
  - **Adam Milne:** Selected in 16 squad sheets, but played **exactly 1 match** (3.2 overs, 0 wickets).

---

## 🎯 Tactical Squad Gaps & Auction Strategy (Goa 2027)

| Tactical Gap | Priority | Target Candidate 1 | Target Candidate 2 | Contingency Backup | Budget Allocation |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **Indian Frontline Pacer** | **CRITICAL** | **Prasidh Krishna** *(₹8.5–10.5 Cr)* | **Avesh Khan** *(₹8.0–10.0 Cr)* | Mukesh Kumar / Akash Deep | **₹9.0 – ₹11.0 Cr** |
| **Overseas Death Bowler** | **CRITICAL** | **Matheesha Pathirana** *(₹8.0–9.5 Cr)* | **Nuwan Thushara** *(₹4.5–5.5 Cr)* | Gerald Coetzee | **₹8.0 – ₹10.0 Cr** |
| **Middle Finger Spinner** | **IMPORTANT** | **R Sai Kishore** *(₹3.5–4.5 Cr)* | **Manav Suthar** *(₹0.8–1.5 Cr)* | Swapnil Singh | **₹3.0 – ₹4.5 Cr** |
| **Domestic Finisher** | **IMPORTANT** | **Ashutosh Sharma** *(₹2.5–3.5 Cr)* | **Abhinav Manohar** *(₹2.0–3.5 Cr)* | Sameer Rizvi | **₹2.5 – ₹3.5 Cr** |

### Purse Arithmetic & Scenarios
```
  Carried Unspent Purse:                        ₹2.65 Cr
+ Shimron Hetmyer Release:                     ₹11.00 Cr
+ Tushar Deshpande Release:                     ₹6.50 Cr
+ Sandeep Sharma Release:                       ₹4.00 Cr
+ Adam Milne Release:                           ₹2.40 Cr
+ Kuldeep Sen Release:                          ₹0.75 Cr
+ Migael Pretorius Release:                     ₹0.30 Cr
---------------------------------------------------------
  Total Freed Player Salaries:                 ₹24.95 Cr
=========================================================
  BASE AVAILABLE PURSE:                        ₹27.60 Cr
  EXPANDED PURSE (+₹5.00 Cr Cap Increase):     ₹32.60 Cr
```

**Regulatory Advisory:** Dasun Shanaka was signed as temporary injury replacement for Sam Curran. RR management must settle Curran's medical fitness before the 17 November 2026 deadline.

---

## 🔬 Mathematical Models & Validation Matrix

| Component | Model Type | Validation Split | Key Metrics | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Pressure Proxy** | Ex-Ante Pre-Delivery | Chronological Match | Zero target leakage, bounded [0, 10] | **PRODUCTION_VALIDATED** |
| **Role Classifier** | 5-State Taxonomy | Multi-Season Workload | 1,118 classified, 0 overlap in gates | **PRODUCTION_VALIDATED** |
| **Joint Performance** | Hierarchical Ridge | Chronological Match | Test RMSE 1.294 (Joint+Pressure lowest) | **RESEARCH_VALIDATED** |
| **Wicket Hazard** | Discrete Logistic Hazard | Chronological Match | Test Log-Loss 0.178, ROC-AUC 0.694 | **PRODUCTION_VALIDATED** |
| **Tail-Risk (CVaR)** | EVT / Over-Level Loss | Over Distribution | VaR90, CVaR90 Pareto Frontier | **PRODUCTION_VALIDATED** |
| **Challenger Model** | LightGBM Gradient Boost | Chronological Match | Runs RMSE 1.289, Wicket AUC 0.701 | **CHALLENGER_BENCHMARK** |
| **Uncertainty** | Match-Clustered Bootstrap | Cluster Resample (500) | 95% Confidence Intervals per player | **PRODUCTION_VALIDATED** |

---

## 🛡️ Data Governance & Quarantine Disclosures

1. **`extras1_runs` is Categorical (Codes 1–7):** Never summed as numeric runs.
2. **Bowling Economy Quarantined:** Total runs conceded cannot be verified without provider extras codebooks; dynamic economy is quarantined.
3. **Dynamic Required Run Rate (RRR) Quarantined:** Scoreboard-dependent chase probabilities remain quarantined.
4. **Super Overs Quarantined:** Innings 3 & 4 (26 balls) segregated from standard 20-over tactical ratings.
5. **Dismissal Integrity:** 581 non-bowler wickets (RunOut, RetiredOut, etc.) excluded from bowler tallies; partner run-outs excluded from striker dismissals.

---

## 🚀 Running the Platform

### Run the Test Suite (30 Tests)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Launch Interactive Executive Dashboard
```powershell
.\.venv\Scripts\streamlit.exe run dashboard/app.py
```
App URL: `http://localhost:8501`
