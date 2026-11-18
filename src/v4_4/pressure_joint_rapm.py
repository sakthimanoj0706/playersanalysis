"""Track A: Pressure-Interaction Joint Batter-Bowler Ridge RAPM on DeltaRE_total for V4.4."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import kendalltau, pearsonr, rankdata, spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import GroupKFold

from src.v4_4.config import DEFAULT_V44_CONFIG, V44Config

ALPHA_GRID: Tuple[float, ...] = (50.0, 100.0, 150.0, 250.0, 400.0, 600.0, 1000.0, 1500.0)


def build_pressure_rapm_design(
    df: pd.DataFrame,
    pressure_mode: str = "continuous_li",
) -> Dict[str, Any]:
    """
    Build sparse design matrix with batter/bowler main effects, context controls,
    and batter/bowler pressure interaction terms.
    """
    n = len(df)
    batter_ids = np.sort(df["striker_id"].dropna().unique())
    bowler_ids = np.sort(df["bowler_id"].dropna().unique())
    seasons_all = sorted(df["season"].astype(str).unique().tolist())
    season_levels = seasons_all[1:]

    bat_map = {pid: i for i, pid in enumerate(batter_ids)}
    bowl_map = {pid: i for i, pid in enumerate(bowler_ids)}

    bat_idx = df["striker_id"].map(bat_map)
    vb = bat_idx.notna().values
    X_bat = sparse.csr_matrix(
        (np.ones(vb.sum()), (np.where(vb)[0], bat_idx[vb].astype(int).values)),
        shape=(n, len(batter_ids)),
    )

    bowl_idx = df["bowler_id"].map(bowl_map)
    vw = bowl_idx.notna().values
    X_bowl = sparse.csr_matrix(
        (np.ones(vw.sum()), (np.where(vw)[0], bowl_idx[vw].astype(int).values)),
        shape=(n, len(bowler_ids)),
    )

    if pressure_mode == "continuous_li":
        # Centered continuous LI: p = clip(LI, 0, 5) - 1.0 (0 at reference average LI=1.0)
        p_vec = np.clip(df["leverage_index"].values, 0.0, 5.0) - 1.0
    else:
        # Binary LI >= 1.50 sensitivity
        p_vec = (df["leverage_index"].values >= 1.50).astype(float)

    X_bat_p = X_bat.multiply(p_vec[:, None]).tocsr()
    X_bowl_p = X_bowl.multiply(p_vec[:, None]).tocsr()

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
        p_vec,
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
    s_col = df["season"].astype(str).values
    for s in season_levels:
        ctrl_cols.append((s_col == s).astype(float))

    X_ctrl = sparse.csr_matrix(np.column_stack(ctrl_cols))
    X = sparse.hstack([X_bat, X_bowl, X_bat_p, X_bowl_p, X_ctrl], format="csr")

    return {
        "X": X,
        "y": df["delta_re_player_attrib"].values.astype(float),
        "batter_ids": batter_ids,
        "bowler_ids": bowler_ids,
        "n_bat": len(batter_ids),
        "n_bowl": len(bowler_ids),
        "pressure_mode": pressure_mode,
    }


def _extract_effects(coef: np.ndarray, n_bat: int, n_bowl: int) -> Dict[str, np.ndarray]:
    b_main = (coef[:n_bat] - np.mean(coef[:n_bat])) * 100.0
    w_main = -(coef[n_bat : n_bat + n_bowl] - np.mean(coef[n_bat : n_bat + n_bowl])) * 100.0
    b_pres = coef[n_bat + n_bowl : 2 * n_bat + n_bowl] * 100.0
    w_pres = -coef[2 * n_bat + n_bowl : 2 * n_bat + 2 * n_bowl] * 100.0
    return {
        "bat_main": b_main,
        "bowl_main": w_main,
        "bat_pres": b_pres,
        "bowl_pres": w_pres,
    }


def run_track_a_pressure_joint_rapm(
    df_trv: pd.DataFrame,
    cfg: V44Config = DEFAULT_V44_CONFIG,
    n_boot: int = 150,
    n_splits: int = 10,
) -> Dict[str, Any]:
    """Fit and validate Track A pressure-interaction joint Ridge RAPM."""
    cfg.ensure_dirs()
    df = df_trv.copy().reset_index(drop=True)
    design = build_pressure_rapm_design(df, pressure_mode="continuous_li")
    X, y = design["X"], design["y"]
    groups = df["match_id"].values

    # 1. Tune alpha via 5-fold match-grouped CV
    gkf = GroupKFold(n_splits=cfg.n_cv_folds)
    tune_rows: List[Dict[str, Any]] = []
    for alpha in ALPHA_GRID:
        oof = np.zeros(len(df), dtype=float)
        for tr_idx, te_idx in gkf.split(X, y, groups=groups):
            m = Ridge(alpha=alpha, fit_intercept=True, solver="lsqr", tol=1e-4, random_state=cfg.random_seed)
            m.fit(X[tr_idx], y[tr_idx])
            oof[te_idx] = m.predict(X[te_idx])
        rmse = float(root_mean_squared_error(y, oof))
        mae = float(mean_absolute_error(y, oof))
        tune_rows.append({"alpha": alpha, "cv_mse": round(rmse ** 2, 6), "cv_rmse": round(rmse, 6), "cv_mae": round(mae, 6), "is_optimal": False})

    tune_df = pd.DataFrame(tune_rows)
    best_idx = int(tune_df["cv_mse"].idxmin())
    tune_df.loc[best_idx, "is_optimal"] = True
    best_alpha = float(tune_df.loc[best_idx, "alpha"])
    tune_df.to_csv(cfg.output_dir / "V4_4_RAPM_ALPHA_TUNING.csv", index=False)

    # 2. Fit primary continuous-LI model & binary LI>=1.50 sensitivity
    model = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-5, random_state=cfg.random_seed).fit(X, y)
    eff = _extract_effects(model.coef_, design["n_bat"], design["n_bowl"])

    design_bin = build_pressure_rapm_design(df, pressure_mode="binary_1_50")
    model_bin = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-5, random_state=cfg.random_seed).fit(design_bin["X"], design_bin["y"])
    eff_bin = _extract_effects(model_bin.coef_, design_bin["n_bat"], design_bin["n_bowl"])

    # 3. Match-cluster bootstrap (B=150)
    m_groups = df.groupby("match_id", sort=False).indices
    idx_lists = [m_groups[k] for k in m_groups]
    n_m = len(idx_lists)
    n_bat, n_bowl = design["n_bat"], design["n_bowl"]
    b_main_boot = np.empty((n_boot, n_bat))
    b_pres_boot = np.empty((n_boot, n_bat))
    w_main_boot = np.empty((n_boot, n_bowl))
    w_pres_boot = np.empty((n_boot, n_bowl))

    rng = np.random.default_rng(cfg.random_seed)
    for b in range(n_boot):
        chosen = rng.integers(0, n_m, size=n_m)
        r_idx = np.concatenate([idx_lists[i] for i in chosen])
        mb = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-4, random_state=cfg.random_seed).fit(X[r_idx], y[r_idx])
        eb = _extract_effects(mb.coef_, n_bat, n_bowl)
        b_main_boot[b], b_pres_boot[b] = eb["bat_main"], eb["bat_pres"]
        w_main_boot[b], w_pres_boot[b] = eb["bowl_main"], eb["bowl_pres"]

    # Build batter & bowler tables + apply 100/300/12 gate AFTER fitting
    bat_names = df.groupby("striker_id")["striker_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()
    df["is_hi_li_150"] = (df["leverage_index"] >= 1.50).astype(int)
    bat_exp = df.groupby("striker_id", as_index=False).agg(
        total_balls=("is_ball_faced", "sum"),
        legal_balls=("legal_ball_inc", "sum"),
        matches=("match_id", "nunique"),
        n_hi_li_150=("is_hi_li_150", "sum"),
        mean_li=("leverage_index", "mean"),
    ).rename(columns={"striker_id": "player_id"})

    bat_df = pd.DataFrame(
        {
            "player_id": design["batter_ids"],
            "rapm_main_per100": eff["bat_main"],
            "rapm_pressure_slope_per100": eff["bat_pres"],
            "rapm_combined_at_li_150": eff["bat_main"] + 0.5 * eff["bat_pres"],
            "rapm_binary_150_pressure": eff_bin["bat_pres"],
            "boot_se_main": np.std(b_main_boot, axis=0, ddof=1),
            "boot_se_pressure": np.std(b_pres_boot, axis=0, ddof=1),
            "ci_low_main": np.percentile(b_main_boot, 2.5, axis=0),
            "ci_high_main": np.percentile(b_main_boot, 97.5, axis=0),
            "ci_low_pressure": np.percentile(b_pres_boot, 2.5, axis=0),
            "ci_high_pressure": np.percentile(b_pres_boot, 97.5, axis=0),
        }
    ).merge(bat_exp, on="player_id", how="left")
    bat_df["player_name"] = bat_df["player_id"].map(bat_names)
    bat_df["eligible_100_300_12"] = (
        (bat_df["n_hi_li_150"] >= 100) & (bat_df["total_balls"] >= 300) & (bat_df["matches"] >= 12)
    )
    el_b = bat_df["eligible_100_300_12"].values
    bat_df["rank_main"] = np.nan
    bat_df["rank_pressure"] = np.nan
    if el_b.sum() > 0:
        bat_df.loc[el_b, "rank_main"] = rankdata(-bat_df.loc[el_b, "rapm_main_per100"].values, method="average")
        bat_df.loc[el_b, "rank_pressure"] = rankdata(-bat_df.loc[el_b, "rapm_pressure_slope_per100"].values, method="average")

    bowl_names = df.groupby("bowler_id")["bowler_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()
    bowl_exp = df.groupby("bowler_id", as_index=False).agg(
        total_balls=("legal_ball_inc", "sum"),
        deliveries_bowled=("delta_re_total", "size"),
        matches=("match_id", "nunique"),
        n_hi_li_150=("is_hi_li_150", "sum"),
        mean_li=("leverage_index", "mean"),
        bowler_credited_wickets=("is_bowler_wicket", "sum"),
    ).rename(columns={"bowler_id": "player_id"})

    bowl_df = pd.DataFrame(
        {
            "player_id": design["bowler_ids"],
            "rapm_defensive_main_per100": eff["bowl_main"],
            "rapm_pressure_slope_per100": eff["bowl_pres"],
            "rapm_combined_at_li_150": eff["bowl_main"] + 0.5 * eff["bowl_pres"],
            "rapm_binary_150_pressure": eff_bin["bowl_pres"],
            "boot_se_main": np.std(w_main_boot, axis=0, ddof=1),
            "boot_se_pressure": np.std(w_pres_boot, axis=0, ddof=1),
            "ci_low_main": np.percentile(w_main_boot, 2.5, axis=0),
            "ci_high_main": np.percentile(w_main_boot, 97.5, axis=0),
            "ci_low_pressure": np.percentile(w_pres_boot, 2.5, axis=0),
            "ci_high_pressure": np.percentile(w_pres_boot, 97.5, axis=0),
        }
    ).merge(bowl_exp, on="player_id", how="left")
    bowl_df["player_name"] = bowl_df["player_id"].map(bowl_names)
    bowl_df["eligible_100_300_12"] = (
        (bowl_df["n_hi_li_150"] >= 100) & (bowl_df["total_balls"] >= 300) & (bowl_df["matches"] >= 12)
    )
    el_w = bowl_df["eligible_100_300_12"].values
    bowl_df["rank_main"] = np.nan
    bowl_df["rank_pressure"] = np.nan
    if el_w.sum() > 0:
        bowl_df.loc[el_w, "rank_main"] = rankdata(-bowl_df.loc[el_w, "rapm_defensive_main_per100"].values, method="average")
        bowl_df.loc[el_w, "rank_pressure"] = rankdata(-bowl_df.loc[el_w, "rapm_pressure_slope_per100"].values, method="average")

    bat_df = bat_df.sort_values(["eligible_100_300_12", "rapm_main_per100"], ascending=[False, False]).reset_index(drop=True)
    bowl_df = bowl_df.sort_values(["eligible_100_300_12", "rapm_defensive_main_per100"], ascending=[False, False]).reset_index(drop=True)
    bat_df.to_csv(cfg.output_dir / "V4_4_BATTER_RAPM.csv", index=False)
    bowl_df.to_csv(cfg.output_dir / "V4_4_BOWLER_RAPM.csv", index=False)

    # Pressure interactions sensitivity summary
    pres_rows = []
    for role, rdf in [("batter", bat_df[bat_df["eligible_100_300_12"]]), ("bowler", bowl_df[bowl_df["eligible_100_300_12"]])]:
        sp_bin, _ = spearmanr(rdf["rapm_pressure_slope_per100"], rdf["rapm_binary_150_pressure"])
        pres_rows.append(
            {
                "role": role,
                "n_eligible_100_300_12": int(len(rdf)),
                "cont_vs_binary_150_spearman": round(float(sp_bin), 4),
                "median_se_main": round(float(rdf["boot_se_main"].median()), 4),
                "median_se_pressure": round(float(rdf["boot_se_pressure"].median()), 4),
            }
        )
    pres_df = pd.DataFrame(pres_rows)
    pres_df.to_csv(cfg.output_dir / "V4_4_PRESSURE_INTERACTIONS.csv", index=False)

    # 4. Split-half reliability on eligible players
    el_bat_mask = np.isin(design["batter_ids"], bat_df.loc[bat_df["eligible_100_300_12"], "player_id"].values)
    el_bowl_mask = np.isin(design["bowler_ids"], bowl_df.loc[bowl_df["eligible_100_300_12"], "player_id"].values)
    sh_rows = []
    for s in range(n_splits):
        perm = rng.permutation(n_m)
        half = n_m // 2
        ia = np.concatenate([idx_lists[i] for i in perm[:half]])
        ib = np.concatenate([idx_lists[i] for i in perm[half:]])
        ma = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-4, random_state=cfg.random_seed).fit(X[ia], y[ia])
        mb = Ridge(alpha=best_alpha, fit_intercept=True, solver="lsqr", tol=1e-4, random_state=cfg.random_seed).fit(X[ib], y[ib])
        ea = _extract_effects(ma.coef_, n_bat, n_bowl)
        eb = _extract_effects(mb.coef_, n_bat, n_bowl)
        for role, k_main, k_pres, mask in [
            ("batter", "bat_main", "bat_pres", el_bat_mask),
            ("bowler", "bowl_main", "bowl_pres", el_bowl_mask),
        ]:
            sh_rows.append(
                {
                    "split": s + 1,
                    "role": role,
                    "main_spearman": float(spearmanr(ea[k_main][mask], eb[k_main][mask])[0]),
                    "pres_spearman": float(spearmanr(ea[k_pres][mask], eb[k_pres][mask])[0]),
                }
            )
    sh_df = pd.DataFrame(sh_rows)
    stab_df = sh_df.groupby("role", as_index=False).agg(
        main_split_half_spearman=("main_spearman", "mean"),
        pres_split_half_spearman=("pres_spearman", "mean"),
    )
    stab_df.to_csv(cfg.output_dir / "V4_4_RANKING_STABILITY.csv", index=False)

    # 5. Comparison with V4.2 and V4.3
    v42 = pd.read_csv("data/outputs/v4_2/V4_2_ALL_PLAYER_ESTIMATES.csv")
    v43_bat = pd.read_csv("data/outputs/v4_3/V4_3_BATTER_RAPM.csv")
    v43_bowl = pd.read_csv("data/outputs/v4_3/V4_3_BOWLER_RAPM.csv")

    comp_rows = []
    for role, u44, c44_main, c44_pres, u43, c43 in [
        ("batter", bat_df, "rapm_main_per100", "rapm_pressure_slope_per100", v43_bat, "rapm_batter_per100"),
        ("bowler", bowl_df, "rapm_defensive_main_per100", "rapm_pressure_slope_per100", v43_bowl, "rapm_bowler_defensive_per100"),
    ]:
        # V4.4 vs V4.3
        m43 = u44[u44["eligible_100_300_12"]].merge(u43[["player_id", c43]], on="player_id", how="inner")
        sp_43, _ = spearmanr(m43[c44_main], m43[c43])
        comp_rows.append(
            {
                "role": role,
                "comparison": "V4.4 Main RAPM (DeltaRE_total) vs V4.3 Main RAPM (DeltaRE_batter)",
                "common_n": int(len(m43)),
                "spearman_r": round(float(sp_43), 4),
            }
        )
        # V4.4 vs V4.2
        v42_el = v42[(v42["role"] == role) & (v42["eligible"] == True)]
        m42 = u44.merge(v42_el[["player_id", "eb_delta", "claim_a_general_skill_fe"]], on="player_id", how="inner")
        sp_skill, _ = spearmanr(m42[c44_main], m42["claim_a_general_skill_fe"])
        sp_pres, _ = spearmanr(m42[c44_pres], m42["eb_delta"])
        comp_rows.append(
            {
                "role": role,
                "comparison": "V4.4 Main RAPM vs V4.2 General Skill FE (Claim A)",
                "common_n": int(len(m42)),
                "spearman_r": round(float(sp_skill), 4),
            }
        )
        comp_rows.append(
            {
                "role": role,
                "comparison": "V4.4 LI Pressure Slope vs V4.2 Pressure Slope (EB Delta)",
                "common_n": int(len(m42)),
                "spearman_r": round(float(sp_pres), 4),
            }
        )

    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(cfg.output_dir / "V4_4_MODEL_COMPARISON.csv", index=False)

    return {
        "best_alpha": best_alpha,
        "tune_df": tune_df,
        "bat_df": bat_df,
        "bowl_df": bowl_df,
        "pres_df": pres_df,
        "stab_df": stab_df,
        "comp_df": comp_df,
    }
