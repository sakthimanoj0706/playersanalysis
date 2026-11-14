"""Tests for V3 Discrete-Time Wicket Hazard Model."""
import pytest
import pandas as pd
import numpy as np

from src.models.v3_wicket_hazard import V3WicketHazardModel


def test_wicket_hazard_evaluation():
    """Verify wicket hazard estimation produces valid probabilities and calibration metrics."""
    records = []
    for m in range(1, 15):
        for b in range(50):
            # Phase-dependent wicket probability
            phase = 'powerplay' if b < 15 else ('middle' if b < 35 else 'death')
            wkt_prob = 0.04 if phase == 'powerplay' else (0.03 if phase == 'middle' else 0.08)
            is_wkt = bool(np.random.random() < wkt_prob)
            records.append({
                'match_id': m,
                'match_date': f'2025-0{1 + (m % 5)}-10',
                'is_legal_ball': True,
                'innings_phase': phase,
                'match_format': 'T20',
                'wickets_fallen_before': b // 8,
                'batting_crisis_score': float(b % 7),
                'is_bowler_wicket': is_wkt
            })
    df = pd.DataFrame(records)

    hazard = V3WicketHazardModel(c_reg=1.0)
    metrics = hazard.fit_and_evaluate(df)

    assert 'AUC' in metrics and metrics['AUC'] >= 0.50
    assert 'Brier_Score' in metrics and metrics['Brier_Score'] < 0.50
    assert 'Log_Loss' in metrics
    assert 'Expected_Wickets' in metrics
    assert 'Actual_Wickets' in metrics
