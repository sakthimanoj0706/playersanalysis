"""Phase 3.5: Evaluation Audit for Observable-State WP vs Elo-Only Baseline."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from src.v4_3.config import DEFAULT_CONFIG, V43Config
from src.v4_3.expected_runs import apply_eb_par_to_deliveries, fit_er_model
from src.v4_3.win_probability import (
    _calibration_curve_bins,
    _calibration_intercept_slope,
    compute_pre_match_elo,
)


def _equal_match_weighted_loss(
    match_ids: np.ndarray,
    y_true: np.ndarray,
    probs: np.ndarray,
) -> Tuple[float, float]:
    """Compute equal-match-weighted Brier score and log loss."""
    p_cl = np.clip(probs, 1e-6, 1.0 - 1e-6)
    brier_i = (y_true - p_cl) ** 2
    ll_i = -(y_true * np.log(p_cl) + (1.0 - y_true) * np.log(1.0 - p_cl))
    tmp = pd.DataFrame({"match_id": match_ids, "brier": brier_i, "ll": ll_i})
    per_m = tmp.groupby("match_id", sort=False).mean()
    return float(per_m["brier"].mean()), float(per_m["ll"].mean())


def _match_cluster_bootstrap_metrics(
    match_ids: np.ndarray,
    y_true: np.ndarray,
    probs: np.ndarray,
    n_boot: int = 300,
    seed: int = 2026,
) -> Dict[str, Tuple[float, float]]:
    """Compute match-cluster bootstrap 95% CIs for equal-match-weighted Brier, LogLoss, and AUC."""
    p_cl = np.clip(probs, 1e-6, 1.0 - 1e-6)
    brier_i = (y_true - p_cl) ** 2
    ll_i = -(y_true * np.log(p_cl) + (1.0 - y_true) * np.log(1.0 - p_cl))

    df_m = pd.DataFrame(
        {"match_id": match_ids, "y": y_true, "p": p_cl, "brier": brier_i, "ll": ll_i}
    )
    m_stats = df_m.groupby("match_id", sort=False).agg(
        y_m=("y", "first"),
        brier_m=("brier", "mean"),
        ll_m=("ll", "mean"),
        p_m=("p", "mean"),
    )
    uniq_m = m_stats.index.to_numpy()
    n_m = len(uniq_m)
    b_arr = m_stats["brier_m"].values
    l_arr = m_stats["ll_m"].values
    y_arr = m_stats["y_m"].values
    p_arr = m_stats["p_m"].values

    rng = np.random.default_rng(seed)
    boot_b = np.empty(n_boot, dtype=float)
    boot_l = np.empty(n_boot, dtype=float)
    boot_auc = np.empty(n_boot, dtype=float)

    for b in range(n_boot):
        idx = rng.integers(0, n_m, size=n_m)
        boot_b[b] = float(np.mean(b_arr[idx]))
        boot_l[b] = float(np.mean(l_arr[idx]))
        yb = y_arr[idx]
        if len(np.unique(yb)) == 2:
            boot_auc[b] = float(roc_auc_score(yb, p_arr[idx]))
        else:
            boot_auc[b] = np.nan

    return {
        "brier_eq_ci": (float(np.nanpercentile(boot_b, 2.5)), float(np.nanpercentile(boot_b, 97.5))),
        "logloss_eq_ci": (float(np.nanpercentile(boot_l, 2.5)), float(np.nanpercentile(boot_l, 97.5))),
        "auc_match_mean_ci": (
            float(np.nanpercentile(boot_auc, 2.5)),
            float(np.nanpercentile(boot_auc, 97.5)),
        ),
    }


def _build_obs_features(df: pd.DataFrame, model_type: str) -> np.ndarray:
    """Strictly pre-delivery observable features."""
    elo = df["elo_diff_bat_minus_bowl"].fillna(0.0).values
    if model_type == "ELO_ONLY_BASELINE":
        return elo.reshape(-1, 1)
    u = np.clip(df["balls_rem_before"].values / np.maximum(df["sched_balls"].values, 1.0), 0.0, 1.0)
    w_rem = df["wkts_rem_before"].values / 10.0
    is_t20i = (df["match_format"].values == "T20I").astype(float)
    par_factor = df["eb_venue_par_factor"].fillna(1.0).values
    return np.column_stack([u, w_rem, u * w_rem, is_t20i, elo, par_factor])


def run_phase3_5_evaluation_audit(
    reg_df: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
    n_boot: int = 300,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Audit Observable-State WP vs Elo-Only Baseline using:
    - Equal-match-weighted Brier & LogLoss + match-cluster bootstrap CIs
    - Delivery-weighted metrics for comparison
    - End-of-over checkpoint evaluation & calibration (overs 3, 6, 10, 15, 18, 20)
    - Match-grouped 5-fold CV & Chronological OOT (> 2024)
    """
    cfg.ensure_dirs()
    df = compute_pre_match_elo(reg_df, cfg)
    valid = df[df["inn1_team_won"].notna() & (~df["is_dl"].fillna(False))].copy().reset_index(drop=True)

    # Identify end-of-over checkpoint deliveries (last delivery of each over)
    valid["is_end_of_over"] = (
        valid.groupby(["match_id", "innings", "overid"])["innings_ball_num"].transform("max")
        == valid["innings_ball_num"]
    )

    audit_rows: List[Dict[str, Any]] = []
    ckpt_rows: List[Dict[str, Any]] = []
    ckpt_cal_rows: List[pd.DataFrame] = []
    checkpoints = [3, 6, 10, 15, 18, 20]

    for inn in (1, 2):
        sub = valid[valid["innings"] == inn].copy().reset_index(drop=True)
        y_model = (sub["inn1_team_won"] if inn == 1 else sub["batting_team_won"]).astype(int).values
        y_inn1 = sub["inn1_team_won"].astype(int).values

        for model_type in ("ELO_ONLY_BASELINE", "OBSERVABLE_STATE_WP"):
            # 1. 5-Fold Match-Grouped CV
            gkf = GroupKFold(n_splits=cfg.n_cv_folds)
            oof_p = np.zeros(len(sub), dtype=float)
            for tr_idx, te_idx in gkf.split(sub, groups=sub["match_id"]):
                tr_f = sub.iloc[tr_idx]
                te_f = sub.iloc[te_idx]
                if model_type == "OBSERVABLE_STATE_WP":
                    tr_m = set(tr_f["match_id"].unique())
                    er_st = fit_er_model(valid[valid["match_id"].isin(tr_m)], cfg)
                    tr_eb = apply_eb_par_to_deliveries(tr_f, er_st["eb_state"])
                    te_eb = apply_eb_par_to_deliveries(te_f, er_st["eb_state"])
                else:
                    tr_eb, te_eb = tr_f, te_f

                X_tr = _build_obs_features(tr_eb, model_type)
                X_te = _build_obs_features(te_eb, model_type)
                sc = StandardScaler()
                clf = LogisticRegression(C=0.5, max_iter=1000, random_state=cfg.random_seed)
                clf.fit(sc.fit_transform(X_tr), y_model[tr_idx])
                oof_p[te_idx] = np.clip(clf.predict_proba(sc.transform(X_te))[:, 1], 1e-6, 1.0 - 1e-6)

            p_inn1_cv = oof_p if inn == 1 else (1.0 - oof_p)

            # 2. Chronological OOT (> 2024)
            tr_m_oot = (sub["year"] <= cfg.oot_cutoff_year).values
            te_m_oot = (sub["year"] > cfg.oot_cutoff_year).values
            tr_o, te_o = sub[tr_m_oot], sub[te_m_oot]
            if model_type == "OBSERVABLE_STATE_WP":
                er_o = fit_er_model(valid[valid["year"] <= cfg.oot_cutoff_year], cfg)
                tr_o_eb = apply_eb_par_to_deliveries(tr_o, er_o["eb_state"])
                te_o_eb = apply_eb_par_to_deliveries(te_o, er_o["eb_state"])
            else:
                tr_o_eb, te_o_eb = tr_o, te_o

            X_tr_o = _build_obs_features(tr_o_eb, model_type)
            X_te_o = _build_obs_features(te_o_eb, model_type)
            sc_o = StandardScaler()
            clf_o = LogisticRegression(C=0.5, max_iter=1000, random_state=cfg.random_seed)
            clf_o.fit(sc_o.fit_transform(X_tr_o), y_model[tr_m_oot])
            p_o = np.clip(clf_o.predict_proba(sc_o.transform(X_te_o))[:, 1], 1e-6, 1.0 - 1e-6)
            p_inn1_oot = p_o if inn == 1 else (1.0 - p_o)

            for split_name, df_s, y_s, p_s in [
                ("MatchGrouped_5Fold_CV", sub, y_inn1, p_inn1_cv),
                (f"Chronological_OOT_gt_{cfg.oot_cutoff_year}", te_o, y_inn1[te_m_oot], p_inn1_oot),
            ]:
                b_eq, ll_eq = _equal_match_weighted_loss(df_s["match_id"].values, y_s, p_s)
                ci = _match_cluster_bootstrap_metrics(
                    df_s["match_id"].values, y_s, p_s, n_boot=n_boot, seed=cfg.random_seed
                )
                c_int, c_slp = _calibration_intercept_slope(y_s, p_s)
                audit_rows.append(
                    {
                        "innings": inn,
                        "model_family": model_type,
                        "evaluation_split": split_name,
                        "n_matches": int(df_s["match_id"].nunique()),
                        "n_deliveries": int(len(df_s)),
                        "brier_equal_match": round(b_eq, 4),
                        "brier_eq_ci_low": round(ci["brier_eq_ci"][0], 4),
                        "brier_eq_ci_high": round(ci["brier_eq_ci"][1], 4),
                        "logloss_equal_match": round(ll_eq, 4),
                        "logloss_eq_ci_low": round(ci["logloss_eq_ci"][0], 4),
                        "logloss_eq_ci_high": round(ci["logloss_eq_ci"][1], 4),
                        "roc_auc_delivery": round(float(roc_auc_score(y_s, p_s)), 4),
                        "brier_delivery": round(float(brier_score_loss(y_s, p_s)), 4),
                        "logloss_delivery": round(float(log_loss(y_s, p_s)), 4),
                        "cal_intercept": round(c_int, 4),
                        "cal_slope": round(c_slp, 4),
                        "governance_status": "RESEARCH_BASELINE",
                    }
                )

            # End-of-over checkpoint evaluation on 5-fold CV
            for ov in checkpoints:
                ck_mask = (sub["is_end_of_over"].values) & (sub["overid"].values == ov)
                if ck_mask.sum() < 30:
                    continue
                y_ck = y_inn1[ck_mask]
                p_ck = p_inn1_cv[ck_mask]
                m_ck = sub.loc[ck_mask, "match_id"].values
                b_ck, ll_ck = _equal_match_weighted_loss(m_ck, y_ck, p_ck)
                ci_ck = _match_cluster_bootstrap_metrics(m_ck, y_ck, p_ck, n_boot=n_boot, seed=cfg.random_seed)
                c_int_ck, c_slp_ck = _calibration_intercept_slope(y_ck, p_ck)
                ckpt_rows.append(
                    {
                        "innings": inn,
                        "over_checkpoint": ov,
                        "model_family": model_type,
                        "n_matches": int(len(np.unique(m_ck))),
                        "roc_auc": round(float(roc_auc_score(y_ck, p_ck)), 4),
                        "brier_equal_match": round(b_ck, 4),
                        "brier_ci_low": round(ci_ck["brier_eq_ci"][0], 4),
                        "brier_ci_high": round(ci_ck["brier_eq_ci"][1], 4),
                        "logloss_equal_match": round(ll_ck, 4),
                        "logloss_ci_low": round(ci_ck["logloss_eq_ci"][0], 4),
                        "logloss_ci_high": round(ci_ck["logloss_eq_ci"][1], 4),
                        "cal_intercept": round(c_int_ck, 4),
                        "cal_slope": round(c_slp_ck, 4),
                    }
                )
                if ov in (6, 15, 20):
                    cal_b = _calibration_curve_bins(y_ck, p_ck, n_bins=5)
                    cal_b["innings"] = inn
                    cal_b["over_checkpoint"] = ov
                    cal_b["model_family"] = model_type
                    ckpt_cal_rows.append(cal_b)

    audit_df = pd.DataFrame(audit_rows)
    ckpt_df = pd.DataFrame(ckpt_rows)
    ckpt_cal_df = pd.concat(ckpt_cal_rows, ignore_index=True)

    audit_df.to_csv(cfg.output_dir / "V4_3_PHASE3_5_WP_AUDIT_METRICS.csv", index=False)
    ckpt_df.to_csv(cfg.output_dir / "V4_3_PHASE3_5_CHECKPOINT_METRICS.csv", index=False)
    ckpt_cal_df.to_csv(cfg.output_dir / "V4_3_PHASE3_5_CHECKPOINT_CALIBRATION.csv", index=False)
    return audit_df, ckpt_df, ckpt_cal_df
