"""Unit tests for match context engine."""
import pytest
import pandas as pd
import numpy as np

from src.context_engine.innings_context import build_innings_context
from src.context_engine.delivery_context import build_delivery_context
from src.context_engine.partnership_tracker import build_partnerships


def test_innings_context_wickets_and_balls_faced():
    # 5 balls in an innings: 2 batters, 1 wicket on ball 3
    df = pd.DataFrame({
        'match_id': [1, 1, 1, 1, 1],
        'innings': [1, 1, 1, 1, 1],
        'innings_ball_num': [1, 2, 3, 4, 5],
        'overid': [1, 1, 1, 1, 1],
        'striker_id': [101, 101, 101, 102, 102],
        'runs': [1, 0, 0, 4, 2],
        'is_wicket': [False, False, True, False, False],
        'is_ball_faced': [True, True, True, True, True],
        'is_legal_ball': [True, True, True, True, True],
    })

    res = build_innings_context(df)

    # Wickets fallen before each delivery
    assert res['wickets_fallen_before'].tolist() == [0, 0, 0, 1, 1]

    # Batter 101 balls faced before each delivery: 0, 1, 2
    # Batter 102 balls faced before each delivery: 0, 1
    assert res['batter_balls_faced'].tolist() == [0, 1, 2, 0, 1]

    # Is new batter: True for ball 1 (batter 101) and ball 4 (batter 102)
    assert res['is_new_batter'].tolist() == [True, False, False, True, False]

    # Batter entry wickets: 0 for 101, 1 for 102
    assert res['batter_entry_wickets'].tolist() == [0, 0, 0, 1, 1]


def test_delivery_context_dots_and_boundaries():
    df = pd.DataFrame({
        'match_id': [1, 1, 1, 1],
        'innings': [1, 1, 1, 1],
        'innings_ball_num': [1, 2, 3, 4],
        'striker_id': [10, 10, 10, 10],
        'runs': [0, 0, 4, 6],
        'is_four': [False, False, True, False],
        'is_six': [False, False, False, True],
        'extras_category': ['None', 'None', 'None', 'None'],
        'is_ball_faced': [True, True, True, True],
    })

    res = build_delivery_context(df)
    assert res['dot_ball'].tolist() == [True, True, False, False]
    assert res['boundary'].tolist() == [False, False, True, True]
    assert res['is_dot_after_dot'].tolist() == [False, True, False, False]
    assert res['consecutive_dots'].tolist() == [0, 1, 2, 0]


def test_partnership_tracker():
    df = pd.DataFrame({
        'match_id': [1, 1, 1, 1],
        'innings': [1, 1, 1, 1],
        'innings_ball_num': [1, 2, 3, 4],
        'striker_id': [1, 2, 1, 3],
        'non_striker_id': [2, 1, 2, 2],
        'runs': [1, 2, 4, 1],
        'is_ball_faced': [True, True, True, True],
    })

    res = build_partnerships(df)
    # Balls 1, 2, 3 belong to partnership {1, 2} -> id 1
    # Ball 4 has pair {3, 2} -> id 2
    assert res['partnership_id'].tolist() == [1, 1, 1, 2]
    # Runs before: 0, 1, 3, 0 (resets for new partnership)
    assert res['partnership_runs'].tolist() == [0, 1, 3, 0]
