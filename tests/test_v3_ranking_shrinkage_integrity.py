"""Tests for V3 Prior Population Masking and Fixed-K Normal Shrinkage."""
import pytest
import pandas as pd
import numpy as np

from src.reliability.v3_reliability import V3ReliabilityEngine


def test_prior_excludes_zero_exposure_and_ineligible_records():
    """Verify that players with 0 balls faced or ineligible status do not contaminate prior mean."""
    obs = pd.Series([200.0, 150.0, 0.0, 0.0, 300.0])
    ns = pd.Series([50.0, 40.0, 0.0, 0.0, 60.0])
    eligible = pd.Series([True, True, False, False, False])

    # With eligible mask: only player 0 and 1 should enter prior
    # mean of 200 and 150 = 175.0
    shrunk, meta = V3ReliabilityEngine.fixed_k_normal_shrinkage(
        obs, ns, k_prior=25.0, eligible_mask=eligible, return_metadata=True
    )

    assert meta['prior_population_count'] == 2
    assert abs(meta['prior_mean'] - 175.0) < 1e-4
    assert meta['shrinkage_status'] == 'FIXED_K_ASSUMPTION'
    assert meta['prior_k'] == 25.0

    # Zero exposure rows must remain NaN
    assert np.isnan(shrunk.iloc[2])
    assert np.isnan(shrunk.iloc[3])


def test_mathematically_correct_shrinkage_weights():
    """Verify that larger samples receive strictly greater weight towards observed value."""
    obs = pd.Series([200.0, 200.0])
    ns = pd.Series([25.0, 75.0])  # K=25: n=25 gives weight 0.5; n=75 gives weight 0.75

    shrunk, meta = V3ReliabilityEngine.fixed_k_normal_shrinkage(
        obs, ns, k_prior=25.0, return_metadata=True
    )

    prior_mean = meta['prior_mean']  # 200.0 here since both are 200
    # Let's test with distinct observed rates
    obs2 = pd.Series([200.0, 200.0])
    ns2 = pd.Series([25.0, 75.0])
    # Force prior mean to 100
    el_mask = pd.Series([False, False])
    # Pass population where mean is known
    all_obs = pd.Series([200.0, 200.0, 100.0, 100.0])
    all_ns = pd.Series([25.0, 75.0, 50.0, 50.0])
    el = pd.Series([False, False, True, True])

    shrunk2, meta2 = V3ReliabilityEngine.fixed_k_normal_shrinkage(
        all_obs, all_ns, k_prior=25.0, eligible_mask=el, return_metadata=True
    )
    assert meta2['prior_mean'] == 100.0
    # For n=25, K=25: w = 25/50 = 0.5 -> 0.5 * 200 + 0.5 * 100 = 150.0
    assert abs(shrunk2.iloc[0] - 150.0) < 1e-2
    # For n=75, K=25: w = 75/100 = 0.75 -> 0.75 * 200 + 0.25 * 100 = 175.0
    assert abs(shrunk2.iloc[1] - 175.0) < 1e-2


def test_bowling_beta_binomial_validity_and_metadata():
    """Verify bowling Beta-Binomial shrinkage masks zero-trial records and outputs prior metadata."""
    successes = pd.Series([10.0, 5.0, 0.0, 0.0])
    trials = pd.Series([100.0, 50.0, 0.0, 20.0])

    shrunk, meta = V3ReliabilityEngine.empirical_bayes_beta_binomial_shrinkage(
        successes, trials, return_metadata=True
    )

    assert meta['shrinkage_method'] == 'BETA_BINOMIAL_EMPIRICAL_BAYES'
    assert 'prior_alpha' in meta
    assert 'prior_beta' in meta
    assert meta['prior_population_count'] >= 1
    # Zero trials must remain NaN
    assert np.isnan(shrunk.iloc[2])
    # Positive trials must produce non-null rate
    assert not np.isnan(shrunk.iloc[0])
    assert not np.isnan(shrunk.iloc[1])
    assert not np.isnan(shrunk.iloc[3])
