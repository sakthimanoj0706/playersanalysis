# Dashboard Validation & QA Report (V3 Canonical Sync)
**Platform:** SupeRR Intelligence V3 — Rajasthan Royals SupeRR Selector Season 2  
**Audit Date:** November 15, 2026  
**Auditor:** Cricket Analytics Engineering Team  

---

## 1. Executive Summary

The SupeRR Intelligence V3 analytics dashboard (`dashboard/app.py`) operates on a **5-section architecture** adhering to the Rajasthan Royals branding guidelines (Deep Navy `#0B1B3D`, Royal Pink `#EA1A85`, Clean White `#FFFFFF`) and reads strictly from the canonical `data/outputs/v3/` CSV artifacts.

---

## 2. Structural & Architectural Verification

The dashboard is structured into five logically distinct analytical sections:

### Section 1: Universal Player Intelligence (`data/outputs/v3/`)
- **Tab 1: Top 10 Batters Under Pressure (`TOP_10_BATTERS.csv`):** Filtered strictly to `BAT_SPECIALIST` and `BAT_PRIMARY_AR` with $\ge 40$ crisis balls, $\ge 120$ total balls, $\ge 5$ crisis matches, and $\ge 30$ normal balls (92 eligible batters). Led by Ashutosh Sharma (#1, Score 93.88), Ramandeep Singh (#2, Score 87.73), Shreyas Iyer (#3, Score 86.82), William Jacks (#4, Score 84.72), and Jos Buttler (#5, Score 80.62), plus expandable Deliverable 3f individual selection rationales for all 10 batters.
- **Tab 2: Top 10 Bowlers Under Pressure (`TOP_10_BOWLERS.csv`):** Filtered strictly to `BOWL_SPECIALIST` and `BOWL_PRIMARY_AR` with $\ge 120$ crisis balls, $\ge 120$ total legal balls, $\ge 5$ crisis matches, and $\ge 100$ normal balls (`MIN_NORMAL_BALLS = 100`, 99 eligible bowlers). Led by Mohammed Shami (#1, Score 75.31), Obed McCoy (#2, Score 73.15), Joshua Little (#3, Score 70.58), Trent Boult (#4, Score 69.31), and Haris Rauf (#5, Score 67.48), plus expandable Deliverable 3f individual selection rationales for all 10 bowlers.
- **Tab 3: Player Performance Breakdown:** Interactive Plotly scatter charts of Crisis vs Normal performance filtered strictly to `final_eligibility == 'ELIGIBLE'`.
- **Tab 4: Role Classification & Eligibility:** 1,100 canonical players across 5 mutually exclusive V3 roles (`BAT_SPECIALIST`, `BAT_PRIMARY_AR`, `BOWL_PRIMARY_AR`, `BOWL_SPECIALIST`, `LOW_EXPOSURE_UNCLASSIFIED`) with zero overlap between batting (360) and bowling (332) gates.
- **Tab 5: Pressure Methodology & Models:** Full specification of the calibrated pre-delivery pressure models (`V3.2_EGM_CALIBRATED_HEURISTIC`) and documented limitations.
- **Tab 6: Reliability & Uncertainty (Bootstrap CIs):** 2,000-iteration match-clustered bootstrap 95% confidence interval charts for both Top 10 Batters and Top 10 Bowlers.

### Section 2: Rajasthan Royals 2026 Analysis
- **Empirical Season Review:** Grounded in all 16 matches and 3,788 ball-by-ball delivery records in IPL 2026.

### Section 3: RR Team Requirements
- **Squad Gap Audit:** 4 verified tactical role gaps prioritized for the IPL 2027 Mini-Auction.

### Section 4: RR Player Fit & Auction Strategy
- **Candidate Evaluation Matrix (`RR_PLAYER_FIT.csv`):** 13 watchlist candidates evaluated against RR tactical gaps with canonical IDs and V3 role alignment.

### Section 5: Data & Model Transparency
- **Governance & Quarantine Matrix:** Full disclosure of `extras1_runs` categorical encoding (1–7), quarantined scoreboard/RRR/economy metrics, and `EXPERIMENTAL_NOT_USED_FOR_RANKING` status for the wicket hazard, joint Ridge, and LightGBM models.

---

## 3. Data Integrity & Code Validation

1. **Single Authoritative Source of Truth:** All tables load dynamically from `data/outputs/v3/`.
2. **Code Quality:** Verified via `py_compile`, `scripts/verify_v3_rankings.py`, and 64 passing `pytest` unit/regression tests.
