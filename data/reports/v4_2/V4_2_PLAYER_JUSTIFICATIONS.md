# SupeRR Intelligence V4.2 — Individual Top 10 Player Justifications

**Release Status:** `V4.2 PROVISIONAL — RESOURCE STRESS`  
**Sources Used Exclusively:** `V4_2_FINAL_SHORTLIST.csv`, `V4_2_ALL_PLAYER_ESTIMATES.csv`, `V4_2_SOURCE_OF_TRUTH.json`, `V4_2_VALIDATION_MATRIX.csv`

> **Honest Interpretation Guardrail:** Candidate order is strictly **relative to the eligible field under pre-delivery resource-stress proxies** (`BATTING_WICKET_DEPLETION_ANOMALY` for batters; `BOWLING_EXPECTED_SCORING_THREAT` for bowlers). Because the pooled eligible population experiences a structural deterioration under high resource stress (`μ₀ = -36.124` runs/100b for batters; `μ₀ = -50.884` proxy units/100b for bowlers), all 20 shortlisted players have negative absolute Empirical-Bayes slopes (`EB Δ < 0`) and `P(Δ > 0) < 0.001`. **No player below is claimed to be a statistically confirmed positive absolute pressure performer.** Positive `EB vs Pop μ₀ = EB Δ − μ₀` indicates smaller deterioration than the pooled eligible average.

---

## Part A — Top 10 Batters (`BATTING_WICKET_DEPLETION_ANOMALY`)

