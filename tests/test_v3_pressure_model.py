"""Tests for V3 Pre-Delivery Dual Pressure Models."""
import pytest
import pandas as pd
import numpy as np

from src.pressure_engine.v3_pressure_model import V3PressureModel


def test_zero_target_leakage_and_bounds():
    """Ensure pressure score stays bounded [0, 10] and is independent of future outcomes."""
    df = pd.DataFrame([
        # High batting crisis: 6 wickets down, cluster of 2 wickets, new batter (1 ball faced)
        {'wickets_fallen_before': 6, 'batting_wickets_remaining': 4, 'wickets_in_last_12_legal_balls': 2, 'batter_balls_faced': 1, 'consecutive_dots': 3, 'dots_in_last_12_legal_balls': 8, 'boundaries_in_last_12_legal_balls': 2, 'innings_phase': 'death', 'runs': 6, 'is_wicket': False},
        # Low batting crisis: 0 wickets down, 40 balls faced
        {'wickets_fallen_before': 0, 'batting_wickets_remaining': 10, 'wickets_in_last_12_legal_balls': 0, 'batter_balls_faced': 40, 'consecutive_dots': 0, 'dots_in_last_12_legal_balls': 2, 'boundaries_in_last_12_legal_balls': 0, 'innings_phase': 'powerplay', 'runs': 0, 'is_wicket': True},
        # High bowling defensive: 9 wickets in hand, death phase, 3 boundaries in last 12
        {'wickets_fallen_before': 1, 'batting_wickets_remaining': 9, 'wickets_in_last_12_legal_balls': 0, 'batter_balls_faced': 30, 'consecutive_dots': 0, 'dots_in_last_12_legal_balls': 1, 'boundaries_in_last_12_legal_balls': 3, 'innings_phase': 'death', 'runs': 0, 'is_wicket': True},
        # Low bowling defensive: 2 wickets in hand, middle phase, 0 boundaries in last 12
        {'wickets_fallen_before': 8, 'batting_wickets_remaining': 2, 'wickets_in_last_12_legal_balls': 0, 'batter_balls_faced': 30, 'consecutive_dots': 0, 'dots_in_last_12_legal_balls': 10, 'boundaries_in_last_12_legal_balls': 0, 'innings_phase': 'middle', 'runs': 4, 'is_wicket': False},
    ])

    res = V3PressureModel.apply_dual_pressure(df)

    # 1. Boundedness
    assert (res['batting_crisis_score'] >= 0.0).all() and (res['batting_crisis_score'] <= 10.0).all()
    assert (res['bowling_defensive_score'] >= 0.0).all() and (res['bowling_defensive_score'] <= 10.0).all()

    # 2. Logic checks
    assert res.loc[0, 'batting_crisis_score'] > res.loc[1, 'batting_crisis_score']
    assert res.loc[2, 'bowling_defensive_score'] > res.loc[3, 'bowling_defensive_score']

    # 3. Target independence: check that changing eventual 'runs' or 'is_wicket' does not alter pre-delivery score
    df_altered = df.copy()
    df_altered['runs'] = 100
    df_altered['is_wicket'] = ~df_altered['is_wicket']
    res_altered = V3PressureModel.apply_dual_pressure(df_altered)

    np.testing.assert_array_equal(res['batting_crisis_score'].values, res_altered['batting_crisis_score'].values)
    np.testing.assert_array_equal(res['bowling_defensive_score'].values, res_altered['bowling_defensive_score'].values)
