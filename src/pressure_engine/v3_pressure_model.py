"""V3 Match Pressure Modeling Engine with Strict Feature Schema Validation.

Provides independent, pre-delivery ex-ante pressure models:
1. Batting Crisis Pressure Model: Measures pre-delivery collapse, resource depletion,
   stagnation, and entry vulnerability.
2. Bowling Defensive Pressure Model: Measures pre-delivery opponent resource threat,
   field restrictions, and opponent boundary momentum.

Zero Target Leakage Guarantee:
Every feature is computed strictly from states established BEFORE the ball is bowled.
No future balls, eventual delivery outcomes, or match results are ingested as inputs.

Missing-Data Integrity:
Silent defaults (e.g. missing wickets -> 0, missing balls faced -> 10) are removed.
Incomplete records are marked as PRESSURE_UNCLASSIFIED and flagged with data validity indicators:
- batting_pressure_data_valid
- bowling_pressure_data_valid
- batting_pressure_missing_features
- bowling_pressure_missing_features
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class V3PressureModel:
    """Pre-delivery pressure state estimator with strict data completeness validation."""

    # Explicit required feature schemas
    BATTING_REQUIRED_FEATURES = [
        'wickets_fallen_before',
        'wickets_in_last_12_legal_balls',
        'batter_balls_faced',
        'consecutive_dots',
        'dots_in_last_12_legal_balls',
        'innings_phase'
    ]

    BOWLING_REQUIRED_FEATURES = [
        'innings_phase',
        'boundaries_in_last_12_legal_balls',
        'dots_in_last_12_legal_balls'
        # Note: requires batting_wickets_remaining OR wickets_fallen_before
    ]

    VALID_PHASES = {'powerplay', 'middle', 'death'}

    @classmethod
    def validate_batting_features(cls, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Validate presence and non-null status of all required batting features."""
        n = len(df)
        valid_mask = np.ones(n, dtype=bool)
        missing_reasons = [[] for _ in range(n)]

        for feat in cls.BATTING_REQUIRED_FEATURES:
            if feat not in df.columns:
                valid_mask[:] = False
                for i in range(n):
                    missing_reasons[i].append(feat)
            else:
                col_vals = df[feat]
                is_null = col_vals.isna().values
                if feat == 'innings_phase':
                    is_invalid_phase = ~col_vals.isin(cls.VALID_PHASES).values
                    is_bad = is_null | is_invalid_phase
                else:
                    is_bad = is_null
                valid_mask = valid_mask & (~is_bad)
                bad_indices = np.where(is_bad)[0]
                for idx in bad_indices:
                    missing_reasons[idx].append(feat)

        missing_str = [",".join(m) for m in missing_reasons]
        return valid_mask, missing_str

    @classmethod
    def validate_bowling_features(cls, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Validate presence and non-null status of all required bowling features."""
        n = len(df)
        valid_mask = np.ones(n, dtype=bool)
        missing_reasons = [[] for _ in range(n)]

        # Check wicket resource feature (either batting_wickets_remaining or wickets_fallen_before)
        has_w_rem = 'batting_wickets_remaining' in df.columns
        has_w_bef = 'wickets_fallen_before' in df.columns
        if not has_w_rem and not has_w_bef:
            valid_mask[:] = False
            for i in range(n):
                missing_reasons[i].append('batting_wickets_remaining')
        else:
            w_col = df['batting_wickets_remaining'] if has_w_rem else df['wickets_fallen_before']
            is_bad = w_col.isna().values
            valid_mask = valid_mask & (~is_bad)
            bad_indices = np.where(is_bad)[0]
            for idx in bad_indices:
                missing_reasons[idx].append('batting_wickets_remaining')

        for feat in cls.BOWLING_REQUIRED_FEATURES:
            if feat not in df.columns:
                valid_mask[:] = False
                for i in range(n):
                    missing_reasons[i].append(feat)
            else:
                col_vals = df[feat]
                is_null = col_vals.isna().values
                if feat == 'innings_phase':
                    is_invalid_phase = ~col_vals.isin(cls.VALID_PHASES).values
                    is_bad = is_null | is_invalid_phase
                else:
                    is_bad = is_null
                valid_mask = valid_mask & (~is_bad)
                bad_indices = np.where(is_bad)[0]
                for idx in bad_indices:
                    missing_reasons[idx].append(feat)

        missing_str = [",".join(m) for m in missing_reasons]
        return valid_mask, missing_str

    @classmethod
    def compute_batting_crisis_pressure(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Estimate pre-delivery batting crisis pressure score on [0.0, 10.0] with explicit validation.

        Formula (strictly ex-ante provisional heuristic):
        1. Wicket depletion (0 to 3.5 pts): wickets_fallen_before * 0.45.
        2. Collapse cluster (0 to 2.0 pts): 2+ wickets in last 12 balls = 2.0, 1 wicket = 0.75.
        3. Batter entry vulnerability (0 to 1.5 pts): 1.5 * (1 - balls_faced / 5) if balls_faced < 5.
        4. Stagnation pressure (0 to 1.5 pts): consecutive_dots * 0.3 + (dots_in_12 / 12) * 0.6.
        5. Innings phase multiplier: death 1.25x, middle 1.0x, powerplay 0.95x.
        """
        df = df.copy()
        n = len(df)
        valid_mask, missing_features = cls.validate_batting_features(df)

        df['batting_pressure_data_valid'] = valid_mask
        df['batting_pressure_missing_features'] = missing_features

        # Initialize output columns
        scores = np.full(n, np.nan, dtype=float)
        tiers = np.full(n, 'PRESSURE_UNCLASSIFIED', dtype=object)
        is_high = np.zeros(n, dtype=bool)
        is_mod = np.zeros(n, dtype=bool)
        is_norm = np.zeros(n, dtype=bool)

        if np.any(valid_mask):
            valid_idx = np.where(valid_mask)[0]
            sub = df.iloc[valid_idx]

            # 1. Wickets fallen before delivery
            w_before = sub['wickets_fallen_before'].values.astype(float)
            c_wkt = np.clip(w_before * 0.50, 0.0, 3.5)

            # 2. Recent wicket cluster
            w12 = sub['wickets_in_last_12_legal_balls'].values.astype(float)
            c_cluster = np.where(w12 >= 2, 2.2, np.where(w12 == 1, 1.0, 0.0))

            # 3. Entry vulnerability
            bf = sub['batter_balls_faced'].values.astype(float)
            c_novelty = np.where(bf < 6, 1.5 * (1.0 - bf / 6.0), 0.0)

            # 4. Stagnation / dots pressure
            consec_dots = sub['consecutive_dots'].values.astype(float)
            dots_12 = sub['dots_in_last_12_legal_balls'].values.astype(float)
            c_stagnation = np.clip(consec_dots * 0.35 + (dots_12 / 12.0) * 0.90, 0.0, 1.8)

            # 5. Innings phase multiplier
            phase_map = {'powerplay': 1.00, 'middle': 1.05, 'death': 1.25}
            phase_mult = sub['innings_phase'].map(phase_map).values.astype(float)

            raw_score = (c_wkt + c_cluster + c_novelty + c_stagnation) * phase_mult
            valid_scores = np.clip(raw_score, 0.0, 10.0).round(2)
            scores[valid_idx] = valid_scores

            # Tier classification
            valid_tiers = pd.cut(
                valid_scores,
                bins=[-0.01, 1.5, 3.5, 5.2, 7.5, 10.01],
                labels=['none', 'low', 'moderate', 'high', 'extreme']
            ).astype(str)
            tiers[valid_idx] = valid_tiers

            is_high[valid_idx] = np.isin(valid_tiers, ['high', 'extreme'])
            is_mod[valid_idx] = (valid_tiers == 'moderate')
            is_norm[valid_idx] = np.isin(valid_tiers, ['none', 'low'])

        df['batting_crisis_score'] = scores
        df['batting_pressure_tier'] = tiers
        df['is_batting_high_pressure'] = is_high
        df['is_batting_moderate_pressure'] = is_mod
        df['is_batting_normal_pressure'] = is_norm

        return df

    @classmethod
    def compute_bowling_defensive_pressure(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Estimate pre-delivery bowling defensive pressure score on [0.0, 10.0] with explicit validation.

        Formula (strictly ex-ante provisional heuristic):
        1. Batting resource threat (0 to 3.0 pts): wickets in hand (>=8: 3.0, >=6: 2.0, >=4: 1.0, <4: 0.2).
        2. Innings phase / restrictions (1.0 to 3.0 pts): death 3.0, powerplay 2.0, middle 1.0.
        3. Opponent boundary momentum (0 to 2.5 pts): boundaries in last 12 balls (>=3: 2.5, 2: 1.6, 1: 0.8, 0: 0.0).
        4. Strike-rotation pressure (0 to 1.5 pts): 1.5 * (1 - dots_in_12 / 12).
        """
        df = df.copy()
        n = len(df)
        valid_mask, missing_features = cls.validate_bowling_features(df)

        df['bowling_pressure_data_valid'] = valid_mask
        df['bowling_pressure_missing_features'] = missing_features

        # Initialize output columns
        scores = np.full(n, np.nan, dtype=float)
        tiers = np.full(n, 'PRESSURE_UNCLASSIFIED', dtype=object)
        is_high = np.zeros(n, dtype=bool)
        is_mod = np.zeros(n, dtype=bool)
        is_norm = np.zeros(n, dtype=bool)

        if np.any(valid_mask):
            valid_idx = np.where(valid_mask)[0]
            sub = df.iloc[valid_idx]

            # 1. Batting resource threat
            if 'batting_wickets_remaining' in sub.columns and sub['batting_wickets_remaining'].notna().all():
                w_rem = sub['batting_wickets_remaining'].values.astype(float)
            else:
                w_rem = 10.0 - sub['wickets_fallen_before'].values.astype(float)
            c_resource = np.where(w_rem >= 8, 2.2, np.where(w_rem >= 6, 1.4, np.where(w_rem >= 4, 0.8, 0.2)))

            # 2. Innings phase
            phase_pts = {'death': 3.2, 'powerplay': 2.6, 'middle': 0.8}
            c_phase = sub['innings_phase'].map(phase_pts).values.astype(float)

            # 3. Opponent boundary momentum
            b12 = sub['boundaries_in_last_12_legal_balls'].values.astype(float)
            c_momentum = np.where(b12 >= 3, 2.8, np.where(b12 == 2, 1.8, np.where(b12 == 1, 0.7, 0.0)))

            # 4. Strike-rotation / lack of dots pressure
            d12 = sub['dots_in_last_12_legal_balls'].values.astype(float)
            c_rotation = np.clip(0.8 * (1.0 - d12 / 12.0), 0.0, 0.8)

            raw_score = c_resource + c_phase + c_momentum + c_rotation
            valid_scores = np.clip(raw_score, 0.0, 10.0).round(2)
            scores[valid_idx] = valid_scores

            # Tier classification
            valid_tiers = pd.cut(
                valid_scores,
                bins=[-0.01, 2.5, 4.5, 5.5, 7.5, 10.01],
                labels=['none', 'low', 'moderate', 'high', 'extreme']
            ).astype(str)
            tiers[valid_idx] = valid_tiers

            is_high[valid_idx] = np.isin(valid_tiers, ['high', 'extreme'])
            is_mod[valid_idx] = (valid_tiers == 'moderate')
            is_norm[valid_idx] = np.isin(valid_tiers, ['none', 'low'])

        df['bowling_defensive_score'] = scores
        df['bowling_pressure_tier'] = tiers
        df['is_bowling_high_pressure'] = is_high
        df['is_bowling_moderate_pressure'] = is_mod
        df['is_bowling_normal_pressure'] = is_norm

        return df

    @classmethod
    def apply_dual_pressure(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Run both pressure engines on delivery-level data."""
        df = cls.compute_batting_crisis_pressure(df)
        df = cls.compute_bowling_defensive_pressure(df)
        return df
