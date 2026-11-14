"""Tests for V3 Ranking Pressure Aggregation and Baseline Integrity."""
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

OUTPUTS_V3 = Path("data/outputs/v3")


def test_unclassified_pressure_excluded_from_metrics():
    """Verify that deliveries without valid pressure classification do not enter normal or crisis pools."""
    bat_master = pd.read_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv")
    bowl_master = pd.read_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv")

    # Sum of crisis_balls + norm_balls must be <= total_balls (moderate pressure & unclassified make up the difference)
    assert (bat_master['crisis_balls'] + bat_master['norm_balls'] <= bat_master['total_balls']).all()
    assert (bowl_master['crisis_balls'] + bowl_master['norm_balls'] <= bowl_master['total_legal_balls']).all()


def test_normal_baseline_validity_flags():
    """Verify that players without >=30 normal balls do not receive a valid normal baseline or fabricated maintenance ratio."""
    bat_master = pd.read_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv")

    no_norm = bat_master[bat_master['norm_balls'] == 0]
    if len(no_norm) > 0:
        assert (no_norm['norm_baseline_status'] == 'NO_NORMAL_EXPOSURE').all()
        assert no_norm['sr_maintenance'].isna().all()

    low_norm = bat_master[(bat_master['norm_balls'] > 0) & (bat_master['norm_balls'] < 30)]
    if len(low_norm) > 0:
        assert (low_norm['norm_baseline_status'] == 'INSUFFICIENT_NORMAL_EXPOSURE').all()
        assert low_norm['sr_maintenance'].isna().all()

    valid_norm = bat_master[bat_master['norm_balls'] >= 30]
    assert (valid_norm['norm_baseline_status'] == 'VALID_NORMAL_BASELINE').all()


def test_component_score_contributions_reconcile():
    """Verify that score contributions sum exactly to the provisional PRI score."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    bat_contrib_sum = (
        top_bat['contrib_maint'] +
        top_bat['contrib_abs'] +
        top_bat['contrib_cons'] +
        top_bat['contrib_sample']
    ).round(2)
    np.testing.assert_allclose(bat_contrib_sum.values, top_bat['provisional_fixed_weight_score'].values, atol=0.05)

    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    bowl_contrib_sum = (
        top_bowl['contrib_maint'] +
        top_bowl['contrib_abs'] +
        top_bowl['contrib_cons'] +
        top_bowl['contrib_sample']
    ).round(2)
    np.testing.assert_allclose(bowl_contrib_sum.values, top_bowl['provisional_fixed_weight_score'].values, atol=0.05)
