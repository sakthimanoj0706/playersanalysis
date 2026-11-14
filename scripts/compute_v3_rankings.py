"""Compute V3 Universal Cricket Rankings and Reliability Profiles.

Generates:
- data/outputs/v3/TOP_10_BATTERS.csv
- data/outputs/v3/TOP_10_BOWLERS.csv
- data/outputs/v3/ALL_BATTER_METRICS.csv
- data/outputs/v3/ALL_BOWLER_METRICS.csv
- data/outputs/v3/PLAYER_ELIGIBILITY.csv
"""
from pathlib import Path
import logging
import numpy as np
import pandas as pd

from src.ingestion.adapters.rr_data_adapter import RRDataAdapter
from src.pressure_engine.v3_pressure_model import V3PressureModel
from src.reliability.v3_reliability import V3ReliabilityEngine
from src.ranking_engine.pressure_rankings import PRI_WEIGHTS, SENSITIVITY_CONFIGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUTS_V3 = DATA_DIR / "outputs" / "v3"
OUTPUTS_V3.mkdir(parents=True, exist_ok=True)


def compute_v3_rankings():
    logging.info("Loading cleaned context and pressure datasets...")
    # Prefer pre-computed ball_by_ball_with_pressure.parquet if available
    press_path = DATA_DIR / "features" / "ball_by_ball_with_pressure.parquet"
    if press_path.exists():
        logging.info(f"Loading {press_path}...")
        bbb = pd.read_parquet(press_path)
    else:
        raw_bbb = pd.read_csv(DATA_DIR / "ball_by_ball_ipl_t20i.csv", dtype={'season': str})
        adapter = RRDataAdapter()
        bbb = adapter.transform_deliveries(raw_bbb)
        bbb = V3PressureModel.apply_dual_pressure(bbb)

    if 'batter_runs' not in bbb.columns and 'runs' in bbb.columns:
        bbb['batter_runs'] = bbb['runs']

    if 'is_dot_ball' not in bbb.columns:
        bbb['is_dot_ball'] = bbb['dot_ball'] if 'dot_ball' in bbb.columns else (bbb['batter_runs'] == 0)

    if 'is_bowler_wicket' not in bbb.columns and 'is_wicket' in bbb.columns:
        non_bowler = ['Run Out', 'RunOut', 'Retired Out', 'Retire Out', 'Obstructing the field', 'Obstracting the field']
        bbb['is_bowler_wicket'] = bbb['is_wicket'] & ~bbb['dismissal_type'].isin(non_bowler)

    if 'is_four_validated' not in bbb.columns:
        bbb['is_four_validated'] = bbb['is_four'] if 'is_four' in bbb.columns else (bbb['batter_runs'] == 4)

    if 'is_six_validated' not in bbb.columns:
        bbb['is_six_validated'] = bbb['is_six'] if 'is_six' in bbb.columns else (bbb['batter_runs'] == 6)

    # Load V3 Player Roles
    roles_df = pd.read_csv(OUTPUTS_V3 / "player_roles.csv")
    role_map = roles_df.set_index('player_id').to_dict('index')

    # ══════════════════════════════════════════════════════════════════════════
    # 1. BATTING RANKINGS PIPELINE
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Computing Universal Batting Intelligence...")
    faced = bbb[bbb['is_ball_faced'] == True].copy()
    
    # Tripartite breakdown
    p_high = faced[faced['is_batting_high_pressure'] == True]
    p_norm = faced[faced['is_batting_normal_pressure'] == True]

    # Aggregates
    def _agg_bat(tier_df, prefix):
        if len(tier_df) == 0:
            return pd.DataFrame(columns=['striker_id', f'{prefix}_balls', f'{prefix}_runs', f'{prefix}_sr', f'{prefix}_matches'])
        agg = tier_df.groupby('striker_id').agg(
            balls=('batter_runs', 'count'),
            runs=('batter_runs', 'sum'),
            fours=('is_four_validated', 'sum'),
            sixes=('is_six_validated', 'sum'),
            matches=('match_id', 'nunique')
        ).reset_index()
        agg[f'{prefix}_balls'] = agg['balls']
        agg[f'{prefix}_runs'] = agg['runs']
        agg[f'{prefix}_sr'] = np.where(agg['balls'] > 0, agg['runs'] / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[['striker_id', f'{prefix}_balls', f'{prefix}_runs', f'{prefix}_sr', f'{prefix}_matches']]

    df_high_bat = _agg_bat(p_high, 'crisis')
    df_norm_bat = _agg_bat(p_norm, 'norm')

    df_tot_bat = faced.groupby('striker_id').agg(
        total_balls=('batter_runs', 'count'),
        total_runs=('batter_runs', 'sum'),
        total_matches=('match_id', 'nunique')
    ).reset_index()

    bat_master = df_tot_bat.merge(df_high_bat, on='striker_id', how='left')
    bat_master = bat_master.merge(df_norm_bat, on='striker_id', how='left').fillna(0)

    # Attach V3 Roles
    bat_master['player_name'] = bat_master['striker_id'].apply(lambda pid: role_map.get(pid, {}).get('player_name', f"Player_{pid}"))
    bat_master['v3_role'] = bat_master['striker_id'].apply(lambda pid: role_map.get(pid, {}).get('v3_role', 'UNRESOLVED'))
    bat_master['role_confidence'] = bat_master['striker_id'].apply(lambda pid: role_map.get(pid, {}).get('role_confidence', 'LOW'))
    bat_master['modal_order'] = bat_master['striker_id'].apply(lambda pid: role_map.get(pid, {}).get('modal_order', 10))
    bat_master['eligible_for_bat_leaderboard'] = bat_master['striker_id'].apply(lambda pid: role_map.get(pid, {}).get('eligible_for_bat_leaderboard', False))

    # Consistency & Uncertainty Calculation
    logging.info("Computing Match Consistency & Bootstrap Confidence Intervals for Batters...")
    consistencies = []
    ci_lows = []
    ci_highs = []
    uncertainty_widths = []

    for _, row in bat_master.iterrows():
        pid = row['striker_id']
        cb = row['crisis_balls']
        cm = row['crisis_matches']

        if cb < 15 or cm < 3:
            consistencies.append(0.10)
            ci_lows.append(max(0.0, row['crisis_sr'] - 40.0))
            ci_highs.append(row['crisis_sr'] + 40.0)
            uncertainty_widths.append(80.0)
            continue

        # Match consistency
        p_p_high = p_high[p_high['striker_id'] == pid]
        m_runs = p_p_high.groupby('match_id')['batter_runs'].sum()
        m_balls = p_p_high.groupby('match_id')['batter_runs'].count()
        m_srs = (m_runs / m_balls) * 100.0

        mean_sr = m_srs.mean()
        std_sr = m_srs.std() if len(m_srs) > 1 else mean_sr * 0.5
        cv = (std_sr / mean_sr) if mean_sr > 0 else 1.5
        m_w = np.sqrt(cm / (cm + 3.0))
        c_score = np.clip(np.exp(-cv) * m_w, 0.05, 0.98)
        consistencies.append(round(float(c_score), 4))

        # Bootstrap CI (using fast 200 iterations for top pool)
        boot = V3ReliabilityEngine.match_clustered_bootstrap_batting(p_high, pid, n_bootstraps=200)
        ci_lows.append(boot['ci_lower'])
        ci_highs.append(boot['ci_upper'])
        uncertainty_widths.append(boot['uncertainty_width'])

    bat_master['consistency_score'] = consistencies
    bat_master['ci_lower'] = ci_lows
    bat_master['ci_upper'] = ci_highs
    bat_master['uncertainty_width'] = uncertainty_widths

    # Eligibility Thresholds: >= 40 crisis balls, >= 120 total balls, >= 5 crisis matches, >= 30 normal balls
    cond_cb = bat_master['crisis_balls'] >= 40
    cond_tb = bat_master['total_balls'] >= 120
    cond_cm = bat_master['crisis_matches'] >= 5
    cond_nb = bat_master['norm_balls'] >= 30
    bat_master['sample_eligible'] = cond_cb & cond_tb & cond_cm & cond_nb

    bat_master['eligibility_status'] = np.where(
        bat_master['sample_eligible'], 'ELIGIBLE',
        np.where(bat_master['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE')
    )

    # Maintenance Ratio
    norm_sr_safe = np.maximum(80.0, bat_master['norm_sr'].values)
    bat_master['sr_maintenance'] = np.clip(bat_master['crisis_sr'].values / norm_sr_safe, 0.5, 1.5).round(3)

    # Shrunk Strike Rate
    bat_master['shrunk_crisis_sr'] = V3ReliabilityEngine.empirical_bayes_normal_shrinkage(
        bat_master['crisis_sr'], bat_master['crisis_balls'], k_prior=25.0
    ).round(2)

    # Sample Confidence
    bat_master['sample_confidence'] = np.clip(
        np.log1p(bat_master['crisis_balls']) / np.log1p(250.0), 0.1, 1.0
    ).round(4)

    # Normalization across sample eligible pool
    el_pool = bat_master[bat_master['sample_eligible']].copy()
    if len(el_pool) == 0:
        el_pool = bat_master.copy()

    def _minmax(s, ref_s):
        lo, hi = ref_s.min(), ref_s.max()
        return np.clip((s - lo) / (hi - lo), 0.0, 1.0) if hi > lo else pd.Series(0.5, index=s.index)

    bat_master['norm_maint'] = _minmax(bat_master['sr_maintenance'], el_pool['sr_maintenance'])
    bat_master['norm_abs'] = _minmax(bat_master['shrunk_crisis_sr'], el_pool['shrunk_crisis_sr'])
    bat_master['norm_cons'] = _minmax(bat_master['consistency_score'], el_pool['consistency_score'])
    bat_master['norm_sample'] = bat_master['sample_confidence']

    # V3 Performance Score
    w = PRI_WEIGHTS
    bat_master['batting_pri'] = (
        w['maintenance'] * bat_master['norm_maint'] +
        w['absolute'] * bat_master['norm_abs'] +
        w['consistency'] * bat_master['norm_cons'] +
        w['sample'] * bat_master['norm_sample']
    ) * 100.0
    bat_master['batting_pri'] = bat_master['batting_pri'].round(2)

    # Filter strictly for Primary Top 10: ELIGIBLE + Role is BAT_SPECIALIST or BAT_PRIMARY_AR
    top_batters_eligible = bat_master[
        (bat_master['sample_eligible'] == True) &
        (bat_master['eligible_for_bat_leaderboard'] == True)
    ].sort_values('batting_pri', ascending=False).reset_index(drop=True)

    top_batters_eligible['rank'] = range(1, len(top_batters_eligible) + 1)
    top10_batters = top_batters_eligible.head(10).copy()

    # ══════════════════════════════════════════════════════════════════════════
    # 2. BOWLING RANKINGS PIPELINE
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Computing Universal Bowling Intelligence...")
    legal = bbb[bbb['is_legal_ball'] == True].copy()
    
    p_high_bowl = legal[legal['is_bowling_high_pressure'] == True]
    p_norm_bowl = legal[legal['is_bowling_normal_pressure'] == True]

    def _agg_bowl(tier_df, prefix):
        if len(tier_df) == 0:
            return pd.DataFrame(columns=['bowler_id', f'{prefix}_balls', f'{prefix}_wickets', f'{prefix}_dot_pct', f'{prefix}_matches'])
        agg = tier_df.groupby('bowler_id').agg(
            balls=('batter_runs', 'count'),
            wickets=('is_bowler_wicket', 'sum'),
            dots=('is_dot_ball', 'sum'),
            matches=('match_id', 'nunique')
        ).reset_index()
        agg[f'{prefix}_balls'] = agg['balls']
        agg[f'{prefix}_wickets'] = agg['wickets']
        agg[f'{prefix}_dot_pct'] = np.where(agg['balls'] > 0, agg['dots'] / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_wicket_rate'] = np.where(agg['balls'] > 0, agg['wickets'] / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[['bowler_id', f'{prefix}_balls', f'{prefix}_wickets', f'{prefix}_dot_pct', f'{prefix}_wicket_rate', f'{prefix}_matches']]

    df_high_bowl = _agg_bowl(p_high_bowl, 'crisis')
    df_norm_bowl = _agg_bowl(p_norm_bowl, 'norm')

    df_tot_bowl = legal.groupby('bowler_id').agg(
        total_legal_balls=('batter_runs', 'count'),
        total_wickets=('is_bowler_wicket', 'sum'),
        total_matches=('match_id', 'nunique')
    ).reset_index()

    bowl_master = df_tot_bowl.merge(df_high_bowl, on='bowler_id', how='left')
    bowl_master = bowl_master.merge(df_norm_bowl, on='bowler_id', how='left').fillna(0)

    # Attach V3 Roles
    bowl_master['player_name'] = bowl_master['bowler_id'].apply(lambda pid: role_map.get(pid, {}).get('player_name', f"Player_{pid}"))
    bowl_master['v3_role'] = bowl_master['bowler_id'].apply(lambda pid: role_map.get(pid, {}).get('v3_role', 'UNRESOLVED'))
    bowl_master['role_confidence'] = bowl_master['bowler_id'].apply(lambda pid: role_map.get(pid, {}).get('role_confidence', 'LOW'))
    bowl_master['eligible_for_bowl_leaderboard'] = bowl_master['bowler_id'].apply(lambda pid: role_map.get(pid, {}).get('eligible_for_bowl_leaderboard', False))

    # Consistency & Uncertainty Calculation
    b_consistencies = []
    b_ci_lows = []
    b_ci_highs = []
    b_uncertainty_widths = []

    for _, row in bowl_master.iterrows():
        bid = row['bowler_id']
        cb = row['crisis_balls']
        cm = row['crisis_matches']

        if cb < 15 or cm < 3:
            b_consistencies.append(0.10)
            b_ci_lows.append(max(0.0, row['crisis_dot_pct'] - 20.0))
            b_ci_highs.append(min(100.0, row['crisis_dot_pct'] + 20.0))
            b_uncertainty_widths.append(40.0)
            continue

        p_p_high = p_high_bowl[p_high_bowl['bowler_id'] == bid]
        m_dots = p_p_high.groupby('match_id')['is_dot_ball'].sum()
        m_balls = p_p_high.groupby('match_id')['batter_runs'].count()
        m_dot_rates = (m_dots / m_balls) * 100.0

        mean_dot = m_dot_rates.mean()
        std_dot = m_dot_rates.std() if len(m_dot_rates) > 1 else mean_dot * 0.4
        cv = (std_dot / mean_dot) if mean_dot > 0 else 1.2
        m_w = np.sqrt(cm / (cm + 3.0))
        c_score = np.clip(np.exp(-cv) * m_w, 0.08, 0.98)
        b_consistencies.append(round(float(c_score), 4))

        boot = V3ReliabilityEngine.match_clustered_bootstrap_bowling(p_high_bowl, bid, n_bootstraps=200)
        b_ci_lows.append(boot['ci_lower'])
        b_ci_highs.append(boot['ci_upper'])
        b_uncertainty_widths.append(boot['uncertainty_width'])

    bowl_master['consistency_score'] = b_consistencies
    bowl_master['ci_lower'] = b_ci_lows
    bowl_master['ci_upper'] = b_ci_highs
    bowl_master['uncertainty_width'] = b_uncertainty_widths

    # Eligibility Thresholds: >= 120 crisis balls (frontline) or >= 40 (all-role), >= 120 total, >= 5 matches, >= 30 norm balls
    cond_b_cb = bowl_master['crisis_balls'] >= 120
    cond_b_tb = bowl_master['total_legal_balls'] >= 120
    cond_b_cm = bowl_master['crisis_matches'] >= 5
    cond_b_nb = bowl_master['norm_balls'] >= 30
    bowl_master['sample_eligible'] = cond_b_cb & cond_b_tb & cond_b_cm & cond_b_nb

    bowl_master['eligibility_status'] = np.where(
        bowl_master['sample_eligible'], 'ELIGIBLE',
        np.where(bowl_master['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE')
    )

    # Dot Maintenance
    norm_dot_safe = np.maximum(25.0, bowl_master['norm_dot_pct'].values)
    bowl_master['dot_maintenance'] = np.clip(bowl_master['crisis_dot_pct'].values / norm_dot_safe, 0.5, 1.5).round(3)

    # Beta-Binomial Shrunk Wicket Rate
    bowl_master['shrunk_crisis_wr'] = V3ReliabilityEngine.empirical_bayes_beta_binomial_shrinkage(
        bowl_master['crisis_wickets'], bowl_master['crisis_balls']
    ).round(2)

    # Sample Confidence
    bowl_master['sample_confidence'] = np.clip(
        np.log1p(bowl_master['crisis_balls']) / np.log1p(250.0), 0.1, 1.0
    ).round(4)

    el_pool_b = bowl_master[bowl_master['sample_eligible']].copy()
    if len(el_pool_b) == 0:
        el_pool_b = bowl_master.copy()

    bowl_master['norm_maint'] = _minmax(bowl_master['dot_maintenance'], el_pool_b['dot_maintenance'])
    bowl_master['norm_abs'] = _minmax(bowl_master['shrunk_crisis_wr'], el_pool_b['shrunk_crisis_wr'])
    bowl_master['norm_cons'] = _minmax(bowl_master['consistency_score'], el_pool_b['consistency_score'])
    bowl_master['norm_sample'] = bowl_master['sample_confidence']

    bowl_master['bowling_pri'] = (
        w['maintenance'] * bowl_master['norm_maint'] +
        w['absolute'] * bowl_master['norm_abs'] +
        w['consistency'] * bowl_master['norm_cons'] +
        w['sample'] * bowl_master['norm_sample']
    ) * 100.0
    bowl_master['bowling_pri'] = bowl_master['bowling_pri'].round(2)

    # Filter strictly for Primary Top 10 Bowlers: ELIGIBLE + Role is BOWL_SPECIALIST or BOWL_PRIMARY_AR
    top_bowlers_eligible = bowl_master[
        (bowl_master['sample_eligible'] == True) &
        (bowl_master['eligible_for_bowl_leaderboard'] == True)
    ].sort_values('bowling_pri', ascending=False).reset_index(drop=True)

    top_bowlers_eligible['rank'] = range(1, len(top_bowlers_eligible) + 1)
    top10_bowlers = top_bowlers_eligible.head(10).copy()

    # ══════════════════════════════════════════════════════════════════════════
    # 3. EXPORT ALL ARTIFACTS
    # ══════════════════════════════════════════════════════════════════════════
    top10_batters.to_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv", index=False)
    top10_bowlers.to_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv", index=False)
    bat_master.to_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", index=False)
    bowl_master.to_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", index=False)

    # Combined Player Eligibility Table
    elig_records = []
    for _, r in bat_master.iterrows():
        elig_records.append({
            'player_id': r['striker_id'],
            'player_name': r['player_name'],
            'discipline': 'Batting',
            'v3_role': r['v3_role'],
            'crisis_deliveries': r['crisis_balls'],
            'total_deliveries': r['total_balls'],
            'crisis_matches': r['crisis_matches'],
            'normal_deliveries': r['norm_balls'],
            'is_sample_eligible': r['sample_eligible'],
            'is_role_eligible': r['eligible_for_bat_leaderboard'],
            'final_eligibility': 'ELIGIBLE' if (r['sample_eligible'] and r['eligible_for_bat_leaderboard']) else 'INELIGIBLE'
        })
    for _, r in bowl_master.iterrows():
        elig_records.append({
            'player_id': r['bowler_id'],
            'player_name': r['player_name'],
            'discipline': 'Bowling',
            'v3_role': r['v3_role'],
            'crisis_deliveries': r['crisis_balls'],
            'total_deliveries': r['total_legal_balls'],
            'crisis_matches': r['crisis_matches'],
            'normal_deliveries': r['norm_balls'],
            'is_sample_eligible': r['sample_eligible'],
            'is_role_eligible': r['eligible_for_bowl_leaderboard'],
            'final_eligibility': 'ELIGIBLE' if (r['sample_eligible'] and r['eligible_for_bowl_leaderboard']) else 'INELIGIBLE'
        })
    elig_df = pd.DataFrame(elig_records)
    elig_df.to_csv(OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv", index=False)

    logging.info("V3 Universal Rankings computation complete!")
    print("\n=== TOP 10 BATTERS UNDER PRESSURE (V3) ===")
    print(top10_batters[['rank', 'player_name', 'v3_role', 'crisis_balls', 'crisis_sr', 'norm_sr', 'sr_maintenance', 'batting_pri']].to_string())

    print("\n=== TOP 10 BOWLERS UNDER PRESSURE (V3) ===")
    print(top10_bowlers[['rank', 'player_name', 'v3_role', 'crisis_balls', 'crisis_dot_pct', 'norm_dot_pct', 'dot_maintenance', 'bowling_pri']].to_string())


if __name__ == '__main__':
    compute_v3_rankings()
