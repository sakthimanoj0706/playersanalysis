"""V4.2 Pressure Proxy Revalidation and Honest Naming Module.

Traces exact parameter usage (R0, b, gamma) inside fit_b3_resource_stress,
replaces misleading leverage naming with exact technical definitions:
  - BATTING_WICKET_DEPLETION_ANOMALY (aliases: BATTING_RESOURCE_STRESS, bat_pressure)
  - BOWLING_EXPECTED_SCORING_THREAT  (aliases: BOWLING_SCORING_THREAT, bowl_pressure)
and builds an interpretable full remaining-resource sensitivity series
(BAT_DEPLETION_FULL_RUW) without modifying pre-delivery zero-leakage guarantees.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.v4.pressure_proxy import (
    apply_b3_resource_stress,
    build_pre_delivery_context,
    fit_b3_resource_stress,
)

CHASE_SCORE_RECONSTRUCTION_BLOCKED: bool = True

BATTING_PROXY_PRIMARY_NAME = "BATTING_WICKET_DEPLETION_ANOMALY"
BOWLING_PROXY_PRIMARY_NAME = "BOWLING_EXPECTED_SCORING_THREAT"


def _empirical_percentile_rank(values: np.ndarray, ref_sorted: np.ndarray) -> np.ndarray:
    idx = np.searchsorted(ref_sorted, values, side="right")
    return np.clip(idx / max(len(ref_sorted), 1), 0.0, 1.0)


def apply_v42_revalidated_proxies(
    df: pd.DataFrame,
    b3_state: Dict[str, Any],
) -> pd.DataFrame:
    """Apply V4 zero-leakage B3 proxies plus V4.2 canonical columns and R(u,w) sensitivity."""
    out = apply_b3_resource_stress(df, b3_state)

    # Canonical V4.2 honest names (preserving backward-compatible aliases)
    out[BATTING_PROXY_PRIMARY_NAME] = out["bat_pressure"].astype(float)
    out["BATTING_RESOURCE_STRESS"] = out["bat_pressure"].astype(float)
    out[BOWLING_PROXY_PRIMARY_NAME] = out["bowl_pressure"].astype(float)
    out["BOWLING_SCORING_THREAT"] = out["bowl_pressure"].astype(float)

    # Alternative full R(u, w) resource-depletion sensitivity using fitted (b, gamma):
    # R(u, w) = ((1 - exp(-b * u)) / (1 - exp(-b))) * ((10 - w)/10)^gamma
    # Depletion anomaly = (1 - R(u, w)) - stage_mean(1 - R(u, w) | innings, overid)
    inn = out["innings"].astype(int).values
    u = np.clip(out["balls_rem_before"].values / 120.0, 0.0, 1.0)
    wk = np.clip((10.0 - out["wkts_before"].values) / 10.0, 0.0, 1.0)
    raw_full_depl = np.zeros(len(out), dtype=float)
    for inn_val in (1, 2):
        m = inn == inn_val
        if not np.any(m):
            continue
        _, b, gamma = b3_state["curve_params"][inn_val]
        denom = max(1.0 - float(np.exp(-b)), 1e-6)
        r_uw = ((1.0 - np.exp(-b * u[m])) / denom) * (np.power(np.maximum(wk[m], 1e-6), gamma))
        raw_full_depl[m] = 1.0 - np.clip(r_uw, 0.0, 1.0)

    out["_raw_full_ruw_depl"] = raw_full_depl
    stage_mean = out.groupby(["innings", "overid"])["_raw_full_ruw_depl"].transform("mean").values
    ruw_anom = raw_full_depl - stage_mean
    ruw_sorted = np.sort(ruw_anom)
    out["BAT_DEPLETION_FULL_RUW"] = _empirical_percentile_rank(ruw_anom, ruw_sorted)
    out.drop(columns=["_raw_full_ruw_depl"], inplace=True)
    return out


def build_v42_delivery_dataset(
    data_dir: str = "data",
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Load pre-delivery context, fit B3 proxy state, and attach V4.2 revalidated proxies."""
    df, matches = build_pre_delivery_context(data_dir)
    b3_state = fit_b3_resource_stress(df)
    df = apply_v42_revalidated_proxies(df, b3_state)
    return df, matches, b3_state


