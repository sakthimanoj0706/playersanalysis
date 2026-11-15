# SupeRR Intelligence V4: Pressure Reliability Analytics & RR 2027 Player Scouting
## Official Technical Methodology Report & Evidence Dossier (V4 Calibrated Ridge Edition)
**Target Event:** Rajasthan Royals — SupeRR Selector Season 2 Hackathon  
**Target Scope:** System A: Historical IPL & Men's T20I (2022–2026) | System B: RR IPL 2026 Audit & 2027 Auction Strategy  
**Authoritative Source Manifest:** `data/outputs/v3/RANKING_SOURCE_OF_TRUTH.json`  
**System Status:** `V4 CALIBRATED RIDGE — UNIFIED RUN VALUE VERIFIED`  

> **Governance & Methodology Disclosure:**
> "Rankings use V4 Calibrated Ridge state-conditional run values with Tier-1 weighting and within-phase quantile tiers. Batter ranks sensitive to scoring weights: #7; Bowler ranks sensitive to scoring weights: #7."

---

## 1. Executive Summary & V4 Architectural Guarantees

Under the Rajasthan Royals problem statement (*"Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels"* + *RR 2027 recruitment fit*), SupeRR Intelligence V4 unifies pressure classification, contextual baseline adjustment, and scouting alignment:

1. **Canonical Player Identity Resolution (`src/identity/player_identity.py`):** Consolidates verified multi-ID provider records before aggregation (`PLAYER_IDENTITY_CROSSWALK.csv`) while quarantining unresolved identity collisions.
2. **DLS-Aware, Survivorship-Free Pre-Delivery Leverage (`V4_CALIBRATED_RIDGE`):** Removes short-window dot/boundary survivorship bias (`dots_12`, `b12`) from pressure classification, incorporates DLS `second_inn_revised_overs` and `revised_target` across 25 rain-affected matches (`innings_context.py`), and calibrates **High (`> q70`) / Moderate (`q50–q70`) / Normal (`<= q50`)** tiers **within `(innings, innings_phase)`** so Powerplay and Death specialists preserve ~50% normal-pressure exposure rather than being over-classified as crisis.
3. **Competition-Tier Weighting & Tier-1 Exposure Gate (`>= 60%`):** De-weights Associate/Mixed T20Is (`T1_IPL = 1.0`, `T1_FM_T20I = 1.0`, `T2_MIXED = 0.5`, `T3_ASSOC = 0.2`) and enforces `tier1_share >= 0.60`, yielding **156 eligible batters** (`>= 60` Tier-weighted crisis balls, `>= 60` normal balls, `>= 200` total balls, `>= 6` matches) and **122 eligible frontline bowlers** (`>= 120` crisis balls, `>= 100` normal balls, `>= 250` total legal balls, `>= 6` matches).
4. **State-Conditional + Ridge Opponent & Match-Par Adjustment (`scipy.sparse.linalg.lsqr`):** Decomposes state residuals (`comp_tier x innings x phase x wkt_bucket`) into `match_par + striker_offense + bowler_defense`, evaluating every player in a unified Run Value currency (Batting **Runs Above Expectation / 100 balls**, `v_wkt = {4.0, 3.5, 2.5}`; Bowling **Runs Saved / Over** including `wide`/`Overstep` penalty runs + empirical `v_wkt = {5.5, 5.0, 3.5}`).
5. **Invariant PRI Weights (`30% Maint / 35% Abs / 25% Cons / 10% Sample`) & Direct RV Bootstrap CIs:** Eliminates the `PRIOR_ANCHORED_SPECIALIST` weight-reallocation loophole; pairs Cohort-Calibrated DiD (`k=90` bat / `k=150` bowl) with Value-Gated Downside Match Consistency and 2,000-iteration Match-Clustered Bootstrap 95% CIs directly on Crisis Run Value / Runs Saved.

---

## 2. Dataset Scope & Data Governance Audit

The platform ingests **853 matches** (837 with ball-by-ball delivery logs) and **193,988 regular deliveries** (after quarantining 26 Super Over deliveries in innings 3 and 4).

1. **`extras1_runs` is Categorical, NOT a Run Count:** Source data integer codes (`1`: Overstep, `2`: wide, `3`: legbyes, `4`: byes, `5`: other, `6`: None, `7`: Penalty) represent an enum codebook and are never summed as numeric runs.
2. **DLS-Aware Clean-Channel Scoring & Penalty Runs:** `innings_context.py` builds a clean lower-bound cumulative score (`runs + 1 * is_wide_or_overstep`) honoring `first_inn_revised_overs`, `second_inn_revised_overs`, and `revised_target`, while bowling economy and `bowl_rv` include `1 * is_wide_or_overstep` as clean extra penalties.
3. **Dismissal Attribution:** 581 non-bowler dismissals (573 run outs, 6 retired outs, 2 obstructing the field) are excluded from bowler wickets; partner run-outs are excluded from striker dismissal rates.
4. **Experimental Challenger Quarantine (`EXPERIMENTAL_NOT_USED_FOR_RANKING`):** The discrete-time logistic hazard model, hierarchical challenger, and LightGBM model remain quarantined from production rankings.

---

## 3. V4 Composite Formulation (`V4_CALIBRATED_RIDGE_SCORE`)

$$\text{Score}_{\text{V4}} = 100 \times \left( 0.30 M_{\text{norm}} + 0.35 A_{\text{norm}} + 0.25 C_{\text{norm}} + 0.10 S_{\text{norm}} \right)$$

