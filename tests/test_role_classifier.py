"""Unit tests for player role classification and dual leaderboard separation."""
import pytest
import pandas as pd
import numpy as np

from src.classification.role_classifier import build_player_name_aliases, classify_player_roles
from src.ranking_engine.pressure_rankings import (
    rank_batters_comprehensive,
    rank_bowlers_comprehensive,
    get_lower_order_pressure_batters,
    get_emerging_and_part_time_bowlers,
)


def test_build_player_name_aliases():
    """Verify that canonical aliases correctly standardize known player names."""
    map_df = pd.DataFrame([
        {'player_id': 7897, 'player_name': 'Namboori Tilak Varma'},
        {'player_id': 8, 'player_name': 'Mahendra Singh Dhoni'},
        {'player_id': 99999, 'player_name': 'Unknown Newcomer'},
    ])
    bbb_df = pd.DataFrame([
        {'striker_id': 7897, 'striker_name': 'Namboori Tilak Varma', 'bowler_id': 8, 'bowler_name': 'Mahendra Singh Dhoni'},
    ])
    aliases = build_player_name_aliases(map_df, bbb_df)
    
    tilak = aliases[aliases['player_id'] == 7897].iloc[0]
    assert tilak['canonical_display_name'] == 'Tilak Varma'
    assert tilak['verification_status'] == 'CANONICAL_STANDARDIZED'
    
    dhoni = aliases[aliases['player_id'] == 8].iloc[0]
    assert dhoni['canonical_display_name'] == 'MS Dhoni'
    
    newcomer = aliases[aliases['player_id'] == 99999].iloc[0]
    assert newcomer['canonical_display_name'] == 'Unknown Newcomer'
    assert newcomer['verification_status'] == 'DIRECT_MATCH'


def test_classify_player_roles_wk_and_bowler():
    """Verify that WKs, specialist batters, and bowlers get classified properly."""
    aliases = pd.DataFrame([
        {'player_id': 1, 'source_player_name': 'Keeper Batter', 'canonical_display_name': 'Keeper Batter', 'verification_status': 'DIRECT_MATCH'},
        {'player_id': 2, 'source_player_name': 'Spin Bowler', 'canonical_display_name': 'Spin Bowler', 'verification_status': 'DIRECT_MATCH'},
    ])
    p11 = pd.DataFrame([
        {'player_id': 1, 'is_played': 1, 'batting_order': 6, 'is_wk': True},
        {'player_id': 1, 'is_played': 1, 'batting_order': 6, 'is_wk': True},
        {'player_id': 1, 'is_played': 1, 'batting_order': 7, 'is_wk': True},
        {'player_id': 1, 'is_played': 1, 'batting_order': 7, 'is_wk': True},
        {'player_id': 1, 'is_played': 1, 'batting_order': 7, 'is_wk': True},
        {'player_id': 2, 'is_played': 1, 'batting_order': 10, 'is_wk': False},
        {'player_id': 2, 'is_played': 1, 'batting_order': 10, 'is_wk': False},
    ])
    bbb = pd.DataFrame([
        {'striker_id': 1, 'is_ball_faced': True, 'runs': 20, 'is_legal_ball': False, 'bowler_id': 99, 'pace_or_spin': None},
        {'striker_id': 2, 'is_ball_faced': True, 'runs': 2, 'is_legal_ball': True, 'bowler_id': 2, 'pace_or_spin': 'Spin'},
    ] * 100)
    
    roles = classify_player_roles(p11, bbb, aliases)
    
    wk_row = roles[roles['player_id'] == 1].iloc[0]
    assert wk_row['primary_role'] == 'WK-Batter'
    assert wk_row['is_wicketkeeper'] == True
    
    bowl_row = roles[roles['player_id'] == 2].iloc[0]
    assert 'Specialist' in bowl_row['primary_role']
    assert bowl_row['modal_batting_position'] == 10
