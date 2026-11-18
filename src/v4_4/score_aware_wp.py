"""Track A: Score-Aware Two-Innings Win Probability Engine for V4.4 (Cricsheet-Verified)."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import optimize
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from src.v4_3.expected_runs import _eb_shrink_group
from src.v4_3.win_probability import (
    _calibration_curve_bins,
    _calibration_intercept_slope,
    compute_pre_match_elo,
)
from src.v4_3.wp_evaluation_audit import _equal_match_weighted_loss
from src.v4_4.config import DEFAULT_V44_CONFIG, V44Config


def _resource_curve(u: np.ndarray, w_rem: np.ndarray, r0: float, b: float, gamma: float) -> np.ndarray:
    u_cl = np.clip(u, 0.0, 1.2)
    wf = np.clip(w_rem / 10.0, 0.0, 1.0)
    b_safe = max(float(b), 1e-4)
    denom = max(1.0 - float(np.exp(-b_safe)), 1e-6)
    return r0 * ((1.0 - np.exp(-b_safe * u_cl)) / denom) * np.power(wf, gamma)


def prepare_verified_score_state(
    reg_enriched: pd.DataFrame,
    cfg: V44Config = DEFAULT_V44_CONFIG,
) -> pd.DataFrame:
    """
    Filter to Cricsheet-verified innings and construct exact pre-delivery total-run state:
    current_score, target, runs_required, rrr, crr, rem_total_runs.
    """
    ver = reg_enriched[reg_enriched["score_verified"] == True].copy()
    ver = ver.sort_values(["match_id", "innings", "event_index_in_innings"]).reset_index(drop=True)

    ver["match_date_dt"] = pd.to_datetime(ver["match_date"], errors="coerce")
    season_yr = pd.to_numeric(ver["season"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    ver["year"] = ver["match_date_dt"].dt.year.fillna(season_yr).astype(int)

    matches = pd.read_csv(cfg.data_dir / "matches_ipl_t20i.csv")
    m_sub = matches[
        [
            "match_id",
            "venue_id",
            "home_team_id",
            "away_team_id",
            "first_inn_revised_overs",
            "second_inn_revised_overs",
            "win_team_id",
            "result",
        ]
    ].copy()
    m_sub["is_dl"] = m_sub["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True)
    ver = ver.merge(m_sub, on="match_id", how="left")

    rev1 = pd.to_numeric(ver["first_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev2 = pd.to_numeric(ver["second_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev1_b = np.where(rev1 > 0, np.where(rev1 <= 20.0, rev1 * 6.0, rev1), float(cfg.standard_t20_balls))
    rev2_b = np.where(rev2 > 0, np.where(rev2 <= 20.0, rev2 * 6.0, rev2), float(cfg.standard_t20_balls))
    ver["sched_balls"] = np.where(ver["innings"] == 1, rev1_b, rev2_b)

    g = ver.groupby(["match_id", "innings"], sort=False)
    ver["legal_ball_inc"] = ver["is_legal_ball"].astype(int)
    ver["legal_balls_before"] = (g["legal_ball_inc"].cumsum() - ver["legal_ball_inc"]).astype(int)
    ver["balls_rem_before"] = np.maximum(ver["sched_balls"] - ver["legal_balls_before"], 0.0)

    ver["wicket_inc"] = (ver["is_wicket"] == True).astype(int)
    ver["wkts_before"] = (g["wicket_inc"].cumsum() - ver["wicket_inc"]).clip(0, 9).astype(int)
    ver["wkts_rem_before"] = (10 - ver["wkts_before"]).astype(int)

    # Exact total runs from Cricsheet (including cs_penalty_pre at innings start)
    ver["actual_total_runs"] = ver["cs_total_runs"].astype(float)
    ver["current_score_before"] = (
        g["actual_total_runs"].cumsum() - ver["actual_total_runs"] + ver["cs_penalty_pre"].fillna(0.0)
    )
    inn_tot_runs = g["actual_total_runs"].transform("sum") + ver["cs_penalty_pre"].fillna(0.0)
    ver["rem_total_runs"] = inn_tot_runs - ver["current_score_before"]

    # Verified innings-1 total for innings-2 target
    inn1_tot = (
        ver[ver["innings"] == 1]
        .groupby("match_id")
        .agg(
            inn1_total=("actual_total_runs", "sum"),
            inn1_pen_pre=("cs_penalty_pre", "first"),
            inn1_pen_post=("cs_penalty_post", "first"),
            inn1_batting_team_id=("batting_team_id", "first"),
        )
        .reset_index()
    )
    inn1_tot["inn1_verified_total"] = (
        inn1_tot["inn1_total"] + inn1_tot["inn1_pen_pre"].fillna(0.0) + inn1_tot["inn1_pen_post"].fillna(0.0)
    )
    ver = ver.merge(inn1_tot[["match_id", "inn1_verified_total", "inn1_batting_team_id"]], on="match_id", how="left")

    # Target: cs_target_runs for DLS/revised if present, else inn1_verified_total + 1
    ver["verified_target"] = np.where(
        ver["innings"] == 2,
        np.where(ver["cs_target_runs"].notna(), ver["cs_target_runs"], ver["inn1_verified_total"] + 1.0),
        np.nan,
    )
    # Innings 2 requires valid target
    ver = ver[(ver["innings"] == 1) | ver["verified_target"].notna()].copy().reset_index(drop=True)

    ver["runs_required"] = np.where(
        ver["innings"] == 2,
        np.maximum(ver["verified_target"] - ver["current_score_before"], 0.0),
        np.nan,
    )
    lb = ver["legal_balls_before"].values.astype(float)
    ver["crr"] = np.divide(
        ver["current_score_before"].values,
        lb / 6.0,
        out=np.full(len(ver), 7.5, dtype=float),
        where=lb > 0,
    )
    br = np.maximum(ver["balls_rem_before"].values, 1.0)
    ver["rrr"] = np.where(
        ver["innings"] == 2,
        np.clip(ver["runs_required"].values / (br / 6.0), 0.0, 36.0),
        np.nan,
    )

    ver["inn1_team_won"] = np.where(
        ver["win_team_id"].isna() | ver["inn1_batting_team_id"].isna(),
        np.nan,
        (ver["win_team_id"] == ver["inn1_batting_team_id"]).astype(float),
    )
    ver["batting_team_won"] = np.where(
        ver["win_team_id"].isna(),
        np.nan,
        (ver["win_team_id"] == ver["batting_team_id"]).astype(float),
    )

    ver = compute_pre_match_elo(ver, cfg)
    return ver


def fit_total_er_model(train_df: pd.DataFrame, cfg: V44Config = DEFAULT_V44_CONFIG) -> Dict[str, Any]:
    """Fit EB venue/format par & resource curve ER_total(B, W) on total runs."""
    inn_df = train_df.groupby(["match_id", "innings", "match_format", "venue_id", "is_dl"], as_index=False).agg(
        total_runs=("actual_total_runs", "sum"),
        legal_balls=("legal_ball_inc", "sum"),
        wickets=("wicket_inc", "sum"),
    )
    clean_par = inn_df[
        (~inn_df["is_dl"].fillna(False))
        & (inn_df["innings"] == 1)
        & ((inn_df["legal_balls"] >= 90) | (inn_df["wickets"] == 10))
    ]
    if len(clean_par) < 20:
        clean_par = inn_df[inn_df["innings"] == 1]
    if len(clean_par) == 0:
        clean_par = inn_df

    g_mean = float(clean_par["total_runs"].mean())
    fmt_grp = clean_par.groupby("match_format", as_index=False).agg(
        n=("total_runs", "size"), raw_mean=("total_runs", "mean"), raw_var=("total_runs", "var")
    )
    fmt_grp["prior"] = g_mean
    fmt_eb = _eb_shrink_group(fmt_grp, "prior", "raw_mean")
    fmt_map = dict(zip(fmt_eb["match_format"], fmt_eb["eb_mean"]))

    fv_grp = clean_par.groupby(["match_format", "venue_id"], as_index=False).agg(
        n=("total_runs", "size"), raw_mean=("total_runs", "mean"), raw_var=("total_runs", "var")
    )
    fv_grp["prior"] = fv_grp["match_format"].map(fmt_map).fillna(g_mean)
    fv_eb = _eb_shrink_group(fv_grp, "prior", "raw_mean")
    fv_map = {
        (r["match_format"], int(r["venue_id"])): float(r["eb_mean"])
        for _, r in fv_eb.iterrows()
        if pd.notna(r["venue_id"])
    }

    par_vals = np.array(
        [
            fv_map.get((f, int(v)), fmt_map.get(f, g_mean)) if pd.notna(v) else fmt_map.get(f, g_mean)
            for f, v in zip(train_df["match_format"], train_df["venue_id"])
        ],
        dtype=float,
    )
    fac = np.clip(par_vals / max(g_mean, 1.0), 0.65, 1.45)

    curve_params: Dict[Tuple[int, str], Tuple[float, float, float]] = {}
    clean_mask = (~train_df["is_dl"].fillna(False)).values
    for inn in sorted(train_df["innings"].unique().astype(int)):
        for fmt in sorted(train_df["match_format"].dropna().unique()):
            m = clean_mask & (train_df["innings"].values == inn) & (train_df["match_format"].values == fmt)
            if m.sum() < 100:
                m = clean_mask & (train_df["innings"].values == inn)
            if m.sum() == 0:
                continue
            u = np.clip(train_df["balls_rem_before"].values[m] / float(cfg.standard_t20_balls), 0.0, 1.2)
            w_rem = train_df["wkts_rem_before"].values[m].astype(float)
            y_norm = train_df["rem_total_runs"].values[m] / fac[m]
            res = optimize.least_squares(
                lambda p: _resource_curve(u, w_rem, p[0], p[1], p[2]) - y_norm,
                x0=np.array([170.0, 0.8, 0.45]),
                bounds=([40.0, 0.05, 0.05], [400.0, 5.0, 2.5]),
                max_nfev=300,
            )
            curve_params[(inn, fmt)] = (float(res.x[0]), float(res.x[1]), float(res.x[2]))

    return {
        "global_mean": g_mean,
        "fmt_map": fmt_map,
        "fv_map": fv_map,
        "curve_params": curve_params,
        "standard_t20_balls": cfg.standard_t20_balls,
    }


def predict_total_er(df: pd.DataFrame, er_state: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Predict ER_total(B, W), eb_venue_par_total, and eb_venue_par_factor."""
    g_mean = er_state["global_mean"]
    fmt_map = er_state["fmt_map"]
    fv_map = er_state["fv_map"]
    par_vals = np.array(
        [
            fv_map.get((f, int(v)), fmt_map.get(f, g_mean)) if pd.notna(v) else fmt_map.get(f, g_mean)
            for f, v in zip(df["match_format"], df["venue_id"])
        ],
        dtype=float,
    )
    fac = np.clip(par_vals / max(g_mean, 1.0), 0.65, 1.45)

    u = np.clip(df["balls_rem_before"].values / float(er_state["standard_t20_balls"]), 0.0, 1.2)
    w_rem = df["wkts_rem_before"].values.astype(float)
    inn_all = df["innings"].values.astype(int)
    fmt_all = df["match_format"].values
    preds = np.zeros(len(df), dtype=float)
    for (inn, fmt), (r0, b, gamma) in er_state["curve_params"].items():
        m = (inn_all == inn) & (fmt_all == fmt)
        if np.any(m):
            preds[m] = _resource_curve(u[m], w_rem[m], r0, b, gamma) * fac[m]
    return np.maximum(preds, 0.0), par_vals, fac