1. **Cohort-Calibrated DiD Maintenance ($M$, 30% invariant):** Fits cohort slope $\beta \in [0.30, 0.80]$ relating capped shrunk normal RV (`min_norm_ref = -5.0` bat / `-0.5` bowl) to shrunk crisis RV (`did_bat_maintenance`, `did_bowl_maintenance`).
2. **Absolute Pressure Value ($A$, 35% invariant):** Shrunk crisis Run Value above state+opponent expectation (`crisis_delta_rv` in runs/100 for batting; `crisis_delta_rv` = `abs_bowl_score` in runs saved/over for bowling).
3. **Value-Gated Downside Match Consistency ($C$, 25% invariant):** Penalizes negative crisis outings via downside RMS deviation (`exp(-sigma_down / s)` with $s=45$ bat, $s=3.0$ bowl), weighted positive-match share $p_{\text{pos}}$, match breadth $\sqrt{m/(m+10)}$, and positive value sigmoid gate.
4. **Sample Confidence ($S$, 10% invariant):** $\min(1.0, \ln(1 + \text{eff\_cb}) / \ln(1 + \text{cap}))$ (`cap=350` batting, `600` bowling). Cohort means for auxiliary classical metrics: `131.04` SR (Bat) / `5.39%` Wkt Rate (Bowl).

---

## 4. Authoritative Top 10 Batters Under Crisis Pressure (`data/outputs/v3/TOP_10_BATTERS.csv`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | crisis_matches | tier1_share | crisis_sr | norm_sr | crisis_delta_rv | did_bat_maintenance | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3125 | Nicholas Pooran | BAT_SPECIALIST | 565 | 64 | 1 | 155.9292 | 171.9424 | 34.96 | 23.96 | 0.2763 | 96.95 | 19.56 | 59.84 | ROBUST_ACROSS_WEIGHTS |
| 2 | 6423 | Riyan Parag | BAT_PRIMARY_AR | 281 | 34 | 1 | 158.363 | 157.6994 | 30.81 | 26.74 | 0.2896 | 96.51 | 11.99 | 65.44 | ROBUST_ACROSS_WEIGHTS |
| 3 | 4260 | Heinrich Klaasen | BAT_SPECIALIST | 437 | 41 | 1 | 146.9108 | 189.5803 | 34.19 | 20.16 | 0.3602 | 94.94 | 25.17 | 54.85 | ROBUST_ACROSS_WEIGHTS |
| 4 | 8101 | Ashutosh Sharma | BAT_SPECIALIST | 197 | 17 | 1 | 162.4365 | 163.6364 | 30.47 | 30.24 | 0.2494 | 93.66 | 6.72 | 74.91 | ROBUST_ACROSS_WEIGHTS |
| 5 | 6396 | Tim David | BAT_SPECIALIST | 432 | 49 | 0.9829 | 153.7037 | 196.3947 | 38.13 | 24.03 | 0.2208 | 93.07 | 18.95 | 68.8 | ROBUST_ACROSS_WEIGHTS |
| 6 | 1318 | Andre Russell | BAT_PRIMARY_AR | 344 | 38 | 1 | 160.1744 | 202.3585 | 35.64 | 23.71 | 0.2097 | 92.06 | 18.01 | 67.68 | ROBUST_ACROSS_WEIGHTS |
| 7 | 6819 | Yashasvi Jaiswal | BAT_SPECIALIST | 118 | 23 | 1 | 204.2373 | 149.007 | 40.21 | 33.91 | 0.1693 | 89.85 | 25.18 | 110.51 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 2756 | Shashank Singh | BAT_PRIMARY_AR | 260 | 26 | 1 | 150.7692 | 187.7778 | 26.58 | 19.14 | 0.2816 | 88.65 | 8.29 | 58.72 | ROBUST_ACROSS_WEIGHTS |
| 9 | 7897 | Tilak Varma | BAT_PRIMARY_AR | 727 | 78 | 0.9913 | 138.1018 | 150.531 | 24.87 | 19.31 | 0.2579 | 86.52 | 13.58 | 42.22 | ROBUST_ACROSS_WEIGHTS |
| 10 | 1077 | David Miller | BAT_SPECIALIST | 452 | 44 | 1 | 151.5487 | 158.1301 | 25.43 | 20.59 | 0.2408 | 86.45 | 8.03 | 47.36 | ROBUST_ACROSS_WEIGHTS |

