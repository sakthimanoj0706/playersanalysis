"""Delivery-level batting context features."""
import numpy as np
import pandas as pd


def build_delivery_context(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Add delivery-level batting context columns.

    - dot_ball: True if runs == 0 and extras_category == 'None'
    - boundary: True if is_four or is_six
    - scoring_shot: True if runs > 0
    - is_dot_after_dot: True if previous ball faced by same batter was also a dot
    - consecutive_dots: consecutive dot balls by this batter before this delivery
    """
    df = bbb_df.sort_values(['match_id', 'innings', 'innings_ball_num']).copy()

    df['dot_ball'] = (df['runs'] == 0) & (df['extras_category'] == 'None')
    df['boundary'] = df['is_four'] | df['is_six']
    df['scoring_shot'] = df['runs'] > 0

    # Consecutive dots per batter within an innings
    n = len(df)
    is_dot_after_dot = np.zeros(n, dtype=bool)
    consec_dots = np.zeros(n, dtype=np.int32)

    dot_arr = df['dot_ball'].values.astype(bool)
    faced_arr = df['is_ball_faced'].values.astype(bool)
    striker_arr = df['striker_id'].values
    match_arr = df['match_id'].values
    inn_arr = df['innings'].values

    # Track per-batter dot streak within each innings
    prev_match = prev_inn = None
    batter_streak = {}  # striker_id -> current consecutive dot count

    for i in range(n):
        m, inn, sid = match_arr[i], inn_arr[i], striker_arr[i]
        if m != prev_match or inn != prev_inn:
            batter_streak = {}
            prev_match, prev_inn = m, inn

        streak = batter_streak.get(sid, 0)
        consec_dots[i] = streak
        is_dot_after_dot[i] = streak > 0 and faced_arr[i] and dot_arr[i]

        # Update streak AFTER recording
        if faced_arr[i]:
            if dot_arr[i]:
                batter_streak[sid] = streak + 1
            else:
                batter_streak[sid] = 0

    df['is_dot_after_dot'] = is_dot_after_dot
    df['consecutive_dots'] = consec_dots
    return df
