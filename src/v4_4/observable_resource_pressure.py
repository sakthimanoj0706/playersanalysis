"""Track B: Experimental Observable Resource Pressure Bridge (V4.3 Score-Blind WP) for V4.4."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from src.v4_3.config import DEFAULT_CONFIG as V43_CFG
from src.v4_3.win_probability import compute_pre_match_elo
from src.v4_4.config import DEFAULT_V44_CONFIG, V44Config


def _obs_features_from_vals(
    balls_rem: np.ndarray,
    sched_balls: np.ndarray,
    wkts_rem: np.ndarray,
    is_t20i: np.ndarray,
    elo: np.ndarray,
    par_fac: np.ndarray,
) -> np.ndarray:
    u = np.clip(balls_rem / np.maximum(sched_balls, 1.0), 0.0, 1.0)
    w = np.clip(wkts_rem / 10.0, 0.0, 1.0)
    return np.column_stack([u, w, u * w, is_t20i, elo, par_fac])


def run_track_b_observable_resource_pressure(
    cfg: V44Config = DEFAULT_V44_CONFIG,
    n_boot: int = 100,
    n_splits: int = 10,
) -> Dict[str, Any]:
    """
    Experimental Track B bridge using V4.3 score-blind WP.
    Measures OBSERVABLE_RESOURCE_PRESSURE (wicket vs ball-consumption WP sensitivity
    without run-state or RRR) and fits OBSERVABLE_RESOURCE_PRESSURE_RAPM_BATTER_RUNS_ONLY.
    """
    cfg.ensure_dirs()
    df = pd.read_parquet(V43_CFG.output_dir / "V4_3_DELIVERY_VALUE_BATTER.parquet")
    matches = pd.read_csv(cfg.data_dir / "matches_ipl_t20i.csv")
    df = df.merge(
        matches[["match_id", "home_team_id", "away_team_id", "win_team_id", "first_inn_revised_overs", "second_inn_revised_overs"]],
        on="match_id",
        how="left",
    )
    df["match_date_dt"] = pd.to_datetime(df["match_date"], errors="coerce")
    rev1 = pd.to_numeric(df["first_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev2 = pd.to_numeric(df["second_inn_revised_overs"], errors="coerce").fillna(0.0)
    df["sched_balls"] = np.where(
        df["innings"] == 1,
        np.where(rev1 > 0, np.where(rev1 <= 20.0, rev1 * 6.0, rev1), 120.0),
        np.where(rev2 > 0, np.where(rev2 <= 20.0, rev2 * 6.0, rev2), 120.0),
    )
    inn1_team = df[df["innings"] == 1].groupby("match_id")["batting_team_id"].first().rename("inn1_batting_team_id")
    df = df.merge(inn1_team, on="match_id", how="left")
    df["inn1_team_won"] = np.where(
        df["win_team_id"].isna() | df["inn1_batting_team_id"].isna(),
        np.nan,
        (df["win_team_id"] == df["inn1_batting_team_id"]).astype(float),
    )
    df["batting_team_won"] = np.where(
        df["win_team_id"].isna(),
        np.nan,
        (df["win_team_id"] == df["batting_team_id"]).astype(float),
    )
    df = compute_pre_match_elo(df, V43_CFG)

    # 1. Cross-fitted score-blind WP sensitivity (Observable Resource Pressure)
    obs_rp = np.zeros(len(df), dtype=float)
    decided = df["inn1_team_won"].notna().values
    gkf = GroupKFold(n_splits=cfg.n_cv_folds)

    for inn in (1, 2):
        sub_m = (df["innings"].values == inn) & decided
        sub = df[sub_m].copy().reset_index(drop=True)
        sub_idx = np.where(sub_m)[0]
        y_m = (sub["inn1_team_won"] if inn == 1 else sub["batting_team_won"]).astype(int).values

        for tr_i, te_i in gkf.split(sub, groups=sub["match_id"]):
            tr_f, te_f = sub.iloc[tr_i], sub.iloc[te_i]
            X_tr = _obs_features_from_vals(
                tr_f["balls_rem_before"].values,
                tr_f["sched_balls"].values,
                tr_f["wkts_rem_before"].values,
                (tr_f["match_format"].values == "T20I").astype(float),
                tr_f["elo_diff_bat_minus_bowl"].fillna(0.0).values,
                tr_f["eb_venue_par_factor_oof"].fillna(1.0).values,
            )
            sc = StandardScaler()
            clf = LogisticRegression(C=0.5, max_iter=1000, random_state=cfg.random_seed).fit(sc.fit_transform(X_tr), y_m[tr_i])

            # Compute observable WP sensitivity: E[|WP(w_after) - WP(before)|] across wicket (p_wkt) vs dot/ball (1-p_wkt)
            p_wkt = float(tr_f["wicket_inc"].mean())
            is_t20i_te = (te_f["match_format"].values == "T20I").astype(float)
            elo_te = te_f["elo_diff_bat_minus_bowl"].fillna(0.0).values
            par_te = te_f["eb_venue_par_factor_oof"].fillna(1.0).values
            sb_te = te_f["sched_balls"].values
            br_te = te_f["balls_rem_before"].values
            wr_te = te_f["wkts_rem_before"].values

            X_bef = _obs_features_from_vals(br_te, sb_te, wr_te, is_t20i_te, elo_te, par_te)
            X_ball = _obs_features_from_vals(np.maximum(br_te - 1, 0), sb_te, wr_te, is_t20i_te, elo_te, par_te)
            X_wkt = _obs_features_from_vals(np.maximum(br_te - 1, 0), sb_te, np.maximum(wr_te - 1, 0), is_t20i_te, elo_te, par_te)

            wp_bef = clf.predict_proba(sc.transform(X_bef))[:, 1]
            wp_ball = clf.predict_proba(sc.transform(X_ball))[:, 1]
            wp_wkt = clf.predict_proba(sc.transform(X_wkt))[:, 1]

            obs_rp[sub_idx[te_i]] = (1.0 - p_wkt) * np.abs(wp_ball - wp_bef) + p_wkt * np.abs(wp_wkt - wp_bef)

    mean_rp = float(np.mean(obs_rp[decided])) if decided.sum() > 0 else 1.0
    df["OBSERVABLE_RESOURCE_PRESSURE"] = obs_rp / max(mean_rp, 1e-9)

    # 2. Fit OBSERVABLE_RESOURCE_PRESSURE_RAPM_BATTER_RUNS_ONLY on DeltaRE_batter
    valid = df[decided].copy().reset_index(drop=True)
    n = len(valid)
    batter_ids = np.sort(valid["striker_id"].dropna().unique())
    bowler_ids = np.sort(valid["bowler_id"].dropna().unique())
    bat_map = {p: i for i, p in enumerate(batter_ids)}
    bowl_map = {p: i for i, p in enumerate(bowler_ids)}

    bi = valid["striker_id"].map(bat_map)
    wi = valid["bowler_id"].map(bowl_map)
    X_bat = sparse.csr_matrix((np.ones(bi.notna().sum()), (np.where(bi.notna())[0], bi[bi.notna()].astype(int).values)), shape=(n, len(batter_ids)))
    X_bowl = sparse.csr_matrix((np.ones(wi.notna().sum()), (np.where(wi.notna())[0], wi[wi.notna()].astype(int).values)), shape=(n, len(bowler_ids)))

    p_vec = np.clip(valid["OBSERVABLE_RESOURCE_PRESSURE"].values, 0.0, 5.0) - 1.0
    X_bat_p = X_bat.multiply(p_vec[:, None]).tocsr()
    X_bowl_p = X_bowl.multiply(p_vec[:, None]).tocsr()
    X_ctrl = sparse.csr_matrix(
        np.column_stack(
            [
                p_vec,
                (valid["innings"].values == 2).astype(float),
                (valid["match_format"].values == "T20I").astype(float),
                (valid["innings_phase"].values == "middle").astype(float),
                (valid["innings_phase"].values == "death").astype(float),
                valid["elo_diff_bat_minus_bowl"].fillna(0.0).values,
                (valid["is_non_bowler_dismissal"] == True).astype(float).values,
            ]
        )
    )
    X = sparse.hstack([X_bat, X_bowl, X_bat_p, X_bowl_p, X_ctrl], format="csr")
    y = valid["delta_re_batter"].values.astype(float)

    n_bat, n_bowl = len(batter_ids), len(bowler_ids)
    m = Ridge(alpha=150.0, fit_intercept=True, solver="lsqr", tol=1e-5, random_state=cfg.random_seed).fit(X, y)
    c = m.coef_
    bat_main = (c[:n_bat] - np.mean(c[:n_bat])) * 100.0
    bowl_main = -(c[n_bat : n_bat + n_bowl] - np.mean(c[n_bat : n_bat + n_bowl])) * 100.0
    bat_rp = c[n_bat + n_bowl : 2 * n_bat + n_bowl] * 100.0
    bowl_rp = -c[2 * n_bat + n_bowl : 2 * n_bat + 2 * n_bowl] * 100.0

    # Data-driven percentile thresholds (P75, P80, P85) — never LI >= 1.50
    p75 = float(np.percentile(valid["OBSERVABLE_RESOURCE_PRESSURE"], 75))
    valid["is_hi_rp_p75"] = (valid["OBSERVABLE_RESOURCE_PRESSURE"] >= p75).astype(int)

    bat_names = valid.groupby("striker_id")["striker_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()
    bat_exp = valid.groupby("striker_id", as_index=False).agg(
        legal_balls=("legal_ball_inc", "sum"),
        matches=("match_id", "nunique"),
        n_hi_p75=("is_hi_rp_p75", "sum"),
    ).rename(columns={"striker_id": "player_id"})
    bat_out = pd.DataFrame(
        {
            "player_id": batter_ids,
            "obs_rp_main_per100": bat_main,
            "obs_rp_pressure_slope_per100": bat_rp,
            "model_label": "OBSERVABLE_RESOURCE_PRESSURE_RAPM_BATTER_RUNS_ONLY",
        }
    ).merge(bat_exp, on="player_id", how="left")
    bat_out["player_name"] = bat_out["player_id"].map(bat_names)
    bat_out["eligible_300b"] = bat_out["legal_balls"] >= 300
    bat_out.to_csv(cfg.output_dir / "V4_4_TRACK_B_RESOURCE_PRESSURE_BATTER.csv", index=False)

    bowl_names = valid.groupby("bowler_id")["bowler_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()
    bowl_exp = valid.groupby("bowler_id", as_index=False).agg(
        legal_balls=("legal_ball_inc", "sum"),
        matches=("match_id", "nunique"),
        n_hi_p75=("is_hi_rp_p75", "sum"),
    ).rename(columns={"bowler_id": "player_id"})
    bowl_out = pd.DataFrame(
        {
            "player_id": bowler_ids,
            "obs_rp_defensive_main_per100": bowl_main,
            "obs_rp_pressure_slope_per100": bowl_rp,
            "model_label": "OBSERVABLE_RESOURCE_PRESSURE_RAPM_BATTER_RUNS_ONLY",
        }
    ).merge(bowl_exp, on="player_id", how="left")
    bowl_out["player_name"] = bowl_out["player_id"].map(bowl_names)
    bowl_out["eligible_300b"] = bowl_out["legal_balls"] >= 300
    bowl_out.to_csv(cfg.output_dir / "V4_4_TRACK_B_RESOURCE_PRESSURE_BOWLER.csv", index=False)

    # Compare Track B with V4.2
    v42 = pd.read_csv("data/outputs/v4_2/V4_2_ALL_PLAYER_ESTIMATES.csv")
    comp_rows: List[Dict[str, Any]] = []
    for role, u_df, c_main, c_pres in [
        ("batter", bat_out, "obs_rp_main_per100", "obs_rp_pressure_slope_per100"),
        ("bowler", bowl_out, "obs_rp_defensive_main_per100", "obs_rp_pressure_slope_per100"),
    ]:
        v42_el = v42[(v42["role"] == role) & (v42["eligible"] == True)]
        m42 = u_df.merge(v42_el[["player_id", "eb_delta", "claim_a_general_skill_fe"]], on="player_id", how="inner")
        comp_rows.append(
            {
                "role": role,
                "comparison": "Track B Main vs V4.2 General Skill FE (Claim A)",
                "common_n": int(len(m42)),
                "spearman_r": round(float(spearmanr(m42[c_main], m42["claim_a_general_skill_fe"])[0]), 4),
            }
        )
        comp_rows.append(
            {
                "role": role,
                "comparison": "Track B Resource-Pressure Slope vs V4.2 Pressure Slope (EB Delta)",
                "common_n": int(len(m42)),
                "spearman_r": round(float(spearmanr(m42[c_pres], m42["eb_delta"])[0]), 4),
            }
        )
    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(cfg.output_dir / "V4_4_TRACK_B_COMPARISON.csv", index=False)

    return {"bat_out": bat_out, "bowl_out": bowl_out, "comp_df": comp_df, "p75_cutoff": p75}
