# DATA AUDIT V4 — SupeRR Intelligence V4

## 1. Scope & Exact Row Reconciliation
- **Scope**: IPL and T20I matches from 2022 onwards (`data/ball_by_ball_ipl_t20i.csv`, `data/matches_ipl_t20i.csv`).
- **Raw Data Pack**: `200,999` ball-by-ball rows across `883` matches (`match_format` IPL + T20I + T20).
- **Non-IPL/T20I Exclusions**: `6,985` deliveries across `30` matches (`comp_id` in `{2670,3289}`: Men's T20 Emerging Teams Asia Cup / Asia Cup Rising Stars; `6,973` regular + `12` Super Over) are excluded from the primary leaderboard.
- **Scoped Files (`data/README.md`)**: `194,014` deliveries (`matches_ipl_t20i.csv`: `853` matches total, `837` with deliveries, `16` abandoned).
- **Regular vs Super Over Split**:
  - Regular innings (`innings in {1, 2}`): **`193,988`** deliveries (`1st=102,054`, `2nd=91,934`).
  - Super Overs (`innings in {3, 4}`): **`26`** deliveries (`3rd=19`, `4th=7`), separated from main model fitting.
  - **Exact Reconciliation**: `194,014 - 193,988 = 26` Super Over deliveries. Full table exported to [`DATA_RECONCILIATION.csv`](file:///d:/rrhackthon/data/outputs/v4/DATA_RECONCILIATION.csv).

## 2. Critical Extras & Score Semantics (`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`)
- **`extras1_runs` is a 1:1 categorical code mapping `extras_type`** (never extra runs): `Overstep=1`, `wide=2`, `legbyes=3`, `byes=4`, `other=5`, `None=6`, `Penalty=7` (`len(table)=7`).
- **`runs` captures batter-scored runs only**: on 100% of `wide` (`wide_nonzero_runs=0`), `legbyes` (`0`), and `byes` (`0`), `runs == 0`. Multi-run wides, leg-byes, byes, and penalty runs are absent.
- **`extras_2_runs`**: non-zero on `35` rows (primarily 1/4 values on Overstep/other); quarantined via `quarantine_extras2_flag` rather than guessed.
- **Match Margin Reconstruction Test**: Testing `clean_runs = batter_runs + 1*(wide | Overstep)` across `390` non-DLS matches decided `"by X runs"` yields only **`48` exact matches vs `342` mismatches (87.7% failure rate)**.
- **Decision**: **`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`**. Exact team totals, first-innings target, runs remaining, required run rate (`RRR`), and score-based `WP(score, target)` / `C_t` are **quarantined and excluded**. All bowler run metrics are explicitly labeled **`BATTER_RUNS_CONCEDED_PROXY`**.

## 3. DLS Revised Overs Units Discovery
- Non-null positive values of `first_inn_revised_overs` and `second_inn_revised_overs` range from **`30` to `114`**, with **`0` rows <= 20**.
- These fields store **revised scheduled BALLS** (e.g. `114`, `90`, `66`, `48`, `30`), NOT overs. Previous code in `src/context_engine/innings_context.py` multiplied values by `6.0`, corrupting shortened innings. V4 reads revised values directly as balls (multiplying by `6.0` only if `<= 20.0`).

## 4. Boundaries, Dismissals, Playing XI & Identity Integrity
- **Boundaries**: `20` rows have `runs == 4 & is_four != 1` (running 4s / all-run boundaries); `3` rows have `runs == 6 & is_six != 1` (`boundary_discrepancy_total=23`). V4 uses `batter_runs` directly for scoring and validated flags only when needed.
- **Dismissals**: `1` delivery has `is_wicket == 1` with missing `dismissed_player_id` (`match_id=40709` Retire Out); `is_striker_out` strictly checks `dismissed_player_id == striker_id`, and `is_bowler_wicket` excludes run-outs and retired-out/hurt via `NON_BOWLER_DISMISSALS`.
- **Playing XI Duplicates**: `35` `(match_id, player_id)` keys appear multiple times (`40` excess rows in `playing_eleven_ipl_t20i.csv`); V4 deduplicates `(match_id, player_id)` deterministically and derives delivery exposure strictly from BBB `player_id`.
- **Player Identity**: `0` IDs map to multiple names; `2` player names map to multiple distinct `player_id`s (Abdul Samad, Haider Ali). **V4 aggregates strictly by `striker_id` and `bowler_id` everywhere.**