def build_inn1_score_wp_features(
    df: pd.DataFrame,
    er_pred: np.ndarray,
    par_vals: np.ndarray,
    fac: np.ndarray,
) -> np.ndarray:
    u = np.clip(df["balls_rem_before"].values / np.maximum(df["sched_balls"].values, 1.0), 0.0, 1.0)
    w_rem = df["wkts_rem_before"].values / 10.0
    is_t20i = (df["match_format"].values == "T20I").astype(float)
    elo = df["elo_diff_bat_minus_bowl"].fillna(0.0).values
    curr = df["current_score_before"].values
    proj_final = curr + er_pred
    proj_diff = (proj_final - par_vals) / 20.0
    crr = df["crr"].values / 10.0
    return np.column_stack([u, w_rem, u * w_rem, is_t20i, elo, fac, curr / 100.0, proj_final / 100.0, proj_diff, crr])


def build_inn2_score_wp_features(df: pd.DataFrame, fac: np.ndarray) -> np.ndarray:
    u = np.clip(df["balls_rem_before"].values / np.maximum(df["sched_balls"].values, 1.0), 0.0, 1.0)
    w_rem = df["wkts_rem_before"].values / 10.0
    is_t20i = (df["match_format"].values == "T20I").astype(float)
    elo = df["elo_diff_bat_minus_bowl"].fillna(0.0).values
    runs_req = df["runs_required"].values
    rrr = df["rrr"].values
    crr = df["crr"].values
    rrr_diff = np.clip(rrr - crr, -20.0, 25.0)
    return np.column_stack(
        [
            u,
            w_rem,
            u * w_rem,
            is_t20i,
            elo,
            fac,
            runs_req / 100.0,
            rrr / 10.0,
            crr / 10.0,
            rrr_diff / 10.0,
            (rrr / 10.0) * (1.0 - w_rem),
        ]
    )