### 4.1 Individual Player Selection Rationales — Top 10 Batters
- **#1 Nicholas Pooran (`canonical_player_id=3125`, `BAT_SPECIALIST`):** Faced **565 crisis balls** (Tier-1 share: 100.0%) across **64 crisis matches** (normal baseline: 973 balls across 80 matches). Crisis SR **155.93** vs Normal SR **171.94**; shrunk Crisis Run Value **+34.96 runs/100** (95% match-clustered RV CI: `[+19.56, +59.84]`), DiD Maintenance **+23.96**, Value-Gated Downside Consistency **0.2763**. Component Breakdown: `Maint(30%)=27.68 + Abs(35%)=35.00 + Cons(25%)=24.27 + Sample(10%)=10.00 = 96.95` (`ROBUST_ACROSS_WEIGHTS`).
- **#2 Riyan Parag (`canonical_player_id=6423`, `BAT_PRIMARY_AR`):** Faced **281 crisis balls** (Tier-1 share: 100.0%) across **34 crisis matches** (normal baseline: 539 balls across 53 matches). Crisis SR **158.36** vs Normal SR **157.70**; shrunk Crisis Run Value **+30.81 runs/100** (95% match-clustered RV CI: `[+11.99, +65.44]`), DiD Maintenance **+26.74**, Value-Gated Downside Consistency **0.2896**. Component Breakdown: `Maint(30%)=29.40 + Abs(35%)=32.48 + Cons(25%)=25.00 + Sample(10%)=9.63 = 96.51` (`ROBUST_ACROSS_WEIGHTS`).
- **#3 Heinrich Klaasen (`canonical_player_id=4260`, `BAT_SPECIALIST`):** Faced **437 crisis balls** (Tier-1 share: 100.0%) across **41 crisis matches** (normal baseline: 691 balls across 49 matches). Crisis SR **146.91** vs Normal SR **189.58**; shrunk Crisis Run Value **+34.19 runs/100** (95% match-clustered RV CI: `[+25.17, +54.85]`), DiD Maintenance **+20.16**, Value-Gated Downside Consistency **0.3602**. Component Breakdown: `Maint(30%)=25.33 + Abs(35%)=34.61 + Cons(25%)=25.00 + Sample(10%)=10.00 = 94.94` (`ROBUST_ACROSS_WEIGHTS`).
- **#4 Ashutosh Sharma (`canonical_player_id=8101`, `BAT_SPECIALIST`):** Faced **197 crisis balls** (Tier-1 share: 100.0%) across **17 crisis matches** (normal baseline: 66 balls across 13 matches). Crisis SR **162.44** vs Normal SR **163.64**; shrunk Crisis Run Value **+30.47 runs/100** (95% match-clustered RV CI: `[+6.72, +74.91]`), DiD Maintenance **+30.24**, Value-Gated Downside Consistency **0.2494**. Component Breakdown: `Maint(30%)=30.00 + Abs(35%)=32.27 + Cons(25%)=22.37 + Sample(10%)=9.02 = 93.66` (`ROBUST_ACROSS_WEIGHTS`).
- **#5 Tim David (`canonical_player_id=6396`, `BAT_SPECIALIST`):** Faced **432 crisis balls** (Tier-1 share: 98.3%) across **49 crisis matches** (normal baseline: 527 balls across 68 matches). Crisis SR **153.70** vs Normal SR **196.39**; shrunk Crisis Run Value **+38.13 runs/100** (95% match-clustered RV CI: `[+18.95, +68.80]`), DiD Maintenance **+24.03**, Value-Gated Downside Consistency **0.2208**. Component Breakdown: `Maint(30%)=27.73 + Abs(35%)=35.00 + Cons(25%)=20.34 + Sample(10%)=10.00 = 93.07` (`ROBUST_ACROSS_WEIGHTS`).
- **#6 Andre Russell (`canonical_player_id=1318`, `BAT_PRIMARY_AR`):** Faced **344 crisis balls** (Tier-1 share: 100.0%) across **38 crisis matches** (normal baseline: 212 balls across 29 matches). Crisis SR **160.17** vs Normal SR **202.36**; shrunk Crisis Run Value **+35.64 runs/100** (95% match-clustered RV CI: `[+18.01, +67.68]`), DiD Maintenance **+23.71**, Value-Gated Downside Consistency **0.2097**. Component Breakdown: `Maint(30%)=27.53 + Abs(35%)=35.00 + Cons(25%)=19.56 + Sample(10%)=9.97 = 92.06` (`ROBUST_ACROSS_WEIGHTS`).
- **#7 Yashasvi Jaiswal (`canonical_player_id=6819`, `BAT_SPECIALIST`):** Faced **118 crisis balls** (Tier-1 share: 100.0%) across **23 crisis matches** (normal baseline: 1561 balls across 83 matches). Crisis SR **204.24** vs Normal SR **149.01**; shrunk Crisis Run Value **+40.21 runs/100** (95% match-clustered RV CI: `[+25.18, +110.51]`), DiD Maintenance **+33.91**, Value-Gated Downside Consistency **0.1693**. Component Breakdown: `Maint(30%)=30.00 + Abs(35%)=35.00 + Cons(25%)=16.70 + Sample(10%)=8.15 = 89.85` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#8 Shashank Singh (`canonical_player_id=2756`, `BAT_PRIMARY_AR`):** Faced **260 crisis balls** (Tier-1 share: 100.0%) across **26 crisis matches** (normal baseline: 180 balls across 23 matches). Crisis SR **150.77** vs Normal SR **187.78**; shrunk Crisis Run Value **+26.58 runs/100** (95% match-clustered RV CI: `[+8.29, +58.72]`), DiD Maintenance **+19.14**, Value-Gated Downside Consistency **0.2816**. Component Breakdown: `Maint(30%)=24.70 + Abs(35%)=29.82 + Cons(25%)=24.64 + Sample(10%)=9.49 = 88.65` (`ROBUST_ACROSS_WEIGHTS`).
- **#9 Tilak Varma (`canonical_player_id=7897`, `BAT_PRIMARY_AR`):** Faced **727 crisis balls** (Tier-1 share: 99.1%) across **78 crisis matches** (normal baseline: 1130 balls across 91 matches). Crisis SR **138.10** vs Normal SR **150.53**; shrunk Crisis Run Value **+24.87 runs/100** (95% match-clustered RV CI: `[+13.58, +42.22]`), DiD Maintenance **+19.31**, Value-Gated Downside Consistency **0.2579**. Component Breakdown: `Maint(30%)=24.81 + Abs(35%)=28.74 + Cons(25%)=22.97 + Sample(10%)=10.00 = 86.52` (`ROBUST_ACROSS_WEIGHTS`).
- **#10 David Miller (`canonical_player_id=1077`, `BAT_SPECIALIST`):** Faced **452 crisis balls** (Tier-1 share: 100.0%) across **44 crisis matches** (normal baseline: 492 balls across 53 matches). Crisis SR **151.55** vs Normal SR **158.13**; shrunk Crisis Run Value **+25.43 runs/100** (95% match-clustered RV CI: `[+8.03, +47.36]`), DiD Maintenance **+20.59**, Value-Gated Downside Consistency **0.2408**. Component Breakdown: `Maint(30%)=25.60 + Abs(35%)=29.09 + Cons(25%)=21.76 + Sample(10%)=10.00 = 86.45` (`ROBUST_ACROSS_WEIGHTS`).

---

## 5. Authoritative Top 10 Bowlers Under Defensive Pressure (`data/outputs/v3/TOP_10_BOWLERS.csv`)

