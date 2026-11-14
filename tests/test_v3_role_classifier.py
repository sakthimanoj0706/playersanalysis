"""Tests for V3 Five-State Role Classifier."""
import pytest
import pandas as pd
import numpy as np

from src.classification.v3_role_classifier import V3RoleClassifier


@pytest.fixture
def sample_classification_data():
    """Create synthetic player data across diverse tactical profiles."""
    p11_records = []
    # Player 101: Pure top order batter (pos 1-2, 20 matches, never bowls)
    for m in range(1, 21):
        p11_records.append({'match_id': m, 'team_id': 1, 'player_id': 101, 'batting_order': 1, 'is_played': True, 'is_wk': False})
    
    # Player 102: Pure specialist fast bowler (pos 10-11, 20 matches, never bats top 7)
    for m in range(1, 21):
        p11_records.append({'match_id': m, 'team_id': 1, 'player_id': 102, 'batting_order': 10, 'is_played': True, 'is_wk': False})

    # Player 103: Batting All-Rounder (pos 4, 20 matches, bats and bowls substantial overs)
    for m in range(1, 21):
        p11_records.append({'match_id': m, 'team_id': 1, 'player_id': 103, 'batting_order': 4, 'is_played': True, 'is_wk': False})

    # Player 104: Bowling All-Rounder (pos 8, 20 matches, frontline bowling + lower-order runs)
    for m in range(1, 21):
        p11_records.append({'match_id': m, 'team_id': 1, 'player_id': 104, 'batting_order': 8, 'is_played': True, 'is_wk': False})

    # Player 105: Low sample / emerging candidate (1 match, 5 balls)
    p11_records.append({'match_id': 1, 'team_id': 1, 'player_id': 105, 'batting_order': 6, 'is_played': True, 'is_wk': False})

    # Player 106: Specialist Wicketkeeper (pos 3, is_wk=True)
    for m in range(1, 21):
        p11_records.append({'match_id': m, 'team_id': 1, 'player_id': 106, 'batting_order': 3, 'is_played': True, 'is_wk': True})

    p11_df = pd.DataFrame(p11_records)

    # Deliveries
    bbb_records = []
    # 101 bats 300 balls, bowls 0
    for i in range(300):
        bbb_records.append({'match_id': (i % 20) + 1, 'innings': 1, 'striker_id': 101, 'bowler_id': 999, 'runs': 1, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': False})

    # 102 bowls 300 balls, bats 10 balls
    for i in range(300):
        bbb_records.append({'match_id': (i % 20) + 1, 'innings': 1, 'striker_id': 999, 'bowler_id': 102, 'runs': 0, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': (i % 20 == 0), 'is_bowler_wicket': (i % 20 == 0)})
    for i in range(10):
        bbb_records.append({'match_id': i + 1, 'innings': 1, 'striker_id': 102, 'bowler_id': 999, 'runs': 0, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': False})

    # 103 bats 250 balls, bowls 200 balls
    for i in range(250):
        bbb_records.append({'match_id': (i % 20) + 1, 'innings': 1, 'striker_id': 103, 'bowler_id': 999, 'runs': 1, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': False})
    for i in range(200):
        bbb_records.append({'match_id': (i % 20) + 1, 'innings': 1, 'striker_id': 999, 'bowler_id': 103, 'runs': 1, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': (i % 25 == 0), 'is_bowler_wicket': (i % 25 == 0)})

    # 104 bowls 300 balls, bats 120 balls
    for i in range(120):
        bbb_records.append({'match_id': (i % 20) + 1, 'innings': 1, 'striker_id': 104, 'bowler_id': 999, 'runs': 1, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': False})
    for i in range(300):
        bbb_records.append({'match_id': (i % 20) + 1, 'innings': 1, 'striker_id': 999, 'bowler_id': 104, 'runs': 0, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': (i % 20 == 0), 'is_bowler_wicket': (i % 20 == 0)})

    # 105 bats 5 balls, bowls 0
    for i in range(5):
        bbb_records.append({'match_id': 1, 'innings': 1, 'striker_id': 105, 'bowler_id': 999, 'runs': 0, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': False})

    # 106 WK bats 250 balls
    for i in range(250):
        bbb_records.append({'match_id': (i % 20) + 1, 'innings': 1, 'striker_id': 106, 'bowler_id': 999, 'runs': 1, 'is_ball_faced': True, 'is_legal_ball': True, 'is_wicket': False})

    bbb_df = pd.DataFrame(bbb_records)
    return p11_df, bbb_df


def test_five_mutually_exclusive_states(sample_classification_data):
    p11_df, bbb_df = sample_classification_data
    result = V3RoleClassifier.classify_roster(p11_df, bbb_df)

    assert len(result) >= 6
    assert set(result['v3_role'].unique()).issubset(V3RoleClassifier.VALID_ROLES)

    # Check player 101: BAT_SPECIALIST
    r101 = result[result['player_id'] == 101].iloc[0]
    assert r101['v3_role'] == 'BAT_SPECIALIST'
    assert r101['eligible_for_bat_leaderboard'] == True
    assert r101['eligible_for_bowl_leaderboard'] == False

    # Check player 102: BOWL_SPECIALIST
    r102 = result[result['player_id'] == 102].iloc[0]
    assert r102['v3_role'] == 'BOWL_SPECIALIST'
    assert r102['eligible_for_bat_leaderboard'] == False
    assert r102['eligible_for_bowl_leaderboard'] == True

    # Check player 103: BAT_PRIMARY_AR
    r103 = result[result['player_id'] == 103].iloc[0]
    assert r103['v3_role'] == 'BAT_PRIMARY_AR'
    assert r103['eligible_for_bat_leaderboard'] == True
    assert r103['eligible_for_bowl_leaderboard'] == False

    # Check player 104: BOWL_PRIMARY_AR
    r104 = result[result['player_id'] == 104].iloc[0]
    assert r104['v3_role'] == 'BOWL_PRIMARY_AR'
    assert r104['eligible_for_bat_leaderboard'] == False
    assert r104['eligible_for_bowl_leaderboard'] == True

    # Check player 105: UNRESOLVED
    r105 = result[result['player_id'] == 105].iloc[0]
    assert r105['v3_role'] == 'UNRESOLVED'
    assert r105['eligible_for_bat_leaderboard'] == False
    assert r105['eligible_for_bowl_leaderboard'] == False

    # Check player 106: WK -> BAT_SPECIALIST
    r106 = result[result['player_id'] == 106].iloc[0]
    assert r106['v3_role'] == 'BAT_SPECIALIST'
    assert r106['is_wicketkeeper'] == True


def test_no_player_in_both_leaderboard_gates(sample_classification_data):
    p11_df, bbb_df = sample_classification_data
    result = V3RoleClassifier.classify_roster(p11_df, bbb_df)

    # Fundamental safety guarantee: no player can be eligible for both leaderboards!
    both_eligible = result[result['eligible_for_bat_leaderboard'] & result['eligible_for_bowl_leaderboard']]
    assert len(both_eligible) == 0, "No player may be eligible for both batter and bowler leaderboards!"
