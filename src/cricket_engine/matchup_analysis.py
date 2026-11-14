"""Batter vs Bowler matchup analysis."""
import numpy as np
import pandas as pd


def compute_matchups(df: pd.DataFrame, min_balls: int = 6) -> pd.DataFrame:
    """Batter vs Bowler matchup statistics.

    Only counts deliveries where the batter faced the ball (excludes wides).
    Dismissals: only bowler-attributed wickets where the dismissed player is the striker.
    """
    faced = df[df['is_ball_faced']].copy()

    agg = faced.groupby(['striker_id', 'bowler_id']).agg(
        batter_name=('striker_name', lambda x: x.mode().iloc[0]),
        bowler_name=('bowler_name', lambda x: x.mode().iloc[0]),
        balls=('runs', 'count'),
        runs=('runs', 'sum'),
        fours=('is_four', 'sum'),
        sixes=('is_six', 'sum'),
    ).reset_index()

    # Dismissals: bowler wickets where dismissed_player_id == striker_id
    wkt = df[df['is_bowler_wicket'] & (df['dismissed_player_id'] == df['striker_id'])].copy()
    dismissals = wkt.groupby(['striker_id', 'bowler_id']).size().reset_index(name='dismissals')
    agg = agg.merge(dismissals, on=['striker_id', 'bowler_id'], how='left')
    agg['dismissals'] = agg['dismissals'].fillna(0).astype(int)

    # Dots
    if 'dot_ball' in faced.columns:
        dots = faced.groupby(['striker_id', 'bowler_id'])['dot_ball'].sum().reset_index(name='dot_balls')
    else:
        dots = faced.groupby(['striker_id', 'bowler_id']).apply(
            lambda g: ((g['runs'] == 0) & (g['extras_category'] == 'None')).sum()
        ).reset_index(name='dot_balls')
    agg = agg.merge(dots, on=['striker_id', 'bowler_id'], how='left')

    # Derived
    agg['strike_rate'] = np.where(agg['balls'] > 0, agg['runs'] / agg['balls'] * 100, 0)
    agg['dot_pct'] = np.where(agg['balls'] > 0, agg['dot_balls'] / agg['balls'] * 100, 0)

    agg = agg[agg['balls'] >= min_balls].copy()
    return agg.sort_values('balls', ascending=False).reset_index(drop=True)
