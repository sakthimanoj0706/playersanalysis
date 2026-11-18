# PRESSURE METHODOLOGY V4 — SupeRR Intelligence V4

## 1. Scientific Quarantine of Score-Based Win Probability
- **Blocked Data Verification**: Because `extras1_runs` is a categorical code and `runs` excludes multi-run wides/byes/leg-byes/penalties, reconstructing non-DLS run-margin results fails on **`342 / 390` matches**.
- **Consequence (`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`)**: Exact team totals, first-innings target, runs remaining, required run rate (`RRR`), and true Leverage `C_t = |dWP / dRun|` are **not reconstructible** without fabrication and are therefore formally blocked.
- **Chronological B1 `WP_obs` Benchmark (Score-Blind Diagnostic Only)**:
| metric | n_eval | split | status |
| --- | --- | --- | --- |
| innings_1_train<=2024_test>2024 | 39959 | AUC=0.6697, Brier=0.2288, CalSlope=1.1995 | QUARANTINED_SCORE_BLIND |
| innings_2_train<=2024_test>2024 | 36215 | AUC=0.7558, Brier=0.202, CalSlope=0.9093 | QUARANTINED_SCORE_BLIND |
  - Score-blind `WP_obs` omits score/target context and exhibits poor first-innings discrimination and slope miscalibration (`CalSlope` deviation from `1.0`), confirming B1/B2 cannot serve as a calibrated match-leverage model.

## 2. Approved V4 Proxy: `RESOURCE_STRESS_PROXY` (`v4.0-b3-resource-stress`)
V4 uses two **strictly pre-delivery, role-separated** resource-stress proxies fit purely from observable innings state (`innings`, `overid`, `innings_phase`, `match_format`, `balls_rem_before`, `wkts_before`, with DLS revised balls handled directly in balls):

1. **Batting Resource Depletion Proxy (`bat_pressure` in `[0, 1]`)**:
   - Fits a monotone empirical remaining-batter-runs curve $R(u, w) = R_0 (1 - e^{-b u}) ((10 - w)/10)^{\gamma}$ on non-DLS regular innings (`Inn 1` params: `[238.014, 1.192, 0.531]`, `Inn 2` params: `[396.488, 0.473, 0.306]`).
   - Measures pre-delivery wicket depletion $1 - ((10 - w_t)/10)^{\gamma}$ minus stage expectation $\mathbb{E}[\text{depl} \mid \text{innings}, \text{overid}]$ so early/middle-over collapses and resource-depleted situations score high without falsely labeling every routine death ball as high batting stress.
   - Mapped via empirical training CDF quantiles to `[0, 1]`; high pressure threshold = **`p >= 0.75`**, low/normal baseline zone = **`p <= 0.25`**.

2. **Bowling Scoring-Threat Proxy (`bowl_pressure` in `[0, 1]`)**:
   - Ridge regression predicting pre-delivery expected batter scoring difficulty $\mathbb{E}[\text{batter\_runs} \mid \text{phase}, \text{innings}, \text{is\_t20i}, u, w_{\text{rem}}, \text{interactions}]$ (fit strictly on training data inside validation folds).
   - Mapped via empirical training CDF quantiles to `[0, 1]` so death-over defending and high-scoring threat phases naturally register high bowling consequence.

## 3. Proxy Limitations & Classification Banner
- This model is classified as **`V4 PROVISIONAL — RESOURCE STRESS PROXY`** (never labeled a calibrated score-based Win Probability / Match Leverage Index `L_t`).
- Because chase deficit and target are unavailable in the scoped CSVs, `bat_pressure` cannot distinguish a tense 12-runs-off-6-balls chase from a dead 70-off-6 chase unless wickets have already fallen.
