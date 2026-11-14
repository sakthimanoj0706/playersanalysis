"""V3 Standalone Reliability and Match-Clustered Bootstrap Engine.

Provides statistical uncertainty estimation and Empirical Bayesian shrinkage:
1. Match-Clustered Bootstrap:
   - Resamples at the match level (with replacement) to preserve within-match dependence.
   - Computes non-parametric 95% confidence intervals [ci_lower, ci_upper] for player metrics.
2. Data-Driven Empirical Bayes Shrinkage:
   - Normal-Normal conjugate shrinkage for continuous metrics (Batting Strike Rate).
   - Beta-Binomial conjugate shrinkage for rate/event metrics (Bowling Wicket Rate, Dot Rate).
   - Population priors estimated from training distribution.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats


class V3ReliabilityEngine:
    """Estimates parameter uncertainty and empirical shrinkage for cricket metrics."""

    @staticmethod
    def match_clustered_bootstrap_batting(
        df: pd.DataFrame,
        player_id: int,
        n_bootstraps: int = 500,
        random_state: int = 42
    ) -> Dict[str, float]:
        """Compute match-clustered bootstrap confidence intervals for a batter's crisis strike rate."""
        rng = np.random.RandomState(random_state)
        faced = df[(df['is_ball_faced'] == True) & (df['striker_id'] == player_id)].copy()
        
        # Filter to crisis balls if flagged
        if 'is_batting_high_pressure' in faced.columns:
            crisis = faced[faced['is_batting_high_pressure'] == True].copy()
        else:
            crisis = faced.copy()

        runs_col = 'batter_runs' if 'batter_runs' in crisis.columns else 'runs'
        matches = crisis['match_id'].unique()
        n_matches = len(matches)

        if n_matches < 3:
            # Low match sample fallback
            point_sr = (crisis[runs_col].sum() / max(1, len(crisis))) * 100.0
            return {
                'point_estimate': round(point_sr, 2),
                'ci_lower': round(max(0.0, point_sr - 30.0), 2),
                'ci_upper': round(point_sr + 30.0, 2),
                'sample_matches': n_matches,
                'sample_deliveries': len(crisis),
                'uncertainty_width': 60.0
            }

        # Cluster by match
        match_groups = [group[runs_col].values for _, group in crisis.groupby('match_id')]
        boot_srs = []

        for _ in range(n_bootstraps):
            sampled_indices = rng.choice(n_matches, size=n_matches, replace=True)
            sampled_runs = np.concatenate([match_groups[i] for i in sampled_indices])
            if len(sampled_runs) > 0:
                boot_srs.append((sampled_runs.sum() / len(sampled_runs)) * 100.0)

        point_sr = (crisis[runs_col].sum() / max(1, len(crisis))) * 100.0
        ci_low = np.percentile(boot_srs, 2.5) if boot_srs else point_sr * 0.7
        ci_high = np.percentile(boot_srs, 97.5) if boot_srs else point_sr * 1.3

        return {
            'point_estimate': round(float(point_sr), 2),
            'ci_lower': round(float(ci_low), 2),
            'ci_upper': round(float(ci_high), 2),
            'sample_matches': n_matches,
            'sample_deliveries': len(crisis),
            'uncertainty_width': round(float(ci_high - ci_low), 2)
        }

    @staticmethod
    def match_clustered_bootstrap_bowling(
        df: pd.DataFrame,
        bowler_id: int,
        n_bootstraps: int = 500,
        random_state: int = 42
    ) -> Dict[str, float]:
        """Compute match-clustered bootstrap confidence intervals for a bowler's defensive dot rate."""
        rng = np.random.RandomState(random_state)
        legal = df[(df['is_legal_ball'] == True) & (df['bowler_id'] == bowler_id)].copy()

        if 'is_bowling_high_pressure' in legal.columns:
            crisis = legal[legal['is_bowling_high_pressure'] == True].copy()
        else:
            crisis = legal.copy()

        dot_col = 'is_dot_ball' if 'is_dot_ball' in crisis.columns else 'runs'
        if dot_col == 'runs':
            crisis['dot_val'] = (crisis['runs'] == 0).astype(int)
        else:
            crisis['dot_val'] = crisis[dot_col].astype(int)

        matches = crisis['match_id'].unique()
        n_matches = len(matches)

        if n_matches < 3:
            point_dot = (crisis['dot_val'].sum() / max(1, len(crisis))) * 100.0
            return {
                'point_estimate': round(point_dot, 2),
                'ci_lower': round(max(0.0, point_dot - 15.0), 2),
                'ci_upper': round(min(100.0, point_dot + 15.0), 2),
                'sample_matches': n_matches,
                'sample_deliveries': len(crisis),
                'uncertainty_width': 30.0
            }

        match_groups = [group['dot_val'].values for _, group in crisis.groupby('match_id')]
        boot_dots = []

        for _ in range(n_bootstraps):
            sampled_indices = rng.choice(n_matches, size=n_matches, replace=True)
            sampled_dots = np.concatenate([match_groups[i] for i in sampled_indices])
            if len(sampled_dots) > 0:
                boot_dots.append((sampled_dots.sum() / len(sampled_dots)) * 100.0)

        point_dot = (crisis['dot_val'].sum() / max(1, len(crisis))) * 100.0
        ci_low = np.percentile(boot_dots, 2.5) if boot_dots else point_dot * 0.7
        ci_high = np.percentile(boot_dots, 97.5) if boot_dots else point_dot * 1.3

        return {
            'point_estimate': round(float(point_dot), 2),
            'ci_lower': round(float(ci_low), 2),
            'ci_upper': round(float(ci_high), 2),
            'sample_matches': n_matches,
            'sample_deliveries': len(crisis),
            'uncertainty_width': round(float(ci_high - ci_low), 2)
        }

    @staticmethod
    def empirical_bayes_normal_shrinkage(
        observed_vals: pd.Series,
        sample_sizes: pd.Series,
        k_prior: float = 25.0
    ) -> pd.Series:
        """Normal-Normal conjugate shrinkage towards population mean."""
        pop_mean = observed_vals.mean()
        w = sample_sizes / (sample_sizes + k_prior)
        return w * observed_vals + (1.0 - w) * pop_mean

    @staticmethod
    def empirical_bayes_beta_binomial_shrinkage(
        successes: pd.Series,
        trials: pd.Series
    ) -> pd.Series:
        """Beta-Binomial conjugate shrinkage for rare event rates."""
        valid = trials >= 10
        if valid.sum() < 5:
            return np.where(trials > 0, (successes / trials) * 100.0, 0.0)

        rates = successes[valid] / trials[valid]
        mu = float(np.clip(rates.mean(), 0.01, 0.30))
        var = float(np.clip(rates.var(), 1e-5, mu * (1.0 - mu) * 0.5))

        m_sum = float(np.clip((mu * (1.0 - mu) / var) - 1.0, 5.0, 100.0))
        alpha = mu * m_sum
        beta = (1.0 - mu) * m_sum

        post_rates = (successes + alpha) / (trials + alpha + beta) * 100.0
        return post_rates
