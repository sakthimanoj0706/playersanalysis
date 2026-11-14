"""Tests for V3 Joint Batter-Bowler Hierarchical Model."""
import pytest
import pandas as pd
import numpy as np

from src.models.v3_joint_performance import V3JointPerformanceModel


def test_joint_model_execution_and_comparison():
    """Ensure all 5 model architectures execute and evaluate MAE/RMSE."""
    # Create synthetic match deliveries across 10 matches
    records = []
    for m in range(1, 11):
        for b in range(40):
            records.append({
                'match_id': m,
                'match_date': f'2025-0{1 + (m % 5)}-15',
                'striker_id': 100 + (b % 4),
                'bowler_id': 200 + (b % 4),
                'innings_phase': 'powerplay' if b < 15 else ('middle' if b < 30 else 'death'),
                'match_format': 'T20',
                'is_ball_faced': True,
                'is_legal_ball': True,
                'batter_runs': float(np.random.choice([0, 1, 2, 4, 6], p=[0.45, 0.35, 0.05, 0.10, 0.05])),
                'batting_crisis_score': float((b % 10)),
            })
    df = pd.DataFrame(records)

    model = V3JointPerformanceModel(alpha=10.0)
    results = model.fit_and_compare(df)

    assert len(results) == 5
    assert '1_Context_Only' in results
    assert '2_Batter_Only' in results
    assert '3_Bowler_Only' in results
    assert '4_Joint_Batter_Bowler' in results
    assert '5_Joint_With_Pressure' in results

    for name, metrics in results.items():
        assert 'MAE' in metrics and metrics['MAE'] > 0
        assert 'RMSE' in metrics and metrics['RMSE'] > 0
