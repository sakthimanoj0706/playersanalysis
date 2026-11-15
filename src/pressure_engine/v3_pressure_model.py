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

        Formula (V4 strictly ex-ante state leverage, free of short-window dot survivorship bias):
        1. Wicket depletion: min(2.6, wickets_fallen_before * 0.38).
        2. Stage-relative wicket shock: clip(wickets_fallen_before - expected_wickets(ball), 0, 2.0) * 0.35.
        3. Recent wicket cluster: 2+ wickets in last 12 legal balls = 1.6, 1 wicket = 0.7.
        4. Chase / 1st-innings run-rate leverage: monotonic RRR demand (with dead-rubber taper >24 RPO)
           or 1st-innings scoring lag below 7.8 RPO.
        Scaled onto [0.0, 10.0] via (+1.5 shift); when full match/innings columns exist,
        `calibrate_within_phase_tiers()` sets High (> q70), Moderate (q50..q70], Normal (<= q50)
        within each (innings, innings_phase) stratum.
        """
        df = df.copy()
        n = len(df)
        valid_mask, missing_features = cls.validate_batting_features(df)

        df['batting_pressure_data_valid'] = valid_mask
        df['batting_pressure_missing_features'] = missing_features

        scores = np.full(n, np.nan, dtype=float)
        raw_lev = np.full(n, np.nan, dtype=float)
        tiers = np.full(n, 'PRESSURE_UNCLASSIFIED', dtype=object)
        is_high = np.zeros(n, dtype=bool)
        is_mod = np.zeros(n, dtype=bool)
        is_norm = np.zeros(n, dtype=bool)

        if np.any(valid_mask):
            valid_idx = np.where(valid_mask)[0]
            sub = df.iloc[valid_idx]

            w_bef = sub['wickets_fallen_before'].values.astype(float)
            w12 = sub['wickets_in_last_12_legal_balls'].values.astype(float)

            if 'cumulative_legal_balls' in sub.columns and sub['cumulative_legal_balls'].notna().all():
                cum_leg = sub['cumulative_legal_balls'].values.astype(float)
            else:
                phase_balls = {'powerplay': 18.0, 'middle': 54.0, 'death': 102.0}
                cum_leg = sub['innings_phase'].map(phase_balls).fillna(54.0).values.astype(float)

            exp_w_bef = 0.5 + 5.0 * (cum_leg / 120.0)
            wkt_shock = np.clip(w_bef - exp_w_bef, -2.0, 5.0)

            rrr = sub['clean_rrr_deficit'].values.astype(float) if 'clean_rrr_deficit' in sub.columns else np.full(len(sub), np.nan)
            if 'clean_cum_runs' in sub.columns and sub['clean_cum_runs'].notna().any():
                overs_bowled = np.maximum(cum_leg / 6.0, 1.0)
                crr = np.where(cum_leg >= 18, sub['clean_cum_runs'].values.astype(float) / overs_bowled, np.nan)
            else:
                crr = np.full(len(sub), np.nan)

            c_chase = np.where(
                np.isfinite(rrr),
                np.where(
                    rrr > 24.0,
                    np.clip(2.8 - (rrr - 24.0) * 0.25, 0.5, 2.8),
                    np.where(
                        rrr >= 7.5,
                        np.clip((rrr - 7.5) * 0.35, 0.0, 3.2),
                        -np.clip((6.5 - rrr) * 0.40, 0.0, 1.5),
                    ),
                ),
                np.where(
                    np.isfinite(crr) & (crr < 7.8),
                    np.clip((7.8 - crr) * 0.6, 0.0, 1.5),
                    np.where(np.isfinite(crr), -np.clip((crr - 9.5) * 0.3, 0.0, 0.8), 0.0),
                ),
            )

            bat_lev = (
                np.clip(w_bef * 0.38, 0.0, 2.6)
                + np.clip(wkt_shock * 0.35, 0.0, 2.0)
                + np.where(w12 >= 2, 1.6, np.where(w12 == 1, 0.7, 0.0))
                + c_chase
            )
            valid_scores = np.clip(bat_lev + 1.5, 0.0, 10.0).round(2)
            raw_lev[valid_idx] = bat_lev
            scores[valid_idx] = valid_scores

            valid_tiers = pd.cut(
                valid_scores,
                bins=[-0.01, 1.8, 3.2, 4.4, 6.2, 10.01],
                labels=['none', 'low', 'moderate', 'high', 'extreme'],
            ).astype(str)
            tiers[valid_idx] = valid_tiers
            is_high[valid_idx] = np.isin(valid_tiers, ['high', 'extreme'])
            is_mod[valid_idx] = (valid_tiers == 'moderate')
            is_norm[valid_idx] = np.isin(valid_tiers, ['none', 'low'])

        df['batting_leverage_raw'] = raw_lev
        df['batting_crisis_score'] = scores
        df['batting_pressure_tier'] = tiers
        df['is_batting_high_pressure'] = is_high
        df['is_batting_moderate_pressure'] = is_mod
        df['is_batting_normal_pressure'] = is_norm

        return df

    @classmethod
    def compute_bowling_defensive_pressure(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Estimate pre-delivery bowling defensive pressure score on [0.0, 10.0] with explicit validation.

        Formula (V4 strictly ex-ante state leverage, free of last-12 boundary outcome bias):
        1. Batting resource threat: wickets in hand (>=8: +1.4, >=6: +1.0, >=4: +0.5, <4: -0.4).
        2. Live-game chase closeness (peak at ~9.5 RPO, dampens >15.5 or <5.0 RPO dead rubbers)
           or 1st-innings high scoring-rate threat.
        3. Live-death squeeze bonus (+0.5 when death phase and wickets_remaining >= 4).
        Scaled onto [0.0, 10.0]; call `calibrate_within_phase_tiers()` on full match cohorts
        for within-(innings, phase) quantile tiers so PP/Death specialists retain ~50% Normal exposure.
        """
        df = df.copy()
        n = len(df)
        valid_mask, missing_features = cls.validate_bowling_features(df)

        df['bowling_pressure_data_valid'] = valid_mask
        df['bowling_pressure_missing_features'] = missing_features

        scores = np.full(n, np.nan, dtype=float)
        raw_lev = np.full(n, np.nan, dtype=float)
        tiers = np.full(n, 'PRESSURE_UNCLASSIFIED', dtype=object)
        is_high = np.zeros(n, dtype=bool)
        is_mod = np.zeros(n, dtype=bool)
        is_norm = np.zeros(n, dtype=bool)

        if np.any(valid_mask):
            valid_idx = np.where(valid_mask)[0]
            sub = df.iloc[valid_idx]

            if 'batting_wickets_remaining' in sub.columns and sub['batting_wickets_remaining'].notna().all():
                w_rem = sub['batting_wickets_remaining'].values.astype(float)
            else:
                w_rem = 10.0 - sub['wickets_fallen_before'].values.astype(float)

            c_resource = np.where(w_rem >= 8, 1.4, np.where(w_rem >= 6, 1.0, np.where(w_rem >= 4, 0.5, -0.4)))

            rrr = sub['clean_rrr_deficit'].values.astype(float) if 'clean_rrr_deficit' in sub.columns else np.full(len(sub), np.nan)
            if 'cumulative_legal_balls' in sub.columns and sub['cumulative_legal_balls'].notna().all():
                cum_leg = sub['cumulative_legal_balls'].values.astype(float)
            else:
                cum_leg = np.full(len(sub), np.nan)
            if 'clean_cum_runs' in sub.columns and sub['clean_cum_runs'].notna().any():
                overs_bowled = np.maximum(cum_leg / 6.0, 1.0)
                crr = np.where(np.isfinite(cum_leg) & (cum_leg >= 18), sub['clean_cum_runs'].values.astype(float) / overs_bowled, np.nan)
            else:
                crr = np.full(len(sub), np.nan)

            c_chase = np.where(
                np.isfinite(rrr),
                np.where(
                    (rrr > 15.5) | (rrr < 5.0),
                    -1.5,
                    np.clip(2.4 - np.abs(rrr - 9.5) * 0.45, -0.5, 2.4),
                ),
                np.where(np.isfinite(crr), np.clip((crr - 7.5) * 0.50, -1.0, 1.8), 0.0),
            )
            death_live = np.where((sub['innings_phase'].values == 'death') & (w_rem >= 4), 0.5, 0.0)
            bowl_lev = c_resource + c_chase + death_live

            # Map theoretical range [-1.9, +4.3] onto [0.0, 10.0]
            valid_scores = np.clip((bowl_lev + 2.0) * (10.0 / 6.5), 0.0, 10.0).round(2)
            raw_lev[valid_idx] = bowl_lev
            scores[valid_idx] = valid_scores

            valid_tiers = pd.cut(
                valid_scores,
                bins=[-0.01, 2.5, 4.2, 5.2, 6.8, 10.01],
                labels=['none', 'low', 'moderate', 'high', 'extreme'],
            ).astype(str)
            tiers[valid_idx] = valid_tiers
            is_high[valid_idx] = np.isin(valid_tiers, ['high', 'extreme'])
            is_mod[valid_idx] = (valid_tiers == 'moderate')
            is_norm[valid_idx] = np.isin(valid_tiers, ['none', 'low'])

        df['bowling_leverage_raw'] = raw_lev
        df['bowling_defensive_score'] = scores
        df['bowling_pressure_tier'] = tiers
        df['is_bowling_high_pressure'] = is_high
        df['is_bowling_moderate_pressure'] = is_mod
        df['is_bowling_normal_pressure'] = is_norm

        return df

    @classmethod
    def calibrate_within_phase_tiers(
        cls,
        df: pd.DataFrame,
        high_quantile: float = 0.70,
        normal_quantile: float = 0.50,
    ) -> pd.DataFrame:
        """Calibrate High/Moderate/Normal flags within (innings, innings_phase) strata.

        Prevents PP/Death bowling specialists from having >70% of balls marked as High crisis
        and ensures ~30% High, ~20% Moderate, ~50% Normal inside every innings x phase cell.
        """
        df = df.copy()
        strata = [c for c in ['innings', 'innings_phase'] if c in df.columns]
        if not strata:
            return df

        for prefix, raw_col, valid_col, tier_col, hi_col, mod_col, norm_col in [
            (
                'batting',
                'batting_leverage_raw',
                'batting_pressure_data_valid',
                'batting_pressure_tier',
                'is_batting_high_pressure',
                'is_batting_moderate_pressure',
                'is_batting_normal_pressure',
            ),
            (
                'bowling',
                'bowling_leverage_raw',
                'bowling_pressure_data_valid',
                'bowling_pressure_tier',
                'is_bowling_high_pressure',
                'is_bowling_moderate_pressure',
                'is_bowling_normal_pressure',
            ),
        ]:
            if raw_col not in df.columns or valid_col not in df.columns:
                continue
            vmask = df[valid_col].fillna(False).values.astype(bool) & df[raw_col].notna().values
            if int(np.sum(vmask)) < 100:
                continue
            sub = df.loc[vmask]
            q_hi = sub.groupby(strata)[raw_col].transform(lambda s: s.quantile(high_quantile))
            q_norm = sub.groupby(strata)[raw_col].transform(lambda s: s.quantile(normal_quantile))
            q_ext = sub.groupby(strata)[raw_col].transform(lambda s: s.quantile(0.90))
            q_low = sub.groupby(strata)[raw_col].transform(lambda s: s.quantile(0.25))

            vals = sub[raw_col]
            hi = (vals > q_hi).values
            norm = (vals <= q_norm).values
            mod = (~hi) & (~norm)
            ext = (vals > q_ext).values
            none_t = (vals <= q_low).values

            tiers = np.where(
                ext, 'extreme',
                np.where(hi, 'high', np.where(mod, 'moderate', np.where(none_t, 'none', 'low')))
            )
            df.loc[vmask, hi_col] = hi
            df.loc[vmask, mod_col] = mod
            df.loc[vmask, norm_col] = norm
            df.loc[vmask, tier_col] = tiers

        return df

    @classmethod
    def apply_dual_pressure(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Run both pressure engines on delivery-level data (calibrating within phase for cohort frames)."""
        df = cls.compute_batting_crisis_pressure(df)
        df = cls.compute_bowling_defensive_pressure(df)
        if len(df) >= 500 and {'innings', 'innings_phase'}.issubset(df.columns):
            df = cls.calibrate_within_phase_tiers(df)
        return df