### 1. David Miller (Player ID: `1077`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#1** (bootstrap avg rank `1.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+6.73` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-29.39`).
- **Total Match Exposure:** `81` matches (`1280` legal balls; overall raw strike rate `149.30` runs/100b).
- **High-Proxy Exposure:** `296` balls across `31` matches (raw high-stress SR `137.84`).
- **Low-Proxy Exposure:** `456` balls across `48` matches (raw low-stress SR `159.65`).
- **Common-Support Matches:** `81` matches (`effective_exposure = 358.98`, `eb_weight = 0.228`).
- **Raw High-Minus-Low Contrast:** `-21.81` runs/100b.
- **Unshrunk FWL Pressure Effect:** `-6.64` runs/100b (`se_delta = 16.09`).
- **Empirical-Bayes `EB Δ`:** `-29.39` runs/100b (`P(Δ > 0) = 0.000066`).
- **`EB vs Pop μ₀`:** `+6.73` runs/100b (`-29.39 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-44.46, -14.33]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-36.29, 0.58]`.
- **Rank 95% Interval:** `[1, 57]` (median bootstrap rank `14.0`).
- **`P(Top 10)` & MCSE:** `0.3900` (MCSE `±0.0109`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.32` across `19` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 6 paired matches (positive within-match hi-vs-lo share `0.50`).
- **Between-Match Spread:** SD = `91.49` runs/100b across `19` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-16.04, -1.05]` (max absolute single-match shift `9.40` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-1.77` per 100b (SE `1.58`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 57]` and `P(Top 10) = 0.390` reflect substantial rank overlap across the eligible batter pool (`n = 106`). Same-match positive-delta share vs own normal (`0.32`) is below `0.50` because individual match deltas are compared against `0` rather than the negative population stress tax (`μ₀ = -36.12`).

### 2. Nehal Wadhera (Player ID: `7059`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#2** (bootstrap avg rank `2.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+6.44` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-29.69`).
- **Total Match Exposure:** `37` matches (`560` legal balls; overall raw strike rate `140.00` runs/100b).
- **High-Proxy Exposure:** `231` balls across `17` matches (raw high-stress SR `131.17`).
- **Low-Proxy Exposure:** `98` balls across `15` matches (raw low-stress SR `133.67`).
- **Common-Support Matches:** `37` matches (`effective_exposure = 137.62`, `eb_weight = 0.158`).
- **Raw High-Minus-Low Contrast:** `-2.50` runs/100b.
- **Unshrunk FWL Pressure Effect:** `+4.64` runs/100b (`se_delta = 20.21`).
- **Empirical-Bayes `EB Δ`:** `-29.69` runs/100b (`P(Δ > 0) = 0.000109`).
- **`EB vs Pop μ₀`:** `+6.44` runs/100b (`-29.69 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-45.43, -13.95]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-35.65, 10.00]`.
- **Rank 95% Interval:** `[1, 56]` (median bootstrap rank `9.0`).
- **`P(Top 10)` & MCSE:** `0.5395` (MCSE `±0.0111`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.60` across `10` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 1 paired matches (positive within-match hi-vs-lo share `1.00`).
- **Between-Match Spread:** SD = `97.29` runs/100b across `10` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-3.61, +13.70]` (max absolute single-match shift `9.06` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-3.49` per 100b (SE `3.28`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 56]` and `P(Top 10) = 0.539` reflect substantial rank overlap across the eligible batter pool (`n = 106`). **Limited Exposure Caveat (Nehal Wadhera):** Moderate sample depth (`37` common-support matches, `98` low-proxy balls across `15` low-proxy matches; `se_delta = 20.21`), though his `P(Top 10) = 0.539` is second highest among batters.

### 3. Ravindra Jadeja (Player ID: `152`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#3** (bootstrap avg rank `3.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.83` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.29`).
- **Total Match Exposure:** `65` matches (`958` legal balls; overall raw strike rate `135.07` runs/100b).
- **High-Proxy Exposure:** `349` balls across `30` matches (raw high-stress SR `123.78`).
- **Low-Proxy Exposure:** `178` balls across `30` matches (raw low-stress SR `172.47`).
- **Common-Support Matches:** `65` matches (`effective_exposure = 235.76`, `eb_weight = 0.262`).
- **Raw High-Minus-Low Contrast:** `-48.69` runs/100b.
- **Unshrunk FWL Pressure Effect:** `-13.82` runs/100b (`se_delta = 14.70`).
- **Empirical-Bayes `EB Δ`:** `-30.29` runs/100b (`P(Δ > 0) = 0.000028`).
- **`EB vs Pop μ₀`:** `+5.83` runs/100b (`-30.29 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-45.03, -15.55]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-39.24, -1.60]`.
- **Rank 95% Interval:** `[2, 67]` (median bootstrap rank `19.0`).
- **`P(Top 10)` & MCSE:** `0.2805` (MCSE `±0.0100`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.36` across `22` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 6 paired matches (positive within-match hi-vs-lo share `0.33`).
- **Between-Match Spread:** SD = `83.54` runs/100b across `22` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-19.87, -7.70]` (max absolute single-match shift `6.12` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-3.19` per 100b (SE `2.03`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[2, 67]` and `P(Top 10) = 0.281` reflect substantial rank overlap across the eligible batter pool (`n = 106`). Same-match positive-delta share vs own normal (`0.36`) is below `0.50` because individual match deltas are compared against `0` rather than the negative population stress tax (`μ₀ = -36.12`).

### 4. Kamindu Mendis (Player ID: `4904`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#4** (bootstrap avg rank `4.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.77` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.35`).
- **Total Match Exposure:** `38` matches (`593` legal balls; overall raw strike rate `129.51` runs/100b).
- **High-Proxy Exposure:** `222` balls across `18` matches (raw high-stress SR `115.32`).
- **Low-Proxy Exposure:** `113` balls across `15` matches (raw low-stress SR `135.40`).
- **Common-Support Matches:** `38` matches (`effective_exposure = 149.77`, `eb_weight = 0.172`).
- **Raw High-Minus-Low Contrast:** `-20.08` runs/100b.
- **Unshrunk FWL Pressure Effect:** `-2.67` runs/100b (`se_delta = 19.17`).
- **Empirical-Bayes `EB Δ`:** `-30.35` runs/100b (`P(Δ > 0) = 0.000069`).
- **`EB vs Pop μ₀`:** `+5.77` runs/100b (`-30.35 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-45.96, -14.75]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-38.58, 1.37]`.
- **Rank 95% Interval:** `[1, 64]` (median bootstrap rank `14.0`).
- **`P(Top 10)` & MCSE:** `0.3850` (MCSE `±0.0109`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.64` across `11` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 2 paired matches (positive within-match hi-vs-lo share `1.00`).
- **Between-Match Spread:** SD = `95.99` runs/100b across `11` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-12.46, +3.82]` (max absolute single-match shift `9.80` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-2.85` per 100b (SE `2.84`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 64]` and `P(Top 10) = 0.385` reflect substantial rank overlap across the eligible batter pool (`n = 106`).

### 5. Andre Russell (Player ID: `1318`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#5** (bootstrap avg rank `5.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.70` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.42`).
- **Total Match Exposure:** `57` matches (`733` legal balls; overall raw strike rate `171.08` runs/100b).
- **High-Proxy Exposure:** `397` balls across `34` matches (raw high-stress SR `162.47`).
- **Low-Proxy Exposure:** `102` balls across `15` matches (raw low-stress SR `193.14`).
- **Common-Support Matches:** `57` matches (`effective_exposure = 162.30`, `eb_weight = 0.165`).
- **Raw High-Minus-Low Contrast:** `-30.67` runs/100b.
- **Unshrunk FWL Pressure Effect:** `-1.58` runs/100b (`se_delta = 19.68`).
- **Empirical-Bayes `EB Δ`:** `-30.42` runs/100b (`P(Δ > 0) = 0.000071`).
- **`EB vs Pop μ₀`:** `+5.70` runs/100b (`-30.42 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-46.10, -14.75]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-38.83, 9.90]`.
- **Rank 95% Interval:** `[1, 65]` (median bootstrap rank `13.0`).
- **`P(Top 10)` & MCSE:** `0.4450` (MCSE `±0.0111`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.38` across `16` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 1 paired matches (positive within-match hi-vs-lo share `0.00`).
- **Between-Match Spread:** SD = `125.28` runs/100b across `16` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-7.15, +8.80]` (max absolute single-match shift `10.38` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-3.43` per 100b (SE `2.65`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 65]` and `P(Top 10) = 0.445` reflect substantial rank overlap across the eligible batter pool (`n = 106`). Same-match positive-delta share vs own normal (`0.38`) is below `0.50` because individual match deltas are compared against `0` rather than the negative population stress tax (`μ₀ = -36.12`).

### 6. Michael Bracewell (Player ID: `6512`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#6** (bootstrap avg rank `6.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.70` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.42`).
- **Total Match Exposure:** `33` matches (`350` legal balls; overall raw strike rate `134.86` runs/100b).
- **High-Proxy Exposure:** `170` balls across `16` matches (raw high-stress SR `124.71`).
- **Low-Proxy Exposure:** `37` balls across `14` matches (raw low-stress SR `108.11`).
- **Common-Support Matches:** `33` matches (`effective_exposure = 60.77`, `eb_weight = 0.111`).
- **Raw High-Minus-Low Contrast:** `+16.60` runs/100b.
- **Unshrunk FWL Pressure Effect:** `+15.06` runs/100b (`se_delta = 24.72`).
- **Empirical-Bayes `EB Δ`:** `-30.42` runs/100b (`P(Δ > 0) = 0.000113`).
- **`EB vs Pop μ₀`:** `+5.70` runs/100b (`-30.42 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-46.59, -14.26]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-35.86, 9.96]`.
- **Rank 95% Interval:** `[1, 58]` (median bootstrap rank `9.0`).
- **`P(Top 10)` & MCSE:** `0.5530` (MCSE `±0.0111`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.56` across `9` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 2 paired matches (positive within-match hi-vs-lo share `1.00`).
- **Between-Match Spread:** SD = `99.50` runs/100b across `9` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[+0.44, +25.76]` (max absolute single-match shift `14.62` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-2.81` per 100b (SE `3.25`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 58]` and `P(Top 10) = 0.553` reflect substantial rank overlap across the eligible batter pool (`n = 106`). **Mandatory Low-Exposure Caveat (Michael Bracewell):** Only `37` low-proxy balls (`14` low-proxy matches) across `33` common-support matches — just above the operational `30`-ball low-exposure floor (`se_delta = 24.72`, `eb_weight = 0.111`). Although his raw (`+16.60`) and unshrunk FWL (`+15.06`) contrasts are positive, his absolute EB slope remains negative (`-30.42`) with broad bootstrap uncertainty (`[-35.86, +9.96]`), high single-match leverage (`LOMO max shift = 14.62`), and a dismissal-risk trade-off (`-2.81` per 100b, `MODERATE_OR_NEUTRAL_TRADEOFF`).

### 7. Salman Agha (Player ID: `3489`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#7** (bootstrap avg rank `7.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.67` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.45`).
- **Total Match Exposure:** `42` matches (`698` legal balls; overall raw strike rate `122.64` runs/100b).
- **High-Proxy Exposure:** `300` balls across `24` matches (raw high-stress SR `105.67`).
- **Low-Proxy Exposure:** `105` balls across `16` matches (raw low-stress SR `126.67`).
- **Common-Support Matches:** `42` matches (`effective_exposure = 155.56`, `eb_weight = 0.174`).
- **Raw High-Minus-Low Contrast:** `-21.00` runs/100b.
- **Unshrunk FWL Pressure Effect:** `-3.60` runs/100b (`se_delta = 19.04`).
- **Empirical-Bayes `EB Δ`:** `-30.45` runs/100b (`P(Δ > 0) = 0.000064`).
- **`EB vs Pop μ₀`:** `+5.67` runs/100b (`-30.45 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-46.04, -14.87]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-38.18, 3.07]`.
- **Rank 95% Interval:** `[1, 64]` (median bootstrap rank `14.0`).
- **`P(Top 10)` & MCSE:** `0.4010` (MCSE `±0.0110`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.50` across `20` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 5 paired matches (positive within-match hi-vs-lo share `0.80`).
- **Between-Match Spread:** SD = `75.46` runs/100b across `20` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-10.66, +5.92]` (max absolute single-match shift `9.53` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-2.84` per 100b (SE `2.51`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 64]` and `P(Top 10) = 0.401` reflect substantial rank overlap across the eligible batter pool (`n = 106`).

### 8. Dewald Brevis (Player ID: `25213`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#8** (bootstrap avg rank `8.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.55` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.58`).
- **Total Match Exposure:** `40` matches (`630` legal balls; overall raw strike rate `152.86` runs/100b).
- **High-Proxy Exposure:** `198` balls across `21` matches (raw high-stress SR `137.88`).
- **Low-Proxy Exposure:** `125` balls across `17` matches (raw low-stress SR `143.20`).
- **Common-Support Matches:** `40` matches (`effective_exposure = 153.25`, `eb_weight = 0.133`).
- **Raw High-Minus-Low Contrast:** `-5.32` runs/100b.
- **Unshrunk FWL Pressure Effect:** `+5.52` runs/100b (`se_delta = 22.32`).
- **Empirical-Bayes `EB Δ`:** `-30.58` runs/100b (`P(Δ > 0) = 0.000087`).
- **`EB vs Pop μ₀`:** `+5.55` runs/100b (`-30.58 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-46.54, -14.61]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-37.06, 6.29]`.
- **Rank 95% Interval:** `[1, 61]` (median bootstrap rank `11.0`).
- **`P(Top 10)` & MCSE:** `0.4760` (MCSE `±0.0112`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.36` across `11` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 4 paired matches (positive within-match hi-vs-lo share `0.50`).
- **Between-Match Spread:** SD = `87.20` runs/100b across `11` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-2.93, +16.13]` (max absolute single-match shift `10.60` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-3.05` per 100b (SE `2.49`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 61]` and `P(Top 10) = 0.476` reflect substantial rank overlap across the eligible batter pool (`n = 106`). Same-match positive-delta share vs own normal (`0.36`) is below `0.50` because individual match deltas are compared against `0` rather than the negative population stress tax (`μ₀ = -36.12`).

### 9. Brian Bennett (Player ID: `24017`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#9** (bootstrap avg rank `9.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.48` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.64`).
- **Total Match Exposure:** `44` matches (`793` legal balls; overall raw strike rate `128.50` runs/100b).
- **High-Proxy Exposure:** `87` balls across `13` matches (raw high-stress SR `139.08`).
- **Low-Proxy Exposure:** `169` balls across `13` matches (raw low-stress SR `130.18`).
- **Common-Support Matches:** `44` matches (`effective_exposure = 114.87`, `eb_weight = 0.141`).
- **Raw High-Minus-Low Contrast:** `+8.90` runs/100b.
- **Unshrunk FWL Pressure Effect:** `+2.75` runs/100b (`se_delta = 21.61`).
- **Empirical-Bayes `EB Δ`:** `-30.64` runs/100b (`P(Δ > 0) = 0.000079`).
- **`EB vs Pop μ₀`:** `+5.48` runs/100b (`-30.64 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-46.54, -14.75]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-36.73, 3.25]`.
- **Rank 95% Interval:** `[1, 59]` (median bootstrap rank `13.0`).
- **`P(Top 10)` & MCSE:** `0.4185` (MCSE `±0.0110`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.42` across `12` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** Unavailable (`NaN` — 0 matches containing both P87.5+ high-stress and P12.5- low-stress deliveries).
- **Between-Match Spread:** SD = `100.74` runs/100b across `12` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-6.92, +9.81]` (max absolute single-match shift `9.67` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-2.71` per 100b (SE `2.84`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[1, 59]` and `P(Top 10) = 0.418` reflect substantial rank overlap across the eligible batter pool (`n = 106`). **Mandatory Paired-Evidence Caveat (Brian Bennett):** Same-match paired high-versus-low (`within_match_hilo_matches`) evidence is **unavailable (`NaN`)** in the committed output; within-match paired consistency is **not established**. His `0.42` share (`12` spread matches) comes from the same-match high-versus-nonhigh consistency diagnostic, which is distinct from paired high-versus-low evidence. Also has modest high-proxy exposure (`87` high-proxy balls, `13` high-proxy matches).

### 10. Harry Tector (Player ID: `4812`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#10** (bootstrap avg rank `10.0`) among `106` eligible batters under `BATTING_WICKET_DEPLETION_ANOMALY`, preserving `+5.45` runs/100b relative to the pooled batter stress deterioration (`μ₀ = -36.12`), while his absolute EB slope remains negative (`-30.67`).
- **Total Match Exposure:** `45` matches (`828` legal balls; overall raw strike rate `122.58` runs/100b).
- **High-Proxy Exposure:** `267` balls across `25` matches (raw high-stress SR `116.85`).
- **Low-Proxy Exposure:** `165` balls across `20` matches (raw low-stress SR `136.36`).
- **Common-Support Matches:** `45` matches (`effective_exposure = 203.96`, `eb_weight = 0.209`).
- **Raw High-Minus-Low Contrast:** `-19.51` runs/100b.
- **Unshrunk FWL Pressure Effect:** `-10.09` runs/100b (`se_delta = 17.00`).
- **Empirical-Bayes `EB Δ`:** `-30.67` runs/100b (`P(Δ > 0) = 0.000040`).
- **`EB vs Pop μ₀`:** `+5.45` runs/100b (`-30.67 - (-36.12)`).
- **Conditional REML-EB 95% Interval:** `[-45.92, -15.42]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-40.58, -0.15]`.
- **Rank 95% Interval:** `[2, 67]` (median bootstrap rank `18.0`).
- **`P(Top 10)` & MCSE:** `0.3075` (MCSE `±0.0103`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.52` across `21` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 6 paired matches (positive within-match hi-vs-lo share `0.50`).
- **Between-Match Spread:** SD = `64.89` runs/100b across `21` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-20.11, -2.91]` (max absolute single-match shift `10.02` runs/100b).
- **Secondary Outcome Evidence:** Dismissal-risk delta = `-2.60` per 100b (SE `2.24`, flag `MODERATE_OR_NEUTRAL_TRADEOFF` — fewer extra dismissals under high wicket-depletion stress relative to own baseline; no composite weighting applied).
- **Player-Specific Limitation:** Rank CI `[2, 67]` and `P(Top 10) = 0.307` reflect substantial rank overlap across the eligible batter pool (`n = 106`).

---

## Part B — Top 10 Bowlers (`BOWLING_EXPECTED_SCORING_THREAT`)

### 1. Matheesha Pathirana (Player ID: `8661`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#1** (bootstrap avg rank `1.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+15.94` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-34.95`).
- **Total Match Exposure:** `54` matches (`1135` legal balls; overall raw suppression `-100 * batter_runs/ball = -129.69`).
- **High-Proxy Exposure:** `515` balls across `43` matches (raw high-threat `-Runs/100b = -137.86`).
- **Low-Proxy Exposure:** `170` balls across `16` matches (raw low-threat `-Runs/100b = -115.29`).
- **Common-Support Matches:** `54` matches (`effective_exposure = 255.62`, `eb_weight = 0.376`).
- **Raw High-Minus-Low Contrast:** `-22.57` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-8.53` proxy units/100b (`se_delta = 13.42`).
- **Empirical-Bayes `EB Δ`:** `-34.95` proxy units/100b (`P(Δ > 0) = 0.0000109`).
- **`EB vs Pop μ₀`:** `+15.94` proxy units/100b (`-34.95 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-51.08, -18.81]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-41.39, -2.13]`.
- **Rank 95% Interval:** `[1, 33]` (median bootstrap rank `4.0`).
- **`P(Top 10)` & MCSE:** `0.7895` (MCSE `±0.0091`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.49` across `37` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 7 paired matches (positive within-match hi-vs-lo share `0.43`).
- **Between-Match Spread:** SD = `81.11` proxy units/100b across `37` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-13.07, -3.49]` (max absolute single-match shift `5.04` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-5.45` pp (SE `4.28`), creditable wicket % EB delta = `+3.82` pp (SE `1.75`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises). Same-match positive-delta share vs `0` is `0.49`, reflecting the negative pooled scoring-threat tax (`μ₀ = -50.88`) rather than worse-than-average execution.

### 2. Haris Rauf (Player ID: `7364`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#2** (bootstrap avg rank `2.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+15.08` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-35.81`).
- **Total Match Exposure:** `48` matches (`1027` legal balls; overall raw suppression `-100 * batter_runs/ball = -139.53`).
- **High-Proxy Exposure:** `273` balls across `32` matches (raw high-threat `-Runs/100b = -143.22`).
- **Low-Proxy Exposure:** `213` balls across `26` matches (raw low-threat `-Runs/100b = -122.54`).
- **Common-Support Matches:** `48` matches (`effective_exposure = 239.30`, `eb_weight = 0.339`).
- **Raw High-Minus-Low Contrast:** `-20.69` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-6.37` proxy units/100b (`se_delta = 14.57`).
- **Empirical-Bayes `EB Δ`:** `-35.81` proxy units/100b (`P(Δ > 0) = 0.0000120`).
- **`EB vs Pop μ₀`:** `+15.08` proxy units/100b (`-35.81 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-52.42, -19.19]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-42.31, 0.56]`.
- **Rank 95% Interval:** `[1, 37]` (median bootstrap rank `4.0`).
- **`P(Top 10)` & MCSE:** `0.7760` (MCSE `±0.0093`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.58` across `31` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 14 paired matches (positive within-match hi-vs-lo share `0.29`).
- **Between-Match Spread:** SD = `70.82` proxy units/100b across `31` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-10.88, -0.34]` (max absolute single-match shift `6.03` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-5.73` pp (SE `4.01`), creditable wicket % EB delta = `+3.75` pp (SE `2.06`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises).

### 3. Lungi Ngidi (Player ID: `4641`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#3** (bootstrap avg rank `3.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+12.93` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-37.95`).
- **Total Match Exposure:** `39` matches (`800` legal balls; overall raw suppression `-100 * batter_runs/ball = -143.50`).
- **High-Proxy Exposure:** `258` balls across `23` matches (raw high-threat `-Runs/100b = -152.33`).
- **Low-Proxy Exposure:** `158` balls across `19` matches (raw low-threat `-Runs/100b = -139.24`).
- **Common-Support Matches:** `39` matches (`effective_exposure = 195.98`, `eb_weight = 0.262`).
- **Raw High-Minus-Low Contrast:** `-13.09` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-1.43` proxy units/100b (`se_delta = 17.52`).
- **Empirical-Bayes `EB Δ`:** `-37.95` proxy units/100b (`P(Δ > 0) = 0.0000114`).
- **`EB vs Pop μ₀`:** `+12.93` proxy units/100b (`-37.95 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-55.51, -20.39]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-41.72, -1.56]`.
- **Rank 95% Interval:** `[1, 34]` (median bootstrap rank `4.0`).
- **`P(Top 10)` & MCSE:** `0.7705` (MCSE `±0.0094`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.48` across `21` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 8 paired matches (positive within-match hi-vs-lo share `0.62`).
- **Between-Match Spread:** SD = `62.83` proxy units/100b across `21` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-11.22, +4.32]` (max absolute single-match shift `9.80` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-7.50` pp (SE `4.54`), creditable wicket % EB delta = `+3.65` pp (SE `2.39`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises). Same-match positive-delta share vs `0` is `0.48`, reflecting the negative pooled scoring-threat tax (`μ₀ = -50.88`) rather than worse-than-average execution.

### 4. Jasprit Bumrah (Player ID: `2933`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#4** (bootstrap avg rank `4.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+12.76` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-38.13`).
- **Total Match Exposure:** `75` matches (`1709` legal balls; overall raw suppression `-100 * batter_runs/ball = -114.16`).
- **High-Proxy Exposure:** `612` balls across `52` matches (raw high-threat `-Runs/100b = -126.80`).
- **Low-Proxy Exposure:** `314` balls across `32` matches (raw low-threat `-Runs/100b = -95.86`).
- **Common-Support Matches:** `75` matches (`effective_exposure = 415.05`, `eb_weight = 0.478`).
- **Raw High-Minus-Low Contrast:** `-30.94` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-24.23` proxy units/100b (`se_delta = 10.88`).
- **Empirical-Bayes `EB Δ`:** `-38.13` proxy units/100b (`P(Δ > 0) = 0.0000002`).
- **`EB vs Pop μ₀`:** `+12.76` proxy units/100b (`-38.13 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-52.88, -23.37]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-47.51, -13.01]`.
- **Rank 95% Interval:** `[1, 55]` (median bootstrap rank `12.0`).
- **`P(Top 10)` & MCSE:** `0.4540` (MCSE `±0.0111`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.48` across `50` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 11 paired matches (positive within-match hi-vs-lo share `0.27`).
- **Between-Match Spread:** SD = `67.12` proxy units/100b across `50` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-28.56, -20.83]` (max absolute single-match shift `4.34` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-13.29` pp (SE `3.28`), creditable wicket % EB delta = `+3.50` pp (SE `1.41`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises). Same-match positive-delta share vs `0` is `0.48`, reflecting the negative pooled scoring-threat tax (`μ₀ = -50.88`) rather than worse-than-average execution.

### 5. Maheesh Theekshana (Player ID: `19316`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#5** (bootstrap avg rank `5.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+12.72` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-38.16`).
- **Total Match Exposure:** `99` matches (`2264` legal balls; overall raw suppression `-100 * batter_runs/ball = -126.15`).
- **High-Proxy Exposure:** `579` balls across `64` matches (raw high-threat `-Runs/100b = -139.72`).
- **Low-Proxy Exposure:** `457` balls across `53` matches (raw low-threat `-Runs/100b = -98.25`).
- **Common-Support Matches:** `99` matches (`effective_exposure = 510.82`, `eb_weight = 0.510`).
- **Raw High-Minus-Low Contrast:** `-41.47` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-25.96` proxy units/100b (`se_delta = 10.21`).
- **Empirical-Bayes `EB Δ`:** `-38.16` proxy units/100b (`P(Δ > 0) = 0.0000001`).
- **`EB vs Pop μ₀`:** `+12.72` proxy units/100b (`-38.16 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-52.46, -23.87]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-46.91, -14.43]`.
- **Rank 95% Interval:** `[2, 52]` (median bootstrap rank `13.0`).
- **`P(Top 10)` & MCSE:** `0.4045` (MCSE `±0.0110`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.52` across `60` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 21 paired matches (positive within-match hi-vs-lo share `0.38`).
- **Between-Match Spread:** SD = `71.34` proxy units/100b across `60` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-29.05, -22.82]` (max absolute single-match shift `3.14` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-7.20` pp (SE `3.11`), creditable wicket % EB delta = `+3.85` pp (SE `1.33`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises).

### 6. Noor Ahmad (Player ID: `7967`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#6** (bootstrap avg rank `6.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+9.24` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-41.65`).
- **Total Match Exposure:** `70` matches (`1467` legal balls; overall raw suppression `-100 * batter_runs/ball = -126.86`).
- **High-Proxy Exposure:** `340` balls across `32` matches (raw high-threat `-Runs/100b = -135.88`).
- **Low-Proxy Exposure:** `388` balls across `42` matches (raw low-threat `-Runs/100b = -106.70`).
- **Common-Support Matches:** `70` matches (`effective_exposure = 362.42`, `eb_weight = 0.356`).
- **Raw High-Minus-Low Contrast:** `-29.18` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-24.93` proxy units/100b (`se_delta = 14.03`).
- **Empirical-Bayes `EB Δ`:** `-41.65` proxy units/100b (`P(Δ > 0) = 0.0000003`).
- **`EB vs Pop μ₀`:** `+9.24` proxy units/100b (`-41.65 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-58.05, -25.25]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-51.52, -16.53]`.
- **Rank 95% Interval:** `[2, 69]` (median bootstrap rank `16.0`).
- **`P(Top 10)` & MCSE:** `0.3380` (MCSE `±0.0106`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.50` across `30` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 8 paired matches (positive within-match hi-vs-lo share `0.38`).
- **Between-Match Spread:** SD = `65.65` proxy units/100b across `30` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-29.96, -21.88]` (max absolute single-match shift `5.04` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-7.96` pp (SE `3.95`), creditable wicket % EB delta = `+3.63` pp (SE `1.61`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises).

### 7. Alzarri Joseph (Player ID: `3275`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#7** (bootstrap avg rank `7.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+9.02` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-41.87`).
- **Total Match Exposure:** `53` matches (`1155` legal balls; overall raw suppression `-100 * batter_runs/ball = -153.85`).
- **High-Proxy Exposure:** `349` balls across `40` matches (raw high-threat `-Runs/100b = -158.74`).
- **Low-Proxy Exposure:** `189` balls across `28` matches (raw low-threat `-Runs/100b = -125.93`).
- **Common-Support Matches:** `53` matches (`effective_exposure = 245.21`, `eb_weight = 0.347`).
- **Raw High-Minus-Low Contrast:** `-32.81` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-24.89` proxy units/100b (`se_delta = 14.31`).
- **Empirical-Bayes `EB Δ`:** `-41.87` proxy units/100b (`P(Δ > 0) = 0.0000003`).
- **`EB vs Pop μ₀`:** `+9.02` proxy units/100b (`-41.87 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-58.38, -25.35]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-52.38, -15.08]`.
- **Rank 95% Interval:** `[2, 74]` (median bootstrap rank `16.0`).
- **`P(Top 10)` & MCSE:** `0.3330` (MCSE `±0.0105`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.51` across `39` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 16 paired matches (positive within-match hi-vs-lo share `0.19`).
- **Between-Match Spread:** SD = `81.17` proxy units/100b across `39` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-31.54, -21.14]` (max absolute single-match shift `6.65` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-10.42` pp (SE `3.93`), creditable wicket % EB delta = `+3.80` pp (SE `1.94`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises).

### 8. Roston Chase (Player ID: `2687`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#8** (bootstrap avg rank `8.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+8.31` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-42.57`).
- **Total Match Exposure:** `45` matches (`836` legal balls; overall raw suppression `-100 * batter_runs/ball = -126.20`).
- **High-Proxy Exposure:** `134` balls across `17` matches (raw high-threat `-Runs/100b = -127.61`).
- **Low-Proxy Exposure:** `244` balls across `25` matches (raw low-threat `-Runs/100b = -111.89`).
- **Common-Support Matches:** `45` matches (`effective_exposure = 172.99`, `eb_weight = 0.250`).
- **Raw High-Minus-Low Contrast:** `-15.73` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-17.67` proxy units/100b (`se_delta = 18.04`).
- **Empirical-Bayes `EB Δ`:** `-42.57` proxy units/100b (`P(Δ > 0) = 0.0000012`).
- **`EB vs Pop μ₀`:** `+8.31` proxy units/100b (`-42.57 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-60.27, -24.88]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-51.82, -9.22]`.
- **Rank 95% Interval:** `[1, 71]` (median bootstrap rank `13.0`).
- **`P(Top 10)` & MCSE:** `0.4220` (MCSE `±0.0110`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.40` across `15` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 4 paired matches (positive within-match hi-vs-lo share `0.50`).
- **Between-Match Spread:** SD = `71.65` proxy units/100b across `15` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-23.74, -10.17]` (max absolute single-match shift `7.50` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-6.47` pp (SE `4.80`), creditable wicket % EB delta = `+3.70` pp (SE `2.27`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises). Same-match positive-delta share vs `0` is `0.40`, reflecting the negative pooled scoring-threat tax (`μ₀ = -50.88`) rather than worse-than-average execution.

### 9. Gerald Coetzee (Player ID: `6628`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#9** (bootstrap avg rank `9.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+7.24` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-43.64`).
- **Total Match Exposure:** `29` matches (`594` legal balls; overall raw suppression `-100 * batter_runs/ball = -147.47`).
- **High-Proxy Exposure:** `192` balls across `22` matches (raw high-threat `-Runs/100b = -158.33`).
- **Low-Proxy Exposure:** `102` balls across `13` matches (raw low-threat `-Runs/100b = -128.43`).
- **Common-Support Matches:** `29` matches (`effective_exposure = 133.22`, `eb_weight = 0.232`).
- **Raw High-Minus-Low Contrast:** `-29.90` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-19.68` proxy units/100b (`se_delta = 18.97`).
- **Empirical-Bayes `EB Δ`:** `-43.64` proxy units/100b (`P(Δ > 0) = 0.0000009`).
- **`EB vs Pop μ₀`:** `+7.24` proxy units/100b (`-43.64 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-61.55, -25.74]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-54.79, -8.47]`.
- **Rank 95% Interval:** `[1, 82]` (median bootstrap rank `15.0`).
- **`P(Top 10)` & MCSE:** `0.3930` (MCSE `±0.0109`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.45` across `20` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 8 paired matches (positive within-match hi-vs-lo share `0.25`).
- **Between-Match Spread:** SD = `68.00` proxy units/100b across `20` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-26.97, -7.08]` (max absolute single-match shift `12.60` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-9.45` pp (SE `5.49`), creditable wicket % EB delta = `+3.71` pp (SE `3.08`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises). **Limited Exposure Caveat (Gerald Coetzee):** Relatively limited common-support exposure (`29` common-support matches, `102` low-proxy balls in `13` matches) and a wide rank interval `[1, 82]` (`LOMO max shift = 12.60`).

### 10. Craig Young (Player ID: `3720`)
- **Why Shortlisted (Relative to Eligible Field):** Ranked **#10** (bootstrap avg rank `10.0`) among `136` eligible bowlers under `BOWLING_EXPECTED_SCORING_THREAT`, losing `+7.17` fewer suppression-proxy units/100b than the pooled bowler stress deterioration (`μ₀ = -50.88`), while his absolute EB slope remains negative (`-43.71`).
- **Total Match Exposure:** `23` matches (`466` legal balls; overall raw suppression `-100 * batter_runs/ball = -140.77`).
- **High-Proxy Exposure:** `120` balls across `15` matches (raw high-threat `-Runs/100b = -141.67`).
- **Low-Proxy Exposure:** `114` balls across `15` matches (raw low-threat `-Runs/100b = -130.70`).
- **Common-Support Matches:** `23` matches (`effective_exposure = 116.92`, `eb_weight = 0.193`).
- **Raw High-Minus-Low Contrast:** `-10.96` proxy units/100b.
- **Unshrunk FWL Pressure Effect:** `-13.74` proxy units/100b (`se_delta = 21.32`).
- **Empirical-Bayes `EB Δ`:** `-43.71` proxy units/100b (`P(Δ > 0) = 0.0000015`).
- **`EB vs Pop μ₀`:** `+7.17` proxy units/100b (`-43.71 - (-50.88)`).
- **Conditional REML-EB 95% Interval:** `[-62.07, -25.36]`.
- **EB Match-Cluster Bootstrap 95% Interval (`B = 2,000`):** `[-52.86, -12.76]`.
- **Rank 95% Interval:** `[2, 75]` (median bootstrap rank `15.0`).
- **`P(Top 10)` & MCSE:** `0.3615` (MCSE `±0.0107`).
- **Same-Match High-vs-Nonhigh Positive-Delta Share:** `0.50` across `14` spread matches.
- **Within-Match High-vs-Low Paired Evidence:** 8 paired matches (positive within-match hi-vs-lo share `0.50`).
- **Between-Match Spread:** SD = `85.97` proxy units/100b across `14` spread matches.
- **Leave-One-Match-Out (LOMO) Sensitivity:** `[-23.76, -4.90]` (max absolute single-match shift `10.02` runs/100b).
- **Secondary Outcome Evidence:** Dot-ball % EB delta = `-8.40` pp (SE `6.03`), creditable wicket % EB delta = `+3.80` pp (SE `2.78`), profile `MIXED_SECONDARY_PROFILE` — dot% drops against attacking scoring threat while creditable wicket-taking rises.
- **Player-Specific Limitation:** Primary outcome measures batter-runs suppression (`-100 * batter_runs / legal_ball`), not full bowling economy (multi-run wides, byes, leg-byes, and other extras are unavailable). All Top 10 bowlers show `MIXED_SECONDARY_PROFILE` (dot-ball % drops against attacking scoring threat while creditable wicket % rises). **Mandatory Boundary & Exposure Caveat (Craig Young):** Only `23` common-support matches (`120` high-proxy balls in `15` matches; `114` low-proxy balls in `15` matches; `se_delta = 21.32`). His broad rank interval `[2, 75]` (`P(Top 10) = 0.362`, MCSE `±0.0107`) confirms that the rank-10 boundary position is provisional and imprecise.
