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
    """Verify that players with <40 crisis balls cannot enter Top 10 Batters, and <120 crisis balls cannot enter Top 10 Bowlers."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")

    assert (top_bat['crisis_balls'] >= 40).all()
    assert (top_bat['crisis_matches'] >= 5).all()
    assert (top_bat['norm_balls'] >= 30).all()
    assert (top_bat['sample_eligible'] == True).all()

    assert (top_bowl['crisis_balls'] >= 120).all()
    assert (top_bowl['crisis_matches'] >= 5).all()
    assert (top_bowl['norm_balls'] >= 30).all()
    assert (top_bowl['sample_eligible'] == True).all()
