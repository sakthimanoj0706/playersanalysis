"""Tests for V3 LightGBM Challenger Model."""
import pytest
import pandas as pd
import numpy as np

from src.models.v3_lightgbm_challenger import V3LightGBMChallenger


def test_lightgbm_challenger_fit_and_evaluate():
    """Ensure LightGBM regression and classification challenger runs without error."""
    records = []
    for m in range(1, 15):
        for b in range(50):
            records.append({
                'match_id': m,
                'match_date': f'2025-0{1 + (m % 5)}-15',
                'is_ball_faced': True,
                'is_legal_ball': True,
                'innings_phase': 'powerplay' if b < 15 else ('middle' if b < 35 else 'death'),
                'match_format': 'T20',
                'wickets_fallen_before': b // 8,
                'batting_crisis_score': float(b % 8),
                'bowling_defensive_score': float((b * 2) % 10),
                'batter_runs': float(np.random.choice([0, 1, 2, 4, 6], p=[0.45, 0.35, 0.05, 0.10, 0.05])),
                'is_bowler_wicket': bool(b % 20 == 0)
            })
    df = pd.DataFrame(records)

    challenger = V3LightGBMChallenger(n_estimators=30, learning_rate=0.1)
    results = challenger.fit_and_evaluate(df)

    assert 'runs_regression' in results
    assert 'wicket_classification' in results
    assert results['runs_regression']['MAE'] > 0
    assert results['runs_regression']['RMSE'] > 0
    assert results['wicket_classification']['AUC'] >= 0.50
