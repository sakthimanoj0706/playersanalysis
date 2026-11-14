"""Phase 0 & 1: Data Audit, Semantics Verification, and Cohort Reconstruction."""
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REPORTS_V3 = DATA_DIR / "reports" / "v3"
OUTPUTS_V3 = DATA_DIR / "outputs" / "v3"
REPORTS_V3.mkdir(parents=True, exist_ok=True)
OUTPUTS_V3.mkdir(parents=True, exist_ok=True)

def run_audit():
    logging.info("Loading source files...")
    bbb = pd.read_csv(DATA_DIR / "ball_by_ball_ipl_t20i.csv", dtype={'season': str})
    matches = pd.read_csv(DATA_DIR / "matches_ipl_t20i.csv")
    p11 = pd.read_csv(DATA_DIR / "playing_eleven_ipl_t20i.csv")
    mapping = pd.read_csv(DATA_DIR / "competition_team_player_mapping_ipl_t20i.csv")
    comps = pd.read_csv(DATA_DIR / "competitions_ipl_t20i.csv")
    teams = pd.read_csv(DATA_DIR / "teams_ipl_t20i.csv")

    logging.info(f"Loaded: BBB={len(bbb)}, Matches={len(matches)}, P11={len(p11)}, Teams={len(teams)}, Comps={len(comps)}, Mapping={len(mapping)}")

    # 1. Matches Cohort Audit
    total_matches = len(matches)
    ipl_matches = matches[matches['match_format'] == 'T20']
    t20i_matches = matches[matches['match_format'] == 'T20I']
    matches_with_bbb = set(bbb['match_id'].unique())
    matches_without_bbb = set(matches['match_id']) - matches_with_bbb

    # Check match results / abandoned
    abandoned_no_result = matches[matches['result'].isin(['abandoned', 'no result']) | matches['win_team_id'].isna()]
    dls_matches = matches[matches['revised_target'].notna() & (matches['revised_target'] > 0)]

    # BBB Innings Breakdown
    regular_inns = bbb[bbb['innings'].isin([1, 2])]
    super_overs = bbb[bbb['innings'].isin([3, 4])]

    print(f"Total Matches: {total_matches}")
    print(f"IPL Matches: {len(ipl_matches)}")
    print(f"T20I Matches: {len(t20i_matches)}")
    print(f"Matches with BBB data: {len(matches_with_bbb)}")
    print(f"Matches missing BBB data: {len(matches_without_bbb)} -> {matches_without_bbb}")
    print(f"DLS / Revised Target matches: {len(dls_matches)}")
    print(f"Regular deliveries (inns 1-2): {len(regular_inns)}")
    print(f"Super over deliveries (inns 3-4): {len(super_overs)}")

    # 2. Extras Analysis
    print("\n--- EXTRAS1_RUNS DISTRIBUTION ---")
    print(bbb['extras1_runs'].value_counts(dropna=False).sort_index())

    print("\n--- EXTRAS_2_RUNS DISTRIBUTION ---")
    print(bbb['extras_2_runs'].value_counts(dropna=False).sort_index())

    print("\n--- EXTRAS_TYPE VS EXTRAS1_RUNS ---")
    print(pd.crosstab(bbb['extras_type'], bbb['extras1_runs'], dropna=False))

    # Cross check runs when extras1_runs == 2 (wide)
    wides = bbb[bbb['extras1_runs'] == 2]
    print(f"\nWide balls count: {len(wides)}")
    print("Runs distribution on wides:")
    print(wides['runs'].value_counts(dropna=False))

    # Oversteps (no balls)
    noballs = bbb[bbb['extras1_runs'] == 1]
    print(f"\nNo-ball (Overstep) count: {len(noballs)}")
    print("Runs distribution on no-balls:")
    print(noballs['runs'].value_counts(dropna=False))

    # 3. Boundary flag audit
    fours_discrepancy = bbb[(bbb['runs'] == 4) & (bbb['is_four'] == False)]
    sixes_discrepancy = bbb[(bbb['runs'] == 6) & (bbb['is_six'] == False)]
    print(f"\nFours discrepancy (runs=4, is_four=False): {len(fours_discrepancy)}")
    print(f"Sixes discrepancy (runs=6, is_six=False): {len(sixes_discrepancy)}")

    # 4. Dismissal audit
    wickets = bbb[bbb['is_wicket'] == True]
    print(f"\nWickets count: {len(wickets)}")
    print("Dismissal types:")
    print(wickets['dismissal_type'].value_counts(dropna=False))
    missing_dismissed_player = wickets[wickets['dismissed_player_id'].isna()]
    print(f"Missing dismissed_player_id on wicket: {len(missing_dismissed_player)}")

    # Bowler creditable
    non_bowler = ['Run Out', 'RunOut', 'Retired Out', 'Retire Out', 'Obstructing the field', 'Obstracting the field']
    bowler_creditable = wickets[~wickets['dismissal_type'].isin(non_bowler)]
    non_bowler_wickets = wickets[wickets['dismissal_type'].isin(non_bowler)]
    print(f"Bowler creditable wickets: {len(bowler_creditable)}")
    print(f"Non-bowler wickets: {len(non_bowler_wickets)}")

    # Stumpings on wides
    stumpings_wide = bbb[(bbb['dismissal_type'] == 'Stumped') & (bbb['extras1_runs'] == 2)]
    print(f"Stumpings on wide deliveries: {len(stumpings_wide)}")

    # 5. Playing Eleven Conflicts
    pe_grouped = p11.groupby(['match_id', 'team_id', 'player_id']).size()
    duplicates_p11 = pe_grouped[pe_grouped > 1]
    print(f"\nDuplicate playing eleven records: {len(duplicates_p11)}")

    # 6. Build MATCH_COHORT_MANIFEST.csv
    cohort_records = []
    for _, m in matches.iterrows():
        mid = m['match_id']
        has_bbb = mid in matches_with_bbb
        n_balls = len(bbb[bbb['match_id'] == mid]) if has_bbb else 0
        is_ipl = m['match_format'] == 'T20'
        is_t20i = m['match_format'] == 'T20I'
        is_dls = pd.notna(m.get('revised_target')) and m.get('revised_target', 0) > 0
        is_ab = str(m.get('result', '')).lower() in ['abandoned', 'no result'] or pd.isna(m.get('win_team_id'))
        has_super_over = len(bbb[(bbb['match_id'] == mid) & (bbb['innings'].isin([3, 4]))]) > 0
        
        status = 'INCLUDED'
        quarantine_reason = 'None'
        if not has_bbb:
            status = 'EXCLUDED'
            quarantine_reason = 'NO_BALL_BY_BALL_DATA'
        elif is_ab:
            status = 'QUARANTINED_ABANDONED'
            quarantine_reason = 'ABANDONED_OR_NO_RESULT'
        elif is_dls:
            status = 'FLAGGED_DLS'
            quarantine_reason = 'DLS_REVISED_TARGET'
            
        cohort_records.append({
            'match_id': mid,
            'comp_id': m['comp_id'],
            'comp_name': m.get('comp_name', ''),
            'match_format': m['match_format'],
            'season': m.get('season', ''),
            'match_date': m.get('match_date', ''),
            'home_team': m.get('home_team', ''),
            'away_team': m.get('away_team', ''),
            'result': m.get('result', ''),
            'win_team_id': m.get('win_team_id', ''),
            'deliveries_count': n_balls,
            'has_super_over': has_super_over,
            'is_dls': is_dls,
            'status': status,
            'quarantine_reason': quarantine_reason
        })
    cohort_df = pd.DataFrame(cohort_records)
    cohort_df.to_csv(REPORTS_V3 / "MATCH_COHORT_MANIFEST.csv", index=False)
    logging.info(f"Saved MATCH_COHORT_MANIFEST.csv with {len(cohort_df)} matches")

    # 7. Quarantined Records CSV
    quarantined = cohort_df[cohort_df['status'] != 'INCLUDED']
    quarantined.to_csv(REPORTS_V3 / "QUARANTINED_RECORDS.csv", index=False)
    logging.info(f"Saved QUARANTINED_RECORDS.csv with {len(quarantined)} records")

    return {
        'total_matches': total_matches,
        'ipl_matches': len(ipl_matches),
        't20i_matches': len(t20i_matches),
        'matches_with_bbb': len(matches_with_bbb),
        'matches_without_bbb': len(matches_without_bbb),
        'dls_matches': len(dls_matches),
        'regular_deliveries': len(regular_inns),
        'super_over_deliveries': len(super_overs),
        'fours_discrepancy': len(fours_discrepancy),
        'sixes_discrepancy': len(sixes_discrepancy),
        'bowler_creditable': len(bowler_creditable),
        'non_bowler_wickets': len(non_bowler_wickets),
        'duplicates_p11': len(duplicates_p11)
    }

if __name__ == '__main__':
    run_audit()