| rank | canonical_player_id | player_name | v3_role | crisis_balls | norm_balls | crisis_matches | tier1_share | crisis_econ | crisis_dot_pct | crisis_wicket_rate | crisis_delta_rv | did_bowl_maintenance | consistency_score | provisional_fixed_weight_score | ci_lower | ci_upper | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 781 | Sunil Narine | BOWL_PRIMARY_AR | 563 | 653 | 40 | 1 | 7.3535 | 36.9449 | 3.9076 | 1.86 | 1.13 | 0.4168 | 95.78 | 1.36 | 3.39 | ROBUST_ACROSS_WEIGHTS |
| 2 | 4722 | Rashid Khan | BOWL_PRIMARY_AR | 825 | 1481 | 64 | 0.9825 | 7.9418 | 31.8788 | 5.2121 | 1.33 | 1.04 | 0.3077 | 87.36 | 0.66 | 2.51 | ROBUST_ACROSS_WEIGHTS |
| 3 | 305 | R Ashwin | BOWL_PRIMARY_AR | 505 | 613 | 38 | 1 | 7.9129 | 30.495 | 4.7525 | 1.11 | 0.99 | 0.3291 | 85.03 | 0.4 | 2.52 | ROBUST_ACROSS_WEIGHTS |
| 4 | 2933 | Jasprit Bumrah | BOWL_SPECIALIST | 570 | 916 | 48 | 0.9895 | 7.9053 | 37.7193 | 2.9825 | 1.38 | 0.71 | 0.3167 | 84.71 | 0.6 | 2.92 | ROBUST_ACROSS_WEIGHTS |
| 5 | 4900 | Wanindu Hasaranga | BOWL_PRIMARY_AR | 580 | 1117 | 43 | 0.9882 | 8.0793 | 32.5862 | 5.8621 | 1.22 | 0.88 | 0.2968 | 83.6 | 0.5 | 2.59 | ROBUST_ACROSS_WEIGHTS |
| 6 | 2687 | Roston Chase | BOWL_PRIMARY_AR | 171 | 494 | 17 | 1 | 7.9649 | 33.3333 | 7.0175 | 1.2 | 1.14 | 0.2665 | 82.71 | -0.16 | 4.51 | ROBUST_ACROSS_WEIGHTS |
| 7 | 722 | Liam Dawson | BOWL_SPECIALIST | 123 | 221 | 14 | 1 | 7.4146 | 36.5854 | 7.3171 | 0.97 | 0.85 | 0.3142 | 78.76 | -0.13 | 4.92 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 19316 | Maheesh Theekshana | BOWL_SPECIALIST | 576 | 1398 | 51 | 0.9894 | 8.2188 | 32.2917 | 4.3403 | 0.95 | 0.82 | 0.2804 | 78.76 | 0.25 | 2.1 | ROBUST_ACROSS_WEIGHTS |
| 9 | 7920 | Nathan Ellis | BOWL_SPECIALIST | 343 | 433 | 32 | 1 | 8.7114 | 34.1108 | 6.414 | 1.12 | 0.81 | 0.2573 | 78.66 | 0.33 | 3.05 | ROBUST_ACROSS_WEIGHTS |
| 10 | 2315 | Reece Topley | BOWL_SPECIALIST | 231 | 330 | 20 | 1 | 8.4156 | 42.8571 | 5.6277 | 0.87 | 0.87 | 0.3075 | 78.38 | -0.08 | 3.28 | ROBUST_ACROSS_WEIGHTS |

