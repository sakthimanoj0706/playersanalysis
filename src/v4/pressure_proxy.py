"""Phase B — Pure Pre-Delivery Context, B1 WP_obs Benchmark & B3 Resource Stress Proxies."""
from __future__ import annotations

import os
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from scipy import optimize
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from src.ingestion.adapters.rr_data_adapter import RRDataAdapter

PRESSURE_MODEL_VERSION = "v4.0-b3-resource-stress"
PRESSURE_SOURCE_TYPE = "RESOURCE_STRESS_PROXY"


def build_pre_delivery_context(data_dir: str = "data") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load scoped IPL/T20I data and construct leak-free pre-delivery innings context."""
    bbb = pd.read_csv(os.path.join(data_dir, "ball_by_ball_ipl_t20i.csv"), low_memory=False)
    matches = pd.read_csv(os.path.join(data_dir, "matches_ipl_t20i.csv"))

    adapter = RRDataAdapter(quarantine_unknown_extras=True)
    cleaned = adapter.transform_deliveries(bbb)
    reg, so = adapter.separate_cohorts(cleaned)

    m = matches[[
        "match_id", "win_team_id", "result", "first_inn_revised_overs",
        "second_inn_revised_overs", "revised_target", "knock_out"
    ]].copy()
    m["is_dl_method"] = m["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True).astype(int)

    reg = reg.merge(m, on="match_id", how="left")
    reg["match_date_dt"] = pd.to_datetime(reg["match_date"], errors="coerce")
    season_yr = pd.to_numeric(reg["season"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    reg["year"] = reg["match_date_dt"].dt.year.fillna(season_yr).astype(int)

    reg = reg.sort_values(
        ["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]
    ).reset_index(drop=True)

    # DLS revised_overs values in dataset are stored in BALLS (30..114); convert only if <=20.
    rev1 = pd.to_numeric(reg["first_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev2 = pd.to_numeric(reg["second_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev1_balls = np.where(rev1 > 0, np.where(rev1 <= 20.0, rev1 * 6.0, rev1), 120.0)
    rev2_balls = np.where(rev2 > 0, np.where(rev2 <= 20.0, rev2 * 6.0, rev2), 120.0)
    reg["sched_balls"] = np.where(reg["innings"] == 1, rev1_balls, rev2_balls)

    g = reg.groupby(["match_id", "innings"], sort=False)
    reg["legal_balls_before"] = (g["is_legal_ball"].cumsum() - reg["is_legal_ball"]).astype(int)
    reg["balls_rem_before"] = np.maximum(reg["sched_balls"] - reg["legal_balls_before"], 0.0)

    is_any_wkt = (reg["is_wicket"] == 1).astype(int)
    reg["wkts_before"] = (g["is_wicket"].cumsum() - is_any_wkt).clip(0, 9).astype(int)
    reg["wkts_rem_before"] = (10 - reg["wkts_before"]).astype(int)
    reg["is_t20i"] = (reg["match_format"] == "T20I").astype(int)
    reg["phase"] = reg["innings_phase"].astype(str)

    reg["batting_won"] = np.where(
        reg["win_team_id"].isna(), np.nan, (reg["win_team_id"] == reg["batting_team_id"]).astype(float)
    )
    reg["is_striker_out"] = (
        (reg["is_wicket"] == 1) & (reg["dismissed_player_id"] == reg["striker_id"])
    ).astype(int)
    reg["is_ctrl_ball"] = reg["is_dot_ball"].astype(int)

    return reg, so


def _calibration_intercept_slope(y_true: np.ndarray, probs: np.ndarray) -> Tuple[float, float]:
    """Logistic calibration intercept and slope on clipped logit probabilities."""
    p_cl = np.clip(probs, 1e-6, 1.0 - 1e-6)
    logits = np.log(p_cl / (1.0 - p_cl)).reshape(-1, 1)
    cal = LogisticRegression(C=1e6, fit_intercept=True, solver="lbfgs").fit(logits, y_true)
    return float(cal.intercept_[0]), float(cal.coef_[0][0])


def evaluate_observable_wp_benchmark(reg_df: pd.DataFrame, cutoff_year: int = 2024) -> pd.DataFrame:
    """Phase B1 diagnostic: chronological score-blind WP_obs fit <=cutoff -> test >cutoff."""
    valid = reg_df[reg_df["batting_won"].notna()].copy()
    valid["bf"] = valid["legal_balls_before"] / np.maximum(valid["sched_balls"], 1.0)
    valid["wf"] = valid["wkts_before"] / 10.0
    valid["bw"] = valid["bf"] * valid["wf"]

    rows = []
    feats = ["bf", "wf", "bw", "is_t20i"]
    for inn in (1, 2):
        sub = valid[valid["innings"] == inn]
        tr = sub[sub["year"] <= cutoff_year]
        te = sub[sub["year"] > cutoff_year]
        lr = LogisticRegression(max_iter=500).fit(tr[feats], tr["batting_won"].astype(int))
        p_te = lr.predict_proba(te[feats])[:, 1]
        y_te = te["batting_won"].values.astype(int)
        cal_int, cal_slp = _calibration_intercept_slope(y_te, p_te)
        rows.append({
            "validation_family": "B1_WP_OBS_CHRONOLOGICAL",
            "split": f"innings_{inn}_train<={cutoff_year}_test>{cutoff_year}",
            "n_train": int(len(tr)),
            "n_test": int(len(te)),
            "metric_name": "Brier/LogLoss/AUC/CalSlope",
            "brier": round(float(brier_score_loss(y_te, p_te)), 4),
            "log_loss": round(float(log_loss(y_te, p_te)), 4),
            "roc_auc": round(float(roc_auc_score(y_te, p_te)), 4),
            "cal_intercept": round(cal_int, 4),
            "cal_slope": round(cal_slp, 4),
            "status": "QUARANTINED_SCORE_BLIND",
        })
    return pd.DataFrame(rows)


def _bowl_design_matrix(df: pd.DataFrame) -> np.ndarray:
    """Strictly pre-delivery design matrix for expected runs threat Ridge model."""
    u = np.clip(df["balls_rem_before"].values / 120.0, 0.0, 1.2)
    wf = df["wkts_rem_before"].values / 10.0
    inn2 = (df["innings"].values == 2).astype(float)
    fmt = df["is_t20i"].values.astype(float)
    pp = (df["phase"].values == "powerplay").astype(float)
    mid = (df["phase"].values == "middle").astype(float)
    death = (df["phase"].values == "death").astype(float)
    return np.column_stack([
        pp, mid, death, inn2, fmt, wf, u,
        pp * wf, mid * wf, death * wf,
        death * (1.0 - wf), inn2 * u, death * u,
    ])


def fit_b3_resource_stress(train_df: pd.DataFrame) -> Dict[str, Any]:
    """Fit Phase B3 batting resource depletion and bowling scoring-threat proxies on train split."""
    tr = train_df.copy()
    tot_runs = tr.groupby(["match_id", "innings"])["batter_runs"].transform("sum")
    cum_before = tr.groupby(["match_id", "innings"])["batter_runs"].cumsum() - tr["batter_runs"]
    tr["rem_runs"] = tot_runs - cum_before

    curve_params: Dict[int, np.ndarray] = {}
    for inn in (1, 2):
        sub = tr[(tr["innings"] == inn) & (tr["is_dl_method"] == 0) & (tr["balls_rem_before"] > 0)]
        agg = sub.groupby(["balls_rem_before", "wkts_before"], as_index=False).agg(
            y=("rem_runs", "mean"), w=("rem_runs", "size")
        )
        u = np.clip(agg["balls_rem_before"].values / 120.0, 1e-4, 1.2)
        wk = np.clip((10.0 - agg["wkts_before"].values) / 10.0, 0.1, 1.0)
        y = agg["y"].values
        wt = agg["w"].values

        def _loss(th: np.ndarray) -> float:
            pred = th[0] * (1.0 - np.exp(-th[1] * u)) * (wk ** th[2])
            return float(np.sum(wt * (y - pred) ** 2))

        opt = optimize.minimize(
            _loss, x0=[200.0, 1.0, 0.5],
            bounds=[(80.0, 400.0), (0.05, 5.0), (0.1, 2.0)],
            method="L-BFGS-B",
        )
        curve_params[inn] = opt.x

    def _raw_depl(d: pd.DataFrame) -> np.ndarray:
        wk = np.clip((10.0 - d["wkts_before"].values) / 10.0, 0.1, 1.0)
        return np.where(
            d["innings"].values == 1,
            1.0 - (wk ** curve_params[1][2]),
            1.0 - (wk ** curve_params[2][2]),
        )

    tr["raw_depl"] = _raw_depl(tr)
    stage_exp = tr.groupby(["innings", "overid"], as_index=False)["raw_depl"].mean().rename(
        columns={"raw_depl": "stage_exp_depl"}
    )
    tr = tr.merge(stage_exp, on=["innings", "overid"], how="left")
    bat_sorted = np.sort((tr["raw_depl"] - tr["stage_exp_depl"].fillna(0.0)).values)

    tr_faced = tr[tr["is_ball_faced"] == 1]
    bowl_ridge = Ridge(alpha=10.0).fit(_bowl_design_matrix(tr_faced), tr_faced["batter_runs"].values.astype(float))
    bowl_sorted = np.sort(bowl_ridge.predict(_bowl_design_matrix(tr)))

    return {
        "curve_params": {k: v.tolist() for k, v in curve_params.items()},
        "stage_exp": stage_exp,
        "bat_sorted": bat_sorted,
        "bowl_ridge": bowl_ridge,
        "bowl_sorted": bowl_sorted,
        "model_version": PRESSURE_MODEL_VERSION,
        "source_type": PRESSURE_SOURCE_TYPE,
    }


def apply_b3_resource_stress(df: pd.DataFrame, b3_state: Dict[str, Any]) -> pd.DataFrame:
    """Apply previously fitted B3 proxies cleanly without target/current-delivery leakage."""
    out = df.copy()
    # Drop stage_exp_depl if re-applying
    if "stage_exp_depl" in out.columns:
        out = out.drop(columns=["stage_exp_depl"])

    wk = np.clip((10.0 - out["wkts_before"].values) / 10.0, 0.1, 1.0)
    gam1 = b3_state["curve_params"][1][2]
    gam2 = b3_state["curve_params"][2][2]
    raw_depl = np.where(out["innings"].values == 1, 1.0 - (wk ** gam1), 1.0 - (wk ** gam2))
    out["raw_depl"] = raw_depl
    out = out.merge(b3_state["stage_exp"], on=["innings", "overid"], how="left")
    out["bat_stress_raw"] = out["raw_depl"] - out["stage_exp_depl"].fillna(0.0)
    bat_sorted = b3_state["bat_sorted"]
    out["bat_pressure"] = np.searchsorted(bat_sorted, out["bat_stress_raw"].values, side="right") / max(len(bat_sorted), 1)

    bowl_threat = b3_state["bowl_ridge"].predict(_bowl_design_matrix(out))
    out["bowl_threat_raw"] = bowl_threat
    bowl_sorted = b3_state["bowl_sorted"]
    out["bowl_pressure"] = np.searchsorted(bowl_sorted, bowl_threat, side="right") / max(len(bowl_sorted), 1)

    out["pressure_model_version"] = b3_state["model_version"]
    out["pressure_source_type"] = b3_state["source_type"]
    return out


def export_pressure_deliveries_parquet(df: pd.DataFrame, output_dir: str = "data/outputs/v4") -> str:
    """Export canonical delivery-level V4 pressure table."""
    os.makedirs(output_dir, exist_ok=True)
    cols = [
        "match_id", "innings", "overid", "over_ball_num", "innings_ball_num",
        "match_format", "season", "year", "innings_phase",
        "striker_id", "striker_name", "bowler_id", "bowler_name",
        "batter_runs", "is_ball_faced", "is_legal_ball", "is_striker_out",
        "is_bowler_wicket", "is_ctrl_ball", "legal_balls_before",
        "balls_rem_before", "wkts_before", "bat_stress_raw", "bat_pressure",
        "bowl_threat_raw", "bowl_pressure", "pressure_model_version", "pressure_source_type",
    ]
    path = os.path.join(output_dir, "PRESSURE_INDEX_DELIVERIES_V4.parquet")
    df[cols].to_parquet(path, index=False)
    return path
