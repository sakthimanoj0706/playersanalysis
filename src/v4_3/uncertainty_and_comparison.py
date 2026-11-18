"""Phase 7: Match-Cluster Bootstrap Uncertainty, Split-Half Reliability, & V4.2 Comparison."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import kendalltau, pearsonr, rankdata, spearmanr
from sklearn.linear_model import Ridge

from src.v4_3.config import DEFAULT_CONFIG, V43Config
from src.v4_3.joint_rapm import build_joint_rapm_design, fit_ridge_rapm


def _match_cluster_bootstrap_rapm(
    df: pd.DataFrame,
    design: Dict[str, Any],
    best_alpha: float,
    n_boot: int = 200,
    seed: int = 2026,
) -> Tuple[np.ndarray, np.ndarray]:
    """Run B match-cluster bootstrap refits of sparse Ridge RAPM."""
    X = design["X"]
    y = design["y"]
    n_bat = design["n_bat"]
    n_bowl = design["n_bowl"]

    # Map each match_id to its row indices in X/y
    m_groups = df.groupby("match_id", sort=False).indices
    match_keys = list(m_groups.keys())
    n_m = len(match_keys)
    idx_lists = [m_groups[k] for k in match_keys]

    bat_boot = np.empty((n_boot, n_bat), dtype=float)
    bowl_boot = np.empty((n_boot, n_bowl), dtype=float)

    rng = np.random.default_rng(seed)
    for b in range(n_boot):
        chosen = rng.integers(0, n_m, size=n_m)
        row_idx = np.concatenate([idx_lists[i] for i in chosen])
        m = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-4, random_state=seed)
        m.fit(X[row_idx], y[row_idx])
        c = m.coef_
        bat_raw = c[:n_bat]
        bowl_raw = c[n_bat : n_bat + n_bowl]
        bat_boot[b] = (bat_raw - float(np.mean(bat_raw))) * 100.0
        bowl_boot[b] = -(bowl_raw - float(np.mean(bowl_raw))) * 100.0

    return bat_boot, bowl_boot


def _attach_uncertainty(
    role_df: pd.DataFrame,
    player_ids_order: np.ndarray,
    boot_mat: np.ndarray,
    score_col: str,
    balls_col: str,
    min_balls: int = 300,
) -> pd.DataFrame:
    """Attach bootstrap SE, 95% CI, rank CI, and Top-10/20 probabilities."""
    pid_to_col = {pid: i for i, pid in enumerate(player_ids_order)}
    col_idx = np.array([pid_to_col[p] for p in role_df["player_id"].values])
    mat = boot_mat[:, col_idx]

    out = role_df.copy()
    out["boot_se"] = np.std(mat, axis=0, ddof=1)
    out["ci_low_95"] = np.percentile(mat, 2.5, axis=0)
    out["ci_high_95"] = np.percentile(mat, 97.5, axis=0)
    out["eligible_balls_300"] = out[balls_col] >= min_balls

    # Rank metrics over eligible pool
    elig_mask = out["eligible_balls_300"].values
    out["final_rank"] = np.nan
    out["boot_rank_ci_low"] = np.nan
    out["boot_rank_ci_high"] = np.nan
    out["prob_top_10"] = 0.0
    out["prob_top_20"] = 0.0

    if elig_mask.sum() > 0:
        elig_scores = out.loc[elig_mask, score_col].values
        out.loc[elig_mask, "final_rank"] = rankdata(-np.round(elig_scores, 10), method="average")

        elig_mat = mat[:, elig_mask]
        ranks_mat = np.apply_along_axis(lambda r: rankdata(-np.round(r, 10), method="average"), 1, elig_mat)
        out.loc[elig_mask, "boot_rank_ci_low"] = np.percentile(ranks_mat, 2.5, axis=0)
        out.loc[elig_mask, "boot_rank_ci_high"] = np.percentile(ranks_mat, 97.5, axis=0)
        out.loc[elig_mask, "prob_top_10"] = np.mean(ranks_mat <= 10.0, axis=0)
        out.loc[elig_mask, "prob_top_20"] = np.mean(ranks_mat <= 20.0, axis=0)

    out["reliability_indicator"] = np.where(
        out[balls_col] >= 750,
        "HIGH_EXPOSURE",
        np.where(out[balls_col] >= min_balls, "MODERATE_EXPOSURE", "LOW_EXPOSURE_UNRANKED"),
    )
    return out


def _split_half_tests(
    df: pd.DataFrame,
    design: Dict[str, Any],
    best_alpha: float,
    elig_bat: set,
    elig_bowl: set,
    n_splits: int = 10,
    seed: int = 2026,
) -> pd.DataFrame:
    """Repeated 50/50 match-level split-half reliability tests."""
    m_groups = df.groupby("match_id", sort=False).indices
    match_keys = np.array(list(m_groups.keys()))
    idx_lists = [m_groups[k] for k in match_keys]
    n_m = len(match_keys)

    X = design["X"]
    y = design["y"]
    n_bat = design["n_bat"]
    n_bowl = design["n_bowl"]
    bat_mask = np.array([p in elig_bat for p in design["batter_ids"]])
    bowl_mask = np.array([p in elig_bowl for p in design["bowler_ids"]])

    rng = np.random.default_rng(seed)
    rows: List[Dict[str, Any]] = []
    for s in range(1, n_splits + 1):
        perm = rng.permutation(n_m)
        half = n_m // 2
        idx_a = np.concatenate([idx_lists[i] for i in perm[:half]])
        idx_b = np.concatenate([idx_lists[i] for i in perm[half:]])

        m_a = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-4, random_state=seed).fit(X[idx_a], y[idx_a])
        m_b = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-4, random_state=seed).fit(X[idx_b], y[idx_b])

        for role, sl, mask in [
            ("batter", slice(0, n_bat), bat_mask),
            ("bowler", slice(n_bat, n_bat + n_bowl), bowl_mask),
        ]:
            va = m_a.coef_[sl][mask]
            vb = m_b.coef_[sl][mask]
            if role == "bowler":
                va, vb = -va, -vb
            rho, _ = spearmanr(va, vb)
            r, _ = pearsonr(va, vb)
            rows.append(
                {
                    "split_id": s,
                    "role": role,
                    "n_eligible": int(mask.sum()),
                    "spearman_r": round(float(rho), 4),
                    "pearson_r": round(float(r), 4),
                }
            )
    return pd.DataFrame(rows)


def run_phase7_uncertainty_and_comparison(
    bat_df: pd.DataFrame,
    bowl_df: pd.DataFrame,
    rapm_meta: Dict[str, Any],
    cfg: V43Config = DEFAULT_CONFIG,
    n_boot: int = 200,
    n_splits: int = 10,
) -> Dict[str, pd.DataFrame]:
    """Run match-cluster bootstrap, split-half tests, eligibility sensitivity, and V4.2 comparison."""
    cfg.ensure_dirs()
    df = rapm_meta["df_with_elo"]
    design = rapm_meta["design_bundle"]
    best_alpha = float(rapm_meta["best_alpha"])

    # 1. Match-cluster bootstrap
    bat_boot, bowl_boot = _match_cluster_bootstrap_rapm(
        df, design, best_alpha, n_boot=n_boot, seed=cfg.random_seed
    )

    bat_u = _attach_uncertainty(
        bat_df, design["batter_ids"], bat_boot, "rapm_batter_per100", "legal_balls_faced", min_balls=300
    )
    bowl_u = _attach_uncertainty(
        bowl_df, design["bowler_ids"], bowl_boot, "rapm_bowler_defensive_per100", "legal_balls_bowled", min_balls=300
    )
    bat_u.to_csv(cfg.output_dir / "V4_3_BATTER_RAPM.csv", index=False)
    bowl_u.to_csv(cfg.output_dir / "V4_3_BOWLER_RAPM.csv", index=False)

    # 2. Split-half reliability
    elig_bat = set(bat_u.loc[bat_u["eligible_balls_300"], "player_id"])
    elig_bowl = set(bowl_u.loc[bowl_u["eligible_balls_300"], "player_id"])
    split_df = _split_half_tests(df, design, best_alpha, elig_bat, elig_bowl, n_splits=n_splits, seed=cfg.random_seed)
    split_df.to_csv(cfg.output_dir / "V4_3_SPLIT_HALF_RELIABILITY.csv", index=False)

    # 3. Eligibility threshold sensitivity
    sens_rows: List[Dict[str, Any]] = []
    for role, u_df, b_col, s_col in [
        ("batter", bat_u, "legal_balls_faced", "rapm_batter_per100"),
        ("bowler", bowl_u, "legal_balls_bowled", "rapm_bowler_defensive_per100"),
    ]:
        for thresh in (150, 300, 500, 750):
            sub = u_df[u_df[b_col] >= thresh].sort_values(s_col, ascending=False)
            sens_rows.append(
                {
                    "role": role,
                    "min_legal_balls_threshold": thresh,
                    "n_eligible": int(len(sub)),
                    "median_boot_se": round(float(sub["boot_se"].median()), 4) if len(sub) else np.nan,
                    "top10_players": ", ".join(sub["player_name"].head(10).tolist()),
                }
            )
    sens_df = pd.DataFrame(sens_rows)
    sens_df.to_csv(cfg.output_dir / "V4_3_ELIGIBILITY_SENSITIVITY.csv", index=False)

    # 4. Ranking stability summary
    stab_rows: List[Dict[str, Any]] = []
    for role, u_df, s_col in [
        ("batter", bat_u, "rapm_batter_per100"),
        ("bowler", bowl_u, "rapm_bowler_defensive_per100"),
    ]:
        el = u_df[u_df["eligible_balls_300"]]
        sh = split_df[split_df["role"] == role]
        stab_rows.append(
            {
                "role": role,
                "n_eligible_300b": int(len(el)),
                "median_boot_se": round(float(el["boot_se"].median()), 4),
                "median_rank_ci_width": round(float((el["boot_rank_ci_high"] - el["boot_rank_ci_low"]).median()), 2),
                "split_half_spearman_mean": round(float(sh["spearman_r"].mean()), 4),
                "split_half_spearman_sd": round(float(sh["spearman_r"].std()), 4),
                "split_half_pearson_mean": round(float(sh["pearson_r"].mean()), 4),
                "boot_iters": n_boot,
                "split_half_iters": n_splits,
            }
        )
    stab_df = pd.DataFrame(stab_rows)
    stab_df.to_csv(cfg.output_dir / "V4_3_RANKING_STABILITY.csv", index=False)

    # 5. V4.2 vs V4.3 Comparison on same eligible V4.2 population
    v42 = pd.read_csv("data/outputs/v4_2/V4_2_ALL_PLAYER_ESTIMATES.csv")
    comp_rows: List[Dict[str, Any]] = []
    for role, u_df, v43_col in [
        ("batter", bat_u, "rapm_batter_per100"),
        ("bowler", bowl_u, "rapm_bowler_defensive_per100"),
    ]:
        v42_el = v42[(v42["role"] == role) & (v42["eligible"] == True)].copy()
        merged = v42_el.merge(u_df[["player_id", v43_col, "boot_se"]], on="player_id", how="inner")
        merged["v43_rank_on_common"] = rankdata(-merged[v43_col].values, method="average")
        merged["v42_rank_eb"] = rankdata(-merged["eb_delta"].values, method="average")
        merged["v42_rank_skill"] = rankdata(-merged["claim_a_general_skill_fe"].values, method="average")

        for v42_col, v42_rcol, desc in [
            ("eb_delta", "v42_rank_eb", "V4.2 Pressure Slope (EB Delta) vs V4.3 Overall Batter-Run RAPM"),
            ("claim_a_general_skill_fe", "v42_rank_skill", "V4.2 General Skill FE (Claim A) vs V4.3 Overall Batter-Run RAPM"),
        ]:
            sp, _ = spearmanr(merged[v42_col], merged[v43_col])
            kt, _ = kendalltau(merged[v42_col], merged[v43_col])
            t10_42 = set(merged.nsmallest(10, v42_rcol)["player_id"])
            t10_43 = set(merged.nsmallest(10, "v43_rank_on_common")["player_id"])
            t20_42 = set(merged.nsmallest(20, v42_rcol)["player_id"])
            t20_43 = set(merged.nsmallest(20, "v43_rank_on_common")["player_id"])
            rank_diff = np.abs(merged[v42_rcol] - merged["v43_rank_on_common"])
            comp_rows.append(
                {
                    "role": role,
                    "comparison": desc,
                    "common_eligible_n": int(len(merged)),
                    "spearman_r": round(float(sp), 4),
                    "kendall_tau": round(float(kt), 4),
                    "top10_overlap": int(len(t10_42 & t10_43)),
                    "top20_overlap": int(len(t20_42 & t20_43)),
                    "median_abs_rank_shift": round(float(np.median(rank_diff)), 1),
                    "max_abs_rank_shift": round(float(np.max(rank_diff)), 1),
                }
            )
    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(cfg.output_dir / "V4_3_MODEL_COMPARISON.csv", index=False)

    return {
        "bat_u": bat_u,
        "bowl_u": bowl_u,
        "split_df": split_df,
        "sens_df": sens_df,
        "stab_df": stab_df,
        "comp_df": comp_df,
    }
