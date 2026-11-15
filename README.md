# SupeRR Intelligence V4.2

**Current Release:** **`V4.2 PROVISIONAL — RESOURCE STRESS`** (`fix/v4-2-statistical-corrections-20261115`)  
**Official Hackathon Objective:** *"Identify the batters and bowlers who perform most consistently under pressure compared with their own usual performance levels."*

> **Mandatory Provisional Disclosure:** Complete innings-total and chase-target reconstruction from the raw ball-by-ball dataset is blocked (`0/837` zero-extras matches; `342/390` non-DLS run-margin checks fail). Because runs required and required run rate are unavailable across deliveries, **no calibrated match-leverage variable exists**. V4.2 estimates relative player resilience under **pre-delivery resource-stress proxies** (`BATTING_WICKET_DEPLETION_ANOMALY` and `BOWLING_EXPECTED_SCORING_THREAT`).

---

## Key Submission Documents

### Authoritative Final Deliverables (`data/outputs/final/`)
- **Authoritative Top 10 Batters CSV:** [data/outputs/final/FINAL_TOP_10_BATTERS.csv](data/outputs/final/FINAL_TOP_10_BATTERS.csv)
- **Authoritative Top 10 Bowlers CSV:** [data/outputs/final/FINAL_TOP_10_BOWLERS.csv](data/outputs/final/FINAL_TOP_10_BOWLERS.csv)
- **All Eligible & Ineligible Player Estimates CSV:** [data/outputs/final/ALL_PLAYER_FINAL_ESTIMATES.csv](data/outputs/final/ALL_PLAYER_FINAL_ESTIMATES.csv)
- **Final Methodology Report:** [data/outputs/final/FINAL_METHODOLOGY_REPORT.md](data/outputs/final/FINAL_METHODOLOGY_REPORT.md)
- **Final Player Justifications (All 20 Players):** [data/outputs/final/FINAL_PLAYER_JUSTIFICATIONS.md](data/outputs/final/FINAL_PLAYER_JUSTIFICATIONS.md)
- **Final Source-of-Truth & SHA-256 Provenance:** [data/outputs/final/FINAL_RANKING_SOURCE_OF_TRUTH.json](data/outputs/final/FINAL_RANKING_SOURCE_OF_TRUTH.json)
- **Star-Player Identity & Eligibility Audit (21 Stars, incl. Pat Cummins = Patrick Cummins ID 1758):** [STAR_PLAYER_ELIGIBILITY_AUDIT.csv](STAR_PLAYER_ELIGIBILITY_AUDIT.csv)
- **Pressure Methodology Empirical Benchmark (5 Proxies + Blocked WPA):** [PRESSURE_METHODOLOGY_COMPARISON.csv](PRESSURE_METHODOLOGY_COMPARISON.csv)
- **Rajasthan Royals Secondary Scouting Module (Strictly Decoupled):** [data/outputs/final/RR_PLAYER_FIT_REPORT.md](data/outputs/final/RR_PLAYER_FIT_REPORT.md), [RR_TEAM_REQUIREMENTS.csv](data/outputs/final/RR_TEAM_REQUIREMENTS.csv), [RR_TOP10_CANDIDATE_FIT.csv](data/outputs/final/RR_TOP10_CANDIDATE_FIT.csv), [RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv](data/outputs/final/RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv), [RR_RECOMMENDED_SQUAD.csv](data/outputs/final/RR_RECOMMENDED_SQUAD.csv)
- **Pre-Fix & Post-Fix Audit Reports:** [FINAL_AUDIT_BEFORE_FIX.md](FINAL_AUDIT_BEFORE_FIX.md) and [FINAL_POST_FIX_AUDIT.md](FINAL_POST_FIX_AUDIT.md)

### Underlying V4.2 Statistical Artifacts (`data/outputs/v4_2/`)
- **Primary Methodology Report:** [METHODOLOGY_REPORT.md](METHODOLOGY_REPORT.md)
- **Individual Top 10 Player Justifications (All 20 Players):** [data/reports/v4_2/V4_2_PLAYER_JUSTIFICATIONS.md](data/reports/v4_2/V4_2_PLAYER_JUSTIFICATIONS.md)
- **Release Decision & Statistical Audit:** [data/reports/v4_2/V4_2_RELEASE_DECISION.md](data/reports/v4_2/V4_2_RELEASE_DECISION.md)
- **Canonical Shortlist CSV:** [data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv](data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv)
- **Source-of-Truth Provenance & SHA-256 Hashes:** [data/outputs/v4_2/V4_2_SOURCE_OF_TRUTH.json](data/outputs/v4_2/V4_2_SOURCE_OF_TRUTH.json)

