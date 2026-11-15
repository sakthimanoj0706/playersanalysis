# Rajasthan Royals Squad-Fit & Scouting Report (Secondary Module)

> **Strict Decoupling Disclosure:** This RR scouting module is a **secondary application** of SupeRR Intelligence V4.2. It never modifies, filters, or overrides the Universal Top 10 leaderboards.

## 1. RR 2026 Tactical Gaps (`RR_TEAM_REQUIREMENTS.csv`)
- **CRITICAL — Indian Frontline Fast Bowler:** Domestic pace support behind Jofra Archer yielded only 9 wickets across 13 combined appearances (Deshpande 4, Sandeep 5).
- **CRITICAL — Overseas Death-Over Specialist:** High boundary leakage in overs 16–20 behind Archer.
- **IMPORTANT — Economical Middle-Over Spinner:** Support alongside Ravindra Jadeja (already in RR) and Ravi Bishnoi.
- **IMPORTANT — Domestic Lower-Order Finisher:** Needed at No. 6/7 to reduce reliance on Shimron Hetmyer.

## 2. Transparent `RR_PLAYER_FIT_SCORE` Formula
`RR_PLAYER_FIT_SCORE = 0.35 * Phase_Execution + 0.25 * Role_Tactical_Need + 0.20 * Pressure_Resilience_V42 + 0.10 * Sample_Confidence + 0.10 * IPL_Balance_Bonus`

