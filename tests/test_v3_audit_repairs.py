"""Regression tests for V3 Audit and Repair validations.

Covers:
1. Canonical Player ID Crosswalk integrity.
2. Adam Milne appearance reconciliation (1 match played vs 16 squad selections).
3. Dhruv Jurel dismissal attribution and average (515 runs / 14 outs = 36.79).
4. Watchlist candidates canonical IDs and provenance schema.
"""
from pathlib import Path
import pandas as pd
import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUTS_V3 = DATA_DIR / "outputs" / "v3"


def test_player_id_crosswalk_integrity():
    """Verify RR_PLAYER_ID_CROSSWALK has 40 entries, no missing canonical IDs, and valid statuses."""
    cw_path = OUTPUTS_V3 / "RR_PLAYER_ID_CROSSWALK.csv"
    assert cw_path.exists(), "RR_PLAYER_ID_CROSSWALK.csv does not exist"
    
    df = pd.read_csv(cw_path)
    assert len(df) == 40, f"Expected 40 crosswalk records, got {len(df)}"
    assert df['canonical_player_id'].notna().all(), "Found NaN canonical player IDs in crosswalk"
    assert (df['verification_status'] == 'VERIFIED').all(), "Not all records are marked VERIFIED"
    
    # Specific known fixes
    soorya = df[df['canonical_player_id'] == 50284].iloc[0]
    assert soorya['reference_player_id'] == 281699
    
    jurel = df[df['canonical_player_id'] == 7260].iloc[0]
    assert jurel['reference_player_id'] == 7825
    
    archer = df[df['canonical_player_id'] == 3298].iloc[0]
    assert archer['reference_player_id'] == 3262
    
    prasidh = df[df['canonical_player_id'] == 4489].iloc[0]
    assert prasidh['canonical_player_name'] == 'Prasidh Krishna'


def test_rr_appearances_adam_milne():
    """Verify Adam Milne has exactly 1 match played despite 16 squad sheet selections."""
    app_path = OUTPUTS_V3 / "rr_2026_player_appearances.csv"
    assert app_path.exists(), "rr_2026_player_appearances.csv does not exist"
    
    df = pd.read_csv(app_path)
    milne = df[df['player_name'] == 'Adam Milne'].iloc[0]
    
    assert milne['matches_selected'] == 16, "Milne should be selected in 16 match squads"
    assert milne['matches_played_overall'] == 1, "Milne should only have 1 actual match appearance"
    assert milne['matches_starting_xi'] == 1
    assert milne['matches_impact_sub'] == 0
    assert milne['matches_batted'] == 1
    assert milne['matches_bowled'] == 1


def test_dhruv_jurel_batting_average_dismissal_attribution():
    """Verify Dhruv Jurel has 515 runs, 14 dismissals, and 36.79 average."""
    bat_path = OUTPUTS_V3 / "rr_2026_batting_stats.csv"
    assert bat_path.exists(), "rr_2026_batting_stats.csv does not exist"
    
    df = pd.read_csv(bat_path)
    jurel = df[df['player_name'] == 'Dhruv Jurel'].iloc[0]
    
    assert jurel['runs'] == 515, f"Expected 515 runs, got {jurel['runs']}"
    assert jurel['dismissals'] == 14, f"Expected 14 dismissals, got {jurel['dismissals']} (partner run-outs must not be counted)"
    assert jurel['not_outs'] == 2, f"Expected 2 not outs, got {jurel['not_outs']}"
    assert pytest.approx(jurel['batting_average'], 0.01) == 36.79, f"Expected average 36.79, got {jurel['batting_average']}"
    assert pytest.approx(jurel['strike_rate'], 0.01) == 154.65


def test_candidate_player_fit_canonical_ids_and_schema():
    """Verify RR_PLAYER_FIT has 13 candidates with valid canonical IDs and provenance fields."""
    fit_path = OUTPUTS_V3 / "RR_PLAYER_FIT.csv"
    assert fit_path.exists(), "RR_PLAYER_FIT.csv does not exist"
    
    df = pd.read_csv(fit_path)
    assert len(df) == 13, f"Expected 13 candidates, got {len(df)}"
    
    required_cols = [
        'canonical_player_id', 'player_name', 'target_gap', 'nationality',
        'is_overseas', 'primary_role', 'key_phase', 'relevant_phase_performance',
        'source_doc_or_url', 'source_period', 'price_estimate', 'availability_status',
        'evidence_verification_status', 'recommendation_category', 'fit_reasoning'
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in RR_PLAYER_FIT.csv"
        
    # Check that Prasidh is 4489, not 6424 (Kuldeep Sen)
    prasidh = df[df['player_name'] == 'Prasidh Krishna'].iloc[0]
    assert prasidh['canonical_player_id'] == 4489
    
    # Check Pathirana is 8661
    pathirana = df[df['player_name'] == 'Matheesha Pathirana'].iloc[0]
    assert pathirana['canonical_player_id'] == 8661
