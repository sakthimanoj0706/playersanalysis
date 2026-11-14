"""Bowler performance analysis."""
import numpy as np
import pandas as pd


def compute_bowler_stats(df: pd.DataFrame, min_balls: int = 60) -> pd.DataFrame:
    """Per-bowler aggregate statistics.

    NOTE: provisional_runs_conceded uses the `runs` column directly.
    Economy rate is PROVISIONAL / BLOCKED from official ranking until extras
    semantics are clarified by RR.
    Bowler wickets strictly exclude run outs, retired outs, and obstructing the field.
    """
    legal_df = df[df['is_legal_ball']].copy()

    agg = legal_df.groupby('bowler_id').agg(
        player_name=('bowler_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        matches=('match_id', 'nunique'),
        legal_balls=('runs', 'count'),
        provisional_runs_conceded=('runs', 'sum'),
        wickets=('is_bowler_wicket', 'sum'),
    ).reset_index()

    # Total deliveries including extras
    tot_deliv = df.groupby('bowler_id').size().reset_index(name='total_deliveries')
    agg = agg.merge(tot_deliv, on='bowler_id', how='left')

    # Innings bowled (distinct match_id, innings per bowler)
    inn_count = (
        df[['bowler_id', 'match_id', 'innings']]
        .drop_duplicates()
        .groupby('bowler_id')
        .size()
        .reset_index(name='innings_bowled')
    )
    agg = agg.merge(inn_count, on='bowler_id', how='left')

    # Dot balls
    if 'dot_ball' in df.columns:
        dots = df[df['is_legal_ball']].groupby('bowler_id')['dot_ball'].sum().reset_index(name='dot_balls')
    else:
        dots = (
            df[df['is_legal_ball']]
            .groupby('bowler_id')['runs']
            .agg(lambda s: (s == 0).sum())
            .reset_index(name='dot_balls')
        )
    agg = agg.merge(dots, on='bowler_id', how='left')
    agg['dot_balls'] = agg['dot_balls'].fillna(0).astype(int)

    # Derived metrics
    agg['bowler_strike_rate'] = np.where(
        agg['wickets'] > 0, (agg['legal_balls'] / agg['wickets']).round(2), np.nan
    )
    agg['dot_pct'] = np.where(
        agg['legal_balls'] > 0, (agg['dot_balls'] / agg['legal_balls'] * 100.0).round(2), 0.0
    )
    # Provisional economy (batter runs conceded per 6 legal balls)
    agg['provisional_economy'] = np.where(
        agg['legal_balls'] > 0,
        (agg['provisional_runs_conceded'] / (agg['legal_balls'] / 6.0)).round(2),
        0.0
    )

    # Overs display format (e.g. 24.3)
    agg['overs'] = (agg['legal_balls'] // 6).astype(str) + '.' + (agg['legal_balls'] % 6).astype(str)

    agg = agg[agg['legal_balls'] >= min_balls].copy()
    return agg.sort_values('wickets', ascending=False).reset_index(drop=True)


def compute_bowler_phase_stats(df: pd.DataFrame, min_balls: int = 20) -> pd.DataFrame:
    """Per-bowler stats by innings_phase."""
    legal_df = df[df['is_legal_ball']].copy()

    agg = legal_df.groupby(['bowler_id', 'innings_phase']).agg(
        player_name=('bowler_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        legal_balls=('runs', 'count'),
        provisional_runs_conceded=('runs', 'sum'),
        wickets=('is_bowler_wicket', 'sum'),
    ).reset_index()

    if 'dot_ball' in legal_df.columns:
        dots = legal_df.groupby(['bowler_id', 'innings_phase'])['dot_ball'].sum().reset_index(name='dot_balls')
    else:
        dots = legal_df.groupby(['bowler_id', 'innings_phase'])['runs'].agg(lambda s: (s == 0).sum()).reset_index(name='dot_balls')
    agg = agg.merge(dots, on=['bowler_id', 'innings_phase'], how='left')
    agg['dot_balls'] = agg['dot_balls'].fillna(0).astype(int)

    agg['dot_pct'] = np.where(agg['legal_balls'] > 0, (agg['dot_balls'] / agg['legal_balls'] * 100.0).round(2), 0.0)
    agg['bowler_strike_rate'] = np.where(agg['wickets'] > 0, (agg['legal_balls'] / agg['wickets']).round(2), np.nan)

    return agg[agg['legal_balls'] >= min_balls].sort_values(['bowler_id', 'innings_phase']).reset_index(drop=True)


def compute_bowler_vs_batting_type(df: pd.DataFrame, min_balls: int = 20) -> pd.DataFrame:
    """Per-bowler stats vs RHB/LHB."""
    legal_df = df[df['is_legal_ball']].copy()

    agg = legal_df.groupby(['bowler_id', 'batting_type']).agg(
        player_name=('bowler_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        legal_balls=('runs', 'count'),
        provisional_runs_conceded=('runs', 'sum'),
        wickets=('is_bowler_wicket', 'sum'),
    ).reset_index()

    agg['bowler_strike_rate'] = np.where(agg['wickets'] > 0, (agg['legal_balls'] / agg['wickets']).round(2), np.nan)
    return agg[agg['legal_balls'] >= min_balls].sort_values(['bowler_id', 'batting_type']).reset_index(drop=True)
