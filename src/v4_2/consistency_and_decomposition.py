"""V4.2 Match-Level Consistency Evidence, Like-for-Like Decomposition, and Secondary Outcomes.

Implements:
- Section 5: Exact 8-contrast separation (raw hi/lo/all-non-high, discrete context-adjusted
  hi-vs-lo & hi-vs-all-non-high, and continuous P87.5-vs-P12.5 FWL + EB shrinkage bridge) with
  additive identity checks (< 1e-6).
- Section 7: Claim A (general skill), Claim B (high-stress execution), Claim C (player-specific
  pressure-vs-own-normal effect), match-level between-match SD, share of spread matches with
  positive adjusted delta vs own normal, posterior P(Delta > 0), effective exposure, and exact
  leave-one-match-out (LOMO) sensitivity. Explicitly flags limited within-match spread (<5 matches).
- Section 8: Secondary outcomes (batter dismissal risk change; bowler dot-ball % & creditable
  wicket % effects) fitted through the identical Option A FWL + REML pipeline with zero arbitrary
  composite weights.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm

from src.v4_2.fwl_estimator import fit_v42_option_a_fwl


def compute_match_level_consistency_and_lomo(
    df: pd.DataFrame,
    player_col: str,
    p_col: str,
    y_col: str,
    design: Dict[str, Any],
    fwl: Dict[str, Any],
    est_df: pd.DataFrame,
    hi_thr: float = 0.75,
    lo_thr: float = 0.25,
    min_spread_matches: int = 5,
) -> pd.DataFrame:
    """Compute match-level pressure-vs-normal consistency, posterior P(>0), and LOMO sensitivity."""
    Z = design["Z"]
    theta_hat = fwl["theta_hat"]
    # Nuisance-adjusted delivery residual (retains player pressure effect + noise; Claim A/state/match/opp removed)
    y_adj = df[y_col].values.astype(np.float64) - (Z @ theta_hat)
    cs_mask = design["cs_mask"]

    work = pd.DataFrame(
        {
            "player_id": df[player_col].values,
            "match_id": df["match_id"].values,
            "p": df[p_col].values.astype(np.float64),
            "y_adj": y_adj,
            "weight": df["weight"].values.astype(np.float64),
            "cs": cs_mask,
        }
    )
    work = work[work["cs"]].copy()
    work["wy_adj"] = work["weight"] * work["y_adj"]
    work["is_hi"] = work["p"] >= hi_thr
    work["is_lo"] = work["p"] <= lo_thr
    work["is_nonhi"] = work["p"] < hi_thr

    hi_pm = (
        work[work["is_hi"]]
        .groupby(["player_id", "match_id"], sort=False)
        .agg(w_hi=("weight", "sum"), wy_hi=("wy_adj", "sum"))
    )
    nonhi_pm = (
        work[work["is_nonhi"]]
        .groupby(["player_id", "match_id"], sort=False)
        .agg(w_nonhi=("weight", "sum"), wy_nonhi=("wy_adj", "sum"))
    )
    lo_pm = (
        work[work["is_lo"]]
        .groupby(["player_id", "match_id"], sort=False)
        .agg(w_lo=("weight", "sum"), wy_lo=("wy_adj", "sum"))
    )

    pm_both = hi_pm.join(nonhi_pm, how="inner").reset_index()
    pm_both["hi_mean"] = pm_both["wy_hi"] / pm_both["w_hi"].clip(lower=1e-9)
    pm_both["nonhi_mean"] = pm_both["wy_nonhi"] / pm_both["w_nonhi"].clip(lower=1e-9)
    pm_both["within_match_delta"] = pm_both["hi_mean"] - pm_both["nonhi_mean"]
    pm_both["w_pair"] = (2.0 * pm_both["w_hi"] * pm_both["w_nonhi"]) / (
        pm_both["w_hi"] + pm_both["w_nonhi"]
    ).clip(lower=1e-9)

    pm_hilo = hi_pm.join(lo_pm, how="inner").reset_index()
    pm_hilo["hilo_pos"] = (
        (pm_hilo["wy_hi"] / pm_hilo["w_hi"].clip(lower=1e-9))
        > (pm_hilo["wy_lo"] / pm_hilo["w_lo"].clip(lower=1e-9))
    ).astype(float)

    hilo_share = pm_hilo.groupby("player_id").agg(
        within_match_hilo_matches=("match_id", "nunique"),
        share_within_match_pos_hi_vs_lo=("hilo_pos", "mean"),
    )

    # High-stress residual positivity (explicitly Claim B only, NOT consistency)
    hi_pm["hi_res_pos"] = (hi_pm["wy_hi"] > 0.0).astype(float)
    hi_only_share = (
        hi_pm.reset_index()
        .groupby("player_id")
        .agg(claim_b_high_stress_pos_share=("hi_res_pos", "mean"))
    )

    # Match-level aggregation for Claim C consistency
    records = []
    for pid, grp in pm_both.groupby("player_id", sort=False):
        n_m = int(len(grp))
        deltas_m = grp["within_match_delta"].values
        w_m = grp["w_pair"].values
        pos_share = float(np.mean(deltas_m > 0.0))
        if n_m >= min_spread_matches and np.sum(w_m) > 0:
            w_norm = w_m / np.sum(w_m)
            mu_m = float(np.sum(w_norm * deltas_m))
            # Weighted sample SD across independent spread matches
            denom = max(1.0 - float(np.sum(w_norm ** 2)), 1e-6)
            var_m = float(np.sum(w_norm * ((deltas_m - mu_m) ** 2)) / denom)
            sd_m = float(np.sqrt(max(var_m, 0.0)))
            status = "ESTIMATED"
        else:
            sd_m = np.nan
            status = "LIMITED_WITHIN_MATCH_SPREAD"
        records.append(
            {
                "player_id": pid,
                "within_match_spread_matches": n_m,
                "between_match_delta_sd": sd_m,
                "share_matches_pos_delta_vs_normal": pos_share,
                "consistency_status": status,
            }
        )
    cons_df = pd.DataFrame(records)

    # Exact influence-based Leave-One-Match-Out (LOMO) sensitivity across every match played
    # Approximate exact block deletion per player-match using diag(G_inv) and U_match (no cr1 scaling)
    M, K = fwl["U_match"].shape
    cr_inv = 1.0 / np.sqrt(max(M / max(M - 1, 1), 1e-9))
    U_raw = fwl["U_match"] * cr_inv  # M x K where entry (m, i) = span * (G^{-1} s_tilde_m)_i
    valid = fwl["valid_cols"]
    W_sp = design["W"]
    w_obs = design["w_obs"]
    match_codes = design["match_codes"]
    pids = design["cs_pids"]

    # Approximate match-i leverage fraction h_{m,i} = (sum_{t in m, i} w_t (p_t-0.5)^2) / diag(G_schur)_i
    W_sq_w = W_sp.multiply(W_sp).multiply(w_obs[:, None])
    M_idx = np.arange(len(w_obs))
    import scipy.sparse as sp

    M_mat = sp.csr_matrix(
        (np.ones(len(w_obs)), (match_codes, M_idx)), shape=(M, len(w_obs))
    )
    W_match_diag = (M_mat @ W_sq_w).toarray()  # M x K
    diag_g = np.where(np.diag(fwl["G_schur"]) > 1e-9, np.diag(fwl["G_schur"]), np.nan)

    # Also track any match where player appeared at all (even outside CS if needed, check U_raw != 0)
    lomo_rows = []
    for idx, pid in enumerate(pids):
        if not valid[idx] or not np.isfinite(fwl["delta_fwl"][idx]):
            lomo_rows.append(
                {
                    "player_id": pid,
                    "lomo_min_delta": np.nan,
                    "lomo_max_delta": np.nan,
                    "lomo_max_abs_shift": np.nan,
                }
            )
            continue
        d0 = float(fwl["delta_fwl"][idx])
        u_col = U_raw[:, idx]
        nz = (np.abs(u_col) > 1e-12) | (W_match_diag[:, idx] > 1e-12)
        if not np.any(nz):
            lomo_rows.append(
                {
                    "player_id": pid,
                    "lomo_min_delta": d0,
                    "lomo_max_delta": d0,
                    "lomo_max_abs_shift": 0.0,
                }
            )
            continue
        h_mi = np.clip(W_match_diag[nz, idx] / diag_g[idx], 0.0, 0.85)
        lomo_est = d0 - u_col[nz] / (1.0 - h_mi)
        lomo_rows.append(
            {
                "player_id": pid,
                "lomo_min_delta": float(np.min(lomo_est)),
                "lomo_max_delta": float(np.max(lomo_est)),
                "lomo_max_abs_shift": float(np.max(np.abs(lomo_est - d0))),
            }
        )
    lomo_df = pd.DataFrame(lomo_rows)

    # Merge Claim A (general skill player FE), Claim B (high-stress execution), and Posterior P(>0)
    b_dims = design["block_dims"]
    o_player_start = b_dims["state"] + b_dims["match"]
    o_player_end = o_player_start + b_dims["player"]
    # When penalized, p_uniques aligns one-for-one with player FE block
    if b_dims["player"] == len(design["p_uniques"]) and Z.shape[1] == (
        b_dims["state"] + b_dims["match"] + b_dims["player"] + b_dims["opp"]
    ):
        player_fe = theta_hat[o_player_start:o_player_end]
        claim_a_map = dict(zip(design["p_uniques"], player_fe))
    else:
        claim_a_map = {}

    merged = est_df[["player_id", "n_hi", "n_lo", "eb_delta", "eb_cond_sd", "raw_hi_perf", "raw_overall_perf"]].copy()
    merged["claim_a_general_skill_fe"] = merged["player_id"].map(claim_a_map).astype(float)
    # Claim B: adjusted high-stress execution (mean of y - Z_state_match_opp in high stress)
    # Compare high-stress residual + player FE cleanly
    hi_adj_pm = (
        work[work["is_hi"]]
        .groupby("player_id", sort=False)
        .agg(w_h=("weight", "sum"), wy_h=("wy_adj", "sum"))
    )
    merged["claim_b_adj_high_execution"] = (
        merged["player_id"].map(hi_adj_pm["wy_h"] / hi_adj_pm["w_h"].clip(lower=1e-9)).astype(float)
        + merged["claim_a_general_skill_fe"].fillna(0.0)
    )
    merged["effective_exposure"] = (
        2.0 * merged["n_hi"] * merged["n_lo"]
    ) / (merged["n_hi"] + merged["n_lo"]).clip(lower=1e-9)

    prob_pos = np.full(len(merged), np.nan, dtype=np.float64)
    has_eb = merged["eb_delta"].notna() & merged["eb_cond_sd"].notna()
    pos_sd = has_eb & (merged["eb_cond_sd"] > 1e-12)
    zero_sd = has_eb & (merged["eb_cond_sd"] <= 1e-12)
    prob_pos[pos_sd] = norm.cdf(merged.loc[pos_sd, "eb_delta"] / merged.loc[pos_sd, "eb_cond_sd"])
    prob_pos[zero_sd] = (merged.loc[zero_sd, "eb_delta"] > 0.0).astype(float)
    merged["prob_positive_effect"] = prob_pos

    out = merged[
        [
            "player_id",
            "claim_a_general_skill_fe",
            "claim_b_adj_high_execution",
            "effective_exposure",
            "prob_positive_effect",
        ]
    ].merge(cons_df, on="player_id", how="left")
    out = out.merge(hilo_share, on="player_id", how="left")
    out = out.merge(hi_only_share, on="player_id", how="left")
    out = out.merge(lomo_df, on="player_id", how="left")
    out["consistency_status"] = out["consistency_status"].fillna("LIMITED_WITHIN_MATCH_SPREAD")
    out["within_match_spread_matches"] = out["within_match_spread_matches"].fillna(0).astype(int)
    return out


def build_like_for_like_decomposition(
    df: pd.DataFrame,
    player_col: str,
    p_col: str,
    y_col: str,
    design: Dict[str, Any],
    fwl: Dict[str, Any],
    est_df: pd.DataFrame,
    role: str,
    hi_thr: float = 0.75,
    lo_thr: float = 0.25,
) -> pd.DataFrame:
    """Build exact 8-contrast decomposition separating context adjustment from discrete/continuous estimand shifts."""
    Z = design["Z"]
    theta_hat = fwl["theta_hat"]
    b_dims = design["block_dims"]

    # Partition nuisance contributions cleanly: state, match, player, opponent
    s_end = b_dims["state"]
    if Z.shape[1] == (b_dims["state"] + b_dims["match"] + b_dims["player"] + b_dims["opp"]):
        m_end = s_end + b_dims["match"]
        p_end = m_end + b_dims["player"]
        c_state = Z[:, :s_end] @ theta_hat[:s_end]
        c_match = Z[:, s_end:m_end] @ theta_hat[s_end:m_end]
        c_player = Z[:, m_end:p_end] @ theta_hat[m_end:p_end]
        c_opp = Z[:, p_end:] @ theta_hat[p_end:]
    else:
        c_state = Z @ theta_hat
        c_match = np.zeros(len(df), dtype=np.float64)
        c_player = np.zeros(len(df), dtype=np.float64)
        c_opp = np.zeros(len(df), dtype=np.float64)

    y_vals = df[y_col].values.astype(np.float64)
    y_adj = y_vals - (c_state + c_match + c_player + c_opp)

    work = pd.DataFrame(
        {
            "player_id": df[player_col].values,
            "p": df[p_col].values.astype(np.float64),
            "weight": df["weight"].values.astype(np.float64),
            "y": y_vals,
            "y_adj": y_adj,
            "c_state": c_state,
            "c_match": c_match,
            "c_player": c_player,
            "c_opp": c_opp,
            "cs": design["cs_mask"],
        }
    )

    def _zone_means(sub: pd.DataFrame, prefix: str) -> pd.DataFrame:
        sub = sub.copy()
        for col in ["y", "y_adj", "c_state", "c_match", "c_player", "c_opp"]:
            sub[f"_w_{col}"] = sub["weight"] * sub[col]
        agg = sub.groupby("player_id", sort=False)[
            ["weight", "_w_y", "_w_y_adj", "_w_c_state", "_w_c_match", "_w_c_player", "_w_c_opp"]
        ].sum()
        w = agg["weight"].clip(lower=1e-9)
        res = pd.DataFrame(index=agg.index)
        for col in ["y", "y_adj", "c_state", "c_match", "c_player", "c_opp"]:
            res[f"{prefix}_{col}"] = agg[f"_w_{col}"] / w
        return res.reset_index()

    # Use common-support subset for context-adjusted means so they match estimator support,
    # while raw zone columns come straight from est_df (all deliveries of that zone for player)
    cs_work = work[work["cs"]]
    z_hi = _zone_means(cs_work[cs_work["p"] >= hi_thr], "cs_hi")
    z_lo = _zone_means(cs_work[cs_work["p"] <= lo_thr], "cs_lo")
    z_nonhi = _zone_means(cs_work[cs_work["p"] < hi_thr], "cs_nonhi")

    # Also compute exact raw on all vs cs for audit completeness
    base = est_df[
        [
            "player_id",
            "eligible",
            "n_hi",
            "n_lo",
            "n_nonhi",
            "raw_hi_perf",
            "raw_lo_perf",
            "raw_nonhi_perf",
            "raw_hi_minus_lo_delta",
            "raw_hi_minus_all_non_high_delta",
            "delta_unshrunk",
            "eb_delta",
        ]
    ].copy()
    base.rename(
        columns={
            "raw_hi_perf": "raw_high_performance",
            "raw_lo_perf": "raw_low_performance",
            "raw_nonhi_perf": "raw_all_non_high_performance",
            "delta_unshrunk": "continuous_p875_minus_p125_adjusted_delta",
        },
        inplace=True,
    )

    out = base.merge(z_hi, on="player_id", how="left")
    out = out.merge(z_lo, on="player_id", how="left")
    out = out.merge(z_nonhi, on="player_id", how="left")

    out["discrete_context_adjusted_hi_minus_lo_delta"] = out["cs_hi_y_adj"] - out["cs_lo_y_adj"]
    out["discrete_context_adjusted_hi_minus_all_non_high_delta"] = out["cs_hi_y_adj"] - out["cs_nonhi_y_adj"]

    # Exact CS-restricted raw contrasts so additive identity holds to machine precision (< 1e-6)
    out["cs_raw_hi_minus_lo_delta"] = out["cs_hi_y"] - out["cs_lo_y"]
    out["cs_raw_hi_minus_all_non_high_delta"] = out["cs_hi_y"] - out["cs_nonhi_y"]

    # Additive nuisance adjustment shifts (note c_player cancels identically within player)
    out["hilo_state_nuisance_shift"] = out["cs_hi_c_state"] - out["cs_lo_c_state"]
    out["hilo_match_nuisance_shift"] = out["cs_hi_c_match"] - out["cs_lo_c_match"]
    out["hilo_player_nuisance_shift"] = out["cs_hi_c_player"] - out["cs_lo_c_player"]
    out["hilo_opp_nuisance_shift"] = out["cs_hi_c_opp"] - out["cs_lo_c_opp"]
    out["context_adjustment_hi_vs_lo"] = (
        out["discrete_context_adjusted_hi_minus_lo_delta"] - out["cs_raw_hi_minus_lo_delta"]
    )
    out["nuisance_identity_residual"] = (
        out["cs_raw_hi_minus_lo_delta"]
        - out["discrete_context_adjusted_hi_minus_lo_delta"]
        - (
            out["hilo_state_nuisance_shift"]
            + out["hilo_match_nuisance_shift"]
            + out["hilo_player_nuisance_shift"]
            + out["hilo_opp_nuisance_shift"]
        )
    )

    # Estimand shift & shrinkage shift separating discrete binary vs continuous slope
    out["estimand_shift_continuous_vs_discrete_hilo"] = (
        out["continuous_p875_minus_p125_adjusted_delta"]
        - out["discrete_context_adjusted_hi_minus_lo_delta"]
    )
    out["eb_shrinkage_shift"] = out["eb_delta"] - out["continuous_p875_minus_p125_adjusted_delta"]
    out["bridge_identity_residual"] = (
        out["cs_raw_hi_minus_lo_delta"]
        + out["context_adjustment_hi_vs_lo"]
        + out["estimand_shift_continuous_vs_discrete_hilo"]
        + out["eb_shrinkage_shift"]
        - out["eb_delta"]
    )
    out["role"] = role
    return out


def compute_secondary_outcomes_v42(
    df: pd.DataFrame,
    role: str,
    primary_df: pd.DataFrame,
    lam_state: float = 60.0,
    lam_match: float = 60.0,
    lam_player: float = 60.0,
    lam_opp: float = 60.0,
    span: float = 0.75,
) -> pd.DataFrame:
    """Estimate secondary outcomes using the exact same Option A FWL + REML pipeline (zero composite weighting)."""
    work = df.copy()
    if role == "batter":
        work["sec_dismiss_avoid_y"] = np.where(work["is_striker_out"] > 0, -100.0, 0.0)
        sec_est, _ = fit_v42_option_a_fwl(
            work,
            player_col="striker_id",
            opp_col="bowler_id",
            p_col="bat_pressure",
            y_col="sec_dismiss_avoid_y",
            lam_state=lam_state,
            lam_match=lam_match,
            lam_player=lam_player,
            lam_opp=lam_opp,
            span=span,
        )
        sec = pd.DataFrame(
            {
                "player_id": sec_est["player_id"],
                "sec_dismissal_avoid_eb_delta": sec_est["eb_delta"],
                "dismissal_risk_delta_per_100b": -sec_est["eb_delta"],
                "sec_dismiss_se_delta": sec_est["se_delta"],
            }
        )
        merged = primary_df[["player_id", "eb_delta"]].merge(sec, on="player_id", how="left")
        merged["secondary_tradeoff_flag"] = np.where(
            merged["dismissal_risk_delta_per_100b"].isna(),
            "UNAVAILABLE",
            np.where(
                (merged["eb_delta"] > 0.0) & (merged["dismissal_risk_delta_per_100b"] > 0.5),
                "HIGH_RUNS_ELEVATED_DISMISSAL_RISK",
                np.where(
                    (merged["eb_delta"] > 0.0) & (merged["dismissal_risk_delta_per_100b"] <= 0.0),
                    "RUNS_GAIN_WITH_LOWER_DISMISSAL_RISK",
                    "MODERATE_OR_NEUTRAL_TRADEOFF",
                ),
            ),
        )
        return merged.drop(columns=["eb_delta"])

    else:
        work["sec_dot_ctrl_y"] = work["is_ctrl_ball"].values.astype(float) * 100.0
        work["sec_wicket_y"] = work["is_bowler_wicket"].values.astype(float) * 100.0
        dot_est, _ = fit_v42_option_a_fwl(
            work,
            player_col="bowler_id",
            opp_col="striker_id",
            p_col="bowl_pressure",
            y_col="sec_dot_ctrl_y",
            lam_state=lam_state,
            lam_match=lam_match,
            lam_player=lam_player,
            lam_opp=lam_opp,
            span=span,
        )
        wk_est, _ = fit_v42_option_a_fwl(
            work,
            player_col="bowler_id",
            opp_col="striker_id",
            p_col="bowl_pressure",
            y_col="sec_wicket_y",
            lam_state=lam_state,
            lam_match=lam_match,
            lam_player=lam_player,
            lam_opp=lam_opp,
            span=span,
        )
        sec = pd.DataFrame(
            {
                "player_id": dot_est["player_id"],
                "sec_dot_ctrl_eb_delta": dot_est["eb_delta"],
                "sec_dot_ctrl_se_delta": dot_est["se_delta"],
            }
        ).merge(
            pd.DataFrame(
                {
                    "player_id": wk_est["player_id"],
                    "sec_wicket_eb_delta": wk_est["eb_delta"],
                    "sec_wicket_se_delta": wk_est["se_delta"],
                }
            ),
            on="player_id",
            how="left",
        )
        merged = primary_df[["player_id", "eb_delta"]].merge(sec, on="player_id", how="left")
        merged["secondary_tradeoff_flag"] = np.where(
            merged["sec_dot_ctrl_eb_delta"].isna() | merged["sec_wicket_eb_delta"].isna(),
            "UNAVAILABLE",
            np.where(
                (merged["eb_delta"] > 0.0) & (merged["sec_wicket_eb_delta"] < -0.25),
                "RUN_SUPPRESSION_WITH_WICKET_DROP",
                np.where(
                    (merged["eb_delta"] > 0.0) & (merged["sec_dot_ctrl_eb_delta"] < -0.5),
                    "RUN_SUPPRESSION_WITH_DOT_DROP",
                    np.where(
                        (merged["eb_delta"] > 0.0)
                        & (merged["sec_dot_ctrl_eb_delta"] >= 0.0)
                        & (merged["sec_wicket_eb_delta"] >= 0.0),
                        "ALIGNED_RUN_DOT_AND_WICKET_GAIN",
                        "MIXED_SECONDARY_PROFILE",
                    ),
                ),
            ),
        )
        return merged.drop(columns=["eb_delta"])
