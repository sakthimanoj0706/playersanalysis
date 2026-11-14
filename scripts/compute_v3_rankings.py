"""Compute V3 Universal Cricket Rankings with Full Statistical Integrity.

Repairs:
1. Priority 1: Canonical player identity resolution before aggregation.
2. Priority 2: Pressure feature schema completeness, data validity flags, no silent defaults.
3. Priority 3: Eligible prior-population masking, fixed-K assumption disclosure.
4. Priority 4: Match-clustered bootstrap confidence intervals without arbitrary fallbacks.
5. Priority 5: Sample eligibility threshold sensitivity study (saved to CSV).
6. Priority 6: Component score contributions and weight sensitivity study (saved to CSV).
7. Priority 7: Mutually exclusive pressure buckets, normal baseline validity flags, deterministic sorting.
8. Priority 8: Authoritative single source of truth Top-10 files and JSON metadata manifest.
"""
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple, Any
import datetime
import hashlib
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.identity.player_identity import PlayerIdentityResolver
from src.ingestion.adapters.rr_data_adapter import RRDataAdapter
from src.pressure_engine.v3_pressure_model import V3PressureModel
from src.reliability.v3_reliability import V3ReliabilityEngine
from src.ranking_engine.pressure_rankings import PRI_WEIGHTS, SENSITIVITY_CONFIGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUTS_V3 = DATA_DIR / "outputs" / "v3"
REPORTS_V3 = DATA_DIR / "reports" / "v3"
OUTPUTS_V3.mkdir(parents=True, exist_ok=True)
REPORTS_V3.mkdir(parents=True, exist_ok=True)

# Baseline Thresholds
DEFAULT_BAT_THRESHOLDS = {
    'crisis_balls': 40,
    'total_balls': 120,
    'crisis_matches': 5,
    'norm_balls': 30
}

DEFAULT_BOWL_THRESHOLDS = {
    'crisis_balls': 120,
    'total_legal_balls': 120,
    'crisis_matches': 5,
    'norm_balls': 30
}


def load_verified_deliveries() -> pd.DataFrame:
    """Load or rebuild verified delivery dataset with canonical IDs and V3 pressure features."""
    press_path = DATA_DIR / "features" / "ball_by_ball_with_pressure.parquet"
    ctx_path = DATA_DIR / "features" / "ball_by_ball_with_context.parquet"
    resolver = PlayerIdentityResolver()

    rebuild_needed = True
    if press_path.exists():
        try:
            df = pd.read_parquet(press_path)
            # Validate required columns
            req = ['canonical_striker_id', 'canonical_bowler_id', 'batting_pressure_data_valid',
                   'bowling_pressure_data_valid', 'is_batting_high_pressure', 'is_bowling_high_pressure']
            if all(c in df.columns for c in req) and len(df) > 0:
                rebuild_needed = False
                logging.info(f"Loaded verified pressure parquet ({len(df)} rows)")
        except Exception as e:
            logging.warning(f"Error reading {press_path}: {e}. Rebuilding...")

    if rebuild_needed:
        logging.info("Rebuilding ball_by_ball_with_pressure.parquet from verified context...")
        if ctx_path.exists():
            df = pd.read_parquet(ctx_path)
        else:
            raw_bbb = pd.read_csv(DATA_DIR / "ball_by_ball_ipl_t20i.csv", dtype={'season': str})
            adapter = RRDataAdapter()
            df = adapter.transform_deliveries(raw_bbb)
        
        df = resolver.resolve_deliveries(df)
        df = V3PressureModel.apply_dual_pressure(df)
        df['v3_pressure_schema_version'] = 'V3.1_CANONICAL'
        df['v3_pressure_formula_version'] = 'V3_PROVISIONAL_HEURISTIC'
        df.to_parquet(press_path, index=False)
        logging.info(f"Saved rebuilt {press_path} ({len(df)} rows)")

    # Standardize column names
    if 'batter_runs' not in df.columns and 'runs' in df.columns:
        df['batter_runs'] = df['runs']
    if 'is_dot_ball' not in df.columns:
        df['is_dot_ball'] = (df['is_legal_ball'] == True) & (df['batter_runs'] == 0)
    if 'is_bowler_wicket' not in df.columns and 'is_wicket' in df.columns:
        non_bowler = ['Run Out', 'RunOut', 'Retired Out', 'Retire Out', 'Obstructing the field', 'Obstracting the field']
        df['is_bowler_wicket'] = df['is_wicket'] & ~df.get('dismissal_type', pd.Series(dtype=str)).isin(non_bowler)
    if 'is_four_validated' not in df.columns:
        df['is_four_validated'] = df.get('is_four', df['batter_runs'] == 4)
    if 'is_six_validated' not in df.columns:
        df['is_six_validated'] = df.get('is_six', df['batter_runs'] == 6)

    # Ensure canonical IDs are active
    if 'canonical_striker_id' in df.columns:
        df['striker_id'] = df['canonical_striker_id']
    if 'canonical_bowler_id' in df.columns:
        df['bowler_id'] = df['canonical_bowler_id']

    return df


