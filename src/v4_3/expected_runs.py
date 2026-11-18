"""Phase 2: Hierarchical Empirical-Bayes Venue/Format/Season Par & Resource ER(B, W) Model."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import optimize
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GroupKFold

from src.v4_3.config import DEFAULT_CONFIG, V43Config


def _eb_shrink_group(
    group_df: pd.DataFrame,
    prior_col: str,
    val_col: str,
    default_prior_weight: float = 10.0,
) -> pd.DataFrame:
    """Empirical-Bayes shrinkage of group means toward a hierarchical prior."""
    out = group_df.copy()
    n = out["n"].values.astype(float)
    raw_mean = out["raw_mean"].values.astype(float)
    prior = out[prior_col].values.astype(float)

    # Estimate within-group variance sigma^2 (pooled across groups with n >= 2)
    valid_var = out.loc[out["n"] >= 2, "raw_var"].dropna()
    sigma2 = float(valid_var.mean()) if len(valid_var) > 0 else 400.0
    sigma2 = max(sigma2, 1.0)

    # Estimate between-group variance tau^2 via DerSimonian-Laird-style moment estimator
    if len(out) >= 3:
        w = n / sigma2
        diff2 = (raw_mean - prior) ** 2
        q_stat = float(np.sum(w * diff2))
        df_q = max(len(out) - 1, 1)
        c_denom = float(np.sum(w) - np.sum(w ** 2) / max(np.sum(w), 1e-9))
        tau2 = max((q_stat - df_q) / max(c_denom, 1e-9), 0.0)
    else:
        tau2 = sigma2 / default_prior_weight

    if tau2 < 1e-6:
        # Fallback mild shrinkage when between-group variance is near zero
        k = default_prior_weight
        shrink_w = n / (n + k)
    else:
        shrink_w = (n * tau2) / (n * tau2 + sigma2)

    out["eb_weight"] = shrink_w
    out["eb_mean"] = shrink_w * raw_mean + (1.0 - shrink_w) * prior
    out["sigma2"] = sigma2
    out["tau2"] = tau2
    return out


def fit_eb_par_model(reg_df: pd.DataFrame, cfg: V43Config = DEFAULT_CONFIG) -> Dict[str, Any]:
    """
    Fit Hierarchical Empirical-Bayes par model on batter_runs_total
    (explicitly scoped to batter runs because extras are unquantified).
    Hierarchy: Global -> Format -> Format x Season -> Format x Venue.
    """
    # Use completed/representative innings (non-DLS, innings 1 or full/chased innings 2 scaled or inn1 baseline)
    # Specifically, use innings 1 non-DLS innings with >= 90 legal balls or all 10 wickets for clean par estimation
    inn_df = (
        reg_df.groupby(["match_id", "innings", "match_format", "season", "venue_id", "is_dl"], as_index=False)
        .agg(
            batter_runs_total=("batter_runs", "sum"),
            legal_balls=("is_legal_ball", "sum"),
            wickets=("wicket_inc", "sum"),
            sched_balls=("sched_balls", "first"),
        )
    )
    clean = inn_df[
        (~inn_df["is_dl"].fillna(False))
        & (inn_df["innings"] == 1)
        & ((inn_df["legal_balls"] >= 90) | (inn_df["wickets"] == 10))
    ].copy()
    if len(clean) < 20:
        clean = inn_df[inn_df["innings"] == 1].copy()
    if len(clean) == 0:
        clean = inn_df.copy()

    global_mean = float(clean["batter_runs_total"].mean())

    # Level 1: Format
    fmt_grp = clean.groupby("match_format", as_index=False).agg(
        n=("batter_runs_total", "size"),
        raw_mean=("batter_runs_total", "mean"),
        raw_var=("batter_runs_total", "var"),
    )
    fmt_grp["prior"] = global_mean
    fmt_eb = _eb_shrink_group(fmt_grp, "prior", "raw_mean", cfg.eb_default_prior_weight)
    fmt_map = dict(zip(fmt_eb["match_format"], fmt_eb["eb_mean"]))

    # Level 2: Format x Season
    fs_grp = clean.groupby(["match_format", "season"], as_index=False).agg(
        n=("batter_runs_total", "size"),
        raw_mean=("batter_runs_total", "mean"),
        raw_var=("batter_runs_total", "var"),
    )
    fs_grp["prior"] = fs_grp["match_format"].map(fmt_map).fillna(global_mean)
    fs_eb = _eb_shrink_group(fs_grp, "prior", "raw_mean", cfg.eb_default_prior_weight)
    fs_map = {
        (r["match_format"], str(r["season"])): float(r["eb_mean"])
        for _, r in fs_eb.iterrows()
    }

    # Level 3: Format x Venue
    fv_grp = clean.groupby(["match_format", "venue_id"], as_index=False).agg(
        n=("batter_runs_total", "size"),
        raw_mean=("batter_runs_total", "mean"),
        raw_var=("batter_runs_total", "var"),
    )
    fv_grp["prior"] = fv_grp["match_format"].map(fmt_map).fillna(global_mean)
    fv_eb = _eb_shrink_group(fv_grp, "prior", "raw_mean", cfg.eb_default_prior_weight)
    fv_map = {
        (r["match_format"], int(r["venue_id"])): float(r["eb_mean"])
        for _, r in fv_eb.iterrows()
        if pd.notna(r["venue_id"])
    }

    return {
        "global_mean": global_mean,
        "format_table": fmt_eb,
        "format_season_table": fs_eb,
        "format_venue_table": fv_eb,
        "fmt_map": fmt_map,
        "fs_map": fs_map,
        "fv_map": fv_map,
    }


def apply_eb_par_to_deliveries(df: pd.DataFrame, eb_state: Dict[str, Any]) -> pd.DataFrame:
    """Attach strictly pre-match EB par expectation and multiplier to deliveries."""
    out = df.copy()
    g_mean = eb_state["global_mean"]
    fmt_map = eb_state["fmt_map"]
    fs_map = eb_state["fs_map"]
    fv_map = eb_state["fv_map"]

    fmt_vals = out["match_format"].map(fmt_map).fillna(g_mean).values
    fv_vals = np.array(
        [
            fv_map.get((f, int(v)), fmt_map.get(f, g_mean)) if pd.notna(v) else fmt_map.get(f, g_mean)
            for f, v in zip(out["match_format"], out["venue_id"])
        ],
        dtype=float,
    )
    fs_vals = np.array(
        [
            fs_map.get((f, str(s)), fmt_map.get(f, g_mean))
            for f, s in zip(out["match_format"], out["season"])
        ],
        dtype=float,
    )
    # Combined EB par: venue-format estimate blended with season-format adjustment
    out["eb_format_par_bat_runs"] = fmt_vals
    out["eb_venue_par_bat_runs"] = fv_vals + 0.5 * (fs_vals - fmt_vals)
    out["eb_venue_par_factor"] = np.clip(out["eb_venue_par_bat_runs"] / max(g_mean, 1.0), 0.65, 1.45)
    return out


def _resource_curve(u: np.ndarray, w_rem: np.ndarray, r0: float, b: float, gamma: float) -> np.ndarray:
    """Resource-based expected remaining batter runs ER(B, W)."""
    u_cl = np.clip(u, 0.0, 1.2)
    wf = np.clip(w_rem / 10.0, 0.0, 1.0)
    b_safe = max(float(b), 1e-4)
    denom = max(1.0 - float(np.exp(-b_safe)), 1e-6)
    return r0 * ((1.0 - np.exp(-b_safe * u_cl)) / denom) * np.power(wf, gamma)


def fit_er_model(
    train_df: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Fit EB par + resource-based ER(B, W) model per (innings, match_format) on training data."""
    eb_state = fit_eb_par_model(train_df, cfg)
    tr = apply_eb_par_to_deliveries(train_df, eb_state)

    # Fit on non-DLS deliveries where remaining batter runs is well-defined
    clean = tr[~tr["is_dl"].fillna(False)].copy()
    curve_params: Dict[Tuple[int, str], Tuple[float, float, float]] = {}

    formats = sorted(clean["match_format"].dropna().unique().tolist())
    innings_list = sorted(clean["innings"].dropna().unique().astype(int).tolist())
    for inn in innings_list:
        for fmt in formats:
            sub = clean[(clean["innings"] == inn) & (clean["match_format"] == fmt)]
            if len(sub) < 100:
                sub = clean[clean["innings"] == inn]
            if len(sub) == 0:
                continue
            u = np.clip(sub["balls_rem_before"].values / float(cfg.standard_t20_balls), 0.0, 1.2)
            w_rem = sub["wkts_rem_before"].values.astype(float)
            # Normalize target by venue par factor so curve represents standard venue resource
            y_norm = sub["rem_batter_runs"].values.astype(float) / sub["eb_venue_par_factor"].values

            def _res(params: np.ndarray) -> np.ndarray:
                return _resource_curve(u, w_rem, params[0], params[1], params[2]) - y_norm

            res = optimize.least_squares(
                _res,
                x0=np.array([160.0, 0.8, 0.45]),
                bounds=([40.0, 0.05, 0.05], [400.0, 5.0, 2.5]),
                max_nfev=300,
            )
            curve_params[(inn, fmt)] = (float(res.x[0]), float(res.x[1]), float(res.x[2]))

    return {
        "eb_state": eb_state,
        "curve_params": curve_params,
        "standard_t20_balls": cfg.standard_t20_balls,
    }


