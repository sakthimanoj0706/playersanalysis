"""V4.1 Sections 4, 6, 7, 9, 10 — Precision Eligibility, Model Comparison, Rank Probabilities & Separated A/B/C Validation."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from src.v4.pressure_proxy import apply_b3_resource_stress, fit_b3_resource_stress
from src.v4_1.decomposition import build_raw_vs_adjusted_decomposition, export_decomposition_and_bowler_audit
from src.v4_1.hierarchical_v41 import (
    add_v41_pressure_aliases,
    fit_joint_hierarchical_slope,
    fit_v41_two_stage,
    run_global_match_cluster_bootstrap,
)

V41_OPERATIONAL_PRECISION_GATE = {
    "min_hi_balls": 50,
    "min_lo_balls": 30,
    "min_cs_matches": 8,
    "max_se_delta": 25.0,
}

V4_LEGACY_GATE = {
    "min_hi_balls": 100,
    "min_lo_balls": 60,
    "min_hi_matches": 10,
    "min_lo_matches": 10,
    "min_cs_matches": 10,
    "min_total_matches": 15,
}


def _safe_corr(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    mask = np.isfinite(x.values) & np.isfinite(y.values)
    xv, yv = x.values[mask], y.values[mask]
    if len(xv) < 6 or np.std(xv) < 1e-12 or np.std(yv) < 1e-12:
        return np.nan, np.nan
    return float(pearsonr(xv, yv)[0]), float(spearmanr(xv, yv)[0])


def _jaccard_overlap(a: List[int], b: List[int]) -> Tuple[int, float]:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0, 1.0
    return len(sa & sb), float(len(sa & sb) / max(len(sa | sb), 1))


def _precision_eligible_mask(df: pd.DataFrame, gate: Dict[str, Any] = V41_OPERATIONAL_PRECISION_GATE) -> pd.Series:
    return (
        (df["n_hi"] >= gate["min_hi_balls"])
        & (df["n_lo"] >= gate["min_lo_balls"])
        & (df["cs_matches"] >= gate["min_cs_matches"])
        & np.isfinite(df["se_delta"])
        & (df["se_delta"] <= gate["max_se_delta"])
        & np.isfinite(df["empirical_bayes_delta"])
    )


def _assign_v41_tiers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["precision_eligible"] = _precision_eligible_mask(out)
    out["positive_adjusted_contrast"] = out["context_adjusted_delta"] > 0.0
    out["strict_reliable_flag"] = (
        out["precision_eligible"]
        & (out["lower_confidence_bound"] > 0.0)
        & (out["boot_ci_low"].fillna(-1.0) > 0.0)
        & (out["probability_positive_effect"] >= 0.95)
        & (out["eb_weight"] >= 0.30)
    )
    out["reliability_tier"] = np.where(
        out["strict_reliable_flag"],
        "RELIABLE",
        np.where(
            out["precision_eligible"],
            "PROVISIONAL_CI_CROSSES_ZERO",
            "INSUFFICIENT_PRECISION_OR_SUPPORT",
        ),
    )
    return out


def build_eligibility_precision_analysis(
    bat_df: pd.DataFrame,
    bowl_df: pd.DataFrame,
    output_dir: str = "data/outputs/v4_1",
) -> pd.DataFrame:
    """Audit V4 cutoffs & test continuous uncertainty-based precision eligibility alternatives."""
    rows: List[Dict[str, Any]] = []
    for role, df in [("batter", bat_df), ("bowler", bowl_df)]:
        base = df[_precision_eligible_mask(df)].sort_values(["empirical_bayes_delta", "player_id"], ascending=[False, True])
        base_t10 = base["player_id"].head(10).tolist()

        sweeps: List[Tuple[str, str, pd.Series]] = []
        for nh in (30, 40, 50, 60, 80, 100, 125, 150, 200, 250):
            sweeps.append(("high_pressure_balls", f"n_hi>={nh} (+lo>=30,cs>=8)", (df["n_hi"] >= nh) & (df["n_lo"] >= 30) & (df["cs_matches"] >= 8) & np.isfinite(df["se_delta"])))
        for nl in (20, 30, 40, 60, 100):
            sweeps.append(("normal_low_balls", f"n_lo>={nl} (+hi>=50,cs>=8)", (df["n_hi"] >= 50) & (df["n_lo"] >= nl) & (df["cs_matches"] >= 8) & np.isfinite(df["se_delta"])))
        for cm in (5, 8, 10, 15):
            sweeps.append(("common_support_matches", f"cs_matches>={cm} (+hi>=50,lo>=30)", (df["n_hi"] >= 50) & (df["n_lo"] >= 30) & (df["cs_matches"] >= cm) & np.isfinite(df["se_delta"])))
        for se_cap in (12.0, 15.0, 18.0, 22.0, 25.0, 30.0):
            sweeps.append(("precision_se_cap", f"se_delta<={se_cap:.0f} (+hi>=50,lo>=30,cs>=8)", (df["n_hi"] >= 50) & (df["n_lo"] >= 30) & (df["cs_matches"] >= 8) & (df["se_delta"] <= se_cap)))
        sweeps.append((
            "gate_framework_comparison",
            "V4_Legacy_6Gate (100/60/10/10/10/15)",
            (df["n_hi"] >= 100) & (df["n_lo"] >= 60) & (df["hi_matches"] >= 10)
            & (df["lo_matches"] >= 10) & (df["cs_matches"] >= 10) & (df["total_matches"] >= 15),
        ))
        sweeps.append(("gate_framework_comparison", "V4_1_Precision_Floor (hi>=50,lo>=30,cs>=8,se<=25)", _precision_eligible_mask(df)))

        for dim, label, mask in sweeps:
            sub = df[mask & np.isfinite(df["empirical_bayes_delta"])].sort_values(["empirical_bayes_delta", "player_id"], ascending=[False, True])
            t10 = sub["player_id"].head(10).tolist()
            ov, jac = _jaccard_overlap(base_t10, t10)
            merged = base[["player_id", "empirical_bayes_delta"]].merge(
                sub[["player_id", "empirical_bayes_delta"]], on="player_id", suffixes=("_b", "_s")
            )
            rho = float(spearmanr(merged["empirical_bayes_delta_b"], merged["empirical_bayes_delta_s"])[0]) if len(merged) >= 6 else np.nan
            med_ci = float((2.0 * 1.96 * sub["post_sd"]).median()) if len(sub) else np.nan
            med_neff = float(sub["effective_sample_size"].median()) if len(sub) else np.nan
            med_cons = float(sub["hi_match_pos_rate"].median()) if len(sub) else np.nan
            rows.append({
                "role": role,
                "dimension": dim,
                "setting": label,
                "eligible_count": int(len(sub)),
                "median_effective_sample_size": round(med_neff, 1) if pd.notna(med_neff) else np.nan,
                "median_posterior_ci_width": round(med_ci, 3) if pd.notna(med_ci) else np.nan,
                "median_hi_match_pos_rate": round(med_cons, 3) if pd.notna(med_cons) else np.nan,
                "top10_overlap_vs_v41_base": ov,
                "jaccard_vs_v41_base": round(jac, 4),
                "spearman_rho_vs_v41_base": round(rho, 4) if pd.notna(rho) else np.nan,
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(os.path.join(output_dir, "V4_1_ELIGIBILITY_PRECISION_ANALYSIS.csv"), index=False)
    return out_df


def _oot_ridge_rmse(reg_df: pd.DataFrame, role: str, lam_m: float, lam_p: float, lam_opp: float) -> float:
    from scipy import sparse
    from scipy.sparse.linalg import lsqr

    flag = "is_ball_faced" if role == "batter" else "is_legal_ball"
    idc = "striker_id" if role == "batter" else "bowler_id"
    opp = "bowler_id" if role == "batter" else "striker_id"
    sc = 100.0 if role == "batter" else -100.0

    tr = reg_df[(reg_df["year"] <= 2024) & (reg_df[flag] == 1)]
    te = reg_df[(reg_df["year"] > 2024) & (reg_df[flag] == 1)]
    skey = tr["innings"].astype(str) + "|" + tr["phase"].astype(str) + "|" + tr["match_format"].astype(str)
    sc_c, mc_c, pc_c, oc_c = pd.Categorical(skey), pd.Categorical(tr["match_id"]), pd.Categorical(tr[idc]), pd.Categorical(tr[opp])
    n = len(tr); rx = np.arange(n)
    X = sparse.hstack([
        sparse.csr_matrix((np.ones(n), (rx, sc_c.codes)), shape=(n, len(sc_c.categories))),
        sparse.csr_matrix((np.ones(n), (rx, mc_c.codes)), shape=(n, len(mc_c.categories))),
        sparse.csr_matrix((np.ones(n), (rx, pc_c.codes)), shape=(n, len(pc_c.categories))),
        sparse.csr_matrix((np.ones(n), (rx, oc_c.codes)), shape=(n, len(oc_c.categories))),
    ], format="csr")
    pen = sparse.diags(np.concatenate([
        np.full(len(sc_c.categories), 0.1),
        np.full(len(mc_c.categories), np.sqrt(lam_m)),
        np.full(len(pc_c.categories), np.sqrt(lam_p)),
        np.full(len(oc_c.categories), np.sqrt(lam_opp)),
    ]))
    c = lsqr(sparse.vstack([X, pen]), np.concatenate([tr["batter_runs"].values * sc, np.zeros(X.shape[1])]), atol=1e-6, btol=1e-6)[0]
    ns, nm, np_ = len(sc_c.categories), len(mc_c.categories), len(pc_c.categories)
    s_map = dict(zip(sc_c.categories, c[:ns]))
    p_map = dict(zip(pc_c.categories, c[ns + nm:ns + nm + np_]))
    o_map = dict(zip(oc_c.categories, c[ns + nm + np_:]))
    te_skey = te["innings"].astype(str) + "|" + te["phase"].astype(str) + "|" + te["match_format"].astype(str)
    pred = te_skey.map(s_map).fillna(sc * 1.30) + te[idc].map(p_map).fillna(0.0) + te[opp].map(o_map).fillna(0.0)
    return float(np.sqrt(np.mean((te["batter_runs"].values * sc - pred.values) ** 2)))


def build_model_comparison(
    reg_v41: pd.DataFrame,
    base_bat: pd.DataFrame,
    diag_bat: Dict[str, Any],
    base_bowl: pd.DataFrame,
    diag_bowl: Dict[str, Any],
    output_dir: str = "data/outputs/v4_1",
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Compare Two-Stage REML, V4 DL (span=0.625), DL (span=0.75), Joint Hierarchical Slope, Ridge Grid, and Gate choices."""
    rows: List[Dict[str, Any]] = []
    joint_dfs: Dict[str, pd.DataFrame] = {}

    for role, outc, sc, base_df, base_diag in [
        ("batter", "batter_runs", 100.0, base_bat, diag_bat),
        ("bowler", "batter_runs", -100.0, base_bowl, diag_bowl),
    ]:
        base_elig = base_df[_precision_eligible_mask(base_df)].sort_values(["empirical_bayes_delta", "player_id"], ascending=[False, True])
        base_t10 = base_elig["player_id"].head(10).tolist()

        # Fit Joint Hierarchical Models across slope penalties
        j_3500 = fit_joint_hierarchical_slope(reg_v41, role=role, outcome=outc, scale=sc, span=0.75, lam_slope=3500.0)
        j_500 = fit_joint_hierarchical_slope(reg_v41, role=role, outcome=outc, scale=sc, span=0.75, lam_slope=500.0)
        joint_dfs[role] = j_3500

        variants = [
            ("V4_1_Base_TwoStage_FWL_REML_60", "reml", 0.75, (60.0, 60.0, 60.0), False, "eb_delta", False, None),
            ("V4_Legacy_TwoStage_DL_35_span0625", "dl", 0.625, (35.0, 30.0, 35.0), True, "lcb95_delta", True, None),
            ("TwoStage_FWL_DL_60_span075", "dl", 0.75, (60.0, 60.0, 60.0), False, "eb_delta", False, None),
            ("TwoStage_REML_With_AbsGate_ebHi>0", "reml", 0.75, (60.0, 60.0, 60.0), True, "eb_delta", False, None),
            ("TwoStage_REML_OrderBy_LCB95", "reml", 0.75, (60.0, 60.0, 60.0), False, "lcb95_delta", False, None),
            ("Ridge_Light_15_REML", "reml", 0.75, (15.0, 15.0, 15.0), False, "eb_delta", False, None),
            ("Ridge_Default_35_REML", "reml", 0.75, (35.0, 30.0, 35.0), False, "eb_delta", False, None),
            ("Ridge_Heavy_120_REML", "reml", 0.75, (120.0, 120.0, 120.0), False, "eb_delta", False, None),
            ("Ridge_VeryHeavy_250_REML", "reml", 0.75, (250.0, 250.0, 250.0), False, "eb_delta", False, None),
            ("Joint_Hierarchical_Slope_lam3500", "reml", 0.75, (60.0, 60.0, 60.0), False, "joint_delta", False, j_3500),
            ("Joint_Hierarchical_Slope_lam500", "reml", 0.75, (60.0, 60.0, 60.0), False, "joint_delta", False, j_500),
        ]

        rmse_cache: Dict[Tuple[float, float, float], float] = {}
        for name, ebm, sp, lams, use_abs_gate, order_col, legacy_cov, jdf in variants:
            if name == "V4_1_Base_TwoStage_FWL_REML_60":
                alt, dg = base_df.copy(), base_diag
            elif lams == (60.0, 60.0, 60.0) and sp == 0.75 and ebm == "reml":
                alt, dg = base_df.copy(), base_diag
            else:
                alt, dg, _, _ = fit_v41_two_stage(
                    reg_v41, role=role, outcome=outc, scale=sc, span=sp, eb_method=ebm,
                    lam_match=lams[0], lam_player=lams[1], lam_opp=lams[2],
                )
            if jdf is not None:
                alt = alt.merge(jdf, on="player_id", how="left")

            if legacy_cov:
                mask = (alt["n_hi"] >= 100) & (alt["n_lo"] >= 60) & (alt["hi_matches"] >= 10) & (alt["lo_matches"] >= 10) & (alt["cs_matches"] >= 10) & (alt["total_matches"] >= 15)
            else:
                mask = _precision_eligible_mask(alt)

            if use_abs_gate:
                mask = mask & (alt["context_adjusted_delta"] > 0.0) & (alt["eb_high_performance"] > 0.0)

            sort_key = "empirical_bayes_delta" if order_col == "eb_delta" else ("lower_confidence_bound" if order_col == "lcb95_delta" else "joint_delta")
            sub = alt[mask].sort_values([sort_key, "player_id"], ascending=[False, True])
            t10_ids = sub["player_id"].head(10).tolist()
            t10_names = sub["player_name"].head(10).tolist()
            ov, jac = _jaccard_overlap(base_t10, t10_ids)
            mrg = base_elig[["player_id", "empirical_bayes_delta"]].merge(
                sub[["player_id", sort_key]].rename(columns={sort_key: "alt_score"}), on="player_id"
            )
            rho = float(spearmanr(mrg["empirical_bayes_delta"], mrg["alt_score"])[0]) if len(mrg) >= 6 else np.nan
            rel_cnt = int((sub["lower_confidence_bound"] > 0.0).sum()) if sort_key != "joint_delta" else 0

            if lams not in rmse_cache:
                rmse_cache[lams] = _oot_ridge_rmse(reg_v41, role, lams[0], lams[1], lams[2])

            rows.append({
                "role": role,
                "model_variant": name,
                "eb_method": "JOINT_RIDGE" if jdf is not None else ebm.upper(),
                "contrast_span": sp,
                "ridge_lambdas": f"{int(lams[0])}/{int(lams[1])}/{int(lams[2])}",
                "eligible_count": int(len(sub)),
                "reliable_count": rel_cnt,
                "mu0": round(dg["mu0"], 4) if jdf is None else np.nan,
                "tau": round(dg["tau"], 4) if jdf is None else round(float(sub["joint_delta"].std()), 4),
                "k_eff": round(dg["k_eff"], 2) if (jdf is None and np.isfinite(dg["k_eff"])) else np.inf,
                "oot_2025_2026_rmse": round(rmse_cache[lams], 4),
                "top10_overlap_vs_v41": ov,
                "jaccard_vs_v41": round(jac, 4),
                "spearman_rho_vs_v41": round(rho, 4) if pd.notna(rho) else np.nan,
                "top10_players": "; ".join(t10_names),
            })

    comp_df = pd.DataFrame(rows)
    comp_df.to_csv(os.path.join(output_dir, "V4_1_MODEL_COMPARISON.csv"), index=False)
    return comp_df, joint_dfs


