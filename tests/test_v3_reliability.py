"""Tests for V3 Reliability and Match-Clustered Bootstrap Engine."""
import pytest
import pandas as pd
import numpy as np

from src.reliability.v3_reliability import V3ReliabilityEngine


def test_match_clustered_bootstrap_batting():
    """Verify match-clustered bootstrap preserves cluster structure and outputs finite bounds."""
    records = []
    for m in range(1, 10):
        # 10 balls per match, batter 101 strikes well in odd matches, poorly in even matches
        for b in range(10):
            runs = 4 if (m % 2 != 0 and b % 2 == 0) else 0
            records.append({
                'match_id': m,
                'striker_id': 101,
                'is_ball_faced': True,
                'is_batting_high_pressure': True,
                'batter_runs': runs
            })
    df = pd.DataFrame(records)

    boot = V3ReliabilityEngine.match_clustered_bootstrap_batting(df, player_id=101, n_bootstraps=100)

    assert boot['ci_lower'] <= boot['point_estimate'] <= boot['ci_upper']
    assert boot['uncertainty_width'] > 0
    assert boot['sample_matches'] == 9
    assert boot['sample_deliveries'] == 90


def test_empirical_bayes_shrinkage():
    """Verify Normal-Normal and Beta-Binomial shrinkage pull small samples towards prior."""
    vals = pd.Series([200.0, 140.0, 80.0])
    ns = pd.Series([10.0, 100.0, 500.0])

    shrunk = V3ReliabilityEngine.empirical_bayes_normal_shrinkage(vals, ns, k_prior=25.0)

    # Small sample (10 balls with 200 SR) should be shrunk substantially towards mean (140)
    assert shrunk.iloc[0] < 200.0
    # Large sample (500 balls with 80 SR) should stay close to 80
    assert abs(shrunk.iloc[2] - 80.0) < 5.0


def test_cohort_calibrated_did_does_not_penalize_elite_baseline():
    """Verify cohort-calibrated DiD avoids penalizing elite normal-overs performers and supports prior-anchored specialists."""
    # Simulate 20 players where normal excess ranges 0..16 and crisis excess scales ~0.45x
    n_players = 20
    norm_ex = pd.Series(np.linspace(0.0, 16.0, n_players))
    crisis_ex = pd.Series(0.45 * norm_ex + 0.5)
    norm_b = pd.Series([200.0] * n_players)
    crisis_b = pd.Series([300.0] * n_players)

    _, _, did_cal = V3ReliabilityEngine.phase_adjusted_dual_arm_did(
        crisis_ex, crisis_b, norm_ex, norm_b,
        k_crisis=25.0, k_norm=25.0, cohort_calibrated=True
    )
    # Elite normal performer (last row: norm_ex=16, crisis_ex=7.7) should stay positive under cohort calibration
    assert did_cal.iloc[-1] > 0.0

    # Prior-anchored specialist with 0 normal balls should get shrunk_norm=0.0 and finite did
    sc, sn, did_spec = V3ReliabilityEngine.phase_adjusted_dual_arm_did(
        pd.Series([5.0]), pd.Series([200.0]),
        pd.Series([np.nan]), pd.Series([0.0]),
        cohort_calibrated=False, allow_prior_anchored=True
    )
    assert sn.iloc[0] == 0.0
    assert np.isfinite(did_spec.iloc[0])
