"""V3 Bowling Tail-Risk and Multi-Objective Pareto Analysis.

Evaluates high-leverage tail risk for bowlers:
1. Binary over-level tail events (e.g., overs with 2+ boundaries conceded off the bat).
2. Upper-tail loss metrics: Value-at-Risk (VaR_90) and Conditional Value-at-Risk (CVaR_90 / Expected Shortfall).
3. Multi-objective Pareto frontier comparing:
   - Run suppression (dot ball retention)
   - Wicket threat (hazard/wicket rate)
   - Tail-risk mitigation (1 - CVaR risk)

Governance Notice:
Because raw extras1_runs is categorical and total bowling runs conceded are quarantined,
all run-based tail metrics operate strictly on verified batter-runs-off-the-bat,
or on verified binary boundary over events.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class V3TailRiskAnalyzer:
    """Evaluates extreme tail outcomes and Pareto trade-offs for bowling."""

    @staticmethod
    def compute_over_level_risk(df: pd.DataFrame, min_overs: int = 15) -> pd.DataFrame:
        """Aggregate delivery logs to over level and calculate tail risk metrics."""
        legal = df[df['is_legal_ball'] == True].copy()
        runs_col = 'batter_runs' if 'batter_runs' in legal.columns else 'runs'

        if 'is_dot_ball' in legal.columns:
            dot_func = 'sum'
            dot_col = 'is_dot_ball'
        else:
            dot_func = lambda x: (x == 0).sum()
            dot_col = runs_col

        # Group by match_id, innings, overid, bowler_id
        over_agg = legal.groupby(['match_id', 'innings', 'overid', 'bowler_id']).agg(
            legal_balls=(runs_col, 'count'),
            bat_runs=(runs_col, 'sum'),
            fours=('is_four_validated' if 'is_four_validated' in legal.columns else 'is_four', 'sum'),
            sixes=('is_six_validated' if 'is_six_validated' in legal.columns else 'is_six', 'sum'),
            wickets=('is_bowler_wicket' if 'is_bowler_wicket' in legal.columns else 'is_wicket', 'sum'),
            dots=(dot_col, dot_func)
        ).reset_index()

        # Only full 6-ball legal overs
        full_overs = over_agg[over_agg['legal_balls'] >= 6].copy()
        full_overs['boundaries'] = full_overs['fours'] + full_overs['sixes']
        full_overs['is_bad_over'] = (full_overs['boundaries'] >= 2) | (full_overs['bat_runs'] >= 12)

        # Aggregate by bowler
        bowler_risk = []
        for bid, grp in full_overs.groupby('bowler_id'):
            n_overs = len(grp)
            if n_overs < min_overs:
                continue

            runs_arr = grp['bat_runs'].values
            q90 = np.percentile(runs_arr, 90)
            cvar90 = runs_arr[runs_arr >= q90].mean() if len(runs_arr[runs_arr >= q90]) > 0 else q90
            bad_over_rate = grp['is_bad_over'].mean() * 100.0
            dot_rate = (grp['dots'].sum() / (n_overs * 6)) * 100.0
            wicket_rate = (grp['wickets'].sum() / (n_overs * 6)) * 100.0

            bowler_risk.append({
                'bowler_id': bid,
                'overs_bowled': n_overs,
                'mean_over_bat_runs': round(float(runs_arr.mean()), 2),
                'var_90': round(float(q90), 2),
                'cvar_90': round(float(cvar90), 2),
                'bad_over_rate_pct': round(float(bad_over_rate), 2),
                'dot_rate_pct': round(float(dot_rate), 2),
                'wicket_rate_pct': round(float(wicket_rate), 2),
            })

        risk_df = pd.DataFrame(bowler_risk)
        if len(risk_df) == 0:
            return pd.DataFrame(columns=['bowler_id', 'overs_bowled', 'mean_over_bat_runs', 'var_90', 'cvar_90', 'bad_over_rate_pct', 'dot_rate_pct', 'wicket_rate_pct', 'is_pareto_optimal'])

        # Identify Pareto Frontier (Maximizing Dot Rate, Maximizing Wicket Rate, Minimizing CVaR_90)
        # Point A dominates Point B if A is >= B in all objectives and strictly > in at least one.
        is_pareto = []
        for i, row in risk_df.iterrows():
            dominated = False
            for j, other in risk_df.iterrows():
                if i == j:
                    continue
                # other dominates row if other has >= dots, >= wkts, and <= cvar, with one strict inequality
                if (other['dot_rate_pct'] >= row['dot_rate_pct'] and
                    other['wicket_rate_pct'] >= row['wicket_rate_pct'] and
                    other['cvar_90'] <= row['cvar_90'] and
                    (other['dot_rate_pct'] > row['dot_rate_pct'] or
                     other['wicket_rate_pct'] > row['wicket_rate_pct'] or
                     other['cvar_90'] < row['cvar_90'])):
                    dominated = True
                    break
            is_pareto.append(not dominated)

        risk_df['is_pareto_optimal'] = is_pareto
        return risk_df.sort_values(['is_pareto_optimal', 'dot_rate_pct'], ascending=[False, False]).reset_index(drop=True)
