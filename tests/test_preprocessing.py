"""Unit tests for preprocessing and cleaning logic."""
import pytest
import pandas as pd
import numpy as np

from src.config import EXTRAS_TYPE_MAP, NON_BOWLER_DISMISSALS
from src.preprocessing.cleaner import (
    classify_extras,
    identify_balls_faced,
    identify_legal_balls,
    classify_bowler_wickets,
    validate_boundaries,
    add_innings_phase,
    separate_super_overs,
)


def test_classify_extras():
    df = pd.DataFrame({'extras1_runs': [1, 2, 3, 4, 5, 6, 7, 99]})
    res = classify_extras(df)
    assert res['extras_category'].tolist() == [
        'Overstep', 'wide', 'legbyes', 'byes', 'other', 'None', 'Penalty', 'Unknown'
    ]


def test_identify_balls_faced():
    # Wides do NOT count as balls faced; Overstep (no balls) DO count as faced
    df = pd.DataFrame({'extras_category': ['None', 'wide', 'Overstep', 'legbyes']})
    res = identify_balls_faced(df)
    assert res['is_ball_faced'].tolist() == [True, False, True, True]


def test_identify_legal_balls():
    # Wides and Oversteps are NOT legal balls
    df = pd.DataFrame({'extras_category': ['None', 'wide', 'Overstep', 'legbyes']})
    res = identify_legal_balls(df)
    assert res['is_legal_ball'].tolist() == [True, False, False, True]


def test_classify_bowler_wickets():
    # Run outs, retired outs, and obstruction must NOT be credited as bowler wickets
    df = pd.DataFrame({
        'is_wicket': [True, True, True, True, True, False],
        'dismissal_type': ['Caught', 'Bowled', 'Run Out', 'Retire Out', 'Obstructing the field', 'None']
    })
    res = classify_bowler_wickets(df)
    assert res['is_bowler_wicket'].tolist() == [True, True, False, False, False, False]


def test_validate_boundaries():
    # Test reconciliation of boundary flags when runs == 4 or 6 but flags are False
    df = pd.DataFrame({
        'runs': [4, 6, 4, 6, 1, 0],
        'is_four': [False, False, True, False, False, False],
        'is_six': [False, False, False, True, False, False],
        'extras_category': ['None', 'None', 'None', 'None', 'None', 'None'],
    })
    res = validate_boundaries(df)
    assert res['is_four_validated'].tolist() == [True, False, True, False, False, False]
    assert res['is_six_validated'].tolist() == [False, True, False, True, False, False]
    assert res['boundary_validated'].tolist() == [True, True, True, True, False, False]


def test_add_innings_phase():
    df = pd.DataFrame({'overid': [1, 6, 7, 15, 16, 20, 21]})
    res = add_innings_phase(df)
    assert res['innings_phase'].tolist() == [
        'powerplay', 'powerplay', 'middle', 'middle', 'death', 'death', 'unknown'
    ]


def test_separate_super_overs():
    df = pd.DataFrame({'innings': [1, 2, 3, 4, 1]})
    reg, so = separate_super_overs(df)
    assert len(reg) == 3
    assert len(so) == 2
    assert reg['innings'].tolist() == [1, 2, 1]
    assert so['innings'].tolist() == [3, 4]
