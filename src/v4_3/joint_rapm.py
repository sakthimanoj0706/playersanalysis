"""Phase 6: Experimental Joint Batter-Bowler Ridge RAPM on DeltaRE_batter for V4.3."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GroupKFold

from src.v4_3.config import DEFAULT_CONFIG, V43Config
from src.v4_3.win_probability import compute_pre_match_elo

ALPHA_GRID: Tuple[float, ...] = (25.0, 50.0, 100.0, 150.0, 250.0, 400.0, 600.0, 1000.0, 1500.0, 2500.0)


def build_joint_rapm_design(
    df: pd.DataFrame,
    batter_ids: np.ndarray | None = None,
    bowler_ids: np.ndarray | None = None,
    season_levels: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Build sparse joint batter-bowler + context design matrix for DeltaRE_batter.
    Includes explicit separation indicators for non-bowler dismissals and unresolved wickets
    so bowlers are never automatically credited for run-outs or non-bowler dismissals.
    """
    n = len(df)
    if batter_ids is None:
        batter_ids = np.sort(df["striker_id"].dropna().unique())
    if bowler_ids is None:
        bowler_ids = np.sort(df["bowler_id"].dropna().unique())
    if season_levels is None:
        seasons_all = sorted(df["season"].astype(str).unique().tolist())
        season_levels = seasons_all[1:]  # reference = earliest season

    bat_map = {pid: i for i, pid in enumerate(batter_ids)}
    bowl_map = {pid: i for i, pid in enumerate(bowler_ids)}

    # Batter sparse one-hot
    bat_idx = df["striker_id"].map(bat_map)
    valid_bat = bat_idx.notna().values
    X_bat = sparse.csr_matrix(
        (np.ones(valid_bat.sum(), dtype=float), (np.where(valid_bat)[0], bat_idx[valid_bat].astype(int).values)),
        shape=(n, len(batter_ids)),
    )

    # Bowler sparse one-hot
    bowl_idx = df["bowler_id"].map(bowl_map)
    valid_bowl = bowl_idx.notna().values
    X_bowl = sparse.csr_matrix(
        (np.ones(valid_bowl.sum(), dtype=float), (np.where(valid_bowl)[0], bowl_idx[valid_bowl].astype(int).values)),
        shape=(n, len(bowler_ids)),
    )

    # Context & dismissal-separation controls (reference coded)
    inn2 = (df["innings"].values == 2).astype(float)
    is_t20i = (df["match_format"].values == "T20I").astype(float)
    ph_mid = (df["innings_phase"].values == "middle").astype(float)
    ph_death = (df["innings_phase"].values == "death").astype(float)
    u = np.clip(df["balls_rem_before"].values / np.maximum(df["sched_balls"].values, 1.0), 0.0, 1.0)
    w_rem = df["wkts_rem_before"].values / 10.0
    par_fac = df["eb_venue_par_factor_oof"].fillna(1.0).values
    elo_diff = df["elo_diff_bat_minus_bowl"].fillna(0.0).values
    non_bowl_wkt = (df["is_non_bowler_dismissal"] == True).astype(float).values
    unres_wkt = ((df["is_wicket"] == True) & df["dismissed_player_id"].isna()).astype(float).values

    ctrl_cols = [
        inn2,
        is_t20i,
        inn2 * is_t20i,
        ph_mid,
        ph_death,
        u,
        w_rem,
        par_fac,
        elo_diff,
        non_bowl_wkt,
        unres_wkt,
    ]
    ctrl_names = [
        "inn2",
        "is_t20i",
        "inn2_x_t20i",
        "phase_middle",
        "phase_death",
        "balls_rem_frac",
        "wkts_rem_frac",
        "eb_venue_par_factor_oof",
        "elo_diff_bat_minus_bowl",
        "is_non_bowler_dismissal_sep",
        "is_unresolved_wicket_sep",
    ]
    s_col = df["season"].astype(str).values
    for s in season_levels:
        ctrl_cols.append((s_col == s).astype(float))
        ctrl_names.append(f"season_{s}")

    X_ctrl = sparse.csr_matrix(np.column_stack(ctrl_cols))
    X = sparse.hstack([X_bat, X_bowl, X_ctrl], format="csr")

    return {
        "X": X,
        "y": df["delta_re_batter"].values.astype(float),
        "batter_ids": batter_ids,
        "bowler_ids": bowler_ids,
        "season_levels": season_levels,
        "ctrl_names": ctrl_names,
        "n_bat": len(batter_ids),
        "n_bowl": len(bowler_ids),
    }