## 3. Top Universal Top 10 Candidates for RR (`RR_TOP10_CANDIDATE_FIT.csv`)
- **Jasprit Bumrah** (bowler, Global #4) — `RR_FIT=93.3` | Role: Powerplay / All-Phase Pacer | `EB Δ=-38.13`
- **Noor Ahmad** (bowler, Global #6) — `RR_FIT=88.7` | Role: Economical Middle-Over Spinner | `EB Δ=-41.65`
- **Matheesha Pathirana** (bowler, Global #1) — `RR_FIT=88.5` | Role: Death-Over Pace Specialist | `EB Δ=-34.95`
- **Maheesh Theekshana** (bowler, Global #5) — `RR_FIT=88.0` | Role: Economical Middle-Over Spinner | `EB Δ=-38.16`
- **Andre Russell** (batter, Global #5) — `RR_FIT=86.1` | Role: Lower-Order Finisher (Overs 15-20) | `EB Δ=-30.42`
- **Roston Chase** (bowler, Global #8) — `RR_FIT=82.1` | Role: Economical Middle-Over Spinner | `EB Δ=-42.57`
- **David Miller** (batter, Global #1) — `RR_FIT=80.0` | Role: Lower-Order Finisher (Overs 15-20) | `EB Δ=-29.39`
- **Dewald Brevis** (batter, Global #8) — `RR_FIT=75.6` | Role: Middle-Order Spin/Pace Accelerator | `EB Δ=-30.58`

## 4. Best RR-Suited Candidates Outside Universal Top 10 (`RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv`)
- **Sunil Narine** (bowler, Global #15) — `RR_FIT=92.1` | Role: Economical Middle-Over Spinner | Matches RR tactical gap (Economical Middle-Over Spinner) with IPL exposure share=100/100 and phase execution=99.3/100 despite ranking #15 globally.
- **Tim David** (batter, Global #39) — `RR_FIT=85.7` | Role: Lower-Order Finisher (Overs 15-20) | Matches RR tactical gap (Lower-Order Finisher (Overs 15-20)) with IPL exposure share=76/100 and phase execution=95.3/100 despite ranking #39 globally.
- **Ravichandran Ashwin** (bowler, Global #24) — `RR_FIT=85.1` | Role: Economical Middle-Over Spinner | Matches RR tactical gap (Economical Middle-Over Spinner) with IPL exposure share=93/100 and phase execution=86.0/100 despite ranking #24 globally.
- **Sikandar Raza** (bowler, Global #18) — `RR_FIT=84.4` | Role: Economical Middle-Over Spinner | Matches RR tactical gap (Economical Middle-Over Spinner) with IPL exposure share=54/100 and phase execution=96.3/100 despite ranking #18 globally.
- **Mitchell Santner** (bowler, Global #47) — `RR_FIT=83.6` | Role: Economical Middle-Over Spinner | Matches RR tactical gap (Economical Middle-Over Spinner) with IPL exposure share=66/100 and phase execution=95.6/100 despite ranking #47 globally.
- **Nicholas Pooran** (batter, Global #19) — `RR_FIT=81.9` | Role: Middle-Order Spin/Pace Accelerator | Matches RR tactical gap (Middle-Order Spin/Pace Accelerator) with IPL exposure share=79/100 and phase execution=80.2/100 despite ranking #19 globally.
- **Kuldeep Yadav** (bowler, Global #45) — `RR_FIT=81.2` | Role: Economical Middle-Over Spinner | Matches RR tactical gap (Economical Middle-Over Spinner) with IPL exposure share=86/100 and phase execution=81.6/100 despite ranking #45 globally.
- **Wanindu Hasaranga** (bowler, Global #30) — `RR_FIT=80.9` | Role: Economical Middle-Over Spinner | Matches RR tactical gap (Economical Middle-Over Spinner) with IPL exposure share=69/100 and phase execution=79.4/100 despite ranking #30 globally.

## 5. Recommended Balanced RR Shortlist (`RR_RECOMMENDED_SQUAD.csv`)
- **Jasprit Bumrah** (bowler, `UNIVERSAL_TOP_10`) — `RR_FIT=93.3` | Role: Powerplay / All-Phase Pacer | `EB Δ=-38.13`
- **Noor Ahmad** (bowler, `UNIVERSAL_TOP_10`) — `RR_FIT=88.7` | Role: Economical Middle-Over Spinner | `EB Δ=-41.65`
- **Matheesha Pathirana** (bowler, `UNIVERSAL_TOP_10`) — `RR_FIT=88.5` | Role: Death-Over Pace Specialist | `EB Δ=-34.95`
- **Maheesh Theekshana** (bowler, `UNIVERSAL_TOP_10`) — `RR_FIT=88.0` | Role: Economical Middle-Over Spinner | `EB Δ=-38.16`
- **Sunil Narine** (bowler, `OUTSIDE_TOP_10_ELIGIBLE_POOL`) — `RR_FIT=92.1` | Role: Economical Middle-Over Spinner | `EB Δ=-44.42`
- **Tim David** (batter, `OUTSIDE_TOP_10_ELIGIBLE_POOL`) — `RR_FIT=85.7` | Role: Lower-Order Finisher (Overs 15-20) | `EB Δ=-33.73`
- **Ravichandran Ashwin** (bowler, `OUTSIDE_TOP_10_ELIGIBLE_POOL`) — `RR_FIT=85.1` | Role: Economical Middle-Over Spinner | `EB Δ=-46.56`
- **Nicholas Pooran** (batter, `OUTSIDE_TOP_10_ELIGIBLE_POOL`) — `RR_FIT=81.9` | Role: Middle-Order Spin/Pace Accelerator | `EB Δ=-32.11`
- **Shashank Singh** (batter, `OUTSIDE_TOP_10_ELIGIBLE_POOL`) — `RR_FIT=80.7` | Role: Lower-Order Finisher (Overs 15-20) | `EB Δ=-33.20`
- **Heinrich Klaasen** (batter, `OUTSIDE_TOP_10_ELIGIBLE_POOL`) — `RR_FIT=80.0` | Role: Middle-Order Spin/Pace Accelerator | `EB Δ=-34.90`

## 6. Weight Sensitivity & Assumptions
- Tested across `Baseline (35/25/20/10/10)`, `Pressure-Heavy (25/20/35/10/10)`, and `Role-Heavy (40/35/10/10/5)`.
- Auction purse and player availability remain **unverified external assumptions** (`data/reference/rr_2027_auction_assumptions.csv`), kept strictly configurable.