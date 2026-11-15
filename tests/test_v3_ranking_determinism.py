"""Tests for V3 Ranking Determinism and Pipeline Integrity."""
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

OUTPUTS_V3 = Path("data/outputs/v3")


def test_top10_authoritative_reconciliation_with_all_metrics():
    """Verify that every row in TOP_10 matches its exact counterpart in ALL_METRICS."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    all_bat = pd.read_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv").set_index('canonical_player_id')

    assert len(top_bat) <= 10
    assert top_bat['canonical_player_id'].nunique() == len(top_bat)

    for _, r in top_bat.iterrows():
        pid = r['canonical_player_id']
        assert pid in all_bat.index
        master_row = all_bat.loc[pid]
        assert abs(r['provisional_fixed_weight_score'] - master_row['provisional_fixed_weight_score']) < 1e-4
        assert r['v3_role'] == master_row['v3_role']
        assert r['crisis_balls'] == master_row['crisis_balls']

    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    all_bowl = pd.read_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv").set_index('canonical_player_id')

    assert len(top_bowl) <= 10
    assert top_bowl['canonical_player_id'].nunique() == len(top_bowl)

    for _, r in top_bowl.iterrows():
        bid = r['canonical_player_id']
        assert bid in all_bowl.index
        master_row = all_bowl.loc[bid]
        assert abs(r['provisional_fixed_weight_score'] - master_row['provisional_fixed_weight_score']) < 1e-4
        assert r['v3_role'] == master_row['v3_role']
        assert r['crisis_balls'] == master_row['crisis_balls']


def test_no_duplicate_canonical_player_in_leaderboards():
    """Verify strictly one appearance per canonical player."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")

    assert top_bat['canonical_player_id'].is_unique
    assert top_bowl['canonical_player_id'].is_unique

    # No player in both leaderboards
    overlap = set(top_bat['canonical_player_id']) & set(top_bowl['canonical_player_id'])
    assert len(overlap) == 0, f"Player(s) {overlap} present in both Top 10 leaderboards!"


def test_deterministic_sorting():
    """Verify rankings are strictly sorted by score descending, with canonical ID ascending as tie-breaker."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    scores = top_bat['provisional_fixed_weight_score'].values
    assert (np.diff(scores) <= 0).all(), "Batting rankings are not sorted descending by score!"

    top_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    bowl_scores = top_bowl['provisional_fixed_weight_score'].values
    assert (np.diff(bowl_scores) <= 0).all(), "Bowling rankings are not sorted descending by score!"


def test_top10_batters_above_cohort_mean_and_weight_sensitivity_flags():
    """Verify all Top-10 batters exceed cohort mean crisis SR, below-mean batters in ALL_BATTER_METRICS are flagged, and weight sensitivity is tracked."""
    top_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    all_bat = pd.read_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv")

    assert (top_bat['crisis_sr'] > top_bat['prior_mean']).all()
    assert (top_bat['crisis_sr_below_cohort_mean'] == False).all()
    assert (top_bat['performance_anomaly_flag'] == 'NONE').all()

    below_mean = all_bat[all_bat['crisis_sr'].notna() & (all_bat['crisis_sr'] < all_bat['prior_mean'])]
    assert len(below_mean) > 0
    assert (below_mean['crisis_sr_below_cohort_mean'] == True).all()
    assert (below_mean['performance_anomaly_flag'] == 'CRISIS_SR_BELOW_COHORT_MEAN').all()

    # Top-5 batters are robust across weights; ranks 6-10 are flagged sensitive to weights
    robust_ranks = set(top_bat[top_bat['ranking_sensitivity_status'] == 'ROBUST_ACROSS_WEIGHTS']['rank'].astype(int))
    sens_ranks = set(top_bat[top_bat['ranking_sensitivity_status'] == 'RANKING_SENSITIVE_TO_WEIGHTS']['rank'].astype(int))
    assert {1, 2, 3, 4, 5}.issubset(robust_ranks)
    assert {6, 7, 8, 9, 10}.issubset(sens_ranks)


def test_downstream_ranking_copies_match_canonical_v3_outputs():
    """Verify all root-level and data/outputs ranking copies are byte-for-byte identical to canonical V3 CSVs."""
    import hashlib

    def _sha256(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    pairs = [
        (OUTPUTS_V3 / "TOP_10_BATTERS.csv", Path("FINAL_TOP_10_BATTERS.csv")),
        (OUTPUTS_V3 / "TOP_10_BATTERS.csv", Path("data/outputs/FINAL_TOP_10_BATTERS.csv")),
        (OUTPUTS_V3 / "TOP_10_BATTERS.csv", Path("data/outputs/top_10_batters.csv")),
        (OUTPUTS_V3 / "TOP_10_BOWLERS.csv", Path("FINAL_TOP_10_BOWLERS.csv")),
        (OUTPUTS_V3 / "TOP_10_BOWLERS.csv", Path("data/outputs/FINAL_TOP_10_BOWLERS.csv")),
        (OUTPUTS_V3 / "TOP_10_BOWLERS.csv", Path("data/outputs/top_10_bowlers.csv")),
        (OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", Path("ALL_BATTER_RANKINGS.csv")),
        (OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", Path("data/outputs/ALL_BATTER_RANKINGS.csv")),
        (OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", Path("ALL_BOWLER_RANKINGS.csv")),
        (OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", Path("data/outputs/ALL_BOWLER_RANKINGS.csv")),
    ]
    for canon, copy in pairs:
        assert copy.exists(), f"Missing copy: {copy}"
        assert _sha256(canon) == _sha256(copy), f"Copy mismatch: {copy} != {canon}"
