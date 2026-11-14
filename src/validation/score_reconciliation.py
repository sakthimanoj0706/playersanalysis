"""Score reconciliation and verification engine."""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class ScoreReconciliationEngine:
    """Verifies reconstructed delivery stats against reference totals."""

    @staticmethod
    def reconcile_batter_totals(deliveries_df: pd.DataFrame, reference_dict: Dict[int, Dict[str, float]]) -> pd.DataFrame:
        """Reconcile calculated batter runs and balls against official reference stats.
        
        reference_dict: {player_id: {'expected_runs': X, 'expected_balls': Y, 'player_name': str}}
        """
        faced = deliveries_df[deliveries_df['is_ball_faced']].copy() if 'is_ball_faced' in deliveries_df.columns else deliveries_df.copy()
        runs_col = 'batter_runs' if 'batter_runs' in faced.columns else 'runs'

        calc = faced.groupby('striker_id').agg(
            actual_balls=(runs_col, 'count'),
            actual_runs=(runs_col, 'sum'),
            actual_fours=('is_four_validated' if 'is_four_validated' in faced.columns else 'is_four', 'sum'),
            actual_sixes=('is_six_validated' if 'is_six_validated' in faced.columns else 'is_six', 'sum'),
        ).reset_index()

        reconciliation_rows = []
        for pid, ref in reference_dict.items():
            player_calc = calc[calc['striker_id'] == pid]
            act_runs = int(player_calc['actual_runs'].iloc[0]) if len(player_calc) > 0 else 0
            act_balls = int(player_calc['actual_balls'].iloc[0]) if len(player_calc) > 0 else 0
            
            exp_runs = ref.get('expected_runs')
            exp_balls = ref.get('expected_balls')
            
            runs_diff = act_runs - exp_runs if exp_runs is not None else None
            balls_diff = act_balls - exp_balls if exp_balls is not None else None
            
            reconciliation_rows.append({
                'player_id': pid,
                'player_name': ref.get('player_name', f'Player_{pid}'),
                'expected_runs': exp_runs,
                'actual_runs': act_runs,
                'runs_match': (runs_diff == 0) if exp_runs is not None else 'N/A',
                'expected_balls': exp_balls,
                'actual_balls': act_balls,
                'balls_match': (balls_diff == 0) if exp_balls is not None else 'N/A',
            })
            
        return pd.DataFrame(reconciliation_rows)

    @staticmethod
    def reconcile_bowler_wickets(deliveries_df: pd.DataFrame, reference_dict: Dict[int, Dict[str, float]]) -> pd.DataFrame:
        """Reconcile bowler-creditable wickets against reference figures."""
        wkt_col = 'is_bowler_wicket' if 'is_bowler_wicket' in deliveries_df.columns else 'is_wicket'
        calc = deliveries_df[deliveries_df[wkt_col] == True].groupby('bowler_id').size().reset_index(name='actual_wickets')

        rows = []
        for pid, ref in reference_dict.items():
            b_calc = calc[calc['bowler_id'] == pid]
            act_w = int(b_calc['actual_wickets'].iloc[0]) if len(b_calc) > 0 else 0
            exp_w = ref.get('expected_wickets')
            rows.append({
                'bowler_id': pid,
                'player_name': ref.get('player_name', f'Bowler_{pid}'),
                'expected_wickets': exp_w,
                'actual_wickets': act_w,
                'wickets_match': (act_w == exp_w) if exp_w is not None else 'N/A',
            })
        return pd.DataFrame(rows)