### 5.1 Individual Player Selection Rationales — Top 10 Bowlers
- **#1 Sunil Narine (`canonical_player_id=781`, `BOWL_PRIMARY_AR`):** Bowled **563 crisis legal balls** (Tier-1 share: 100.0%) across **40 crisis matches** (normal baseline: 653 legal balls across 45 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **7.35** (incl. wides/no-balls), Dot% **36.94%**, Wkt Rate **3.91%**; shrunk Crisis Runs Saved **+1.86/over** (95% match-clustered RV CI: `[+1.36, +3.39]`), DiD Maintenance **+1.13/over**, Value-Gated Downside Consistency **0.4168**. Component Breakdown: `Maint(30%)=25.88 + Abs(35%)=35.00 + Cons(25%)=25.00 + Sample(10%)=9.90 = 95.78` (`ROBUST_ACROSS_WEIGHTS`).
- **#2 Rashid Khan (`canonical_player_id=4722`, `BOWL_PRIMARY_AR`):** Bowled **825 crisis legal balls** (Tier-1 share: 98.2%) across **64 crisis matches** (normal baseline: 1481 legal balls across 95 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **7.94** (incl. wides/no-balls), Dot% **31.88%**, Wkt Rate **5.21%**; shrunk Crisis Runs Saved **+1.33/over** (95% match-clustered RV CI: `[+0.66, +2.51]`), DiD Maintenance **+1.04/over**, Value-Gated Downside Consistency **0.3077**. Component Breakdown: `Maint(30%)=24.87 + Abs(35%)=30.44 + Cons(25%)=22.05 + Sample(10%)=10.00 = 87.36` (`ROBUST_ACROSS_WEIGHTS`).
- **#3 R Ashwin (`canonical_player_id=305`, `BOWL_PRIMARY_AR`):** Bowled **505 crisis legal balls** (Tier-1 share: 100.0%) across **38 crisis matches** (normal baseline: 613 legal balls across 44 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **7.91** (incl. wides/no-balls), Dot% **30.50%**, Wkt Rate **4.75%**; shrunk Crisis Runs Saved **+1.11/over** (95% match-clustered RV CI: `[+0.40, +2.52]`), DiD Maintenance **+0.99/over**, Value-Gated Downside Consistency **0.3291**. Component Breakdown: `Maint(30%)=24.32 + Abs(35%)=27.77 + Cons(25%)=23.21 + Sample(10%)=9.73 = 85.03` (`ROBUST_ACROSS_WEIGHTS`).
- **#4 Jasprit Bumrah (`canonical_player_id=2933`, `BOWL_SPECIALIST`):** Bowled **570 crisis legal balls** (Tier-1 share: 99.0%) across **48 crisis matches** (normal baseline: 916 legal balls across 66 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **7.91** (incl. wides/no-balls), Dot% **37.72%**, Wkt Rate **2.98%**; shrunk Crisis Runs Saved **+1.38/over** (95% match-clustered RV CI: `[+0.60, +2.92]`), DiD Maintenance **+0.71/over**, Value-Gated Downside Consistency **0.3167**. Component Breakdown: `Maint(30%)=21.20 + Abs(35%)=31.05 + Cons(25%)=22.54 + Sample(10%)=9.92 = 84.71` (`ROBUST_ACROSS_WEIGHTS`).
- **#5 Wanindu Hasaranga (`canonical_player_id=4900`, `BOWL_PRIMARY_AR`):** Bowled **580 crisis legal balls** (Tier-1 share: 98.8%) across **43 crisis matches** (normal baseline: 1117 legal balls across 68 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **8.08** (incl. wides/no-balls), Dot% **32.59%**, Wkt Rate **5.86%**; shrunk Crisis Runs Saved **+1.22/over** (95% match-clustered RV CI: `[+0.50, +2.59]`), DiD Maintenance **+0.88/over**, Value-Gated Downside Consistency **0.2968**. Component Breakdown: `Maint(30%)=23.09 + Abs(35%)=29.10 + Cons(25%)=21.46 + Sample(10%)=9.95 = 83.60` (`ROBUST_ACROSS_WEIGHTS`).
- **#6 Roston Chase (`canonical_player_id=2687`, `BOWL_PRIMARY_AR`):** Bowled **171 crisis legal balls** (Tier-1 share: 100.0%) across **17 crisis matches** (normal baseline: 494 legal balls across 35 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **7.96** (incl. wides/no-balls), Dot% **33.33%**, Wkt Rate **7.02%**; shrunk Crisis Runs Saved **+1.20/over** (95% match-clustered RV CI: `[-0.16, +4.51]`), DiD Maintenance **+1.14/over**, Value-Gated Downside Consistency **0.2665**. Component Breakdown: `Maint(30%)=25.99 + Abs(35%)=28.86 + Cons(25%)=19.82 + Sample(10%)=8.04 = 82.71` (`ROBUST_ACROSS_WEIGHTS`).
- **#7 Liam Dawson (`canonical_player_id=722`, `BOWL_SPECIALIST`):** Bowled **123 crisis legal balls** (Tier-1 share: 100.0%) across **14 crisis matches** (normal baseline: 221 legal balls across 17 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **7.41** (incl. wides/no-balls), Dot% **36.59%**, Wkt Rate **7.32%**; shrunk Crisis Runs Saved **+0.97/over** (95% match-clustered RV CI: `[-0.13, +4.92]`), DiD Maintenance **+0.85/over**, Value-Gated Downside Consistency **0.3142**. Component Breakdown: `Maint(30%)=22.76 + Abs(35%)=26.07 + Cons(25%)=22.40 + Sample(10%)=7.53 = 78.76` (`RANKING_SENSITIVE_TO_WEIGHTS`).
- **#8 Maheesh Theekshana (`canonical_player_id=19316`, `BOWL_SPECIALIST`):** Bowled **576 crisis legal balls** (Tier-1 share: 98.9%) across **51 crisis matches** (normal baseline: 1398 legal balls across 90 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **8.22** (incl. wides/no-balls), Dot% **32.29%**, Wkt Rate **4.34%**; shrunk Crisis Runs Saved **+0.95/over** (95% match-clustered RV CI: `[+0.25, +2.10]`), DiD Maintenance **+0.82/over**, Value-Gated Downside Consistency **0.2804**. Component Breakdown: `Maint(30%)=22.43 + Abs(35%)=25.83 + Cons(25%)=20.57 + Sample(10%)=9.93 = 78.76` (`ROBUST_ACROSS_WEIGHTS`).
- **#9 Nathan Ellis (`canonical_player_id=7920`, `BOWL_SPECIALIST`):** Bowled **343 crisis legal balls** (Tier-1 share: 100.0%) across **32 crisis matches** (normal baseline: 433 legal balls across 33 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **8.71** (incl. wides/no-balls), Dot% **34.11%**, Wkt Rate **6.41%**; shrunk Crisis Runs Saved **+1.12/over** (95% match-clustered RV CI: `[+0.33, +3.05]`), DiD Maintenance **+0.81/over**, Value-Gated Downside Consistency **0.2573**. Component Breakdown: `Maint(30%)=22.31 + Abs(35%)=27.89 + Cons(25%)=19.33 + Sample(10%)=9.13 = 78.66` (`ROBUST_ACROSS_WEIGHTS`).
- **#10 Reece Topley (`canonical_player_id=2315`, `BOWL_SPECIALIST`):** Bowled **231 crisis legal balls** (Tier-1 share: 100.0%) across **20 crisis matches** (normal baseline: 330 legal balls across 27 matches, `VALID_NORMAL_BASELINE`). Crisis Econ **8.42** (incl. wides/no-balls), Dot% **42.86%**, Wkt Rate **5.63%**; shrunk Crisis Runs Saved **+0.87/over** (95% match-clustered RV CI: `[-0.08, +3.28]`), DiD Maintenance **+0.87/over**, Value-Gated Downside Consistency **0.3075**. Component Breakdown: `Maint(30%)=22.98 + Abs(35%)=24.85 + Cons(25%)=22.04 + Sample(10%)=8.51 = 78.38` (`ROBUST_ACROSS_WEIGHTS`).

---

## 6. Extended Crisis-Ball Threshold Sensitivity (`40..750`)

