# SupeRR Selector Season 2 — Dataset Audit & Data Dictionary

**Source:** Rajasthan Royals Round 1 data pack supplied by the participant  
**Audit date:** 10 November 2026  
**Purpose:** Establish the usable data structure and identify issues to resolve before defining pressure metrics or ranking players.

## 1. Dataset inventory

| File | Rows | Columns | Main purpose |
|---|---:|---:|---|
| `ball_by_ball.csv` | 200,999 | 33 | Delivery-level batting, bowling and match events |
| `matches.csv` | 883 | 22 | Match, competition, date, teams, result and target context |
| `playing_eleven.csv` | 28,381 | 9 | Match-team-player participation and impact-player metadata |
| `competition_team_player_mapping.csv` | 6,413 | 6 | Competition/team/player identity mapping |
| `competitions.csv` | 141 | 4 | Competition format and season |
| `teams.csv` | 353 | 3 | Competition-specific team identity mapping |

The pack also includes the two-page Round 1 problem statement.

## 2. Competition scope

The problem statement specifies historical **IPL and T20I** data from 2022 onwards. The pack contains:

| Scope | Matches |
|---|---:|
| T20I | 482 |
| IPL 2022 | 74 |
| IPL 2023 | 74 |
| IPL 2024 | 74 |
| IPL 2025 | 75 |
| IPL 2026 | 74 |
| **IPL total** | **371** |
| **Required-scope total** | **853** |

There are also 30 matches from two other T20 competitions: Men's T20 Emerging Teams Asia Cup 2024 (15) and Asia Cup Rising Stars 2025 (15). They should be excluded from the primary IPL + T20I ranking unless RR confirms otherwise.

The match table runs from **22 January 2022 to 1 November 2026**. Of the 853 IPL/T20I matches, 837 have ball-by-ball records. The remaining 16 are marked `Match Abandoned` and have no delivery rows. Across the complete pack, 867 distinct matches have ball-by-ball rows.

## 3. Table relationships

Use IDs for joins; do not join by player names.

- `matches.match_id` → `ball_by_ball.match_id`
- `matches.comp_id` → `competitions.comp_id`
- `matches.comp_id` + `home_team_id` / `away_team_id` → competition/team identity tables
- `competition_team_player_mapping.comp_id, team_id, player_id` identifies a player in a competition/team
- `ball_by_ball.striker_id` and `bowler_id` identify delivery participants; the observed batter/bowler competition-team IDs all match the mapping table in this pack.
- `playing_eleven` is keyed conceptually by `match_id + team_id + player_id`, but it has repeated keys in a small number of matches (see data-quality notes).

## 4. Column dictionary

Descriptions below are based on column names and observed values in the supplied files. Where the source does not define a field unambiguously, it is explicitly marked **confirm with RR**.

### 4.1 `ball_by_ball.csv` — 33 columns

| Column | Observed / likely meaning | Use / caution |
|---|---|---|
| `match_id` | Match identifier | Join to `matches.match_id` |
| `innings` | Innings number (1–4 observed) | Innings 3 and 4 occur in six matches and appear to represent Super Overs; validate before including in normal T20 rankings |
| `overid` | Over index within innings | Use for innings stage; verify treatment of shortened innings |
| `over_ball_num` | Delivery sequence within an over | Values can exceed 6 (up to 13 observed); it counts recorded deliveries, not simply legal balls |
| `innings_ball_num` | Sequential delivery index within innings | Unique and sequential in inspected innings; includes recorded extra deliveries, so do not treat directly as legal-ball count |
| `batting_team_id` | Batting team ID | Join using competition context |
| `bowling_team_id` | Bowling team ID | Join using competition context |
| `striker_id` | Batter facing the delivery | Primary batter-performance ID |
| `striker_name` | Batter name | Display only; prefer ID for calculations |
| `non_striker_id` | Batter at the non-striker's end | Useful for context, not a faced-ball count |
| `non_striker_name` | Non-striker name | Display only |
| `bowler_id` | Bowler delivering the ball | Primary bowler-performance ID |
| `bowler_name` | Bowler name | Display only; prefer ID for calculations |
| `batting_type` | RHB / LHB | Possible split analysis |
| `bowling_type` | Bowling style text | Normalize carefully before grouping |
| `batting_order` | Batter's recorded batting position | Use cautiously; compare with playing-XI data |
| `runs` | Recorded run value on the delivery (0–6 observed) | Appears to align mostly with batter runs, but RR must confirm exact semantics before reconstructing team totals or strike rate |
| `is_four` | Four-boundary flag | 20 rows have `runs=4` but `is_four=false`; validate whether this represents non-bat 4s or a source inconsistency |
| `is_six` | Six-boundary flag | 3 rows have `runs=6` but `is_six=false`; validate before boundary calculations |
| `is_wicket` | Wicket event flag | Boolean text (`true` / `false`) |
| `dismissal_type_id` | Dismissal category code | Use alongside the text field; do not assume every dismissal is credited to the bowler |
| `dismissal_type` | Dismissal description | 10 observed categories, including caught, bowled, LBW, run out, stumped, hit wicket, retired out and obstructing the field |
| `dismissed_player_id` | Dismissed batter ID | One wicket event has this field blank; validate that record |
| `extras_type` | Extra classification | Values observed: `None`, `wide`, `legbyes`, `Overstep`, `byes`, `other`, `Penalty` |
| `extras1_runs` | Numeric code corresponding to `extras_type` | It is categorical, **not a count of runs**. Observed mapping: 1=Overstep, 2=wide, 3=legbyes, 4=byes, 5=other, 6=None, 7=Penalty. Never sum this field as runs. |
| `extras_2_runs` | Secondary numeric extra field | 200,963 rows are zero; only 36 rows are non-zero (20 values of 1 and 16 values of 4). Exact meaning is unclear; **confirm with RR**. |
| `pace_or_spin` | Pace / Spin classification | Useful bowling-type grouping |
| `bowl_speed` | Recorded bowling speed | 77,861 rows (38.7%) are zero; treat zero as missing/unknown unless RR confirms that zero is a valid measurement |
| `stroke` | Shot/stroke label | Useful exploratory feature; 12 blanks |
| `delivery_style` | Delivery variation/style label | Useful exploratory feature; 7 blanks |
| `over_or_around` | Bowler's angle/line label | 407 blanks; normalize text before use |
| `on_or_off` | On-side / Off-side direction label | Observed values are On-side and Off-side |
| `delivery_ist_time` | Delivery timestamp field | Name indicates IST, but sample values carry `UTC`; verify timezone semantics. Prefer innings/over sequence fields for ball ordering. |

