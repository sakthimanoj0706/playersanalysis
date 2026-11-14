"""Tests for V3 Pressure Feature Completeness and Missing-Data Integrity."""
import pytest
import pandas as pd
import numpy as np

from src.pressure_engine.v3_pressure_model import V3PressureModel


def test_missing_features_produce_unclassified_not_normal():
    """Verify that deliveries with missing features are marked PRESSURE_UNCLASSIFIED and NOT normal."""
    # Delivery missing 'wickets_in_last_12_legal_balls' and 'consecutive_dots'
    df_missing = pd.DataFrame([{
        'wickets_fallen_before': 2,
        'batter_balls_faced': 15,
        'dots_in_last_12_legal_balls': 4,
        'innings_phase': 'middle',
        'boundaries_in_last_12_legal_balls': 1,
        'batting_wickets_remaining': 8
    }])

    res = V3PressureModel.apply_dual_pressure(df_missing)

    # Batting should be invalid
    assert res.loc[0, 'batting_pressure_data_valid'] == False
    assert 'wickets_in_last_12_legal_balls' in res.loc[0, 'batting_pressure_missing_features']
    assert 'consecutive_dots' in res.loc[0, 'batting_pressure_missing_features']
    assert np.isnan(res.loc[0, 'batting_crisis_score'])
    assert res.loc[0, 'batting_pressure_tier'] == 'PRESSURE_UNCLASSIFIED'
    assert res.loc[0, 'is_batting_normal_pressure'] == False
    assert res.loc[0, 'is_batting_high_pressure'] == False
    assert res.loc[0, 'is_batting_moderate_pressure'] == False


def test_mutual_exclusivity_of_pressure_tiers():
    """Verify that high, moderate, normal, and unclassified pressure tiers are mutually exclusive."""
    df = pd.DataFrame([
        # Valid High
        {'wickets_fallen_before': 7, 'batting_wickets_remaining': 3, 'wickets_in_last_12_legal_balls': 2, 'batter_balls_faced': 2, 'consecutive_dots': 3, 'dots_in_last_12_legal_balls': 8, 'boundaries_in_last_12_legal_balls': 3, 'innings_phase': 'death'},
        # Valid Moderate
        {'wickets_fallen_before': 2, 'batting_wickets_remaining': 8, 'wickets_in_last_12_legal_balls': 0, 'batter_balls_faced': 10, 'consecutive_dots': 1, 'dots_in_last_12_legal_balls': 4, 'boundaries_in_last_12_legal_balls': 1, 'innings_phase': 'middle'},
        # Valid Normal
        {'wickets_fallen_before': 0, 'batting_wickets_remaining': 10, 'wickets_in_last_12_legal_balls': 0, 'batter_balls_faced': 25, 'consecutive_dots': 0, 'dots_in_last_12_legal_balls': 1, 'boundaries_in_last_12_legal_balls': 0, 'innings_phase': 'powerplay'},
        # Incomplete / Unclassified
        {'wickets_fallen_before': np.nan, 'batting_wickets_remaining': np.nan, 'wickets_in_last_12_legal_balls': 0, 'batter_balls_faced': 10, 'consecutive_dots': 0, 'dots_in_last_12_legal_balls': 2, 'boundaries_in_last_12_legal_balls': 0, 'innings_phase': 'unknown'}
    ])

    res = V3PressureModel.apply_dual_pressure(df)

    for i in range(len(res)):
        # At most one is True
        bat_flags = [
            res.loc[i, 'is_batting_high_pressure'],
            res.loc[i, 'is_batting_moderate_pressure'],
            res.loc[i, 'is_batting_normal_pressure']
        ]
        bowl_flags = [
            res.loc[i, 'is_bowling_high_pressure'],
            res.loc[i, 'is_bowling_moderate_pressure'],
            res.loc[i, 'is_bowling_normal_pressure']
        ]
        assert sum(bat_flags) <= 1
        assert sum(bowl_flags) <= 1

        if not res.loc[i, 'batting_pressure_data_valid']:
            assert sum(bat_flags) == 0
            assert res.loc[i, 'batting_pressure_tier'] == 'PRESSURE_UNCLASSIFIED'
        else:
            assert sum(bat_flags) == 1

        if not res.loc[i, 'bowling_pressure_data_valid']:
            assert sum(bowl_flags) == 0
            assert res.loc[i, 'bowling_pressure_tier'] == 'PRESSURE_UNCLASSIFIED'
        else:
            assert sum(bowl_flags) == 1


def test_future_outcomes_cannot_affect_pre_delivery_pressure():
    """Verify that runs or wickets on the ball never leak into pre-delivery pressure."""
    row = {
        'wickets_fallen_before': 3,
        'batting_wickets_remaining': 7,
        'wickets_in_last_12_legal_balls': 1,
        'batter_balls_faced': 12,
        'consecutive_dots': 2,
        'dots_in_last_12_legal_balls': 5,
        'boundaries_in_last_12_legal_balls': 1,
        'innings_phase': 'middle'
    }

    df_dot = pd.DataFrame([{**row, 'batter_runs': 0, 'is_wicket': False, 'is_four': False, 'is_six': False}])
    df_six = pd.DataFrame([{**row, 'batter_runs': 6, 'is_wicket': False, 'is_four': False, 'is_six': True}])
    df_wkt = pd.DataFrame([{**row, 'batter_runs': 0, 'is_wicket': True, 'is_four': False, 'is_six': False}])

    res_dot = V3PressureModel.apply_dual_pressure(df_dot)
    res_six = V3PressureModel.apply_dual_pressure(df_six)
    res_wkt = V3PressureModel.apply_dual_pressure(df_wkt)

    assert res_dot.loc[0, 'batting_crisis_score'] == res_six.loc[0, 'batting_crisis_score']
    assert res_dot.loc[0, 'batting_crisis_score'] == res_wkt.loc[0, 'batting_crisis_score']
    assert res_dot.loc[0, 'bowling_defensive_score'] == res_six.loc[0, 'bowling_defensive_score']
    assert res_dot.loc[0, 'bowling_defensive_score'] == res_wkt.loc[0, 'bowling_defensive_score']


def test_cached_parquet_schema_and_integrity():
    """Validate that the cached ball_by_ball_with_pressure parquet matches the V3 schema."""
    from pathlib import Path
    press_path = Path("data/features/ball_by_ball_with_pressure.parquet")
    if not press_path.exists():
        pytest.skip("Parquet not built yet")

    df = pd.read_parquet(press_path)
    required_cols = [
        'canonical_striker_id', 'canonical_bowler_id',
        'batting_pressure_data_valid', 'bowling_pressure_data_valid',
        'batting_crisis_score', 'bowling_defensive_score',
        'is_batting_high_pressure', 'is_batting_normal_pressure',
        'is_bowling_high_pressure', 'is_bowling_normal_pressure',
        'v3_pressure_schema_version'
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"

    assert df['batting_pressure_data_valid'].all()
    assert df['bowling_pressure_data_valid'].all()
    assert len(df) == 193988

