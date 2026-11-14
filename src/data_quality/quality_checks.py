"""Data Quality and Semantic Governance Engine."""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


class QualityAuditEngine:
    """Automated data quality validation and integrity checks."""

    @staticmethod
    def check_boundary_anomalies(df: pd.DataFrame) -> pd.DataFrame:
        """Find deliveries where runs are 4 or 6 but boundary flag is False."""
        mask = ((df['runs'] == 4) & (df['is_four'] == False)) | \
               ((df['runs'] == 6) & (df['is_six'] == False))
        return df[mask].copy()

    @staticmethod
    def check_wicket_attribution(df: pd.DataFrame) -> Dict[str, int]:
        """Audit wicket counts, bowler-creditable vs non-bowler, and missing IDs."""
        wickets = df[df['is_wicket'] == True]
        non_bowler_types = {'Run Out', 'RunOut', 'Retired Out', 'Retire Out', 'Obstructing the field', 'Obstracting the field'}
        bowler_wkts = wickets[~wickets['dismissal_type'].isin(non_bowler_types)]
        non_bowler_wkts = wickets[wickets['dismissal_type'].isin(non_bowler_types)]
        missing_player_id = wickets['dismissed_player_id'].isna().sum()

        return {
            'total_wickets': len(wickets),
            'bowler_creditable': len(bowler_wkts),
            'non_bowler': len(non_bowler_wkts),
            'missing_dismissed_player_id': int(missing_player_id)
        }

    @staticmethod
    def check_playing_xi_duplicates(p11_df: pd.DataFrame) -> pd.DataFrame:
        """Identify duplicate player entries for the same match and team."""
        dupes = p11_df[p11_df.duplicated(subset=['match_id', 'team_id', 'player_id'], keep=False)]
        return dupes.sort_values(['match_id', 'team_id', 'player_id']).copy()

    @staticmethod
    def check_quarantined_matches(matches_df: pd.DataFrame, bbb_df: pd.DataFrame) -> pd.DataFrame:
        """Flag matches missing BBB data, abandoned matches, and DLS revised target matches."""
        bbb_match_ids = set(bbb_df['match_id'].unique())
        records = []
        for _, row in matches_df.iterrows():
            mid = row['match_id']
            has_bbb = mid in bbb_match_ids
            is_dls = pd.notna(row.get('revised_target')) and row.get('revised_target', 0) > 0
            is_abandoned = str(row.get('result', '')).lower() in ['abandoned', 'no result'] or pd.isna(row.get('win_team_id'))

            if not has_bbb or is_dls or is_abandoned:
                reason = []
                if not has_bbb:
                    reason.append("MISSING_BALL_BY_BALL")
                if is_abandoned:
                    reason.append("ABANDONED_OR_NO_RESULT")
                if is_dls:
                    reason.append("DLS_REVISED_TARGET")

                records.append({
                    'match_id': mid,
                    'comp_name': row.get('comp_name', ''),
                    'season': row.get('season', ''),
                    'match_date': row.get('match_date', ''),
                    'reason': "; ".join(reason)
                })
        return pd.DataFrame(records)
