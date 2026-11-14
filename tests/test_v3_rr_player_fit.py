"""Tests for V3 RR Squad Analysis and Player-Fit Engine."""
import pytest
import pandas as pd
import numpy as np

from src.scouting_engine.v3_rr_squad_analysis import V3RRSquadAnalyzer
from src.scouting_engine.v3_rr_player_fit import V3RRPlayerFitEngine


def test_rr_squad_phase_audit():
    """Verify phase coverage aggregation logic."""
    df = pd.DataFrame([
        {'pp_legal_balls': 60, 'pp_wickets': 3, 'middle_legal_balls': 90, 'middle_wickets': 4, 'death_legal_balls': 30, 'death_wickets': 2},
        {'pp_legal_balls': 60, 'pp_wickets': 2, 'middle_legal_balls': 90, 'middle_wickets': 3, 'death_legal_balls': 30, 'death_wickets': 1},
    ])
    audit = V3RRSquadAnalyzer.audit_phase_coverage(df)
    assert audit['powerplay']['legal_balls'] == 120
    assert audit['powerplay']['wickets'] == 5
    assert audit['middle']['legal_balls'] == 180
    assert audit['death']['legal_balls'] == 60


def test_watchlist_candidates_structure_and_categories():
    """Verify all 13 watchlist candidates are evaluated with valid recommendation categories."""
    fit_df = V3RRPlayerFitEngine.generate_player_fit_dataset()

    assert len(fit_df) == 13
    assert set(fit_df['recommendation_category'].unique()).issubset({
        'Strong Fit', 'Conditional Fit', 'Low Priority', 'Not Suitable for Current RR Needs', 'Insufficient Evidence'
    })

    # Verify key targets exist
    names = set(fit_df['player_name'])
    assert 'Matheesha Pathirana' in names
    assert 'Prasidh Krishna' in names
    assert 'Avesh Khan' in names
    assert 'R Sai Kishore' in names
    assert 'Ashutosh Sharma' in names
