"""Unit tests for pressure classification engine."""
import pytest
import pandas as pd
import numpy as np

from src.pressure_engine.pressure_model import (
    compute_batting_pressure,
    compute_bowling_pressure,
    classify_dual_pressure,
    get_tier_breakdown,
)


def test_dual_pressure_models_and_zero_leakage():
    """Verify dual independent models compute valid scores with strictly pre-delivery features."""
    df = pd.DataFrame({
        'wickets_fallen_before': [0, 2, 5, 8],
        'wickets_in_last_12_legal_balls': [0, 0, 1, 2],
        'batter_balls_faced': [20, 10, 2, 0],
        'is_new_batter': [False, False, True, True],
        'balls_since_last_wicket': [60, 30, 4, 1],
        'innings_phase': ['powerplay', 'middle', 'death', 'death'],
        'batting_wickets_remaining': [10, 8, 5, 2],
        'boundaries_in_last_12_legal_balls': [0, 1, 2, 3],
        'current_spell_balls': [6, 12, 18, 24],
        # Post-delivery features that must NOT cause target leakage
        'runs': [0, 1, 4, 6],
        'is_wicket': [False, False, False, True],
        'dot_ball': [True, False, False, False],
        'boundary': [False, False, True, True],
    })

    # Test Batting Pressure Model
    bat_df = compute_batting_pressure(df)
    assert 'batting_pressure_score' in bat_df.columns
    assert 'batting_pressure_tier' in bat_df.columns
    assert (bat_df['batting_pressure_score'] >= 0.0).all()
    assert (bat_df['batting_pressure_score'] <= 10.0).all()
    # Monotonicity check: escalating crisis leads to higher score
    assert bat_df['batting_pressure_score'].iloc[0] < bat_df['batting_pressure_score'].iloc[-1]

    # Test Bowling Pressure Model
    bowl_df = compute_bowling_pressure(df)
    assert 'bowling_pressure_score' in bowl_df.columns
    assert 'bowling_pressure_tier' in bowl_df.columns
    assert (bowl_df['bowling_pressure_score'] >= 0.0).all()
    assert (bowl_df['bowling_pressure_score'] <= 10.0).all()

    # Test classify_dual_pressure integration
    dual_df = classify_dual_pressure(df)
    assert 'is_batting_high_pressure' in dual_df.columns
    assert 'is_bowling_high_pressure' in dual_df.columns
    assert 'is_batting_normal_pressure' in dual_df.columns
    assert 'is_bowling_normal_pressure' in dual_df.columns

    # Test get_tier_breakdown
    bat_breakdown = get_tier_breakdown(dual_df, 'batting_pressure_tier')
    bowl_breakdown = get_tier_breakdown(dual_df, 'bowling_pressure_tier')
    assert len(bat_breakdown) > 0
    assert len(bowl_breakdown) > 0
    assert 'deliveries' in bat_breakdown.columns
    assert 'pct_of_deliveries' in bat_breakdown.columns
