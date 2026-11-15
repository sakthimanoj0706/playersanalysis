"""V4.1 Sections 5 & 8 — Exact Raw-vs-Adjusted Bridge, Composition Decomposition & Bowler Field Separation."""
from __future__ import annotations

import os
from typing import Tuple

import numpy as np
import pandas as pd


def build_raw_vs_adjusted_decomposition(
    res_df: pd.DataFrame,
    work_df: pd.DataFrame,
    role: str = "batter",
    hi_thr: float = 0.75,
) -> pd.DataFrame:
    """
    Build exact additive bridge from raw_observed_delta to context_adjusted_delta plus
    player-level composition shares (phase, format, season, wickets remaining, quantile, match exposure).
    """
    id_col = "striker_id" if role == "batter" else "bowler_id"
    w = work_df.copy()
    w["is_hi_z"] = w["p"] >= hi_thr
    w["is_pp"] = (w["phase"] == "powerplay").astype(float)
    w["is_mid"] = (w["phase"] == "middle").astype(float)
    w["is_death"] = (w["phase"] == "death").astype(float)
    w["is_recent_2526"] = (w["year"] >= 2025).astype(float)

    comp_hi = w[w["is_hi_z"]].groupby(id_col, as_index=False).agg(
        pp_share_hi=("is_pp", "mean"),
        mid_share_hi=("is_mid", "mean"),
        death_share_hi=("is_death", "mean"),
        t20i_share_hi=("is_t20i", "mean"),
        recent_2025_2026_share_hi=("is_recent_2526", "mean"),
        mean_wkts_rem_hi=("wkts_rem_before", "mean"),
    )
    comp_norm = w[~w["is_hi_z"]].groupby(id_col, as_index=False).agg(
        pp_share_norm=("is_pp", "mean"),
        mid_share_norm=("is_mid", "mean"),
        death_share_norm=("is_death", "mean"),
        t20i_share_norm=("is_t20i", "mean"),
        recent_2025_2026_share_norm=("is_recent_2526", "mean"),
        mean_wkts_rem_norm=("wkts_rem_before", "mean"),
    )

    m = (
        res_df
        .merge(comp_hi.rename(columns={id_col: "player_id"}), on="player_id", how="left")
        .merge(comp_norm.rename(columns={id_col: "player_id"}), on="player_id", how="left")
    )

    # Exact additive context decomposition:
    # context_par(t) = alpha_pfs(t) + alpha_pq_resid(t) + u_match(t) + psi_opp(t)
    # Subtracting context_par(hi) - context_par(norm) yields discrete_context_adjusted_delta identically.
    m["delta_shift_phase_fmt_season"] = -(m["hi_alpha_pfs"] - m["norm_alpha_pfs"])
    m["delta_shift_pressure_wkt_state"] = -(m["hi_alpha_pq"] - m["norm_alpha_pq"])
    m["delta_shift_match_par"] = -(m["hi_match_opp"] - m["norm_match_opp"])
    m["delta_shift_opponent_quality"] = -(m["hi_opp_only"] - m["norm_opp_only"])
    m["delta_shift_continuous_fwl_vs_discrete"] = (
        m["context_adjusted_delta"] - m["discrete_context_adjusted_delta"]
    )
    m["total_context_adjustment_shift"] = m["context_adjusted_delta"] - m["raw_observed_delta"]

    m["metric_unit"] = (
        "BATTER_RUNS_PER_100_BALLS (positive = higher strike rate under high BATTING_RESOURCE_STRESS)"
        if role == "batter"
        else "BATTER_RUNS_CONCEDED_PROXY_SAVED_PER_100_BALLS (+ = fewer batter-credited runs conceded under high BOWLING_SCORING_THREAT; multi-run wides/byes/legbyes unavailable)"
    )
    m["pressure_feature_used"] = (
        "BATTING_RESOURCE_STRESS (alias: bat_pressure)"
        if role == "batter"
        else "BOWLING_SCORING_THREAT (alias: bowl_pressure)"
    )
    return m


