# EGM Application Audit — SupeRR Intelligence V3

**Audit Identifier:** `EGM-APPLICATION-AUDIT-001`  
**Repository:** `d:\rrhackthon` (Branch: `fix/v3-pre-submission-consistency-001`, Commit: `3b18f48`)  
**Audit Mode:** Strictly Read-Only (Zero Code or Ranking Modifications)  
**Audit Date:** 15 November 2026

---

## 1. Executive Summary of Application Audit

The existing application (`dashboard/app.py`, `src/reporting/report_generator.py`, `scripts/compute_v3_rankings.py`, and output artifacts across `data/outputs/v3/`, `data/outputs/`, and project root) was audited across all 13 functional and data-consistency dimensions required by Section 6.

### Key Application Audit Conclusions
1. **Runtime Execution & Column Integrity (`PASS`):** `dashboard/app.py` (777 lines) loads all 21 CSVs in `load_v3_data()` (`lines 151-187`) without runtime exceptions, and all DataFrame column accesses across all 5 navigation sections match the schema of `data/outputs/v3/*.csv`.
2. **Deliverable 3f Failure — Missing Individual Selection Rationales for the 20 Selected Players (`FAIL — GROUP A`):**
   - The official hackathon prompt mandates explaining **"why each of the 20 players is selected"** (10 batters + 10 bowlers).
   - `FINAL_SUPERR_METHODOLOGY_REPORT.md` / `.pdf` (`src/reporting/report_generator.py:152-167, 284-370`) only explains **1 batter (#9 Iftikhar Ahmed)** in detail and provides **zero player-by-player justification for any of the 10 bowlers**!
   - `dashboard/app.py` (`lines 281-285, 326-328`) only provides bullet points for **4 batters (#1, #2, #8, #9)** and **4 bowlers (#1, #2, #4, #5)**, leaving **12 of the 20 selected players without individual selection commentary in the UI**.
   - Even at the CSV level, `TOP_10_BOWLERS.csv` lacks the `component_breakdown_explanation` column that was added to `TOP_10_BATTERS.csv` (`scripts/compute_v3_rankings.py:993` vs `1005-1024`).
3. **Stale Pre-P1.1 Leaderboard Artifacts in Root & `data/outputs/` (`FAIL — GROUP A`):**
   - While `scripts/compute_v3_rankings.py:1086-1126` synchronized 14 CSV copies, it left **11 prominent V2 / pre-P1.1 files** in the project root and `data/outputs/` displaying **contradictory, discredited Top-10 lists**:
     - `d:\rrhackthon\PRI_SENSITIVITY_ANALYSIS.csv` (root): Lists Mark Adair #1 bowler (`86.16`), Craig Young #2 (`86.10`), Mark Wood #3 (`77.94`), Obed McCoy #4 (`77.83`), Trent Boult #5 (`76.46`); and lists Ravindra Jadeja #8 batter (`63.77`) and Rinku Singh #10 batter (`62.78`).
     - `batting_pri_details.csv` & `bowling_pri_details.csv` (in both root and `data/outputs/`): Lists **#3 Gudakesh Motie (`74.59`)** and **#6 Akeal Hosein (`68.23`)** as `ELIGIBLE` Top-10 batters, and **#3 Harry Tector (`86.00`)** as an `ELIGIBLE` Top-10 bowler!
     - `data/outputs/batting_pressure_rankings.parquet` & `bowling_pressure_rankings.parquet`: Contradict `batting_pressure_rankings.csv` and `bowling_pressure_rankings.csv` in the same folder.
     - `ALL_BATTER_RANKINGS.csv`, `ALL_BOWLER_RANKINGS.csv`, `batting_pressure_rankings.csv`, `bowling_pressure_rankings.csv`: Exported in raw `striker_id` / `bowler_id` order (`MS Dhoni`, `Piyush Chawla`, `Ishant Sharma`, `Virat Kohli` first) without sorting by rank and without a `rank` / `provisional_rank` column!
     - `data/outputs/RR_SQUAD_SCOUTING_REPORT.csv`: Recommends retired **Dinesh Karthik**, contradicting `data/outputs/v3/RR_PLAYER_FIT.csv`.
     - `DASHBOARD_VALIDATION_REPORT.md` (root): Describes the old 4-section dashboard with Mark Adair #1 and Tilak Varma PRI `91.30`.
4. **UI Role-Gating Leak & Incomplete Visuals in `dashboard/app.py` (`GROUP B`):**
   - `u_tab3` (`dashboard/app.py:338, 355`) filters `all_bat` and `all_bowl` by `sample_eligible == True` instead of `final_eligibility == 'ELIGIBLE'`, plotting **22 `BOWL_PRIMARY_AR` tailenders** (Gudakesh Motie, Akeal Hosein, R Ashwin, Shardul Thakur) on the Batters chart and **7 `BAT_PRIMARY_AR` batters** (Hardik Pandya, Cameron Green, Saim Ayub) on the Bowlers chart.
   - `u_tab6` (`dashboard/app.py:421-437`) states `"500 bootstrap iterations"` (contradicting `2,000` in line 768 and the CSVs) and **omits the Top 10 Bowlers 95% CI plot entirely**.
   - `u_tab3` ("Player Performance Deep-Dive") has **no individual player profile selector, no component breakdown chart, and no match-by-match evidence table** for Universal Top-10 players.

---

## 2. Subsystem-by-Subsystem Application Checklist

| Application Area | File & Line Reference | Status | Audit Evidence & Findings |
| :--- | :--- | :---: | :--- |
| **1. Dashboard Pages & Navigation** | `dashboard/app.py:200-222` | **PASS** | 5-section sidebar radio navigation: (1) Universal Player Intelligence (6 tabs), (2) RR 2026 Analysis (7 tabs), (3) RR Team Requirements, (4) RR Player Fit & Auction Strategy (4 tabs), (5) Data & Model Transparency (4 tabs). |
| **2. Top 10 Batter & Bowler Displays** | `dashboard/app.py:244-328` | **PARTIAL** | Tables in `u_tab1` and `u_tab2` match `data/outputs/v3/TOP_10_BATTERS.csv` and `TOP_10_BOWLERS.csv`. However, `u_tab1` labels the score column `'Batting PRI'` (`batting_pri`) while `u_tab2` labels it `'Provisional Score'` (`provisional_fixed_weight_score`), and `u_tab1` omits `norm_balls`, `raw_sr_maintenance`, `is_maintenance_capped`, and `performance_anomaly_flag` from the table columns. |
| **3. Individual Player Profiles & Selection Rationale** | `dashboard/app.py:278-328, 330-367`<br>`FINAL_SUPERR_METHODOLOGY_REPORT.md` | **FAIL (`GROUP A`)** | Neither the dashboard nor the methodology report includes a dedicated profile or selection justification for each of the 20 Top-10 players (Deliverable 3f). Only 4 batters and 4 bowlers are discussed in `dashboard/app.py`, and only 1 batter (#9 Iftikhar Ahmed) is explained in `FINAL_SUPERR_METHODOLOGY_REPORT.md`. |
| **4. Player Comparisons (Universal vs RR)** | `dashboard/app.py:330-367, 639-661` | **PARTIAL** | Section 4 (`af_tab2`, lines 639–661) provides an interactive role-gap comparison expander for the 13 RR watchlist candidates. Section 1 (`u_tab3`, lines 330–367) has **no interactive player comparison tool** for universal players. |
| **5. Normal vs Pressure Visualizations** | `dashboard/app.py:333-367` | **PARTIAL (`GROUP B` Bug)** | `u_tab3` plots `norm_sr` vs `crisis_sr` (batters) and `norm_dot_pct` vs `crisis_dot_pct` (bowlers) with a $y=x$ parity line. **Bug:** Filters by `sample_eligible == True` instead of `final_eligibility == 'ELIGIBLE'`, leaking 22 `BOWL_PRIMARY_AR` bowlers into the batter scatter plot and 7 `BAT_PRIMARY_AR` batters into the bowler scatter plot. |
| **6. Match-by-Match Evidence** | `dashboard/app.py:462-465` | **PARTIAL (`GROUP B` Gap)** | Section 2 (`rr_tab1`, line 464) displays match-by-match results for RR's 16 IPL 2026 games (`rr_2026_matches.csv`). Section 1 has **zero match-by-match crisis evidence** for any of the Universal Top-10 batters or bowlers. |
| **7. RR 2026 Team Analysis** | `dashboard/app.py:433-559` | **PASS** | Accurately displays RR's 16 matches, audited batting stats (`Dhruv Jurel` 515 runs, 14 dismissals, `36.79` avg; `Vaibhav Sooryavanshi` 776 runs, `237.31` SR), bowler-creditable wickets (`Jofra Archer` 25 wkts), audited appearances (`Adam Milne` 1 match played vs 16 squad sheets), and phase `team_batter_runs`. |
| **8. Player Suitability & Scouting** | `dashboard/app.py:564-713`<br>`data/outputs/v3/RR_PLAYER_FIT.csv` | **PARTIAL (`GROUP B` Bug)** | Evaluates 13 candidates across 4 gaps and displays purse provenance (`UNVERIFIED_USER_BRIEF_SCENARIO`). **Bug:** `RR_PLAYER_FIT.csv` hardcodes Akeal Hosein (`2417`), Gerald Coetzee (`6628`), Rahul Chahar (`6161`), and Ravi Bishnoi (`7503`) as Specialist Bowlers (`BOWL_SPECIALIST`), contradicting `player_roles.csv` (`BOWL_PRIMARY_AR`). |
| **9. Backend Scripts & Library Alignment** | `scripts/compute_v3_rankings.py` vs `src/ranking_engine/pressure_rankings.py` | **PARTIAL (`GROUP B` Bug)** | `src/ranking_engine/pressure_rankings.py` is out of sync with `scripts/compute_v3_rankings.py` (`BOWL_MIN_NORMAL_BALLS = 30` vs `100`; bowler consistency uses `dot_rate + 2.0 * wkt_rate` in `pressure_rankings.py:414` vs dot rate only in `compute_v3_rankings.py:609`). |
| **10. Data Consistency Across All Output Files** | `data/outputs/v3/`, `data/outputs/`, project root | **FAIL (`GROUP A`)** | 11 legacy V2 files in root and `data/outputs/` contradict the V3 canonical CSVs; `player_roles.csv` and `ALL_BOWLER_METRICS.csv` disagree on career balls/wickets for 8 bowlers because `scripts/generate_v3_roles.py` did not filter out Super Overs (`innings` 3 & 4) or `is_played == False` bench rows. |
| **11. Charts & Uncertainty Calculations** | `dashboard/app.py:418-438` | **PARTIAL (`GROUP B` Bug)** | `u_tab6` claims `500 bootstrap iterations` (`line 421`) instead of `2,000` (`line 768`), and plots 95% CIs only for Batters while omitting Bowlers. |
| **12. Report & PDF Exports** | `src/reporting/report_generator.py`<br>`FINAL_SUPERR_METHODOLOGY_REPORT.pdf` | **PARTIAL** | Synchronized across all 6 PDF paths and 4 MD paths; tables match `TOP_10_BATTERS.csv` and `TOP_10_BOWLERS.csv`, but omits individual selection rationales for 19 of the 20 players. |
| **13. Error Handling & Reliability** | `dashboard/app.py:151-189` | **PASS** | `try/except` wrapper in `load_v3_data()` with `.empty` guards before rendering every table and chart. |
