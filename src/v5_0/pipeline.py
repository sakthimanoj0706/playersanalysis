"""End-to-End Pipeline for SupeRR Intelligence V5.0 (Phases 0-10)."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, rankdata, spearmanr
from sklearn.metrics import mean_squared_error

from src.v4_3.config import DEFAULT_CONFIG as V43_CFG
from src.v4_3.win_probability import compute_pre_match_elo
from src.v5_0.asymmetric_pressure_rapm import (
    build_asymmetric_blocks,
    predict_block_ridge,
    solve_block_ridge,
    tune_asymmetric_ridge_cv,
)
from src.v5_0.config import DEFAULT_V50_CONFIG, V50Config
from src.v5_0.player_archetypes import classify_player_archetypes, save_archetype_quadrant_plot
from src.v5_0.pressure_scales import load_track_a_with_pressure_scales


def _compute_exposure(df: pd.DataFrame, hp_col: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Exact role-specific exposure accounting:
      - Batters: valid delivery opportunities faced (is_ball_faced)
      - Bowlers: valid delivery events bowled (all deliveries including wides/no-balls)
    """
    bat_names = df.groupby("striker_id")["striker_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()
    bowl_names = df.groupby("bowler_id")["bowler_name"].agg(lambda s: s.mode().iloc[0] if len(s) else "").to_dict()

    df_b = df[df["is_ball_faced"] == True]
    bat_exp = df.groupby("striker_id", as_index=False).agg(
        total_opportunities=("is_ball_faced", "sum"),
        matches=("match_id", "nunique"),
        n_hp_global=("H_global_150", lambda s: int(s[df.loc[s.index, "is_ball_faced"] == True].sum())),
        n_hp_innings=("H_innings_150", lambda s: int(s[df.loc[s.index, "is_ball_faced"] == True].sum())),
        ipl_balls=("match_format", lambda s: int((s == "T20").sum())),
        t20i_balls=("match_format", lambda s: int((s == "T20I").sum())),
    ).rename(columns={"striker_id": "player_id"})
    bat_hp_m = (
        df_b[df_b[hp_col] == 1]
        .groupby("striker_id")["match_id"]
        .nunique()
        .rename("m_hp")
        .reset_index()
        .rename(columns={"striker_id": "player_id"})
    )
    bat_exp = bat_exp.merge(bat_hp_m, on="player_id", how="left")
    bat_exp["m_hp"] = bat_exp["m_hp"].fillna(0).astype(int)
    bat_exp["player_name"] = bat_exp["player_id"].map(bat_names)

    bowl_exp = df.groupby("bowler_id", as_index=False).agg(
        total_opportunities=("delta_re_total", "size"),
        matches=("match_id", "nunique"),
        n_hp_global=("H_global_150", "sum"),
        n_hp_innings=("H_innings_150", "sum"),
        ipl_balls=("match_format", lambda s: int((s == "T20").sum())),
        t20i_balls=("match_format", lambda s: int((s == "T20I").sum())),
    ).rename(columns={"bowler_id": "player_id"})
    bowl_hp_m = (
        df[df[hp_col] == 1]
        .groupby("bowler_id")["match_id"]
        .nunique()
        .rename("m_hp")
        .reset_index()
        .rename(columns={"bowler_id": "player_id"})
    )
    bowl_exp = bowl_exp.merge(bowl_hp_m, on="player_id", how="left")
    bowl_exp["m_hp"] = bowl_exp["m_hp"].fillna(0).astype(int)
    bowl_exp["player_name"] = bowl_exp["player_id"].map(bowl_names)
    return bat_exp, bowl_exp


def _run_innings_split_models(
    df: pd.DataFrame,
    alpha_main: float,
    alpha_int: float,
    cfg: V50Config,
) -> pd.DataFrame:
    """Estimate separate Innings 1 and Innings 2 player effects under LI_global and LI_innings."""
    rows: List[pd.DataFrame] = []
    for scale_label, hp_col in [("LI_global", "H_global_150"), ("LI_innings", "H_innings_150")]:
        for inn in (1, 2):
            sub = df[df["innings"] == inn].copy().reset_index(drop=True)
            blocks = build_asymmetric_blocks(sub, pressure_col=hp_col)
            fit = solve_block_ridge(blocks, alpha_main, alpha_int, cfg.alpha_context, cfg.random_seed)

            bat_sub_b = sub[sub["is_ball_faced"] == True]
            b_exp = bat_sub_b.groupby("striker_id", as_index=False).agg(
                n_total=("is_ball_faced", "size"),
                n_hp=(hp_col, "sum"),
                m_hp=("match_id", lambda s: int(s[bat_sub_b.loc[s.index, hp_col] == 1].nunique())),
            ).rename(columns={"striker_id": "player_id"})
            b_df = pd.DataFrame(
                {
                    "player_id": blocks["batter_ids"],
                    "role": "batter",
                    "innings": inn,
                    "scale": scale_label,
                    "main_effect": fit["bat_main"],
                    "pressure_uplift": fit["bat_pres"],
                    "hp_effect": fit["bat_hp"],
                }
            ).merge(b_exp, on="player_id", how="left")

            w_exp = sub.groupby("bowler_id", as_index=False).agg(
                n_total=("delta_re_total", "size"),
                n_hp=(hp_col, "sum"),
                m_hp=("match_id", lambda s: int(s[sub.loc[s.index, hp_col] == 1].nunique())),
            ).rename(columns={"bowler_id": "player_id"})
            w_df = pd.DataFrame(
                {
                    "player_id": blocks["bowler_ids"],
                    "role": "bowler",
                    "innings": inn,
                    "scale": scale_label,
                    "main_effect": fit["bowl_main"],
                    "pressure_uplift": fit["bowl_pres"],
                    "hp_effect": fit["bowl_hp"],
                }
            ).merge(w_exp, on="player_id", how="left")

            part = pd.concat([b_df, w_df], ignore_index=True)
            part["innings_eligible"] = (
                (part["n_hp"] >= cfg.min_inn_hp_opportunities)
                & (part["n_total"] >= cfg.min_inn_total_opportunities)
                & (part["m_hp"] >= cfg.min_inn_hp_matches)
            )
            rows.append(part)

    res = pd.concat(rows, ignore_index=True)
    # Attach player names
    names = pd.concat(
        [
            df[["striker_id", "striker_name"]].rename(columns={"striker_id": "player_id", "striker_name": "player_name"}),
            df[["bowler_id", "bowler_name"]].rename(columns={"bowler_id": "player_id", "bowler_name": "player_name"}),
        ]
    ).drop_duplicates("player_id")
    res = res.merge(names, on="player_id", how="left")
    return res


def run_v5_0_pipeline(cfg: V50Config = DEFAULT_V50_CONFIG) -> Dict[str, Any]:
    """Execute complete V5.0 pipeline (Phases 0-10) and save all required deliverables."""
    cfg.ensure_dirs()
    df, counts = load_track_a_with_pressure_scales(cfg)
    df = compute_pre_match_elo(df, V43_CFG)

    df["H_global_150"] = (df["LI_global"] >= cfg.li_global_hp_threshold).astype(int)
    df["H_innings_150"] = (df["LI_innings"] >= cfg.li_global_hp_threshold).astype(int)
    df["LI_global_centered"] = np.clip(df["LI_global"].values, 0.0, 5.0) - 1.0

    # Save reproducibility config
    (cfg.artifacts_dir / "v5_0_reproducibility_config.json").write_text(
        json.dumps(
            {
                "random_seed": cfg.random_seed,
                "supported_formats": list(cfg.supported_formats),
                "alpha_main_grid": list(cfg.alpha_main_grid),
                "alpha_int_grid": list(cfg.alpha_int_grid),
                "alpha_context": cfg.alpha_context,
                "li_global_hp_threshold": cfg.li_global_hp_threshold,
                "gate_global": [cfg.min_hp_opportunities, cfg.min_total_opportunities, cfg.min_hp_matches],
                "gate_innings": [cfg.min_inn_hp_opportunities, cfg.min_inn_total_opportunities, cfg.min_inn_hp_matches],
                "n_bootstrap": cfg.n_bootstrap,
                "n_split_half": cfg.n_split_half,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Phase 1: Asymmetric Ridge Alpha Tuning (5-fold CV + 1-SE rule)
    sel_main, sel_int, tune_df = tune_asymmetric_ridge_cv(df, cfg, pressure_col="H_global_150")

    # Chronological OOT (> 2024) validation
    tr_oot = df[df["year"] <= cfg.oot_cutoff_year]
    te_oot = df[df["year"] > cfg.oot_cutoff_year]
    b_tr_o = build_asymmetric_blocks(tr_oot, "H_global_150")
    b_te_o = build_asymmetric_blocks(te_oot, "H_global_150", b_tr_o["batter_ids"], b_tr_o["bowler_ids"], b_tr_o["season_levels"], b_tr_o["cont_stats"])
    f_oot = solve_block_ridge(b_tr_o, sel_main, sel_int, cfg.alpha_context, cfg.random_seed)
    p_oot = predict_block_ridge(b_te_o, f_oot)
    oot_mse = float(mean_squared_error(b_te_o["y"], p_oot))
    oot_rmse = float(np.sqrt(oot_mse))

    # Full-data Global HP Model (Binary H_global_150) + Continuous LI sensitivity
    blocks = build_asymmetric_blocks(df, "H_global_150")
    fit_bin = solve_block_ridge(blocks, sel_main, sel_int, cfg.alpha_context, cfg.random_seed)

    blocks_cont = build_asymmetric_blocks(df, "LI_global_centered", blocks["batter_ids"], blocks["bowler_ids"], blocks["season_levels"])
    fit_cont = solve_block_ridge(blocks_cont, sel_main, sel_int, cfg.alpha_context, cfg.random_seed)

    # Phase 4: Paired Match-Cluster Bootstrap (B=200) for theta_main, delta_pressure, AND theta_HP
    m_groups = df.groupby("match_id", sort=False).indices
    idx_lists = [m_groups[k] for k in m_groups]
    n_m = len(idx_lists)
    n_bat, n_bowl = blocks["n_bat"], blocks["n_bowl"]

    b_main_boot = np.empty((cfg.n_bootstrap, n_bat))
    b_pres_boot = np.empty((cfg.n_bootstrap, n_bat))
    b_hp_boot = np.empty((cfg.n_bootstrap, n_bat))
    w_main_boot = np.empty((cfg.n_bootstrap, n_bowl))
    w_pres_boot = np.empty((cfg.n_bootstrap, n_bowl))
    w_hp_boot = np.empty((cfg.n_bootstrap, n_bowl))

    rng = np.random.default_rng(cfg.random_seed)
    X_m, X_p, X_c, y_all = blocks["X_main"], blocks["X_pressure"], blocks["X_context"], blocks["y"]
    for b in range(cfg.n_bootstrap):
        chosen = rng.integers(0, n_m, size=n_m)
        r_idx = np.concatenate([idx_lists[i] for i in chosen])
        sub_b = {
            "X_main": X_m[r_idx],
            "X_pressure": X_p[r_idx],
            "X_context": X_c[r_idx],
            "y": y_all[r_idx],
            "n_bat": n_bat,
            "n_bowl": n_bowl,
        }
        fb = solve_block_ridge(sub_b, sel_main, sel_int, cfg.alpha_context, cfg.random_seed, tol=1e-4)
        b_main_boot[b], b_pres_boot[b], b_hp_boot[b] = fb["bat_main"], fb["bat_pres"], fb["bat_hp"]
        w_main_boot[b], w_pres_boot[b], w_hp_boot[b] = fb["bowl_main"], fb["bowl_pres"], fb["bowl_hp"]

    # Exposure & Innings Split
    bat_exp, bowl_exp = _compute_exposure(df, "H_global_150")
    inn_split = _run_innings_split_models(df, sel_main, sel_int, cfg)
    inn_split.to_csv(cfg.output_dir / "V5_0_INNINGS_SPLIT_RANKINGS.csv", index=False)

    # Assemble Global Leaderboards + Paired Bootstrap CIs + Archetypes
    boot_rows: List[pd.DataFrame] = []
    role_tables: Dict[str, pd.DataFrame] = {}

    for role, pids, exp_df, m_eff, p_eff, hp_eff, c_eff, mb, pb, hpb in [
        ("batter", blocks["batter_ids"], bat_exp, fit_bin["bat_main"], fit_bin["bat_pres"], fit_bin["bat_hp"], fit_cont["bat_pres"], b_main_boot, b_pres_boot, b_hp_boot),
        ("bowler", blocks["bowler_ids"], bowl_exp, fit_bin["bowl_main"], fit_bin["bowl_pres"], fit_bin["bowl_hp"], fit_cont["bowl_pres"], w_main_boot, w_pres_boot, w_hp_boot),
    ]:
        t = pd.DataFrame(
            {
                "player_id": pids,
                "role": role,
                "main_effect_per100": m_eff,
                "pressure_interaction_per100": p_eff,
                "combined_hp_per100": hp_eff,
                "cont_li_pressure_slope_per100": c_eff,
                "se_main": np.std(mb, axis=0, ddof=1),
                "ci_low_main": np.percentile(mb, 2.5, axis=0),
                "ci_high_main": np.percentile(mb, 97.5, axis=0),
                "se_pres": np.std(pb, axis=0, ddof=1),
                "ci_low_pres": np.percentile(pb, 2.5, axis=0),
                "ci_high_pres": np.percentile(pb, 97.5, axis=0),
                "se_hp": np.std(hpb, axis=0, ddof=1),
                "ci_low_hp": np.percentile(hpb, 2.5, axis=0),
                "ci_high_hp": np.percentile(hpb, 97.5, axis=0),
            }
        ).merge(exp_df, on="player_id", how="left")

        t["eligible"] = (
            (t["n_hp_global"] >= cfg.min_hp_opportunities)
            & (t["total_opportunities"] >= cfg.min_total_opportunities)
            & (t["m_hp"] >= cfg.min_hp_matches)
        )
        t["reliability"] = np.where(
            t["n_hp_global"] >= 250,
            "HIGH",
            np.where(t["eligible"], "MODERATE", "LOW_UNRANKED"),
        )
        t["rank_hp"] = np.nan
        t["rank_ci_low"] = np.nan
        t["rank_ci_high"] = np.nan
        t["prob_top_10"] = 0.0
        t["prob_top_20"] = 0.0

        el = t["eligible"].values
        if el.sum() > 0:
            t.loc[el, "rank_hp"] = rankdata(-np.round(t.loc[el, "combined_hp_per100"].values, 10), method="average")
            el_hpb = hpb[:, el]
            r_mat = np.apply_along_axis(lambda r: rankdata(-np.round(r, 10), method="average"), 1, el_hpb)
            t.loc[el, "rank_ci_low"] = np.percentile(r_mat, 2.5, axis=0)
            t.loc[el, "rank_ci_high"] = np.percentile(r_mat, 97.5, axis=0)
            t.loc[el, "prob_top_10"] = np.mean(r_mat <= 10.0, axis=0)
            t.loc[el, "prob_top_20"] = np.mean(r_mat <= 20.0, axis=0)

        # Merge innings 1 & innings 2 global pressure effects
        for inn in (1, 2):
            sub_i = inn_split[(inn_split["role"] == role) & (inn_split["innings"] == inn) & (inn_split["scale"] == "LI_global")]
            sub_i = sub_i[["player_id", "hp_effect", "innings_eligible"]].rename(
                columns={"hp_effect": f"inn{inn}_hp_effect", "innings_eligible": f"inn{inn}_eligible"}
            )
            t = t.merge(sub_i, on="player_id", how="left")

        t = classify_player_archetypes(t, tol=cfg.clutch_non_inferiority_tol)
        t = t.sort_values(["eligible", "combined_hp_per100"], ascending=[False, False]).reset_index(drop=True)
        role_tables[role] = t
        boot_rows.append(
            t[
                [
                    "player_id",
                    "player_name",
                    "role",
                    "eligible",
                    "main_effect_per100",
                    "ci_low_main",
                    "ci_high_main",
                    "pressure_interaction_per100",
                    "ci_low_pres",
                    "ci_high_pres",
                    "combined_hp_per100",
                    "ci_low_hp",
                    "ci_high_hp",
                    "rank_hp",
                    "rank_ci_low",
                    "rank_ci_high",
                    "prob_top_10",
                    "prob_top_20",
                ]
            ]
        )

    role_tables["batter"].to_csv(cfg.output_dir / "V5_0_GLOBAL_BATTER_PRESSURE.csv", index=False)
    role_tables["bowler"].to_csv(cfg.output_dir / "V5_0_GLOBAL_BOWLER_PRESSURE.csv", index=False)
    pd.concat(boot_rows, ignore_index=True).to_csv(cfg.output_dir / "V5_0_BOOTSTRAP_CONFIDENCE.csv", index=False)

    arch_df = pd.concat([role_tables["batter"], role_tables["bowler"]], ignore_index=True)
    arch_df.to_csv(cfg.output_dir / "V5_0_PLAYER_ARCHETYPES.csv", index=False)
    save_archetype_quadrant_plot(role_tables["batter"], "batter", str(cfg.plots_dir / "v5_0_archetype_quadrant_batter.html"))
    save_archetype_quadrant_plot(role_tables["bowler"], "bowler", str(cfg.plots_dir / "v5_0_archetype_quadrant_bowler.html"))

    # Phase 10: 50 Repeated Split-Half Tests
    el_bat_mask = np.isin(blocks["batter_ids"], role_tables["batter"].loc[role_tables["batter"]["eligible"], "player_id"].values)
    el_bowl_mask = np.isin(blocks["bowler_ids"], role_tables["bowler"].loc[role_tables["bowler"]["eligible"], "player_id"].values)

    sh_rows: List[Dict[str, Any]] = []
    for s in range(cfg.n_split_half):
        perm = rng.permutation(n_m)
        half = n_m // 2
        ia = np.concatenate([idx_lists[i] for i in perm[:half]])
        ib = np.concatenate([idx_lists[i] for i in perm[half:]])
        ba = {"X_main": X_m[ia], "X_pressure": X_p[ia], "X_context": X_c[ia], "y": y_all[ia], "n_bat": n_bat, "n_bowl": n_bowl}
        bb = {"X_main": X_m[ib], "X_pressure": X_p[ib], "X_context": X_c[ib], "y": y_all[ib], "n_bat": n_bat, "n_bowl": n_bowl}
        fa = solve_block_ridge(ba, sel_main, sel_int, cfg.alpha_context, cfg.random_seed, tol=1e-4)
        fb = solve_block_ridge(bb, sel_main, sel_int, cfg.alpha_context, cfg.random_seed, tol=1e-4)

        for role, k_m, k_p, k_hp, mask in [
            ("batter", "bat_main", "bat_pres", "bat_hp", el_bat_mask),
            ("bowler", "bowl_main", "bowl_pres", "bowl_hp", el_bowl_mask),
        ]:
            t10_a = set(np.argsort(-fa[k_hp][mask])[:10])
            t10_b = set(np.argsort(-fb[k_hp][mask])[:10])
            t20_a = set(np.argsort(-fa[k_hp][mask])[:20])
            t20_b = set(np.argsort(-fb[k_hp][mask])[:20])
            sh_rows.append(
                {
                    "split": s + 1,
                    "role": role,
                    "main_spearman": float(spearmanr(fa[k_m][mask], fb[k_m][mask])[0]),
                    "pres_spearman": float(spearmanr(fa[k_p][mask], fb[k_p][mask])[0]),
                    "hp_spearman": float(spearmanr(fa[k_hp][mask], fb[k_hp][mask])[0]),
                    "top10_overlap": len(t10_a & t10_b),
                    "top20_overlap": len(t20_a & t20_b),
                }
            )
    sh_df = pd.DataFrame(sh_rows)
    stab_df = sh_df.groupby("role", as_index=False).agg(
        n_splits=("split", "count"),
        main_spearman_mean=("main_spearman", "mean"),
        pres_spearman_mean=("pres_spearman", "mean"),
        hp_spearman_mean=("hp_spearman", "mean"),
        top10_overlap_mean=("top10_overlap", "mean"),
        top20_overlap_mean=("top20_overlap", "mean"),
    )
    stab_df.to_csv(cfg.output_dir / "V5_0_RANKING_STABILITY.csv", index=False)

    # Model Comparison: V5.0 vs V4.2, V4.3, V4.4 Track A & Track B
    v42 = pd.read_csv(cfg.v42_dir / "V4_2_ALL_PLAYER_ESTIMATES.csv")
    v43_b = pd.read_csv(cfg.v43_dir / "V4_3_BATTER_RAPM.csv")
    v43_w = pd.read_csv(cfg.v43_dir / "V4_3_BOWLER_RAPM.csv")
    v44_b = pd.read_csv(cfg.v44_dir / "V4_4_BATTER_RAPM.csv")
    v44_w = pd.read_csv(cfg.v44_dir / "V4_4_BOWLER_RAPM.csv")
    tb_b = pd.read_csv(cfg.v44_dir / "V4_4_TRACK_B_RESOURCE_PRESSURE_BATTER.csv")
    tb_w = pd.read_csv(cfg.v44_dir / "V4_4_TRACK_B_RESOURCE_PRESSURE_BOWLER.csv")

    cmp_rows: List[Dict[str, Any]] = []
    for role, u50, u43, c43, u44, c44_m, c44_p, utb, ctb_m, ctb_p in [
        ("batter", role_tables["batter"], v43_b, "rapm_batter_per100", v44_b, "rapm_main_per100", "rapm_pressure_slope_per100", tb_b, "obs_rp_main_per100", "obs_rp_pressure_slope_per100"),
        ("bowler", role_tables["bowler"], v43_w, "rapm_bowler_defensive_per100", v44_w, "rapm_defensive_main_per100", "rapm_pressure_slope_per100", tb_w, "obs_rp_defensive_main_per100", "obs_rp_pressure_slope_per100"),
    ]:
        el50 = u50[u50["eligible"]]
        # vs V4.4 Track A
        m44 = el50.merge(u44[["player_id", c44_m, c44_p]], on="player_id", how="inner")
        cmp_rows.append({"role": role, "comparison": "V5.0 Main vs V4.4 Track A Main", "common_n": len(m44), "spearman_r": round(float(spearmanr(m44["main_effect_per100"], m44[c44_m])[0]), 4)})
        cmp_rows.append({"role": role, "comparison": "V5.0 Binary HP Uplift vs V4.4 Continuous LI Slope", "common_n": len(m44), "spearman_r": round(float(spearmanr(m44["pressure_interaction_per100"], m44[c44_p])[0]), 4)})
        # vs V4.3
        m43 = el50.merge(u43[["player_id", c43]], on="player_id", how="inner")
        cmp_rows.append({"role": role, "comparison": "V5.0 Main vs V4.3 Batter-Run RAPM", "common_n": len(m43), "spearman_r": round(float(spearmanr(m43["main_effect_per100"], m43[c43])[0]), 4)})
        # vs Track B
        mtb = el50.merge(utb[["player_id", ctb_m, ctb_p]], on="player_id", how="inner")
        cmp_rows.append({"role": role, "comparison": "V5.0 Track A Main vs V4.4 Track B Main", "common_n": len(mtb), "spearman_r": round(float(spearmanr(mtb["main_effect_per100"], mtb[ctb_m])[0]), 4)})
        cmp_rows.append({"role": role, "comparison": "V5.0 Track A HP Uplift vs Track B Resource Slope", "common_n": len(mtb), "spearman_r": round(float(spearmanr(mtb["pressure_interaction_per100"], mtb[ctb_p])[0]), 4)})
        # vs V4.2
        v42_el = v42[(v42["role"] == role) & (v42["eligible"] == True)]
        m42 = el50.merge(v42_el[["player_id", "eb_delta", "claim_a_general_skill_fe"]], on="player_id", how="inner")
        cmp_rows.append({"role": role, "comparison": "V5.0 Main vs V4.2 Claim A General Skill", "common_n": len(m42), "spearman_r": round(float(spearmanr(m42["main_effect_per100"], m42["claim_a_general_skill_fe"])[0]), 4)})
        cmp_rows.append({"role": role, "comparison": "V5.0 HP Uplift vs V4.2 Pressure Slope (EB Delta)", "common_n": len(m42), "spearman_r": round(float(spearmanr(m42["pressure_interaction_per100"], m42["eb_delta"])[0]), 4)})

    cmp_df = pd.DataFrame(cmp_rows)
    cmp_df.to_csv(cfg.output_dir / "V5_0_MODEL_COMPARISON.csv", index=False)

    # Gate sensitivity
    gate_rows = []
    for label, g_hp, g_tot, g_m in [("Permissive (50/200/8)", 50, 200, 8), ("Primary (100/300/12)", 100, 300, 12), ("Strict (150/500/15)", 150, 500, 15)]:
        for role, tbl in role_tables.items():
            ok = (tbl["n_hp_global"] >= g_hp) & (tbl["total_opportunities"] >= g_tot) & (tbl["m_hp"] >= g_m)
            gate_rows.append({"gate": label, "role": role, "n_eligible": int(ok.sum()), "n_excluded": int((~ok).sum())})
    pd.DataFrame(gate_rows).to_csv(cfg.artifacts_dir / "v5_0_gate_sensitivity.csv", index=False)

    return {
        "counts": counts,
        "sel_main": sel_main,
        "sel_int": sel_int,
        "oot_mse": oot_mse,
        "oot_rmse": oot_rmse,
        "tune_df": tune_df,
        "stab_df": stab_df,
        "cmp_df": cmp_df,
        "bat_df": role_tables["batter"],
        "bowl_df": role_tables["bowler"],
    }