def export_decomposition_and_bowler_audit(
    bat_decomp: pd.DataFrame,
    bowl_decomp: pd.DataFrame,
    reg_df: pd.DataFrame,
    output_dir: str = "data/outputs/v4_1",
) -> pd.DataFrame:
    """
    Export unified V4_1_RAW_ADJUSTED_DECOMPOSITION.csv across precision-eligible candidates
    with all 10 mandatory comparison columns and explicit bowler metric separation.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Add bowler verified observable rate breakdown (legal balls, dot%, boundary%, wicket%, batter runs conceded/100b)
    leg = reg_df[reg_df["is_legal_ball"] == 1].copy()
    leg["is_four_or_six"] = ((leg["batter_runs"] == 4) | (leg["batter_runs"] == 6)).astype(int)
    b_obs = leg.groupby("bowler_id", as_index=False).agg(
        bowler_legal_balls=("is_legal_ball", "sum"),
        bowler_batter_runs_conceded=("batter_runs", "sum"),
        bowler_dot_balls=("is_ctrl_ball", "sum"),
        bowler_creditable_wickets=("is_bowler_wicket", "sum"),
        bowler_boundaries_conceded=("is_four_or_six", "sum"),
    )
    b_obs["bowler_batter_runs_per_100b"] = 100.0 * b_obs["bowler_batter_runs_conceded"] / np.maximum(b_obs["bowler_legal_balls"], 1)
    b_obs["bowler_dot_pct"] = 100.0 * b_obs["bowler_dot_balls"] / np.maximum(b_obs["bowler_legal_balls"], 1)
    b_obs["bowler_wicket_pct"] = 100.0 * b_obs["bowler_creditable_wickets"] / np.maximum(b_obs["bowler_legal_balls"], 1)
    b_obs["bowler_extras_status"] = "TOTAL_RUNS_UNAVAILABLE (wide/noball/penalty multi-run values unverified; legbyes/byes excluded)"
    bowl_m = bowl_decomp.merge(b_obs.rename(columns={"bowler_id": "player_id"}), on="player_id", how="left")

    common_cols = [
        "role", "player_id", "player_name", "formats_played", "metric_unit", "pressure_feature_used",
        "total_balls", "total_matches", "n_hi", "n_norm", "n_lo", "hi_matches", "lo_matches", "cs_matches",
        "raw_high_performance", "raw_normal_performance", "raw_observed_delta",
        "context_adjusted_high_performance", "context_adjusted_normal_performance",
        "discrete_context_adjusted_delta", "context_adjusted_delta",
        "empirical_bayes_delta", "lower_confidence_bound", "upper_confidence_bound",
        "probability_positive_effect", "eb_weight", "se_delta", "post_sd",
        "delta_shift_phase_fmt_season", "delta_shift_pressure_wkt_state",
        "delta_shift_match_par", "delta_shift_opponent_quality",
        "delta_shift_continuous_fwl_vs_discrete", "total_context_adjustment_shift",
        "pp_share_hi", "pp_share_norm", "mid_share_hi", "mid_share_norm",
        "death_share_hi", "death_share_norm", "t20i_share_hi", "t20i_share_norm",
        "recent_2025_2026_share_hi", "recent_2025_2026_share_norm", "mean_wkts_rem_hi", "mean_wkts_rem_norm",
        "mean_p_hi", "mean_p_norm", "mean_p_lo",
    ]
    bowler_extra = [
        "bowler_legal_balls", "bowler_batter_runs_conceded", "bowler_batter_runs_per_100b",
        "bowler_dot_balls", "bowler_dot_pct", "bowler_creditable_wickets", "bowler_wicket_pct",
        "bowler_boundaries_conceded", "bowler_extras_status",
    ]

    b_sub = bat_decomp[(bat_decomp["n_hi"] >= 30) & (bat_decomp["n_lo"] >= 30) & (bat_decomp["cs_matches"] >= 5)].copy()
    w_sub = bowl_m[(bowl_m["n_hi"] >= 30) & (bowl_m["n_lo"] >= 30) & (bowl_m["cs_matches"] >= 5)].copy()

    for c in bowler_extra:
        b_sub[c] = np.nan if c != "bowler_extras_status" else "NOT_APPLICABLE_BATTER"

    all_decomp = pd.concat([b_sub[common_cols + bowler_extra], w_sub[common_cols + bowler_extra]], ignore_index=True)
    all_decomp = all_decomp.sort_values(["role", "empirical_bayes_delta", "player_id"], ascending=[True, False, True]).reset_index(drop=True)
    all_decomp.to_csv(os.path.join(output_dir, "V4_1_RAW_ADJUSTED_DECOMPOSITION.csv"), index=False)
    return all_decomp