def describe_pressure_proxy_trace(b3_state: Dict[str, Any]) -> Dict[str, Any]:
    """Document exact equations, fitted parameters, missing state, and limitations."""
    c1 = b3_state["curve_params"][1]
    c2 = b3_state["curve_params"][2]
    return {
        "chase_score_reconstruction_blocked": CHASE_SCORE_RECONSTRUCTION_BLOCKED,
        "fitted_parameters": {
            "innings_1": {"R0": float(c1[0]), "b": float(c1[1]), "gamma": float(c1[2])},
            "innings_2": {"R0": float(c2[0]), "b": float(c2[1]), "gamma": float(c2[2])},
            "bowl_ridge_alpha": 10.0,
        },
        "parameter_role_trace": {
            "R0": (
                "Fitted scale parameter of expected remaining runs R(u,w) = R0*(1-exp(-b*u))*((10-w)/10)^gamma. "
                "Used ONLY during parameter optimization to fit gamma on clean non-DLS matches; NOT used directly in bat_pressure scoring."
            ),
            "b": (
                "Fitted ball-decay parameter of R(u,w). Absorbs balls-remaining expectations during MLE/LS estimation of gamma; "
                "NOT directly multiplied into bat_pressure, which uses (innings, overid) stage centering instead."
            ),
            "gamma": (
                "Fitted wicket-elasticity exponent. Directly enters raw_depl = 1 - ((10 - wickets_before)/10)^gamma before subtracting stage_exp[innings, overid]."
            ),
        },
        "proxies": {
            BATTING_PROXY_PRIMARY_NAME: {
                "aliases": ["BATTING_RESOURCE_STRESS", "bat_pressure"],
                "role_applies_to": "Batter facing each legal delivery (pre-delivery state).",
                "formula": "F_emp((1 - ((10 - wickets_before)/10)^gamma) - E[1 - ((10 - wickets_before)/10)^gamma | innings, overid])",
                "what_it_measures": "Wicket-depletion anomaly above the empirical innings-stage average; higher values indicate more wickets already lost than typical for that over and innings.",
                "inputs_used": ["innings", "overid", "wkts_before (wickets_before)", "fitted gamma (estimated using clean non-DLS matches)"],
                "missing_state_variables": ["exact score", "target score", "runs_required", "required_run_rate", "DLS par score"],
                "cannot_distinguish": "Cannot distinguish needing 12 runs from needing 70 runs when balls remaining and wickets remaining are identical.",
                "zero_leakage": True,
                "is_calibrated_match_leverage": False,
                "is_dls_resources": False,
            },
            BOWLING_PROXY_PRIMARY_NAME: {
                "aliases": ["BOWLING_SCORING_THREAT", "bowl_pressure"],
                "role_applies_to": "Bowler delivering each legal ball (pre-delivery state).",
                "formula": "F_emp(Ridge_10(alpha=10.0) predicted expected batter runs per 100b from pre-delivery innings, phase, overid, balls_rem, wickets_before, log(wickets_rem), venue_season)",
                "what_it_measures": "Expected pre-delivery batter scoring rate given match stage and resource state; higher values represent tougher scoring environments for the bowler.",
                "inputs_used": ["innings", "phase", "overid", "balls_rem_before", "wkts_before (wickets_before)", "venue_season"],
                "missing_state_variables": ["exact score", "target score", "runs_required", "required_run_rate", "match win-probability leverage"],
                "cannot_distinguish": "Cannot distinguish a defending bowler protecting a 10-run cushion in the final over from defending 35 runs in the final over.",
                "zero_leakage": True,
                "is_calibrated_match_leverage": False,
            },
            "BAT_DEPLETION_FULL_RUW": {
                "role_applies_to": "Sensitivity check only (batter).",
                "formula": "F_emp((1 - ((1-exp(-b*u))/(1-exp(-b))) * ((10-w)/10)^gamma) - E[.|innings, overid])",
                "what_it_measures": "Interpretable remaining-resource depletion combining fitted b (balls curve) and gamma (wicket curve) centered by innings-stage mean.",
                "is_calibrated_match_leverage": False,
            },
        },
    }