def fit_ridge_rapm(
    design: Dict[str, Any],
    alpha: float,
    seed: int = 2026,
) -> Dict[str, Any]:
    """Fit sparse Ridge RAPM on pre-built design matrix."""
    model = Ridge(alpha=alpha, fit_intercept=True, solver="lsqr", tol=1e-5, random_state=seed)
    model.fit(design["X"], design["y"])
    coef = model.coef_
    n_bat = design["n_bat"]
    n_bowl = design["n_bowl"]

    bat_raw = coef[:n_bat]
    bowl_raw = coef[n_bat : n_bat + n_bowl]
    ctrl_coef = coef[n_bat + n_bowl :]

    # Mean-center player effects for explicit identifiability; scale to per-100 deliveries
    bat_centered = (bat_raw - float(np.mean(bat_raw))) * 100.0
    bowl_centered_raw = (bowl_raw - float(np.mean(bowl_raw))) * 100.0
    # Convert bowler effect to intuitive "higher is better" defensive batter-run prevention score
    bowl_defensive_score = -bowl_centered_raw

    return {
        "model": model,
        "intercept": float(model.intercept_),
        "bat_raw": bat_raw,
        "bowl_raw": bowl_raw,
        "bat_effect_per100": bat_centered,
        "bowl_coef_per100": bowl_centered_raw,
        "bowl_defensive_per100": bowl_defensive_score,
        "ctrl_coef": ctrl_coef,
    }


def tune_rapm_alpha_cv(
    df: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
    alpha_grid: Tuple[float, ...] = ALPHA_GRID,
) -> Tuple[float, pd.DataFrame]:
    """Tune Ridge alpha using 5-fold grouped-by-match cross-validation."""
    gkf = GroupKFold(n_splits=cfg.n_cv_folds)
    batter_ids = np.sort(df["striker_id"].dropna().unique())
    bowler_ids = np.sort(df["bowler_id"].dropna().unique())
    seasons_all = sorted(df["season"].astype(str).unique().tolist())
    season_levels = seasons_all[1:]

    design_full = build_joint_rapm_design(df, batter_ids, bowler_ids, season_levels)
    X = design_full["X"]
    y = design_full["y"]
    groups = df["match_id"].values

    rows: List[Dict[str, Any]] = []
    for alpha in alpha_grid:
        oof_pred = np.zeros(len(df), dtype=float)
        for tr_idx, te_idx in gkf.split(X, y, groups=groups):
            m = Ridge(alpha=alpha, fit_intercept=True, solver="lsqr", tol=1e-5, random_state=cfg.random_seed)
            m.fit(X[tr_idx], y[tr_idx])
            oof_pred[te_idx] = m.predict(X[te_idx])
        rmse = float(root_mean_squared_error(y, oof_pred))
        mae = float(mean_absolute_error(y, oof_pred))
        mse = rmse ** 2
        rows.append(
            {
                "alpha": float(alpha),
                "cv_mse": round(mse, 6),
                "cv_rmse": round(rmse, 6),
                "cv_mae": round(mae, 6),
                "is_optimal": False,
            }
        )

    tune_df = pd.DataFrame(rows)
    best_idx = int(tune_df["cv_mse"].idxmin())
    tune_df.loc[best_idx, "is_optimal"] = True
    best_alpha = float(tune_df.loc[best_idx, "alpha"])
    tune_df.to_csv(cfg.output_dir / "V4_3_RAPM_ALPHA_TUNING.csv", index=False)
    return best_alpha, tune_df


