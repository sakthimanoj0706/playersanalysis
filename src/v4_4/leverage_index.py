"""Track A: True Expected Leverage Index (LI) on Verified Score-Aware WP for V4.4."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from src.v4_4.config import DEFAULT_V44_CONFIG, V44Config
from src.v4_4.score_aware_wp import (
    build_inn1_score_wp_features,
    build_inn2_score_wp_features,
    predict_total_er,
)

OUTCOME_CATS = (
    "dot",
    "single",
    "two",
    "three",
    "four",
    "six",
    "wide",
    "noball",
    "bye",
    "legbye",
    "wicket",
    "other",
)


def classify_delivery_outcome(df: pd.DataFrame) -> np.ndarray:
    """Assign each delivery to one of 12 mutually exclusive outcome categories."""
    is_wkt = (df["wicket_inc"].values == 1)
    wides = df["cs_wides"].fillna(0).values
    nbs = df["cs_noballs"].fillna(0).values
    byes = df["cs_byes"].fillna(0).values
    legbyes = df["cs_legbyes"].fillna(0).values
    runs = df["actual_total_runs"].values

    out = np.full(len(df), "other", dtype=object)
    # Order matters for mutual exclusivity
    out[runs == 0] = "dot"
    out[runs == 1] = "single"
    out[runs == 2] = "two"
    out[runs == 3] = "three"
    out[runs == 4] = "four"
    out[runs == 6] = "six"
    out[legbyes > 0] = "legbye"
    out[byes > 0] = "bye"
    out[nbs > 0] = "noball"
    out[wides > 0] = "wide"
    out[is_wkt] = "wicket"
    return out


def _fit_outcome_probs(train_df: pd.DataFrame) -> Tuple[Dict[Tuple[int, str, str], np.ndarray], Dict[str, float]]:
    """Fit Laplace-smoothed outcome probability table P(e | innings, phase, format) and mean runs per extra."""
    cats = list(OUTCOME_CATS)
    outcomes = classify_delivery_outcome(train_df)
    tmp = pd.DataFrame(
        {
            "innings": train_df["innings"].values.astype(int),
            "phase": train_df["innings_phase"].astype(str).values,
            "format": train_df["match_format"].astype(str).values,
            "outcome": outcomes,
            "runs": train_df["actual_total_runs"].values,
        }
    )
    prob_map: Dict[Tuple[int, str, str], np.ndarray] = {}
    global_counts = pd.Series(outcomes).value_counts().reindex(cats, fill_value=0).values.astype(float) + 1.0
    global_probs = global_counts / global_counts.sum()

    for (inn, ph, fmt), grp in tmp.groupby(["innings", "phase", "format"]):
        cnts = grp["outcome"].value_counts().reindex(cats, fill_value=0).values.astype(float) + 0.5
        prob_map[(int(inn), str(ph), str(fmt))] = cnts / cnts.sum()
    prob_map[(-1, "default", "default")] = global_probs

    mean_runs = {}
    for c in cats:
        sub = tmp.loc[tmp["outcome"] == c, "runs"]
        mean_runs[c] = float(sub.mean()) if len(sub) > 0 else 1.0
    # Fix standard discrete bat outcomes
    mean_runs.update({"dot": 0.0, "single": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "six": 6.0, "wicket": 0.0})
    return prob_map, mean_runs


def _wp_after_outcome(
    sub_df: pd.DataFrame,
    inn: int,
    model_bundle: Dict[str, Any],
    run_inc: float,
    legal_inc: int,
    wkt_inc: int,
) -> np.ndarray:
    """Compute WP_after (in inn1_team perspective) after applying exact state transition."""
    mod = sub_df.copy()
    mod["current_score_before"] = mod["current_score_before"] + run_inc
    mod["legal_balls_before"] = mod["legal_balls_before"] + legal_inc
    mod["balls_rem_before"] = np.maximum(mod["sched_balls"] - mod["legal_balls_before"], 0.0)
    mod["wkts_before"] = np.minimum(mod["wkts_before"] + wkt_inc, 10)
    mod["wkts_rem_before"] = 10 - mod["wkts_before"]

    lb = mod["legal_balls_before"].values.astype(float)
    mod["crr"] = np.divide(
        mod["current_score_before"].values,
        lb / 6.0,
        out=np.full(len(mod), 7.5, dtype=float),
        where=lb > 0,
    )

    er_st = model_bundle["er_state"]
    sc = model_bundle["scaler"]
    clf = model_bundle["clf"]

    if inn == 1:
        er_p, par_p, fac_p = predict_total_er(mod, er_st)
        term = (mod["balls_rem_before"].values <= 0) | (mod["wkts_rem_before"].values <= 0)
        er_p[term] = 0.0
        X = build_inn1_score_wp_features(mod, er_p, par_p, fac_p)
        p_inn1 = np.clip(clf.predict_proba(sc.transform(X))[:, 1], 1e-6, 1.0 - 1e-6)
        return p_inn1
    else:
        mod["runs_required"] = np.maximum(mod["verified_target"] - mod["current_score_before"], 0.0)
        br = np.maximum(mod["balls_rem_before"].values, 1.0)
        mod["rrr"] = np.clip(mod["runs_required"].values / (br / 6.0), 0.0, 36.0)
        _, _, fac_p = predict_total_er(mod, er_st)
        X = build_inn2_score_wp_features(mod, fac_p)
        p_chase = np.clip(clf.predict_proba(sc.transform(X))[:, 1], 1e-6, 1.0 - 1e-6)
        # Terminal chase rules: target reached -> chasing wins (inn1_wp = 0); all out / balls=0 & runs_req>0 -> inn1_wp = 1
        p_inn1 = 1.0 - p_chase
        won_chase = mod["current_score_before"].values >= mod["verified_target"].values
        lost_chase = ((mod["balls_rem_before"].values <= 0) | (mod["wkts_rem_before"].values <= 0)) & (~won_chase)
        p_inn1[won_chase] = 0.0
        p_inn1[lost_chase] = 1.0
        return p_inn1


def compute_track_a_leverage_index(
    wp_res: Dict[str, Any],
    cfg: V44Config = DEFAULT_V44_CONFIG,
) -> Dict[str, Any]:
    """Compute fold-isolated RawL_t = E[|WP_after - WP_before| | state_before] and normalized LI_t."""
    cfg.ensure_dirs()
    valid = wp_res["valid_df"].copy().reset_index(drop=True)
    fold_models = wp_res["fold_models"]

    raw_l = np.zeros(len(valid), dtype=float)
    wp_before = valid["wp_inn1_team_oof"].values

    for inn in (1, 2):
        sub_mask = (valid["innings"].values == inn)
        sub = valid[sub_mask].copy().reset_index(drop=True)
        sub_indices = np.where(sub_mask)[0]
        gkf = GroupKFold(n_splits=cfg.n_cv_folds)

        for fold_idx, (tr_idx, te_idx) in enumerate(gkf.split(sub, groups=sub["match_id"]), start=1):
            tr_f = sub.iloc[tr_idx]
            te_f = sub.iloc[te_idx]
            prob_map, mean_runs = _fit_outcome_probs(tr_f)
            mb = fold_models[(inn, fold_idx)]

            # Lookup P(e | state) for each test row
            keys = list(
                zip(
                    te_f["innings"].astype(int),
                    te_f["innings_phase"].astype(str),
                    te_f["match_format"].astype(str),
                )
            )
            default_p = prob_map[(-1, "default", "default")]
            p_mat = np.vstack([prob_map.get(k, default_p) for k in keys])

            wb = wp_before[sub_indices[te_idx]]
            expected_swing = np.zeros(len(te_f), dtype=float)

            for c_idx, cat in enumerate(OUTCOME_CATS):
                r_inc = mean_runs[cat]
                l_inc = 0 if cat in ("wide", "noball") else 1
                w_inc = 1 if cat == "wicket" else 0
                wp_aft = _wp_after_outcome(te_f, inn, mb, r_inc, l_inc, w_inc)
                expected_swing += p_mat[:, c_idx] * np.abs(wp_aft - wb)

            raw_l[sub_indices[te_idx]] = expected_swing

    valid["raw_expected_wp_swing"] = raw_l
    mean_raw_ref = float(np.mean(raw_l))
    valid["leverage_index"] = raw_l / max(mean_raw_ref, 1e-9)

    # Realized next-ball WP swing for diagnostic validation
    valid["wp_after_actual"] = valid.groupby(["match_id", "innings"])["wp_inn1_team_oof"].shift(-1)
    valid["realized_wp_swing"] = np.abs(valid["wp_after_actual"] - valid["wp_inn1_team_oof"])

    # Save distribution summary
    dist_rows: List[Dict[str, Any]] = []
    for grp_name, grp in [
        ("ALL_VERIFIED", valid),
        ("Innings_1", valid[valid["innings"] == 1]),
        ("Innings_2", valid[valid["innings"] == 2]),
        ("Format_T20", valid[valid["match_format"] == "T20"]),
        ("Format_T20I", valid[valid["match_format"] == "T20I"]),
    ]:
        dist_rows.append(
            {
                "cohort": grp_name,
                "n_deliveries": int(len(grp)),
                "mean_raw_wp_swing": round(float(grp["raw_expected_wp_swing"].mean()), 6),
                "mean_li": round(float(grp["leverage_index"].mean()), 4),
                "median_li": round(float(grp["leverage_index"].median()), 4),
                "p75_li": round(float(grp["leverage_index"].quantile(0.75)), 4),
                "p90_li": round(float(grp["leverage_index"].quantile(0.90)), 4),
                "share_li_ge_1_50": round(float((grp["leverage_index"] >= 1.50).mean()), 4),
            }
        )
    dist_df = pd.DataFrame(dist_rows)
    dist_df.to_csv(cfg.output_dir / "V4_4_LEVERAGE_DISTRIBUTION.csv", index=False)

    # Threshold comparison (1.00, 1.25, 1.50, 1.75, 2.00, Top 25%)
    p75_cut = float(valid["leverage_index"].quantile(0.75))
    thresh_rows: List[Dict[str, Any]] = []
    for label, mask in [
        ("LI >= 1.00", valid["leverage_index"] >= 1.00),
        ("LI >= 1.25", valid["leverage_index"] >= 1.25),
        ("LI >= 1.50", valid["leverage_index"] >= 1.50),
        ("LI >= 1.75", valid["leverage_index"] >= 1.75),
        ("LI >= 2.00", valid["leverage_index"] >= 2.00),
        (f"Top 25% (LI >= {p75_cut:.3f})", valid["leverage_index"] >= p75_cut),
    ]:
        sub_t = valid[mask]
        bo = pd.to_numeric(sub_t["batting_order"], errors="coerce")
        thresh_rows.append(
            {
                "threshold": label,
                "n_deliveries": int(len(sub_t)),
                "coverage_pct": round(100.0 * len(sub_t) / len(valid), 2),
                "wicket_rate_pct": round(100.0 * sub_t["wicket_inc"].mean(), 3),
                "mean_realized_wp_swing": round(float(sub_t["realized_wp_swing"].mean()), 5),
                "top_order_1_3_pct": round(100.0 * (bo <= 3).mean(), 2),
                "middle_order_4_6_pct": round(100.0 * ((bo >= 4) & (bo <= 6)).mean(), 2),
                "lower_order_7_11_pct": round(100.0 * (bo >= 7).mean(), 2),
            }
        )
    thresh_df = pd.DataFrame(thresh_rows)
    thresh_df.to_csv(cfg.output_dir / "V4_4_LEVERAGE_THRESHOLDS.csv", index=False)

    return {
        "valid_df": valid,
        "dist_df": dist_df,
        "thresh_df": thresh_df,
        "mean_raw_ref": mean_raw_ref,
    }