def run_track_a_score_aware_wp(
    ver_df: pd.DataFrame,
    cfg: V44Config = DEFAULT_V44_CONFIG,
) -> Dict[str, Any]:
    """
    Train & evaluate score-aware Two-Innings WP on Cricsheet-verified deliveries.
    Computes 5-fold match-grouped OOF WP predictions (for downstream Leverage Index)
    plus Chronological OOT (> 2024) metrics, equal-match-weighted loss, and checkpoints.
    """
    cfg.ensure_dirs()
    valid = ver_df[ver_df["inn1_team_won"].notna()].copy().reset_index(drop=True)
    valid["is_end_of_over"] = (
        valid.groupby(["match_id", "innings", "overid"])["event_index_in_innings"].transform("max")
        == valid["event_index_in_innings"]
    )

    inn1_rows: List[Dict[str, Any]] = []
    inn2_rows: List[Dict[str, Any]] = []
    cal_rows: List[pd.DataFrame] = []
    ckpt_rows: List[Dict[str, Any]] = []

    oof_wp_inn1_persp = np.full(len(valid), np.nan, dtype=float)
    fold_models: Dict[Tuple[int, int], Dict[str, Any]] = {}

    for inn in (1, 2):
        sub_mask = (valid["innings"].values == inn)
        sub = valid[sub_mask].copy().reset_index(drop=True)
        y_m = (sub["inn1_team_won"] if inn == 1 else sub["batting_team_won"]).astype(int).values
        y_inn1 = sub["inn1_team_won"].astype(int).values

        gkf = GroupKFold(n_splits=cfg.n_cv_folds)
        oof_p = np.zeros(len(sub), dtype=float)

        for fold_idx, (tr_idx, te_idx) in enumerate(gkf.split(sub, groups=sub["match_id"]), start=1):
            tr_m = set(sub.iloc[tr_idx]["match_id"].unique())
            er_st = fit_total_er_model(valid[valid["match_id"].isin(tr_m)], cfg)
            er_tr, par_tr, fac_tr = predict_total_er(sub.iloc[tr_idx], er_st)
            er_te, par_te, fac_te = predict_total_er(sub.iloc[te_idx], er_st)

            X_tr = (
                build_inn1_score_wp_features(sub.iloc[tr_idx], er_tr, par_tr, fac_tr)
                if inn == 1
                else build_inn2_score_wp_features(sub.iloc[tr_idx], fac_tr)
            )
            X_te = (
                build_inn1_score_wp_features(sub.iloc[te_idx], er_te, par_te, fac_te)
                if inn == 1
                else build_inn2_score_wp_features(sub.iloc[te_idx], fac_te)
            )
            sc = StandardScaler()
            clf = LogisticRegression(C=0.5, max_iter=1000, random_state=cfg.random_seed)
            clf.fit(sc.fit_transform(X_tr), y_m[tr_idx])
            oof_p[te_idx] = np.clip(clf.predict_proba(sc.transform(X_te))[:, 1], 1e-6, 1.0 - 1e-6)
            fold_models[(inn, fold_idx)] = {"er_state": er_st, "scaler": sc, "clf": clf}

        p_inn1_cv = oof_p if inn == 1 else (1.0 - oof_p)
        oof_wp_inn1_persp[sub_mask] = p_inn1_cv

        # Chronological OOT (> 2024)
        tr_oot_m = (sub["year"] <= cfg.oot_cutoff_year).values
        te_oot_m = (sub["year"] > cfg.oot_cutoff_year).values
        er_oot = fit_total_er_model(valid[valid["year"] <= cfg.oot_cutoff_year], cfg)
        er_tr_o, par_tr_o, fac_tr_o = predict_total_er(sub[tr_oot_m], er_oot)
        er_te_o, par_te_o, fac_te_o = predict_total_er(sub[te_oot_m], er_oot)
        X_tr_o = (
            build_inn1_score_wp_features(sub[tr_oot_m], er_tr_o, par_tr_o, fac_tr_o)
            if inn == 1
            else build_inn2_score_wp_features(sub[tr_oot_m], fac_tr_o)
        )
        X_te_o = (
            build_inn1_score_wp_features(sub[te_oot_m], er_te_o, par_te_o, fac_te_o)
            if inn == 1
            else build_inn2_score_wp_features(sub[te_oot_m], fac_te_o)
        )
        sc_o = StandardScaler()
        clf_o = LogisticRegression(C=0.5, max_iter=1000, random_state=cfg.random_seed)
        clf_o.fit(sc_o.fit_transform(X_tr_o), y_m[tr_oot_m])
        p_o = np.clip(clf_o.predict_proba(sc_o.transform(X_te_o))[:, 1], 1e-6, 1.0 - 1e-6)
        p_inn1_oot = p_o if inn == 1 else (1.0 - p_o)

        for split_name, df_s, y_s, p_s in [
            ("MatchGrouped_5Fold_CV", sub, y_inn1, p_inn1_cv),
            (f"Chronological_OOT_gt_{cfg.oot_cutoff_year}", sub[te_oot_m], y_inn1[te_oot_m], p_inn1_oot),
        ]:
            b_eq, ll_eq = _equal_match_weighted_loss(df_s["match_id"].values, y_s, p_s)
            c_int, c_slp = _calibration_intercept_slope(y_s, p_s)
            row = {
                "innings": inn,
                "model_family": "V4_4_SCORE_AWARE_WP",
                "evaluation_split": split_name,
                "n_matches": int(df_s["match_id"].nunique()),
                "n_deliveries": int(len(df_s)),
                "roc_auc": round(float(roc_auc_score(y_s, p_s)), 4),
                "brier_equal_match": round(b_eq, 4),
                "logloss_equal_match": round(ll_eq, 4),
                "brier_delivery": round(float(brier_score_loss(y_s, p_s)), 4),
                "logloss_delivery": round(float(log_loss(y_s, p_s)), 4),
                "cal_intercept": round(c_int, 4),
                "cal_slope": round(c_slp, 4),
                "perspective": "P(inn1_batting_team_wins)",
                "governance_status": "CONDITIONALLY_VALIDATED_CRICSHEET_EXACT",
            }
            if inn == 1:
                inn1_rows.append(row)
            else:
                inn2_rows.append(row)

        cal_b = _calibration_curve_bins(y_inn1, p_inn1_cv, n_bins=10)
        cal_b["innings"] = inn
        cal_rows.append(cal_b)

        for ov in (3, 6, 10, 15, 18, 20):
            ck = (sub["is_end_of_over"].values) & (sub["overid"].values == ov)
            if ck.sum() < 30:
                continue
            b_ck, ll_ck = _equal_match_weighted_loss(sub.loc[ck, "match_id"].values, y_inn1[ck], p_inn1_cv[ck])
            ckpt_rows.append(
                {
                    "innings": inn,
                    "over_checkpoint": ov,
                    "n_matches": int(sub.loc[ck, "match_id"].nunique()),
                    "roc_auc": round(float(roc_auc_score(y_inn1[ck], p_inn1_cv[ck])), 4),
                    "brier_equal_match": round(b_ck, 4),
                    "logloss_equal_match": round(ll_ck, 4),
                }
            )

    valid["wp_inn1_team_oof"] = oof_wp_inn1_persp
    inn1_df = pd.DataFrame(inn1_rows)
    inn2_df = pd.DataFrame(inn2_rows)
    cal_df = pd.concat(cal_rows, ignore_index=True)
    ckpt_df = pd.DataFrame(ckpt_rows)

    inn1_df.to_csv(cfg.output_dir / "V4_4_FIRST_INNINGS_WP_METRICS.csv", index=False)
    inn2_df.to_csv(cfg.output_dir / "V4_4_SECOND_INNINGS_WP_METRICS.csv", index=False)
    cal_df.to_csv(cfg.output_dir / "V4_4_WP_CALIBRATION.csv", index=False)
    ckpt_df.to_csv(cfg.output_dir / "V4_4_WP_CHECKPOINTS.csv", index=False)

    # Save calibration plots
    for inn in (1, 2):
        sub_c = cal_df[cal_df["innings"] == inn].dropna(subset=["mean_pred_prob", "empirical_win_rate"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect", line=dict(dash="dash", color="gray")))
        fig.add_trace(go.Scatter(x=sub_c["mean_pred_prob"], y=sub_c["empirical_win_rate"], mode="lines+markers", name=f"V4.4 Inn {inn}"))
        fig.update_layout(title=f"V4.4 Score-Aware WP Calibration (Innings {inn})", xaxis_title="Predicted WP", yaxis_title="Empirical Win Rate", template="plotly_white")
        fig.write_html(str(cfg.plots_dir / f"v4_4_wp_inn{inn}_calibration.html"))

    return {
        "valid_df": valid,
        "inn1_df": inn1_df,
        "inn2_df": inn2_df,
        "cal_df": cal_df,
        "ckpt_df": ckpt_df,
        "fold_models": fold_models,
    }