def run_phase6_joint_rapm(
    df_p5: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Fit tuned experimental joint batter-bowler Ridge RAPM on all regular deliveries."""
    cfg.ensure_dirs()
    df = compute_pre_match_elo(df_p5, cfg)
    best_alpha, tune_df = tune_rapm_alpha_cv(df, cfg)

    design = build_joint_rapm_design(df)
    fit = fit_ridge_rapm(design, alpha=best_alpha, seed=cfg.random_seed)

    # Batter stats & outputs
    bat_names = df.groupby("striker_id")["striker_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()
    bat_exp = (
        df.groupby("striker_id", as_index=False)
        .agg(
            deliveries_faced=("is_ball_faced", "sum"),
            legal_balls_faced=("legal_ball_inc", "sum"),
            total_rows=("delta_re_batter", "size"),
            matches=("match_id", "nunique"),
            innings=("innings", "size"),
            raw_batter_runs=("batter_runs", "sum"),
            raw_mean_delta_re=("delta_re_batter", "mean"),
        )
        .rename(columns={"striker_id": "player_id"})
    )
    bat_effects = pd.DataFrame(
        {
            "player_id": design["batter_ids"],
            "rapm_batter_per100": fit["bat_effect_per100"],
        }
    )
    bat_df = bat_effects.merge(bat_exp, on="player_id", how="left")
    bat_df["player_name"] = bat_df["player_id"].map(bat_names)
    bat_df["role"] = "batter"
    bat_df["target_scope"] = "DeltaRE_batter (batter runs only; extras unquantified)"
    bat_df["governance_status"] = "EXPERIMENTAL_NO_PRESSURE_INTERACTION"

    # Bowler stats & outputs (explicitly excluding non-bowler dismissals from bowler wicket count)
    bowl_names = df.groupby("bowler_id")["bowler_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()
    bowl_exp = (
        df.groupby("bowler_id", as_index=False)
        .agg(
            deliveries_bowled=("delta_re_batter", "size"),
            legal_balls_bowled=("legal_ball_inc", "sum"),
            matches=("match_id", "nunique"),
            bowler_credited_wickets=("is_bowler_wicket", "sum"),
            non_bowler_dismissals_on_bowler=("is_non_bowler_dismissal", "sum"),
            raw_batter_runs_conceded=("batter_runs", "sum"),
            raw_mean_delta_re=("delta_re_batter", "mean"),
        )
        .rename(columns={"bowler_id": "player_id"})
    )
    bowl_effects = pd.DataFrame(
        {
            "player_id": design["bowler_ids"],
            "rapm_bowler_raw_coef_per100": fit["bowl_coef_per100"],
            "rapm_bowler_defensive_per100": fit["bowl_defensive_per100"],
        }
    )
    bowl_df = bowl_effects.merge(bowl_exp, on="player_id", how="left")
    bowl_df["player_name"] = bowl_df["player_id"].map(bowl_names)
    bowl_df["role"] = "bowler"
    bowl_df["target_scope"] = "DeltaRE_batter (batter-run prevention only; excludes wides/byes/legbyes)"
    bowl_df["governance_status"] = "EXPERIMENTAL_NO_PRESSURE_INTERACTION"

    bat_df = bat_df.sort_values("rapm_batter_per100", ascending=False).reset_index(drop=True)
    bowl_df = bowl_df.sort_values("rapm_bowler_defensive_per100", ascending=False).reset_index(drop=True)

    bat_df.to_csv(cfg.output_dir / "V4_3_BATTER_RAPM.csv", index=False)
    bowl_df.to_csv(cfg.output_dir / "V4_3_BOWLER_RAPM.csv", index=False)

    meta = {
        "best_alpha": best_alpha,
        "n_deliveries": int(len(df)),
        "n_batters": int(design["n_bat"]),
        "n_bowlers": int(design["n_bowl"]),
        "intercept": fit["intercept"],
        "non_bowler_dismissal_sep_coef": float(fit["ctrl_coef"][design["ctrl_names"].index("is_non_bowler_dismissal_sep")]),
        "unresolved_wicket_sep_coef": float(fit["ctrl_coef"][design["ctrl_names"].index("is_unresolved_wicket_sep")]),
        "design_bundle": design,
        "df_with_elo": df,
    }
    (cfg.artifacts_dir / "phase6_rapm_summary.json").write_text(
        json.dumps({k: v for k, v in meta.items() if k not in ("design_bundle", "df_with_elo")}, indent=2),
        encoding="utf-8",
    )
    return bat_df, bowl_df, tune_df, meta
