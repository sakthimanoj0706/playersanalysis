"""Dual Pressure Model Engine for SupeRR Intelligence.

Constructs two logically independent, pre-delivery pressure models:
1. Batting Crisis Pressure Proxy: measures batting collapse, wickets lost,
   stagnation, and entry vulnerability.
2. Bowling Defensive Pressure Proxy: measures resource threat (wickets in hand),
   critical phase (death overs, powerplay field restrictions), and opponent
   boundary momentum.

IMPORTANT: No score-dependent features (RRR, total runs) are used because extras
semantics are unconfirmed. All features use strictly pre-delivery information to
guarantee zero target leakage.
"""
import numpy as np
import pandas as pd


# ── BATTING CRISIS PRESSURE PROXY ──────────────────────────────────────────

def compute_batting_pressure(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pre-delivery batting crisis pressure score and categories.

    Components:
    1. Wicket depletion: wickets lost before delivery (0 to 3.5 pts)
    2. Wicket collapse/cluster: 2+ wickets in last 12 legal balls (0 or 2.0 pts)
    3. Batter novelty/vulnerability: first 5 balls faced (0 to 1.5 pts)
    4. Scoring stagnation: consecutive dots or low scoring in last 12 balls (0 to 1.5 pts)
    5. Innings phase multiplier: death overs 1.25x, middle 1.0x, powerplay 0.95x

    Scale: 0.0 to 10.0
    Categories:
    - None: [0.0, 1.5)
    - Low: [1.5, 3.5)
    - Moderate: [3.5, 5.5)
    - High: [5.5, 7.5)
    - Extreme: [7.5, 10.0]
    """
    df = df.copy()

    # 1. Wicket depletion (0 to 3.5)
    w_before = df['wickets_fallen_before'].values.astype(float)
    c_wkt = np.clip(w_before * 0.45, 0.0, 3.5)

    # 2. Wicket collapse in last 12 legal balls (0 or 2.0)
    if 'wickets_in_last_12_legal_balls' in df.columns:
        w12 = df['wickets_in_last_12_legal_balls'].values.astype(float)
        c_cluster = np.where(w12 >= 2, 2.0, np.where(w12 == 1, 0.75, 0.0))
    elif 'recent_wicket_cluster' in df.columns:
        c_cluster = np.where(df['recent_wicket_cluster'].values, 2.0, 0.0)
    else:
        c_cluster = np.zeros(len(df))

    # 3. Batter entry vulnerability (0 to 1.5)
    bf = df['batter_balls_faced'].values.astype(float)
    c_novelty = np.where(bf < 5, 1.5 * (1.0 - bf / 5.0), 0.0)

    # 4. Stagnation / dots pressure (0 to 1.5)
    consec_dots = df['consecutive_dots'].values.astype(float) if 'consecutive_dots' in df.columns else np.zeros(len(df))
    dots_12 = df['dots_in_last_12_legal_balls'].values.astype(float) if 'dots_in_last_12_legal_balls' in df.columns else np.zeros(len(df))
    c_stagnation = np.clip(consec_dots * 0.3 + (dots_12 / 12.0) * 0.6, 0.0, 1.5)

    # 5. Phase multiplier
    phase_weights = {'powerplay': 0.95, 'middle': 1.0, 'death': 1.25, 'unknown': 1.0}
    phase_mult = df['innings_phase'].map(phase_weights).fillna(1.0).values

    raw_bat_score = (c_wkt + c_cluster + c_novelty + c_stagnation) * phase_mult
    df['batting_pressure_score'] = np.clip(raw_bat_score, 0.0, 10.0).round(2)

    # Batting pressure tier
    df['batting_pressure_tier'] = pd.cut(
        df['batting_pressure_score'],
        bins=[-0.01, 1.5, 3.5, 5.5, 7.5, 10.01],
        labels=['none', 'low', 'moderate', 'high', 'extreme']
    )

    # Comparison groupings
    df['is_batting_high_pressure'] = df['batting_pressure_tier'].isin(['high', 'extreme'])
    df['is_batting_moderate_pressure'] = df['batting_pressure_tier'] == 'moderate'
    df['is_batting_normal_pressure'] = df['batting_pressure_tier'].isin(['none', 'low'])

    # Backwards compatibility alias
    df['is_pressure_delivery'] = df['is_batting_high_pressure']
    df['pressure_score'] = df['batting_pressure_score']
    df['pressure_category'] = df['batting_pressure_tier']

    return df


class BattingPressureEngine:
    """Independent pre-delivery pressure engine for batting match situations."""

    @staticmethod
    def calculate(df: pd.DataFrame) -> pd.DataFrame:
        """Compute pre-delivery batting crisis pressure score and tiers."""
        return compute_batting_pressure(df)

    @staticmethod
    def classify(df: pd.DataFrame) -> pd.DataFrame:
        """Alias for calculate to maintain standard interface."""
        return compute_batting_pressure(df)


# ── BOWLING DEFENSIVE PRESSURE PROXY ───────────────────────────────────────

def compute_bowling_pressure(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pre-delivery bowling defensive pressure score and categories.

    Components:
    1. Batting resource threat: wickets in hand for batting team (0 to 3.0 pts)
       (Fewer wickets lost = opponent has resources to attack = high bowling pressure)
    2. Critical phase / field restrictions: death overs 3.0, powerplay 2.0, middle 1.0
    3. Opponent momentum: boundaries in last 12 legal balls (0 to 2.5 pts)
    4. Run-flow pressure: low dot balls in last 12 legal balls (0 to 1.5 pts)

    Scale: 0.0 to 10.0
    Categories:
    - None: [0.0, 2.5)
    - Low: [2.5, 4.5)
    - Moderate: [4.5, 6.5)
    - High: [6.5, 8.0)
    - Extreme: [8.0, 10.0]
    """
    df = df.copy()

    # 1. Batting resource threat (0 to 3.0 pts)
    # Wickets in hand = 10 - wickets_fallen_before
    w_rem = df['batting_wickets_remaining'].values.astype(float) if 'batting_wickets_remaining' in df.columns else (10.0 - df['wickets_fallen_before'].values.astype(float))
    # 8-10 wickets in hand -> 3.0, 6-7 -> 2.0, 4-5 -> 1.0, 1-3 -> 0.2
    c_resource = np.where(w_rem >= 8, 3.0, np.where(w_rem >= 6, 2.0, np.where(w_rem >= 4, 1.0, 0.2)))

    # 2. Critical phase / field restrictions (1.0 to 3.0 pts)
    phase_pts = {'death': 3.0, 'powerplay': 2.0, 'middle': 1.0, 'unknown': 1.0}
    c_phase = df['innings_phase'].map(phase_pts).fillna(1.0).values

    # 3. Opponent boundary momentum (0 to 2.5 pts)
    if 'boundaries_in_last_12_legal_balls' in df.columns:
        b12 = df['boundaries_in_last_12_legal_balls'].values.astype(float)
        c_momentum = np.where(b12 >= 3, 2.5, np.where(b12 == 2, 1.6, np.where(b12 == 1, 0.8, 0.0)))
    else:
        c_momentum = np.zeros(len(df))

    # 4. Strike-rotation pressure / few dots (0 to 1.5 pts)
    if 'dots_in_last_12_legal_balls' in df.columns:
        d12 = df['dots_in_last_12_legal_balls'].values.astype(float)
        # Fewer dots = batting side scoring every ball = high pressure
        c_rotation = np.clip(1.5 * (1.0 - d12 / 12.0), 0.0, 1.5)
    else:
        c_rotation = np.zeros(len(df))

    raw_bowl_score = c_resource + c_phase + c_momentum + c_rotation
    df['bowling_pressure_score'] = np.clip(raw_bowl_score, 0.0, 10.0).round(2)

    # Bowling pressure tier
    df['bowling_pressure_tier'] = pd.cut(
        df['bowling_pressure_score'],
        bins=[-0.01, 2.5, 4.5, 6.5, 8.0, 10.01],
        labels=['none', 'low', 'moderate', 'high', 'extreme']
    )

    # Comparison groupings
    df['is_bowling_high_pressure'] = df['bowling_pressure_tier'].isin(['high', 'extreme'])
    df['is_bowling_moderate_pressure'] = df['bowling_pressure_tier'] == 'moderate'
    df['is_bowling_normal_pressure'] = df['bowling_pressure_tier'].isin(['none', 'low'])

    return df


def classify_dual_pressure(df: pd.DataFrame) -> pd.DataFrame:
    """Run both batting and bowling pressure models on delivery dataframe."""
    df = compute_batting_pressure(df)
    df = compute_bowling_pressure(df)
    return df


class BowlingPressureEngine:
    """Independent pre-delivery pressure engine for bowling defensive match situations."""

    @staticmethod
    def calculate(df: pd.DataFrame) -> pd.DataFrame:
        """Compute pre-delivery bowling defensive pressure score and tiers."""
        return compute_bowling_pressure(df)

    @staticmethod
    def classify(df: pd.DataFrame) -> pd.DataFrame:
        """Alias for calculate to maintain standard interface."""
        return compute_bowling_pressure(df)


def get_tier_breakdown(df: pd.DataFrame, pressure_col: str) -> pd.DataFrame:
    """Summary of delivery distribution across pressure tiers."""
    summary = df.groupby(pressure_col, observed=True).agg(
        deliveries=('runs', 'count'),
        avg_runs=('runs', 'mean'),
        boundary_rate=('boundary', 'mean') if 'boundary' in df.columns else ('is_four', 'mean'),
        wicket_rate=('is_wicket', 'mean'),
        dot_rate=('dot_ball', 'mean') if 'dot_ball' in df.columns else ('runs', lambda x: (x == 0).mean()),
    ).reset_index()
    summary['pct_of_deliveries'] = (summary['deliveries'] / summary['deliveries'].sum() * 100).round(2)
    return summary