---

## Interpreting `EB Δ` vs `EB vs Pop μ₀`

Every shortlisted player's absolute Empirical-Bayes slope (`EB Δ`) is compared against the REML pooled eligible-player mean (`μ₀`):

$$\text{EB vs Pop }\mu_0 = \text{EB }\Delta - \mu_0$$

- **Batters (`μ₀ = -36.12` runs/100 legal balls):** When wickets fall early, scoring drops across the entire population. David Miller (`EB Δ = -29.39`, `EB vs Pop μ₀ = +6.73`) deteriorates ~`6.73` runs/100b *less* than the pooled batter average, though his absolute effect remains negative.
- **Bowlers (`μ₀ = -50.88` suppression-proxy units/100 legal balls):** Against high expected scoring threat, batter runs conceded rise across the field. Matheesha Pathirana (`EB Δ = -34.95`, `EB vs Pop μ₀ = +15.94`) deteriorates ~`15.94` proxy units/100b *less* than the pooled bowler average, though his absolute effect remains negative.
- **`P(Top 10)` vs `P(Δ > 0)`:** `P(Top 10)` is the bootstrap probability of entering the Top 10 candidate group; `P(Δ > 0)` is the probability of a positive absolute slope (`< 0.001` for all 20 candidates). Do not confuse them or label negative-`EB Δ` players as positive absolute pressure performers.

---

## Canonical V4.2 Top 10 Batters (`PROVISIONAL — RESOURCE STRESS`)

*(Source: `data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv`, `n = 106` eligible batters)*

| Rank | Player ID | Player Name | Matches (`CS`) | `n_hi / n_lo` | Unshrunk Δ | `EB Δ` | `EB vs Pop μ₀` | Boot 95% CI | Rank 95% CI | `P(Top 10)` [MCSE] |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|
| 1 | `1077` | David Miller | 81 (`81`) | 296 / 456 | -6.64 | **-29.39** | **+6.73** | [-36.29, +0.58] | [1, 57] | 0.390 [0.011] |
| 2 | `7059` | Nehal Wadhera | 37 (`37`) | 231 / 98 | +4.64 | **-29.69** | **+6.44** | [-35.65, +10.00] | [1, 56] | 0.540 [0.011] |
| 3 | `152` | Ravindra Jadeja | 65 (`65`) | 349 / 178 | -13.82 | **-30.29** | **+5.83** | [-39.24, -1.60] | [2, 67] | 0.281 [0.010] |
| 4 | `4904` | Kamindu Mendis | 38 (`38`) | 222 / 113 | -2.67 | **-30.35** | **+5.77** | [-38.58, +1.37] | [1, 64] | 0.385 [0.011] |
| 5 | `1318` | Andre Russell | 57 (`57`) | 397 / 102 | -1.58 | **-30.42** | **+5.70** | [-38.83, +9.90] | [1, 65] | 0.445 [0.011] |
| 6 | `6512` | Michael Bracewell | 33 (`33`) | 170 / 37 | +15.06 | **-30.42** | **+5.70** | [-35.86, +9.96] | [1, 58] | 0.553 [0.011] |
| 7 | `3489` | Salman Agha | 42 (`42`) | 300 / 105 | -3.60 | **-30.45** | **+5.67** | [-38.18, +3.07] | [1, 64] | 0.401 [0.011] |
| 8 | `25213` | Dewald Brevis | 40 (`40`) | 198 / 125 | +5.52 | **-30.58** | **+5.55** | [-37.06, +6.29] | [1, 61] | 0.476 [0.011] |
| 9 | `24017` | Brian Bennett | 44 (`44`) | 87 / 169 | +2.75 | **-30.64** | **+5.48** | [-36.73, +3.25] | [1, 59] | 0.419 [0.011] |
| 10 | `4812` | Harry Tector | 45 (`45`) | 267 / 165 | -10.09 | **-30.67** | **+5.45** | [-40.58, -0.15] | [2, 67] | 0.308 [0.010] |

## Canonical V4.2 Top 10 Bowlers (`PROVISIONAL — RESOURCE STRESS`)

*(Source: `data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv`, `n = 136` eligible bowlers; outcome is `-100 * batter_runs / legal_ball`, not full economy with multi-run extras)*