def run_v41_validation_matrix(
    reg_ctx: pd.DataFrame,
    reg_v41: pd.DataFrame,
    output_dir: str = "data/outputs/v4_1",
) -> pd.DataFrame:
    """Section 9 validation suite separating Claim A (general skill), Claim B (high-stress level), Claim C (relative delta) & diagnostics."""
    records: List[Dict[str, Any]] = []
    specs = [
        ("batter", "striker_id", "batter_runs", 100.0, "BATTING_RESOURCE_STRESS"),
        ("bowler", "bowler_id", "batter_runs", -100.0, "BOWLING_SCORING_THREAT"),
        ("bowler", "bowler_id", "is_ctrl_ball", 100.0, "BOWLING_SCORING_THREAT"),
    ]

    # 1. Rolling-origin temporal validation (separated Claims A, B, C)
    for cutoff in (2023, 2024, 2025):
        tr_raw = reg_ctx[reg_ctx["year"] <= cutoff]
        te_raw = reg_ctx[reg_ctx["year"] == cutoff + 1]
        b3_st = fit_b3_resource_stress(tr_raw)
        tr_df = add_v41_pressure_aliases(apply_b3_resource_stress(tr_raw, b3_st))
        te_df = add_v41_pressure_aliases(apply_b3_resource_stress(te_raw, b3_st))
        for role, idc, outc, sc, pcol in specs:
            r_tr, dg_tr, _, _ = fit_v41_two_stage(tr_df, role=role, outcome=outc, scale=sc, p_col=pcol)
            r_te, _, _, _ = fit_v41_two_stage(te_df, role=role, outcome=outc, scale=sc, p_col=pcol)
            mrg = r_tr.merge(
                r_te[["player_id", "ridge_overall_player_effect", "context_adjusted_high_performance", "context_adjusted_delta", "raw_observed_delta", "n_hi", "n_lo"]],
                on="player_id", suffixes=("_tr", "_te"),
            )
            good = mrg[(mrg["n_hi_tr"] >= 25) & (mrg["n_lo_tr"] >= 25) & (mrg["n_hi_te"] >= 10) & (mrg["n_lo_te"] >= 10)]
            r_skill, _ = _safe_corr(good["ridge_overall_player_effect_tr"], good["ridge_overall_player_effect_te"])
            r_hi, _ = _safe_corr(good["eb_high_performance"], good["context_adjusted_high_performance_te"])
            r_eb, rho_eb = _safe_corr(good["empirical_bayes_delta"], good["context_adjusted_delta_te"])
            r_unadj, _ = _safe_corr(good["raw_observed_delta_tr"], good["raw_observed_delta_te"])

            records.extend([
                {
                    "claim_category": "CLAIM_A_GENERAL_SKILL_REPEATABILITY",
                    "validation_family": "ROLLING_ORIGIN_TEMPORAL",
                    "role": role, "metric": outc, "split": f"<={cutoff} -> {cutoff+1}", "n_eval": int(len(good)),
                    "tau_train": round(dg_tr["tau"], 3), "pearson_r": round(r_skill, 4) if pd.notna(r_skill) else np.nan,
                    "spearman_rho": np.nan, "status": "REPEATABLE_GENERAL_SKILL" if pd.notna(r_skill) and r_skill > 0.20 else "WEAK",
                },
                {
                    "claim_category": "CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY",
                    "validation_family": "ROLLING_ORIGIN_TEMPORAL",
                    "role": role, "metric": outc, "split": f"<={cutoff} -> {cutoff+1}", "n_eval": int(len(good)),
                    "tau_train": round(dg_tr["hi_tau"], 3), "pearson_r": round(r_hi, 4) if pd.notna(r_hi) else np.nan,
                    "spearman_rho": np.nan, "status": "REPLICATED" if pd.notna(r_hi) and r_hi > 0.15 else "LOW_OR_MIXED",
                },
                {
                    "claim_category": "CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY",
                    "validation_family": "ROLLING_ORIGIN_TEMPORAL",
                    "role": role, "metric": outc, "split": f"<={cutoff} -> {cutoff+1}", "n_eval": int(len(good)),
                    "tau_train": round(dg_tr["tau"], 3), "pearson_r": round(r_eb, 4) if pd.notna(r_eb) else np.nan,
                    "spearman_rho": round(rho_eb, 4) if pd.notna(rho_eb) else np.nan,
                    "status": "ESTABLISHED" if pd.notna(r_eb) and r_eb > 0.20 else "INCONCLUSIVE_WEAK_TEMPORAL_DELTA",
                },
                {
                    "claim_category": "CLAIM_C_DECOMPOSITION_STABILITY",
                    "validation_family": "UNADJUSTED_VS_ADJUSTED_TEMPORAL",
                    "role": role, "metric": outc, "split": f"raw_delta <= {cutoff} -> {cutoff+1}", "n_eval": int(len(good)),
                    "tau_train": np.nan, "pearson_r": round(r_unadj, 4) if pd.notna(r_unadj) else np.nan,
                    "spearman_rho": np.nan, "status": "UNADJUSTED_BASELINE_TRACKED",
                },
            ])

    # 2. Even/Odd match parity split-half
    m_ord = reg_v41[["match_id", "match_date_dt"]].drop_duplicates().sort_values(["match_date_dt", "match_id"]).reset_index(drop=True)
    m_ord["half"] = np.arange(len(m_ord)) % 2
    sh = reg_v41.merge(m_ord[["match_id", "half"]], on="match_id", how="left")
    for role, idc, outc, sc, pcol in specs[:2]:
        r0, d0, _, _ = fit_v41_two_stage(sh[sh["half"] == 0], role=role, outcome=outc, scale=sc, p_col=pcol)
        r1, d1, _, _ = fit_v41_two_stage(sh[sh["half"] == 1], role=role, outcome=outc, scale=sc, p_col=pcol)
        mrg = r0.merge(r1[["player_id", "context_adjusted_delta", "empirical_bayes_delta", "eb_high_performance", "ridge_overall_player_effect", "n_hi", "n_lo"]], on="player_id", suffixes=("_0", "_1"))
        good = mrg[(mrg["n_hi_0"] >= 25) & (mrg["n_lo_0"] >= 25) & (mrg["n_hi_1"] >= 25) & (mrg["n_lo_1"] >= 25)]
        r_sk, _ = _safe_corr(good["ridge_overall_player_effect_0"], good["ridge_overall_player_effect_1"])
        r_hi, _ = _safe_corr(good["eb_high_performance_0"], good["eb_high_performance_1"])
        r_d, rho_d = _safe_corr(good["context_adjusted_delta_0"], good["context_adjusted_delta_1"])
        records.extend([
            {"claim_category": "CLAIM_A_GENERAL_SKILL_REPEATABILITY", "validation_family": "EVEN_ODD_SPLIT_HALF", "role": role, "metric": outc, "split": "even_vs_odd_matches", "n_eval": int(len(good)), "tau_train": np.nan, "pearson_r": round(r_sk, 4) if pd.notna(r_sk) else np.nan, "spearman_rho": np.nan, "status": "SPLIT_HALF_GENERAL_SKILL"},
            {"claim_category": "CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY", "validation_family": "EVEN_ODD_SPLIT_HALF", "role": role, "metric": outc, "split": "even_vs_odd_matches", "n_eval": int(len(good)), "tau_train": round(0.5*(d0["hi_tau"]+d1["hi_tau"]), 3), "pearson_r": round(r_hi, 4) if pd.notna(r_hi) else np.nan, "spearman_rho": np.nan, "status": "SPLIT_HALF_HIGH_STRESS"},
            {"claim_category": "CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY", "validation_family": "EVEN_ODD_SPLIT_HALF", "role": role, "metric": outc, "split": "even_vs_odd_matches", "n_eval": int(len(good)), "tau_train": round(0.5*(d0["tau"]+d1["tau"]), 3), "pearson_r": round(r_d, 4) if pd.notna(r_d) else np.nan, "spearman_rho": round(rho_d, 4) if pd.notna(rho_d) else np.nan, "status": "INCONCLUSIVE_LOW_SPLIT_HALF_DELTA"},
        ])

    # 3. Resource-stress specification & reference quantile sensitivity (Claim C robustness)
    alt_spec_df = reg_v41.copy()
    # Alt batter spec: empirical empirical CDF of pure wickets lost minus innings/over average (non-parametric vs R(u,w))
    alt_spec_df["raw_wkts_lost"] = alt_spec_df["wkts_before"].astype(float) - alt_spec_df.groupby(["innings", "overid"])["wkts_before"].transform("mean")
    alt_spec_df["BAT_STRESS_NONPARAM_WKT"] = alt_spec_df["raw_wkts_lost"].rank(pct=True)
    # Alt bowler spec: raw empirical scoring rate by (phase, innings, is_t20i)
    alt_spec_df["BOWL_THREAT_CELL_MEAN"] = alt_spec_df.groupby(["phase", "innings", "is_t20i"])["batter_runs"].transform("mean").rank(pct=True)

    base_bat_ref, _, _, _ = fit_v41_two_stage(reg_v41, role="batter", outcome="batter_runs", scale=100.0)
    base_bowl_ref, _, _, _ = fit_v41_two_stage(reg_v41, role="bowler", outcome="batter_runs", scale=-100.0)

    for role, base_r, alt_pcol, sc in [
        ("batter", base_bat_ref, "BAT_STRESS_NONPARAM_WKT", 100.0),
        ("bowler", base_bowl_ref, "BOWL_THREAT_CELL_MEAN", -100.0),
    ]:
        r_alt, dg_alt, _, _ = fit_v41_two_stage(alt_spec_df, role=role, outcome="batter_runs", scale=sc, p_col=alt_pcol)
        mrg = base_r[_precision_eligible_mask(base_r)][["player_id", "empirical_bayes_delta"]].merge(
            r_alt[["player_id", "empirical_bayes_delta"]], on="player_id", suffixes=("_b", "_a")
        )
        pr, rho = _safe_corr(mrg["empirical_bayes_delta_b"], mrg["empirical_bayes_delta_a"])
        records.append({
            "claim_category": "CLAIM_C_RESOURCE_STRESS_SPEC_SENSITIVITY",
            "validation_family": "PROXY_SPEC_SENSITIVITY",
            "role": role, "metric": "batter_runs", "split": alt_pcol,
            "n_eval": int(len(mrg)), "tau_train": round(dg_alt["tau"], 3),
            "pearson_r": round(pr, 4) if pd.notna(pr) else np.nan,
            "spearman_rho": round(rho, 4) if pd.notna(rho) else np.nan,
            "status": "SPECIFICATION_SENSITIVITY_LOGGED",
        })

    for q_hi, q_lo, qlab in [(0.80, 0.20, "P80_vs_P20"), (0.85, 0.15, "P85_vs_P15")]:
        for role, base_r, sc in [("batter", base_bat_ref, 100.0), ("bowler", base_bowl_ref, -100.0)]:
            r_q, dg_q, _, _ = fit_v41_two_stage(reg_v41, role=role, outcome="batter_runs", scale=sc, hi_thr=q_hi, lo_thr=q_lo, span=float(q_hi - q_lo))
            mrg = base_r[_precision_eligible_mask(base_r)][["player_id", "empirical_bayes_delta"]].merge(
                r_q[["player_id", "empirical_bayes_delta"]], on="player_id", suffixes=("_b", "_q")
            )
            pr, rho = _safe_corr(mrg["empirical_bayes_delta_b"], mrg["empirical_bayes_delta_q"])
            records.append({
                "claim_category": "CLAIM_C_QUANTILE_SENSITIVITY",
                "validation_family": "PRESSURE_QUANTILE_CUTOFFS",
                "role": role, "metric": "batter_runs", "split": qlab,
                "n_eval": int(len(mrg)), "tau_train": round(dg_q["tau"], 3),
                "pearson_r": round(pr, 4) if pd.notna(pr) else np.nan,
                "spearman_rho": round(rho, 4) if pd.notna(rho) else np.nan,
                "status": "QUANTILE_SENSITIVITY_LOGGED",
            })

    # 4. Engineering Diagnostics Only (Placebo & Synthetic Recovery)
    for role, sc in [("batter", 100.0), ("bowler", -100.0)]:
        _, dg_pl, _, _ = fit_v41_two_stage(reg_v41, role=role, outcome="batter_runs", scale=sc, shuffle_pressure_seed=42)
        df_q = max(1, int(dg_pl["df"]))
        z_q = (float(dg_pl["Q"]) - df_q) / np.sqrt(2.0 * df_q)
        null_ok = float(dg_pl["Q"]) <= (df_q + 1.96 * np.sqrt(2.0 * df_q))
        records.append({
            "claim_category": "ENGINEERING_DIAGNOSTIC_ONLY",
            "validation_family": "SHUFFLED_PRESSURE_PLACEBO_NULL",
            "role": role, "metric": "batter_runs", "split": "permuted_pressure_null",
            "n_eval": int(dg_pl["n_pool_het"]), "tau_train": round(dg_pl["tau"], 4),
            "pearson_r": np.nan, "spearman_rho": np.nan,
            "status": f"DIAGNOSTIC_PASS_NULL (Q={dg_pl['Q']:.1f}/{df_q}, z={z_q:+.2f})" if null_ok else f"WARN_Q={dg_pl['Q']:.1f}/{df_q}",
        })

    # Synthetic recovery check (+0.60 runs/ball high stress)
    syn_df = reg_v41.copy()
    syn_df["batter_runs"] = syn_df["batter_runs"].astype(float)
    elig_pool = sorted(base_bat_ref.loc[_precision_eligible_mask(base_bat_ref), "player_id"].tolist())
    rng = np.random.default_rng(42)
    inj_ids = list(rng.choice(elig_pool, size=min(10, len(elig_pool)), replace=False))
    inj_mask = (syn_df["striker_id"].isin(inj_ids)) & (syn_df["BATTING_RESOURCE_STRESS"] >= 0.75) & (syn_df["is_ball_faced"] == 1)
    syn_df.loc[inj_mask, "batter_runs"] = syn_df.loc[inj_mask, "batter_runs"] + 0.60
    r_syn, dg_syn, _, _ = fit_v41_two_stage(syn_df, role="batter", outcome="batter_runs", scale=100.0)
    top15_syn = r_syn[_precision_eligible_mask(r_syn)].sort_values("empirical_bayes_delta", ascending=False)["player_id"].head(15).tolist()
    hits = len(set(inj_ids) & set(top15_syn))
    records.append({
        "claim_category": "ENGINEERING_DIAGNOSTIC_ONLY",
        "validation_family": "SYNTHETIC_SIGNAL_RECOVERY",
        "role": "batter", "metric": "batter_runs (+60 SR injected)", "split": "10_injected_eligible",
        "n_eval": int(len(inj_ids)), "tau_train": round(dg_syn["tau"], 3),
        "pearson_r": np.nan, "spearman_rho": round(hits / max(len(inj_ids), 1), 3),
        "status": f"DIAGNOSTIC_RECOVERY_{hits}_OF_{len(inj_ids)}_IN_TOP15",
    })

    val_df = pd.DataFrame(records)
    val_df.to_csv(os.path.join(output_dir, "V4_1_VALIDATION_MATRIX.csv"), index=False)
    return val_df


