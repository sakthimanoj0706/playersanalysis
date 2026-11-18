"""Phase 3: Two-Innings Win Probability Engine (Model A: Inn 1, Model B: Inn 2) for V4.3."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from src.v4_3.config import DEFAULT_CONFIG, V43Config
from src.v4_3.expected_runs import apply_eb_par_to_deliveries, fit_er_model, predict_er


def compute_pre_match_elo(reg_df: pd.DataFrame, cfg: V43Config = DEFAULT_CONFIG) -> pd.DataFrame:
    """
    Compute strictly chronological pre-match Elo ratings for batting and bowling teams.
    Zero future-data leakage: ratings for match m use ONLY matches strictly before match m.
    """
    match_teams = (
        reg_df.groupby("match_id", as_index=False)
        .agg(
            match_date_dt=("match_date_dt", "first"),
            inn1_team=("inn1_batting_team_id", "first"),
            home_team=("home_team_id", "first"),
            away_team=("away_team_id", "first"),
            win_team=("win_team_id", "first"),
        )
        .sort_values(["match_date_dt", "match_id"])
        .reset_index(drop=True)
    )

    elos: Dict[Any, float] = {}
    pre_home: List[float] = []
    pre_away: List[float] = []

    for _, row in match_teams.iterrows():
        t1 = row["home_team"]
        t2 = row["away_team"]
        r1 = elos.get(t1, cfg.team_elo_base)
        r2 = elos.get(t2, cfg.team_elo_base)
        pre_home.append(r1)
        pre_away.append(r2)

        w = row["win_team"]
        if pd.notna(w) and pd.notna(t1) and pd.notna(t2):
            e1 = 1.0 / (1.0 + 10.0 ** ((r2 - r1) / 400.0))
            s1 = 1.0 if w == t1 else (0.0 if w == t2 else 0.5)
            elos[t1] = r1 + cfg.team_elo_k * (s1 - e1)
            elos[t2] = r2 + cfg.team_elo_k * ((1.0 - s1) - (1.0 - e1))

    match_teams["pre_home_elo"] = pre_home
    match_teams["pre_away_elo"] = pre_away

    out = reg_df.merge(
        match_teams[["match_id", "pre_home_elo", "pre_away_elo"]],
        on="match_id",
        how="left",
    )
    out["bat_team_elo"] = np.where(
        out["batting_team_id"] == out["home_team_id"], out["pre_home_elo"], out["pre_away_elo"]
    )
    out["bowl_team_elo"] = np.where(
        out["bowling_team_id"] == out["home_team_id"], out["pre_home_elo"], out["pre_away_elo"]
    )
    out["elo_diff_bat_minus_bowl"] = (out["bat_team_elo"] - out["bowl_team_elo"]) / 100.0
    return out


def _calibration_intercept_slope(y_true: np.ndarray, probs: np.ndarray) -> Tuple[float, float]:
    """Compute logistic calibration intercept and slope on clipped logit probabilities."""
    p_cl = np.clip(probs, 1e-6, 1.0 - 1e-6)
    logits = np.log(p_cl / (1.0 - p_cl)).reshape(-1, 1)
    cal = LogisticRegression(C=1e6, fit_intercept=True, solver="lbfgs").fit(logits, y_true)
    return float(cal.intercept_[0]), float(cal.coef_[0][0])


def _calibration_curve_bins(
    y_true: np.ndarray,
    probs: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """Compute equal-width probability calibration bins."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        if i == n_bins - 1:
            m = (probs >= lo) & (probs <= hi)
        else:
            m = (probs >= lo) & (probs < hi)
        n = int(m.sum())
        rows.append(
            {
                "bin_idx": i,
                "bin_lower": float(lo),
                "bin_upper": float(hi),
                "n_deliveries": n,
                "mean_pred_prob": float(np.mean(probs[m])) if n > 0 else np.nan,
                "empirical_win_rate": float(np.mean(y_true[m])) if n > 0 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def _build_inn1_features(df: pd.DataFrame, er_pred: np.ndarray, include_score: bool) -> np.ndarray:
    """Design matrix for Model A (First Innings Win Probability)."""
    u = np.clip(df["balls_rem_before"].values / np.maximum(df["sched_balls"].values, 1.0), 0.0, 1.0)
    w_rem = df["wkts_rem_before"].values / 10.0
    is_t20i = (df["match_format"].values == "T20I").astype(float)
    elo_diff = df["elo_diff_bat_minus_bowl"].fillna(0.0).values
    par_factor = df["eb_venue_par_factor"].fillna(1.0).values

    cols = [u, w_rem, u * w_rem, is_t20i, elo_diff, par_factor]
    if include_score:
        # Use verified score if available, else lower bound (for diagnostic only)
        curr_score = df["min_team_score_before_lb"].values
        proj_final = curr_score + er_pred
        par_score = df["eb_venue_par_bat_runs"].fillna(150.0).values
        proj_diff = (proj_final - par_score) / 20.0
        lb = df["legal_balls_before"].values.astype(float)
        curr_crr = np.divide(curr_score, lb / 6.0, out=np.full(len(curr_score), 7.5, dtype=float), where=lb > 0)
        cols.extend([proj_final / 100.0, proj_diff, curr_crr / 10.0])
    return np.column_stack(cols)


def _build_inn2_features(df: pd.DataFrame, include_score: bool) -> np.ndarray:
    """Design matrix for Model B (Second Innings Win Probability)."""
    u = np.clip(df["balls_rem_before"].values / np.maximum(df["sched_balls"].values, 1.0), 0.0, 1.0)
    w_rem = df["wkts_rem_before"].values / 10.0
    is_t20i = (df["match_format"].values == "T20I").astype(float)
    elo_diff = df["elo_diff_bat_minus_bowl"].fillna(0.0).values
    par_factor = df["eb_venue_par_factor"].fillna(1.0).values

    cols = [u, w_rem, u * w_rem, is_t20i, elo_diff, par_factor]
    if include_score:
        curr_score = df["min_team_score_before_lb"].values
        target_lb = df["inn1_min_total_lb"].values + 1.0
        runs_req = np.maximum(target_lb - curr_score, 0.0)
        balls_rem = np.maximum(df["balls_rem_before"].values, 1.0)
        rrr = np.clip(runs_req / (balls_rem / 6.0), 0.0, 36.0)
        lb = df["legal_balls_before"].values.astype(float)
        crr = np.divide(curr_score, lb / 6.0, out=np.full(len(curr_score), 7.5, dtype=float), where=lb > 0)
        rrr_minus_crr = np.clip(rrr - crr, -20.0, 25.0)
        cols.extend(
            [
                runs_req / 100.0,
                rrr / 10.0,
                crr / 10.0,
                rrr_minus_crr / 10.0,
                (rrr / 10.0) * (1.0 - w_rem),
            ]
        )
    return np.column_stack(cols)


def _fit_predict_logistic(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_te: np.ndarray,
    c_reg: float = 0.5,
) -> Tuple[np.ndarray, LogisticRegression, StandardScaler]:
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)
    clf = LogisticRegression(C=c_reg, max_iter=1000, solver="lbfgs", random_state=2026)
    clf.fit(X_tr_s, y_tr)
    probs = np.clip(clf.predict_proba(X_te_s)[:, 1], 1e-6, 1.0 - 1e-6)
    return probs, clf, scaler


def _save_calibration_plot(cal_df: pd.DataFrame, title: str, out_path: Any) -> None:
    """Save interactive Plotly calibration curve."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect Calibration",
            line=dict(dash="dash", color="gray"),
        )
    )
    for model_name, grp in cal_df.groupby("model_family"):
        valid = grp.dropna(subset=["mean_pred_prob", "empirical_win_rate"])
        fig.add_trace(
            go.Scatter(
                x=valid["mean_pred_prob"],
                y=valid["empirical_win_rate"],
                mode="lines+markers",
                name=model_name,
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Predicted Win Probability",
        yaxis_title="Empirical Win Rate",
        template="plotly_white",
        width=760,
        height=480,
    )
    fig.write_html(str(out_path))


def evaluate_phase3_win_probability(
    reg_df: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Evaluate Two-Innings Win Probability Engine under 5-fold Match-Grouped CV and Chronological OOT.
    Separately evaluates:
      1) OBSERVABLE_STATE_WP (valid on unverified-extras data, score-blind)
      2) LOWER_BOUND_SCORE_WP_DIAGNOSTIC (score-aware architecture using min_team_score_before_lb;
         explicitly blocked for production due to Phase 1 unquantified extras).
    Both innings expose consistent perspective: P(inn1_batting_team wins).
    """
    cfg.ensure_dirs()
    df = compute_pre_match_elo(reg_df, cfg)

    # Attach innings-1 lower-bound total for innings-2 diagnostic chase target
    inn1_lb = (
        df[df["innings"] == 1]
        .groupby("match_id")["min_delivery_runs_lb"]
        .sum()
        .rename("inn1_min_total_lb")
    )
    df = df.merge(inn1_lb, on="match_id", how="left")
    df["inn1_min_total_lb"] = df["inn1_min_total_lb"].fillna(150.0)

    # Valid decided non-DLS matches with known win_team_id
    valid = df[df["inn1_team_won"].notna() & (~df["is_dl"].fillna(False))].copy().reset_index(drop=True)

    inn1_metrics_rows: List[Dict[str, Any]] = []
    inn2_metrics_rows: List[Dict[str, Any]] = []
    cal_rows: List[pd.DataFrame] = []

    for inn in (1, 2):
        sub = valid[valid["innings"] == inn].copy().reset_index(drop=True)
        # Model A predicts inn1_team_won; Model B predicts chasing_team_won then converts to inn1_team_won
        y_model = (sub["inn1_team_won"] if inn == 1 else sub["batting_team_won"]).astype(int).values
        y_inn1_persp = sub["inn1_team_won"].astype(int).values

        for family_name, include_score, gov_status in [
            ("OBSERVABLE_STATE_WP", False, "VALIDATED_SCORE_BLIND_BASELINE"),
            ("LOWER_BOUND_SCORE_WP_DIAGNOSTIC", True, "BLOCKED_FOR_PRODUCTION_UNVERIFIED_EXTRAS"),
        ]:
            # 1. 5-Fold Match-Grouped CV
            gkf = GroupKFold(n_splits=cfg.n_cv_folds)
            oof_p_model = np.zeros(len(sub), dtype=float)
            fold_aucs: List[float] = []

            for tr_idx, te_idx in gkf.split(sub, groups=sub["match_id"]):
                tr_f = sub.iloc[tr_idx]
                te_f = sub.iloc[te_idx]
                tr_match_ids = set(tr_f["match_id"].unique())
                er_st = fit_er_model(valid[valid["match_id"].isin(tr_match_ids)], cfg)
                tr_eb = apply_eb_par_to_deliveries(tr_f, er_st["eb_state"])
                te_eb = apply_eb_par_to_deliveries(te_f, er_st["eb_state"])

                if inn == 1:
                    er_tr = predict_er(tr_eb, er_st)
                    er_te = predict_er(te_eb, er_st)
                    X_tr = _build_inn1_features(tr_eb, er_tr, include_score)
                    X_te = _build_inn1_features(te_eb, er_te, include_score)
                else:
                    X_tr = _build_inn2_features(tr_eb, include_score)
                    X_te = _build_inn2_features(te_eb, include_score)

                p_te, _, _ = _fit_predict_logistic(X_tr, y_model[tr_idx], X_te, c_reg=0.5)
                oof_p_model[te_idx] = p_te
                fold_aucs.append(float(roc_auc_score(y_model[te_idx], p_te)))

            # Convert to unified inn1_team perspective
            oof_p_inn1_persp = oof_p_model if inn == 1 else (1.0 - oof_p_model)
            cal_int, cal_slp = _calibration_intercept_slope(y_inn1_persp, oof_p_inn1_persp)

            cv_row = {
                "innings": inn,
                "model_family": family_name,
                "evaluation_split": "MatchGrouped_5Fold_CV",
                "n_deliveries": int(len(sub)),
                "n_matches": int(sub["match_id"].nunique()),
                "roc_auc": round(float(roc_auc_score(y_inn1_persp, oof_p_inn1_persp)), 4),
                "brier_score": round(float(brier_score_loss(y_inn1_persp, oof_p_inn1_persp)), 4),
                "log_loss": round(float(log_loss(y_inn1_persp, oof_p_inn1_persp)), 4),
                "cal_intercept": round(cal_int, 4),
                "cal_slope": round(cal_slp, 4),
                "cv_auc_std": round(float(np.std(fold_aucs)), 4),
                "perspective": "P(inn1_batting_team_wins)",
                "governance_status": gov_status,
            }

            cal_bins = _calibration_curve_bins(y_inn1_persp, oof_p_inn1_persp, cfg.wp_calibration_bins)
            cal_bins["innings"] = inn
            cal_bins["model_family"] = family_name
            cal_bins["evaluation_split"] = "MatchGrouped_5Fold_CV"
            cal_rows.append(cal_bins)

            # 2. Chronological OOT Split
            tr_mask = (sub["year"] <= cfg.oot_cutoff_year).values
            te_mask = (sub["year"] > cfg.oot_cutoff_year).values
            tr_oot = sub[tr_mask]
            te_oot = sub[te_mask]

            er_oot = fit_er_model(valid[valid["year"] <= cfg.oot_cutoff_year], cfg)
            tr_oot_eb = apply_eb_par_to_deliveries(tr_oot, er_oot["eb_state"])
            te_oot_eb = apply_eb_par_to_deliveries(te_oot, er_oot["eb_state"])
            if inn == 1:
                X_tr_o = _build_inn1_features(tr_oot_eb, predict_er(tr_oot_eb, er_oot), include_score)
                X_te_o = _build_inn1_features(te_oot_eb, predict_er(te_oot_eb, er_oot), include_score)
            else:
                X_tr_o = _build_inn2_features(tr_oot_eb, include_score)
                X_te_o = _build_inn2_features(te_oot_eb, include_score)

            p_oot_m, _, _ = _fit_predict_logistic(X_tr_o, y_model[tr_mask], X_te_o, c_reg=0.5)
            p_oot_inn1 = p_oot_m if inn == 1 else (1.0 - p_oot_m)
            y_oot_inn1 = y_inn1_persp[te_mask]
            c_int_o, c_slp_o = _calibration_intercept_slope(y_oot_inn1, p_oot_inn1)

            oot_row = {
                "innings": inn,
                "model_family": family_name,
                "evaluation_split": f"Chronological_OOT_gt_{cfg.oot_cutoff_year}",
                "n_deliveries": int(len(te_oot)),
                "n_matches": int(te_oot["match_id"].nunique()),
                "roc_auc": round(float(roc_auc_score(y_oot_inn1, p_oot_inn1)), 4),
                "brier_score": round(float(brier_score_loss(y_oot_inn1, p_oot_inn1)), 4),
                "log_loss": round(float(log_loss(y_oot_inn1, p_oot_inn1)), 4),
                "cal_intercept": round(c_int_o, 4),
                "cal_slope": round(c_slp_o, 4),
                "cv_auc_std": np.nan,
                "perspective": "P(inn1_batting_team_wins)",
                "governance_status": gov_status,
            }

            if inn == 1:
                inn1_metrics_rows.extend([cv_row, oot_row])
            else:
                inn2_metrics_rows.extend([cv_row, oot_row])

    inn1_df = pd.DataFrame(inn1_metrics_rows)
    inn2_df = pd.DataFrame(inn2_metrics_rows)
    cal_df = pd.concat(cal_rows, ignore_index=True)

    inn1_df.to_csv(cfg.output_dir / "V4_3_FIRST_INNINGS_WP_METRICS.csv", index=False)
    inn2_df.to_csv(cfg.output_dir / "V4_3_SECOND_INNINGS_WP_METRICS.csv", index=False)
    cal_df.to_csv(cfg.output_dir / "V4_3_WP_CALIBRATION.csv", index=False)

    _save_calibration_plot(
        cal_df[cal_df["innings"] == 1],
        "V4.3 First-Innings Win Probability Calibration (5-Fold Match-Grouped CV)",
        cfg.plots_dir / "wp_first_innings_calibration.html",
    )
    _save_calibration_plot(
        cal_df[cal_df["innings"] == 2],
        "V4.3 Second-Innings Win Probability Calibration (5-Fold Match-Grouped CV; Perspective: Inn1 Team)",
        cfg.plots_dir / "wp_second_innings_calibration.html",
    )

    summary = {
        "first_innings_metrics": inn1_metrics_rows,
        "second_innings_metrics": inn2_metrics_rows,
        "production_status": "BLOCKED_ON_REAL_DATA_FOR_SCORE_AWARE_WP",
    }
    (cfg.artifacts_dir / "phase3_wp_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return inn1_df, inn2_df, cal_df, summary