| Rank | Player ID | Player Name | Matches (`CS`) | `n_hi / n_lo` | Unshrunk Δ | `EB Δ` | `EB vs Pop μ₀` | Boot 95% CI | Rank 95% CI | `P(Top 10)` [MCSE] |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|
| 1 | `8661` | Matheesha Pathirana | 54 (`54`) | 515 / 170 | -8.53 | **-34.95** | **+15.94** | [-41.39, -2.13] | [1, 33] | 0.790 [0.009] |
| 2 | `7364` | Haris Rauf | 48 (`48`) | 273 / 213 | -6.37 | **-35.81** | **+15.08** | [-42.31, +0.56] | [1, 37] | 0.776 [0.009] |
| 3 | `4641` | Lungi Ngidi | 39 (`39`) | 258 / 158 | -1.43 | **-37.95** | **+12.93** | [-41.72, -1.56] | [1, 34] | 0.771 [0.009] |
| 4 | `2933` | Jasprit Bumrah | 75 (`75`) | 612 / 314 | -24.23 | **-38.13** | **+12.76** | [-47.51, -13.01] | [1, 55] | 0.454 [0.011] |
| 5 | `19316` | Maheesh Theekshana | 99 (`99`) | 579 / 457 | -25.96 | **-38.16** | **+12.72** | [-46.91, -14.43] | [2, 52] | 0.405 [0.011] |
| 6 | `7967` | Noor Ahmad | 70 (`70`) | 340 / 388 | -24.93 | **-41.65** | **+9.24** | [-51.52, -16.53] | [2, 69] | 0.338 [0.011] |
| 7 | `3275` | Alzarri Joseph | 53 (`53`) | 349 / 189 | -24.89 | **-41.87** | **+9.02** | [-52.38, -15.08] | [2, 74] | 0.333 [0.011] |
| 8 | `2687` | Roston Chase | 45 (`45`) | 134 / 244 | -17.67 | **-42.57** | **+8.31** | [-51.82, -9.22] | [1, 71] | 0.422 [0.011] |
| 9 | `6628` | Gerald Coetzee | 29 (`29`) | 192 / 102 | -19.68 | **-43.64** | **+7.24** | [-54.79, -8.47] | [1, 82] | 0.393 [0.011] |
| 10 | `3720` | Craig Young | 23 (`23`) | 120 / 114 | -13.74 | **-43.71** | **+7.17** | [-52.86, -12.76] | [2, 75] | 0.362 [0.011] |

---

## Dataset Scope, Model & Validation Summary

- **Dataset:** `837` IPL + T20I matches (2022–2026), `193,988` regular delivery rows, `185,951` validated legal balls (`Super Overs` isolated; `legal_balls` excludes wides and no-ball `Overstep`).
- **Primary Estimator:** **Option A Complete Penalized FWL Partial Regression + REML Empirical Bayes** residualizing both outcome $y$ and common-support interaction matrix $W$ against full nuisance design $Z = [X_{\text{state}}, X_{\text{match}}, X_{\text{player}}, X_{\text{opp}}]$, benchmarked against **Option B Joint REML-EM** (`rho = 0.992` batters / `0.996` bowlers).
- **Uncertainty & Validation:** `B = 2,000` REML match-cluster bootstrap verified against `K = 25` full nuisance+B3 refits; tie-aware `average` ranks and fractional Top-10 membership; exact 8-contrast additive identities (`< 1e-13`); permutation placebo pass; honest Claim C OOT disclosure (`CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS`).
- **Secondary RR Scouting Scope:** Rajasthan Royals 2026 squad audit and 2027 auction watchlist modules remain strictly secondary applications and never influence or alter the universal Top 10 leaderboards.
- **Archived Baselines:** Historical V3 (`data/outputs/v3/`, `scripts/compute_v3_rankings.py`), V4 (`data/outputs/v4/`), and V4.1 (`data/outputs/v4_1/`) outputs are preserved as archived comparison artifacts.

---

## Reproducibility Commands

```powershell
# Verify V4.2 artifact integrity, SHA-256 hashes, and mathematical invariants
.\.venv\Scripts\python.exe scripts/verify_v4_2_rankings.py

# Re-run V4.2 pipeline (only when regenerating from raw inputs)
.\.venv\Scripts\python.exe scripts/compute_v4_2_rankings.py

# Run full automated test suite
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Launch interactive Streamlit dashboard
.\.venv\Scripts\streamlit.exe run dashboard/app.py
```
