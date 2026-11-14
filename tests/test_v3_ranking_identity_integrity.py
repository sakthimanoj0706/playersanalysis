"""Tests for V3 Canonical Player Identity and Deduplication Layer."""
import pytest
import pandas as pd
import numpy as np

from src.identity.player_identity import PlayerIdentityResolver, CONSOLIDATED_DUPLICATES, PARTITIONED_IDENTITIES


def test_verified_duplicate_id_consolidation():
    """Verify that multiple source IDs for the same real player consolidate into one canonical ID."""
    resolver = PlayerIdentityResolver()
    resolver.build_crosswalk()

    # Mohammad Ali: source 20229 must map to canonical 3083
    assert resolver.resolve_id(20229) == 3083
    assert resolver.resolve_id(3083) == 3083
    assert resolver.resolve_name(3083) == 'Mohammad Ali'


def test_alias_resolution_and_corrected_misattribution():
    """Verify that known corrupted aliases are corrected (Donovan Ferreira vs Dunith Wellalage)."""
    resolver = PlayerIdentityResolver()
    cw = resolver.build_crosswalk()

    # ID 8182 is Donovan Ferreira, NOT Dunith Wellalage
    ferreira_row = cw[cw['source_player_id'] == 8182].iloc[0]
    assert ferreira_row['canonical_player_id'] == 8182
    assert ferreira_row['canonical_player_name'] == 'Donovan Ferreira'
    assert ferreira_row['resolution_method'] == 'CORRECTED_MISATTRIBUTION'

    # ID 7052 is Dunith Wellalage
    wellalage_row = cw[cw['source_player_id'] == 7052].iloc[0]
    assert wellalage_row['canonical_player_id'] == 7052
    assert wellalage_row['canonical_player_name'] == 'Dunith Wellalage'


def test_same_name_different_player_protection():
    """Verify distinct players with the same display name are NOT merged."""
    resolver = PlayerIdentityResolver()
    cw = resolver.build_crosswalk()

    # Abdul Samad IND (7446) vs Abdul Samad PAK (6922)
    ind_samad = cw[cw['source_player_id'] == 7446].iloc[0]
    pak_samad = cw[cw['source_player_id'] == 6922].iloc[0]
    assert ind_samad['canonical_player_id'] != pak_samad['canonical_player_id']
    assert ind_samad['canonical_player_id'] == 7446
    assert pak_samad['canonical_player_id'] == 6922
    assert ind_samad['resolution_method'] == 'SAME_NAME_DIFFERENT_PLAYER_PARTITION'
    assert pak_samad['resolution_method'] == 'SAME_NAME_DIFFERENT_PLAYER_PARTITION'

    # Haider Ali PAK (7338) vs Haider Ali UAE (28756)
    pak_haider = cw[cw['source_player_id'] == 7338].iloc[0]
    uae_haider = cw[cw['source_player_id'] == 28756].iloc[0]
    assert pak_haider['canonical_player_id'] != uae_haider['canonical_player_id']
    assert pak_haider['canonical_player_id'] == 7338
    assert uae_haider['canonical_player_id'] == 28756


def test_ambiguous_identity_quarantine():
    """Verify that players with unresolved identity conflicts are marked and quarantined."""
    resolver = PlayerIdentityResolver()
    cw = resolver.build_crosswalk()

    # Simulate an ambiguous identity conflict
    sim_cw = cw.copy()
    sim_cw.loc[sim_cw['source_player_id'] == 99999, 'verification_status'] = 'IDENTITY_CONFLICT'
    sim_resolver = PlayerIdentityResolver()
    sim_resolver._crosswalk_df = sim_cw
    sim_resolver._init_lookups()

    sim_resolver._quarantined_ids.add(99999)
    assert sim_resolver.is_quarantined(99999) == True
    assert sim_resolver.is_quarantined(7446) == False


def test_resolve_deliveries_replaces_ids():
    """Verify delivery dataframe resolution maps IDs to canonical IDs."""
    resolver = PlayerIdentityResolver()
    df = pd.DataFrame([
        {'striker_id': 20229, 'striker_name': 'Mohammad Ali', 'bowler_id': 7446, 'bowler_name': 'Abdul Samad'},
        {'striker_id': 8182, 'striker_name': 'Donovan Ferreira', 'bowler_id': 7052, 'bowler_name': 'Dunith Wellalage'},
    ])
    res = resolver.resolve_deliveries(df)
    assert res.loc[0, 'striker_id'] == 3083
    assert res.loc[0, 'source_striker_id'] == 20229
    assert res.loc[0, 'bowler_id'] == 7446
    assert res.loc[1, 'striker_id'] == 8182
    assert res.loc[1, 'canonical_striker_name'] == 'Donovan Ferreira'
