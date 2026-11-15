"""Compute V4 Unified Universal Cricket Rankings with Statistical & Context Integrity.

Architecture (V4 Calibrated Ridge):
1. DLS-aware innings context + pure ex-ante state leverage (free of last-12 dot/boundary survivorship bias).
2. Within-(innings, phase) quantile calibration (Top 30% High / 50-70% Moderate / Bottom 50% Normal)
   eliminating the >70% PP/Death crisis classification defect.
3. Competition-tier weighting (T1_IPL / T1_FM_T20I = 1.0, T2_MIXED = 0.5, T3_ASSOC = 0.2)
   and Tier-1 share eligibility (>= 60%).
4. State-conditional expectations (comp_tier x innings x phase x wkt_bucket) + weighted Ridge
   regression (`lsqr`, match_par + striker_offense + bowler_defense) in a single unified currency
   (Runs Above Expectation / 100 balls for batting; Runs Saved / Over including wides & no-balls for bowling).
5. Invariant PRI weights (30% Maint / 35% Abs / 25% Cons / 10% Sample) with strict Normal Baseline
   validity for both disciplines (no weight-reallocation loophole).
6. Value-Gated Downside Match Consistency and Direct Run-Value Match-Clustered Bootstrap 95% CIs.
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
from scipy.sparse import csr_matrix, hstack
from scipy.sparse.linalg import lsqr

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

FULL_MEMBER_TEAMS = {
    'India', 'Pakistan', 'West Indies', 'New Zealand', 'Bangladesh', 'England',
    'Sri Lanka', 'Australia', 'South Africa', 'Afghanistan', 'Zimbabwe', 'Ireland',
}
COMP_TIER_WEIGHTS = {
    'T1_IPL': 1.0,
    'T1_FM_T20I': 1.0,
    'T2_MIXED': 0.5,
    'T3_ASSOC': 0.2,
}
MIN_TIER1_SHARE = 0.60

# Baseline Thresholds (V4 Invariant Normal-Baseline Gate)
DEFAULT_BAT_THRESHOLDS = {
    'crisis_balls': 60,
    'total_balls': 200,
    'crisis_matches': 6,
    'norm_balls': 60,
}

MIN_NORMAL_BALLS_BOWLER = 100

DEFAULT_BOWL_THRESHOLDS = {
    'crisis_balls': 120,
    'total_legal_balls': 250,
    'crisis_matches': 6,
    'norm_balls': MIN_NORMAL_BALLS_BOWLER,
}

V_WKT_BOWL_BY_PHASE = {'powerplay': 5.5, 'middle': 5.0, 'death': 3.5}
V_WKT_BAT_BY_PHASE = {'powerplay': 4.0, 'middle': 3.5, 'death': 2.5}


def _attach_competition_tiers(df: pd.DataFrame, teams_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Attach competition tier (`T1_IPL`, `T1_FM_T20I`, `T2_MIXED`, `T3_ASSOC`) and tier weights."""
    df = df.copy()
    if teams_df is None:
        teams_df = pd.read_csv(DATA_DIR / "teams_ipl_t20i.csv")
    tmap = teams_df[['team_id', 'team_name']].drop_duplicates().set_index('team_id')['team_name'].to_dict()
    bat_team = df['batting_team_id'].map(tmap)
    bowl_team = df['bowling_team_id'].map(tmap)
    is_ipl = df['match_format'] == 'T20'
    is_fm = (~is_ipl) & bat_team.isin(FULL_MEMBER_TEAMS) & bowl_team.isin(FULL_MEMBER_TEAMS)
    is_mixed = (~is_ipl) & (~is_fm) & (bat_team.isin(FULL_MEMBER_TEAMS) | bowl_team.isin(FULL_MEMBER_TEAMS))
    df['comp_tier'] = np.where(
        is_ipl, 'T1_IPL', np.where(is_fm, 'T1_FM_T20I', np.where(is_mixed, 'T2_MIXED', 'T3_ASSOC'))
    )
    df['tier_weight'] = df['comp_tier'].map(COMP_TIER_WEIGHTS).fillna(0.2).astype(float)
    return df