### 4.2 `matches.csv` — 22 columns

| Column | Observed / likely meaning | Use / caution |
|---|---|---|
| `match_id` | Match identifier | Primary match key |
| `comp_id` | Competition identifier | Join to `competitions.comp_id` |
| `match_number` | Match number within competition | Context only |
| `match_date` | Match date | Date filtering and season grouping |
| `stage` | Competition stage | League, final, qualifier, eliminator, etc. |
| `venue_id` | Venue identifier | Venue joins require a venue reference table, which is not in this pack |
| `venue_country` | Country of venue | Context split |
| `home_team_id`, `home_team` | Home team ID and name | Team context |
| `away_team_id`, `away_team` | Away team ID and name | Team context |
| `home_team_captain_id` | Home captain ID | Missing in 44 rows |
| `away_team_captain_id` | Away captain ID | Missing in 45 rows |
| `toss_win_team_id` | Toss-winning team ID | Missing in 15 rows |
| `toss_opted` | Batting/fielding toss decision | Missing in 15 rows |
| `man_of_the_match` | Player ID or zero placeholder | 119 rows contain `0`; treat as missing unless confirmed |
| `first_inn_revised_overs` | Revised first-innings limit | Values/units need confirmation; do not assume the values are overs without a data dictionary |
| `second_inn_revised_overs` | Revised second-innings limit | Same unit caution; blank in 858 rows |
| `revised_target` | Revised chase target | Populated in only 23 of 883 rows; cannot be the only source of chase targets |
| `knock_out` | Knockout-stage flag | Values 0/1 observed |
| `win_team_id` | Winning team ID | Missing in 41 rows; use with result carefully |
| `result` | Result text | 670 distinct strings; useful for match outcome, not a substitute for delivery-level score progression |

### 4.3 `playing_eleven.csv` — 9 columns

| Column | Observed / likely meaning | Use / caution |
|---|---|---|
| `match_id` | Match identifier | Join to matches |
| `team_id` | Team identifier | Join with match competition |
| `player_id` | Player identifier | Prefer ID to name |
| `batting_order` | Recorded batting order | Blank for 8,678 rows; 11 rows are marked played but have blank order |
| `is_played` | Whether player is marked as played | 19,714 true and 8,667 false; confirm exact meaning for substitutes/impact players |
| `is_captain` | Captain flag | Blank for 8,667 rows |
| `is_wk` | Wicketkeeper flag | Blank for 8,667 rows |
| `is_impact` | Impact-player indicator | 558 rows have value 1 |
| `is_impact_off` | Impact-player-off indicator | 558 rows have value 1; confirm semantics before using |

There are 35 repeated `(match_id, team_id, player_id)` keys (40 excess rows), concentrated in three matches (`13613`, `21176`, `28962`). These records have different `batting_order` values. They are not byte-for-byte duplicate rows. Deduplicate or resolve this table carefully before using it for player appearance counts.

### 4.4 `competition_team_player_mapping.csv` — 6 columns

| Column | Meaning | Use |
|---|---|---|
| `comp_id` | Competition identifier | Competition join |
| `comp_name` | Competition name | Scope filtering and display |
| `team_id` | Team identifier in competition | Team join |
| `team_name` | Team name | Display |
| `player_id` | Player identifier | Player join |
| `player_name` | Player name | Display; IDs should remain the calculation key |

### 4.5 `competitions.csv` — 4 columns