def run_full_v41_pipeline(
    reg_ctx: pd.DataFrame,
    reg_b3: pd.DataFrame,
    score_audit_summary: Dict[str, Any],
    output_dir: str = "data/outputs/v4_1",
    bootstrap_iter: int = 1000,
    bootstrap_seed: int = 42,
) -> Dict[str, Any]:
    """Execute complete V4.1 estimation, global ranking bootstrap, decomposition & comparisons."""
    os.makedirs(output_dir, exist_ok=True)
    reg_v41 = add_v41_pressure_aliases(reg_b3)

    bat_raw, diag_bat, m_fwl_bat, work_bat = fit_v41_two_stage(
        reg_v41, role="batter", outcome="batter_runs", scale=100.0,
        p_col="BATTING_RESOURCE_STRESS", span=0.75, eb_method="reml",
        lam_match=60.0, lam_player=60.0, lam_opp=60.0,
    )
    bat_out, diag_bat_out, _, _ = fit_v41_two_stage(
        reg_v41, role="batter", outcome="is_striker_out", scale=-100.0,
        p_col="BATTING_RESOURCE_STRESS", span=0.75, eb_method="reml",
        lam_match=60.0, lam_player=60.0, lam_opp=60.0,
    )
    bowl_raw, diag_bowl, m_fwl_bowl, work_bowl = fit_v41_two_stage(
        reg_v41, role="bowler", outcome="batter_runs", scale=-100.0,
        p_col="BOWLING_SCORING_THREAT", span=0.75, eb_method="reml",
        lam_match=60.0, lam_player=60.0, lam_opp=60.0,
    )
    bowl_ctrl, diag_bowl_ctrl, _, _ = fit_v41_two_stage(
        reg_v41, role="bowler", outcome="is_ctrl_ball", scale=100.0,
        p_col="BOWLING_SCORING_THREAT", span=0.75, eb_method="reml",
        lam_match=60.0, lam_player=60.0, lam_opp=60.0,
    )
    bowl_wkt, diag_bowl_wkt, _, _ = fit_v41_two_stage(
        reg_v41, role="bowler", outcome="is_bowler_wicket", scale=100.0,
        p_col="BOWLING_SCORING_THREAT", span=0.75, eb_method="reml",
        lam_match=60.0, lam_player=60.0, lam_opp=60.0,
    )

    # Correlated global match-cluster bootstrap at the complete-ranking level
    bat_elig_ids = bat_raw.loc[_precision_eligible_mask(bat_raw), "player_id"].astype(int).tolist()
    bat_pool_ids = bat_raw.loc[(bat_raw["n_hi"] >= 30) & (bat_raw["n_lo"] >= 30) & (bat_raw["sxx"] > 2.0), "player_id"].astype(int).tolist()
    bat_boot, bat_corr_diag = run_global_match_cluster_bootstrap(
        m_fwl_bat, eligible_ids=bat_elig_ids, pool_ids=bat_pool_ids, span=0.75,
        n_iter=bootstrap_iter, seed=bootstrap_seed,
    )

    bowl_elig_ids = bowl_raw.loc[_precision_eligible_mask(bowl_raw), "player_id"].astype(int).tolist()
    bowl_pool_ids = bowl_raw.loc[(bowl_raw["n_hi"] >= 30) & (bowl_raw["n_lo"] >= 30) & (bowl_raw["sxx"] > 2.0), "player_id"].astype(int).tolist()
    bowl_boot, bowl_corr_diag = run_global_match_cluster_bootstrap(
        m_fwl_bowl, eligible_ids=bowl_elig_ids, pool_ids=bowl_pool_ids, span=0.75,
        n_iter=bootstrap_iter, seed=bootstrap_seed + 1,
    )

    bat_full = _assign_v41_tiers(bat_raw.merge(bat_boot, on="player_id", how="left"))
    bat_full = bat_full.merge(
        bat_out[["player_id", "context_adjusted_delta", "empirical_bayes_delta", "eb_high_performance"]].rename(columns={
            "context_adjusted_delta": "sec_dismissal_avoid_adj_delta",
            "empirical_bayes_delta": "sec_dismissal_avoid_eb_delta",
            "eb_high_performance": "sec_dismissal_avoid_eb_hi",
        }),
        on="player_id", how="left",
    )

    bowl_full = _assign_v41_tiers(bowl_raw.merge(bowl_boot, on="player_id", how="left"))
    bowl_full = bowl_full.merge(
        bowl_ctrl[["player_id", "context_adjusted_delta", "empirical_bayes_delta", "eb_high_performance"]].rename(columns={
            "context_adjusted_delta": "sec_dot_ctrl_adj_delta",
            "empirical_bayes_delta": "sec_dot_ctrl_eb_delta",
            "eb_high_performance": "sec_dot_ctrl_eb_hi",
        }),
        on="player_id", how="left",
    ).merge(
        bowl_wkt[["player_id", "context_adjusted_delta", "empirical_bayes_delta", "eb_high_performance"]].rename(columns={
            "context_adjusted_delta": "sec_wicket_adj_delta",
            "empirical_bayes_delta": "sec_wicket_eb_delta",
            "eb_high_performance": "sec_wicket_eb_hi",
        }),
        on="player_id", how="left",
    )

    # Exact raw vs adjusted decomposition & bowler field separation
    bat_decomp = build_raw_vs_adjusted_decomposition(bat_full, work_bat, role="batter")
    bowl_decomp = build_raw_vs_adjusted_decomposition(bowl_full, work_bowl, role="bowler")
    decomp_df = export_decomposition_and_bowler_audit(bat_decomp, bowl_decomp, reg_v41, output_dir=output_dir)

    # Rank probabilities across all precision-eligible candidates
    prob_cols = [
        "role", "player_id", "player_name", "formats_played", "metric_unit",
        "total_balls", "total_matches", "n_hi", "n_norm", "n_lo", "cs_matches",
        "raw_high_performance", "raw_normal_performance", "raw_observed_delta",
        "context_adjusted_high_performance", "context_adjusted_normal_performance",
        "context_adjusted_delta", "empirical_bayes_delta",
        "lower_confidence_bound", "upper_confidence_bound", "probability_positive_effect",
        "boot_mean_delta", "boot_ci_low", "boot_ci_high", "boot_prob_pos",
        "boot_rank_mean", "boot_rank_median", "boot_rank_ci_low", "boot_rank_ci_high",
        "prob_top_10", "precision_eligible", "strict_reliable_flag", "reliability_tier",
    ]
    bat_elig = bat_decomp[bat_decomp["precision_eligible"]].sort_values(["empirical_bayes_delta", "player_id"], ascending=[False, True]).copy().reset_index(drop=True)
    bat_elig.insert(0, "provisional_rank", np.arange(1, len(bat_elig) + 1))

    bowl_elig = bowl_decomp[bowl_decomp["precision_eligible"]].sort_values(["empirical_bayes_delta", "player_id"], ascending=[False, True]).copy().reset_index(drop=True)
    bowl_elig.insert(0, "provisional_rank", np.arange(1, len(bowl_elig) + 1))

    rank_probs_df = pd.concat([bat_elig[["provisional_rank"] + prob_cols], bowl_elig[["provisional_rank"] + prob_cols]], ignore_index=True)
    rank_probs_df.to_csv(os.path.join(output_dir, "V4_1_RANK_PROBABILITIES.csv"), index=False)

    # V4_1_FINAL_SHORTLIST.csv (Top 10 Batters + Top 10 Bowlers ordered strictly by empirical_bayes_delta)
    t10_bat = bat_elig.head(10).copy()
    t10_bowl = bowl_elig.head(10).copy()
    shortlist_df = pd.concat([t10_bat[["provisional_rank"] + prob_cols], t10_bowl[["provisional_rank"] + prob_cols]], ignore_index=True)
    shortlist_df["shortlist_status"] = "PROVISIONAL_CANDIDATE_ORDER (ALL_95PCT_CI_CROSS_ZERO)"
    shortlist_df["release_decision"] = "V4.1 PROVISIONAL — RESOURCE STRESS"
    shortlist_df.to_csv(os.path.join(output_dir, "V4_1_FINAL_SHORTLIST.csv"), index=False)

    # Eligibility precision analysis, model comparison, and separated validation
    elig_prec_df = build_eligibility_precision_analysis(bat_decomp, bowl_decomp, output_dir=output_dir)
    comp_df, joint_dfs = build_model_comparison(reg_v41, bat_decomp, diag_bat, bowl_decomp, diag_bowl, output_dir=output_dir)
    val_df = run_v41_validation_matrix(reg_ctx, reg_v41, output_dir=output_dir)

    bat_rel_cnt = int(bat_elig["strict_reliable_flag"].sum())
    bowl_rel_cnt = int(bowl_elig["strict_reliable_flag"].sum())
    release_status = "V4.1 PROVISIONAL — RESOURCE STRESS"

    sot = {
        "model_version": "v4.1-resource-stress-reml",
        "release_status": release_status,
        "chase_score_reconstruction_blocked": bool(score_audit_summary["chase_score_reconstruction_blocked"]),
        "pressure_aliases": {
            "bat_pressure": "BATTING_RESOURCE_STRESS",
            "bowl_pressure": "BOWLING_SCORING_THREAT",
        },
        "operational_precision_gate": V41_OPERATIONAL_PRECISION_GATE,
        "v4_legacy_gate_reference": V4_LEGACY_GATE,
        "score_audit_summary": score_audit_summary,
        "diagnostics": {
            "batter_runs": diag_bat,
            "batter_dismissal_avoid": diag_bat_out,
            "bowler_runs_saved_proxy": diag_bowl,
            "bowler_dot_control": diag_bowl_ctrl,
            "bowler_wicket": diag_bowl_wkt,
            "batter_global_bootstrap": bat_corr_diag,
            "bowler_global_bootstrap": bowl_corr_diag,
        },
        "counts": {
            "batter_total": int(len(bat_decomp)),
            "batter_precision_eligible": int(len(bat_elig)),
            "batter_reliable": bat_rel_cnt,
            "batter_provisional": int(len(bat_elig) - bat_rel_cnt),
            "bowler_total": int(len(bowl_decomp)),
            "bowler_precision_eligible": int(len(bowl_elig)),
            "bowler_reliable": bowl_rel_cnt,
            "bowler_provisional": int(len(bowl_elig) - bowl_rel_cnt),
        },
        "shortlist_batters": t10_bat[["provisional_rank", "player_id", "player_name", "empirical_bayes_delta", "context_adjusted_delta", "raw_observed_delta", "lower_confidence_bound", "upper_confidence_bound", "probability_positive_effect", "boot_rank_ci_low", "boot_rank_ci_high", "prob_top_10", "reliability_tier"]].to_dict(orient="records"),
        "shortlist_bowlers": t10_bowl[["provisional_rank", "player_id", "player_name", "empirical_bayes_delta", "context_adjusted_delta", "raw_observed_delta", "lower_confidence_bound", "upper_confidence_bound", "probability_positive_effect", "boot_rank_ci_low", "boot_rank_ci_high", "prob_top_10", "reliability_tier"]].to_dict(orient="records"),
    }
    import json
    with open(os.path.join(output_dir, "V4_1_SOURCE_OF_TRUTH.json"), "w", encoding="utf-8") as f:
        json.dump(sot, f, indent=2)

    return {
        "shortlist": shortlist_df,
        "rank_probabilities": rank_probs_df,
        "decomposition": decomp_df,
        "eligibility_precision": elig_prec_df,
        "model_comparison": comp_df,
        "validation": val_df,
        "bat_elig": bat_elig,
        "bowl_elig": bowl_elig,
        "bat_all": bat_decomp,
        "bowl_all": bowl_decomp,
        "sot": sot,
    }
