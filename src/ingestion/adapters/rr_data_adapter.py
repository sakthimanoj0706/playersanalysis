"""Provider adapter for Rajasthan Royals / IPL / T20I dataset.

Standardizes delivery and match semantics with explicit lineage and provenance tracking.
Preserves raw fields untouched and creates documented derived fields.
"""
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from src.config import EXTRAS_TYPE_MAP, NON_BOWLER_DISMISSALS, SUPER_OVER_INNINGS, PHASE_OVERS


class RRDataAdapter:
    """Standardizes delivery records from the RR source data format."""

    def __init__(self, quarantine_unknown_extras: bool = True):
        self.quarantine_unknown_extras = quarantine_unknown_extras

    def transform_deliveries(self, bbb_df: pd.DataFrame) -> pd.DataFrame:
        """Apply documented semantic transformations to raw ball-by-ball DataFrame."""
        df = bbb_df.copy()

        # 1. Extras categorization (strictly categorical mapping)
        df['extras_category'] = df['extras1_runs'].map(EXTRAS_TYPE_MAP).fillna('Unknown')
        
        # 2. Flag balls faced by batter:
        # Wides do not count as a ball faced; No-balls (Overstep) count as a ball faced
        df['is_ball_faced'] = df['extras_category'] != 'wide'

        # 3. Flag legal balls bowled:
        # Neither wides nor oversteps (no-balls) are legal balls
        df['is_legal_ball'] = ~df['extras_category'].isin({'wide', 'Overstep'})

        # 4. Batter runs (verified as the runs off the bat)
        df['batter_runs'] = df['runs'].fillna(0).astype(int)

        # 5. Boundary audit and reconciliation
        bat_hit = df['extras_category'].isin({'None', 'Overstep'})
        df['is_four_validated'] = df['is_four'] | ((df['batter_runs'] == 4) & bat_hit)
        df['is_six_validated'] = df['is_six'] | ((df['batter_runs'] == 6) & bat_hit)
        df['is_boundary_validated'] = df['is_four_validated'] | df['is_six_validated']
        df['boundary_discrepancy_flag'] = (
            (df['is_four'] != df['is_four_validated']) |
            (df['is_six'] != df['is_six_validated'])
        )

        # 6. Bowler-creditable wicket classification
        is_wicket = df['is_wicket'] == True
        is_non_bowler = df['dismissal_type'].isin(NON_BOWLER_DISMISSALS)
        df['is_bowler_wicket'] = is_wicket & ~is_non_bowler
        df['is_non_bowler_dismissal'] = is_wicket & is_non_bowler

        # 7. Dot ball identification (on legal balls where batter_runs == 0)
        df['is_dot_ball'] = df['is_legal_ball'] & (df['batter_runs'] == 0)

        # 8. Innings phase
        conditions = [
            (df['overid'] >= 1) & (df['overid'] <= 6),
            (df['overid'] >= 7) & (df['overid'] <= 15),
            (df['overid'] >= 16) & (df['overid'] <= 20)
        ]
        choices = ['powerplay', 'middle', 'death']
        df['innings_phase'] = np.select(conditions, choices, default='unknown')

        # 9. Super Over Flag
        df['is_super_over'] = df['innings'].isin(SUPER_OVER_INNINGS)

        # 10. Quarantine flag for unknown extras_2_runs
        if self.quarantine_unknown_extras and 'extras_2_runs' in df.columns:
            df['quarantine_extras2_flag'] = df['extras_2_runs'] > 0
        else:
            df['quarantine_extras2_flag'] = False

        return df

    def separate_cohorts(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Separate regular 20-over deliveries from super-over deliveries."""
        regular = df[~df['is_super_over']].copy()
        super_overs = df[df['is_super_over']].copy()
        return regular, super_overs
