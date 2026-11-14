# RR SupeRR Selector — Analysis-ready IPL + T20I pack

This is a filtered working copy of the supplied RR data pack. Original source values have been preserved; uncertain fields have not been silently corrected.

## Scope
- Matches: 853 (T20I: 482; IPL: 371)
- Matches with ball-by-ball records: 837
- Ball-by-ball rows: 194014
- Abandoned matches with no ball rows: 16
- Excluded: 30 matches from Men's T20 Emerging Teams Asia Cup 2024 and Asia Cup Rising Stars 2025 (these are non-IPL T20 competitions, not T20I).

## Files
- `matches_ipl_t20i.csv`: all 853 matches in the requested scope, including abandoned matches; adds competition name/format/season.
- `ball_by_ball_ipl_t20i.csv`: ball-by-ball rows for the 837 matches with delivery records; adds match and competition context.
- `playing_eleven_ipl_t20i.csv`: playing-eleven records for matches in scope; repeated keys retained.
- `competition_team_player_mapping_ipl_t20i.csv`: competition/team/player lookup for the scope.
- `competitions_ipl_t20i.csv`: competitions represented in scoped match rows.
- `teams_ipl_t20i.csv`: teams for scoped competitions.
- `data_quality_summary.csv`: issues and recommended handling.
- `delivery_anomalies.csv`: delivery rows with boundary-flag mismatches, non-zero extras_2_runs, missing dismissed-player ID, or innings 3/4.
- `playing_eleven_key_conflicts.csv`: all rows involved in repeated match/team/player keys.
- `DATA_DICTIONARY_AND_AUDIT.md`: full column dictionary, scope audit and questions for RR.

## Critical caution
`extras1_runs` is an extras-type code, not runs. The meanings of `runs` and `extras_2_runs` are not sufficiently documented to safely reconstruct total innings scores, required run rate or bowling economy. Obtain RR's data dictionary before building score-dependent pressure metrics.

## Ordering
Within an innings, use `innings_ball_num` to preserve delivery order. It counts recorded deliveries, including extra deliveries; calculate legal balls using explicit wides/no-balls rules after RR confirms field semantics. Treat innings 3 and 4 separately as possible Super Overs.