def _fit_ridge_state_residuals(bbb: pd.DataFrame, resolver: PlayerIdentityResolver) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute state-conditional baselines + Ridge opponent/match-par residuals for bowling and batting."""
    df = bbb.copy()
    df['batter_runs'] = pd.to_numeric(df['batter_runs'], errors='coerce').fillna(0.0)
    if 'extras_category' in df.columns:
        df['bowler_runs_conceded'] = df['batter_runs'] + df['extras_category'].isin(['wide', 'Overstep']).astype(float)
    else:
        df['bowler_runs_conceded'] = df['batter_runs']

    non_bowler = ['Run Out', 'RunOut', 'Retired Out', 'Retire Out', 'Obstructing the field', 'Obstracting the field']
    if 'is_wicket' in df.columns:
        df['is_bowler_wicket'] = (df['is_wicket'] == True) & (~df.get('dismissal_type', pd.Series(dtype=str)).isin(non_bowler))
    else:
        df['is_bowler_wicket'] = False

    def _resolve_dismissed(val):
        if pd.isna(val):
            return None
        try:
            raw_id = str(int(float(val)))
        except (ValueError, TypeError):
            raw_id = str(val).strip()
        return resolver.resolve_id(raw_id)

    df['canonical_dismissed_id'] = df['dismissed_player_id'].apply(_resolve_dismissed)
    df['is_striker_out'] = (df['is_wicket'] == True) & (
        df['canonical_dismissed_id'].astype(str) == df['striker_id'].astype(str)
    )
    df['wkt_bucket'] = np.where(
        df['wickets_fallen_before'] <= 2, 'low_wkt',
        np.where(df['wickets_fallen_before'] <= 5, 'mid_wkt', 'tail_wkt')
    )
    state_cols = ['comp_tier', 'innings', 'innings_phase', 'wkt_bucket']

    # Bowling state baseline
    st_bowl = df.groupby(state_cols).agg(
        s_runs=('bowler_runs_conceded', 'sum'),
        s_leg=('is_legal_ball', 'sum'),
        s_wkts=('is_bowler_wicket', 'sum'),
    ).reset_index()
    st_bowl['st_mu_rpb'] = st_bowl['s_runs'] / np.maximum(1.0, st_bowl['s_leg'])
    st_bowl['st_mu_wkt'] = st_bowl['s_wkts'] / np.maximum(1.0, st_bowl['s_leg'])
    df = df.merge(st_bowl[state_cols + ['st_mu_rpb', 'st_mu_wkt']], on=state_cols, how='left')

    # Tier-weighted Ridge regression on legal-ball run residuals:
    # (batter_runs - st_mu_rpb) ~ striker_offense + bowler_defense + match_par
    leg_df = df.loc[df['is_legal_ball'] == True, ['match_id', 'striker_id', 'bowler_id', 'batter_runs', 'st_mu_rpb', 'tier_weight']]
    bat_ids = np.sort(leg_df['striker_id'].unique())
    bowl_ids = np.sort(leg_df['bowler_id'].unique())
    match_ids = np.sort(leg_df['match_id'].unique())
    bat_idx_map = {pid: i for i, pid in enumerate(bat_ids)}
    bowl_idx_map = {pid: i for i, pid in enumerate(bowl_ids)}
    m_idx_map = {mid: i for i, mid in enumerate(match_ids)}

    n_rows = len(leg_df)
    r_rows = np.arange(n_rows)
    w_sqrt = np.sqrt(leg_df['tier_weight'].values.astype(float))
    X_bat = csr_matrix((w_sqrt, (r_rows, leg_df['striker_id'].map(bat_idx_map).values)), shape=(n_rows, len(bat_ids)))
    X_bowl = csr_matrix((w_sqrt, (r_rows, leg_df['bowler_id'].map(bowl_idx_map).values)), shape=(n_rows, len(bowl_ids)))
    X_match = csr_matrix((w_sqrt, (r_rows, leg_df['match_id'].map(m_idx_map).values)), shape=(n_rows, len(match_ids)))
    X = hstack([X_bat, X_bowl, X_match]).tocsr()
    y_res = w_sqrt * (leg_df['batter_runs'].values.astype(float) - leg_df['st_mu_rpb'].values.astype(float))

    sol = lsqr(X, y_res, damp=12.0, atol=1e-5, btol=1e-5)[0]
    bat_off = sol[:len(bat_ids)]
    bowl_def = sol[len(bat_ids):len(bat_ids) + len(bowl_ids)]
    match_par = sol[len(bat_ids) + len(bowl_ids):]

    bat_off_map = dict(zip(bat_ids, bat_off))
    bowl_def_map = dict(zip(bowl_ids, bowl_def))
    match_par_map = dict(zip(match_ids, match_par))

    df['opp_bat_rpb'] = df['striker_id'].map(bat_off_map).fillna(0.0)
    df['opp_bowl_rpb'] = df['bowler_id'].map(bowl_def_map).fillna(0.0)
    df['ridge_match_par'] = df['match_id'].map(match_par_map).fillna(0.0)

    df['exp_rpb_for_bowl'] = np.clip(df['st_mu_rpb'] + df['ridge_match_par'] + df['opp_bat_rpb'], 0.5, 2.8)
    df['v_wkt_bowl'] = df['innings_phase'].map(V_WKT_BOWL_BY_PHASE).fillna(4.5)
    is_leg_f = df['is_legal_ball'].astype(float)
    df['is_legal_ball_float'] = is_leg_f
    df['bowl_rv'] = (
        (df['exp_rpb_for_bowl'] * is_leg_f - df['bowler_runs_conceded'])
        + df['v_wkt_bowl'] * (df['is_bowler_wicket'].astype(float) - df['st_mu_wkt'] * is_leg_f)
    )
    df['r_ctrl'] = df['bowl_rv'] * 6.0  # Runs saved per over equivalence for compatibility
    df['r_wkt'] = 100.0 * (df['is_bowler_wicket'].astype(float) - df['st_mu_wkt'] * is_leg_f)

    # Batting expectation & unified run value per 100 balls
    faced = df[df['is_ball_faced'] == True].copy()
    st_bat = faced.groupby(state_cols).agg(
        st_mu_bat_rpb=('batter_runs', 'mean'),
        st_mu_bat_out=('is_striker_out', 'mean'),
    ).reset_index()
    faced = faced.merge(st_bat, on=state_cols, how='left')
    faced['exp_rpb_for_bat'] = np.clip(
        faced['st_mu_bat_rpb'] + faced['ridge_match_par'] + faced['opp_bowl_rpb'], 0.5, 2.8
    )
    faced['v_wkt_bat'] = faced['innings_phase'].map(V_WKT_BAT_BY_PHASE).fillna(3.5)
    faced['bat_rv100'] = (
        100.0 * (faced['batter_runs'] - faced['exp_rpb_for_bat'])
        + 100.0 * faced['v_wkt_bat'] * (faced['st_mu_bat_out'] - faced['is_striker_out'].astype(float))
    )
    faced['r_bat'] = faced['bat_rv100']

    return df, faced


def load_verified_deliveries() -> pd.DataFrame:
    """Load or rebuild verified delivery dataset with canonical IDs and V4 calibrated pressure features."""
    press_path = DATA_DIR / "features" / "ball_by_ball_with_pressure.parquet"
    ctx_path = DATA_DIR / "features" / "ball_by_ball_with_context.parquet"
    resolver = PlayerIdentityResolver()

    rebuild_needed = True
    if press_path.exists():
        try:
            df = pd.read_parquet(press_path)
            req = [
                'canonical_striker_id', 'canonical_bowler_id', 'batting_pressure_data_valid',
                'bowling_pressure_data_valid', 'is_batting_high_pressure', 'is_bowling_high_pressure',
                'v3_pressure_formula_version', 'clean_rrr_deficit', 'comp_tier', 'tier_weight',
                'batting_leverage_raw', 'bowling_leverage_raw',
            ]
            if all(c in df.columns for c in req) and len(df) == 193988:
                if (str(df['v3_pressure_formula_version'].iloc[0]) == 'V4_CALIBRATED_RIDGE'
                        and int(df['batting_pressure_data_valid'].sum()) == len(df)):
                    rebuild_needed = False
                    logging.info(f"Loaded verified V4 pressure parquet ({len(df)} rows)")
        except Exception as e:
            logging.warning(f"Error reading {press_path}: {e}. Rebuilding...")

    if rebuild_needed:
        logging.info("Rebuilding ball_by_ball_with_context.parquet and ball_by_ball_with_pressure.parquet (V4)...")
        from src.ingestion.loader import load_all_data
        from src.preprocessing.cleaner import clean_all
        from src.context_engine.innings_context import build_innings_context
        from src.context_engine.delivery_context import build_delivery_context
        from src.context_engine.partnership_tracker import build_partnerships

        raw_data = load_all_data()
        df_regular, _ = clean_all(raw_data['ball_by_ball'], raw_data['matches'])
        df = build_innings_context(df_regular, matches_df=raw_data['matches'])
        df = build_delivery_context(df)
        df = build_partnerships(df)
        df = _attach_competition_tiers(df, raw_data['teams'])
        df.to_parquet(ctx_path, index=False)

        df = resolver.resolve_deliveries(df)
        df = V3PressureModel.apply_dual_pressure(df)
        df['v3_pressure_schema_version'] = 'V4_CANONICAL'
        df['v3_pressure_formula_version'] = 'V4_CALIBRATED_RIDGE'
        df.to_parquet(press_path, index=False)
        logging.info(f"Saved rebuilt V4 {press_path} ({len(df)} rows)")

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
    # 1. V4 STATE + RIDGE RESIDUALS & BATTING PIPELINE
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Fitting V4 State-Conditional Baselines & Weighted Ridge Opponent/Match-Par...")
    bbb['is_bnd'] = (bbb['is_four_validated'] == True) | (bbb['is_six_validated'] == True)
    bbb, faced = _fit_ridge_state_residuals(bbb, resolver)
    faced['is_tier1'] = faced['comp_tier'].isin(['T1_IPL', 'T1_FM_T20I'])

    logging.info("Aggregating Universal Batting Intelligence (V4)...")
    # Mutually exclusive pressure sets (only valid pressure records)
    p_high = faced[(faced['batting_pressure_data_valid'] == True) & (faced['is_batting_high_pressure'] == True)]
    p_norm = faced[(faced['batting_pressure_data_valid'] == True) & (faced['is_batting_normal_pressure'] == True)]

    def _agg_bat(tier_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        cols = [
            'striker_id', f'{prefix}_balls', f'eff_{prefix}_balls', f'{prefix}_runs',
            f'{prefix}_sr', f'{prefix}_outs', f'{prefix}_out_pct', f'{prefix}_r_bat',
            f'{prefix}_matches'
        ]
        if len(tier_df) == 0:
            return pd.DataFrame(columns=cols)
        agg = (
            tier_df.assign(_rv_w=tier_df['bat_rv100'] * tier_df['tier_weight'])
            .groupby('striker_id')
            .agg(
                balls=('batter_runs', 'count'),
                eff_balls=('tier_weight', 'sum'),
                runs=('batter_runs', 'sum'),
                outs=('is_striker_out', 'sum'),
                rv_w_sum=('_rv_w', 'sum'),
                matches=('match_id', 'nunique'),
            )
            .reset_index()
        )
        agg[f'{prefix}_balls'] = agg['balls']
        agg[f'eff_{prefix}_balls'] = agg['eff_balls'].round(2)
        agg[f'{prefix}_runs'] = agg['runs']
        agg[f'{prefix}_sr'] = np.where(agg['balls'] > 0, (agg['runs'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_outs'] = agg['outs']
        agg[f'{prefix}_out_pct'] = np.where(agg['balls'] > 0, (agg['outs'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_r_bat'] = np.where(agg['eff_balls'] > 0, agg['rv_w_sum'] / agg['eff_balls'], np.nan)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[cols]

    df_high_bat = _agg_bat(p_high, 'crisis')
    df_norm_bat = _agg_bat(p_norm, 'norm')

    df_tot_bat = faced.groupby('striker_id').agg(
        total_balls=('batter_runs', 'count'),
        total_runs=('batter_runs', 'sum'),
        tier1_balls=('is_tier1', 'sum'),
        total_matches=('match_id', 'nunique')
    ).reset_index()
    df_tot_bat['total_sr'] = np.where(
        df_tot_bat['total_balls'] > 0,
        (df_tot_bat['total_runs'] / df_tot_bat['total_balls']) * 100.0,
        np.nan
    )
    df_tot_bat['tier1_share'] = np.where(
        df_tot_bat['total_balls'] > 0,
        (df_tot_bat['tier1_balls'] / df_tot_bat['total_balls']).round(4),
        0.0
    )

    bat_master = df_tot_bat.merge(df_high_bat, on='striker_id', how='left')
    bat_master = bat_master.merge(df_norm_bat, on='striker_id', how='left')

    # Fill count fields with 0; performance rates remain NaN if balls == 0
    count_cols = ['crisis_balls', 'crisis_runs', 'crisis_outs', 'crisis_matches', 'norm_balls', 'norm_runs', 'norm_outs', 'norm_matches']
    for c in count_cols:
        bat_master[c] = pd.to_numeric(bat_master[c], errors='coerce').fillna(0).astype(int)
    for c in ['eff_crisis_balls', 'eff_norm_balls']:
        bat_master[c] = pd.to_numeric(bat_master[c], errors='coerce').fillna(0.0).astype(float)
    for c in ['crisis_sr', 'norm_sr', 'total_sr', 'crisis_out_pct', 'norm_out_pct', 'crisis_r_bat', 'norm_r_bat']:
        bat_master[c] = pd.to_numeric(bat_master[c], errors='coerce').astype(float)

    # Attach Canonical Player Metadata & Roles
    bat_master['canonical_player_id'] = bat_master['striker_id']
    bat_master['player_name'] = bat_master['canonical_player_id'].apply(resolver.resolve_name)
    bat_master['v3_role'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('v3_role', 'UNRESOLVED'))
    bat_master['role_confidence'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('role_confidence', 'LOW'))
    bat_master['modal_order'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('modal_order', 10))
    bat_master['eligible_for_bat_leaderboard'] = bat_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('eligible_for_bat_leaderboard', False))
    bat_master['is_quarantined'] = bat_master['canonical_player_id'].apply(resolver.is_quarantined)

    # Normal comparison validity (Batters: Tier-weighted eff_norm_balls >= 60, no silent imputation)
    norm_elig_bat = []
    norm_status = []
    raw_sr_maints = []
    capped_sr_maints = []
    is_maint_capped_bat = []
    for _, r in bat_master.iterrows():
        nb = r['norm_balls']
        eff_nb = r['eff_norm_balls']
        nsr = r['norm_sr']
        csr = r['crisis_sr']
        if eff_nb >= DEFAULT_BAT_THRESHOLDS['norm_balls'] and nb > 0 and pd.notna(nsr) and float(nsr) > 0:
            norm_elig_bat.append(True)
            norm_status.append('VALID_NORMAL_BASELINE')
            if pd.notna(csr):
                raw_val = float(csr) / float(nsr)
                cap_val = float(np.clip(raw_val, 0.5, 1.5))
                raw_sr_maints.append(round(raw_val, 3))
                capped_sr_maints.append(round(cap_val, 3))
                is_maint_capped_bat.append(bool(raw_val > 1.5 or raw_val < 0.5))
            else:
                raw_sr_maints.append(np.nan)
                capped_sr_maints.append(np.nan)
                is_maint_capped_bat.append(False)
        elif nb > 0:
            norm_elig_bat.append(False)
            norm_status.append('INSUFFICIENT_NORMAL_EXPOSURE')
            if pd.notna(nsr) and float(nsr) > 0 and pd.notna(csr):
                raw_sr_maints.append(round(float(csr) / float(nsr), 3))
            else:
                raw_sr_maints.append(np.nan)
            capped_sr_maints.append(np.nan)
            is_maint_capped_bat.append(False)
        else:
            norm_elig_bat.append(False)
            norm_status.append('NO_NORMAL_EXPOSURE')
            raw_sr_maints.append(np.nan)
            capped_sr_maints.append(np.nan)
            is_maint_capped_bat.append(False)

    bat_master['norm_baseline_eligible'] = norm_elig_bat
    bat_master['norm_baseline_status'] = norm_status
    bat_master['raw_sr_maintenance'] = raw_sr_maints
    bat_master['capped_sr_maintenance'] = capped_sr_maints
    bat_master['sr_maintenance'] = capped_sr_maints
    bat_master['is_maintenance_capped'] = is_maint_capped_bat

    # Sample Eligibility (V4): eff_crisis >= 60, eff_norm >= 60, total >= 200, crisis_matches >= 6, tier1_share >= 0.60
    c_cb = bat_master['eff_crisis_balls'] >= DEFAULT_BAT_THRESHOLDS['crisis_balls']
    c_tb = bat_master['total_balls'] >= DEFAULT_BAT_THRESHOLDS['total_balls']
    c_cm = bat_master['crisis_matches'] >= DEFAULT_BAT_THRESHOLDS['crisis_matches']
    c_nb = bat_master['norm_baseline_eligible']
    c_t1 = bat_master['tier1_share'] >= MIN_TIER1_SHARE
    c_not_quar = ~bat_master['is_quarantined']

    bat_master['sample_eligible'] = c_cb & c_tb & c_cm & c_nb & c_t1 & c_not_quar
    bat_master['eligibility_status'] = np.where(
        bat_master['sample_eligible'], 'ELIGIBLE',
        np.where(bat_master['is_quarantined'], 'IDENTITY_CONFLICT_QUARANTINE',
                 np.where(bat_master['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE'))
    )
    bat_master['final_eligibility'] = np.where(
        bat_master['sample_eligible'] & bat_master['eligible_for_bat_leaderboard'] & (~bat_master['is_quarantined']),
        'ELIGIBLE', 'INELIGIBLE'
    )

    def _bat_exclusion_reason(r):
        reasons = []
        if r['is_quarantined']:
            reasons.append('IDENTITY_CONFLICT')
        if r['eff_crisis_balls'] < DEFAULT_BAT_THRESHOLDS['crisis_balls']:
            reasons.append(f"EFF_CRISIS_BALLS<{DEFAULT_BAT_THRESHOLDS['crisis_balls']}")
        if r['total_balls'] < DEFAULT_BAT_THRESHOLDS['total_balls']:
            reasons.append(f"TOTAL_BALLS<{DEFAULT_BAT_THRESHOLDS['total_balls']}")
        if r['crisis_matches'] < DEFAULT_BAT_THRESHOLDS['crisis_matches']:
            reasons.append(f"CRISIS_MATCHES<{DEFAULT_BAT_THRESHOLDS['crisis_matches']}")
        if not r['norm_baseline_eligible']:
            reasons.append(f"EFF_NORM_BALLS<{DEFAULT_BAT_THRESHOLDS['norm_balls']}")
        if r['tier1_share'] < MIN_TIER1_SHARE:
            reasons.append(f"TIER1_SHARE<{MIN_TIER1_SHARE:.2f}")
        if not r['eligible_for_bat_leaderboard']:
            reasons.append(f"INELIGIBLE_ROLE_{r['v3_role']}")
        return "; ".join(reasons) if reasons else 'NONE'

    bat_master['exclusion_reasons'] = bat_master.apply(_bat_exclusion_reason, axis=1)

    # Auxiliary Shrunk Crisis SR with explicit eligible prior population
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

    bat_master['crisis_sr_vs_cohort_mean'] = (bat_master['crisis_sr'] - bat_master['prior_mean']).round(2)
    bat_master['crisis_sr_below_cohort_mean'] = bat_master['crisis_sr'] < bat_master['prior_mean']
    bat_master['performance_anomaly_flag'] = np.where(
        bat_master['crisis_sr'].isna(), 'NO_CRISIS_SAMPLE',
        np.where(bat_master['crisis_sr_below_cohort_mean'], 'CRISIS_SR_BELOW_COHORT_MEAN', 'NONE')
    )

    # V4 Dual-arm EB shrinkage & cohort-calibrated DiD maintenance on Tier-weighted Ridge Run Value/100
    c_delta_bat, n_delta_bat, did_bat = V3ReliabilityEngine.phase_adjusted_dual_arm_did(
        bat_master['crisis_r_bat'],
        bat_master['eff_crisis_balls'],
        bat_master['norm_r_bat'],
        bat_master['eff_norm_balls'],
        k_crisis=90.0,
        k_norm=90.0,
        floor_normal_at_zero=False,
        min_norm_ref=-5.0,
        cohort_calibrated=True,
        cohort_mask=prior_bat_mask,
    )
    bat_master['crisis_delta_rv'] = c_delta_bat.round(2)
    bat_master['norm_delta_rv'] = n_delta_bat.round(2)
    bat_master['did_bat_maintenance'] = did_bat.round(2)

    # Sample Confidence
    bat_master['sample_confidence'] = np.clip(
        np.log1p(bat_master['eff_crisis_balls']) / np.log1p(350.0), 0.1, 1.0
    ).round(4)

    # Value-Gated Downside Match Consistency & Direct Run-Value Bootstrap CI
    logging.info(f"Computing Value-Gated Downside Consistency & Match-Clustered Bootstrap ({n_bootstrap_final} iter) for Batters...")
    bat_clusters = {pid: g for pid, g in p_high.groupby('striker_id')}
    consistencies = []
    ci_lows, ci_highs, uncert_widths = [], [], []
    ci_statuses, ci_methods, ci_conf_levels = [], [], []
    ci_sample_matches, ci_sample_deliveries = [], []

    for _, row in bat_master.iterrows():
        pid = row['canonical_player_id']
        cb = row['crisis_balls']
        cm = row['crisis_matches']
        p_sub = bat_clusters.get(pid)

        if p_sub is None or cb < 45 or cm < 5:
            consistencies.append(0.05)
        else:
            mg = p_sub.groupby('match_id').agg(
                rv=('bat_rv100', 'mean'),
                lb=('batter_runs', 'count'),
                tw=('tier_weight', 'mean'),
            )
            mg = mg[mg['lb'] > 0]
            w_m = (mg['lb'] * mg['tw']).values.astype(float)
            m_rv = mg['rv'].values.astype(float)
            sigma_down = float(np.sqrt(np.average(np.minimum(0.0, m_rv) ** 2, weights=w_m)))
            mean_wm = max(1e-9, float(np.mean(w_m)))
            p_pos = float((np.sum(w_m * (m_rv > 0.0)) + 2.0 * 0.45 * mean_wm) / (np.sum(w_m) + 2.0 * mean_wm))
            m_shrink = np.sqrt(cm / (cm + 10.0))
            c_rv_val = float(row['crisis_r_bat']) if pd.notna(row['crisis_r_bat']) else 0.0
            val_gate = 1.0 / (1.0 + np.exp(-c_rv_val / 8.0))
            c_score = np.clip(np.exp(-sigma_down / 45.0) * p_pos * m_shrink * val_gate, 0.01, 0.98)
            consistencies.append(round(float(c_score), 4))

        boot = V3ReliabilityEngine.match_clustered_bootstrap_metric(
            p_sub if p_sub is not None else p_high.iloc[0:0],
            value_col='bat_rv100',
            weight_col='tier_weight',
            scale=1.0,
            n_bootstraps=n_bootstrap_final,
            random_state=random_state,
            min_matches=3,
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
    bat_master['ci_metric'] = 'CRISIS_RUN_VALUE_PER_100'

    # Normalization across eligible pool (2.5% / 97.5% winsorized z-score mapped to [0, 1])
    el_pool_bat = bat_master[bat_master['sample_eligible'] & bat_master['eligible_for_bat_leaderboard']].copy()
    if len(el_pool_bat) == 0:
        el_pool_bat = bat_master[bat_master['sample_eligible']].copy()
    if len(el_pool_bat) == 0:
        el_pool_bat = bat_master.copy()

    def _winsorized_zscore(s: pd.Series, ref_s: pd.Series) -> pd.Series:
        valid_ref = ref_s.dropna()
        if len(valid_ref) == 0:
            return pd.Series(0.5, index=s.index)
        ql, qh = valid_ref.quantile(0.025), valid_ref.quantile(0.975)
        ref_w = np.clip(valid_ref, ql, qh)
        mu_w = float(ref_w.mean())
        sd_w = float(ref_w.std(ddof=0))
        if sd_w <= 1e-12:
            return pd.Series(0.5, index=s.index)
        return np.clip(((s - mu_w) / sd_w + 2.5) / 5.0, 0.0, 1.0).fillna(0.0)

    bat_master['norm_maint'] = _winsorized_zscore(bat_master['did_bat_maintenance'], el_pool_bat['did_bat_maintenance'])
    bat_master['norm_abs'] = _winsorized_zscore(bat_master['crisis_delta_rv'], el_pool_bat['crisis_delta_rv'])
    bat_master['norm_cons'] = _winsorized_zscore(bat_master['consistency_score'], el_pool_bat['consistency_score'])
    bat_master['norm_sample'] = bat_master['sample_confidence']

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
    bat_master.loc[~bat_master['norm_baseline_eligible'], ['norm_maint', 'contrib_maint', 'batting_pri_provisional']] = np.nan
    bat_master['provisional_fixed_weight_score'] = bat_master['batting_pri_provisional']
    bat_master['batting_pri'] = bat_master['batting_pri_provisional']
    bat_master['formula_status'] = 'V4_CALIBRATED_RIDGE_SCORE'

    def _bat_score_explanation(r):
        if pd.isna(r['provisional_fixed_weight_score']):
            return f"UNRANKED_INSUFFICIENT_BASELINE ({r['norm_baseline_status']})"
        wm = int(round(w['maintenance'] * 100))
        wa = int(round(w['absolute'] * 100))
        wc = int(round(w['consistency'] * 100))
        ws = int(round(w['sample'] * 100))
        base_str = (
            f"Maint({wm}%)={r['contrib_maint']:.2f} + Abs({wa}%)={r['contrib_abs']:.2f} + "
            f"Cons({wc}%)={r['contrib_cons']:.2f} + Sample({ws}%)={r['contrib_sample']:.2f} = {r['provisional_fixed_weight_score']:.2f}"
        )
        if r['crisis_sr_below_cohort_mean']:
            return (
                f"CRISIS_SR_BELOW_COHORT_MEAN ({r['crisis_sr']:.2f} vs cohort mean {r['prior_mean']:.2f}): "
                f"{base_str}; evaluated via Ridge Run Value/100 ({r['crisis_delta_rv']:+.2f} crisis, DiD {r['did_bat_maintenance']:+.2f})."
            )
        return base_str

    bat_master['component_breakdown_explanation'] = bat_master.apply(_bat_score_explanation, axis=1)

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
    # 2. BOWLING RANKINGS PIPELINE (V4 UNIFIED RUNS SAVED PER OVER)
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Aggregating Universal Bowling Intelligence (V4)...")
    bbb['is_tier1_legal'] = (bbb['is_legal_ball'] == True) & bbb['comp_tier'].isin(['T1_IPL', 'T1_FM_T20I'])

    # Keep all deliveries (including wides & no-balls) so bowler_runs_conceded & bowl_rv capture extra penalties
    p_high_bowl = bbb[(bbb['bowling_pressure_data_valid'] == True) & (bbb['is_bowling_high_pressure'] == True)]
    p_norm_bowl = bbb[(bbb['bowling_pressure_data_valid'] == True) & (bbb['is_bowling_normal_pressure'] == True)]

    def _agg_bowl(tier_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        cols = [
            'bowler_id', f'{prefix}_balls', f'eff_{prefix}_balls', f'{prefix}_runs',
            f'{prefix}_econ', f'{prefix}_wickets', f'{prefix}_dot_pct', f'{prefix}_bnd_pct',
            f'{prefix}_wicket_rate', f'{prefix}_r_rv', f'{prefix}_r_ctrl', f'{prefix}_r_wkt',
            f'{prefix}_matches'
        ]
        if len(tier_df) == 0:
            return pd.DataFrame(columns=cols)
        leg_tw = tier_df['is_legal_ball_float'] * tier_df['tier_weight']
        agg = (
            tier_df.assign(
                _leg_tw=leg_tw,
                _rv_w=tier_df['bowl_rv'] * tier_df['tier_weight'],
                _ctrl_w=tier_df['r_ctrl'] * tier_df['tier_weight'],
                _wkt_w=tier_df['r_wkt'] * tier_df['tier_weight'],
            )
            .groupby('bowler_id')
            .agg(
                balls=('is_legal_ball', 'sum'),
                eff_balls=('_leg_tw', 'sum'),
                runs=('bowler_runs_conceded', 'sum'),
                wickets=('is_bowler_wicket', 'sum'),
                dots=('is_dot_ball', 'sum'),
                bnds=('is_bnd', 'sum'),
                rv_w_sum=('_rv_w', 'sum'),
                ctrl_w_sum=('_ctrl_w', 'sum'),
                wkt_w_sum=('_wkt_w', 'sum'),
                matches=('match_id', 'nunique'),
            )
            .reset_index()
        )
        agg[f'{prefix}_balls'] = agg['balls']
        agg[f'eff_{prefix}_balls'] = agg['eff_balls'].round(2)
        agg[f'{prefix}_runs'] = agg['runs']
        agg[f'{prefix}_econ'] = np.where(agg['balls'] > 0, (agg['runs'] / agg['balls']) * 6.0, np.nan)
        agg[f'{prefix}_wickets'] = agg['wickets']
        agg[f'{prefix}_dot_pct'] = np.where(agg['balls'] > 0, (agg['dots'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_bnd_pct'] = np.where(agg['balls'] > 0, (agg['bnds'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_wicket_rate'] = np.where(agg['balls'] > 0, (agg['wickets'] / agg['balls']) * 100.0, np.nan)
        agg[f'{prefix}_r_rv'] = np.where(agg['eff_balls'] > 0, (agg['rv_w_sum'] / agg['eff_balls']) * 6.0, np.nan)
        agg[f'{prefix}_r_ctrl'] = np.where(agg['eff_balls'] > 0, agg['ctrl_w_sum'] / agg['eff_balls'] * 6.0, np.nan)
        agg[f'{prefix}_r_wkt'] = np.where(agg['eff_balls'] > 0, agg['wkt_w_sum'] / agg['eff_balls'], np.nan)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[cols]

    df_high_bowl = _agg_bowl(p_high_bowl, 'crisis')
    df_norm_bowl = _agg_bowl(p_norm_bowl, 'norm')

    df_tot_bowl = bbb.groupby('bowler_id').agg(
        total_legal_balls=('is_legal_ball', 'sum'),
        total_runs_conceded=('bowler_runs_conceded', 'sum'),
        total_wickets=('is_bowler_wicket', 'sum'),
        total_dots=('is_dot_ball', 'sum'),
        tier1_legal_balls=('is_tier1_legal', 'sum'),
        total_matches=('match_id', 'nunique')
    ).reset_index()
    df_tot_bowl['total_dot_pct'] = np.where(
        df_tot_bowl['total_legal_balls'] > 0,
        (df_tot_bowl['total_dots'] / df_tot_bowl['total_legal_balls']) * 100.0,
        np.nan
    )
    df_tot_bowl['tier1_share'] = np.where(
        df_tot_bowl['total_legal_balls'] > 0,
        (df_tot_bowl['tier1_legal_balls'] / df_tot_bowl['total_legal_balls']).round(4),
        0.0
    )

    bowl_master = df_tot_bowl.merge(df_high_bowl, on='bowler_id', how='left')
    bowl_master = bowl_master.merge(df_norm_bowl, on='bowler_id', how='left')

    for c in ['crisis_balls', 'crisis_wickets', 'crisis_matches', 'norm_balls', 'norm_wickets', 'norm_matches', 'total_legal_balls']:
        bowl_master[c] = pd.to_numeric(bowl_master[c], errors='coerce').fillna(0).astype(int)
    for c in ['crisis_runs', 'norm_runs', 'eff_crisis_balls', 'eff_norm_balls']:
        bowl_master[c] = pd.to_numeric(bowl_master[c], errors='coerce').fillna(0.0).astype(float)
    for c in [
        'crisis_econ', 'norm_econ', 'crisis_dot_pct', 'crisis_bnd_pct', 'crisis_wicket_rate',
        'norm_dot_pct', 'norm_bnd_pct', 'norm_wicket_rate', 'total_dot_pct',
        'crisis_r_rv', 'norm_r_rv', 'crisis_r_ctrl', 'norm_r_ctrl', 'crisis_r_wkt', 'norm_r_wkt'
    ]:
        bowl_master[c] = pd.to_numeric(bowl_master[c], errors='coerce').astype(float)

    # Attach Canonical Player Metadata & Roles
    bowl_master['canonical_player_id'] = bowl_master['bowler_id']
    bowl_master['player_name'] = bowl_master['canonical_player_id'].apply(resolver.resolve_name)
    bowl_master['v3_role'] = bowl_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('v3_role', 'UNRESOLVED'))
    bowl_master['role_confidence'] = bowl_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('role_confidence', 'LOW'))
    bowl_master['eligible_for_bowl_leaderboard'] = bowl_master['canonical_player_id'].apply(lambda pid: role_map.get(pid, {}).get('eligible_for_bowl_leaderboard', False))
    bowl_master['is_quarantined'] = bowl_master['canonical_player_id'].apply(resolver.is_quarantined)

    # Normal comparison validity for Bowlers (Strict V4 Gate: eff_norm_balls >= 100, zero weight-shift loophole)
    norm_elig_b = []
    norm_status_b = []
    raw_dot_maints = []
    capped_dot_maints = []
    is_maint_capped_b = []
    for _, r in bowl_master.iterrows():
        nb = r['norm_balls']
        eff_nb = r['eff_norm_balls']
        ndot = r['norm_dot_pct']
        cdot = r['crisis_dot_pct']
        if nb > 0 and pd.notna(ndot) and float(ndot) > 0 and pd.notna(cdot):
            raw_val = round(float(cdot) / float(ndot), 3)
        else:
            raw_val = np.nan

        if eff_nb >= MIN_NORMAL_BALLS_BOWLER and nb > 0 and pd.notna(ndot) and float(ndot) > 0:
            norm_elig_b.append(True)
            norm_status_b.append('VALID_NORMAL_BASELINE')
            raw_dot_maints.append(raw_val)
            if pd.notna(raw_val):
                cap_val = round(float(np.clip(float(cdot) / float(ndot), 0.5, 1.5)), 3)
                capped_dot_maints.append(cap_val)
                is_maint_capped_b.append(bool((float(cdot) / float(ndot) > 1.5) or (float(cdot) / float(ndot) < 0.5)))
            else:
                capped_dot_maints.append(np.nan)
                is_maint_capped_b.append(False)
        elif nb > 0:
            norm_elig_b.append(False)
            norm_status_b.append('INSUFFICIENT_NORMAL_EXPOSURE')
            raw_dot_maints.append(raw_val)
            capped_dot_maints.append(np.nan)
            is_maint_capped_b.append(False)
        else:
            norm_elig_b.append(False)
            norm_status_b.append('NO_NORMAL_EXPOSURE')
            raw_dot_maints.append(np.nan)
            capped_dot_maints.append(np.nan)
            is_maint_capped_b.append(False)

    bowl_master['norm_baseline_eligible'] = norm_elig_b
    bowl_master['norm_baseline_status'] = norm_status_b
    bowl_master['raw_dot_maintenance'] = raw_dot_maints
    bowl_master['capped_dot_maintenance'] = capped_dot_maints
    bowl_master['dot_maintenance'] = capped_dot_maints
    bowl_master['is_maintenance_capped'] = is_maint_capped_b

    # Sample Eligibility (V4): eff_crisis >= 120, eff_norm >= 100, total >= 250, crisis_matches >= 6, tier1_share >= 0.60
    c_b_cb = bowl_master['eff_crisis_balls'] >= DEFAULT_BOWL_THRESHOLDS['crisis_balls']
    c_b_nb = bowl_master['norm_baseline_eligible']
    c_b_tb = bowl_master['total_legal_balls'] >= DEFAULT_BOWL_THRESHOLDS['total_legal_balls']
    c_b_cm = bowl_master['crisis_matches'] >= DEFAULT_BOWL_THRESHOLDS['crisis_matches']
    c_b_t1 = bowl_master['tier1_share'] >= MIN_TIER1_SHARE
    c_b_not_quar = ~bowl_master['is_quarantined']

    bowl_master['sample_eligible'] = c_b_cb & c_b_nb & c_b_tb & c_b_cm & c_b_t1 & c_b_not_quar
    bowl_master['eligibility_status'] = np.where(
        bowl_master['sample_eligible'], 'ELIGIBLE',
        np.where(bowl_master['is_quarantined'], 'IDENTITY_CONFLICT_QUARANTINE',
                 np.where(bowl_master['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE'))
    )
    bowl_master['final_eligibility'] = np.where(
        bowl_master['sample_eligible'] & bowl_master['eligible_for_bowl_leaderboard'] & (~bowl_master['is_quarantined']),
        'ELIGIBLE', 'INELIGIBLE'
    )

    def _bowl_exclusion_reason(r):
        reasons = []
        if r['is_quarantined']:
            reasons.append('IDENTITY_CONFLICT')
        if r['eff_crisis_balls'] < DEFAULT_BOWL_THRESHOLDS['crisis_balls']:
            reasons.append(f"EFF_CRISIS_BALLS<{DEFAULT_BOWL_THRESHOLDS['crisis_balls']}")
        if not r['norm_baseline_eligible']:
            reasons.append(f"EFF_NORM_BALLS<{DEFAULT_BOWL_THRESHOLDS['norm_balls']}")
        if r['total_legal_balls'] < DEFAULT_BOWL_THRESHOLDS['total_legal_balls']:
            reasons.append(f"TOTAL_LEGAL_BALLS<{DEFAULT_BOWL_THRESHOLDS['total_legal_balls']}")
        if r['crisis_matches'] < DEFAULT_BOWL_THRESHOLDS['crisis_matches']:
            reasons.append(f"CRISIS_MATCHES<{DEFAULT_BOWL_THRESHOLDS['crisis_matches']}")
        if r['tier1_share'] < MIN_TIER1_SHARE:
            reasons.append(f"TIER1_SHARE<{MIN_TIER1_SHARE:.2f}")
        if not r['eligible_for_bowl_leaderboard']:
            reasons.append(f"INELIGIBLE_ROLE_{r['v3_role']}")
        return "; ".join(reasons) if reasons else 'NONE'

    bowl_master['exclusion_reasons'] = bowl_master.apply(_bowl_exclusion_reason, axis=1)

    # Auxiliary Shrunk Crisis Wicket Rate (Beta-Binomial) on strictly eligible frontline population
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

    # V4 Unified Runs Saved per Over (k=150) & Cohort-Calibrated DiD Maintenance
    c_delta_rv_b, n_delta_rv_b, did_bowl = V3ReliabilityEngine.phase_adjusted_dual_arm_did(
        bowl_master['crisis_r_rv'],
        bowl_master['eff_crisis_balls'],
        bowl_master['norm_r_rv'],
        bowl_master['eff_norm_balls'],
        k_crisis=150.0,
        k_norm=150.0,
        floor_normal_at_zero=False,
        min_norm_ref=-0.5,
        cohort_calibrated=True,
        allow_prior_anchored=False,
        cohort_mask=prior_bowl_mask,
    )
    bowl_master['crisis_delta_rv'] = c_delta_rv_b.round(2)
    bowl_master['norm_delta_rv'] = n_delta_rv_b.round(2)
    bowl_master['crisis_delta_ctrl'] = bowl_master['crisis_delta_rv']
    bowl_master['norm_delta_ctrl'] = bowl_master['norm_delta_rv']
    bowl_master['did_bowl_maintenance'] = did_bowl.round(2)
    c_delta_wkt = np.where(
        (bowl_master['crisis_balls'] > 0) & bowl_master['crisis_r_wkt'].notna(),
        (bowl_master['crisis_balls'] / (bowl_master['crisis_balls'] + 150.0)) * bowl_master['crisis_r_wkt'],
        np.nan,
    )
    bowl_master['crisis_delta_wkt'] = pd.Series(c_delta_wkt, index=bowl_master.index).round(3)
    bowl_master['abs_bowl_score'] = bowl_master['crisis_delta_rv']

    # Sample Confidence
    bowl_master['sample_confidence'] = np.clip(
        np.log1p(bowl_master['eff_crisis_balls']) / np.log1p(600.0), 0.1, 1.0
    ).round(4)

    # Value-Gated Downside Match Consistency & Direct Run-Value Bootstrap CI
    logging.info(f"Computing Value-Gated Downside Consistency & Match-Clustered Bootstrap ({n_bootstrap_final} iter) for Bowlers...")
    bowl_clusters = {bid: g for bid, g in p_high_bowl.groupby('bowler_id')}
    b_consistencies = []
    b_ci_lows, b_ci_highs, b_uncert_widths = [], [], []
    b_ci_statuses, b_ci_methods, b_ci_conf_levels = [], [], []
    b_ci_sample_matches, b_ci_sample_deliveries = [], []

    for _, row in bowl_master.iterrows():
        bid = row['canonical_player_id']
        cb = row['crisis_balls']
        cm = row['crisis_matches']
        p_sub = bowl_clusters.get(bid)

        if p_sub is None or cb < 60 or cm < 5:
            b_consistencies.append(0.05)
        else:
            mg = p_sub.groupby('match_id').agg(
                rv=('bowl_rv', 'sum'),
                lb=('is_legal_ball', 'sum'),
                tw=('tier_weight', 'mean'),
            )
            mg = mg[mg['lb'] > 0]
            if len(mg) == 0:
                b_consistencies.append(0.05)
            else:
                m_rv = (mg['rv'] / mg['lb']).values.astype(float) * 6.0
                w_m = (mg['lb'] * mg['tw']).values.astype(float)
                sigma_down = float(np.sqrt(np.average(np.minimum(0.0, m_rv) ** 2, weights=w_m)))
                mean_wm = max(1e-9, float(np.mean(w_m)))
                p_pos = float((np.sum(w_m * (m_rv > 0.0)) + 2.0 * 0.45 * mean_wm) / (np.sum(w_m) + 2.0 * mean_wm))
                m_shrink = np.sqrt(cm / (cm + 10.0))
                c_rv_val = float(row['crisis_r_rv']) if pd.notna(row['crisis_r_rv']) else 0.0
                val_gate = 1.0 / (1.0 + np.exp(-c_rv_val / 0.6))
                c_score = np.clip(np.exp(-sigma_down / 3.0) * p_pos * m_shrink * val_gate, 0.01, 0.98)
                b_consistencies.append(round(float(c_score), 4))

        boot = V3ReliabilityEngine.match_clustered_bootstrap_metric(
            p_sub if p_sub is not None else p_high_bowl.iloc[0:0],
            value_col='bowl_rv',
            weight_col='tier_weight',
            denom_col='is_legal_ball_float',
            scale=6.0,
            n_bootstraps=n_bootstrap_final,
            random_state=random_state,
            min_matches=3,
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
    bowl_master['ci_metric'] = 'CRISIS_RUNS_SAVED_PER_OVER'

    el_pool_bowl = bowl_master[bowl_master['sample_eligible'] & bowl_master['eligible_for_bowl_leaderboard']].copy()
    if len(el_pool_bowl) == 0:
        el_pool_bowl = bowl_master[bowl_master['sample_eligible']].copy()
    if len(el_pool_bowl) == 0:
        el_pool_bowl = bowl_master.copy()

    bowl_master['norm_maint'] = _winsorized_zscore(bowl_master['did_bowl_maintenance'], el_pool_bowl['did_bowl_maintenance'])
    bowl_master['norm_abs'] = _winsorized_zscore(bowl_master['abs_bowl_score'], el_pool_bowl['abs_bowl_score'])
    bowl_master['norm_cons'] = _winsorized_zscore(bowl_master['consistency_score'], el_pool_bowl['consistency_score'])
    bowl_master['norm_sample'] = bowl_master['sample_confidence']

    # Strictly invariant V4 weights across ALL eligible bowlers (zero weight reallocation loophole)
    bowl_master['effective_w_maint'] = np.round(w['maintenance'], 4)
    bowl_master['effective_w_abs'] = np.round(w['absolute'], 4)
    bowl_master['effective_w_cons'] = np.round(w['consistency'], 4)

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
    bowl_master.loc[~bowl_master['norm_baseline_eligible'], ['norm_maint', 'contrib_maint', 'bowling_pri_provisional']] = np.nan
    bowl_master['provisional_fixed_weight_score'] = bowl_master['bowling_pri_provisional']
    bowl_master['bowling_pri'] = bowl_master['bowling_pri_provisional']
    bowl_master['formula_status'] = 'V4_CALIBRATED_RIDGE_SCORE'

    def _bowl_score_explanation(r):
        if pd.isna(r['provisional_fixed_weight_score']):
            return f"UNRANKED_INSUFFICIENT_BASELINE ({r['norm_baseline_status']})"
        wm = int(round(w['maintenance'] * 100))
        wa = int(round(w['absolute'] * 100))
        wc = int(round(w['consistency'] * 100))
        ws = int(round(w['sample'] * 100))
        return (
            f"Maint({wm}%)={r['contrib_maint']:.2f} + Abs({wa}%)={r['contrib_abs']:.2f} + "
            f"Cons({wc}%)={r['contrib_cons']:.2f} + Sample({ws}%)={r['contrib_sample']:.2f} = {r['provisional_fixed_weight_score']:.2f}"
        )

    bowl_master['component_breakdown_explanation'] = bowl_master.apply(_bowl_score_explanation, axis=1)

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

    # Attach ranks to master tables and sort deterministically (eligible ranked first, then by score descending)
    bat_rank_map = top_batters_eligible.set_index('canonical_player_id')['rank'].to_dict()
    bat_master['provisional_rank'] = bat_master['canonical_player_id'].map(bat_rank_map)
    bat_master['rank'] = bat_master['provisional_rank']
    bat_master['_is_el_sort'] = np.where(bat_master['final_eligibility'] == 'ELIGIBLE', 0, 1)
    bat_master = bat_master.sort_values(
        by=['_is_el_sort', 'provisional_fixed_weight_score', 'canonical_player_id'],
        ascending=[True, False, True],
        na_position='last'
    ).drop(columns=['_is_el_sort']).reset_index(drop=True)

    bowl_rank_map = top_bowlers_eligible.set_index('canonical_player_id')['rank'].to_dict()
    bowl_master['provisional_rank'] = bowl_master['canonical_player_id'].map(bowl_rank_map)
    bowl_master['rank'] = bowl_master['provisional_rank']
    bowl_master['_is_el_sort'] = np.where(bowl_master['final_eligibility'] == 'ELIGIBLE', 0, 1)
    bowl_master = bowl_master.sort_values(
        by=['_is_el_sort', 'provisional_fixed_weight_score', 'canonical_player_id'],
        ascending=[True, False, True],
        na_position='last'
    ).drop(columns=['_is_el_sort']).reset_index(drop=True)

    # ══════════════════════════════════════════════════════════════════════════
    # 3. PRIORITY 5 & P1.1 — EXTENDED THRESHOLD SENSITIVITY STUDY
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Running Extended Threshold Sensitivity Study (40, 60, 80, 100, 150, 200, 250, 500, 750)...")
    thresh_records = []

    crisis_ball_grid = [40, 60, 80, 100, 150, 200, 250, 500, 750]
    crisis_match_grid = [5, 6, 8, 10]

    base_top10_bat_ids = set(top10_batters['canonical_player_id'])
    base_bat_ranks = top_batters_eligible.set_index('canonical_player_id')['provisional_rank'].to_dict()
    base_bat_names = bat_master.set_index('canonical_player_id')['player_name'].to_dict()

    base_top10_bowl_ids = set(top10_bowlers['canonical_player_id'])
    base_bowl_ranks = top_bowlers_eligible.set_index('canonical_player_id')['provisional_rank'].to_dict()
    base_bowl_names = bowl_master.set_index('canonical_player_id')['player_name'].to_dict()

    # Precompute paired eligible counts for (cb, cm) at baseline normal/total/Tier-1 cutoffs
    paired_counts = {}
    for cb in crisis_ball_grid:
        for cm in crisis_match_grid:
            b_cnt = int((
                (bat_master['eff_crisis_balls'] >= cb) &
                (bat_master['crisis_matches'] >= cm) &
                (bat_master['eff_norm_balls'] >= DEFAULT_BAT_THRESHOLDS['norm_balls']) &
                (bat_master['total_balls'] >= DEFAULT_BAT_THRESHOLDS['total_balls']) &
                (bat_master['tier1_share'] >= MIN_TIER1_SHARE) &
                (bat_master['eligible_for_bat_leaderboard'] == True) &
                (~bat_master['is_quarantined'])
            ).sum())
            w_cnt = int((
                (bowl_master['eff_crisis_balls'] >= cb) &
                (bowl_master['crisis_matches'] >= cm) &
                (bowl_master['eff_norm_balls'] >= DEFAULT_BOWL_THRESHOLDS['norm_balls']) &
                (bowl_master['total_legal_balls'] >= DEFAULT_BOWL_THRESHOLDS['total_legal_balls']) &
                (bowl_master['tier1_share'] >= MIN_TIER1_SHARE) &
                (bowl_master['eligible_for_bowl_leaderboard'] == True) &
                (~bowl_master['is_quarantined'])
            ).sum())
            paired_counts[(cb, cm)] = (b_cnt, w_cnt)

    # Batter grid: cb in [40, 60, 80, 100, 150, 200, 250], cm in [5, 6, 8, 10], nb in [30, 60, 80, 100], tb in [120, 200]
    for cb in crisis_ball_grid:
        for cm in crisis_match_grid:
            for nb in [30, 60, 80, 100]:
                for tb in [120, 200]:
                    mask = (
                        (bat_master['eff_crisis_balls'] >= cb) &
                        (bat_master['crisis_matches'] >= cm) &
                        (bat_master['eff_norm_balls'] >= nb) &
                        (bat_master['total_balls'] >= tb) &
                        (bat_master['tier1_share'] >= MIN_TIER1_SHARE) &
                        (bat_master['eligible_for_bat_leaderboard'] == True) &
                        (~bat_master['is_quarantined']) &
                        (bat_master['provisional_fixed_weight_score'].notna())
                    )
                    cand = bat_master[mask].sort_values(
                        by=['provisional_fixed_weight_score', 'canonical_player_id'],
                        ascending=[False, True]
                    ).reset_index(drop=True)
                    cand['cand_rank'] = range(1, len(cand) + 1)
                    # Do NOT force a Top 10 when fewer than 10 players are eligible
                    cand_top10 = cand.head(10).copy()
                    cand_top10_ids = set(cand_top10['canonical_player_id'])
                    overlap = len(cand_top10_ids & base_top10_bat_ids)
                    union_len = len(cand_top10_ids | base_top10_bat_ids)
                    jaccard = round(float(overlap / union_len), 4) if union_len > 0 else 0.0

                    # Rank movement among cand_top10 players
                    rank_shifts = []
                    shift_details = []
                    for _, cr in cand_top10.iterrows():
                        pid = cr['canonical_player_id']
                        new_r = int(cr['cand_rank'])
                        old_r = base_bat_ranks.get(pid, None)
                        if old_r is not None:
                            diff = abs(new_r - int(old_r))
                            rank_shifts.append(diff)
                            shift_details.append(f"{cr['player_name']}: #{old_r}->#{new_r} ({int(old_r)-new_r:+d})")
                        else:
                            shift_details.append(f"{cr['player_name']}: UNRANKED->#{new_r}")

                    mean_move = round(float(np.mean(rank_shifts)), 2) if rank_shifts else 0.0
                    max_move = int(np.max(rank_shifts)) if rank_shifts else 0
                    entering = [base_bat_names.get(pid, str(pid)) for pid in cand_top10['canonical_player_id'] if pid not in base_top10_bat_ids]
                    leaving = [r['player_name'] for _, r in top10_batters.iterrows() if r['canonical_player_id'] not in cand_top10_ids]

                    ci_widths = cand['uncertainty_width'].dropna()
                    med_ci = round(float(ci_widths.median()), 2) if len(ci_widths) > 0 else np.nan
                    max_ci = round(float(ci_widths.max()), 2) if len(ci_widths) > 0 else np.nan
                    unest_ci = int(cand['ci_status'].ne('ESTIMATED_MATCH_CLUSTER_BOOTSTRAP').sum())

                    b_cnt, w_cnt = paired_counts[(cb, cm)]
                    thresh_records.append({
                        'discipline': 'Batting',
                        'min_crisis_balls': cb,
                        'min_crisis_matches': cm,
                        'min_normal_balls': nb,
                        'min_total_deliveries': tb,
                        'is_primary_crisis_sweep': (cm == 6 and nb == 60 and tb == 200),
                        'eligible_players': len(cand),
                        'eligible_batter_count': len(cand) if (nb == 60 and tb == 200) else b_cnt,
                        'eligible_bowler_count': w_cnt,
                        'unique_canonical_ids': cand['canonical_player_id'].nunique(),
                        'available_top10_count': len(cand_top10),
                        'top10_count': len(cand_top10),
                        'top10_overlap_with_baseline': overlap,
                        'jaccard_similarity': jaccard,
                        'mean_abs_rank_movement': mean_move,
                        'max_rank_movement': max_move,
                        'rank_movement_summary': "; ".join(shift_details) if shift_details else "NONE",
                        'players_entering_top10': ", ".join(entering) if entering else "NONE",
                        'players_leaving_top10': ", ".join(leaving) if leaving else "NONE",
                        'median_ci_width': med_ci,
                        'max_ci_width': max_ci,
                        'unestimated_ci_count': unest_ci,
                        'top_eligible_players': ", ".join(cand_top10['player_name'].head(5).tolist()) if len(cand_top10) > 0 else "NONE"
                    })

    # Bowler grid: cb in [40, 60, 80, 100, 120, 150, 200, 250], cm in [5, 6, 8, 10], nb in [100, 125, 150], tb in [120, 200, 250]
    bowl_cb_grid = sorted(list(set(crisis_ball_grid + [120])))
    for cb in bowl_cb_grid:
        for cm in crisis_match_grid:
            for nb in [100, 125, 150]:
                for tb in [120, 200, 250]:
                    mask = (
                        (bowl_master['eff_crisis_balls'] >= cb) &
                        (bowl_master['crisis_matches'] >= cm) &
                        (bowl_master['eff_norm_balls'] >= nb) &
                        (bowl_master['total_legal_balls'] >= tb) &
                        (bowl_master['tier1_share'] >= MIN_TIER1_SHARE) &
                        (bowl_master['eligible_for_bowl_leaderboard'] == True) &
                        (~bowl_master['is_quarantined']) &
                        (bowl_master['provisional_fixed_weight_score'].notna())
                    )
                    cand = bowl_master[mask].sort_values(
                        by=['provisional_fixed_weight_score', 'canonical_player_id'],
                        ascending=[False, True]
                    ).reset_index(drop=True)
                    cand['cand_rank'] = range(1, len(cand) + 1)
                    # Do NOT force a Top 10 when fewer than 10 players are eligible
                    cand_top10 = cand.head(10).copy()
                    cand_top10_ids = set(cand_top10['canonical_player_id'])
                    overlap = len(cand_top10_ids & base_top10_bowl_ids)
                    union_len = len(cand_top10_ids | base_top10_bowl_ids)
                    jaccard = round(float(overlap / union_len), 4) if union_len > 0 else 0.0

                    rank_shifts = []
                    shift_details = []
                    for _, cr in cand_top10.iterrows():
                        pid = cr['canonical_player_id']
                        new_r = int(cr['cand_rank'])
                        old_r = base_bowl_ranks.get(pid, None)
                        if old_r is not None:
                            diff = abs(new_r - int(old_r))
                            rank_shifts.append(diff)
                            shift_details.append(f"{cr['player_name']}: #{old_r}->#{new_r} ({int(old_r)-new_r:+d})")
                        else:
                            shift_details.append(f"{cr['player_name']}: #{int(bowl_master.loc[bowl_master['canonical_player_id']==pid, 'crisis_balls'].iloc[0])}b->#{new_r}")

                    mean_move = round(float(np.mean(rank_shifts)), 2) if rank_shifts else 0.0
                    max_move = int(np.max(rank_shifts)) if rank_shifts else 0
                    entering = [base_bowl_names.get(pid, str(pid)) for pid in cand_top10['canonical_player_id'] if pid not in base_top10_bowl_ids]
                    leaving = [r['player_name'] for _, r in top10_bowlers.iterrows() if r['canonical_player_id'] not in cand_top10_ids]

                    ci_widths = cand['uncertainty_width'].dropna()
                    med_ci = round(float(ci_widths.median()), 2) if len(ci_widths) > 0 else np.nan
                    max_ci = round(float(ci_widths.max()), 2) if len(ci_widths) > 0 else np.nan
                    unest_ci = int(cand['ci_status'].ne('ESTIMATED_MATCH_CLUSTER_BOOTSTRAP').sum())

                    b_cnt = int((
                        (bat_master['eff_crisis_balls'] >= cb) &
                        (bat_master['crisis_matches'] >= cm) &
                        (bat_master['eff_norm_balls'] >= DEFAULT_BAT_THRESHOLDS['norm_balls']) &
                        (bat_master['total_balls'] >= DEFAULT_BAT_THRESHOLDS['total_balls']) &
                        (bat_master['tier1_share'] >= MIN_TIER1_SHARE) &
                        (bat_master['eligible_for_bat_leaderboard'] == True) &
                        (~bat_master['is_quarantined'])
                    ).sum())

                    thresh_records.append({
                        'discipline': 'Bowling',
                        'min_crisis_balls': cb,
                        'min_crisis_matches': cm,
                        'min_normal_balls': nb,
                        'min_total_deliveries': tb,
                        'is_primary_crisis_sweep': (cm == 6 and nb == 100 and tb == 250),
                        'eligible_players': len(cand),
                        'eligible_batter_count': b_cnt,
                        'eligible_bowler_count': len(cand),
                        'unique_canonical_ids': cand['canonical_player_id'].nunique(),
                        'available_top10_count': len(cand_top10),
                        'top10_count': len(cand_top10),
                        'top10_overlap_with_baseline': overlap,
                        'jaccard_similarity': jaccard,
                        'mean_abs_rank_movement': mean_move,
                        'max_rank_movement': max_move,
                        'rank_movement_summary': "; ".join(shift_details) if shift_details else "NONE",
                        'players_entering_top10': ", ".join(entering) if entering else "NONE",
                        'players_leaving_top10': ", ".join(leaving) if leaving else "NONE",
                        'median_ci_width': med_ci,
                        'max_ci_width': max_ci,
                        'unestimated_ci_count': unest_ci,
                        'top_eligible_players': ", ".join(cand_top10['player_name'].head(5).tolist()) if len(cand_top10) > 0 else "NONE"
                    })

    thresh_df = pd.DataFrame(thresh_records)
    thresh_df.to_csv(OUTPUTS_V3 / "RANKING_THRESHOLD_SENSITIVITY.csv", index=False)

    # ══════════════════════════════════════════════════════════════════════════
    # 4. PRIORITY 6 — WEIGHT SENSITIVITY STUDY (INVARIANT V4 WEIGHTS)
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
                'contrib_maint': r.get('contrib_maint', np.nan),
                'contrib_abs': r.get('contrib_abs', np.nan),
                'contrib_cons': r.get('contrib_cons', np.nan),
                'contrib_sample': r.get('contrib_sample', np.nan),
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

    # Attach sensitivity status back to top 10 and master tables
    bat_sens_map = bat_sens.set_index('canonical_player_id')['ranking_sensitivity_status'].to_dict()
    bowl_sens_map = bowl_sens.set_index('canonical_player_id')['ranking_sensitivity_status'].to_dict()
    top10_batters['ranking_sensitivity_status'] = top10_batters['canonical_player_id'].map(bat_sens_map)
    top10_bowlers['ranking_sensitivity_status'] = top10_bowlers['canonical_player_id'].map(bowl_sens_map)
    bat_master['ranking_sensitivity_status'] = bat_master['canonical_player_id'].map(bat_sens_map).fillna('INELIGIBLE_POOL')
    bowl_master['ranking_sensitivity_status'] = bowl_master['canonical_player_id'].map(bowl_sens_map).fillna('INELIGIBLE_POOL')

    weight_df = pd.DataFrame(weight_records)
    weight_df.to_csv(OUTPUTS_V3 / "RANKING_WEIGHT_SENSITIVITY.csv", index=False)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. PRIORITY 8 & P1.1 — ONE AUTHORITATIVE SOURCE OF TRUTH & SYNCHRONIZED COPIES
    # ══════════════════════════════════════════════════════════════════════════
    logging.info("Exporting Authoritative Top 10 and Synchronizing Downstream Copies...")

    # Attach compatibility and provenance metadata columns so canonical and downstream copies are byte-for-byte identical
    for df_b in [top10_batters, bat_master]:
        df_b['canonical_display_name'] = df_b['player_name']
        df_b['primary_role'] = df_b['v3_role']
        df_b['modal_batting_position'] = df_b['modal_order']
        df_b['source_of_truth_file'] = 'data/outputs/v3/TOP_10_BATTERS.csv'
        df_b['pressure_model_status'] = 'V4_CALIBRATED_RIDGE'
        df_b['hazard_model_status'] = 'EXPERIMENTAL_NOT_USED_FOR_RANKING'

    for df_w in [top10_bowlers, bowl_master]:
        df_w['canonical_display_name'] = df_w['player_name']
        df_w['primary_role'] = df_w['v3_role']
        df_w['source_of_truth_file'] = 'data/outputs/v3/TOP_10_BOWLERS.csv'
        df_w['pressure_model_status'] = 'V4_CALIBRATED_RIDGE'
        df_w['hazard_model_status'] = 'EXPERIMENTAL_NOT_USED_FOR_RANKING'

    # Authoritative Batter Fields
    bat_auth_cols = [
        'rank', 'provisional_rank', 'canonical_player_id', 'striker_id', 'player_name',
        'canonical_display_name', 'v3_role', 'primary_role', 'role_confidence',
        'modal_order', 'modal_batting_position',
        'eligibility_status', 'final_eligibility', 'sample_eligible',
        'eligible_for_bat_leaderboard', 'norm_baseline_eligible', 'norm_baseline_status',
        'total_balls', 'total_runs', 'total_sr', 'total_matches', 'tier1_share',
        'crisis_balls', 'eff_crisis_balls', 'crisis_runs', 'crisis_sr', 'crisis_matches',
        'norm_balls', 'eff_norm_balls', 'norm_runs', 'norm_sr', 'norm_matches',
        'raw_sr_maintenance', 'capped_sr_maintenance', 'sr_maintenance', 'is_maintenance_capped',
        'crisis_r_bat', 'norm_r_bat', 'did_bat_maintenance', 'crisis_delta_rv', 'norm_delta_rv',
        'shrunk_crisis_sr', 'crisis_sr_vs_cohort_mean', 'crisis_sr_below_cohort_mean',
        'performance_anomaly_flag', 'consistency_score', 'sample_confidence',
        'norm_maint', 'norm_abs', 'norm_cons', 'norm_sample',
        'contrib_maint', 'contrib_abs', 'contrib_cons', 'contrib_sample',
        'batting_pri_provisional', 'provisional_fixed_weight_score', 'batting_pri',
        'component_breakdown_explanation',
        'ci_lower', 'ci_upper', 'uncertainty_width', 'ci_status', 'ci_method',
        'ci_confidence_level', 'ci_bootstrap_iterations', 'ci_sample_matches',
        'ci_sample_deliveries', 'ci_metric', 'ranking_sensitivity_status',
        'prior_k', 'prior_mean', 'prior_population_count', 'prior_population_definition',
        'shrinkage_status', 'formula_status', 'pressure_model_status', 'hazard_model_status',
        'source_of_truth_file'
    ]
    top10_batters = top10_batters[bat_auth_cols].copy()
    top10_batters.to_csv(OUTPUTS_V3 / "TOP_10_BATTERS.csv", index=False)

    # Authoritative Bowler Fields
    bowl_auth_cols = [
        'rank', 'provisional_rank', 'canonical_player_id', 'bowler_id', 'player_name',
        'canonical_display_name', 'v3_role', 'primary_role', 'role_confidence',
        'eligibility_status', 'final_eligibility', 'sample_eligible',
        'eligible_for_bowl_leaderboard', 'norm_baseline_eligible', 'norm_baseline_status',
        'total_legal_balls', 'total_wickets', 'total_dots', 'total_dot_pct', 'total_matches', 'tier1_share',
        'crisis_balls', 'eff_crisis_balls', 'crisis_runs', 'crisis_econ', 'crisis_wickets',
        'crisis_dot_pct', 'crisis_wicket_rate', 'crisis_matches',
        'norm_balls', 'eff_norm_balls', 'norm_runs', 'norm_econ', 'norm_wickets',
        'norm_dot_pct', 'norm_wicket_rate', 'norm_matches',
        'raw_dot_maintenance', 'capped_dot_maintenance', 'dot_maintenance', 'is_maintenance_capped',
        'crisis_r_rv', 'norm_r_rv', 'did_bowl_maintenance', 'crisis_delta_rv', 'norm_delta_rv', 'abs_bowl_score',
        'effective_w_maint', 'effective_w_abs', 'effective_w_cons',
        'shrunk_crisis_wr', 'consistency_score', 'sample_confidence',
        'norm_maint', 'norm_abs', 'norm_cons', 'norm_sample',
        'contrib_maint', 'contrib_abs', 'contrib_cons', 'contrib_sample',
        'bowling_pri_provisional', 'provisional_fixed_weight_score', 'bowling_pri',
        'component_breakdown_explanation',
        'ci_lower', 'ci_upper', 'uncertainty_width', 'ci_status', 'ci_method',
        'ci_confidence_level', 'ci_bootstrap_iterations', 'ci_sample_matches',
        'ci_sample_deliveries', 'ci_metric', 'ranking_sensitivity_status',
        'prior_alpha', 'prior_beta', 'prior_mean', 'prior_population_count',
        'shrinkage_status', 'formula_status', 'pressure_model_status', 'hazard_model_status',
        'source_of_truth_file'
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
            'norm_baseline_eligible': r['norm_baseline_eligible'],
            'norm_baseline_status': r['norm_baseline_status'],
            'raw_maintenance_ratio': r['raw_sr_maintenance'],
            'capped_maintenance_ratio': r['capped_sr_maintenance'],
            'is_maintenance_capped': r['is_maintenance_capped'],
            'is_sample_eligible': r['sample_eligible'],
            'is_role_eligible': r['eligible_for_bat_leaderboard'],
            'is_quarantined': r['is_quarantined'],
            'eligibility_status': r['eligibility_status'],
            'final_eligibility': r['final_eligibility'],
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
            'norm_baseline_eligible': r['norm_baseline_eligible'],
            'norm_baseline_status': r['norm_baseline_status'],
            'raw_maintenance_ratio': r['raw_dot_maintenance'],
            'capped_maintenance_ratio': r['capped_dot_maintenance'],
            'is_maintenance_capped': r['is_maintenance_capped'],
            'is_sample_eligible': r['sample_eligible'],
            'is_role_eligible': r['eligible_for_bowl_leaderboard'],
            'is_quarantined': r['is_quarantined'],
            'eligibility_status': r['eligibility_status'],
            'final_eligibility': r['final_eligibility'],
            'exclusion_reasons': r['exclusion_reasons']
        })
    elig_df = pd.DataFrame(elig_records)
    elig_df.to_csv(OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv", index=False)

    # Synchronize all downstream and root-level ranking copies as exact copies of canonical V3 outputs
    import shutil
    OUTPUTS_ROOT = DATA_DIR / "outputs"
    OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)

    bat_copy_targets = [
        ROOT / "FINAL_TOP_10_BATTERS.csv",
        OUTPUTS_ROOT / "FINAL_TOP_10_BATTERS.csv",
        OUTPUTS_ROOT / "top_10_batters.csv"
    ]
    for tgt in bat_copy_targets:
        shutil.copyfile(OUTPUTS_V3 / "TOP_10_BATTERS.csv", tgt)

    bowl_copy_targets = [
        ROOT / "FINAL_TOP_10_BOWLERS.csv",
        OUTPUTS_ROOT / "FINAL_TOP_10_BOWLERS.csv",
        OUTPUTS_ROOT / "top_10_bowlers.csv"
    ]
    for tgt in bowl_copy_targets:
        shutil.copyfile(OUTPUTS_V3 / "TOP_10_BOWLERS.csv", tgt)

    all_bat_copy_targets = [
        ROOT / "ALL_BATTER_RANKINGS.csv",
        OUTPUTS_ROOT / "ALL_BATTER_RANKINGS.csv",
        OUTPUTS_ROOT / "batting_pressure_rankings.csv",
        OUTPUTS_ROOT / "batting_pri_details.csv"
    ]
    for tgt in all_bat_copy_targets:
        shutil.copyfile(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv", tgt)

    all_bowl_copy_targets = [
        ROOT / "ALL_BOWLER_RANKINGS.csv",
        OUTPUTS_ROOT / "ALL_BOWLER_RANKINGS.csv",
        OUTPUTS_ROOT / "bowling_pressure_rankings.csv",
        OUTPUTS_ROOT / "bowling_pri_details.csv"
    ]
    for tgt in all_bowl_copy_targets:
        shutil.copyfile(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv", tgt)

    elig_copy_targets = [
        ROOT / "PLAYER_ELIGIBILITY_REPORT.csv",
        OUTPUTS_ROOT / "PLAYER_ELIGIBILITY_REPORT.csv"
    ]
    for tgt in elig_copy_targets:
        shutil.copyfile(OUTPUTS_V3 / "PLAYER_ELIGIBILITY.csv", tgt)

    shutil.copyfile(OUTPUTS_V3 / "RANKING_WEIGHT_SENSITIVITY.csv", OUTPUTS_ROOT / "PRI_SENSITIVITY_ANALYSIS.csv")
    shutil.copyfile(OUTPUTS_V3 / "RANKING_WEIGHT_SENSITIVITY.csv", ROOT / "PRI_SENSITIVITY_ANALYSIS.csv")

    # Synchronize legacy parquet copies in data/outputs/
    top10_batters.to_parquet(OUTPUTS_ROOT / "top_10_batters.parquet", index=False)
    top10_bowlers.to_parquet(OUTPUTS_ROOT / "top_10_bowlers.parquet", index=False)
    bat_master.to_parquet(OUTPUTS_ROOT / "batting_pressure_rankings.parquet", index=False)
    bowl_master.to_parquet(OUTPUTS_ROOT / "bowling_pressure_rankings.parquet", index=False)

    # Synchronize System B RR Player Fit against fresh System A rankings BEFORE hashing manifest
    try:
        from src.scouting_engine.v3_rr_player_fit import V3RRPlayerFitEngine
        V3RRPlayerFitEngine.generate_player_fit_dataset()
        logging.info("Synchronized RR_PLAYER_FIT.csv with updated V4 System A rankings.")
    except Exception as exc:
        logging.warning(f"Could not synchronize RR_PLAYER_FIT.csv during ranking run: {exc}")

    def _file_sha256(p: Path) -> Optional[str]:
        if not p.exists():
            return None
        h = hashlib.sha256()
        with open(p, 'rb') as fh:
            for chunk in iter(lambda: fh.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()

    sens_bat_ranks = [int(r) for r in top10_batters.loc[top10_batters['ranking_sensitivity_status'] == 'RANKING_SENSITIVE_TO_WEIGHTS', 'rank'].tolist()]
    sens_bowl_ranks = [int(r) for r in top10_bowlers.loc[top10_bowlers['ranking_sensitivity_status'] == 'RANKING_SENSITIVE_TO_WEIGHTS', 'rank'].tolist()]
    bat_sens_str = ", ".join(f"#{r}" for r in sens_bat_ranks) if sens_bat_ranks else "none"
    bowl_sens_str = ", ".join(f"#{r}" for r in sens_bowl_ranks) if sens_bowl_ranks else "none"

    # Master JSON Manifest
    manifest = {
        'manifest_title': 'SupeRR Intelligence V4 Unified Calibrated-Ridge Player Ranking Single Source of Truth',
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
        'artifact_sha256': {
            'TOP_10_BATTERS.csv': _file_sha256(OUTPUTS_V3 / "TOP_10_BATTERS.csv"),
            'TOP_10_BOWLERS.csv': _file_sha256(OUTPUTS_V3 / "TOP_10_BOWLERS.csv"),
            'ALL_BATTER_METRICS.csv': _file_sha256(OUTPUTS_V3 / "ALL_BATTER_METRICS.csv"),
            'ALL_BOWLER_METRICS.csv': _file_sha256(OUTPUTS_V3 / "ALL_BOWLER_METRICS.csv"),
            'RR_PLAYER_FIT.csv': _file_sha256(OUTPUTS_V3 / "RR_PLAYER_FIT.csv"),
        },
        'summary_metrics': {
            'eligible_batters_count': int(len(top_batters_eligible)),
            'eligible_bowlers_count': int(len(top_bowlers_eligible)),
            'sensitive_bat_ranks': sens_bat_ranks,
            'sensitive_bowl_ranks': sens_bowl_ranks,
            'threshold_sensitivity_combinations': int(len(thresh_df)),
        },
        'synchronized_downstream_copies': {
            'top_10_batters_copies': [
                'FINAL_TOP_10_BATTERS.csv',
                'data/outputs/FINAL_TOP_10_BATTERS.csv',
                'data/outputs/top_10_batters.csv'
            ],
            'top_10_bowlers_copies': [
                'FINAL_TOP_10_BOWLERS.csv',
                'data/outputs/FINAL_TOP_10_BOWLERS.csv',
                'data/outputs/top_10_bowlers.csv'
            ],
            'all_batter_metrics_copies': [
                'ALL_BATTER_RANKINGS.csv',
                'data/outputs/ALL_BATTER_RANKINGS.csv',
                'data/outputs/batting_pressure_rankings.csv'
            ],
            'all_bowler_metrics_copies': [
                'ALL_BOWLER_RANKINGS.csv',
                'data/outputs/ALL_BOWLER_RANKINGS.csv',
                'data/outputs/bowling_pressure_rankings.csv'
            ],
            'player_eligibility_copies': [
                'PLAYER_ELIGIBILITY_REPORT.csv',
                'data/outputs/PLAYER_ELIGIBILITY_REPORT.csv'
            ]
        },
        'source_datasets': {
            'ball_by_ball': 'data/ball_by_ball_ipl_t20i.csv',
            'playing_eleven': 'data/playing_eleven_ipl_t20i.csv',
            'competition_mapping': 'data/competition_team_player_mapping_ipl_t20i.csv',
            'features_pressure_parquet': 'data/features/ball_by_ball_with_pressure.parquet'
        },
        'governance': {
            'git_baseline_commit': '537777c8436fd647a484a49cfbfa30b843c98a1c',
            'git_branch': 'fix/v3-pre-submission-consistency-001',
            'ranking_script_version': 'V4_UNIFIED_CALIBRATED_RIDGE',
            'pressure_formula_version': 'V4_CALIBRATED_RIDGE',
            'hazard_model_status': 'EXPERIMENTAL_NOT_USED_FOR_RANKING',
            'identity_crosswalk_version': 'V3.1_CANONICAL',
            'ranking_score_status': 'V4_CALIBRATED_RIDGE_SCORE',
            'threshold_governance': 'INVARIANT_NORMAL_AND_TIER1_GATED',
            'ranking_approval_status': 'V4 CALIBRATED RIDGE — UNIFIED RUN VALUE VERIFIED',
            'mandatory_disclosure': (
                f"Rankings use V4 Calibrated Ridge state-conditional run values with Tier-1 weighting and within-phase quantile tiers. "
                f"Batter ranks sensitive to scoring weights: {bat_sens_str}; "
                f"Bowler ranks sensitive to scoring weights: {bowl_sens_str}."
            )
        },
        'configurations': {
            'pri_weights': PRI_WEIGHTS,
            'sensitivity_configs': SENSITIVITY_CONFIGS,
            'default_batting_thresholds': DEFAULT_BAT_THRESHOLDS,
            'default_bowling_thresholds': DEFAULT_BOWL_THRESHOLDS,
            'min_normal_balls_bowler': MIN_NORMAL_BALLS_BOWLER,
            'min_tier1_share': MIN_TIER1_SHARE,
            'comp_tier_weights': COMP_TIER_WEIGHTS,
            'v_wkt_bowl_by_phase': V_WKT_BOWL_BY_PHASE,
            'v_wkt_bat_by_phase': V_WKT_BAT_BY_PHASE,
            'shrinkage_configuration': {
                'batting_method': 'RIDGE_DUAL_ARM_EMPIRICAL_SHRINKAGE',
                'prior_k': 90.0,
                'batting_prior_mean': bat_prior_meta['prior_mean'],
                'batting_prior_pop_count': bat_prior_meta['prior_population_count'],
                'bowling_method': 'RIDGE_DUAL_ARM_AND_BETA_BINOMIAL',
                'bowling_prior_k': 150.0,
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
    print(top10_batters[['rank', 'canonical_player_id', 'player_name', 'v3_role', 'crisis_balls', 'crisis_sr', 'raw_sr_maintenance', 'sr_maintenance', 'provisional_fixed_weight_score', 'performance_anomaly_flag']].to_string())

    print("\n=== TOP 10 BOWLERS UNDER PRESSURE (V3 AUTHORITATIVE, MIN_NORMAL_BALLS=100) ===")
    print(top10_bowlers[['rank', 'canonical_player_id', 'player_name', 'v3_role', 'crisis_balls', 'norm_balls', 'crisis_dot_pct', 'raw_dot_maintenance', 'dot_maintenance', 'is_maintenance_capped', 'provisional_fixed_weight_score']].to_string())

    return top10_batters, top10_bowlers, bat_master, bowl_master, elig_df


if __name__ == '__main__':
    compute_v3_rankings()
