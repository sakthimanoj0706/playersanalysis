"""Batter performance analysis."""
import numpy as np
import pandas as pd


def compute_batter_stats(df: pd.DataFrame, min_balls: int = 50) -> pd.DataFrame:
    """Per-batter aggregate statistics.

    Uses is_ball_faced for balls faced (excludes wides).
    Uses `runs` column (provisional batter runs).
    Reports both conventional batting average (runs / dismissals)
    and average runs per innings separately.
    """
    faced = df[df['is_ball_faced']].copy()

    fours_col = 'is_four_validated' if 'is_four_validated' in faced.columns else 'is_four'
    sixes_col = 'is_six_validated' if 'is_six_validated' in faced.columns else 'is_six'

    agg = faced.groupby('striker_id').agg(
        player_name=('striker_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        matches=('match_id', 'nunique'),
        balls_faced=('runs', 'count'),
        runs=('runs', 'sum'),
        fours=(fours_col, 'sum'),
        sixes=(sixes_col, 'sum'),
    ).reset_index()

    # Dots
    if 'dot_ball' in faced.columns:
        dots = faced.groupby('striker_id')['dot_ball'].sum().reset_index(name='dots')
    else:
        dots = faced.groupby('striker_id')['runs'].agg(lambda s: (s == 0).sum()).reset_index(name='dots')
    agg = agg.merge(dots, on='striker_id', how='left')

    # Innings count - distinct (match_id, innings) pairs per striker
    inn_count = (
        faced[['striker_id', 'match_id', 'innings']]
        .drop_duplicates()
        .groupby('striker_id')
        .size()
        .reset_index(name='innings')
    )
    agg = agg.merge(inn_count, on='striker_id', how='left')

    # Dismissals from full dataset
    dismissals = df[df['is_wicket']].groupby('dismissed_player_id').size().reset_index(name='dismissals')
    dismissals = dismissals.rename(columns={'dismissed_player_id': 'striker_id'})
    agg = agg.merge(dismissals, on='striker_id', how='left')
    agg['dismissals'] = agg['dismissals'].fillna(0).astype(int)

    # Derived metrics
    agg['strike_rate'] = np.where(agg['balls_faced'] > 0, agg['runs'] / agg['balls_faced'] * 100.0, 0.0).round(2)
    agg['batting_average'] = np.where(agg['dismissals'] > 0, (agg['runs'] / agg['dismissals']).round(2), np.nan)
    agg['runs_per_innings'] = np.where(agg['innings'] > 0, (agg['runs'] / agg['innings']).round(2), 0.0)
    agg['average'] = agg['batting_average']  # backwards compatibility alias
    agg['boundary_pct'] = np.where(agg['balls_faced'] > 0, ((agg['fours'] + agg['sixes']) / agg['balls_faced'] * 100.0).round(2), 0.0)
    agg['dot_pct'] = np.where(agg['balls_faced'] > 0, (agg['dots'] / agg['balls_faced'] * 100.0).round(2), 0.0)

    # Scoring consistency (CV of per-innings runs)
    per_innings = faced.groupby(['striker_id', 'match_id', 'innings'])['runs'].sum().reset_index(name='inn_runs')
    cv = per_innings.groupby('striker_id')['inn_runs'].agg(['mean', 'std']).reset_index()
    cv['scoring_consistency'] = np.where(cv['mean'] > 0, (cv['std'] / cv['mean']).round(3), np.nan)
    agg = agg.merge(cv[['striker_id', 'scoring_consistency']], on='striker_id', how='left')

    # Filter minimum balls
    agg = agg[agg['balls_faced'] >= min_balls].copy()
    return agg.sort_values('runs', ascending=False).reset_index(drop=True)


def compute_batter_phase_stats(df: pd.DataFrame, min_balls: int = 20) -> pd.DataFrame:
    """Per-batter stats by innings_phase."""
    faced = df[df['is_ball_faced']].copy()
    fours_col = 'is_four_validated' if 'is_four_validated' in faced.columns else 'is_four'
    sixes_col = 'is_six_validated' if 'is_six_validated' in faced.columns else 'is_six'

    agg = faced.groupby(['striker_id', 'innings_phase']).agg(
        player_name=('striker_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        balls_faced=('runs', 'count'),
        runs=('runs', 'sum'),
        fours=(fours_col, 'sum'),
        sixes=(sixes_col, 'sum'),
    ).reset_index()

    agg['strike_rate'] = np.where(agg['balls_faced'] > 0, (agg['runs'] / agg['balls_faced'] * 100.0).round(2), 0.0)
    agg['boundary_pct'] = np.where(agg['balls_faced'] > 0, ((agg['fours'] + agg['sixes']) / agg['balls_faced'] * 100.0).round(2), 0.0)

    return agg[agg['balls_faced'] >= min_balls].sort_values(['striker_id', 'innings_phase']).reset_index(drop=True)


def compute_batter_position_stats(df: pd.DataFrame, min_balls: int = 30) -> pd.DataFrame:
    """Per-batter stats by batting_order."""
    faced = df[df['is_ball_faced']].copy()
    fours_col = 'is_four_validated' if 'is_four_validated' in faced.columns else 'is_four'
    sixes_col = 'is_six_validated' if 'is_six_validated' in faced.columns else 'is_six'

    agg = faced.groupby(['striker_id', 'batting_order']).agg(
        player_name=('striker_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        balls_faced=('runs', 'count'),
        runs=('runs', 'sum'),
        fours=(fours_col, 'sum'),
        sixes=(sixes_col, 'sum'),
    ).reset_index()

    agg['strike_rate'] = np.where(agg['balls_faced'] > 0, (agg['runs'] / agg['balls_faced'] * 100.0).round(2), 0.0)
    return agg[agg['balls_faced'] >= min_balls].sort_values(['striker_id', 'batting_order']).reset_index(drop=True)


def compute_batter_vs_bowling_type(df: pd.DataFrame, min_balls: int = 20) -> pd.DataFrame:
    """Per-batter stats vs pace_or_spin."""
    faced = df[df['is_ball_faced']].copy()
    fours_col = 'is_four_validated' if 'is_four_validated' in faced.columns else 'is_four'
    sixes_col = 'is_six_validated' if 'is_six_validated' in faced.columns else 'is_six'

    agg = faced.groupby(['striker_id', 'pace_or_spin']).agg(
        player_name=('striker_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        balls_faced=('runs', 'count'),
        runs=('runs', 'sum'),
        fours=(fours_col, 'sum'),
        sixes=(sixes_col, 'sum'),
    ).reset_index()

    agg['strike_rate'] = np.where(agg['balls_faced'] > 0, (agg['runs'] / agg['balls_faced'] * 100.0).round(2), 0.0)
    return agg[agg['balls_faced'] >= min_balls].sort_values(['striker_id', 'pace_or_spin']).reset_index(drop=True)