### 6.1 Batting Primary Crisis-Ball Sweep (`crisis_matches >= 6, norm_balls >= 60, total_balls >= 200, tier1_share >= 0.60`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 6 | 169 | 164 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 60 | 6 | 156 | 163 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 80 | 6 | 141 | 149 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 100 | 6 | 125 | 137 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 150 | 6 | 95 | 101 | 10 | 9 | 0.8182 | 0.4 | 1 | Dinesh Karthik | Yashasvi Jaiswal |
| 200 | 6 | 71 | 77 | 10 | 8 | 0.6667 | 1.3 | 3 | Dinesh Karthik, Suryakumar Yadav | Ashutosh Sharma, Yashasvi Jaiswal |
| 250 | 6 | 45 | 62 | 10 | 8 | 0.6667 | 1.3 | 3 | Dinesh Karthik, Suryakumar Yadav | Ashutosh Sharma, Yashasvi Jaiswal |
| 500 | 6 | 4 | 20 | 4 | 2 | 0.1667 | 13.5 | 37 | Suryakumar Yadav, Rovman Powell | Riyan Parag, Heinrich Klaasen, Ashutosh Sharma, Tim David, Andre Russell, Yashasvi Jaiswal, Shashank Singh, David Miller |
| 750 | 6 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | NONE | Nicholas Pooran, Riyan Parag, Heinrich Klaasen, Ashutosh Sharma, Tim David, Andre Russell, Yashasvi Jaiswal, Shashank Singh, Tilak Varma, David Miller |

### 6.2 Bowling Primary Crisis-Ball Sweep (`crisis_matches >= 6, norm_balls >= 100, total_legal_balls >= 250, tier1_share >= 0.60`)
| min_crisis_balls | min_crisis_matches | eligible_batter_count | eligible_bowler_count | available_top10_count | top10_overlap_with_baseline | jaccard_similarity | mean_abs_rank_movement | max_rank_movement | players_entering_top10 | players_leaving_top10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 6 | 169 | 164 | 10 | 7 | 0.5385 | 1 | 3 | Mark Wood, Matthew Humphreys, Ben Dwarshuis | Maheesh Theekshana, Nathan Ellis, Reece Topley |
| 60 | 6 | 156 | 163 | 10 | 7 | 0.5385 | 1 | 3 | Mark Wood, Matthew Humphreys, Ben Dwarshuis | Maheesh Theekshana, Nathan Ellis, Reece Topley |
| 80 | 6 | 141 | 149 | 10 | 7 | 0.5385 | 1 | 3 | Mark Wood, Matthew Humphreys, Ben Dwarshuis | Maheesh Theekshana, Nathan Ellis, Reece Topley |
| 100 | 6 | 125 | 137 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 120 | 6 | 106 | 122 | 10 | 10 | 1 | 0 | 0 | NONE | NONE |
| 150 | 6 | 95 | 101 | 10 | 9 | 0.8182 | 0.4 | 1 | Harpreet Brar | Liam Dawson |
| 200 | 6 | 71 | 77 | 10 | 8 | 0.6667 | 1 | 2 | Harpreet Brar, Axar Patel | Roston Chase, Liam Dawson |
| 250 | 6 | 45 | 62 | 10 | 7 | 0.5385 | 1.3 | 3 | Harpreet Brar, Axar Patel, Lungi Ngidi | Roston Chase, Liam Dawson, Reece Topley |
| 500 | 6 | 4 | 20 | 10 | 6 | 0.4286 | 3.3 | 11 | Axar Patel, Bhuvneshwar Kumar, Varun Chakravarthy, Ravi Bishnoi | Roston Chase, Liam Dawson, Nathan Ellis, Reece Topley |
| 750 | 6 | 0 | 4 | 4 | 1 | 0.0769 | 16.75 | 37 | Axar Patel, Yuzvendra Chahal, Arshdeep Singh | Sunil Narine, R Ashwin, Jasprit Bumrah, Wanindu Hasaranga, Roston Chase, Liam Dawson, Maheesh Theekshana, Nathan Ellis, Reece Topley |

---

## 7. Weight Sensitivity Analysis Across 5 Configurations (`RANKING_WEIGHT_SENSITIVITY.csv`)

### 7.1 Batting Weight Sensitivity (Top 10)
| provisional_rank | canonical_player_id | player_name | provisional_fixed_weight_score | contrib_maint | contrib_abs | contrib_cons | contrib_sample | rank_balanced_default | rank_maintenance_heavy | rank_absolute_heavy | rank_consistency_heavy | rank_equal_weights | max_rank_shift | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3125 | Nicholas Pooran | 96.95 | 27.68 | 35 | 24.27 | 10 | 1 | 2 | 1 | 2 | 1 | 1 | ROBUST_ACROSS_WEIGHTS |
| 2 | 6423 | Riyan Parag | 96.51 | 29.4 | 32.48 | 25 | 9.63 | 2 | 1 | 3 | 1 | 2 | 2 | ROBUST_ACROSS_WEIGHTS |
| 3 | 4260 | Heinrich Klaasen | 94.94 | 25.33 | 34.61 | 25 | 10 | 3 | 5 | 2 | 3 | 3 | 3 | ROBUST_ACROSS_WEIGHTS |
| 4 | 8101 | Ashutosh Sharma | 93.66 | 30 | 32.27 | 22.37 | 9.02 | 4 | 3 | 6 | 4 | 5 | 3 | ROBUST_ACROSS_WEIGHTS |
| 5 | 6396 | Tim David | 93.07 | 27.73 | 35 | 20.34 | 10 | 5 | 4 | 4 | 6 | 4 | 2 | ROBUST_ACROSS_WEIGHTS |
| 6 | 1318 | Andre Russell | 92.06 | 27.53 | 35 | 19.56 | 9.97 | 6 | 6 | 5 | 7 | 6 | 2 | ROBUST_ACROSS_WEIGHTS |
| 7 | 6819 | Yashasvi Jaiswal | 89.85 | 30 | 35 | 16.7 | 8.15 | 7 | 7 | 7 | 12 | 11 | 5 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 2756 | Shashank Singh | 88.65 | 24.7 | 29.82 | 24.64 | 9.49 | 8 | 8 | 8 | 5 | 7 | 3 | ROBUST_ACROSS_WEIGHTS |
| 9 | 7897 | Tilak Varma | 86.52 | 24.81 | 28.74 | 22.97 | 10 | 9 | 12 | 11 | 8 | 8 | 4 | ROBUST_ACROSS_WEIGHTS |
| 10 | 1077 | David Miller | 86.45 | 25.6 | 29.09 | 21.76 | 10 | 10 | 10 | 10 | 10 | 9 | 1 | ROBUST_ACROSS_WEIGHTS |