def predict_er(df: pd.DataFrame, er_state: Dict[str, Any]) -> np.ndarray:
    """Predict expected remaining batter runs ER(B, W) * eb_venue_par_factor."""
    with_eb = apply_eb_par_to_deliveries(df, er_state["eb_state"])
    preds = np.zeros(len(with_eb), dtype=float)
    u_all = np.clip(with_eb["balls_rem_before"].values / float(er_state["standard_t20_balls"]), 0.0, 1.2)
    w_all = with_eb["wkts_rem_before"].values.astype(float)
    inn_all = with_eb["innings"].values.astype(int)
    fmt_all = with_eb["match_format"].values
    fac_all = with_eb["eb_venue_par_factor"].values.astype(float)

    for (inn, fmt), (r0, b, gamma) in er_state["curve_params"].items():
        mask = (inn_all == inn) & (fmt_all == fmt)
        if np.any(mask):
            preds[mask] = _resource_curve(u_all[mask], w_all[mask], r0, b, gamma) * fac_all[mask]

    return np.maximum(preds, 0.0)


def evaluate_phase2_expected_runs(
    reg_df: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Evaluate EB venue par and ER(B, W) under 5-fold match-grouped CV and chronological OOT.
    Saves V4_3_VENUE_PAR_EB.csv, V4_3_EXPECTED_RUNS_METRICS.csv, V4_3_EXPECTED_RUNS_BY_SUBGROUP.csv.
    """
    cfg.ensure_dirs()
    clean = reg_df[~reg_df["is_dl"].fillna(False)].copy().reset_index(drop=True)

    # 1. 5-fold Match-Grouped CV
    gkf = GroupKFold(n_splits=cfg.n_cv_folds)
    oof_preds = np.zeros(len(clean), dtype=float)
    for tr_idx, te_idx in gkf.split(clean, groups=clean["match_id"]):
        tr_fold = clean.iloc[tr_idx]
        te_fold = clean.iloc[te_idx]
        er_state = fit_er_model(tr_fold, cfg)
        oof_preds[te_idx] = predict_er(te_fold, er_state)

    clean["er_oof_pred"] = oof_preds
    clean["er_oof_residual"] = clean["rem_batter_runs"] - clean["er_oof_pred"]

    # 2. Chronological OOT split
    tr_oot = clean[clean["year"] <= cfg.oot_cutoff_year]
    te_oot = clean[clean["year"] > cfg.oot_cutoff_year].copy()
    er_oot_state = fit_er_model(tr_oot, cfg)
    te_oot["er_oot_pred"] = predict_er(te_oot, er_oot_state)
    te_oot["er_oot_residual"] = te_oot["rem_batter_runs"] - te_oot["er_oot_pred"]

    # 3. Full-data fit for reporting EB venue par & curve parameters
    full_er_state = fit_er_model(clean, cfg)
    fv_table = full_er_state["eb_state"]["format_venue_table"].sort_values(["match_format", "n"], ascending=[True, False])
    fv_table.to_csv(cfg.output_dir / "V4_3_VENUE_PAR_EB.csv", index=False)

    metrics_rows: List[Dict[str, Any]] = []
    for eval_name, df_eval, pred_col in [
        ("MatchGrouped_5Fold_CV", clean, "er_oof_pred"),
        (f"Chronological_OOT_gt_{cfg.oot_cutoff_year}", te_oot, "er_oot_pred"),
    ]:
        y = df_eval["rem_batter_runs"].values
        p = df_eval[pred_col].values
        metrics_rows.append(
            {
                "evaluation_split": eval_name,
                "subgroup": "ALL_REGULAR_NON_DLS",
                "n_deliveries": int(len(df_eval)),
                "n_matches": int(df_eval["match_id"].nunique()),
                "mae": round(float(mean_absolute_error(y, p)), 4),
                "rmse": round(float(root_mean_squared_error(y, p)), 4),
                "mean_residual": round(float(np.mean(y - p)), 4),
                "target_definition": "rem_batter_runs (extras unquantified)",
            }
        )

    # Subgroup breakdown on OOF CV
    sub_rows: List[Dict[str, Any]] = []
    for grp_cols, grp_label in [
        (["innings"], "by_innings"),
        (["match_format"], "by_format"),
        (["innings", "match_format"], "by_innings_format"),
    ]:
        for keys, grp in clean.groupby(grp_cols):
            y = grp["rem_batter_runs"].values
            p = grp["er_oof_pred"].values
            sub_rows.append(
                {
                    "grouping": grp_label,
                    "subgroup": str(keys),
                    "n_deliveries": int(len(grp)),
                    "n_matches": int(grp["match_id"].nunique()),
                    "mae": round(float(mean_absolute_error(y, p)), 4),
                    "rmse": round(float(root_mean_squared_error(y, p)), 4),
                    "mean_residual": round(float(np.mean(y - p)), 4),
                }
            )

    metrics_df = pd.DataFrame(metrics_rows)
    sub_df = pd.DataFrame(sub_rows)
    metrics_df.to_csv(cfg.output_dir / "V4_3_EXPECTED_RUNS_METRICS.csv", index=False)
    sub_df.to_csv(cfg.output_dir / "V4_3_EXPECTED_RUNS_BY_SUBGROUP.csv", index=False)

    summary = {
        "global_inn1_bat_runs_par": round(full_er_state["eb_state"]["global_mean"], 3),
        "curve_params": {f"inn{k[0]}_{k[1]}": [round(x, 4) for x in v] for k, v in full_er_state["curve_params"].items()},
        "cv_mae": float(metrics_df.loc[0, "mae"]),
        "cv_rmse": float(metrics_df.loc[0, "rmse"]),
        "oot_mae": float(metrics_df.loc[1, "mae"]),
        "oot_rmse": float(metrics_df.loc[1, "rmse"]),
    }
    (cfg.artifacts_dir / "phase2_expected_runs_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return metrics_df, sub_df, full_er_state
