"""Partnership tracking for ball-by-ball cricket data."""
import numpy as np
import pandas as pd


def build_partnerships(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Track batting partnerships delivery-by-delivery.

    A partnership consists of the pair of batters at the crease. It starts at the
    beginning of an innings or immediately after a dismissal (including dismissals
    occurring on wide deliveries or run outs).

    Adds:
    - partnership_id: sequential partnership index within the innings (1-based)
    - partnership_batter_runs: cumulative runs off the bat BEFORE this delivery
    - partnership_deliveries: cumulative delivery events BEFORE this delivery
    - partnership_balls_faced: cumulative faced balls (excl. wides) BEFORE this delivery
    - partnership_legal_balls: cumulative legal deliveries BEFORE this delivery
    - partnership_runs: alias for partnership_batter_runs (provisional batter runs)
    - partnership_balls: alias for partnership_balls_faced
    - is_wicket_on_wide: True if a dismissal occurred on a wide delivery
    """
    df = bbb_df.sort_values(['match_id', 'innings', 'innings_ball_num']).copy()
    df = df.reset_index(drop=True)

    n = len(df)
    p_id = np.zeros(n, dtype=np.int32)
    p_batter_runs = np.zeros(n, dtype=np.int32)
    p_delivs = np.zeros(n, dtype=np.int32)
    p_balls_faced = np.zeros(n, dtype=np.int32)
    p_legal = np.zeros(n, dtype=np.int32)

    striker_arr = df['striker_id'].values
    non_striker_arr = df['non_striker_id'].values
    match_arr = df['match_id'].values
    inn_arr = df['innings'].values
    runs_arr = df['runs'].values.astype(np.int32)
    faced_arr = df['is_ball_faced'].values.astype(bool)
    legal_arr = df['is_legal_ball'].values.astype(bool) if 'is_legal_ball' in df.columns else faced_arr
    wkt_arr = df['is_wicket'].values.astype(bool) if 'is_wicket' in df.columns else np.zeros(n, dtype=bool)

    if 'extras_category' in df.columns:
        is_wide_arr = (df['extras_category'].values == 'wide')
    else:
        is_wide_arr = np.zeros(n, dtype=bool)

    df['is_wicket_on_wide'] = wkt_arr & is_wide_arr

    prev_match = prev_inn = None
    cur_pair = None
    cur_pid = 0
    cum_runs = 0
    cum_delivs = 0
    cum_faced = 0
    cum_legal = 0

    for i in range(n):
        m, inn = match_arr[i], inn_arr[i]
        pair = frozenset([striker_arr[i], non_striker_arr[i]])

        if m != prev_match or inn != prev_inn:
            # New innings starts
            prev_match, prev_inn = m, inn
            cur_pair = pair
            cur_pid = 1
            cum_runs = 0
            cum_delivs = 0
            cum_faced = 0
            cum_legal = 0
        else:
            # Check if pair changed (new batter arrived)
            if pair != cur_pair:
                cur_pair = pair
                cur_pid += 1
                cum_runs = 0
                cum_delivs = 0
                cum_faced = 0
                cum_legal = 0

        # Record BEFORE values
        p_id[i] = cur_pid
        p_batter_runs[i] = cum_runs
        p_delivs[i] = cum_delivs
        p_balls_faced[i] = cum_faced
        p_legal[i] = cum_legal

        # Update AFTER current delivery
        cum_runs += int(runs_arr[i])
        cum_delivs += 1
        if faced_arr[i]:
            cum_faced += 1
        if legal_arr[i]:
            cum_legal += 1

    df['partnership_id'] = p_id
    df['partnership_batter_runs'] = p_batter_runs
    df['partnership_deliveries'] = p_delivs
    df['partnership_balls_faced'] = p_balls_faced
    df['partnership_legal_balls'] = p_legal
    df['partnership_runs'] = p_batter_runs
    df['partnership_balls'] = p_balls_faced

    return df