### 7.2 Bowling Weight Sensitivity (Top 10)
| provisional_rank | canonical_player_id | player_name | provisional_fixed_weight_score | contrib_maint | contrib_abs | contrib_cons | contrib_sample | rank_balanced_default | rank_maintenance_heavy | rank_absolute_heavy | rank_consistency_heavy | rank_equal_weights | max_rank_shift | ranking_sensitivity_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 781 | Sunil Narine | 95.78 | 25.88 | 35 | 25 | 9.9 | 1 | 1 | 1 | 1 | 1 | 0 | ROBUST_ACROSS_WEIGHTS |
| 2 | 4722 | Rashid Khan | 87.36 | 24.87 | 30.44 | 22.05 | 10 | 2 | 2 | 2 | 2 | 2 | 0 | ROBUST_ACROSS_WEIGHTS |
| 3 | 305 | R Ashwin | 85.03 | 24.32 | 27.77 | 23.21 | 9.73 | 3 | 3 | 4 | 3 | 3 | 1 | ROBUST_ACROSS_WEIGHTS |
| 4 | 2933 | Jasprit Bumrah | 84.71 | 21.2 | 31.05 | 22.54 | 9.92 | 4 | 6 | 3 | 4 | 4 | 3 | ROBUST_ACROSS_WEIGHTS |
| 5 | 4900 | Wanindu Hasaranga | 83.6 | 23.09 | 29.1 | 21.46 | 9.95 | 5 | 5 | 5 | 5 | 5 | 0 | ROBUST_ACROSS_WEIGHTS |
| 6 | 2687 | Roston Chase | 82.71 | 25.99 | 28.86 | 19.82 | 8.04 | 6 | 4 | 6 | 6 | 7 | 3 | ROBUST_ACROSS_WEIGHTS |
| 7 | 722 | Liam Dawson | 78.76 | 22.76 | 26.07 | 22.4 | 7.53 | 7 | 10 | 9 | 7 | 15 | 8 | RANKING_SENSITIVE_TO_WEIGHTS |
| 8 | 19316 | Maheesh Theekshana | 78.76 | 22.43 | 25.83 | 20.57 | 9.93 | 8 | 7 | 8 | 9 | 6 | 3 | ROBUST_ACROSS_WEIGHTS |
| 9 | 7920 | Nathan Ellis | 78.66 | 22.31 | 27.89 | 19.33 | 9.13 | 9 | 11 | 7 | 10 | 9 | 4 | ROBUST_ACROSS_WEIGHTS |
| 10 | 2315 | Reece Topley | 78.38 | 22.98 | 24.85 | 22.04 | 8.51 | 10 | 9 | 12 | 8 | 10 | 4 | ROBUST_ACROSS_WEIGHTS |

---

## 8. System B: Rajasthan Royals IPL 2026 Audit & 2027 Auction Strategy

### 8.1 RR 2026 Phase Profile & Tactical Deficiencies (`USER_PROVIDED_UNVERIFIED` Provenance Disclosed)
| phase | overs_range | team_batter_runs | team_balls_faced | team_batting_sr | team_bowling_legal_balls | team_bowler_wickets_taken | team_bowling_dot_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Powerplay | 1-6 | 1079 | 576 | 187.33 | 577 | 28 | 42.63 |
| Middle | 7-15 | 1262 | 825 | 152.97 | 840 | 44 | 27.14 |
| Death | 16-20 | 611 | 374 | 163.37 | 407 | 26 | 32.19 |

- **Primary Empirical Weaknesses:** Death-Over Pace Defense (High Concession Rate at the Death), Overseas Finisher Underperformance (Shimron Hetmyer Contract Concentration vs Output), Indian Fast Bowling Depth (Over-reliance on Jofra Archer), Middle-Over Spin Penetration (Ravi Bishnoi Limited Exposure & Match Count), Injury & Replacement Instability (Sam Curran Groin Injury & Temporary Contract).

### 8.2 Prioritized 2027 Recruitment Roles (`RR_REQUIRED_ROLES.csv`)
| priority | role_title | urgency | existing_rr_cover | budget_allocation_cr |
| --- | --- | --- | --- | --- |
| 1 | Indian Frontline Fast Bowler | CRITICAL | Tushar Deshpande & Sandeep Sharma | 10.0-13.0 |
| 2 | Overseas Death-Over Specialist | CRITICAL | Nandre Burger & Jofra Archer | 8.0-11.0 |
| 3 | Economical Middle-Over Spinner | IMPORTANT | Ravi Bishnoi & Ravindra Jadeja | 3.0-5.0 |
| 4 | Domestic Lower-Order Finisher | IMPORTANT | Shubham Dubey & Donovan Ferreira | 2.0-3.0 |
| 5 | All-Rounder Availability Cover | OPTIONAL | Dasun Shanaka (temporary contract) | 1.5-3.0 |

### 8.3 Retention, Release & Overseas Slot Governance (`RR_RETENTION_SCENARIOS.csv`, `RR_AUCTION_BUDGET_SCENARIOS.csv`)
- **Released Contracts (24.95 Cr Freed):** Releases Shimron Hetmyer (11.00 Cr, Overseas), Tushar Deshpande (6.50 Cr), Sandeep Sharma (4.00 Cr), Adam Milne (2.40 Cr, Overseas), Kuldeep Sen (0.75 Cr), and Lhuan-dre Pretorius (0.30 Cr, Overseas). Combined with carry-over cap headroom, this establishes the ₹27.60 Cr base auction purse.
- **Overseas Slot Arithmetic Disclosure:** Core retentions include **3 overseas players** (`Jofra Archer`, `Donovan Ferreira`, `Nandre Burger`) plus **1 `CONFLICTING_STATUS` contract** (`Sam Curran vs Dasun Shanaka`). Against the IPL maximum of 8 overseas squad slots (4 in Playing XI), releasing 3 overseas players frees ample squad headroom; if `Sam Curran` is confirmed retained (4th squad overseas), 4 squad overseas slots (and 1 XI overseas slot alongside Archer & Ferreira) remain open, consistent with targeting **1 frontline overseas death bowler** (`Matheesha Pathirana` / `Nuwan Thushara`).

