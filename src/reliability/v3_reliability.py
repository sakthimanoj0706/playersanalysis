"""V3 Standalone Reliability and Match-Clustered Bootstrap Engine.

Provides statistical uncertainty estimation and Empirical Bayesian shrinkage:
1. Match-Clustered Bootstrap:
   - Resamples at the match level (with replacement) to preserve within-match dependence.
   - Computes non-parametric 95% confidence intervals [ci_lower, ci_upper] for player metrics.
   - Enforces explicit status (ESTIMATED_MATCH_CLUSTER_BOOTSTRAP, NOT_ESTIMATED_INSUFFICIENT_MATCH_CLUSTERS,
     NOT_ESTIMATED_NO_VALID_PRESSURE_DATA) without fabricated fixed-width fallbacks.
2. Data-Driven Shrinkage:
   - Fixed-K Normal-Normal conjugate shrinkage for continuous metrics (Batting Strike Rate).
   - Beta-Binomial conjugate shrinkage for rate/event metrics (Bowling Wicket Rate, Dot Rate).
   - Prior populations explicitly exclude zero-exposure and ineligible rows.
"""
from typing import Dict, List, Optional, Tuple, Union
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
        random_state: int = 42,
        min_matches: int = 3
    ) -> Dict[str, Union[float, int, str]]:
        """Compute match-clustered bootstrap confidence intervals for a batter's crisis strike rate.
        
        Strictly resamples whole match clusters with replacement. Returns explicit status without
        arbitrary fixed-width fallbacks.
        """
        rng = np.random.RandomState(random_state)
        # Match either canonical_striker_id or striker_id
        is_striker = (df['striker_id'] == player_id)
        if 'canonical_striker_id' in df.columns:
            is_striker = is_striker | (df['canonical_striker_id'] == player_id)

        faced = df[(df['is_ball_faced'] == True) & is_striker].copy()
        
        # Filter to crisis balls if flagged
        if 'is_batting_high_pressure' in faced.columns:
            crisis = faced[faced['is_batting_high_pressure'] == True].copy()
        else:
            crisis = faced.copy()

        runs_col = 'batter_runs' if 'batter_runs' in crisis.columns else 'runs'
        n_deliveries = len(crisis)

        if n_deliveries == 0:
            return {
                'point_estimate': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_NO_VALID_PRESSURE_DATA',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': 0,
                'ci_sample_deliveries': 0,
                'sample_matches': 0,
                'sample_deliveries': 0
            }

        matches = crisis['match_id'].unique()
        n_matches = len(matches)
        point_sr = (crisis[runs_col].sum() / n_deliveries) * 100.0

        if n_matches < min_matches:
            # Low match sample: strictly produce unestimated CI with explicit status
            return {
                'point_estimate': round(float(point_sr), 2),
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_INSUFFICIENT_MATCH_CLUSTERS',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': n_matches,
                'ci_sample_deliveries': n_deliveries,
                'sample_matches': n_matches,
                'sample_deliveries': n_deliveries
            }

        # Cluster by match
        match_groups = [group[runs_col].values for _, group in crisis.groupby('match_id')]
        boot_srs = []

        for _ in range(n_bootstraps):
            sampled_indices = rng.choice(n_matches, size=n_matches, replace=True)
            sampled_runs = np.concatenate([match_groups[i] for i in sampled_indices])
            if len(sampled_runs) > 0:
                boot_srs.append((sampled_runs.sum() / len(sampled_runs)) * 100.0)

        if len(boot_srs) < 10:
            return {
                'point_estimate': round(float(point_sr), 2),
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_BOOTSTRAP_FAILURE',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': n_matches,
                'ci_sample_deliveries': n_deliveries,
                'sample_matches': n_matches,
                'sample_deliveries': n_deliveries
            }

        ci_low = float(np.percentile(boot_srs, 2.5))
        ci_high = float(np.percentile(boot_srs, 97.5))

        return {
            'point_estimate': round(float(point_sr), 2),
            'ci_lower': round(ci_low, 2),
            'ci_upper': round(ci_high, 2),
            'uncertainty_width': round(ci_high - ci_low, 2),
            'ci_status': 'ESTIMATED_MATCH_CLUSTER_BOOTSTRAP',
            'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
            'ci_confidence_level': 0.95,
            'ci_bootstrap_iterations': n_bootstraps,
            'ci_sample_matches': n_matches,
            'ci_sample_deliveries': n_deliveries,
            'sample_matches': n_matches,
            'sample_deliveries': n_deliveries
        }

    @staticmethod
    def match_clustered_bootstrap_metric(
        df: pd.DataFrame,
        value_col: str,
        weight_col: Optional[str] = None,
        denom_col: Optional[str] = None,
        scale: float = 1.0,
        n_bootstraps: int = 500,
        random_state: int = 42,
        min_matches: int = 3,
    ) -> Dict[str, Union[float, int, str]]:
        """Compute match-clustered bootstrap 95% CIs for a weighted match-cluster metric.

        When ``denom_col`` is provided alongside ``weight_col``, sums ``value_col * weight_col``
        in the numerator and ``denom_col * weight_col`` in the denominator (preserving extra-ball
        penalties such as wides/no-balls in bowling run value per legal over).
        """
        n_deliveries = len(df)
        if n_deliveries == 0 or value_col not in df.columns:
            return {
                'point_estimate': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_NO_VALID_PRESSURE_DATA',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': 0,
                'ci_sample_deliveries': 0,
                'sample_matches': 0,
                'sample_deliveries': 0,
            }

        w = (
            pd.to_numeric(df[weight_col], errors='coerce').fillna(0.0).values
            if weight_col and weight_col in df.columns
            else np.ones(n_deliveries, dtype=float)
        )
        v = pd.to_numeric(df[value_col], errors='coerce').fillna(0.0).values
        d = (
            pd.to_numeric(df[denom_col], errors='coerce').fillna(0.0).values * w
            if denom_col and denom_col in df.columns
            else w
        )
        valid = (w > 0) & np.isfinite(v)
        if not np.any(valid) or float(np.sum(d[valid])) <= 0:
            return {
                'point_estimate': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_NO_VALID_PRESSURE_DATA',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': 0,
                'ci_sample_deliveries': 0,
                'sample_matches': 0,
                'sample_deliveries': 0,
            }

        sub_m = df.loc[valid, 'match_id'].values
        v = v[valid]
        w = w[valid]
        d = d[valid]
        _, inv = np.unique(sub_m, return_inverse=True)
        n_matches = int(inv.max() + 1)
        m_num = np.bincount(inv, weights=v * w, minlength=n_matches)
        m_den = np.bincount(inv, weights=d, minlength=n_matches)
        tot_den = float(np.sum(m_den))
        point_est = (float(np.sum(m_num)) / max(1e-9, tot_den)) * scale
        n_eff_deliveries = int(np.sum(d > 0)) if denom_col else int(np.sum(valid))

        if n_matches < min_matches:
            return {
                'point_estimate': round(point_est, 2),
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_INSUFFICIENT_MATCH_CLUSTERS',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': n_matches,
                'ci_sample_deliveries': n_eff_deliveries,
                'sample_matches': n_matches,
                'sample_deliveries': n_eff_deliveries,
            }

        rng = np.random.RandomState(random_state)
        probs = np.full(n_matches, 1.0 / n_matches)
        counts = rng.multinomial(n_matches, probs, size=n_bootstraps)
        boot_num = counts @ m_num
        boot_den = np.maximum(1e-9, counts @ m_den)
        boot_vals = (boot_num / boot_den) * scale

        ci_lower = float(np.percentile(boot_vals, 2.5))
        ci_upper = float(np.percentile(boot_vals, 97.5))
        return {
            'point_estimate': round(point_est, 2),
            'ci_lower': round(ci_lower, 2),
            'ci_upper': round(ci_upper, 2),
            'uncertainty_width': round(ci_upper - ci_lower, 2),
            'ci_status': 'ESTIMATED_MATCH_CLUSTER_BOOTSTRAP',
            'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
            'ci_confidence_level': 0.95,
            'ci_bootstrap_iterations': n_bootstraps,
            'ci_sample_matches': n_matches,
            'ci_sample_deliveries': n_eff_deliveries,
            'sample_matches': n_matches,
            'sample_deliveries': n_eff_deliveries,
        }

    @staticmethod
    def match_clustered_bootstrap_bowling(
        df: pd.DataFrame,
        bowler_id: int,
        n_bootstraps: int = 500,
        random_state: int = 42,
        min_matches: int = 3
    ) -> Dict[str, Union[float, int, str]]:
        """Compute match-clustered bootstrap confidence intervals for a bowler's defensive dot rate.
        
        Strictly resamples whole match clusters with replacement. Returns explicit status without
        arbitrary fixed-width fallbacks.
        """
        rng = np.random.RandomState(random_state)
        is_bowler = (df['bowler_id'] == bowler_id)
        if 'canonical_bowler_id' in df.columns:
            is_bowler = is_bowler | (df['canonical_bowler_id'] == bowler_id)

        legal = df[(df['is_legal_ball'] == True) & is_bowler].copy()

        if 'is_bowling_high_pressure' in legal.columns:
            crisis = legal[legal['is_bowling_high_pressure'] == True].copy()
        else:
            crisis = legal.copy()

        n_deliveries = len(crisis)

        if n_deliveries == 0:
            return {
                'point_estimate': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_NO_VALID_PRESSURE_DATA',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': 0,
                'ci_sample_deliveries': 0,
                'sample_matches': 0,
                'sample_deliveries': 0
            }

        dot_col = 'is_dot_ball' if 'is_dot_ball' in crisis.columns else 'runs'
        if dot_col == 'runs':
            crisis['dot_val'] = (crisis['runs'] == 0).astype(int)
        else:
            crisis['dot_val'] = crisis[dot_col].astype(int)

        matches = crisis['match_id'].unique()
        n_matches = len(matches)
        point_dot = (crisis['dot_val'].sum() / n_deliveries) * 100.0

        if n_matches < min_matches:
            return {
                'point_estimate': round(float(point_dot), 2),
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_INSUFFICIENT_MATCH_CLUSTERS',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': n_matches,
                'ci_sample_deliveries': n_deliveries,
                'sample_matches': n_matches,
                'sample_deliveries': n_deliveries
            }

        match_groups = [group['dot_val'].values for _, group in crisis.groupby('match_id')]
        boot_dots = []

        for _ in range(n_bootstraps):
            sampled_indices = rng.choice(n_matches, size=n_matches, replace=True)
            sampled_dots = np.concatenate([match_groups[i] for i in sampled_indices])
            if len(sampled_dots) > 0:
                boot_dots.append((sampled_dots.sum() / len(sampled_dots)) * 100.0)

        if len(boot_dots) < 10:
            return {
                'point_estimate': round(float(point_dot), 2),
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'uncertainty_width': np.nan,
                'ci_status': 'NOT_ESTIMATED_BOOTSTRAP_FAILURE',
                'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
                'ci_confidence_level': 0.95,
                'ci_bootstrap_iterations': n_bootstraps,
                'ci_sample_matches': n_matches,
                'ci_sample_deliveries': n_deliveries,
                'sample_matches': n_matches,
                'sample_deliveries': n_deliveries
            }

        ci_low = float(np.percentile(boot_dots, 2.5))
        ci_high = float(np.percentile(boot_dots, 97.5))

        return {
            'point_estimate': round(float(point_dot), 2),
            'ci_lower': round(ci_low, 2),
            'ci_upper': round(ci_high, 2),
            'uncertainty_width': round(ci_high - ci_low, 2),
            'ci_status': 'ESTIMATED_MATCH_CLUSTER_BOOTSTRAP',
            'ci_method': 'MATCH_CLUSTERED_BOOTSTRAP',
            'ci_confidence_level': 0.95,
            'ci_bootstrap_iterations': n_bootstraps,
            'ci_sample_matches': n_matches,
            'ci_sample_deliveries': n_deliveries,
            'sample_matches': n_matches,
            'sample_deliveries': n_deliveries
        }

    @classmethod
    def fixed_k_normal_shrinkage(
        cls,
        observed_vals: pd.Series,
        sample_sizes: pd.Series,
        k_prior: float = 25.0,
        eligible_mask: Optional[pd.Series] = None,
        return_metadata: bool = False
    ) -> Union[pd.Series, Tuple[pd.Series, Dict[str, any]]]:
        """Fixed-K Normal-Normal conjugate shrinkage towards eligible population prior mean.
        
        Formula:
            theta_i = (n_i / (n_i + K)) * Y_i + (K / (n_i + K)) * mu_0
        
        Strict Prior Masking:
            Excludes zero-exposure and ineligible rows from prior mean estimation.
            Zero-exposure rows remain NaN (never populated with synthetic rates).
        """
        # Determine eligible prior population
        obs_float = pd.to_numeric(observed_vals, errors='coerce').astype(float)
        if eligible_mask is not None:
            prior_mask = (sample_sizes > 0) & obs_float.notna() & ~np.isinf(obs_float) & eligible_mask
        else:
            prior_mask = (sample_sizes > 0) & obs_float.notna() & ~np.isinf(obs_float)

        if prior_mask.sum() == 0:
            prior_mask = (sample_sizes > 0) & obs_float.notna() & ~np.isinf(obs_float)

        if prior_mask.sum() == 0:
            pop_mean = 130.0  # Safe default if entirely empty
            prior_pop_count = 0
        else:
            pop_mean = float(obs_float[prior_mask].mean())
            prior_pop_count = int(prior_mask.sum())

        w = sample_sizes / (sample_sizes + k_prior)
        # Positive exposure rows are shrunk; zero-exposure rows stay NaN
        shrunk = np.where(
            (sample_sizes > 0) & obs_float.notna(),
            w * obs_float + (1.0 - w) * pop_mean,
            np.nan
        )
        res_series = pd.Series(shrunk, index=observed_vals.index, dtype=float)

        metadata = {
            'shrinkage_method': 'FIXED_K_NORMAL_SHRINKAGE',
            'prior_k': float(k_prior),
            'prior_mean': round(pop_mean, 2),
            'prior_population_count': prior_pop_count,
            'prior_population_definition': 'Valid positive-exposure eligible cohort',
            'prior_fit_period': 'Cohort Training Baseline',
            'shrinkage_status': 'FIXED_K_ASSUMPTION'
        }

        if return_metadata:
            return res_series, metadata
        return res_series

    @classmethod
    def empirical_bayes_normal_shrinkage(
        cls,
        observed_vals: pd.Series,
        sample_sizes: pd.Series,
        k_prior: float = 25.0,
        eligible_mask: Optional[pd.Series] = None
    ) -> pd.Series:
        """Alias for fixed_k_normal_shrinkage for backwards compatibility."""
        return cls.fixed_k_normal_shrinkage(
            observed_vals, sample_sizes, k_prior=k_prior, eligible_mask=eligible_mask, return_metadata=False
        )

    @classmethod
    def empirical_bayes_beta_binomial_shrinkage(
        cls,
        successes: pd.Series,
        trials: pd.Series,
        eligible_mask: Optional[pd.Series] = None,
        return_metadata: bool = False
    ) -> Union[pd.Series, Tuple[pd.Series, Dict[str, any]]]:
        """Beta-Binomial conjugate shrinkage for rate metrics with method-of-moments prior.
        
        Requires 0 <= successes <= trials.
        Zero-trial records are excluded from prior estimation and stay NaN.
        """
        if eligible_mask is not None:
            valid = (trials >= 10) & eligible_mask & (successes <= trials) & (successes >= 0)
        else:
            valid = (trials >= 10) & (successes <= trials) & (successes >= 0)

        if valid.sum() < 5:
            valid = (trials > 0) & (successes <= trials) & (successes >= 0)

        if valid.sum() == 0:
            mu = 0.05
            var = 0.002
            alpha = 1.0
            beta = 19.0
            prior_pop_count = 0
        else:
            rates = successes[valid] / trials[valid]
            mu = float(np.clip(rates.mean(), 0.01, 0.30))
            var = float(np.clip(rates.var(), 1e-5, mu * (1.0 - mu) * 0.5)) if len(rates) > 1 else 0.002
            m_sum = float(np.clip((mu * (1.0 - mu) / var) - 1.0, 5.0, 100.0))
            alpha = mu * m_sum
            beta = (1.0 - mu) * m_sum
            prior_pop_count = int(valid.sum())

        post_rates = np.where(
            trials > 0,
            (successes + alpha) / (trials + alpha + beta) * 100.0,
            np.nan
        )
        res_series = pd.Series(post_rates, index=trials.index)

        metadata = {
            'shrinkage_method': 'BETA_BINOMIAL_EMPIRICAL_BAYES',
            'prior_alpha': round(alpha, 4),
            'prior_beta': round(beta, 4),
            'prior_mean': round(mu * 100.0, 2),
            'prior_population_count': prior_pop_count,
            'prior_population_definition': 'Valid trial-exposed eligible cohort (trials >= 10)',
            'shrinkage_status': 'ESTIMATED_EMPIRICAL_BAYES'
        }

        if return_metadata:
            return res_series, metadata
        return res_series

    @classmethod
    def phase_adjusted_dual_arm_did(
        cls,
        crisis_excess: pd.Series,
        crisis_balls: pd.Series,
        norm_excess: pd.Series,
        norm_balls: pd.Series,
        k_crisis: float = 25.0,
        k_norm: float = 25.0,
        floor_normal_at_zero: bool = True,
        min_norm_ref: Optional[float] = None,
        cohort_calibrated: bool = True,
        allow_prior_anchored: bool = False,
        cohort_mask: Optional[pd.Series] = None,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Shrink phase-adjusted crisis and normal residuals toward 0 (league phase average)
        and return (shrunk_crisis, shrunk_norm, did_maintenance).

        When ``cohort_calibrated=True``, fits the cohort's empirical regression-to-the-mean
        slope ``beta`` (clipped to [0.30, 0.80]) between capped normal excess and crisis excess
        so elite normal-overs performers (e.g., Jasprit Bumrah) are not penalized for having
        a high normal baseline.

        When ``min_norm_ref`` is provided (e.g., ``-5.0`` runs/100 or ``-0.5`` runs/over),
        ``raw_pos_n`` is floored at ``min_norm_ref`` instead of hard 0.0, preventing weak normal
        baselines from artificially inflating maintenance while avoiding runaway leverage distortion.
        """
        c_val = pd.to_numeric(crisis_excess, errors='coerce').astype(float)
        c_n = pd.to_numeric(crisis_balls, errors='coerce').fillna(0.0).astype(float)
        n_val = pd.to_numeric(norm_excess, errors='coerce').astype(float)
        n_n = pd.to_numeric(norm_balls, errors='coerce').fillna(0.0).astype(float)

        shrunk_c = np.where((c_n > 0) & c_val.notna(), (c_n / (c_n + k_crisis)) * c_val, np.nan)
        if allow_prior_anchored:
            shrunk_n = np.where((n_n > 0) & n_val.notna(), (n_n / (n_n + k_norm)) * n_val, 0.0)
        else:
            shrunk_n = np.where((n_n > 0) & n_val.notna(), (n_n / (n_n + k_norm)) * n_val, np.nan)

        if min_norm_ref is not None:
            raw_pos_n = np.maximum(shrunk_n, float(min_norm_ref))
        elif floor_normal_at_zero:
            raw_pos_n = np.maximum(shrunk_n, 0.0)
        else:
            raw_pos_n = shrunk_n

        if cohort_calibrated:
            fit_mask = pd.notna(shrunk_c) & pd.notna(shrunk_n) & (c_n > 0) & (n_n > 0)
            if cohort_mask is not None:
                fit_mask = fit_mask & cohort_mask.values.astype(bool)
            if int(np.sum(fit_mask)) >= 15:
                x = raw_pos_n[fit_mask]
                y = shrunk_c[fit_mask]
                x_w = np.clip(x, np.quantile(x, 0.025), np.quantile(x, 0.975))
                y_w = np.clip(y, np.quantile(y, 0.025), np.quantile(y, 0.975))
                vx = float(np.var(x_w))
                if vx > 1e-8:
                    beta = float(np.clip(np.cov(x_w, y_w, ddof=0)[0, 1] / vx, 0.30, 0.80))
                else:
                    beta = 0.45
            else:
                beta = 0.45
            baseline_ref = beta * raw_pos_n
        else:
            baseline_ref = raw_pos_n

        did = np.where(pd.notna(shrunk_c) & pd.notna(shrunk_n), shrunk_c - baseline_ref, np.nan)

        return (
            pd.Series(shrunk_c, index=crisis_excess.index, dtype=float),
            pd.Series(shrunk_n, index=norm_excess.index, dtype=float),
            pd.Series(did, index=crisis_excess.index, dtype=float),
        )
