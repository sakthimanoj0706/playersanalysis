"""Unit tests for Rajasthan Royals scouting engine."""
import pytest
import pandas as pd
import numpy as np

from src.scouting_engine.rr_scouting import (
    scout_explosive_middle_order,
    scout_phase_bowlers,
    scout_spin_support,
    scout_batting_combinations,
)


def test_scout_explosive_middle_order():
    df = pd.DataFrame({
        'match_id': list(range(12)) * 2,
        'striker_id': [1] * 12 + [2] * 12,
        'striker_name': ['Power Batter'] * 12 + ['Anchor Batter'] * 12,
        'batting_order': [4] * 24,
        'runs': [6, 4, 6, 2, 4, 6, 4, 2, 6, 4, 6, 4] + [1, 1, 0, 1, 1, 2, 1, 1, 0, 1, 1, 2],
        'is_four': [True, True, True, False, True, True, True, False, True, True, True, True] + [False] * 12,
        'is_six': [True, False, True, False, False, True, False, False, True, False, True, False] + [False] * 12,
        'is_ball_faced': [True] * 24,
    })

    res = scout_explosive_middle_order(df, min_innings=5)
    assert len(res) == 2
    assert res.iloc[0]['player_name'] == 'Power Batter'
    assert res.iloc[0]['suitability'] > res.iloc[1]['suitability']


def test_scout_phase_bowlers():
    df = pd.DataFrame({
        'match_id': list(range(10)) * 2,
        'bowler_id': [10] * 10 + [20] * 10,
        'bowler_name': ['Death Specialist'] * 10 + ['Expensive Bowler'] * 10,
        'innings_phase': ['death'] * 20,
        'is_legal_ball': [True] * 20,
        'is_bowler_wicket': [True, False, True, False, True, False, True, False, False, True] + [False] * 10,
        'dot_ball': [True, True, True, False, True, True, False, True, True, True] + [False, True, False, False, False, False, True, False, False, False],
        'runs': [0, 0, 0, 4, 0, 0, 6, 0, 0, 0] + [4, 0, 4, 6, 4, 2, 0, 4, 6, 4],
        'extras_category': ['None'] * 20,
        'pace_or_spin': ['Pace'] * 20,
    })

    res = scout_phase_bowlers(df, phase='death', min_balls=5)
    assert len(res) == 2
    assert res.iloc[0]['player_name'] == 'Death Specialist'
    assert res.iloc[0]['suitability'] > res.iloc[1]['suitability']
