"""Partnership analysis."""
import numpy as np
import pandas as pd


def compute_partnership_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-partnership statistics from ball-by-ball data.

    Requires partnership_id column from context engine.
    Correctly accounts for batter runs vs total partnership deliveries,
    individual balls faced, and wickets occurring on wide deliveries.
    """
    if 'partnership_id' not in df.columns:
        raise ValueError("partnership_id column missing. Run partnership_tracker first.")

    # Group full delivery df to capture all events (including wides)
    def _partnership_agg(g):
        s1 = g.iloc[0]
        b1_id = s1['striker_id']
        b1_name = s1['striker_name']
        b2_id = s1['non_striker_id']
        b2_name = s1['non_striker_name']

        b1_faced = g[(g['striker_id'] == b1_id) & (g['is_ball_faced'])]
        b2_faced = g[(g['striker_id'] == b2_id) & (g['is_ball_faced'])]

        # Batter runs vs total deliveries
        batter_runs = g['runs'].sum()
        total_deliveries = len(g)
        legal_balls = g['is_legal_ball'].sum() if 'is_legal_ball' in g.columns else total_deliveries
        total_balls_faced = len(b1_faced) + len(b2_faced)
        wickets = g['is_wicket'].sum()

        last_row = g.iloc[-1]
        how_ended = last_row['dismissal_type'] if last_row['is_wicket'] else 'not_out'
        wicket_on_wide = last_row['is_wicket'] and (last_row['extras_category'] == 'wide' if 'extras_category' in last_row else False)

        return pd.Series({
            'batter1_id': b1_id, 'batter1_name': b1_name,
            'batter2_id': b2_id, 'batter2_name': b2_name,
            'batter_runs': batter_runs,
            'total_deliveries': total_deliveries,
            'total_balls_faced': total_balls_faced,
            'legal_balls': legal_balls,
            'batter1_runs': b1_faced['runs'].sum() if len(b1_faced) > 0 else 0,
            'batter1_balls': len(b1_faced),
            'batter2_runs': b2_faced['runs'].sum() if len(b2_faced) > 0 else 0,
            'batter2_balls': len(b2_faced),
            'wickets': wickets,
            'how_ended': how_ended,
            'wicket_on_wide': wicket_on_wide,
            'wickets_when_formed': g['wickets_fallen_before'].iloc[0] if 'wickets_fallen_before' in g.columns else -1,
        })

    # Group by (match_id, innings, partnership_id)
    cols = ['match_id', 'innings', 'partnership_id', 'striker_id', 'striker_name', 'non_striker_id', 'non_striker_name', 'runs', 'is_wicket', 'dismissal_type', 'is_ball_faced', 'is_legal_ball', 'wickets_fallen_before']
    sub_df = df[[c for c in cols if c in df.columns]]
    result = sub_df.groupby(['match_id', 'innings', 'partnership_id'], as_index=False).apply(_partnership_agg, include_groups=False).reset_index(drop=True)
    return result


def compute_pair_stats(df: pd.DataFrame, min_partnerships: int = 3) -> pd.DataFrame:
    """Aggregate stats for batting pairs across matches."""
    pships = compute_partnership_stats(df)

    pships['pair_key'] = pships.apply(
        lambda r: tuple(sorted([r['batter1_id'], r['batter2_id']])), axis=1
    )

    pair_agg = pships.groupby('pair_key').agg(
        partnerships=('batter_runs', 'count'),
        total_runs=('batter_runs', 'sum'),
        total_balls_faced=('total_balls_faced', 'sum'),
        total_deliveries=('total_deliveries', 'sum'),
        avg_runs=('batter_runs', 'mean'),
        max_runs=('batter_runs', 'max'),
    ).reset_index()

    # Get names
    name_map = {}
    for _, r in pships.iterrows():
        name_map[r['batter1_id']] = r['batter1_name']
        name_map[r['batter2_id']] = r['batter2_name']

    pair_agg['batter1_name'] = pair_agg['pair_key'].apply(lambda pk: name_map.get(pk[0], ''))
    pair_agg['batter2_name'] = pair_agg['pair_key'].apply(lambda pk: name_map.get(pk[1], ''))

    pair_agg['combined_sr'] = np.where(
        pair_agg['total_balls_faced'] > 0,
        (pair_agg['total_runs'] / pair_agg['total_balls_faced'] * 100.0).round(2),
        0.0
    )

    pair_agg = pair_agg[pair_agg['partnerships'] >= min_partnerships].copy()
    return pair_agg.sort_values('total_runs', ascending=False).reset_index(drop=True)
