"""Venue analysis."""
import numpy as np
import pandas as pd


def compute_venue_stats(df: pd.DataFrame, matches_df: pd.DataFrame) -> pd.DataFrame:
    """Per-venue aggregate statistics.

    venue_id is available but no venue-name table exists in the pack.
    We use venue_country as the primary grouping, with venue_id for granularity.
    """
    # Join venue_id from matches if not already present
    if 'venue_id' not in df.columns:
        venue_map = matches_df[['match_id', 'venue_id']].drop_duplicates()
        df = df.merge(venue_map, on='match_id', how='left')

    # Per venue_id stats
    agg = df.groupby(['venue_id', 'venue_country']).agg(
        matches=('match_id', 'nunique'),
        total_deliveries=('runs', 'count'),
        total_runs=('runs', 'sum'),  # provisional batter runs only
        total_wickets=('is_wicket', 'sum'),
        boundaries=('boundary', 'sum') if 'boundary' in df.columns else ('is_four', 'sum'),
        sixes=('is_six', 'sum'),
    ).reset_index()

    # Per-innings averages
    innings_agg = df.groupby(['venue_id', 'match_id', 'innings']).agg(
        inn_runs=('runs', 'sum'),
        inn_wickets=('is_wicket', 'sum'),
    ).reset_index()

    venue_inn = innings_agg.groupby('venue_id').agg(
        avg_innings_runs=('inn_runs', 'mean'),
        avg_innings_wickets=('inn_wickets', 'mean'),
    ).reset_index()

    agg = agg.merge(venue_inn, on='venue_id', how='left')

    # Pace vs spin wickets
    pace_wkt = df[df['is_bowler_wicket'] & (df['pace_or_spin'] == 'Pace')].groupby('venue_id').size().reset_index(name='pace_wickets')
    spin_wkt = df[df['is_bowler_wicket'] & (df['pace_or_spin'] == 'Spin')].groupby('venue_id').size().reset_index(name='spin_wickets')
    agg = agg.merge(pace_wkt, on='venue_id', how='left').merge(spin_wkt, on='venue_id', how='left')
    agg['pace_wickets'] = agg['pace_wickets'].fillna(0).astype(int)
    agg['spin_wickets'] = agg['spin_wickets'].fillna(0).astype(int)
    total_venue_wkt = agg['pace_wickets'] + agg['spin_wickets']
    agg['pace_wicket_pct'] = np.where(total_venue_wkt > 0, agg['pace_wickets'] / total_venue_wkt * 100, 0)

    return agg.sort_values('matches', ascending=False).reset_index(drop=True)
