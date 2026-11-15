"""Innings-level context builder for ball-by-ball data.

Adds match-situation columns to each delivery: wickets fallen, legal-ball windows,
recent wicket pressure, batting/bowling crisis context, and over-ball position.
"""
import numpy as np
import pandas as pd


def build_innings_context(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Add match context columns to each delivery strictly using pre-delivery information.

    For each delivery (ordered by match_id, innings, innings_ball_num):
    - wickets_fallen_before: cumulative wickets fallen BEFORE this delivery
    - batting_wickets_remaining: 10 - wickets_fallen_before (wickets in hand)
    - wickets_in_last_12_deliveries: wickets in the 12 delivery events before this one
    - wickets_in_last_12_legal_balls: wickets in the 12 legal balls before this one
    - runs_in_last_12_legal_balls: runs conceded in last 12 legal balls
    - boundaries_in_last_12_legal_balls: boundaries in last 12 legal balls
    - dots_in_last_12_legal_balls: dots in last 12 legal balls
    - cumulative_legal_balls: legal balls bowled in innings BEFORE this delivery
    - legal_balls_remaining: max(0, 120 - cumulative_legal_balls)
    - recent_wicket_cluster: True if 2+ wickets in last 12 deliveries
    - recent_wicket_cluster_legal: True if 2+ wickets in last 12 legal balls
    - balls_since_last_wicket: deliveries since last wicket (999 if none)
    - batter_balls_faced: cumulative balls faced by striker BEFORE this delivery
    - batter_runs_scored: cumulative runs scored by striker BEFORE this delivery
    - is_new_batter: True if batter_balls_faced < 5 (vulnerability window)
    - batter_entry_wickets: wickets fallen when batter first appeared
    - over_ball: legal ball number within the over (1-6)

    Parameters
    ----------
    bbb_df : pd.DataFrame
        Cleaned ball-by-ball data.

    Returns
    -------
    pd.DataFrame
        Input dataframe with pre-delivery context columns appended.
    """
    df = bbb_df.sort_values(['match_id', 'innings', 'innings_ball_num']).copy()
    df = df.reset_index(drop=True)

    n = len(df)
    out_wickets_before = np.zeros(n, dtype=np.int32)
    out_wickets_12_del = np.zeros(n, dtype=np.int32)
    out_wickets_12_leg = np.zeros(n, dtype=np.int32)
    out_runs_12_leg = np.zeros(n, dtype=np.int32)
    out_bnd_12_leg = np.zeros(n, dtype=np.int32)
    out_dots_12_leg = np.zeros(n, dtype=np.int32)
    out_cum_legal = np.zeros(n, dtype=np.int32)
    out_cluster_del = np.zeros(n, dtype=bool)
    out_cluster_leg = np.zeros(n, dtype=bool)
    out_balls_since = np.full(n, 999, dtype=np.int32)
    out_bf = np.zeros(n, dtype=np.int32)
    out_br = np.zeros(n, dtype=np.int32)
    out_new = np.zeros(n, dtype=bool)
    out_entry_w = np.zeros(n, dtype=np.int32)
    out_over_ball = np.zeros(n, dtype=np.int32)

    is_wkt_arr = df['is_wicket'].values.astype(bool)
    striker_arr = df['striker_id'].values
    is_faced_arr = df['is_ball_faced'].values.astype(bool)
    runs_arr = df['runs'].values.astype(np.int32)
    is_legal_arr = df['is_legal_ball'].values.astype(bool)
    over_arr = df['overid'].values

    # Determine boundary and dot indicators
    if 'boundary_validated' in df.columns:
        is_bnd_arr = df['boundary_validated'].values.astype(bool)
    elif 'is_four' in df.columns and 'is_six' in df.columns:
        is_bnd_arr = (df['is_four'] | df['is_six']).values.astype(bool)
    else:
        is_bnd_arr = np.isin(runs_arr, [4, 6])

    if 'is_dot_ball' in df.columns:
        is_dot_arr = df['is_dot_ball'].values.astype(bool)
    else:
        is_dot_arr = is_legal_arr & (runs_arr == 0)

    grp = df.groupby(['match_id', 'innings'], sort=False)

    for _, group_idx in grp.groups.items():
        positions = group_idx.values
        start = positions[0]
        end = positions[-1] + 1
        length = end - start

        is_wkt = is_wkt_arr[start:end]
        strikers = striker_arr[start:end]
        is_faced = is_faced_arr[start:end]
        runs = runs_arr[start:end]
        is_legal = is_legal_arr[start:end]
        overs = over_arr[start:end]
        is_bnd = is_bnd_arr[start:end]
        is_dot = is_dot_arr[start:end]

        # Cumulative wickets before
        cum_wkt = np.cumsum(is_wkt.astype(np.int32))
        shifted_wkt = np.empty(length, dtype=np.int32)
        shifted_wkt[0] = 0
        shifted_wkt[1:] = cum_wkt[:-1]
        out_wickets_before[start:end] = shifted_wkt

        # Cumulative legal balls before
        cum_leg = np.cumsum(is_legal.astype(np.int32))
        shifted_leg = np.empty(length, dtype=np.int32)
        shifted_leg[0] = 0
        shifted_leg[1:] = cum_leg[:-1]
        out_cum_legal[start:end] = shifted_leg

        # Delivery event window (last 12 delivery events)
        wkt_int = is_wkt.astype(np.int32)
        for i in range(length):
            lb_del = max(0, i - 12)
            out_wickets_12_del[start + i] = np.sum(wkt_int[lb_del:i])
        out_cluster_del[start:end] = out_wickets_12_del[start:end] >= 2

        # Legal ball window (last 12 legal balls, capturing wickets/boundaries/runs on extras within the span)
        legal_indices = []
        for i in range(length):
            if len(legal_indices) > 0:
                recent_legal = legal_indices[-12:]
                win_start = recent_legal[0]
                out_wickets_12_leg[start + i] = np.sum(wkt_int[win_start:i])
                out_runs_12_leg[start + i] = np.sum(runs[win_start:i])
                out_bnd_12_leg[start + i] = np.sum(is_bnd[win_start:i])
                out_dots_12_leg[start + i] = np.sum(is_dot[recent_legal])
            if is_legal[i]:
                legal_indices.append(i)

        out_cluster_leg[start:end] = out_wickets_12_leg[start:end] >= 2

        # Balls since last wicket
        last_wkt_pos = -1
        for i in range(length):
            if last_wkt_pos >= 0:
                out_balls_since[start + i] = i - last_wkt_pos
            if is_wkt[i]:
                last_wkt_pos = i

        # Over ball
        legal_count = 0
        cur_over = -1
        for i in range(length):
            if overs[i] != cur_over:
                cur_over = overs[i]
                legal_count = 0
            if is_legal[i]:
                legal_count += 1
            out_over_ball[start + i] = legal_count if legal_count > 0 else 1

        # Batter context
        batter_bf = {}
        batter_br = {}
        batter_entry = {}

        for i in range(length):
            pos = start + i
            sid = strikers[i]

            if sid not in batter_bf:
                batter_bf[sid] = 0
                batter_br[sid] = 0
                batter_entry[sid] = shifted_wkt[i]

            out_bf[pos] = batter_bf[sid]
            out_br[pos] = batter_br[sid]
            out_new[pos] = batter_bf[sid] == 0
            out_entry_w[pos] = batter_entry[sid]

            if is_faced[i]:
                batter_bf[sid] += 1
            batter_br[sid] += int(runs[i])

    df['wickets_fallen_before'] = out_wickets_before
    df['batting_wickets_remaining'] = 10 - out_wickets_before
    df['wickets_in_last_12_deliveries'] = out_wickets_12_del
    df['wickets_in_last_12_balls'] = out_wickets_12_del  # backwards compatibility alias
    df['wickets_in_last_12_legal_balls'] = out_wickets_12_leg
    df['runs_in_last_12_legal_balls'] = out_runs_12_leg
    df['boundaries_in_last_12_legal_balls'] = out_bnd_12_leg
    df['dots_in_last_12_legal_balls'] = out_dots_12_leg
    df['cumulative_legal_balls'] = out_cum_legal
    df['legal_balls_remaining'] = np.maximum(0, 120 - out_cum_legal)
    df['recent_wicket_cluster'] = out_cluster_del  # backwards compatibility alias
    df['recent_wicket_cluster_legal'] = out_cluster_leg
    df['balls_since_last_wicket'] = out_balls_since
    df['batter_balls_faced'] = out_bf
    df['batter_runs_scored'] = out_br
    df['is_new_batter'] = out_new
    df['batter_entry_wickets'] = out_entry_w
    df['over_ball'] = out_over_ball

    return df
