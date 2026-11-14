"""Tests for V3 Confidence Interval and Match-Clustered Bootstrap Integrity."""
import pytest
import pandas as pd
import numpy as np

from src.reliability.v3_reliability import V3ReliabilityEngine


def test_no_arbitrary_fixed_width_fallback_when_insufficient_matches():
    """Verify that players with <3 matches receive explicit unestimated status and NaN bounds."""
    # Batter with only 2 matches
    records = [
        {'match_id': 1, 'striker_id': 99, 'is_ball_faced': True, 'is_batting_high_pressure': True, 'batter_runs': 4},
        {'match_id': 2, 'striker_id': 99, 'is_ball_faced': True, 'is_batting_high_pressure': True, 'batter_runs': 0},
    ]
    df = pd.DataFrame(records)

    res = V3ReliabilityEngine.match_clustered_bootstrap_batting(df, player_id=99, min_matches=3)

    assert res['ci_status'] == 'NOT_ESTIMATED_INSUFFICIENT_MATCH_CLUSTERS'
    assert np.isnan(res['ci_lower'])
    assert np.isnan(res['ci_upper'])
    assert np.isnan(res['uncertainty_width'])
    assert res['sample_matches'] == 2
    assert res['sample_deliveries'] == 2


def test_zero_deliveries_produces_no_data_status():
    """Verify that players with 0 high-pressure deliveries receive NOT_ESTIMATED_NO_VALID_PRESSURE_DATA."""
    df = pd.DataFrame([
        {'match_id': 1, 'striker_id': 99, 'is_ball_faced': True, 'is_batting_high_pressure': False, 'batter_runs': 4}
    ])
    res = V3ReliabilityEngine.match_clustered_bootstrap_batting(df, player_id=99)
    assert res['ci_status'] == 'NOT_ESTIMATED_NO_VALID_PRESSURE_DATA'
    assert np.isnan(res['ci_lower'])
    assert np.isnan(res['ci_upper'])


def test_bootstrap_reproducibility_with_fixed_seed():
    """Verify match-clustered bootstrap produces identical results with fixed random seed."""
    records = []
    for m in range(1, 8):
        for b in range(10):
            runs = 4 if (m % 2 != 0 and b % 2 == 0) else 0
            records.append({
                'match_id': m,
                'striker_id': 55,
                'is_ball_faced': True,
                'is_batting_high_pressure': True,
                'batter_runs': runs
            })
    df = pd.DataFrame(records)

    run1 = V3ReliabilityEngine.match_clustered_bootstrap_batting(df, player_id=55, n_bootstraps=500, random_state=42)
    run2 = V3ReliabilityEngine.match_clustered_bootstrap_batting(df, player_id=55, n_bootstraps=500, random_state=42)

    assert run1['ci_status'] == 'ESTIMATED_MATCH_CLUSTER_BOOTSTRAP'
    assert run1['ci_lower'] == run2['ci_lower']
    assert run1['ci_upper'] == run2['ci_upper']
    assert run1['uncertainty_width'] == run2['uncertainty_width']
    assert run1['ci_lower'] <= run1['point_estimate'] <= run1['ci_upper']


def test_bowling_bootstrap_insufficient_matches():
    """Verify bowler bootstrap returns unestimated when <3 matches."""
    records = [
        {'match_id': 1, 'bowler_id': 88, 'is_legal_ball': True, 'is_bowling_high_pressure': True, 'is_dot_ball': True, 'runs': 0},
        {'match_id': 2, 'bowler_id': 88, 'is_legal_ball': True, 'is_bowling_high_pressure': True, 'is_dot_ball': False, 'runs': 1},
    ]
    df = pd.DataFrame(records)

    res = V3ReliabilityEngine.match_clustered_bootstrap_bowling(df, bowler_id=88, min_matches=3)

    assert res['ci_status'] == 'NOT_ESTIMATED_INSUFFICIENT_MATCH_CLUSTERS'
    assert np.isnan(res['ci_lower'])
    assert np.isnan(res['ci_upper'])
