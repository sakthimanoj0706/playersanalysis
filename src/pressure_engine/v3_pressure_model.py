"""V3 Match Pressure Modeling Engine.

Provides independent, pre-delivery ex-ante pressure models:
1. Batting Crisis Pressure Model: Measures pre-delivery collapse, resource depletion,
   stagnation, and entry vulnerability.
2. Bowling Defensive Pressure Model: Measures pre-delivery opponent resource threat,
   field restrictions, and opponent boundary momentum.

Zero Target Leakage Guarantee:
Every feature is computed strictly from states established BEFORE the ball is bowled.
No future balls, eventual delivery outcomes, or match results are ingested as inputs.
"""
from typing import Dict, Tuple
import numpy as np
import pandas as pd


class V3PressureModel:
    """Pre-delivery pressure state estimator for batting and bowling situations."""

    @staticmethod
    def compute_batting_crisis_pressure(df: pd.DataFrame) -> pd.DataFrame:
        """Estimate pre-delivery batting crisis pressure score on [0.0, 10.0].

        Components (strictly ex-ante):
        1. Wicket depletion (0 to 3.5 pts): wickets lost before delivery.
        2. Collapse cluster (0 to 2.0 pts): 2+ wickets in last 12 legal balls.
        3. Batter entry vulnerability (0 to 1.5 pts): first 5 balls faced.
        4. Stagnation pressure (0 to 1.5 pts): consecutive dots and low scoring in last 12 balls.
        5. Innings phase multiplier: death overs 1.25x, middle 1.0x, powerplay 0.95x.
        """
        df = df.copy()

        # 1. Wickets fallen before delivery
        if 'wickets_fallen_before' in df.columns:
            w_before = df['wickets_fallen_before'].fillna(0).values.astype(float)
        else:
            w_before = np.zeros(len(df))
        c_wkt = np.clip(w_before * 0.45, 0.0, 3.5)

        # 2. Recent wicket cluster (last 12 legal balls)
        if 'wickets_in_last_12_legal_balls' in df.columns:
            w12 = df['wickets_in_last_12_legal_balls'].fillna(0).values.astype(float)
            c_cluster = np.where(w12 >= 2, 2.0, np.where(w12 == 1, 0.75, 0.0))
        elif 'recent_wicket_cluster' in df.columns:
            c_cluster = np.where(df['recent_wicket_cluster'].fillna(False).values, 2.0, 0.0)
        else:
            c_cluster = np.zeros(len(df))

        # 3. Entry vulnerability (first 5 balls faced by the striker)
        if 'batter_balls_faced' in df.columns:
            bf = df['batter_balls_faced'].fillna(10.0).values.astype(float)
        else:
            bf = np.full(len(df), 10.0)
        c_novelty = np.where(bf < 5, 1.5 * (1.0 - bf / 5.0), 0.0)

        # 4. Stagnation / dots pressure
        if 'consecutive_dots' in df.columns:
            consec_dots = df['consecutive_dots'].fillna(0).values.astype(float)
        else:
            consec_dots = np.zeros(len(df))
            
        if 'dots_in_last_12_legal_balls' in df.columns:
            dots_12 = df['dots_in_last_12_legal_balls'].fillna(0).values.astype(float)
        else:
            dots_12 = np.zeros(len(df))
        c_stagnation = np.clip(consec_dots * 0.3 + (dots_12 / 12.0) * 0.6, 0.0, 1.5)

        # 5. Innings phase multiplier
        phase_map = {'powerplay': 0.95, 'middle': 1.0, 'death': 1.25, 'unknown': 1.0}
        phase_mult = df['innings_phase'].map(phase_map).fillna(1.0).values if 'innings_phase' in df.columns else np.ones(len(df))

        raw_score = (c_wkt + c_cluster + c_novelty + c_stagnation) * phase_mult
        df['batting_crisis_score'] = np.clip(raw_score, 0.0, 10.0).round(2)

        # Tier classification
        df['batting_pressure_tier'] = pd.cut(
            df['batting_crisis_score'],
            bins=[-0.01, 1.5, 3.5, 5.5, 7.5, 10.01],
            labels=['none', 'low', 'moderate', 'high', 'extreme']
        )
        df['is_batting_high_pressure'] = df['batting_pressure_tier'].isin(['high', 'extreme'])
        df['is_batting_moderate_pressure'] = df['batting_pressure_tier'] == 'moderate'
        df['is_batting_normal_pressure'] = df['batting_pressure_tier'].isin(['none', 'low'])

        return df

    @staticmethod
    def compute_bowling_defensive_pressure(df: pd.DataFrame) -> pd.DataFrame:
        """Estimate pre-delivery bowling defensive pressure score on [0.0, 10.0].

        Components (strictly ex-ante):
        1. Batting resource threat (0 to 3.0 pts): opponent wickets in hand (10 - wickets_fallen_before).
        2. Critical phase / field restrictions (1.0 to 3.0 pts): death = 3.0, powerplay = 2.0, middle = 1.0.
        3. Opponent boundary momentum (0 to 2.5 pts): boundaries conceded in last 12 legal balls.
        4. Strike-rotation pressure (0 to 1.5 pts): low dot frequency in last 12 legal balls.
        """
        df = df.copy()

        # 1. Batting resource threat
        if 'batting_wickets_remaining' in df.columns:
            w_rem = df['batting_wickets_remaining'].values.astype(float)
        elif 'wickets_fallen_before' in df.columns:
            w_rem = 10.0 - df['wickets_fallen_before'].values.astype(float)
        else:
            w_rem = np.full(len(df), 7.0)

        c_resource = np.where(w_rem >= 8, 3.0, np.where(w_rem >= 6, 2.0, np.where(w_rem >= 4, 1.0, 0.2)))

        # 2. Innings phase / field restriction leverage
        phase_pts = {'death': 3.0, 'powerplay': 2.0, 'middle': 1.0, 'unknown': 1.0}
        c_phase = df['innings_phase'].map(phase_pts).fillna(1.0).values if 'innings_phase' in df.columns else np.ones(len(df))

        # 3. Opponent boundary momentum
        if 'boundaries_in_last_12_legal_balls' in df.columns:
            b12 = df['boundaries_in_last_12_legal_balls'].values.astype(float)
            c_momentum = np.where(b12 >= 3, 2.5, np.where(b12 == 2, 1.6, np.where(b12 == 1, 0.8, 0.0)))
        else:
            c_momentum = np.zeros(len(df))

        # 4. Strike-rotation / lack of dots pressure
        if 'dots_in_last_12_legal_balls' in df.columns:
            d12 = df['dots_in_last_12_legal_balls'].values.astype(float)
            c_rotation = np.clip(1.5 * (1.0 - d12 / 12.0), 0.0, 1.5)
        else:
            c_rotation = np.zeros(len(df))

        raw_score = c_resource + c_phase + c_momentum + c_rotation
        df['bowling_defensive_score'] = np.clip(raw_score, 0.0, 10.0).round(2)

        # Tier classification
        df['bowling_pressure_tier'] = pd.cut(
            df['bowling_defensive_score'],
            bins=[-0.01, 2.5, 4.5, 6.5, 8.0, 10.01],
            labels=['none', 'low', 'moderate', 'high', 'extreme']
        )
        df['is_bowling_high_pressure'] = df['bowling_pressure_tier'].isin(['high', 'extreme'])
        df['is_bowling_moderate_pressure'] = df['bowling_pressure_tier'] == 'moderate'
        df['is_bowling_normal_pressure'] = df['bowling_pressure_tier'].isin(['none', 'low'])

        return df

    @classmethod
    def apply_dual_pressure(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Run both pressure engines on delivery-level data."""
        df = cls.compute_batting_crisis_pressure(df)
        df = cls.compute_bowling_defensive_pressure(df)
        return df
