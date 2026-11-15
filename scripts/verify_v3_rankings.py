"""Independent Verification Script for V3 Universal Player Rankings (P1.1 Patch).

Independently recalculates component normalization, PRI formulas, eligibility filtering,
bowler normal-baseline sufficiency (MIN_NORMAL_BALLS = 100), raw vs capped maintenance,
extended threshold sensitivity (40..250), and downstream copy synchronization directly
against the authoritative V3 CSVs.
"""
import hashlib
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_V3 = ROOT / "data" / "outputs" / "v3"
OUTPUTS_ROOT = ROOT / "data" / "outputs"

PRI_WEIGHTS = {
    'maintenance': 0.35,
    'absolute': 0.35,
    'consistency': 0.20,
    'sample': 0.10
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_rankings():
    print("=" * 75)
    print("INDEPENDENT AUDIT & VERIFICATION OF V3 UNIVERSAL RANKINGS (P1.1 PATCH)")
    print("=" * 75)

    # 1. Load Authoritative Files
    top10_bat = pd.read_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv")
    top10_bowl = pd.read_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv")
    all_bat = pd.read_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv")
    all_bowl = pd.read_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv")
    elig = pd.read_csv(OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv")
    thresh = pd.read_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv")
    weights = pd.read_csv(OUTPUTS_V3 / "RANKING_WEIGHT_SENSITIVITY.csv")

    print(f"Loaded ALL_BATTER_METRICS ({len(all_bat)} rows), ALL_BOWLER_METRICS ({len(all_bowl)} rows)")
    print(f"Loaded TOP_10_BATTERS ({len(top10_bat)} rows), TOP_10_BOWLERS ({len(top10_bowl)} rows)")

    # ══════════════════════════════════════════════════════════════════════════
    # 2. INDEPENDENT RE-CALCULATION: BATTERS
    # ══════════════════════════════════════════════════════════════════════════
    print("\n[1/6] Verifying Batting Calculations & Transparency Flags...")
    el_bat = all_bat[all_bat['sample_eligible'] & all_bat['eligible_for_bat_leaderboard']].copy()

    def _minmax(s, ref):
        lo, hi = ref.dropna().min(), ref.dropna().max()
        return np.clip((s - lo) / (hi - lo), 0.0, 1.0).fillna(0.0)

    indep_norm_maint = _minmax(all_bat['sr_maintenance'], el_bat['sr_maintenance'])
    indep_norm_abs = _minmax(all_bat['shrunk_crisis_sr'], el_bat['shrunk_crisis_sr'])
    indep_norm_cons = _minmax(all_bat['consistency_score'], el_bat['consistency_score'])
    indep_norm_sample = all_bat['sample_confidence']

    indep_score = (
        (PRI_WEIGHTS['maintenance'] * indep_norm_maint * 100.0).round(2) +
        (PRI_WEIGHTS['absolute'] * indep_norm_abs * 100.0).round(2) +
        (PRI_WEIGHTS['consistency'] * indep_norm_cons * 100.0).round(2) +
        (PRI_WEIGHTS['sample'] * indep_norm_sample * 100.0).round(2)
    ).round(2)
    indep_score = np.where(all_bat['norm_baseline_eligible'], indep_score, np.nan)

    valid_bat_scores = all_bat['norm_baseline_eligible'] == True
    score_diff = (all_bat.loc[valid_bat_scores, 'provisional_fixed_weight_score'] - indep_score[valid_bat_scores]).abs()
    max_diff_bat = score_diff.max()
    assert max_diff_bat < 0.05, f"Batting score reconciliation mismatch: max diff = {max_diff_bat}"
    assert all_bat.loc[~valid_bat_scores, 'provisional_fixed_weight_score'].isna().all(), \
        "Batters with insufficient normal baseline must have NaN composite score"
    print(f"  ✓ Batting scores independently reconciled across {valid_bat_scores.sum()} valid-baseline batters (max diff: {max_diff_bat:.4f})")

    # Verify Top-10 Batters all exceed cohort mean crisis SR & below-mean batters in ALL_BATTER_METRICS are flagged
    assert (top10_bat['crisis_sr'] > top10_bat['prior_mean']).all(), "All Top-10 batters must exceed cohort mean crisis SR"
    assert (top10_bat['crisis_sr_below_cohort_mean'] == False).all()
    assert (top10_bat['performance_anomaly_flag'] == 'NONE').all()
    below_mean_bat = all_bat[all_bat['crisis_sr'].notna() & (all_bat['crisis_sr'] < all_bat['prior_mean'])]
    assert len(below_mean_bat) > 0
    assert (below_mean_bat['crisis_sr_below_cohort_mean'] == True).all()
    assert (below_mean_bat['performance_anomaly_flag'] == 'CRISIS_SR_BELOW_COHORT_MEAN').all()
    print(f"  ✓ Top-10 batters all exceed cohort mean ({top10_bat['prior_mean'].iloc[0]:.2f} SR); {len(below_mean_bat)} below-mean batters flagged")

    # Independent Ranking
    all_bat['indep_score'] = indep_score
    indep_top_bat = all_bat[
        all_bat['sample_eligible'] & all_bat['eligible_for_bat_leaderboard'] & (~all_bat['is_quarantined'])
    ].sort_values(
        by=['indep_score', 'canonical_player_id'],
        ascending=[False, True]
    ).head(10).reset_index(drop=True)

    for i in range(10):
        actual_row = top10_bat.iloc[i]
        calc_row = indep_top_bat.iloc[i]
        assert actual_row['canonical_player_id'] == calc_row['canonical_player_id'], \
            f"Batting Rank {i+1} mismatch: expected {calc_row['canonical_player_id']}, got {actual_row['canonical_player_id']}"
        assert abs(actual_row['provisional_fixed_weight_score'] - calc_row['indep_score']) < 0.05
    print("  ✓ TOP_10_BATTERS matches independent recalculation and sorting exactly (10/10)")

    # ══════════════════════════════════════════════════════════════════════════
    # 3. INDEPENDENT RE-CALCULATION: BOWLERS & MIN_NORMAL_BALLS = 100
    # ══════════════════════════════════════════════════════════════════════════
    print("\n[2/6] Verifying Bowling Calculations & MIN_NORMAL_BALLS = 100 Gate...")
    # Verify MIN_NORMAL_BALLS = 100 enforcement
    insuff_bowl = all_bowl[all_bowl['norm_balls'] < 100]
    suff_bowl = all_bowl[all_bowl['norm_balls'] >= 100]
    assert (insuff_bowl['norm_baseline_eligible'] == False).all(), "Bowlers with <100 norm_balls must have norm_baseline_eligible=False"
    assert (insuff_bowl['norm_baseline_status'] == 'BOWLER_NORMAL_BASELINE_INSUFFICIENT').all(), \
        "Bowlers with <100 norm_balls must be flagged BOWLER_NORMAL_BASELINE_INSUFFICIENT"
    assert (insuff_bowl['sample_eligible'] == False).all(), "Bowlers with <100 norm_balls must have sample_eligible=False"
    assert insuff_bowl['capped_dot_maintenance'].isna().all(), "Bowlers with <100 norm_balls must have NaN capped_dot_maintenance"
    assert insuff_bowl['dot_maintenance'].isna().all(), "Bowlers with <100 norm_balls must have NaN dot_maintenance"
    assert insuff_bowl['provisional_fixed_weight_score'].isna().all(), \
        "Bowlers with <100 norm_balls must not receive a composite ranking score"
    assert (top10_bowl['norm_balls'] >= 100).all(), "Every Top-10 bowler must have >= 100 normal balls"

    # Verify raw vs capped separation on bowlers with >=100 normal balls
    valid_maint_b = suff_bowl[suff_bowl['raw_dot_maintenance'].notna()]
    expected_capped = np.clip(valid_maint_b['raw_dot_maintenance'], 0.5, 1.5).round(3)
    assert (valid_maint_b['capped_dot_maintenance'].round(3) == expected_capped).all()
    expected_cap_flag = (valid_maint_b['raw_dot_maintenance'] > 1.5) | (valid_maint_b['raw_dot_maintenance'] < 0.5)
    assert (valid_maint_b['is_maintenance_capped'] == expected_cap_flag).all()
    print(f"  ✓ MIN_NORMAL_BALLS=100 strictly enforced ({len(insuff_bowl)} flagged BOWLER_NORMAL_BASELINE_INSUFFICIENT, {len(suff_bowl)} sufficient)")

    el_bowl = all_bowl[all_bowl['sample_eligible'] & all_bowl['eligible_for_bowl_leaderboard']].copy()
    indep_norm_maint_b = _minmax(all_bowl['dot_maintenance'], el_bowl['dot_maintenance'])
    indep_norm_abs_b = _minmax(all_bowl['shrunk_crisis_wr'], el_bowl['shrunk_crisis_wr'])
    indep_norm_cons_b = _minmax(all_bowl['consistency_score'], el_bowl['consistency_score'])
    indep_norm_sample_b = all_bowl['sample_confidence']

    indep_score_b = (
        (PRI_WEIGHTS['maintenance'] * indep_norm_maint_b * 100.0).round(2) +
        (PRI_WEIGHTS['absolute'] * indep_norm_abs_b * 100.0).round(2) +
        (PRI_WEIGHTS['consistency'] * indep_norm_cons_b * 100.0).round(2) +
        (PRI_WEIGHTS['sample'] * indep_norm_sample_b * 100.0).round(2)
    ).round(2)
    indep_score_b = np.where(all_bowl['norm_baseline_eligible'], indep_score_b, np.nan)

    valid_bowl_scores = all_bowl['norm_baseline_eligible'] == True
    score_diff_b = (all_bowl.loc[valid_bowl_scores, 'provisional_fixed_weight_score'] - indep_score_b[valid_bowl_scores]).abs()
    max_diff_bowl = score_diff_b.max()
    assert max_diff_bowl < 0.05, f"Bowling score reconciliation mismatch: max diff = {max_diff_bowl}"
    print(f"  ✓ Bowling scores independently reconciled across {valid_bowl_scores.sum()} valid-baseline bowlers (max diff: {max_diff_bowl:.4f})")

    all_bowl['indep_score'] = indep_score_b
    indep_top_bowl = all_bowl[
        all_bowl['sample_eligible'] & all_bowl['eligible_for_bowl_leaderboard'] & (~all_bowl['is_quarantined'])
    ].sort_values(
        by=['indep_score', 'canonical_player_id'],
        ascending=[False, True]
    ).head(10).reset_index(drop=True)

    for i in range(len(top10_bowl)):
        actual_row = top10_bowl.iloc[i]
        calc_row = indep_top_bowl.iloc[i]
        assert actual_row['canonical_player_id'] == calc_row['canonical_player_id'], \
            f"Bowling Rank {i+1} mismatch: expected {calc_row['canonical_player_id']}, got {actual_row['canonical_player_id']}"
        assert abs(actual_row['provisional_fixed_weight_score'] - calc_row['indep_score']) < 0.05
    print(f"  ✓ TOP_10_BOWLERS matches independent recalculation and sorting exactly ({len(top10_bowl)}/{len(top10_bowl)})")

    # ══════════════════════════════════════════════════════════════════════════
    # 4. EXTENDED THRESHOLD SENSITIVITY VERIFICATION
    # ══════════════════════════════════════════════════════════════════════════
    print("\n[3/6] Verifying Extended Threshold Sensitivity Grid (40..250)...")
    req_cb = {40, 60, 80, 100, 150, 200, 250}
    bat_cb = set(thresh[thresh['discipline'] == 'Batting']['min_crisis_balls'].unique())
    bowl_cb = set(thresh[thresh['discipline'] == 'Bowling']['min_crisis_balls'].unique())
    assert req_cb.issubset(bat_cb), f"Missing batting crisis ball thresholds: {req_cb - bat_cb}"
    assert req_cb.issubset(bowl_cb), f"Missing bowling crisis ball thresholds: {req_cb - bowl_cb}"
    req_thresh_cols = [
        'eligible_batter_count', 'eligible_bowler_count', 'available_top10_count',
        'top10_overlap_with_baseline', 'jaccard_similarity', 'mean_abs_rank_movement',
        'max_rank_movement', 'players_entering_top10', 'players_leaving_top10'
    ]
    for col in req_thresh_cols:
        assert col in thresh.columns, f"Missing required threshold column: {col}"
    # Verify Top 10 is never forced when <10 players are eligible
    sub10 = thresh[thresh['eligible_players'] < 10]
    assert len(sub10) > 0, "Expected high-threshold combinations with <10 eligible players"
    assert (sub10['available_top10_count'] == sub10['eligible_players']).all(), \
        "available_top10_count must equal eligible_players when <10 players are eligible"
    print(f"  ✓ Extended threshold grid verified across {len(thresh)} combinations (no forced Top 10 when <10 eligible)")

    # ══════════════════════════════════════════════════════════════════════════
    # 5. CONFIDENCE INTERVAL AND IDENTITY INTEGRITY
    # ══════════════════════════════════════════════════════════════════════════
    print("\n[4/6] Verifying Uncertainty & Identity Guarantees...")
    assert (top10_bat['ci_status'] == 'ESTIMATED_MATCH_CLUSTER_BOOTSTRAP').all()
    assert (top10_bat['uncertainty_width'] > 0).all()
    assert (top10_bowl['ci_status'] == 'ESTIMATED_MATCH_CLUSTER_BOOTSTRAP').all()
    assert (top10_bowl['uncertainty_width'] > 0).all()

    top_overlap = set(top10_bat['canonical_player_id']) & set(top10_bowl['canonical_player_id'])
    assert len(top_overlap) == 0, f"Leaderboard collision: {top_overlap}"
    print("  ✓ Confidence intervals strictly estimated via match clusters; 0 fallback bounds")
    print("  ✓ Zero player overlap between Batting and Bowling Top 10 leaderboards")

    # ══════════════════════════════════════════════════════════════════════════
    # 6. ELIGIBILITY AUDIT RECONCILIATION
    # ══════════════════════════════════════════════════════════════════════════
    print("\n[5/6] Verifying Eligibility Exclusions...")
    assert len(elig) == len(all_bat) + len(all_bowl)
    inelig_count = (elig['final_eligibility'] == 'INELIGIBLE').sum()
    elig_count = (elig['final_eligibility'] == 'ELIGIBLE').sum()
    print(f"  ✓ PLAYER_ELIGIBILITY matches master population ({elig_count} eligible, {inelig_count} ineligible)")

    # ══════════════════════════════════════════════════════════════════════════
    # 7. AUTHORITATIVE SINGLE SOURCE OF TRUTH & COPY CONSISTENCY GATE
    # ══════════════════════════════════════════════════════════════════════════
    print("\n[6/6] Verifying Downstream Ranking Copies Against Canonical V3 CSVs...")
    copy_pairs = [
        (OUTPUTS_V3 / "TOP_10_BATTERS.csv", ROOT / "FINAL_TOP_10_BATTERS.csv"),
        (OUTPUTS_V3 / "TOP_10_BATTERS.csv", OUTPUTS_ROOT / "FINAL_TOP_10_BATTERS.csv"),
        (OUTPUTS_V3 / "TOP_10_BATTERS.csv", OUTPUTS_ROOT / "top_10_batters.csv"),
        (OUTPUTS_V3 / "TOP_10_BOWLERS.csv", ROOT / "FINAL_TOP_10_BOWLERS.csv"),
        (OUTPUTS_V3 / "TOP_10_BOWLERS.csv", OUTPUTS_ROOT / "FINAL_TOP_10_BOWLERS.csv"),
        (OUTPUTS_V3 / "TOP_10_BOWLERS.csv", OUTPUTS_ROOT / "top_10_bowlers.csv"),
        (OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", ROOT / "ALL_BATTER_RANKINGS.csv"),
        (OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", OUTPUTS_ROOT / "ALL_BATTER_RANKINGS.csv"),
        (OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", OUTPUTS_ROOT / "batting_pressure_rankings.csv"),
        (OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", ROOT / "ALL_BOWLER_RANKINGS.csv"),
        (OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", OUTPUTS_ROOT / "ALL_BOWLER_RANKINGS.csv"),
        (OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", OUTPUTS_ROOT / "bowling_pressure_rankings.csv"),
        (OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv", ROOT / "PLAYER_ELIGIBILITY_REPORT.csv"),
        (OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv", OUTPUTS_ROOT / "PLAYER_ELIGIBILITY_REPORT.csv"),
    ]
    for canon_path, copy_path in copy_pairs:
        assert copy_path.exists(), f"Missing synchronized ranking copy: {copy_path}"
        h_canon = _sha256(canon_path)
        h_copy = _sha256(copy_path)
        assert h_canon == h_copy, f"Ranking copy out of sync: {copy_path} ({h_copy}) != {canon_path} ({h_canon})"
    print(f"  ✓ All {len(copy_pairs)} downstream ranking copies match canonical V3 CSVs byte-for-byte (SHA-256 identical)")

    print("\n" + "=" * 75)
    print("ALL INDEPENDENT VERIFICATION GATES PASSED — P1.1 PATCH VERIFIED — PROVISIONAL MODEL")
    print("=" * 75)
    return True


if __name__ == '__main__':
    verify_rankings()
