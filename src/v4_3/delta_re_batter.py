"""Phase 5: Cross-Fitted Batter-Run Expected Value (ER_batter & DeltaRE_batter) for V4.3."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GroupKFold

from src.v4_3.config import DEFAULT_CONFIG, V43Config
from src.v4_3.expected_runs import apply_eb_par_to_deliveries, fit_er_model, predict_er


def _predict_er_after(df: pd.DataFrame, er_state: Dict[str, Any]) -> np.ndarray:
    """Predict ER(B_after, W_after) using exact post-delivery balls and wickets remaining."""
    after_df = df[
        ["match_id", "innings", "match_format", "season", "venue_id", "balls_rem_after", "wkts_rem_after"]
    ].rename(columns={"balls_rem_after": "balls_rem_before", "wkts_rem_after": "wkts_rem_before"})
    preds = predict_er(after_df, er_state)
    terminal = (df["balls_rem_after"].values <= 0) | (df["wkts_rem_after"].values <= 0)
    preds[terminal] = 0.0
    return preds


def _historical_rate_baseline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray]:
    """Simple historical-rate baseline: mean batter_runs per legal ball * balls_rem."""
    rates = (
        train_df.groupby(["innings", "match_format"])
        .apply(
            lambda g: float(g["batter_runs"].sum()) / max(float(g["legal_ball_inc"].sum()), 1.0),
            include_groups=False,
        )
        .to_dict()
    )
    global_rate = float(train_df["batter_runs"].sum()) / max(float(train_df["legal_ball_inc"].sum()), 1.0)
    r_arr = np.array(
        [rates.get((int(i), str(f)), global_rate) for i, f in zip(test_df["innings"], test_df["match_format"])],
        dtype=float,
    )
    er_before_base = r_arr * test_df["balls_rem_before"].values
    er_after_base = r_arr * test_df["balls_rem_after"].values
    terminal = (test_df["balls_rem_after"].values <= 0) | (test_df["wkts_rem_after"].values <= 0)
    er_after_base[terminal] = 0.0
    return er_before_base, er_after_base


def _boot_mae_rmse_ci(
    match_ids: np.ndarray,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_boot: int = 300,
    seed: int = 2026,
) -> Dict[str, Tuple[float, float]]:
    """Match-cluster bootstrap 95% CI for MAE and RMSE."""
    abs_err = np.abs(y_true - y_pred)
    sq_err = (y_true - y_pred) ** 2
    m_df = pd.DataFrame({"match_id": match_ids, "abs_err": abs_err, "sq_err": sq_err})
    m_grp = m_df.groupby("match_id", sort=False).mean()
    a_arr = m_grp["abs_err"].values
    s_arr = m_grp["sq_err"].values
    n_m = len(a_arr)
    rng = np.random.default_rng(seed)
    b_mae = np.empty(n_boot, dtype=float)
    b_rmse = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n_m, size=n_m)
        b_mae[b] = float(np.mean(a_arr[idx]))
        b_rmse[b] = float(np.sqrt(np.mean(s_arr[idx])))
    return {
        "mae_ci": (float(np.percentile(b_mae, 2.5)), float(np.percentile(b_mae, 97.5))),
        "rmse_ci": (float(np.percentile(b_rmse, 2.5)), float(np.percentile(b_rmse, 97.5))),
    }


def compute_phase5_delta_re_batter(
    reg_df: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
    n_boot: int = 300,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute strictly out-of-fold (5-fold match-grouped CV) and OOT ER_batter(B, W)
    and DeltaRE_batter = actual_batter_runs + ER_after_batter - ER_before_batter.
    Never uses a match's own deliveries to train its ER expectation.
    """
    cfg.ensure_dirs()
    df = reg_df.copy().reset_index(drop=True)

    # Exact post-delivery transitions (wides/oversteps do NOT consume legal balls)
    df["legal_balls_after"] = df["legal_balls_before"] + df["legal_ball_inc"]
    df["balls_rem_after"] = np.maximum(df["sched_balls"] - df["legal_balls_after"], 0.0)
    df["wkts_after"] = np.minimum(df["wkts_before"] + df["wicket_inc"], 10).astype(int)
    df["wkts_rem_after"] = (10 - df["wkts_after"]).astype(int)

    # Cross-fitted 5-fold match-grouped predictions
    gkf = GroupKFold(n_splits=cfg.n_cv_folds)
    er_before_oof = np.zeros(len(df), dtype=float)
    er_after_oof = np.zeros(len(df), dtype=float)
    base_before_oof = np.zeros(len(df), dtype=float)
    base_after_oof = np.zeros(len(df), dtype=float)
    eb_par_factor_oof = np.zeros(len(df), dtype=float)
    provenance = np.empty(len(df), dtype=object)

    for fold_idx, (tr_idx, te_idx) in enumerate(gkf.split(df, groups=df["match_id"]), start=1):
        tr_f = df.iloc[tr_idx]
        te_f = df.iloc[te_idx]
        er_state = fit_er_model(tr_f, cfg)
        te_eb = apply_eb_par_to_deliveries(te_f, er_state["eb_state"])

        er_before_oof[te_idx] = predict_er(te_f, er_state)
        er_after_oof[te_idx] = _predict_er_after(te_f, er_state)
        eb_par_factor_oof[te_idx] = te_eb["eb_venue_par_factor"].values

        b_bef, b_aft = _historical_rate_baseline(tr_f, te_f)
        base_before_oof[te_idx] = b_bef
        base_after_oof[te_idx] = b_aft
        provenance[te_idx] = f"5Fold_MatchGrouped_OOF_Fold_{fold_idx}"

    df["eb_venue_par_factor_oof"] = eb_par_factor_oof
    df["er_before_batter"] = er_before_oof
    df["er_after_batter"] = er_after_oof
    df["delta_re_batter"] = (
        df["batter_runs"].astype(float) + df["er_after_batter"] - df["er_before_batter"]
    )
    df["baseline_er_before"] = base_before_oof
    df["baseline_er_after"] = base_after_oof
    df["prediction_provenance"] = provenance
    df["data_quality_status"] = "BATTER_RUNS_ONLY_EXTRAS_UNQUANTIFIED"

    # Chronological OOT check (> 2024)
    tr_oot = df[df["year"] <= cfg.oot_cutoff_year]
    te_oot = df[df["year"] > cfg.oot_cutoff_year].copy()
    er_oot_state = fit_er_model(tr_oot, cfg)
    te_oot["er_before_oot"] = predict_er(te_oot, er_oot_state)
    te_oot["er_after_oot"] = _predict_er_after(te_oot, er_oot_state)
    te_oot["base_before_oot"], _ = _historical_rate_baseline(tr_oot, te_oot)

    # Validation summary comparing ER_batter(B, W) vs Historical-Rate Baseline
    val_rows: List[Dict[str, Any]] = []
    non_dl = ~df["is_dl"].fillna(False)
    for split_name, sub, pred_col, base_col in [
        ("MatchGrouped_5Fold_OOF", df[non_dl], "er_before_batter", "baseline_er_before"),
        (
            f"Chronological_OOT_gt_{cfg.oot_cutoff_year}",
            te_oot[~te_oot["is_dl"].fillna(False)],
            "er_before_oot",
            "base_before_oot",
        ),
    ]:
        y = sub["rem_batter_runs"].values
        for m_name, col in [("ER_batter_BW_EB_Par", pred_col), ("Historical_Rate_Baseline", base_col)]:
            p = sub[col].values
            res = y - p
            ci = _boot_mae_rmse_ci(sub["match_id"].values, y, p, n_boot=n_boot, seed=cfg.random_seed)
            val_rows.append(
                {
                    "evaluation_split": split_name,
                    "model_name": m_name,
                    "n_deliveries": int(len(sub)),
                    "n_matches": int(sub["match_id"].nunique()),
                    "mae": round(float(mean_absolute_error(y, p)), 4),
                    "mae_ci_low": round(ci["mae_ci"][0], 4),
                    "mae_ci_high": round(ci["mae_ci"][1], 4),
                    "rmse": round(float(root_mean_squared_error(y, p)), 4),
                    "rmse_ci_low": round(ci["rmse_ci"][0], 4),
                    "rmse_ci_high": round(ci["rmse_ci"][1], 4),
                    "residual_mean": round(float(np.mean(res)), 4),
                    "residual_std": round(float(np.std(res)), 4),
                    "residual_p05": round(float(np.percentile(res, 5)), 4),
                    "residual_p50": round(float(np.percentile(res, 50)), 4),
                    "residual_p95": round(float(np.percentile(res, 95)), 4),
                    "governance_status": "CONDITIONAL_GO_BATTER_RUNS_ONLY",
                }
            )

    val_df = pd.DataFrame(val_rows)
    val_df.to_csv(cfg.output_dir / "V4_3_PHASE5_ER_VALIDATION.csv", index=False)

    # Delivery-value audit summary by extras_category & wicket status
    audit_df = (
        df.groupby(["extras_category", "wicket_inc"], as_index=False)
        .agg(
            n_deliveries=("delta_re_batter", "size"),
            mean_batter_runs=("batter_runs", "mean"),
            mean_legal_ball_inc=("legal_ball_inc", "mean"),
            mean_er_before=("er_before_batter", "mean"),
            mean_er_after=("er_after_batter", "mean"),
            mean_delta_re_batter=("delta_re_batter", "mean"),
            std_delta_re_batter=("delta_re_batter", "std"),
        )
        .sort_values(["extras_category", "wicket_inc"])
    )
    audit_df["data_quality_status"] = "BATTER_RUNS_ONLY_EXTRAS_UNQUANTIFIED"
    audit_df.to_csv(cfg.output_dir / "V4_3_PHASE5_DELIVERY_VALUE_AUDIT.csv", index=False)

    # Save delivery-level parquet with all required fields
    export_cols = [
        "match_id",
        "innings",
        "overid",
        "over_ball_num",
        "innings_ball_num",
        "match_date",
        "match_format",
        "season",
        "venue_id",
        "batting_team_id",
        "bowling_team_id",
        "striker_id",
        "striker_name",
        "bowler_id",
        "bowler_name",
        "innings_phase",
        "extras_category",
        "is_wicket",
        "is_bowler_wicket",
        "is_non_bowler_dismissal",
        "dismissal_type",
        "dismissed_player_id",
        "legal_balls_before",
        "balls_rem_before",
        "wkts_before",
        "wkts_rem_before",
        "legal_balls_after",
        "balls_rem_after",
        "wkts_after",
        "wkts_rem_after",
        "batter_runs",
        "legal_ball_inc",
        "wicket_inc",
        "eb_venue_par_factor_oof",
        "er_before_batter",
        "er_after_batter",
        "delta_re_batter",
        "prediction_provenance",
        "data_quality_status",
    ]
    df[export_cols].to_parquet(cfg.output_dir / "V4_3_DELIVERY_VALUE_BATTER.parquet", index=False)
    return df, val_df, audit_df