| scenario_name | total_purse_cr | overseas_slots_available | priority_1_indian_pacer_cr | priority_2_overseas_death_cr | priority_3_spinner_cr | priority_4_finisher_cr | squad_fillers_cr | feasibility_assessment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Base Purse Scenario (No Cap Increase) | 27.6 | 3 | 10.50 (Prasidh/Avesh) | 9.50 (Pathirana/Thushara) | 4.00 (Sai Kishore) | 2.50 (Ashutosh Sharma) | 1.10 (Uncapped backups) | Highly Feasible: Fills all 4 key gaps within ₹27.60 Cr purse |
| Expanded Cap Scenario (+₹5 Cr Increase) | 32.6 | 3 | 12.50 (Aggressive bid for Prasidh) | 11.50 (Aggressive bid for Pathirana) | 4.50 (Sai Kishore) | 3.00 (Ashutosh Sharma) | 1.10 (Backups) | Premium Scenario: Allows winning bidding wars on top-tier pacer and death specialist |
| Conservative Budget Scenario | 27.6 | 3 | 8.00 (Avesh Khan / Mukesh Kumar) | 5.50 (Nuwan Thushara) | 3.50 (Sai Kishore) | 2.50 (Ashutosh Sharma) | 8.10 (Purse Reserve for Auction Flexibility) | Prudent Scenario: Retains ₹8.10 Cr reserve by securing Thushara over Pathirana |

### 8.4 Auction Player-Fit Evaluation Matrix (Synced Dynamically from System A V4 Rankings)
| player_name | target_gap | is_overseas | universal_ranking | price_estimate | recommendation_category | evidence_verification_status |
| --- | --- | --- | --- | --- | --- | --- |
| Prasidh Krishna | Indian Frontline Fast Bowler | False | Rank #64 Universal V4 Bowler (Score 54.59, BOWL_SPECIALIST) | ₹8.0 - ₹11.0 Cr | Strong Fit | VERIFIED |
| Avesh Khan | Indian Frontline Fast Bowler | False | Rank #66 Universal V4 Bowler (Score 52.61, BOWL_SPECIALIST) | ₹7.0 - ₹9.5 Cr | Strong Fit | VERIFIED |
| Mukesh Kumar | Indian Frontline Fast Bowler | False | Rank #75 Universal V4 Bowler (Score 48.36, BOWL_SPECIALIST) | ₹5.5 - ₹8.0 Cr | Conditional Fit | VERIFIED |
| Akash Deep | Indian Frontline Fast Bowler | False | Unranked in V4 Bowling Pool (BOWL_SPECIALIST: EFF_CRISIS_BALLS<120) | ₹4.0 - ₹6.5 Cr | Conditional Fit | VERIFIED |
| Matheesha Pathirana | Overseas Death-Over Specialist | True | Rank #25 Universal V4 Bowler (Score 71.72, BOWL_SPECIALIST) | ₹8.0 - ₹9.5 Cr (Ceiling: ₹11.0 Cr) | Strong Fit | VERIFIED |
| Gerald Coetzee | Overseas Death-Over Specialist | True | Rank #86 Universal V4 Bowler (Score 40.28, BOWL_PRIMARY_AR) | ₹6.0 - ₹8.5 Cr | Conditional Fit | VERIFIED |
| Nuwan Thushara | Overseas Death-Over Specialist | True | Rank #30 Universal V4 Bowler (Score 69.86, BOWL_SPECIALIST) | ₹4.5 - ₹5.5 Cr (Ceiling: ₹6.5 Cr) | Strong Fit | VERIFIED |
| R Sai Kishore | Economical Middle-Over Spinner | False | Rank #60 Universal V4 Bowler (Score 56.12, BOWL_SPECIALIST) | ₹3.5 - ₹4.5 Cr (Ceiling: ₹5.5 Cr) | Strong Fit | VERIFIED |
| Rahul Chahar | Economical Middle-Over Spinner | False | Rank #50 Universal V4 Bowler (Score 60.62, BOWL_SPECIALIST) | ₹3.0 - ₹4.5 Cr | Low Priority | VERIFIED |
| Akeal Hosein | Economical Middle-Over Spinner | True | Rank #46 Universal V4 Bowler (Score 62.18, BOWL_SPECIALIST) | ₹2.5 - ₹4.0 Cr | Conditional Fit | VERIFIED |
| Ashutosh Sharma | Domestic Lower-Order Finisher | False | Rank #4 Universal V4 Batter (Score 93.66, BAT_SPECIALIST) | ₹2.5 - ₹3.5 Cr (Ceiling: ₹4.5 Cr) | Strong Fit | VERIFIED |
| Abhinav Manohar | Domestic Lower-Order Finisher | False | Rank #152 Universal V4 Batter (Score 19.01, BAT_SPECIALIST) | ₹2.0 - ₹3.5 Cr | Strong Fit | VERIFIED |
| Sameer Rizvi | Domestic Lower-Order Finisher | False | Rank #153 Universal V4 Batter (Score 15.23, BAT_SPECIALIST) | ₹1.5 - ₹2.5 Cr | Conditional Fit | VERIFIED |

---

## 9. Reproducibility & Verification Gates

- Pipeline execution: `.venv\Scripts\python scripts/compute_v3_rankings.py`
- Independent verification: `.venv\Scripts\python scripts/verify_v3_rankings.py`
- Automated test suite: `.venv\Scripts\python -m pytest tests/ -v`