| Column | Meaning | Use |
|---|---|---|
| `comp_id` | Competition identifier | Primary competition key |
| `comp_name` | Competition name | Exact IPL filtering; identify T20I competitions |
| `match_format` | Format label (`T20I` or `T20`) | Main scope filter |
| `season` | Competition season | Season comparison |

### 4.6 `teams.csv` — 3 columns

| Column | Meaning | Use |
|---|---|---|
| `comp_id` | Competition identifier | Part of team key |
| `team_id` | Team identifier | Part of team key |
| `team_name` | Team name | Display |

## 5. Critical data-quality findings

1. **Score reconstruction is not yet safe.** `runs` appears to capture the batter-run component, while `extras1_runs` is an extras-type code and `extras_2_runs` is almost always zero. Wide, bye and leg-bye records do not expose a clearly interpretable complete extra-run amount. Do not calculate current team score, required run rate, runs remaining, or bowler economy from assumed sums until RR explains these fields.
2. **`extras1_runs` is categorical.** It maps exactly to `extras_type` in this file and must never be summed as runs.
3. **`extras_2_runs` is undefined.** Ask RR what it represents and whether another field/lookup is missing.
4. **Ball sequence fields include extra deliveries.** `over_ball_num` reaches 13 and `innings_ball_num` is a delivery sequence. Neither should be mistaken for legal balls without applying delivery rules.
5. **Boundary flags have 23 mismatches** against the `runs` value (20 fours and 3 sixes where the matching flag is false).
6. **Bowling speed is incomplete.** 38.7% of `bowl_speed` values are zero.
7. **Bowler wicket attribution needs dismissal filtering.** There are 10,881 wicket events. Run outs (600), retired outs (6) and obstructing-the-field dismissals (3) should not be credited as bowler wickets. Other dismissal categories still need standard rule-aware treatment.
8. **Super Overs exist.** Six matches contain innings 3 and 4 (38 delivery rows in total). Decide whether to exclude them from ordinary innings pressure rankings or analyse them separately.
9. **Abandoned matches have no deliveries.** All 16 matches missing ball-by-ball records are marked `Match Abandoned`; exclude them from delivery-performance metrics, but retain them in match counts only where relevant.
10. **Playing-XI key collisions exist.** The 35 repeated match/team/player keys in three matches have conflicting batting-order values; don't count them as separate player appearances.
11. **Revised target data is sparse.** `revised_target` is blank in 860 of 883 matches. Revised-overs fields also need their units confirmed.
12. **Timestamp semantics need confirmation.** `delivery_ist_time` values include a `UTC` suffix despite the column name containing `ist`; do not derive local match timing from this field without clarification.

## 6. Safe vs. blocked analyses at this stage

| Analysis | Status | Reason |
|---|---|---|
| Batter runs as stored in `runs` | Provisional | Confirm whether this is batter runs only |
| Boundary count using flags | Provisional | 23 flag/value mismatches |
| Batter faced-ball count | Derivable with delivery rules | Exclude wides; count no-balls as faced balls, subject to confirmation of `Overstep` |
| Innings stage / over phase | Derivable | Use sequence fields, not naive legal-ball assumptions |
| Wickets lost before a delivery | Derivable with dismissal sequence | Need to handle wicket events and Super Overs correctly |
| Bowler wickets | Derivable after dismissal filtering | Exclude run out, retired out and obstructing the field |
| Pressure classification by over stage and wickets | Feasible as a transparent proxy | Must be labelled as a proxy, not actual chase pressure |
| Exact chase pressure / required run rate | Blocked pending data clarification | Complete innings score and target cannot yet be reconstructed safely |
| Bowling economy / runs conceded | Blocked pending data clarification | Extra-run representation is unclear |

## 7. Questions to send to Rajasthan Royals

1. Is `runs` batter runs only, or total runs scored off the delivery?
2. What exactly do `extras1_runs` and `extras_2_runs` represent? Please share the codebook and one or two examples for each `extras_type`.
3. How should total team runs be reconstructed for wides, no-balls/`Overstep`, byes, leg-byes and `other` extras?
4. Does `over_ball_num` count all recorded deliveries, including wides and no-balls? Which field should be used to calculate legal balls and balls faced?
5. What are the units for `first_inn_revised_overs` and `second_inn_revised_overs`? Are they balls or overs?
6. Does `is_played` mean part of the starting XI, appeared in the match, or active after substitutions? What do `is_impact` and `is_impact_off` mean?
7. Is the `delivery_ist_time` timezone UTC or IST?

## 8. Recommended next step

Do not rank players yet. First obtain RR's clarification for score/extras and delivery-count semantics. In parallel, build a reproducible cleaning pipeline that:

- filters to IPL + T20I only;
- joins by IDs;
- orders deliveries using match, innings and sequence fields;
- identifies regular innings separately from Super Overs;
- records all exclusions and data-quality warnings;
- keeps unknown values unknown instead of silently converting them to zero.

Only after these checks should we define pressure conditions and player ratings.
