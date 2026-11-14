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