def compute_v3_rankings(
    n_bootstrap_final: int = 2000,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute complete Universal Ranking Pipeline with sensitivity studies and single-source outputs."""
    logging.info("Starting Universal Player Ranking Pipeline...")
    bbb = load_verified_deliveries()
    resolver = PlayerIdentityResolver()
    resolver.load_or_build()

    # Load V3 Player Roles
    roles_path = OUTPUTS_V3 / "player_roles.csv"
    if not roles_path.exists():
        logging.info("Generating player_roles.csv using canonical identity...")
        from scripts.generate_v3_roles import main as gen_roles
        gen_roles()
    roles_df = pd.read_csv(roles_path)
    role_map = roles_df.set_index('player_id').to_dict('index')

    # ══════════════════════════════════════════════════════════════════════════
    # 1. BATTING RANKINGS PIPELINE
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Aggregating Universal Batting Intelligence...")
    faced = bbb[bbb['is_ball_faced'] == True].copy()

    # Mutually exclusive pressure sets (only valid pressure records)
    p_high = faced[(faced['batting_pressure_data_valid'] == True) & (faced['is_batting_high_pressure'] == True)]
    p_norm = faced[(faced['batting_pressure_data_valid'] == True) & (faced['is_batting_normal_pressure'] == True)]
    p_mod = faced[(faced['batting_pressure_data_valid'] == True) & (faced['is_batting_moderate_pressure'] == True)]
    p_unclass = faced[faced['batting_pressure_data_valid'] == False]

    def _agg_bat(tier_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
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
        agg[f'{prefix}_sr'] = np.where(agg['balls'] > 0, (agg['runs'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[['striker_id', f'{prefix}_balls', f'{prefix}_runs', f'{prefix}_sr', f'{prefix}_matches']]

    df_high_bat = _agg_bat(p_high, 'crisis')
    df_norm_bat = _agg_bat(p_norm, 'norm')

    df_tot_bat = faced.groupby('striker_id').agg(
        total_balls=('batter_runs', 'count'),
        total_runs=('batter_runs', 'sum'),
        total_matches=('match_id', 'nunique')
    ).reset_index()
    df_tot_bat['total_sr'] = np.where(
        df_tot_bat['total_balls'] > 0,
        (df_tot_bat['total_runs'] / df_tot_bat['total_balls']) * 100.0,
        np.nan
    )

    bat_master = df_tot_bat.merge(df_high_bat, on='striker_id', how='left')
    bat_master = bat_master.merge(df_norm_bat, on='striker_id', how='left')

    # Fill count fields with 0; performance rates remain NaN if balls == 0
    count_cols = ['crisis_balls', 'crisis_runs', 'crisis_matches', 'norm_balls', 'norm_runs', 'norm_matches']
    for c in count_cols:
        bat_master[c] = bat_master[c].fillna(0).astype(int)

    # Attach Canonical Player Metadata & Roles
    bat_master['canonical_player_id'] = bat_master['striker_id']
    bat_master['player_name'] = bat_master['canonical_player_id'].apply(resolver.resolve_name)
    bat_master['v3_role'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('v3_role', 'UNRESOLVED'))
    bat_master['role_confidence'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('role_confidence', 'LOW'))
    bat_master['modal_order'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('modal_order', 10))
    bat_master['eligible_for_bat_leaderboard'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('eligible_for_bat_leaderboard', False))
    bat_master['is_quarantined'] = bat_master['canonical_player_id'].apply(resolver.is_quarantined)

    # Normal comparison validity
    norm_status = []
    sr_maints = []
    for _, r in bat_master.iterrows():
        nb = r['norm_balls']
        nsr = r['norm_sr']
        csr = r['crisis_sr']
        if nb >= 30 and pd.notna(nsr):
            norm_status.append('VALID_NORMAL_BASELINE')
            safe_norm_sr = max(80.0, float(nsr))
            maint = round(float(np.clip(csr / safe_norm_sr, 0.5, 1.5)), 3) if pd.notna(csr) else np.nan
            sr_maints.append(maint)
        elif nb > 0:
            norm_status.append('INSUFFICIENT_NORMAL_EXPOSURE')
            sr_maints.append(np.nan)
        else:
            norm_status.append('NO_NORMAL_EXPOSURE')
            sr_maints.append(np.nan)

    bat_master['norm_baseline_status'] = norm_status
    bat_master['sr_maintenance'] = sr_maints

    # Sample Eligibility: crisis >= 40, total >= 120, crisis matches >= 5, norm balls >= 30
    c_cb = bat_master['crisis_balls'] >= DEFAULT_BAT_THRESHOLDS['crisis_balls']
    c_tb = bat_master['total_balls'] >= DEFAULT_BAT_THRESHOLDS['total_balls']
    c_cm = bat_master['crisis_matches'] >= DEFAULT_BAT_THRESHOLDS['crisis_matches']
    c_nb = bat_master['norm_balls'] >= DEFAULT_BAT_THRESHOLDS['norm_balls']
    c_not_quar = ~bat_master['is_quarantined']

    bat_master['sample_eligible'] = c_cb & c_tb & c_cm & c_nb & c_not_quar
    bat_master['eligibility_status'] = np.where(
        bat_master['sample_eligible'], 'ELIGIBLE',
        np.where(bat_master['is_quarantined'], 'IDENTITY_CONFLICT_QUARANTINE',
                 np.where(bat_master['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE'))
    )

    # Detailed exclusion reason tracking
    def _bat_exclusion_reason(r):
        reasons = []
        if r['is_quarantined']:
            reasons.append('IDENTITY_CONFLICT')
        if r['crisis_balls'] < DEFAULT_BAT_THRESHOLDS['crisis_balls']:
            reasons.append(f"CRISIS_BALLS<{DEFAULT_BAT_THRESHOLDS['crisis_balls']}")
        if r['total_balls'] < DEFAULT_BAT_THRESHOLDS['total_balls']:
            reasons.append(f"TOTAL_BALLS<{DEFAULT_BAT_THRESHOLDS['total_balls']}")
        if r['crisis_matches'] < DEFAULT_BAT_THRESHOLDS['crisis_matches']:
            reasons.append(f"CRISIS_MATCHES<{DEFAULT_BAT_THRESHOLDS['crisis_matches']}")
        if r['norm_balls'] < DEFAULT_BAT_THRESHOLDS['norm_balls']:
            reasons.append(f"NORM_BALLS<{DEFAULT_BAT_THRESHOLDS['norm_balls']}")
        if not r['eligible_for_bat_leaderboard']:
            reasons.append(f"INELIGIBLE_ROLE_{r['v3_role']}")
        return "; ".join(reasons) if reasons else 'NONE'

    bat_master['exclusion_reasons'] = bat_master.apply(_bat_exclusion_reason, axis=1)

    # Shrunk Crisis SR with explicit eligible prior population
    prior_bat_mask = bat_master['sample_eligible'] & bat_master['eligible_for_bat_leaderboard'] & (bat_master['crisis_balls'] > 0)
    shrunk_sr, bat_prior_meta = V3ReliabilityEngine.fixed_k_normal_shrinkage(
        bat_master['crisis_sr'],
        bat_master['crisis_balls'],
        k_prior=25.0,
        eligible_mask=prior_bat_mask,
        return_metadata=True
    )
    bat_master['shrunk_crisis_sr'] = shrunk_sr.round(2)
    bat_master['prior_k'] = bat_prior_meta['prior_k']
    bat_master['prior_mean'] = bat_prior_meta['prior_mean']
    bat_master['prior_population_count'] = bat_prior_meta['prior_population_count']
    bat_master['prior_population_definition'] = bat_prior_meta['prior_population_definition']
    bat_master['shrinkage_status'] = bat_prior_meta['shrinkage_status']

    # Sample Confidence
    bat_master['sample_confidence'] = np.clip(
        np.log1p(bat_master['crisis_balls']) / np.log1p(250.0), 0.1, 1.0
    ).round(4)

    # Consistency & Match-Clustered Bootstrap CI
    logging.info(f"Computing Match-Clustered Bootstrap ({n_bootstrap_final} iter) for Batters...")
    consistencies = []
    ci_lows = []
    ci_highs = []
    uncert_widths = []
    ci_statuses = []
    ci_methods = []
    ci_conf_levels = []
    ci_sample_matches = []
    ci_sample_deliveries = []

    for _, row in bat_master.iterrows():
        pid = row['canonical_player_id']
        cb = row['crisis_balls']
        cm = row['crisis_matches']

        # Consistency score
        if cb < 15 or cm < 3:
            consistencies.append(0.10)
        else:
            p_sub = p_high[p_high['striker_id'] == pid]
            m_runs = p_sub.groupby('match_id')['batter_runs'].sum()
            m_balls = p_sub.groupby('match_id')['batter_runs'].count()
            m_srs = (m_runs / m_balls) * 100.0
            mean_sr = m_srs.mean()
            std_sr = m_srs.std() if len(m_srs) > 1 else mean_sr * 0.5
            cv = (std_sr / mean_sr) if mean_sr > 0 else 1.5
            m_w = np.sqrt(cm / (cm + 3.0))
            c_score = np.clip(np.exp(-cv) * m_w, 0.05, 0.98)
            consistencies.append(round(float(c_score), 4))

        # Bootstrap CI on match cluster
        boot = V3ReliabilityEngine.match_clustered_bootstrap_batting(
            p_high, pid, n_bootstraps=n_bootstrap_final, random_state=random_state, min_matches=3
        )
        ci_lows.append(boot['ci_lower'])
        ci_highs.append(boot['ci_upper'])
        uncert_widths.append(boot['uncertainty_width'])
        ci_statuses.append(boot['ci_status'])
        ci_methods.append(boot['ci_method'])
        ci_conf_levels.append(boot['ci_confidence_level'])
        ci_sample_matches.append(boot['ci_sample_matches'])
        ci_sample_deliveries.append(boot['ci_sample_deliveries'])

    bat_master['consistency_score'] = consistencies
    bat_master['ci_lower'] = ci_lows
    bat_master['ci_upper'] = ci_highs
    bat_master['uncertainty_width'] = uncert_widths
    bat_master['ci_status'] = ci_statuses
    bat_master['ci_method'] = ci_methods
    bat_master['ci_confidence_level'] = ci_conf_levels
    bat_master['ci_bootstrap_iterations'] = n_bootstrap_final
    bat_master['ci_sample_matches'] = ci_sample_matches
    bat_master['ci_sample_deliveries'] = ci_sample_deliveries
    bat_master['ci_metric'] = 'CRISIS_STRIKE_RATE'

    # Normalization across eligible pool
    el_pool_bat = bat_master[bat_master['sample_eligible'] & bat_master['eligible_for_bat_leaderboard']].copy()
    if len(el_pool_bat) == 0:
        el_pool_bat = bat_master[bat_master['sample_eligible']].copy()
    if len(el_pool_bat) == 0:
        el_pool_bat = bat_master.copy()

    def _minmax(s: pd.Series, ref_s: pd.Series) -> pd.Series:
        valid_ref = ref_s.dropna()
        if len(valid_ref) == 0 or valid_ref.max() == valid_ref.min():
            return pd.Series(0.5, index=s.index)
        lo, hi = valid_ref.min(), valid_ref.max()
        return np.clip((s - lo) / (hi - lo), 0.0, 1.0).fillna(0.0)

    bat_master['norm_maint'] = _minmax(bat_master['sr_maintenance'], el_pool_bat['sr_maintenance'])
    bat_master['norm_abs'] = _minmax(bat_master['shrunk_crisis_sr'], el_pool_bat['shrunk_crisis_sr'])
    bat_master['norm_cons'] = _minmax(bat_master['consistency_score'], el_pool_bat['consistency_score'])
    bat_master['norm_sample'] = bat_master['sample_confidence']

    # Component contributions & Provisional PRI Score
    w = PRI_WEIGHTS
    bat_master['contrib_maint'] = (w['maintenance'] * bat_master['norm_maint'] * 100.0).round(2)
    bat_master['contrib_abs'] = (w['absolute'] * bat_master['norm_abs'] * 100.0).round(2)
    bat_master['contrib_cons'] = (w['consistency'] * bat_master['norm_cons'] * 100.0).round(2)
    bat_master['contrib_sample'] = (w['sample'] * bat_master['norm_sample'] * 100.0).round(2)

    bat_master['batting_pri_provisional'] = (
        bat_master['contrib_maint'] +
        bat_master['contrib_abs'] +
        bat_master['contrib_cons'] +
        bat_master['contrib_sample']
    ).round(2)
    bat_master['provisional_fixed_weight_score'] = bat_master['batting_pri_provisional']
    bat_master['batting_pri'] = bat_master['batting_pri_provisional']  # Backward compatibility
    bat_master['formula_status'] = 'PROVISIONAL_FIXED_WEIGHT_SCORE'

    # Filter strictly for Primary Eligible Batters: ELIGIBLE + Role is BAT_SPECIALIST or BAT_PRIMARY_AR
    top_batters_eligible = bat_master[
        (bat_master['sample_eligible'] == True) &
        (bat_master['eligible_for_bat_leaderboard'] == True)
    ].sort_values(
        by=['provisional_fixed_weight_score', 'canonical_player_id'],
        ascending=[False, True]
    ).reset_index(drop=True)

    top_batters_eligible['provisional_rank'] = range(1, len(top_batters_eligible) + 1)
    top_batters_eligible['rank'] = top_batters_eligible['provisional_rank']
    top10_batters = top_batters_eligible.head(10).copy()

    # ══════════════════════════════════════════════════════════════════════════
    # 2. BOWLING RANKINGS PIPELINE
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Aggregating Universal Bowling Intelligence...")
    legal = bbb[bbb['is_legal_ball'] == True].copy()

    p_high_bowl = legal[(legal['bowling_pressure_data_valid'] == True) & (legal['is_bowling_high_pressure'] == True)]
    p_norm_bowl = legal[(legal['bowling_pressure_data_valid'] == True) & (legal['is_bowling_normal_pressure'] == True)]

    def _agg_bowl(tier_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
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
        agg[f'{prefix}_dot_pct'] = np.where(agg['balls'] > 0, (agg['dots'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_wicket_rate'] = np.where(agg['balls'] > 0, (agg['wickets'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[['bowler_id', f'{prefix}_balls', f'{prefix}_wickets', f'{prefix}_dot_pct', f'{prefix}_wicket_rate', f'{prefix}_matches']]

    df_high_bowl = _agg_bowl(p_high_bowl, 'crisis')
    df_norm_bowl = _agg_bowl(p_norm_bowl, 'norm')

    df_tot_bowl = legal.groupby('bowler_id').agg(
        total_legal_balls=('batter_runs', 'count'),
        total_wickets=('is_bowler_wicket', 'sum'),
        total_dots=('is_dot_ball', 'sum'),
        total_matches=('match_id', 'nunique')
    ).reset_index()
    df_tot_bowl['total_dot_pct'] = np.where(
        df_tot_bowl['total_legal_balls'] > 0,
        (df_tot_bowl['total_dots'] / df_tot_bowl['total_legal_balls']) * 100.0,
        np.nan
    )

    bowl_master = df_tot_bowl.merge(df_high_bowl, on='bowler_id', how='left')
    bowl_master = bowl_master.merge(df_norm_bowl, on='bowler_id', how='left')

    for c in ['crisis_balls', 'crisis_wickets', 'crisis_matches', 'norm_balls', 'norm_wickets', 'norm_matches']:
        bowl_master[c] = bowl_master[c].fillna(0).astype(int)

    # Attach Canonical Player Metadata & Roles
    bowl_master['canonical_player_id'] = bowl_master['bowler_id']
    bowl_master['player_name'] = bowl_master['canonical_player_id'].apply(resolver.resolve_name)
    bowl_master['v3_role'] = bowl_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('v3_role', 'UNRESOLVED'))
    bowl_master['role_confidence'] = bowl_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('role_confidence', 'LOW'))
    bowl_master['eligible_for_bowl_leaderboard'] = bowl_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('eligible_for_bowl_leaderboard', False))
    bowl_master['is_quarantined'] = bowl_master['canonical_player_id'].apply(resolver.is_quarantined)

    # Normal comparison validity
    norm_status_b = []
    dot_maints = []
    for _, r in bowl_master.iterrows():
        nb = r['norm_balls']
        ndot = r['norm_dot_pct']
        cdot = r['crisis_dot_pct']
        if nb >= 30 and pd.notna(ndot):
            norm_status_b.append('VALID_NORMAL_BASELINE')
            safe_norm_dot = max(25.0, float(ndot))
            maint = round(float(np.clip(cdot / safe_norm_dot, 0.5, 1.5)), 3) if pd.notna(cdot) else np.nan
            dot_maints.append(maint)
        elif nb > 0:
            norm_status_b.append('INSUFFICIENT_NORMAL_EXPOSURE')
            dot_maints.append(np.nan)
        else:
            norm_status_b.append('NO_NORMAL_EXPOSURE')
            dot_maints.append(np.nan)

    bowl_master['norm_baseline_status'] = norm_status_b
    bowl_master['dot_maintenance'] = dot_maints

    # Sample Eligibility: crisis >= 120, total >= 120, crisis matches >= 5, norm balls >= 30
    c_b_cb = bowl_master['crisis_balls'] >= DEFAULT_BOWL_THRESHOLDS['crisis_balls']
    c_b_tb = bowl_master['total_legal_balls'] >= DEFAULT_BOWL_THRESHOLDS['total_legal_balls']
    c_b_cm = bowl_master['crisis_matches'] >= DEFAULT_BOWL_THRESHOLDS['crisis_matches']
    c_b_nb = bowl_master['norm_balls'] >= DEFAULT_BOWL_THRESHOLDS['norm_balls']
    c_b_not_quar = ~bowl_master['is_quarantined']

    bowl_master['sample_eligible'] = c_b_cb & c_b_tb & c_b_cm & c_b_nb & c_b_not_quar
    bowl_master['eligibility_status'] = np.where(
        bowl_master['sample_eligible'], 'ELIGIBLE',
        np.where(bowl_master['is_quarantined'], 'IDENTITY_CONFLICT_QUARANTINE',
                 np.where(bowl_master['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE'))
    )

    def _bowl_exclusion_reason(r):
        reasons = []
        if r['is_quarantined']:
            reasons.append('IDENTITY_CONFLICT')
        if r['crisis_balls'] < DEFAULT_BOWL_THRESHOLDS['crisis_balls']:
            reasons.append(f"CRISIS_BALLS<{DEFAULT_BOWL_THRESHOLDS['crisis_balls']}")
        if r['total_legal_balls'] < DEFAULT_BOWL_THRESHOLDS['total_legal_balls']:
            reasons.append(f"TOTAL_LEGAL_BALLS<{DEFAULT_BOWL_THRESHOLDS['total_legal_balls']}")
        if r['crisis_matches'] < DEFAULT_BOWL_THRESHOLDS['crisis_matches']:
            reasons.append(f"CRISIS_MATCHES<{DEFAULT_BOWL_THRESHOLDS['crisis_matches']}")
        if r['norm_balls'] < DEFAULT_BOWL_THRESHOLDS['norm_balls']:
            reasons.append(f"NORM_BALLS<{DEFAULT_BOWL_THRESHOLDS['norm_balls']}")
        if not r['eligible_for_bowl_leaderboard']:
            reasons.append(f"INELIGIBLE_ROLE_{r['v3_role']}")
        return "; ".join(reasons) if reasons else 'NONE'

    bowl_master['exclusion_reasons'] = bowl_master.apply(_bowl_exclusion_reason, axis=1)

    # Shrunk Crisis Wicket Rate (Beta-Binomial)
    prior_bowl_mask = bowl_master['sample_eligible'] & bowl_master['eligible_for_bowl_leaderboard'] & (bowl_master['crisis_balls'] > 0)
    shrunk_wr, bowl_prior_meta = V3ReliabilityEngine.empirical_bayes_beta_binomial_shrinkage(
        bowl_master['crisis_wickets'],
        bowl_master['crisis_balls'],
        eligible_mask=prior_bowl_mask,
        return_metadata=True
    )
    bowl_master['shrunk_crisis_wr'] = shrunk_wr.round(2)
    bowl_master['prior_alpha'] = bowl_prior_meta['prior_alpha']
    bowl_master['prior_beta'] = bowl_prior_meta['prior_beta']
    bowl_master['prior_mean'] = bowl_prior_meta['prior_mean']
    bowl_master['prior_population_count'] = bowl_prior_meta['prior_population_count']
    bowl_master['shrinkage_status'] = bowl_prior_meta['shrinkage_status']

    # Sample Confidence
    bowl_master['sample_confidence'] = np.clip(
        np.log1p(bowl_master['crisis_balls']) / np.log1p(250.0), 0.1, 1.0
    ).round(4)

    # Consistency & Match-Clustered Bootstrap CI
    logging.info(f"Computing Match-Clustered Bootstrap ({n_bootstrap_final} iter) for Bowlers...")
    b_consistencies = []
    b_ci_lows = []
    b_ci_highs = []
    b_uncert_widths = []
    b_ci_statuses = []
    b_ci_methods = []
    b_ci_conf_levels = []
    b_ci_sample_matches = []
    b_ci_sample_deliveries = []

    for _, row in bowl_master.iterrows():
        bid = row['canonical_player_id']
        cb = row['crisis_balls']
        cm = row['crisis_matches']

        if cb < 15 or cm < 3:
            b_consistencies.append(0.10)
        else:
            p_sub = p_high_bowl[p_high_bowl['bowler_id'] == bid]
            m_dots = p_sub.groupby('match_id')['is_dot_ball'].sum()
            m_balls = p_sub.groupby('match_id')['batter_runs'].count()
            m_dot_rates = (m_dots / m_balls) * 100.0
            mean_dot = m_dot_rates.mean()
            std_dot = m_dot_rates.std() if len(m_dot_rates) > 1 else mean_dot * 0.4
            cv = (std_dot / mean_dot) if mean_dot > 0 else 1.2
            m_w = np.sqrt(cm / (cm + 3.0))
            c_score = np.clip(np.exp(-cv) * m_w, 0.08, 0.98)
            b_consistencies.append(round(float(c_score), 4))

        boot = V3ReliabilityEngine.match_clustered_bootstrap_bowling(
            p_high_bowl, bid, n_bootstraps=n_bootstrap_final, random_state=random_state, min_matches=3
        )
        b_ci_lows.append(boot['ci_lower'])
        b_ci_highs.append(boot['ci_upper'])
        b_uncert_widths.append(boot['uncertainty_width'])
        b_ci_statuses.append(boot['ci_status'])
        b_ci_methods.append(boot['ci_method'])
        b_ci_conf_levels.append(boot['ci_confidence_level'])
        b_ci_sample_matches.append(boot['ci_sample_matches'])
        b_ci_sample_deliveries.append(boot['ci_sample_deliveries'])

    bowl_master['consistency_score'] = b_consistencies
    bowl_master['ci_lower'] = b_ci_lows
    bowl_master['ci_upper'] = b_ci_highs
    bowl_master['uncertainty_width'] = b_uncert_widths
    bowl_master['ci_status'] = b_ci_statuses
    bowl_master['ci_method'] = b_ci_methods
    bowl_master['ci_confidence_level'] = b_ci_conf_levels
    bowl_master['ci_bootstrap_iterations'] = n_bootstrap_final
    bowl_master['ci_sample_matches'] = b_ci_sample_matches
    bowl_master['ci_sample_deliveries'] = b_ci_sample_deliveries
    bowl_master['ci_metric'] = 'CRISIS_DOT_PERCENTAGE'

    el_pool_bowl = bowl_master[bowl_master['sample_eligible'] & bowl_master['eligible_for_bowl_leaderboard']].copy()
    if len(el_pool_bowl) == 0:
        el_pool_bowl = bowl_master[bowl_master['sample_eligible']].copy()
    if len(el_pool_bowl) == 0:
        el_pool_bowl = bowl_master.copy()

    bowl_master['norm_maint'] = _minmax(bowl_master['dot_maintenance'], el_pool_bowl['dot_maintenance'])
    bowl_master['norm_abs'] = _minmax(bowl_master['shrunk_crisis_wr'], el_pool_bowl['shrunk_crisis_wr'])
    bowl_master['norm_cons'] = _minmax(bowl_master['consistency_score'], el_pool_bowl['consistency_score'])
    bowl_master['norm_sample'] = bowl_master['sample_confidence']

    bowl_master['contrib_maint'] = (w['maintenance'] * bowl_master['norm_maint'] * 100.0).round(2)
    bowl_master['contrib_abs'] = (w['absolute'] * bowl_master['norm_abs'] * 100.0).round(2)
    bowl_master['contrib_cons'] = (w['consistency'] * bowl_master['norm_cons'] * 100.0).round(2)
    bowl_master['contrib_sample'] = (w['sample'] * bowl_master['norm_sample'] * 100.0).round(2)

    bowl_master['bowling_pri_provisional'] = (
        bowl_master['contrib_maint'] +
        bowl_master['contrib_abs'] +
        bowl_master['contrib_cons'] +
        bowl_master['contrib_sample']
    ).round(2)
    bowl_master['provisional_fixed_weight_score'] = bowl_master['bowling_pri_provisional']
    bowl_master['bowling_pri'] = bowl_master['bowling_pri_provisional']
    bowl_master['formula_status'] = 'PROVISIONAL_FIXED_WEIGHT_SCORE'

    top_bowlers_eligible = bowl_master[
        (bowl_master['sample_eligible'] == True) &
        (bowl_master['eligible_for_bowl_leaderboard'] == True)
    ].sort_values(
        by=['provisional_fixed_weight_score', 'canonical_player_id'],
        ascending=[False, True]
    ).reset_index(drop=True)

    top_bowlers_eligible['provisional_rank'] = range(1, len(top_bowlers_eligible) + 1)
    top_bowlers_eligible['rank'] = top_bowlers_eligible['provisional_rank']
    top10_bowlers = top_bowlers_eligible.head(10).copy()

    # ══════════════════════════════════════════════════════════════════════════
    # 3. PRIORITY 5 — THRESHOLD SENSITIVITY STUDY
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Running Threshold Sensitivity Study...")
    thresh_records = []

    # Batter grid: cb in [40, 60, 80, 100], cm in [5, 8, 10], nb in [30, 50, 75], tb in [120, 200, 300]
    base_top10_bat_ids = set(top10_batters['canonical_player_id'])
    for cb in [40, 60, 80, 100]:
        for cm in [5, 8, 10]:
            for nb in [30, 50, 75]:
                for tb in [120, 200, 300]:
                    mask = (
                        (bat_master['crisis_balls'] >= cb) &
                        (bat_master['crisis_matches'] >= cm) &
                        (bat_master['norm_balls'] >= nb) &
                        (bat_master['total_balls'] >= tb) &
                        (bat_master['eligible_for_bat_leaderboard'] == True) &
                        (~bat_master['is_quarantined'])
                    )
                    cand = bat_master[mask].sort_values('provisional_fixed_weight_score', ascending=False)
                    cand_top10 = cand.head(10)
                    cand_top10_ids = set(cand_top10['canonical_player_id'])
                    overlap = len(cand_top10_ids & base_top10_bat_ids)
                    
                    ci_widths = cand['uncertainty_width'].dropna()
                    med_ci = round(float(ci_widths.median()), 2) if len(ci_widths) > 0 else np.nan
                    max_ci = round(float(ci_widths.max()), 2) if len(ci_widths) > 0 else np.nan
                    unest_ci = int(cand['ci_status'].ne('ESTIMATED_MATCH_CLUSTER_BOOTSTRAP').sum())

                    thresh_records.append({
                        'discipline': 'Batting',
                        'min_crisis_balls': cb,
                        'min_crisis_matches': cm,
                        'min_normal_balls': nb,
                        'min_total_deliveries': tb,
                        'eligible_players': len(cand),
                        'unique_canonical_ids': cand['canonical_player_id'].nunique(),
                        'top10_count': len(cand_top10),
                        'top10_overlap_with_baseline': overlap,
                        'median_ci_width': med_ci,
                        'max_ci_width': max_ci,
                        'unestimated_ci_count': unest_ci,
                        'top_eligible_players': ", ".join(cand_top10['player_name'].head(5).tolist())
                    })

    # Bowler grid: cb in [60, 90, 120, 150], cm in [5, 8, 10], nb in [30, 50, 75], tb in [120, 200, 300]
    base_top10_bowl_ids = set(top10_bowlers['canonical_player_id'])
    for cb in [60, 90, 120, 150]:
        for cm in [5, 8, 10]:
            for nb in [30, 50, 75]:
                for tb in [120, 200, 300]:
                    mask = (
                        (bowl_master['crisis_balls'] >= cb) &
                        (bowl_master['crisis_matches'] >= cm) &
                        (bowl_master['norm_balls'] >= nb) &
                        (bowl_master['total_legal_balls'] >= tb) &
                        (bowl_master['eligible_for_bowl_leaderboard'] == True) &
                        (~bowl_master['is_quarantined'])
                    )
                    cand = bowl_master[mask].sort_values('provisional_fixed_weight_score', ascending=False)
                    cand_top10 = cand.head(10)
                    cand_top10_ids = set(cand_top10['canonical_player_id'])
                    overlap = len(cand_top10_ids & base_top10_bowl_ids)

                    ci_widths = cand['uncertainty_width'].dropna()
                    med_ci = round(float(ci_widths.median()), 2) if len(ci_widths) > 0 else np.nan
                    max_ci = round(float(ci_widths.max()), 2) if len(ci_widths) > 0 else np.nan
                    unest_ci = int(cand['ci_status'].ne('ESTIMATED_MATCH_CLUSTER_BOOTSTRAP').sum())

                    thresh_records.append({
                        'discipline': 'Bowling',
                        'min_crisis_balls': cb,
                        'min_crisis_matches': cm,
                        'min_normal_balls': nb,
                        'min_total_deliveries': tb,
                        'eligible_players': len(cand),
                        'unique_canonical_ids': cand['canonical_player_id'].nunique(),
                        'top10_count': len(cand_top10),
                        'top10_overlap_with_baseline': overlap,
                        'median_ci_width': med_ci,
                        'max_ci_width': max_ci,
                        'unestimated_ci_count': unest_ci,
                        'top_eligible_players': ", ".join(cand_top10['player_name'].head(5).tolist())
                    })

    thresh_df = pd.DataFrame(thresh_records)
    thresh_df.to_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv", index=False)

    # ══════════════════════════════════════════════════════════════════════════
    # 4. PRIORITY 6 — WEIGHT SENSITIVITY STUDY
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Running Weight Sensitivity Study across SENSITIVITY_CONFIGS...")
    weight_records = []

    def _eval_weights(df_pool: pd.DataFrame, disc: str, norm_cols: Dict[str, str], base_top10_ids: set) -> pd.DataFrame:
        p_df = df_pool.copy()
        for cfg_name, weights in SENSITIVITY_CONFIGS.items():
            scores = (
                weights['maintenance'] * p_df[norm_cols['maint']] +
                weights['absolute'] * p_df[norm_cols['abs']] +
                weights['consistency'] * p_df[norm_cols['cons']] +
                weights['sample'] * p_df[norm_cols['sample']]
            ) * 100.0
            p_df[f'score_{cfg_name}'] = scores.round(2)
            p_df[f'rank_{cfg_name}'] = p_df[f'score_{cfg_name}'].rank(ascending=False, method='min').astype(int)

        # Rank delta and volatility
        rank_cols = [f'rank_{cfg}' for cfg in SENSITIVITY_CONFIGS.keys()]
        p_df['max_rank_shift'] = p_df[rank_cols].max(axis=1) - p_df[rank_cols].min(axis=1)
        p_df['rank_volatility_std'] = p_df[rank_cols].std(axis=1).round(2)
        p_df['ranking_sensitivity_status'] = np.where(
            p_df['max_rank_shift'] >= 5, 'RANKING_SENSITIVE_TO_WEIGHTS', 'ROBUST_ACROSS_WEIGHTS'
        )

        for _, r in p_df.iterrows():
            weight_records.append({
                'discipline': disc,
                'canonical_player_id': r['canonical_player_id'],
                'player_name': r['player_name'],
                'v3_role': r['v3_role'],
                'provisional_rank': r.get('provisional_rank', np.nan),
                'provisional_fixed_weight_score': r.get('provisional_fixed_weight_score', np.nan),
                'rank_balanced_default': r['rank_balanced_default'],
                'rank_maintenance_heavy': r['rank_maintenance_heavy'],
                'rank_absolute_heavy': r['rank_absolute_heavy'],
                'rank_consistency_heavy': r['rank_consistency_heavy'],
                'rank_equal_weights': r['rank_equal_weights'],
                'max_rank_shift': r['max_rank_shift'],
                'rank_volatility_std': r['rank_volatility_std'],
                'ranking_sensitivity_status': r['ranking_sensitivity_status']
            })
        return p_df

    bat_sens = _eval_weights(
        top_batters_eligible, 'Batting',
        {'maint': 'norm_maint', 'abs': 'norm_abs', 'cons': 'norm_cons', 'sample': 'norm_sample'},
        base_top10_bat_ids
    )
    bowl_sens = _eval_weights(
        top_bowlers_eligible, 'Bowling',
        {'maint': 'norm_maint', 'abs': 'norm_abs', 'cons': 'norm_cons', 'sample': 'norm_sample'},
        base_top10_bowl_ids
    )

    # Attach sensitivity status back to top 10
    top10_batters['ranking_sensitivity_status'] = top10_batters['canonical_player_id'].map(
        bat_sens.set_index('canonical_player_id')['ranking_sensitivity_status'].to_dict()
    )
    top10_bowlers['ranking_sensitivity_status'] = top10_bowlers['canonical_player_id'].map(
        bowl_sens.set_index('canonical_player_id')['ranking_sensitivity_status'].to_dict()
    )

    weight_df = pd.DataFrame(weight_records)
    weight_df.to_csv(OUTPUTS_V3 / "RANKING_WEIGHT_SENSITIVITY.csv", index=False)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. PRIORITY 8 — ONE AUTHORITATIVE SOURCE OF TRUTH OUTPUTS
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Exporting Authoritative Top 10 and Source of Truth artifacts...")
    
    # Authoritative Batter Fields
    bat_auth_cols = [
        'rank', 'provisional_rank', 'canonical_player_id', 'striker_id', 'player_name',
        'v3_role', 'role_confidence', 'modal_order', 'eligibility_status', 'sample_eligible',
        'eligible_for_bat_leaderboard', 'norm_baseline_status',
        'total_balls', 'total_runs', 'total_sr', 'total_matches',
        'crisis_balls', 'crisis_runs', 'crisis_sr', 'crisis_matches',
        'norm_balls', 'norm_runs', 'norm_sr', 'norm_matches',
        'sr_maintenance', 'shrunk_crisis_sr', 'consistency_score', 'sample_confidence',
        'norm_maint', 'norm_abs', 'norm_cons', 'norm_sample',
        'contrib_maint', 'contrib_abs', 'contrib_cons', 'contrib_sample',
        'batting_pri_provisional', 'provisional_fixed_weight_score', 'batting_pri',
        'ci_lower', 'ci_upper', 'uncertainty_width', 'ci_status', 'ci_method',
        'ci_confidence_level', 'ci_bootstrap_iterations', 'ci_sample_matches',
        'ci_sample_deliveries', 'ci_metric', 'ranking_sensitivity_status',
        'prior_k', 'prior_mean', 'prior_population_count', 'prior_population_definition',
        'shrinkage_status', 'formula_status'
    ]
    top10_batters = top10_batters[bat_auth_cols].copy()
    top10_batters.to_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv", index=False)

    # Authoritative Bowler Fields
    bowl_auth_cols = [
        'rank', 'provisional_rank', 'canonical_player_id', 'bowler_id', 'player_name',
        'v3_role', 'role_confidence', 'eligibility_status', 'sample_eligible',
        'eligible_for_bowl_leaderboard', 'norm_baseline_status',
        'total_legal_balls', 'total_wickets', 'total_dots', 'total_dot_pct', 'total_matches',
        'crisis_balls', 'crisis_wickets', 'crisis_dot_pct', 'crisis_wicket_rate', 'crisis_matches',
        'norm_balls', 'norm_wickets', 'norm_dot_pct', 'norm_wicket_rate', 'norm_matches',
        'dot_maintenance', 'shrunk_crisis_wr', 'consistency_score', 'sample_confidence',
        'norm_maint', 'norm_abs', 'norm_cons', 'norm_sample',
        'contrib_maint', 'contrib_abs', 'contrib_cons', 'contrib_sample',
        'bowling_pri_provisional', 'provisional_fixed_weight_score', 'bowling_pri',
        'ci_lower', 'ci_upper', 'uncertainty_width', 'ci_status', 'ci_method',
        'ci_confidence_level', 'ci_bootstrap_iterations', 'ci_sample_matches',
        'ci_sample_deliveries', 'ci_metric', 'ranking_sensitivity_status',
        'prior_alpha', 'prior_beta', 'prior_mean', 'prior_population_count',
        'shrinkage_status', 'formula_status'
    ]
    top10_bowlers = top10_bowlers[bowl_auth_cols].copy()
    top10_bowlers.to_csv(OUTPUTS_V3 / "TOP_10_BOWLERS.csv", index=False)

    # All metrics tables
    bat_master.to_csv(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", index=False)
    bowl_master.to_csv(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", index=False)

    # Master Combined Player Eligibility
    elig_records = []
    for _, r in bat_master.iterrows():
        elig_records.append({
            'canonical_player_id': r['canonical_player_id'],
            'player_name': r['player_name'],
            'discipline': 'Batting',
            'v3_role': r['v3_role'],
            'crisis_deliveries': r['crisis_balls'],
            'total_deliveries': r['total_balls'],
            'crisis_matches': r['crisis_matches'],
            'normal_deliveries': r['norm_balls'],
            'is_sample_eligible': r['sample_eligible'],
            'is_role_eligible': r['eligible_for_bat_leaderboard'],
            'is_quarantined': r['is_quarantined'],
            'final_eligibility': 'ELIGIBLE' if (r['sample_eligible'] and r['eligible_for_bat_leaderboard'] and not r['is_quarantined']) else 'INELIGIBLE',
            'exclusion_reasons': r['exclusion_reasons']
        })
    for _, r in bowl_master.iterrows():
        elig_records.append({
            'canonical_player_id': r['canonical_player_id'],
            'player_name': r['player_name'],
            'discipline': 'Bowling',
            'v3_role': r['v3_role'],
            'crisis_deliveries': r['crisis_balls'],
            'total_deliveries': r['total_legal_balls'],
            'crisis_matches': r['crisis_matches'],
            'normal_deliveries': r['norm_balls'],
            'is_sample_eligible': r['sample_eligible'],
            'is_role_eligible': r['eligible_for_bowl_leaderboard'],
            'is_quarantined': r['is_quarantined'],
            'final_eligibility': 'ELIGIBLE' if (r['sample_eligible'] and r['eligible_for_bowl_leaderboard'] and not r['is_quarantined']) else 'INELIGIBLE',
            'exclusion_reasons': r['exclusion_reasons']
        })
    elig_df = pd.DataFrame(elig_records)
    elig_df.to_csv(OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv", index=False)

    # Master JSON Manifest
    manifest = {
        'manifest_title': 'SupeRR Intelligence V3 Universal Player Ranking Single Source of Truth',
        'generation_timestamp_utc': datetime.datetime.utcnow().isoformat() + 'Z',
        'authoritative_artifacts': {
            'top_10_batters_csv': 'data/outputs/v3/TOP_10_BATTERS.csv',
            'top_10_bowlers_csv': 'data/outputs/v3/TOP_10_BOWLERS.csv',
            'all_batter_metrics_csv': 'data/outputs/v3/ALL_BATTER_METRICS.csv',
            'all_bowler_metrics_csv': 'data/outputs/v3/ALL_BOWLER_METRICS.csv',
            'player_eligibility_csv': 'data/outputs/v3/PLAYER_ELIGIBILITY.csv',
            'threshold_sensitivity_csv': 'data/outputs/v3/RANKING_THRESHOLD_SENSITIVITY.csv',
            'weight_sensitivity_csv': 'data/outputs/v3/RANKING_WEIGHT_SENSITIVITY.csv',
            'player_identity_crosswalk_csv': 'data/outputs/v3/PLAYER_IDENTITY_CROSSWALK.csv'
        },
        'source_datasets': {
            'ball_by_ball': 'data/ball_by_ball_ipl_t20i.csv',
            'playing_eleven': 'data/playing_eleven_ipl_t20i.csv',
            'competition_mapping': 'data/competition_team_player_mapping_ipl_t20i.csv',
            'features_pressure_parquet': 'data/features/ball_by_ball_with_pressure.parquet'
        },
        'governance': {
            'git_baseline_commit': '537777c8436fd647a484a49cfbfa30b843c98a1c',
            'git_branch': 'fix/v3-ranking-integrity-001',
            'ranking_script_version': 'V3.1_INTEGRITY_REPAIRED',
            'pressure_formula_version': 'V3_PROVISIONAL_HEURISTIC',
            'identity_crosswalk_version': 'V3.1_CANONICAL',
            'ranking_score_status': 'PROVISIONAL_FIXED_WEIGHT_SCORE',
            'threshold_governance': 'PROVISIONAL_ELIGIBILITY_CONFIRMED',
            'ranking_approval_status': 'PROVISIONAL_RELEASE_CANDIDATE'
        },
        'configurations': {
            'pri_weights': PRI_WEIGHTS,
            'sensitivity_configs': SENSITIVITY_CONFIGS,
            'default_batting_thresholds': DEFAULT_BAT_THRESHOLDS,
            'default_bowling_thresholds': DEFAULT_BOWL_THRESHOLDS,
            'shrinkage_configuration': {
                'batting_method': 'FIXED_K_NORMAL_SHRINKAGE',
                'prior_k': 25.0,
                'batting_prior_mean': bat_prior_meta['prior_mean'],
                'batting_prior_pop_count': bat_prior_meta['prior_population_count'],
                'bowling_method': 'BETA_BINOMIAL_EMPIRICAL_BAYES',
                'bowling_prior_alpha': bowl_prior_meta['prior_alpha'],
                'bowling_prior_beta': bowl_prior_meta['prior_beta'],
                'bowling_prior_mean': bowl_prior_meta['prior_mean'],
                'bowling_prior_pop_count': bowl_prior_meta['prior_population_count']
            },
            'bootstrap_configuration': {
                'method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'cluster_unit': 'match_id',
                'iterations': n_bootstrap_final,
                'confidence_level': 0.95,
                'random_state': random_state,
                'min_matches': 3
            }
        }
    }
    with open(OUTPUTS_V3 / "RANKING_SOURCE_OF_TRUTH.json", "w") as f:
        json.dump(manifest, f, indent=2)

    logging.info("V3 Universal Rankings execution complete!")
    print("\n=== TOP 10 BATTERS UNDER PRESSURE (V3 AUTHORITATIVE) ===")
    print(top10_batters[['rank', 'canonical_player_id', 'player_name', 'v3_role', 'crisis_balls', 'crisis_sr', 'sr_maintenance', 'provisional_fixed_weight_score', 'ci_status']].to_string())

    print("\n=== TOP 10 BOWLERS UNDER PRESSURE (V3 AUTHORITATIVE) ===")
    print(top10_bowlers[['rank', 'canonical_player_id', 'player_name', 'v3_role', 'crisis_balls', 'crisis_dot_pct', 'dot_maintenance', 'provisional_fixed_weight_score', 'ci_status']].to_string())

    return top10_batters, top10_bowlers, bat_master, bowl_master, elig_df


if __name__ == '__main__':
    compute_v3_rankings()
