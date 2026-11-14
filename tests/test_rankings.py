"""Unit tests for player rankings and reliability indices."""
import pytest
import pandas as pd
import numpy as np

from src.ranking_engine.pressure_rankings import (
    empirical_bayes_normal_shrink,
    empirical_bayes_beta_binomial,
    compute_batter_match_consistency,
    compute_bowler_match_consistency,
    rank_batters_comprehensive,
    rank_bowlers_comprehensive,
)


def test_empirical_bayes_normal_shrink():
    # Large sample (n=500) -> close to observed
    obs = pd.Series([190.0, 130.0, 120.0, 140.0, 150.0])
    sizes = pd.Series([500.0, 50.0, 60.0, 70.0, 80.0])
    shrunk = empirical_bayes_normal_shrink(obs, sizes, prior_k=30.0)
    
    assert abs(shrunk.iloc[0] - 190.0) < 5.0

    # Small sample (n=5) -> pulled heavily towards population mean (~146)
    sizes_small = pd.Series([5.0, 50.0, 60.0, 70.0, 80.0])
    shrunk_small = empirical_bayes_normal_shrink(obs, sizes_small, prior_k=30.0)
    assert shrunk_small.iloc[0] < 160.0


def test_empirical_bayes_beta_binomial():
    # 6 players with trials >= 10 to fit method of moments
    successes = pd.Series([30.0, 5.0, 6.0, 4.0, 7.0, 2.0])
    trials = pd.Series([300.0, 100.0, 120.0, 80.0, 110.0, 5.0]) # Player 5 has only 5 trials
    
    shrunk_rates = empirical_bayes_beta_binomial(successes, trials)
    # Player 0: 30/300 = 10%
    assert abs(shrunk_rates.iloc[0] - 10.0) < 2.0
    # Player 5: 2/5 = 40%, should be shrunk significantly towards population mean (~5-7%)
    assert shrunk_rates.iloc[5] < 20.0


def test_calculate_bowler_match_consistency_strictly_positive():
    """Verify that bowler consistency never degenerates to zero."""
    # Bowler with high match-to-match variance across 5 matches
    rows = []
    for m in range(5):
        for b in range(10):
            rows.append({
                'match_id': m,
                'bowler_id': 101,
                'is_legal_ball': True,
                'is_bowling_high_pressure': True,
                'runs': 0 if (m == 0 and b < 2) else 1,
                'is_bowler_wicket': True if (m == 0 and b < 2) else False,
                'dot_ball': True if (m % 2 == 0) else False,
            })
            
    df = pd.DataFrame(rows)
    cons_df = compute_bowler_match_consistency(df)
    assert len(cons_df) == 1
    score = cons_df.iloc[0]['consistency_score']
    # Must be strictly positive and bounded in (0, 1]
    assert score > 0.0
    assert score <= 1.0


def test_calculate_batter_match_consistency_strictly_positive():
    """Verify that batter consistency produces valid scores."""
    rows = []
    for m in range(5):
        for b in range(10):
            rows.append({
                'match_id': m,
                'striker_id': 201,
                'is_ball_faced': True,
                'is_batting_high_pressure': True,
                'runs': 2 if (m % 2 == 0) else 1,
                'dot_ball': False,
            })
            
    df = pd.DataFrame(rows)
    cons_df = compute_batter_match_consistency(df)
    assert len(cons_df) == 1
    score = cons_df.iloc[0]['consistency_score']
    assert score > 0.0
    assert score <= 1.0
