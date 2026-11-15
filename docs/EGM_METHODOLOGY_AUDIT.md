# EGM Methodology Audit — SupeRR Intelligence V3

**Audit Identifier:** `EGM-METHODOLOGY-AUDIT-001`  
**Repository:** `d:\rrhackthon` (Branch: `fix/v3-pre-submission-consistency-001`, Commit: `3b18f48`)  
**Audit Mode:** Strictly Read-Only (Zero Code or Ranking Modifications)  
**Audit Date:** 15 November 2026

---

## 1. Pressure Classification Audit (`src/pressure_engine/v3_pressure_model.py`)

### 1.1 Available vs. Missing Contextual Features in the Raw Dataset
Inspection of `data/ball_by_ball_ipl_t20i.csv` (`194,014` deliveries across `837` matches) and `src/context_engine/innings_context.py`:

| Contextual Feature | Available in Raw Data? | Used in `V3PressureModel`? | Audit Finding & Evidence |
| :--- | :---: | :---: | :--- |
| **Exact Wickets Fallen Before Ball (`wickets_fallen_before`)** | **YES** (`is_wicket` cumulative sum per innings) | **YES** (`c_wkt` in batting, `c_resource` in bowling) | `innings_context.py:100-104` accurately computes exact wickets fallen before each delivery. *(Note: The documentation's claim that `batting_position` is used as a proxy for wickets fallen comes from legacy V1/V2 notes; in V3 `wickets_fallen_before` is exact, but `batting_crisis_score > 5.50` behaves like a batting-order filter because `c_wkt = 0.45 * wickets_fallen_before` requires 4+ wickets down to reach `> 5.50`.)* |
| **Balls Remaining / Over & Phase (`innings_phase`, `overid`)** | **YES** | **YES** (Coarse 3-phase step function only) | Uses coarse step multipliers (`powerplay`, `middle`, `death`) instead of continuous balls remaining (`120 - legal_balls_bowled`). |
| **Recent Wicket Cluster (`wickets_in_last_12_legal_balls`)** | **YES** | **YES** (Batting `c_cluster`) | **Bug (`GROUP A`):** `innings_context.py:121-131` indexes only `is_legal == True`, **ignoring 44 wickets (run-outs/stumpings) and 126 boundaries that occurred on wides/no-balls**! |
| **Recent Dot & Boundary Momentum (`last_12_legal_balls`)** | **YES** | **YES** | **Bug (`GROUP B`):** `innings_context.py:78` defines dots as `(runs == 0) & (extras_category == 'None')` (excluding 2,661 leg-byes and 505 byes), whereas `rr_data_adapter.py:55` defines dots as `is_legal_ball & (batter_runs == 0)` (including leg-byes/byes)—a **3,427-ball discrepancy** between pressure features and bowler evaluation. |
| **Batter Balls Faced (`batter_balls_faced`)** | **YES** | **YES** (`c_novelty` for `bf < 5`) | Gives up to `+1.5` points for the first 5 balls a batter faces. Causes batters to enter the crisis filter for **1 to 3 balls** upon arrival and then exit once `bf >= 5`, generating **2,060 crisis batter-match appearances of 1–2 balls (`47.0%` of all crisis batter-matches)**! |
| **Innings Number (`1` vs `2` — Setting vs Chasing)** | **YES** (`innings` column) | **NO (Ignored!)** | Even without exact extras run counts, `innings == 2` (chasing) vs `innings == 1` (setting) and cumulative `batter_runs` + minimum extras (`+1` per wide/no-ball) are available in `ball_by_ball_ipl_t20i.csv`, yet `V3PressureModel` treats 1st and 2nd innings identically! |
| **Exact Target & Required Run Rate (RRR)** | **PARTIAL / QUARANTINED** (`extras1_runs` is enum 1–7) | **NO (Quarantined)** | Because `extras1_runs` records the extra type (`2=wide, 3=legbyes, 4=byes`) without the run magnitude (e.g., 1 wide vs 5 wides), exact scoreboard targets are unobservable. Quarantining exact RRR is justified, though an approximate lower-bound RRR (`batter_runs + count(wide/noball/legbye/bye)`) could have been tested as a feature. |
| **Match Stakes (Playoffs / Knockouts / Close Finishes)** | **YES** (`matches_ipl_t20i.csv` dates/stages) | **NO (Ignored!)** | Eliminators, Qualifiers, and Finals receive the exact same pressure score as dead-rubber league games. |

### 1.2 Mathematical Proof of Pressure Misclassification (`v3_pressure_model.py`)

1. **Bowling Defensive Pressure (`src/pressure_engine/v3_pressure_model.py:194-261`) Misclassifies Normal Powerplay & Death Bowling as "Crisis" and Post-Collapse Middle Overs as "Normal":**
   - Formula: $\text{Score} = c_{\text{resource}} + c_{\text{phase}} + c_{\text{momentum}} + c_{\text{rotation}}$.
   - In the **Powerplay** (`c_phase = 2.0`), when 0–2 wickets are down (`w_rem >= 8` $\rightarrow$ `c_resource = 3.0`), the minimum possible score is $3.0 + 2.0 + 0.0 + 0.0 = \mathbf{5.00 > 4.50}$.
   - **Result:** **`0.00%` (`0 / 59,331`) of Powerplay deliveries with 0–2 wickets down are classified as Normal (`<= 4.50`)**, while **`71.12%` of all Powerplay deliveries are classified as High/Extreme Pressure (`> 6.50`)**!
   - Across the entire dataset (`185,951` legal balls), **`52.55%` are High/Extreme Pressure (`> 6.50`)**, **`36.91%` are Moderate (`4.50 < score <= 6.50`)**, and **only `10.66%` (`19,816` balls) are Normal (`<= 4.50`)**—of which **`87.75%` are in the Middle overs** and **`98.94%` occur when $\ge 3$ wickets have already fallen**!
2. **Batting Crisis Pressure (`src/pressure_engine/v3_pressure_model.py:120-191`) Misclassifies Top-Order Pressure as "Normal" and Lower-Order Entry as "Crisis":**
   - Because `c_wkt = min(3.5, wickets_fallen_before * 0.45)` and `phase_mult` is `0.95` (Powerplay), `1.00` (Middle), and `1.25` (Death), a top-3 batter (`wickets_fallen_before <= 1`, `c_wkt <= 0.45`) in the Powerplay or Middle overs can almost never exceed `5.50`.
   - **Empirical Crisis Rate by Batting Position (`ball_by_ball_with_pressure.parquet`):**
     - Order 1: `0.26%` (`84 / 31,795` balls)
     - Order 2: `0.24%` (`76 / 32,260` balls)
     - Order 3: `0.37%` (`106 / 28,944` balls)
     - Order 4: `0.87%` (`243 / 27,808` balls)
     - Order 5: `3.21%` (`719 / 22,365` balls)
     - Order 6: `10.07%` (`1,691 / 16,785` balls)
     - Order 7: `23.87%` (`2,882 / 12,074` balls)
     - Orders 8–11: `45.82%` to `91.61%`!

---

## 2. Individual Performance Measurement & Composite Formula Audit

### 2.1 Batting Performance & Why Iftikhar Ahmed (#9) and Jaker Ali Anik (#5) Make the Top 10

In `scripts/compute_v3_rankings.py:379-396`, the batting score is:
$$\text{Score}_{\text{bat}} = 35 \cdot \text{minmax}(\text{sr\_maint}) + 35 \cdot \text{minmax}(\text{shrunk\_crisis\_sr}) + 20 \cdot \text{minmax}(\text{consistency}) + 10 \cdot \text{sample\_conf}$$

1. **Why Iftikhar Ahmed (`ID=3056`, Crisis SR `127.50` vs Cohort Mean `140.20`) Ranks #9 (`62.38`):**
   - **Normal SR (`120.96` across 291 balls):** 2nd lowest in the entire 39-player eligible cohort (`#38 / 39`, ahead of only Clive Madande at `119.66`).
   - **Crisis SR (`127.50` across exactly `40` balls in `11` matches):** 6th lowest in the eligible cohort (`#34 / 39`, `-12.70` SR points below the cohort mean of `140.20`), yielding only **`14.71 / 35.00` points** on absolute crisis performance (`shrunk_crisis_sr = 132.39`).
   - **Why does he rank #9 ahead of #11 Ramandeep Singh (`155.71` SR), #12 Marcus Stoinis (`163.38` SR), and #13 Rinku Singh (`150.82` SR on `122` balls)?**
     - **Flaw 1 — Unweighted Micro-Cameo Consistency (`20.00 / 20.00` pts):** In `compute_v3_rankings.py:329-338`, `m_srs = (m_runs / m_balls) * 100.0` computes an unweighted strike rate for every match with $\ge 1$ crisis ball (`CV = std_sr / mean_sr`). Across Iftikhar's 11 crisis matches, **he never faced more than 6 crisis balls in a match** (`1b, 1b, 1b, 2b, 3b, 4b, 5b, 5b, 6b, 6b, 6b`), nudging singles (`1(1)=100 SR`, `3(3)=100 SR`, `5(4)=125 SR`, `7(5)=140 SR`). Because he never hit a boundary in a 1–2 ball cameo, his unweighted match SRs have `CV = 0.4779` (`consistency_score = 0.5497`), the **#1 highest in the cohort**, handing him the full **`20.00 / 20.00` consistency points**!
     - Meanwhile, **Rinku Singh (`#13`, `122` crisis balls)** hit `6(1)=600 SR` and `4(1)=400 SR` in 1-ball crisis cameos, which inflated his `std_sr` to `135.28` (`CV = 0.8234`) and slashed his consistency score to **`9.13 / 20.00` pts** (**-10.87 pts behind Iftikhar**)! Similarly, **Jitesh Sharma (`#10`, `172.55` crisis SR)** gets only **`4.12 / 20.00` pts** and **Shashank Singh (`#25`, `152.56` crisis SR)** gets **`0.00 / 20.00` pts** for hitting boundaries in short cameos!
     - **Flaw 2 — Low-Baseline Ratio Inflation (`20.95 / 35.00` pts):** Because Iftikhar's normal SR is `120.96`, a crisis SR of `127.50` gives `sr_maintenance = 1.054x` (`20.95 / 35.00` pts)—higher than Rinku Singh (`150.82 / 147.56 = 1.022x -> 19.49 pts`), Marcus Stoinis (`163.38 / 158.58 = 1.030x -> 19.86 pts`), and Abdul Samad (`169.57 / 168.67 = 1.005x -> 18.71 pts`).
2. **Why Jaker Ali Anik (`ID=4773`, Crisis SR `139.68` vs Cohort Mean `140.20`) Ranks #5 (`65.13`):**
   - Jaker Ali Anik also has a crisis SR below the cohort mean (`139.68`, `#26 / 39`), but has the **3rd-lowest normal SR in the cohort (`122.38`, `#37 / 39`)**, giving him `sr_maintenance = 1.141x` (**`24.93 / 35.00` pts**).
   - Furthermore, **9 of his 15 crisis matches (`60%`) are 1-to-3 ball cameos** (including four `1(1)=100 SR` and one `2(2)=100 SR`), suppressing his `CV` (`0.6274`) and giving him **`14.79 / 20.00` consistency points**, vaulting him to **#5 in the world** ahead of Abdul Samad (`169.57` SR), David Miller (`166.07` SR), and MS Dhoni (`154.89` SR)!
3. **Does the Methodology Justify Iftikhar Ahmed (#9) and Jaker Ali Anik (#5)?**
   - **Mathematically under the written code:** Yes, `verify_v3_rankings.py` confirms the arithmetic is exact.
   - **Scientifically / Domain-wise against the Hackathon Prompt:** **NO.** A metric that awards `#1` consistency (`20/20` pts) for averaging `3.6` balls per match at `127.50` SR while punishing Rinku Singh (`9.13/20` pts) and Jitesh Sharma (`4.12/20` pts) for hitting first-ball sixes (`600 SR`) in 1–2 ball cameos is a **statistical artifact of unweighted 1-ball ratio variance**, not true consistency under pressure.

---

### 2.2 Bowling Performance & Construct Mismatch (`scripts/compute_v3_rankings.py:488-667`)

1. **Construct Split Between Maintenance (Dot %) and Absolute Performance (Wicket Rate):**
   - `contrib_maint` (35%) measures **only** `dot_maintenance = crisis_dot_pct / norm_dot_pct`.
   - `contrib_abs` (35%) measures **only** `shrunk_crisis_wr` (crisis wicket rate), **without comparing crisis wicket rate to `norm_wicket_rate`**, and **without including `crisis_dot_pct` or runs/boundaries conceded off the bat**.
   - `contrib_cons` (20%) in `scripts/compute_v3_rankings.py:609` measures **only** match-to-match `crisis_dot_pct` CV (diverging from `src/ranking_engine/pressure_rankings.py:414`, which used `dot_rate + 2.0 * wkt_rate`).
   - `contrib_sample` (10%) uses un-normalized `sample_confidence = clip(log1p(crisis_balls)/log1p(250), 0.1, 1.0)`. Because all 39 eligible bowlers have `crisis_balls >= 225` (37 of 39 have `>= 250`), **37 of 39 bowlers receive `10.00 / 10.00` points** and the other 2 receive `9.81` and `9.84` pts—making the 10% sample weight a **dead constant** (`0.19` pt spread).
2. **8 of the Top 10 Bowlers Perform WORSE in Dot % Under Pressure (`raw_dot_maintenance < 1.0`), and 3 Perform Worse on BOTH Dot % and Wicket Rate:**
   - Because `norm_balls` (`score <= 4.50`) are post-collapse middle-over deliveries, **37 of the 39 eligible bowlers (`94.87%`) have `raw_dot_maintenance < 1.000`** (`range = [0.517, 1.096]`).
   - Min-max scaling `[0.517, 1.096]` onto `[0, 35]` points turns a **16.6% drop in dot-ball performance (`0.834x`, #4 Arshdeep Singh)** into **`19.16 / 35.00` "maintenance" points**!
   - **#4 Arshdeep Singh (`0.834x` dot maint, `5.94%` crisis WR vs `6.71%` norm WR = `0.886x` wkt maint)**, **#6 Taskin Ahmed (`0.833x` dot maint, `6.34%` crisis WR vs `7.00%` norm WR = `0.906x` wkt maint)**, and **#8 Avesh Khan (`0.861x` dot maint, `5.82%` crisis WR vs `5.88%` norm WR = `0.989x` wkt maint)** degrade under pressure on **every metric tracked**, yet make the Top 10!
   - Conversely, **#10 Gudakesh Motie** has a below-average crisis wicket rate (`4.44%` vs `5.00%` normal and `5.52%` cohort mean $\rightarrow$ `5.63 / 35` abs pts, `5.60 / 20` cons pts), but makes the Top 10 solely because a low normal dot rate (`31.00%` on exactly `100` normal balls) gives him `1.096x` dot maintenance (`35.00 / 35.00` maint pts).

---

### 2.3 Empirical Bayes Shrinkage & Min-Max Normalization Flaws

1. **Batter Shrinkage `K = 25.0` Under-Shrinks Small Samples (`src/reliability/v3_reliability.py:247-301`):**
   - Within-delivery variance of `batter_runs * 100` in crisis is $\sigma^2 = 32,208.54$ ($\text{SD} = 179.47$ SR pts), while between-batter variance across the 39 eligible batters after subtracting sampling noise is $\hat{\tau}^2 = 48.06$ (or $572.56$ unadjusted).
   - True Empirical Bayes shrinkage implies $K = \sigma^2 / \tau^2 \approx 670$ balls (or $56.3$ balls unadjusted)—more than double the hardcoded `K = 25.0`. And `sr_maintenance` (`35%` weight) uses **unshrunk** raw `crisis_sr / norm_sr`.
2. **Bowler Beta-Binomial Shrinkage Slams Into the Hardcoded `100.0` Clip (`src/reliability/v3_reliability.py:347`):**
   - Method-of-moments concentration `m_sum = 397.56` is clipped by `np.clip(..., 5.0, 100.0)` to `100.0` (`prior_alpha = 5.5151, prior_beta = 94.4849`), turning `ESTIMATED_EMPIRICAL_BAYES` into a capped $K=100$ prior.
3. **Min-Max Scaling Violation of Independence of Irrelevant Alternatives (IIA):**
   - Because `_minmax` scales each component between the single minimum and maximum player of the 39-player cohort:
     - Removing #39 bowler **Suyash Sharma** (`dot_maintenance = 0.517`, an extreme bottom outlier compared to #38 Jamie Overton at `0.672`) causes **#10 Gudakesh Motie to jump 4 places to #6**, **#5 Ravi Bishnoi to overtake #4 Arshdeep Singh**, and **#7 Wanindu Hasaranga to drop to #10**.
     - Adding 39-ball **Nicholas Pooran** (`shrunk_crisis_sr = 182.89`) shifts the upper bound of `norm_abs` and flips the relative order of **#8 MS Dhoni and #9 Iftikhar Ahmed**.

---

## 3. Weight Sensitivity Audit (`data/outputs/v3/RANKING_WEIGHT_SENSITIVITY.csv`)

### 3.1 Top 10 Batters Weight Sensitivity Across 5 Prespecified Configurations

| Baseline Rank | Player Name (`ID`) | Default `(35/35/20/10)` | Maint Heavy `(50/25/15/10)` | Abs Heavy `(25/50/15/10)` | Cons Heavy `(30/30/30/10)` | Equal `(25/25/25/25)` | Max Rank Shift | Status & Component Driving Shift |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#1** | Tilak Varma (`7897`) | 1 | 1 | 1 | 1 | 1 | **0** | `ROBUST_ACROSS_WEIGHTS` (#1 on both Maint & Abs) |
| **#2** | Matthew Wade (`796`) | 2 | 2 | 2 | 2 | 2 | **0** | `ROBUST_ACROSS_WEIGHTS` |
| **#3** | Daryl Mitchell (`4106`) | 3 | 3 | 3 | 3 | 3 | **0** | `ROBUST_ACROSS_WEIGHTS` |
| **#4** | Liam Livingstone (`4391`) | 4 | 4 | 4 | 5 | 4 | **1** | `ROBUST_ACROSS_WEIGHTS` |
| **#5** | **Jaker Ali Anik (`4773`)** | **5** | **5** | **11** *(Out)* | **6** | **5** | **6** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (Drops out of Top 10 under `absolute_heavy` due to `139.68` crisis SR) |
| **#6** | **Abdul Samad (`7446`)** | **6** | **11** *(Out)* | **5** | **7** | **7** | **6** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (Drops out of Top 10 under `maintenance_heavy` due to `1.005x` maint) |
| **#7** | David Miller (`1077`) | 7 | 9 | 6 | 8 | 9 | **3** | `ROBUST_ACROSS_WEIGHTS` |
| **#8** | MS Dhoni (`8`) | 8 | 7 | 8 | 9 | 8 | **2** | `ROBUST_ACROSS_WEIGHTS` |
| **#9** | **Iftikhar Ahmed (`3056`)** | **9** | **10** | **14** *(Out)* | **4** | **6** | **10** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (Swings 10 ranks: #4 under `consistency_heavy` vs #14 under `absolute_heavy`) |
| **#10** | **Jitesh Sharma (`3916`)** | **10** | **8** | **7** | **12** *(Out)* | **14** *(Out)* | **7** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (Drops out of Top 10 when consistency weight increases due to `4.12/20` cons pts) |

### 3.2 Top 10 Bowlers Weight Sensitivity Across 5 Prespecified Configurations

*(Note: `RANKING_SOURCE_OF_TRUTH.json` and the mandatory disclosure mention batter weight sensitivity at ranks 5, 6, 9, 10, but fail to disclose that **59.0% (`23/39`) of eligible bowlers and 4 of the Top 10 bowlers—ranks 5, 7, 9, and 10—are also `RANKING_SENSITIVE_TO_WEIGHTS`**!)*

| Baseline Rank | Player Name (`ID`) | Default `(35/35/20/10)` | Maint Heavy `(50/25/15/10)` | Abs Heavy `(25/50/15/10)` | Cons Heavy `(30/30/30/10)` | Equal `(25/25/25/25)` | Max Rank Shift | Status & Component Driving Shift |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#1** | Matheesha Pathirana (`8661`) | 1 | 1 | 1 | 1 | 1 | **0** | `ROBUST_ACROSS_WEIGHTS` |
| **#2** | Keshav Maharaj (`1944`) | 2 | 2 | 3 | 4 | 5 | **3** | `ROBUST_ACROSS_WEIGHTS` |
| **#3** | M. Rishad Hossain (`8380`) | 3 | 5 | 2 | 5 | 4 | **3** | `ROBUST_ACROSS_WEIGHTS` |
| **#4** | Arshdeep Singh (`6464`) | 4 | 6 | 6 | 2 | 2 | **4** | `ROBUST_ACROSS_WEIGHTS` |
| **#5** | **Ravi Bishnoi (`7503`)** | **5** | **4** | **9** | **3** | **3** | **6** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (Low crisis WR `5.56%` drops him to #9 under `absolute_heavy`) |
| **#6** | Taskin Ahmed (`2681`) | 6 | 10 | 7 | 6 | 6 | **4** | `ROBUST_ACROSS_WEIGHTS` |
| **#7** | **Wanindu Hasaranga (`4900`)** | **7** | **14** *(Out)* | **4** | **8** | **8** | **10** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (`0.749x` dot maintenance plunges him to #14 under `maintenance_heavy`) |
| **#8** | Avesh Khan (`3653`) | 8 | 8 | 10 | 7 | 7 | **3** | `ROBUST_ACROSS_WEIGHTS` |
| **#9** | **Ish Sodhi (`2526`)** | **9** | **9** | **5** | **13** *(Out)* | **13** *(Out)* | **8** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (Low consistency `2.53/20` pts drops him to #13 under `consistency_heavy`/`equal`) |
| **#10** | **Gudakesh Motie (`3276`)** | **10** | **3** | **19** *(Out)* | **15** *(Out)* | **15** *(Out)* | **16** | **`RANKING_SENSITIVE_TO_WEIGHTS`** (**Swings 16 places from #3 to #19!** Driven entirely by `1.096x` dot maintenance vs `4.44%` crisis WR) |
