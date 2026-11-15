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
    """Verify that players with <60 crisis balls cannot enter Top 10 Batters, and <120 crisis balls cannot enter Top 10 Bowlers."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")

    assert (top_bat['crisis_balls'] >= 60).all()
    assert (top_bat['crisis_matches'] >= 5).all()
    assert (top_bat['norm_balls'] >= 60).all()
    assert (top_bat['sample_eligible'] == True).all()

    assert (top_bowl['crisis_balls'] >= 120).all()
    assert (top_bowl['crisis_matches'] >= 5).all()
    assert (top_bowl['norm_baseline_eligible'] == True).all()
    assert (top_bowl['sample_eligible'] == True).all()


def test_bowler_normal_baseline_prior_anchored_and_raw_vs_capped_maintenance():
    """Verify PRIOR_ANCHORED_SPECIALIST (<100 norm balls) vs VALID_NORMAL_BASELINE (>=100), and separate raw/capped ratios."""
    all_bowl = pd.read_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv")

    insuff = all_bowl[all_bowl['norm_balls'] < 100]
    suff = all_bowl[all_bowl['norm_balls'] >= 100]

    assert len(insuff) > 0
    assert (insuff['norm_baseline_eligible'] == True).all()
    assert (insuff['norm_baseline_status'] == 'PRIOR_ANCHORED_SPECIALIST').all()
    assert insuff['capped_dot_maintenance'].isna().all()
    assert insuff['dot_maintenance'].isna().all()
    assert (insuff['effective_w_maint'] < 0.35).all()

    assert (suff['norm_baseline_eligible'] == True).all()
    assert (suff['norm_baseline_status'] == 'VALID_NORMAL_BASELINE').all()
    assert (suff['effective_w_maint'] == 0.35).all()
    valid_suff = suff[suff['raw_dot_maintenance'].notna()]
    expected_capped = np.clip(valid_suff['raw_dot_maintenance'], 0.5, 1.5).round(3)
    assert (valid_suff['capped_dot_maintenance'].round(3) == expected_capped).all()
    expected_flag = (valid_suff['raw_dot_maintenance'] > 1.5) | (valid_suff['raw_dot_maintenance'] < 0.5)
    assert (valid_suff['is_maintenance_capped'] == expected_flag).all()


def test_extended_threshold_sensitivity_grid_and_no_forced_top10():
    """Verify crisis-ball threshold grid includes 40, 60, 80, 100, 150, 200, 250 and does not force Top 10 when <10 eligible."""
    thresh = pd.read_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv")
    req_grid = {40, 60, 80, 100, 150, 200, 250}

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
