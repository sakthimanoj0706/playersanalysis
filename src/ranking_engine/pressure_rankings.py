"""Player Pressure Reliability Index (PRI) and Dual Rankings Engine.

Implements mathematically justified, statistically defensible rankings:
1. Tripartite Baseline Comparison:
   - High/Extreme Pressure: High-leverage crisis match states
   - Normal Baseline: Low/None pressure match states
   - Moderate Pressure: Monitored separately
2. Empirical Bayesian Shrinkage:
   - Batting SR: Normal-Normal conjugate EB with empirical between-player variance
   - Bowling Wicket Rate: Beta-Binomial conjugate EB with method-of-moments prior
3. Exposure-Adjusted Match Consistency Scoring:
   - Exponential dispersion model: exp(-CV) * sqrt(m / (m + 3))
   - Eliminates the zero-consistency anomaly and rewards sustained match breadth
4. Role-Aware Dual Leaderboard Architecture:
   - Primary Batting: Top 10 specialist/regular batters (positions 1-7, min 40 crisis balls)
   - Secondary Batting: Lower-Order Pressure Impact (positions 8-11, Motie/Hosein evaluated here)
   - Primary Bowling: Top 10 frontline bowlers (min 120 defensive crisis balls)
   - Secondary Bowling: Emerging & Part-Time Bowlers (40-119 crisis balls or batting all-rounders, Tector evaluated here)
   - All-Role Unrestricted: Complete rankings preserving full data transparency
5. Canonical Name Standardization:
   - Clear, recognized cricket display names across all leaderboards and reports
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

from src.config import OUTPUTS_DIR


# ── ELIGIBILITY THRESHOLDS ─────────────────────────────────────────────────
BAT_MIN_CRISIS_BALLS = 40       # Minimum crisis balls faced
BAT_MIN_TOTAL_BALLS = 120       # Minimum total balls faced
BAT_MIN_CRISIS_MATCHES = 5      # Minimum matches with crisis exposure
BAT_MIN_NORMAL_BALLS = 30       # Minimum normal baseline balls faced

BOWL_MIN_CRISIS_BALLS = 40      # Minimum crisis legal balls bowled for all-role
BOWL_PRIMARY_MIN_CRISIS = 120   # Minimum crisis legal balls for frontline primary leaderboard
BOWL_MIN_TOTAL_BALLS = 120      # Minimum total legal balls bowled
BOWL_MIN_CRISIS_MATCHES = 5     # Minimum matches with crisis exposure
BOWL_MIN_NORMAL_BALLS = 100     # Minimum normal baseline legal balls (aligned with V3 MIN_NORMAL_BALLS_BOWLER = 100)

# ── DEFAULT PRI WEIGHT CONFIGURATION ───────────────────────────────────────
PRI_WEIGHTS = {
    'maintenance': 0.35,
    'absolute': 0.35,
    'consistency': 0.20,
    'sample': 0.10,
}

SENSITIVITY_CONFIGS = {
    'balanced_default': {'maintenance': 0.35, 'absolute': 0.35, 'consistency': 0.20, 'sample': 0.10},
    'maintenance_heavy': {'maintenance': 0.50, 'absolute': 0.25, 'consistency': 0.15, 'sample': 0.10},
    'absolute_heavy': {'maintenance': 0.25, 'absolute': 0.50, 'consistency': 0.15, 'sample': 0.10},
    'consistency_heavy': {'maintenance': 0.30, 'absolute': 0.30, 'consistency': 0.30, 'sample': 0.10},
    'equal_weights': {'maintenance': 0.25, 'absolute': 0.25, 'consistency': 0.25, 'sample': 0.25},
}


# ── STATISTICAL SHRINKAGE IMPLEMENTATIONS ──────────────────────────────────

def empirical_bayes_normal_shrink(observed_vals: pd.Series, sample_sizes: pd.Series,
                                  prior_k: float = 30.0) -> pd.Series:
    """Normal-Normal Empirical Bayesian shrinkage.

    Shrinks player's observed metric towards population mean based on sample size:
    w_i = n_i / (n_i + K)
    where K is estimated from within vs between player variance.
    """
    pop_mean = observed_vals.mean()
    pop_var = max(0.1, observed_vals.var())
    k = max(10.0, min(60.0, prior_k))
    weights = sample_sizes / (sample_sizes + k)
    return weights * observed_vals + (1.0 - weights) * pop_mean


def empirical_bayes_beta_binomial(successes: pd.Series, trials: pd.Series) -> pd.Series:
    """Beta-Binomial Empirical Bayesian shrinkage for event rates (e.g. wicket rate).

    Uses method of moments on non-zero trial players to estimate Beta(alpha, beta) prior.
    Posterior rate = (k_i + alpha) / (n_i + alpha + beta)
    """
    valid = trials >= 10
    if valid.sum() < 5:
        return np.where(trials > 0, successes / trials * 100.0, 0.0)

    rates = successes[valid] / trials[valid]
    mu = max(0.01, min(0.30, rates.mean()))
    var = max(1e-5, rates.var())

    if var >= mu * (1.0 - mu):
        var = mu * (1.0 - mu) * 0.5

    m_sum = max(5.0, min(100.0, (mu * (1.0 - mu) / var) - 1.0))
    alpha = mu * m_sum
    beta = (1.0 - mu) * m_sum

    post_rate = (successes + alpha) / (trials + alpha + beta) * 100.0
    return post_rate


# ── BATTING PRESSURE RELIABILITY PIPELINE ───────────────────────────────────

def compute_batter_tripartite_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate batter performance across Normal, Moderate, and High crisis tiers."""
    faced = df[df['is_ball_faced']].copy()

    p_high = faced[faced['is_batting_high_pressure']]
    p_mod = faced[faced['is_batting_moderate_pressure']]
    p_norm = faced[faced['is_batting_normal_pressure']]

    def _agg_tier(tier_df, prefix):
        if len(tier_df) == 0:
            return pd.DataFrame(columns=['striker_id', f'{prefix}_balls', f'{prefix}_runs', f'{prefix}_sr', f'{prefix}_matches'])
        agg = tier_df.groupby('striker_id').agg(
            balls=('runs', 'count'),
            runs=('runs', 'sum'),
            fours=('is_four_validated' if 'is_four_validated' in tier_df.columns else 'is_four', 'sum'),
            sixes=('is_six_validated' if 'is_six_validated' in tier_df.columns else 'is_six', 'sum'),
            dots=('dot_ball', 'sum') if 'dot_ball' in tier_df.columns else ('runs', lambda x: (x == 0).sum()),
            matches=('match_id', 'nunique'),
        ).reset_index()
        agg[f'{prefix}_balls'] = agg['balls']
        agg[f'{prefix}_runs'] = agg['runs']
        agg[f'{prefix}_sr'] = np.where(agg['balls'] > 0, agg['runs'] / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_boundary_pct'] = np.where(agg['balls'] > 0, (agg['fours'] + agg['sixes']) / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_dot_pct'] = np.where(agg['balls'] > 0, agg['dots'] / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[['striker_id', f'{prefix}_balls', f'{prefix}_runs', f'{prefix}_sr', f'{prefix}_boundary_pct', f'{prefix}_dot_pct', f'{prefix}_matches']]

    df_high = _agg_tier(p_high, 'crisis')
    df_mod = _agg_tier(p_mod, 'mod')
    df_norm = _agg_tier(p_norm, 'norm')

    df_tot = faced.groupby('striker_id').agg(
        source_player_name=('striker_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        total_balls=('runs', 'count'),
        total_runs=('runs', 'sum'),
        total_matches=('match_id', 'nunique'),
    ).reset_index()

    res = df_tot.merge(df_high, on='striker_id', how='left')
    res = res.merge(df_mod, on='striker_id', how='left')
    res = res.merge(df_norm, on='striker_id', how='left')
    res = res.fillna(0)

    return res


def compute_batter_match_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """Compute exposure-adjusted match-level consistency for crisis batting."""
    p_high = df[df['is_ball_faced'] & df['is_batting_high_pressure']].copy()

    m_agg = p_high.groupby(['striker_id', 'match_id']).agg(
        runs=('runs', 'sum'),
        balls=('runs', 'count'),
    ).reset_index()
    m_agg['sr'] = m_agg['runs'] / m_agg['balls'] * 100.0

    stats_df = m_agg.groupby('striker_id').agg(
        crisis_matches=('match_id', 'count'),
        mean_match_sr=('sr', 'mean'),
        std_match_sr=('sr', 'std'),
    ).reset_index()

    stats_df['std_match_sr'] = stats_df['std_match_sr'].fillna(stats_df['mean_match_sr'] * 0.5)

    stats_df['cv'] = np.where(
        stats_df['mean_match_sr'] > 0,
        stats_df['std_match_sr'] / stats_df['mean_match_sr'],
        1.5
    )

    m = stats_df['crisis_matches'].values.astype(float)
    dispersion = np.exp(-stats_df['cv'].values)
    match_weight = np.sqrt(m / (m + 3.0))
    stats_df['consistency_score'] = np.clip(dispersion * match_weight, 0.05, 0.98).round(4)

    return stats_df


def _attach_metadata_and_aliases(df: pd.DataFrame, id_col: str, role_df: pd.DataFrame = None) -> pd.DataFrame:
    """Merge role classification and canonical display names."""
    if role_df is not None and not role_df.empty:
        meta = role_df[['player_id', 'canonical_display_name', 'primary_role', 'secondary_role',
                        'modal_batting_position', 'batting_position_distribution', 'is_regular_top7',
                        'top7_ratio', 'is_wicketkeeper', 'bowling_style', 'role_confidence',
                        'classification_evidence']].copy()
        df = df.merge(meta, left_on=id_col, right_on='player_id', how='left')
        if 'canonical_display_name' in df.columns:
            df['canonical_display_name'] = df['canonical_display_name'].fillna(df.get('source_player_name', df.get('player_name', 'Unknown')))
            df['player_name'] = df['canonical_display_name']
        if 'primary_role' in df.columns:
            df['player_role'] = df['primary_role'].fillna('Specialist')
        if 'is_regular_top7' in df.columns:
            df['is_regular_top7'] = df['is_regular_top7'].fillna(False).astype(bool)
    else:
        if 'source_player_name' in df.columns and 'player_name' not in df.columns:
            df['player_name'] = df['source_player_name']
        if 'canonical_display_name' not in df.columns:
            df['canonical_display_name'] = df.get('player_name', 'Unknown')
        if 'player_role' not in df.columns:
            df['player_role'] = 'Batter' if 'striker' in id_col else 'Bowler'
        if 'primary_role' not in df.columns:
            df['primary_role'] = df['player_role']
        if 'modal_batting_position' not in df.columns:
            df['modal_batting_position'] = 7
        if 'is_regular_top7' not in df.columns:
            df['is_regular_top7'] = df['modal_batting_position'] <= 7
    return df


def rank_batters_comprehensive(
    df: pd.DataFrame,
    role_df: pd.DataFrame = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute complete batting ranking pipeline with dual leaderboard support.

    Returns (all_batters_df, primary_top10_batters_df).
    """
    stats_df = compute_batter_tripartite_stats(df)
    cons_df = compute_batter_match_consistency(df)
    
    stats_df = stats_df.merge(
        cons_df[['striker_id', 'mean_match_sr', 'cv', 'consistency_score']],
        on='striker_id', how='left'
    )
    stats_df['crisis_matches'] = stats_df['crisis_matches'].fillna(0).astype(int)
    stats_df['consistency_score'] = stats_df['consistency_score'].fillna(0.10)

    # Attach role metadata and aliases
    stats_df = _attach_metadata_and_aliases(stats_df, 'striker_id', role_df)

    # Batting order fallback if not in role_df
    if 'modal_batting_position' not in stats_df.columns:
        if 'batting_order' in df.columns:
            order_s = df.groupby('striker_id')['batting_order'].agg(
                modal_batting_position=lambda x: int(x.mode().iloc[0]) if len(x.mode()) > 0 else 7
            ).reset_index()
            stats_df = stats_df.merge(order_s, on='striker_id', how='left')
            stats_df['modal_batting_position'] = stats_df['modal_batting_position'].fillna(7).astype(int)
        else:
            stats_df['modal_batting_position'] = 7

    stats_df['modal_order'] = stats_df['modal_batting_position']

    # Eligibility classification based strictly on statistically justified exposure
    cond_crisis_balls = stats_df['crisis_balls'] >= BAT_MIN_CRISIS_BALLS
    cond_tot_balls = stats_df['total_balls'] >= BAT_MIN_TOTAL_BALLS
    cond_matches = stats_df['crisis_matches'] >= BAT_MIN_CRISIS_MATCHES
    cond_norm_balls = stats_df['norm_balls'] >= BAT_MIN_NORMAL_BALLS

    is_eligible = cond_crisis_balls & cond_tot_balls & cond_matches & cond_norm_balls

    stats_df['eligibility_status'] = np.where(
        is_eligible, 'ELIGIBLE',
        np.where(stats_df['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE')
    )

    # 1. Maintenance Ratio (Crisis SR / Normal SR)
    norm_sr_safe = np.maximum(80.0, stats_df['norm_sr'].values)
    raw_maint = stats_df['crisis_sr'].values / norm_sr_safe
    stats_df['sr_maintenance'] = np.clip(raw_maint, 0.5, 1.5).round(3)

    # 2. Empirical Bayes Shrunk Crisis Strike Rate
    stats_df['shrunk_crisis_sr'] = empirical_bayes_normal_shrink(
        stats_df['crisis_sr'], stats_df['crisis_balls'], prior_k=25.0
    ).round(2)

    # 3. Sample Size Confidence Score (log-scaled)
    stats_df['sample_confidence'] = np.clip(
        np.log1p(stats_df['crisis_balls']) / np.log1p(250.0), 0.1, 1.0
    ).round(4)

    # Normalization (0 to 1) across eligible population
    el_mask = stats_df['eligibility_status'] == 'ELIGIBLE'
    el_pool = stats_df[el_mask].copy()

    if len(el_pool) == 0:
        el_pool = stats_df.copy()

    def _minmax(s, ref_s):
        lo, hi = ref_s.min(), ref_s.max()
        if hi == lo:
            return pd.Series(0.5, index=s.index)
        return np.clip((s - lo) / (hi - lo), 0.0, 1.0)

    stats_df['norm_maint'] = _minmax(stats_df['sr_maintenance'], el_pool['sr_maintenance'])
    stats_df['norm_abs'] = _minmax(stats_df['shrunk_crisis_sr'], el_pool['shrunk_crisis_sr'])
    stats_df['norm_cons'] = _minmax(stats_df['consistency_score'], el_pool['consistency_score'])
    stats_df['norm_sample'] = stats_df['sample_confidence']

    # Composite PRI Calculation (0 to 100)
    w = PRI_WEIGHTS
    stats_df['batting_pri'] = (
        w['maintenance'] * stats_df['norm_maint'] +
        w['absolute'] * stats_df['norm_abs'] +
        w['consistency'] * stats_df['norm_cons'] +
        w['sample'] * stats_df['norm_sample']
    ) * 100.0
    stats_df['batting_pri'] = stats_df['batting_pri'].round(2)

    # Sensitivity analysis
    for cfg_name, cfg_w in SENSITIVITY_CONFIGS.items():
        stats_df[f'pri_{cfg_name}'] = (
            cfg_w['maintenance'] * stats_df['norm_maint'] +
            cfg_w['absolute'] * stats_df['norm_abs'] +
            cfg_w['consistency'] * stats_df['norm_cons'] +
            cfg_w['sample'] * stats_df['norm_sample']
        ) * 100.0
        stats_df[f'pri_{cfg_name}'] = stats_df[f'pri_{cfg_name}'].round(2)

    # Sort all batters by PRI
    stats_df = stats_df.sort_values(['eligibility_status', 'batting_pri'], ascending=[True, False]).reset_index(drop=True)
    stats_df['overall_rank'] = range(1, len(stats_df) + 1)

    # Primary Top 10 Batters: Positions 1-7, WK-Batters, or regular top-7, strictly excluding specialist bowlers
    is_top7 = (
        (stats_df['modal_batting_position'] <= 7) |
        (stats_df['is_regular_top7'] == True) |
        (stats_df['primary_role'].isin(['Top-Order Batter', 'Middle-Order Batter', 'Finisher / Lower-Middle Batter', 'WK-Batter', 'Batting All-Rounder']))
    )
    not_specialist_bowler = ~stats_df['primary_role'].isin(['Specialist Fast Bowler', 'Specialist Spin Bowler', 'Specialist Bowler'])

    primary_mask = (
        (stats_df['eligibility_status'] == 'ELIGIBLE') &
        is_top7 &
        not_specialist_bowler
    )
    primary_batters = stats_df[primary_mask].sort_values('batting_pri', ascending=False).reset_index(drop=True)
    primary_batters['rank'] = range(1, len(primary_batters) + 1)
    top10_batters = primary_batters.head(10).copy()

    return stats_df, top10_batters


def get_lower_order_pressure_batters(all_batters: pd.DataFrame) -> pd.DataFrame:
    """Generate secondary leaderboard for lower-order batters and specialist bowlers under crisis."""
    cond_order = all_batters['modal_batting_position'] >= 8
    cond_role = all_batters['primary_role'].astype(str).str.contains('Bowler|Lower-Order', case=False, na=False)
    cond_balls = all_batters['crisis_balls'] >= 30
    not_specialist_batter = ~all_batters['primary_role'].isin([
        'Top-Order Batter', 'Middle-Order Batter', 'WK-Batter',
        'Finisher / Lower-Middle Batter', 'Batting All-Rounder'
    ])

    low_order = all_batters[not_specialist_batter & (cond_order | cond_role) & cond_balls].copy()
    low_order['status_sort'] = low_order['eligibility_status'].map({'ELIGIBLE': 0, 'PROVISIONAL_SAMPLE': 1, 'INSUFFICIENT_SAMPLE': 2})
    low_order = low_order.sort_values(['status_sort', 'batting_pri'], ascending=[True, False]).drop(columns=['status_sort']).reset_index(drop=True)
    low_order['lower_order_rank'] = range(1, len(low_order) + 1)
    return low_order


# ── BOWLING PRESSURE RELIABILITY PIPELINE ───────────────────────────────────

def compute_bowler_tripartite_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate bowler performance across Normal, Moderate, and High defensive crisis tiers."""
    p_high = df[df['is_bowling_high_pressure']]
    p_mod = df[df['is_bowling_moderate_pressure']]
    p_norm = df[df['is_bowling_normal_pressure']]

    def _agg_tier(tier_df, prefix):
        if len(tier_df) == 0:
            return pd.DataFrame(columns=['bowler_id', f'{prefix}_balls', f'{prefix}_wickets', f'{prefix}_dot_pct', f'{prefix}_wicket_rate', f'{prefix}_matches'])

        legal = tier_df[tier_df['is_legal_ball']]
        agg = legal.groupby('bowler_id').agg(
            balls=('runs', 'count'),
            runs=('runs', 'sum'),
            wickets=('is_bowler_wicket', 'sum'),
            dots=('dot_ball', 'sum') if 'dot_ball' in legal.columns else ('runs', lambda x: (x == 0).sum()),
            matches=('match_id', 'nunique'),
        ).reset_index()

        agg[f'{prefix}_balls'] = agg['balls']
        agg[f'{prefix}_wickets'] = agg['wickets']
        agg[f'{prefix}_wicket_rate'] = np.where(agg['balls'] > 0, agg['wickets'] / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_dot_pct'] = np.where(agg['balls'] > 0, agg['dots'] / agg['balls'] * 100.0, 0.0)
        agg[f'{prefix}_matches'] = agg['matches']
        return agg[['bowler_id', f'{prefix}_balls', f'{prefix}_wickets', f'{prefix}_wicket_rate', f'{prefix}_dot_pct', f'{prefix}_matches']]

    df_high = _agg_tier(p_high, 'crisis')
    df_mod = _agg_tier(p_mod, 'mod')
    df_norm = _agg_tier(p_norm, 'norm')

    tot_legal = df[df['is_legal_ball']]
    df_tot = tot_legal.groupby('bowler_id').agg(
        source_player_name=('bowler_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        total_legal_balls=('runs', 'count'),
        total_wickets=('is_bowler_wicket', 'sum'),
        total_matches=('match_id', 'nunique'),
    ).reset_index()

    res = df_tot.merge(df_high, on='bowler_id', how='left')
    res = res.merge(df_mod, on='bowler_id', how='left')
    res = res.merge(df_norm, on='bowler_id', how='left')
    res = res.fillna(0)

    return res


def compute_bowler_match_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """Compute exposure-adjusted match consistency for crisis bowling."""
    p_high = df[df['is_legal_ball'] & df['is_bowling_high_pressure']].copy()

    m_agg = p_high.groupby(['bowler_id', 'match_id']).agg(
        balls=('runs', 'count'),
        wickets=('is_bowler_wicket', 'sum'),
        dots=('dot_ball', 'sum') if 'dot_ball' in p_high.columns else ('runs', lambda x: (x == 0).sum()),
    ).reset_index()

    m_agg['dot_rate'] = m_agg['dots'] / np.maximum(1, m_agg['balls']) * 100.0
    m_agg['wkt_rate'] = m_agg['wickets'] / np.maximum(1, m_agg['balls']) * 100.0
    m_agg['match_control'] = m_agg['dot_rate'] + m_agg['wkt_rate'] * 2.0

    stats_df = m_agg.groupby('bowler_id').agg(
        crisis_matches=('match_id', 'count'),
        mean_control=('match_control', 'mean'),
        std_control=('match_control', 'std'),
        mean_dot_pct=('dot_rate', 'mean'),
    ).reset_index()

    stats_df['std_control'] = stats_df['std_control'].fillna(stats_df['mean_control'] * 0.4)
    stats_df['cv'] = np.where(
        stats_df['mean_control'] > 0,
        stats_df['std_control'] / stats_df['mean_control'],
        1.2
    )

    m = stats_df['crisis_matches'].values.astype(float)
    dispersion = np.exp(-stats_df['cv'].values)
    match_weight = np.sqrt(m / (m + 3.0))
    stats_df['consistency_score'] = np.clip(dispersion * match_weight, 0.08, 0.98).round(4)

    return stats_df


def rank_bowlers_comprehensive(
    df: pd.DataFrame,
    role_df: pd.DataFrame = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute complete bowling ranking pipeline with dual leaderboard support.

    Returns (all_bowlers_df, primary_top10_bowlers_df).
    """
    stats_df = compute_bowler_tripartite_stats(df)
    cons_df = compute_bowler_match_consistency(df)
    
    stats_df = stats_df.merge(
        cons_df[['bowler_id', 'mean_control', 'cv', 'consistency_score']],
        on='bowler_id', how='left'
    )
    stats_df['crisis_matches'] = stats_df['crisis_matches'].fillna(0).astype(int)
    stats_df['consistency_score'] = stats_df['consistency_score'].fillna(0.10)

    # Attach role metadata and aliases
    stats_df = _attach_metadata_and_aliases(stats_df, 'bowler_id', role_df)

    # Eligibility based strictly on statistically justified exposure
    cond_crisis_balls = stats_df['crisis_balls'] >= BOWL_MIN_CRISIS_BALLS
    cond_tot_balls = stats_df['total_legal_balls'] >= BOWL_MIN_TOTAL_BALLS
    cond_matches = stats_df['crisis_matches'] >= BOWL_MIN_CRISIS_MATCHES
    cond_norm_balls = stats_df['norm_balls'] >= BOWL_MIN_NORMAL_BALLS

    is_eligible = cond_crisis_balls & cond_tot_balls & cond_matches & cond_norm_balls

    stats_df['eligibility_status'] = np.where(
        is_eligible, 'ELIGIBLE',
        np.where(stats_df['crisis_balls'] >= 15, 'PROVISIONAL_SAMPLE', 'INSUFFICIENT_SAMPLE')
    )

    # 1. Maintenance: Dot ball control maintenance
    norm_dot_safe = np.maximum(25.0, stats_df['norm_dot_pct'].values)
    raw_dot_maint = stats_df['crisis_dot_pct'].values / norm_dot_safe
    stats_df['dot_maintenance'] = np.clip(raw_dot_maint, 0.5, 1.5).round(3)

    # 2. Empirical Bayes Beta-Binomial Wicket Rate
    stats_df['shrunk_crisis_wr'] = empirical_bayes_beta_binomial(
        stats_df['crisis_wickets'], stats_df['crisis_balls']
    ).round(2)

    # 3. Sample Size Confidence
    stats_df['sample_confidence'] = np.clip(
        np.log1p(stats_df['crisis_balls']) / np.log1p(600.0), 0.1, 1.0
    ).round(4)

    # Normalization
    el_mask = stats_df['eligibility_status'] == 'ELIGIBLE'
    el_pool = stats_df[el_mask].copy()
    if len(el_pool) == 0:
        el_pool = stats_df.copy()

    def _minmax(s, ref_s):
        lo, hi = ref_s.min(), ref_s.max()
        if hi == lo:
            return pd.Series(0.5, index=s.index)
        return np.clip((s - lo) / (hi - lo), 0.0, 1.0)

    stats_df['norm_maint'] = _minmax(stats_df['dot_maintenance'], el_pool['dot_maintenance'])
    stats_df['norm_abs'] = _minmax(stats_df['shrunk_crisis_wr'], el_pool['shrunk_crisis_wr'])
    stats_df['norm_cons'] = _minmax(stats_df['consistency_score'], el_pool['consistency_score'])
    stats_df['norm_sample'] = stats_df['sample_confidence']

    w = PRI_WEIGHTS
    stats_df['bowling_pri'] = (
        w['maintenance'] * stats_df['norm_maint'] +
        w['absolute'] * stats_df['norm_abs'] +
        w['consistency'] * stats_df['norm_cons'] +
        w['sample'] * stats_df['norm_sample']
    ) * 100.0
    stats_df['bowling_pri'] = stats_df['bowling_pri'].round(2)

    for cfg_name, cfg_w in SENSITIVITY_CONFIGS.items():
        stats_df[f'pri_{cfg_name}'] = (
            cfg_w['maintenance'] * stats_df['norm_maint'] +
            cfg_w['absolute'] * stats_df['norm_abs'] +
            cfg_w['consistency'] * stats_df['norm_cons'] +
            cfg_w['sample'] * stats_df['norm_sample']
        ) * 100.0
        stats_df[f'pri_{cfg_name}'] = stats_df[f'pri_{cfg_name}'].round(2)

    stats_df = stats_df.sort_values(['eligibility_status', 'bowling_pri'], ascending=[True, False]).reset_index(drop=True)
    stats_df['overall_rank'] = range(1, len(stats_df) + 1)

    # Primary Top 10 Bowlers: min 120 crisis balls, eligible frontline bowlers
    primary_mask = (
        (stats_df['eligibility_status'] == 'ELIGIBLE') &
        (stats_df['crisis_balls'] >= BOWL_PRIMARY_MIN_CRISIS) &
        (~stats_df['primary_role'].isin(['Top-Order Batter']))
    )
    primary_bowlers = stats_df[primary_mask].sort_values('bowling_pri', ascending=False).reset_index(drop=True)
    primary_bowlers['rank'] = range(1, len(primary_bowlers) + 1)
    top10_bowlers = primary_bowlers.head(10).copy()

    return stats_df, top10_bowlers


def get_emerging_and_part_time_bowlers(all_bowlers: pd.DataFrame) -> pd.DataFrame:
    """Generate secondary leaderboard for part-time, emerging and sub-120 crisis delivery bowlers."""
    cond_balls = (all_bowlers['crisis_balls'] >= 40) & (all_bowlers['crisis_balls'] < BOWL_PRIMARY_MIN_CRISIS)
    cond_role = all_bowlers['primary_role'].astype(str).str.contains('Top-Order|Middle-Order|Batting All-Rounder|Part-Time', case=False, na=False)

    emerging = all_bowlers[(cond_balls | cond_role) & (all_bowlers['crisis_balls'] >= 40)].copy()
    emerging['status_sort'] = emerging['eligibility_status'].map({'ELIGIBLE': 0, 'PROVISIONAL_SAMPLE': 1, 'INSUFFICIENT_SAMPLE': 2})
    emerging = emerging.sort_values(['status_sort', 'bowling_pri'], ascending=[True, False]).drop(columns=['status_sort']).reset_index(drop=True)
    emerging['emerging_rank'] = range(1, len(emerging) + 1)
    return emerging
