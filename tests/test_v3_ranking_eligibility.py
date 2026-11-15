"""Tests for V3 Sample Eligibility and Threshold Governance."""
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

OUTPUTS_V3 = Path("data/outputs/v3")


def test_threshold_sensitivity_matrix_exists_and_valid():
    """Verify threshold sensitivity study exists and covers both disciplines."""
    thresh_path = OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv"
    assert thresh_path.exists(), "Threshold sensitivity CSV must exist"

    df = pd.read_csv(thresh_path)
    assert len(df) > 0
    assert set(df['discipline'].unique()) == {'Batting', 'Bowling'}
    assert 'eligible_players' in df.columns
    assert 'top10_overlap_with_baseline' in df.columns
    assert 'median_ci_width' in df.columns
    assert 'unestimated_ci_count' in df.columns


def test_player_eligibility_tracking_and_exclusion_reasons():
    """Verify PLAYER_ELIGIBILITY tracks reasons and handles low samples."""
    elig_path = OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv"
    assert elig_path.exists(), "PLAYER_ELIGIBILITY.csv must exist"

    df = pd.read_csv(elig_path)
    assert 'exclusion_reasons' in df.columns
    assert 'final_eligibility' in df.columns

    # Ineligible players must have an explicit reason
    inelig = df[df['final_eligibility'] == 'INELIGIBLE']
    assert (inelig['exclusion_reasons'] != 'NONE').all()

    # Eligible players must have no failure reasons
    elig = df[df['final_eligibility'] == 'ELIGIBLE']
    assert (elig['exclusion_reasons'] == 'NONE').all()


def test_no_player_eligible_for_both_leaderboards():
    """Verify that role classification prevents any player from entering both leaderboards."""
    roles_path = OUTPUTS_V3 / "player_roles.csv"
    assert roles_path.exists()
    roles = pd.read_csv(roles_path)

    both = roles[roles['eligible_for_bat_leaderboard'] & roles['eligible_for_bowl_leaderboard']]
    assert len(both) == 0, f"Found {len(both)} players eligible for both leaderboards!"


def test_low_sample_players_cannot_enter_final_top10():
    """Verify V4 minimum sample, normal-baseline, and Tier-1 exposure gates on Top 10."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")

    assert (top_bat['eff_crisis_balls'] >= 60).all()
    assert (top_bat['crisis_matches'] >= 6).all()
    assert (top_bat['eff_norm_balls'] >= 60).all()
    assert (top_bat['tier1_share'] >= 0.60).all()
    assert (top_bat['sample_eligible'] == True).all()

    assert (top_bowl['eff_crisis_balls'] >= 120).all()
    assert (top_bowl['crisis_matches'] >= 6).all()
    assert (top_bowl['eff_norm_balls'] >= 100).all()
    assert (top_bowl['tier1_share'] >= 0.60).all()
    assert (top_bowl['norm_baseline_eligible'] == True).all()
    assert (top_bowl['sample_eligible'] == True).all()


def test_bowler_normal_baseline_strict_and_invariant_weights():
    """Verify V4 strict normal baseline (<100 Tier-weighted balls excluded), raw/capped ratios, and invariant weights."""
    all_bowl = pd.read_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv")

    eff_nb = all_bowl['eff_norm_balls']
    insuff = all_bowl[(eff_nb < 100) | (all_bowl['norm_balls'] == 0) | (all_bowl['norm_dot_pct'].fillna(0) <= 0)]
    suff = all_bowl[(eff_nb >= 100) & (all_bowl['norm_balls'] > 0) & (all_bowl['norm_dot_pct'].fillna(0) > 0)]

    assert len(insuff) > 0
    assert (insuff['norm_baseline_eligible'] == False).all()
    assert insuff['provisional_fixed_weight_score'].isna().all()
    assert insuff['capped_dot_maintenance'].isna().all()
    assert insuff['dot_maintenance'].isna().all()

    assert len(suff) > 0
    assert (suff['norm_baseline_eligible'] == True).all()
    assert (suff['norm_baseline_status'] == 'VALID_NORMAL_BASELINE').all()
    assert np.allclose(all_bowl['effective_w_maint'].values, 0.30, atol=1e-4)
    assert np.allclose(all_bowl['effective_w_abs'].values, 0.35, atol=1e-4)
    assert np.allclose(all_bowl['effective_w_cons'].values, 0.25, atol=1e-4)
    valid_suff = suff[suff['raw_dot_maintenance'].notna()]
    expected_capped = np.clip(valid_suff['raw_dot_maintenance'], 0.5, 1.5).round(3)
    assert (valid_suff['capped_dot_maintenance'].round(3) == expected_capped).all()
    expected_flag = (valid_suff['raw_dot_maintenance'] > 1.5) | (valid_suff['raw_dot_maintenance'] < 0.5)
    assert (valid_suff['is_maintenance_capped'] == expected_flag).all()


def test_extended_threshold_sensitivity_grid_and_no_forced_top10():
    """Verify crisis-ball threshold grid includes 40..750 and does not force Top 10 when <10 eligible."""
    thresh = pd.read_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv")
    req_grid = {40, 60, 80, 100, 150, 200, 250, 500, 750}

    bat_grid = set(thresh[thresh['discipline'] == 'Batting']['min_crisis_balls'].unique())
    bowl_grid = set(thresh[thresh['discipline'] == 'Bowling']['min_crisis_balls'].unique())
    assert req_grid.issubset(bat_grid)
    assert req_grid.issubset(bowl_grid)

    for col in [
        'eligible_batter_count', 'eligible_bowler_count', 'available_top10_count',
        'top10_overlap_with_baseline', 'jaccard_similarity', 'mean_abs_rank_movement',
        'max_rank_movement', 'players_entering_top10', 'players_leaving_top10'
    ]:
        assert col in thresh.columns

    sub10 = thresh[thresh['eligible_players'] < 10]
    assert len(sub10) > 0
    assert (sub10['available_top10_count'] == sub10['eligible_players']).all()
