"""Tests for V3 Bowling Tail-Risk & Pareto Analysis."""
import pytest
import pandas as pd
import numpy as np

from src.models.v3_tail_risk import V3TailRiskAnalyzer


def test_tail_risk_computation_and_pareto():
    """Ensure over-level tail metrics and Pareto frontier computation run properly."""
    records = []
    # Create 20 overs for 2 bowlers
    # Bowler 1: High control, low variance (cvar low)
    # Bowler 2: Expensive, high variance
    for m in range(1, 11):
        for inn in [1, 2]:
            for o in range(1, 3):
                for b in range(1, 7):
                    # Bowler 1
                    records.append({
                        'match_id': m, 'innings': inn, 'overid': o, 'bowler_id': 1,
                        'is_legal_ball': True, 'batter_runs': 0 if b < 5 else 1,
                        'is_four_validated': False, 'is_six_validated': False,
                        'is_bowler_wicket': (b == 6 and o == 1), 'is_dot_ball': (b < 5)
                    })
                    # Bowler 2
                    records.append({
                        'match_id': m, 'innings': inn, 'overid': o + 2, 'bowler_id': 2,
                        'is_legal_ball': True, 'batter_runs': 4 if b % 2 == 0 else 1,
                        'is_four_validated': (b % 2 == 0), 'is_six_validated': False,
                        'is_bowler_wicket': False, 'is_dot_ball': False
                    })
    df = pd.DataFrame(records)

    risk_df = V3TailRiskAnalyzer.compute_over_level_risk(df, min_overs=10)

    assert len(risk_df) == 2
    b1 = risk_df[risk_df['bowler_id'] == 1].iloc[0]
    b2 = risk_df[risk_df['bowler_id'] == 2].iloc[0]

    assert b1['cvar_90'] < b2['cvar_90']
    assert b1['dot_rate_pct'] > b2['dot_rate_pct']
    assert b1['is_pareto_optimal'] == True
    assert b2['is_pareto_optimal'] == False  # Dominated by bowler 1
