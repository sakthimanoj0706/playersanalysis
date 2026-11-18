"""Phase 1: Asymmetric Block-Penalized Joint Ridge RAPM for SupeRR Intelligence V5.0."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold

from src.v4_3.config import DEFAULT_CONFIG as V43_CFG
from src.v4_3.win_probability import compute_pre_match_elo
from src.v5_0.config import DEFAULT_V50_CONFIG, V50Config


def build_asymmetric_blocks(
    df: pd.DataFrame,
    pressure_col: str = "H_global_150",
    batter_ids: np.ndarray | None = None,
    bowler_ids: np.ndarray | None = None,
    season_levels: List[str] | None = None,
    cont_stats: Dict[str, Tuple[float, float]] | None = None,
) -> Dict[str, Any]:
    """
    Build [X_main, X_pressure, X_context] sparse blocks.
    Standardizes continuous context features using provided training-fold stats only.
    """
    n = len(df)
    if batter_ids is None:
        batter_ids = np.sort(df["striker_id"].dropna().unique())
    if bowler_ids is None:
        bowler_ids = np.sort(df["bowler_id"].dropna().unique())
    if season_levels is None:
        s_all = sorted(df["season"].astype(str).unique().tolist())
        season_levels = s_all[1:]

    bat_map = {p: i for i, p in enumerate(batter_ids)}
    bowl_map = {p: i for i, p in enumerate(bowler_ids)}

    bi = df["striker_id"].map(bat_map)
    vb = bi.notna().values
    X_bat = sparse.csr_matrix(
        (np.ones(vb.sum()), (np.where(vb)[0], bi[vb].astype(int).values)),
        shape=(n, len(batter_ids)),
    )

    wi = df["bowler_id"].map(bowl_map)
    vw = wi.notna().values
    X_bowl = sparse.csr_matrix(
        (np.ones(vw.sum()), (np.where(vw)[0], wi[vw].astype(int).values)),
        shape=(n, len(bowler_ids)),
    )

    p_vec = df[pressure_col].values.astype(float)
    X_main = sparse.hstack([X_bat, X_bowl], format="csr")
    X_pressure = sparse.hstack([X_bat.multiply(p_vec[:, None]), X_bowl.multiply(p_vec[:, None])], format="csr")

    # Continuous features standardized strictly from training-fold stats
    u_raw = np.clip(df["balls_rem_before"].values / np.maximum(df["sched_balls"].values, 1.0), 0.0, 1.0)
    w_raw = df["wkts_rem_before"].values / 10.0
    elo_raw = df["elo_diff_bat_minus_bowl"].fillna(0.0).values

    if cont_stats is None:
        cont_stats = {
            "u": (float(np.mean(u_raw)), max(float(np.std(u_raw)), 1e-6)),
            "w": (float(np.mean(w_raw)), max(float(np.std(w_raw)), 1e-6)),
            "elo": (float(np.mean(elo_raw)), max(float(np.std(elo_raw)), 1e-6)),
        }

    u_std = (u_raw - cont_stats["u"][0]) / cont_stats["u"][1]
    w_std = (w_raw - cont_stats["w"][0]) / cont_stats["w"][1]
    elo_std = (elo_raw - cont_stats["elo"][0]) / cont_stats["elo"][1]

    inn2 = (df["innings"].values == 2).astype(float)
    is_t20i = (df["match_format"].values == "T20I").astype(float)
    ph_mid = (df["innings_phase"].values == "middle").astype(float)
    ph_death = (df["innings_phase"].values == "death").astype(float)
    non_bowl_wkt = (df["is_non_bowler_dismissal"] == True).astype(float).values

    ctx_cols = [p_vec, inn2, is_t20i, inn2 * is_t20i, ph_mid, ph_death, u_std, w_std, elo_std, non_bowl_wkt]
    s_arr = df["season"].astype(str).values
    for s in season_levels:
        ctx_cols.append((s_arr == s).astype(float))
    X_context = sparse.csr_matrix(np.column_stack(ctx_cols))

    return {
        "X_main": X_main,
        "X_pressure": X_pressure,
        "X_context": X_context,
        "y": df["delta_re_player_attrib"].values.astype(float),
        "batter_ids": batter_ids,
        "bowler_ids": bowler_ids,
        "season_levels": season_levels,
        "cont_stats": cont_stats,
        "n_bat": len(batter_ids),
        "n_bowl": len(bowler_ids),
    }


def solve_block_ridge(
    blocks: Dict[str, Any],
    alpha_main: float,
    alpha_int: float,
    alpha_context: float = 250.0,
    seed: int = 2026,
    tol: float = 1e-5,
) -> Dict[str, Any]:
    """
    Solve exact block-penalized Ridge:
      min ||y - X_m*theta - X_p*delta - X_c*gamma - b0||^2
          + alpha_main*||theta||^2 + alpha_int*||delta||^2 + alpha_context*||gamma||^2
    by scaling X_k -> X_k / sqrt(alpha_k) and fitting Ridge(alpha=1.0).
    """
    sm = 1.0 / np.sqrt(max(alpha_main, 1e-9))
    sp = 1.0 / np.sqrt(max(alpha_int, 1e-9))
    sc = 1.0 / np.sqrt(max(alpha_context, 1e-9))

    X_scaled = sparse.hstack(
        [blocks["X_main"] * sm, blocks["X_pressure"] * sp, blocks["X_context"] * sc],
        format="csr",
    )
    model = Ridge(alpha=1.0, fit_intercept=True, solver="lsqr", tol=tol, random_state=seed)
    model.fit(X_scaled, blocks["y"])

    n_bat = blocks["n_bat"]
    n_bowl = blocks["n_bowl"]
    n_main = n_bat + n_bowl

    c = model.coef_
    theta = c[:n_main] * sm
    delta = c[n_main : 2 * n_main] * sp
    gamma = c[2 * n_main :] * sc

    bat_main = (theta[:n_bat] - np.mean(theta[:n_bat])) * 100.0
    bowl_main = -(theta[n_bat:] - np.mean(theta[n_bat:])) * 100.0
    bat_pres = delta[:n_bat] * 100.0
    bowl_pres = -delta[n_bat:] * 100.0

    return {
        "intercept": float(model.intercept_),
        "theta": theta,
        "delta": delta,
        "gamma": gamma,
        "bat_main": bat_main,
        "bowl_main": bowl_main,
        "bat_pres": bat_pres,
        "bowl_pres": bowl_pres,
        "bat_hp": bat_main + bat_pres,
        "bowl_hp": bowl_main + bowl_pres,
    }


def predict_block_ridge(blocks: Dict[str, Any], fit: Dict[str, Any]) -> np.ndarray:
    """Predict target from unscaled block coefficients."""
    return (
        fit["intercept"]
        + blocks["X_main"] @ fit["theta"]
        + blocks["X_pressure"] @ fit["delta"]
        + blocks["X_context"] @ fit["gamma"]
    )


def tune_asymmetric_ridge_cv(
    df: pd.DataFrame,
    cfg: V50Config = DEFAULT_V50_CONFIG,
    pressure_col: str = "H_global_150",
) -> Tuple[float, float, pd.DataFrame]:
    """
    Tune (alpha_main, alpha_int) using 5-fold match-grouped CV with fold-isolated
    feature standardization, split-half pressure stability, and the 1-SE rule.
    """
    cfg.ensure_dirs()
    if "elo_diff_bat_minus_bowl" not in df.columns:
        df = compute_pre_match_elo(df, V43_CFG)
    batter_ids = np.sort(df["striker_id"].dropna().unique())
    bowler_ids = np.sort(df["bowler_id"].dropna().unique())
    season_levels = sorted(df["season"].astype(str).unique().tolist())[1:]

    # Identify eligible players post-fit for stability diagnostics
    bat_hp = df.groupby("striker_id")[pressure_col].sum()
    bat_tot = df.groupby("striker_id")["is_ball_faced"].sum()
    elig_bat = np.isin(batter_ids, bat_hp[(bat_hp >= 100) & (bat_tot >= 300)].index)

    bowl_hp = df.groupby("bowler_id")[pressure_col].sum()
    bowl_tot = df.groupby("bowler_id").size()
    elig_bowl = np.isin(bowler_ids, bowl_hp[(bowl_hp >= 100) & (bowl_tot >= 300)].index)

    gkf = GroupKFold(n_splits=cfg.n_cv_folds)
    fold_splits = list(gkf.split(df, groups=df["match_id"]))

    # Pre-build fold-isolated blocks so standardization never leaks validation matches
    fold_blocks = []
    for tr_idx, te_idx in fold_splits:
        b_tr = build_asymmetric_blocks(df.iloc[tr_idx], pressure_col, batter_ids, bowler_ids, season_levels, cont_stats=None)
        b_te = build_asymmetric_blocks(df.iloc[te_idx], pressure_col, batter_ids, bowler_ids, season_levels, cont_stats=b_tr["cont_stats"])
        fold_blocks.append((b_tr, b_te, te_idx))

    # 2 random match-level split-halves for stability check per (alpha_main, alpha_int)
    m_groups = df.groupby("match_id", sort=False).indices
    idx_lists = [m_groups[k] for k in m_groups]
    rng = np.random.default_rng(cfg.random_seed)
    perm = rng.permutation(len(idx_lists))
    half = len(idx_lists) // 2
    ia = np.concatenate([idx_lists[i] for i in perm[:half]])
    ib = np.concatenate([idx_lists[i] for i in perm[half:]])
    b_ha = build_asymmetric_blocks(df.iloc[ia], pressure_col, batter_ids, bowler_ids, season_levels)
    b_hb = build_asymmetric_blocks(df.iloc[ib], pressure_col, batter_ids, bowler_ids, season_levels)

    rows: List[Dict[str, Any]] = []
    for a_main in cfg.alpha_main_grid:
        for a_int in cfg.alpha_int_grid:
            fold_mses: List[float] = []
            oof_pred = np.zeros(len(df), dtype=float)
            for b_tr, b_te, te_idx in fold_blocks:
                fit = solve_block_ridge(b_tr, a_main, a_int, cfg.alpha_context, cfg.random_seed, tol=1e-4)
                p_te = predict_block_ridge(b_te, fit)
                oof_pred[te_idx] = p_te
                fold_mses.append(float(mean_squared_error(b_te["y"], p_te)))

            pooled_mse = float(mean_squared_error(df["delta_re_player_attrib"].values, oof_pred))
            fold_mse_mean = float(np.mean(fold_mses))
            fold_mse_se = float(np.std(fold_mses, ddof=1) / np.sqrt(len(fold_mses)))

            fa = solve_block_ridge(b_ha, a_main, a_int, cfg.alpha_context, cfg.random_seed, tol=1e-4)
            fb = solve_block_ridge(b_hb, a_main, a_int, cfg.alpha_context, cfg.random_seed, tol=1e-4)
            sp_bat = float(spearmanr(fa["bat_pres"][elig_bat], fb["bat_pres"][elig_bat])[0])
            sp_bowl = float(spearmanr(fa["bowl_pres"][elig_bowl], fb["bowl_pres"][elig_bowl])[0])

            rows.append(
                {
                    "alpha_main": a_main,
                    "alpha_int": a_int,
                    "alpha_context": cfg.alpha_context,
                    "pooled_oof_mse": round(pooled_mse, 6),
                    "oof_rmse": round(float(np.sqrt(pooled_mse)), 6),
                    "fold_mse_mean": round(fold_mse_mean, 6),
                    "fold_mse_se": round(fold_mse_se, 6),
                    "split_half_bat_pres_r": round(sp_bat, 4),
                    "split_half_bowl_pres_r": round(sp_bowl, 4),
                    "selected_1se": False,
                }
            )

    tune_df = pd.DataFrame(rows)
    # Apply 1-SE rule at primary alpha_main=250 (or global minimum): strongest alpha_int within min + 1*SE
    sub_250 = tune_df[tune_df["alpha_main"] == cfg.alpha_main_default]
    min_row = sub_250.loc[sub_250["fold_mse_mean"].idxmin()]
    thresh = float(min_row["fold_mse_mean"] + min_row["fold_mse_se"])
    cands = sub_250[sub_250["fold_mse_mean"] <= thresh]
    sel_idx = int(cands["alpha_int"].idxmax())
    tune_df.loc[sel_idx, "selected_1se"] = True
    sel_main = float(tune_df.loc[sel_idx, "alpha_main"])
    sel_int = float(tune_df.loc[sel_idx, "alpha_int"])
    tune_df.to_csv(cfg.output_dir / "V5_0_ALPHA_TUNING.csv", index=False)
    return sel_main, sel_int, tune_df
