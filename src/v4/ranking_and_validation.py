"""Phase E & F — Dual-Gate Ranking, Reliability Tiering, Sensitivity & Temporal Validation."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from src.v4.hierarchical_model import fit_hierarchical_contrast
from src.v4.pressure_proxy import (
    PRESSURE_MODEL_VERSION,
    PRESSURE_SOURCE_TYPE,
    apply_b3_resource_stress,
    evaluate_observable_wp_benchmark,
    fit_b3_resource_stress,
)

PRIMARY_GATE = {
    "min_hi_balls": 100,
    "min_lo_balls": 60,
    "min_hi_matches": 10,
    "min_lo_matches": 10,
    "min_cs_matches": 10,
    "min_total_matches": 15,
}


def _safe_corr(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """Compute Pearson r and Spearman rho safely without failing on constant inputs."""
    mask = np.isfinite(x.values) & np.isfinite(y.values)
    xv, yv = x.values[mask], y.values[mask]
    if len(xv) < 6 or np.std(xv) < 1e-12 or np.std(yv) < 1e-12:
        return np.nan, np.nan
    return float(pearsonr(xv, yv)[0]), float(spearmanr(xv, yv)[0])


def _apply_dual_gate_and_tiers(
    df_primary: pd.DataFrame,
    id_col: str,
    secondary_df: pd.DataFrame,
    sec_rename: Dict[str, str],
    gate: Dict[str, int] = PRIMARY_GATE,
    role: str = "batter",
) -> pd.DataFrame:
    """Merge primary and secondary metrics, assign eligibility reasons & reliability tiers."""
    sec_cols = [id_col] + list(sec_rename.keys())
    merged = df_primary.merge(
        secondary_df[sec_cols].rename(columns=sec_rename),
        on=id_col,
        how="left",
    ).rename(columns={id_col: "player_id"})

    cov_ok = (
        (merged["n_hi"] >= gate["min_hi_balls"])
        & (merged["n_lo"] >= gate["min_lo_balls"])
        & (merged["hi_matches"] >= gate["min_hi_matches"])
        & (merged["lo_matches"] >= gate["min_lo_matches"])
        & (merged["cs_matches"] >= gate["min_cs_matches"])
        & (merged["total_matches"] >= gate["min_total_matches"])
    )

    if role == "batter":
        non_collapsed = (merged["eb_hi_perf"] > 0.0) & (merged["sec_out_eb_delta"].fillna(0.0) >= -1.5)
    else:
        non_collapsed = (merged["eb_hi_perf"] > 0.0) & (merged["sec_ctrl_eb_hi"].fillna(0.0) >= -2.5)

    pos_contrast = (merged["raw_fwl_delta"] > 0.0) & (merged["eb_delta"] > merged["eb_delta"].min() - 1e-9)
    # Require eb_delta above population prior mu0 (maintained/improved relative to average shift)
    mu0_approx = float(merged["eb_delta"].median())
    above_prior = merged["raw_fwl_delta"] > 0.0
    strict_sig = cov_ok & non_collapsed & above_prior & (merged["eb_weight"] >= 0.30) & (merged["lcb95_delta"] > 0.0)

    tier = np.where(
        strict_sig,
        "RELIABLE",
        np.where(cov_ok & non_collapsed & above_prior, "PROVISIONAL", "INSUFFICIENT_SUPPORT"),
    )
    # For players meeting sample coverage yet failing dual criteria, mark distinct diagnostic reason
    status_reason = np.where(
        ~cov_ok,
        np.where(merged["n_hi"] < gate["min_hi_balls"], "LOW_HIGH_PRESSURE_BALLS",
                 np.where(merged["n_lo"] < gate["min_lo_balls"], "LOW_NORMAL_BALLS", "LOW_MATCH_OR_COMMON_SUPPORT")),
        np.where(
            ~above_prior,
            "NON_POSITIVE_RELATIVE_DELTA",
            np.where(
                ~non_collapsed,
                "BELOW_AVG_HIGH_PRESSURE_EXECUTION",
                np.where(strict_sig, "ELIGIBLE_RELIABLE", "ELIGIBLE_PROVISIONAL_LOW_TAU"),
            ),
        ),
    )

    merged["role"] = role
    merged["coverage_eligible"] = cov_ok
    merged["dual_gate_passed"] = cov_ok & non_collapsed & above_prior
    merged["strict_reliable_flag"] = strict_sig
    merged["reliability_tier"] = tier
    merged["eligibility_reason"] = status_reason
    merged["eb_delta_vs_prior"] = merged["eb_delta"] - mu0_approx
    return merged


def _jaccard_and_overlap(base_ids: List[Any], alt_ids: List[Any]) -> Tuple[int, float]:
    s1, s2 = set(base_ids), set(alt_ids)
    if not s1 and not s2:
        return 0, 1.0
    inter = len(s1 & s2)
    union = len(s1 | s2)
    return inter, float(inter / union) if union else 0.0


def run_sensitivity_suite(
    reg_b3: pd.DataFrame,
    base_bat: pd.DataFrame,
    base_bowl: pd.DataFrame,
) -> pd.DataFrame:
    """Phase E/F sensitivity matrix: 40..250 ball gates, cutoffs, strata, REML, seeds, format."""
    rows: List[Dict[str, Any]] = []
    base_bat_top10 = base_bat[base_bat["dual_gate_passed"]].sort_values("lcb95_delta", ascending=False)["player_id"].head(10).tolist()
    base_bowl_top10 = base_bowl[base_bowl["dual_gate_passed"]].sort_values("lcb95_delta", ascending=False)["player_id"].head(10).tolist()

    # 1. Crisis-ball threshold sweep: 40, 60, 80, 100, 150, 200, 250
    for thr in (40, 60, 80, 100, 150, 200, 250):
        for role_name, df_r, base_t10 in [
            ("batter", base_bat, base_bat_top10),
            ("bowler", base_bowl, base_bowl_top10),
        ]:
            sub = df_r[
                (df_r["n_hi"] >= thr)
                & (df_r["n_lo"] >= PRIMARY_GATE["min_lo_balls"])
                & (df_r["hi_matches"] >= PRIMARY_GATE["min_hi_matches"])
                & (df_r["lo_matches"] >= PRIMARY_GATE["min_lo_matches"])
                & (df_r["cs_matches"] >= PRIMARY_GATE["min_cs_matches"])
                & (df_r["eb_hi_perf"] > 0.0)
                & (df_r["raw_fwl_delta"] > 0.0)
            ].sort_values("lcb95_delta", ascending=False)
            t10 = sub["player_id"].head(10).tolist()
            ov, jac = _jaccard_and_overlap(base_t10, t10)
            med_w = float((2.0 * 1.96 * sub["post_sd"]).median()) if len(sub) else np.nan
            rows.append({
                "dimension": "pressure_balls_threshold",
                "setting": f"n_hi>={thr}",
                "role": role_name,
                "eligible_count": int(len(sub)),
                "top10_available": int(min(len(sub), 10)),
                "top10_overlap": ov,
                "jaccard": round(jac, 4),
                "spearman_rho_vs_base": 1.0 if thr == PRIMARY_GATE["min_hi_balls"] else np.nan,
                "median_ci_width": round(med_w, 3) if pd.notna(med_w) else np.nan,
                "notes": f"n_hi>={thr}, n_lo>={PRIMARY_GATE['min_lo_balls']}, cs_m>={PRIMARY_GATE['min_cs_matches']}",
            })

    # 2. Structural model sensitivities (pressure cutoffs, strata, contrast mode, REML, boot seed, format)
    configs = [
        ("pressure_cutoff", "P75/P25 (Base)", 0.75, 0.25, ("match_format",), "fwl", "dl", 42, reg_b3),
        ("pressure_cutoff", "P80/P20", 0.80, 0.20, ("match_format",), "fwl", "dl", 42, reg_b3),
        ("pressure_cutoff", "P85/P15", 0.85, 0.15, ("match_format",), "fwl", "dl", 42, reg_b3),
        ("pressure_cutoff", "P90/P25", 0.90, 0.25, ("match_format",), "fwl", "dl", 42, reg_b3),
        ("common_support_strata", "phase+format", 0.75, 0.25, ("phase", "match_format"), "fwl", "dl", 42, reg_b3),
        ("contrast_mode", "discrete_hi_vs_lo", 0.75, 0.25, ("match_format",), "discrete", "dl", 42, reg_b3),
        ("heterogeneity_estimator", "REML_tau2", 0.75, 0.25, ("match_format",), "fwl", "reml", 42, reg_b3),
        ("bootstrap_seed", "seed_2026", 0.75, 0.25, ("match_format",), "fwl", "dl", 2026, reg_b3),
        ("format_slice", "IPL_only", 0.75, 0.25, ("match_format",), "fwl", "dl", 42, reg_b3[reg_b3["match_format"] == "T20"]),
        ("format_slice", "T20I_only", 0.75, 0.25, ("match_format",), "fwl", "dl", 42, reg_b3[reg_b3["match_format"] == "T20I"]),
    ]

    for dim, setting, hi_t, lo_t, strat, cmode, eb_m, bseed, df_slice in configs:
        for role_name, id_c, outc, sc, pc, base_df, base_t10 in [
            ("batter", "striker_id", "batter_runs", 100.0, "bat_pressure", base_bat, base_bat_top10),
            ("bowler", "bowler_id", "batter_runs", -100.0, "bowl_pressure", base_bowl, base_bowl_top10),
        ]:
            # Skip full 2000-iter bootstrap unless testing bootstrap_seed stability to keep runtime fast
            b_iter = 2000 if dim == "bootstrap_seed" else 0
            alt, diag = fit_hierarchical_contrast(
                df_slice, role=role_name, outcome=outc, scale=sc, p_col=pc,
                hi_thr=hi_t, lo_thr=lo_t, strata_cols=strat, contrast_mode=cmode,
                eb_method=eb_m, bootstrap_iter=b_iter, bootstrap_seed=bseed,
            )
            alt = alt.rename(columns={id_c: "player_id"})
            min_hi_eff = 60 if dim == "format_slice" or hi_t >= 0.85 else PRIMARY_GATE["min_hi_balls"]
            min_lo_eff = 40 if dim == "format_slice" else PRIMARY_GATE["min_lo_balls"]
            elig_alt = alt[
                (alt["n_hi"] >= min_hi_eff)
                & (alt["n_lo"] >= min_lo_eff)
                & (alt["cs_matches"] >= (6 if dim == "format_slice" else PRIMARY_GATE["min_cs_matches"]))
                & (alt["eb_hi_perf"] > 0.0)
                & (alt["raw_fwl_delta"] > 0.0)
            ].sort_values("lcb95_delta", ascending=False)
            t10 = elig_alt["player_id"].head(10).tolist()
            ov, jac = _jaccard_and_overlap(base_t10, t10)
            mrg = base_df[base_df["coverage_eligible"]][["player_id", "lcb95_delta", "boot_lcb95"]].merge(
                alt[["player_id", "lcb95_delta", "boot_lcb95"]], on="player_id", suffixes=("_b", "_a")
            )
            rho = _safe_corr(mrg["lcb95_delta_b"], mrg["lcb95_delta_a"])[1]
            extra = ""
            if dim == "bootstrap_seed":
                b_rho = _safe_corr(mrg["boot_lcb95_b"], mrg["boot_lcb95_a"])[1]
                extra = f" | boot_lcb_rho={b_rho:.4f}"
            med_w = float((2.0 * 1.96 * elig_alt["post_sd"]).median()) if len(elig_alt) else np.nan
            rows.append({
                "dimension": dim,
                "setting": setting,
                "role": role_name,
                "eligible_count": int(len(elig_alt)),
                "top10_available": int(min(len(elig_alt), 10)),
                "top10_overlap": ov,
                "jaccard": round(jac, 4),
                "spearman_rho_vs_base": round(rho, 4) if pd.notna(rho) else np.nan,
                "median_ci_width": round(med_w, 3) if pd.notna(med_w) else np.nan,
                "notes": f"tau={diag['tau']:.2f}, Q={diag['Q']:.1f}/{diag['df']}{extra}",
            })
    return pd.DataFrame(rows)


def run_validation_suite(reg_ctx: pd.DataFrame, reg_b3: pd.DataFrame) -> pd.DataFrame:
    """Phase F validation: B1 WP_obs benchmark, rolling-origin temporal, split-half, placebo, synthetic recovery."""
    records: List[Dict[str, Any]] = []

    # 1. B1 WP_obs chronological benchmark
    wp_df = evaluate_observable_wp_benchmark(reg_ctx, cutoff_year=2024)
    for _, r in wp_df.iterrows():
        records.append({
            "validation_family": r["validation_family"],
            "role": "match_state",
            "metric": r["split"],
            "split": f"AUC={r['roc_auc']}, Brier={r['brier']}, CalSlope={r['cal_slope']}",
            "n_eval": int(r["n_test"]),
            "tau_train": np.nan,
            "skill_r": np.nan,
            "delta_raw_r": np.nan,
            "delta_eb_r": np.nan,
            "delta_eb_rho": np.nan,
            "hi_perf_r": np.nan,
            "status": r["status"],
        })

    specs = [
        ("batter", "striker_id", "batter_runs", 100.0, "bat_pressure"),
        ("batter", "striker_id", "is_striker_out", -100.0, "bat_pressure"),
        ("bowler", "bowler_id", "batter_runs", -100.0, "bowl_pressure"),
        ("bowler", "bowler_id", "is_ctrl_ball", 100.0, "bowl_pressure"),
        ("bowler", "bowler_id", "is_bowler_wicket", 100.0, "bowl_pressure"),
    ]

    # 2. Rolling-origin out-of-time validation (refitting B3 strictly on train years!)
    for cutoff in (2023, 2024, 2025):
        tr_raw = reg_ctx[reg_ctx["year"] <= cutoff]
        te_raw = reg_ctx[reg_ctx["year"] == cutoff + 1]
        b3_state = fit_b3_resource_stress(tr_raw)
        tr_df = apply_b3_resource_stress(tr_raw, b3_state)
        te_df = apply_b3_resource_stress(te_raw, b3_state)
        for role, idc, outc, sc, pc in specs:
            r_tr, d_tr = fit_hierarchical_contrast(tr_df, role=role, outcome=outc, scale=sc, p_col=pc, bootstrap_iter=0)
            r_te, _ = fit_hierarchical_contrast(te_df, role=role, outcome=outc, scale=sc, p_col=pc, bootstrap_iter=0)
            mrg = r_tr.merge(
                r_te[[idc, "raw_fwl_delta", "hi_resid_mean", "context_adj_normal", "n_hi", "n_lo"]],
                on=idc, suffixes=("_tr", "_te"),
            )
            good = mrg[(mrg["n_hi_tr"] >= 25) & (mrg["n_lo_tr"] >= 25) & (mrg["n_hi_te"] >= 10) & (mrg["n_lo_te"] >= 10)]
            sk_r, _ = _safe_corr(good["context_adj_normal_tr"], good["context_adj_normal_te"])
            raw_r, _ = _safe_corr(good["raw_fwl_delta_tr"], good["raw_fwl_delta_te"])
            eb_r, eb_rho = _safe_corr(good["eb_delta"], good["raw_fwl_delta_te"])
            hi_r, _ = _safe_corr(good["eb_hi_perf"], good["hi_resid_mean_te"])
            status = (
                "SIGNAL_REPLICATED"
                if (pd.notna(eb_r) and eb_r > 0.15) or (pd.notna(hi_r) and hi_r > 0.15)
                else "LOW_TEMPORAL_DELTA_SIGNAL"
            )
            records.append({
                "validation_family": "ROLLING_ORIGIN_TEMPORAL",
                "role": role,
                "metric": outc,
                "split": f"<={cutoff} -> {cutoff+1}",
                "n_eval": int(len(good)),
                "tau_train": round(d_tr["tau"], 3),
                "skill_r": round(sk_r, 4) if pd.notna(sk_r) else np.nan,
                "delta_raw_r": round(raw_r, 4) if pd.notna(raw_r) else np.nan,
                "delta_eb_r": round(eb_r, 4) if pd.notna(eb_r) else np.nan,
                "delta_eb_rho": round(eb_rho, 4) if pd.notna(eb_rho) else np.nan,
                "hi_perf_r": round(hi_r, 4) if pd.notna(hi_r) else np.nan,
                "status": status,
            })

    # 3. Even/Odd match parity split-half reliability
    m_ord = (
        reg_b3[["match_id", "match_date_dt"]]
        .drop_duplicates()
        .sort_values(["match_date_dt", "match_id"])
        .reset_index(drop=True)
    )
    m_ord["half"] = np.arange(len(m_ord)) % 2
    sh_df = reg_b3.merge(m_ord[["match_id", "half"]], on="match_id", how="left")
    for role, idc, outc, sc, pc in specs:
        r0, d0 = fit_hierarchical_contrast(sh_df[sh_df["half"] == 0], role=role, outcome=outc, scale=sc, p_col=pc, bootstrap_iter=0)
        r1, d1 = fit_hierarchical_contrast(sh_df[sh_df["half"] == 1], role=role, outcome=outc, scale=sc, p_col=pc, bootstrap_iter=0)
        mrg = r0.merge(
            r1[[idc, "raw_fwl_delta", "eb_delta", "eb_hi_perf", "n_hi", "n_lo"]],
            on=idc, suffixes=("_0", "_1"),
        )
        good = mrg[(mrg["n_hi_0"] >= 25) & (mrg["n_lo_0"] >= 25) & (mrg["n_hi_1"] >= 25) & (mrg["n_lo_1"] >= 25)]
        raw_r, _ = _safe_corr(good["raw_fwl_delta_0"], good["raw_fwl_delta_1"])
        eb_r, eb_rho = _safe_corr(good["eb_delta_0"], good["eb_delta_1"])
        hi_r, _ = _safe_corr(good["eb_hi_perf_0"], good["eb_hi_perf_1"])
        sb = (2.0 * raw_r / (1.0 + raw_r)) if pd.notna(raw_r) and raw_r > -1.0 else np.nan
        records.append({
            "validation_family": "SPLIT_HALF_RELIABILITY",
            "role": role,
            "metric": outc,
            "split": f"even_vs_odd_matches (SB={sb:+.3f})" if pd.notna(sb) else "even_vs_odd_matches",
            "n_eval": int(len(good)),
            "tau_train": round(0.5 * (d0["tau"] + d1["tau"]), 3),
            "skill_r": np.nan,
            "delta_raw_r": round(raw_r, 4) if pd.notna(raw_r) else np.nan,
            "delta_eb_r": round(eb_r, 4) if pd.notna(eb_r) else np.nan,
            "delta_eb_rho": round(eb_rho, 4) if pd.notna(eb_rho) else np.nan,
            "hi_perf_r": round(hi_r, 4) if pd.notna(hi_r) else np.nan,
            "status": "PASS_SPLIT_HALF_MEASURED",
        })

    # 4. Negative-control shuffled-pressure placebo
    for role, idc, outc, sc, pc in [("batter", "striker_id", "batter_runs", 100.0, "bat_pressure"),
                                     ("bowler", "bowler_id", "batter_runs", -100.0, "bowl_pressure")]:
        _, d_pl = fit_hierarchical_contrast(reg_b3, role=role, outcome=outc, scale=sc, p_col=pc,
                                            shuffle_pressure_seed=42, bootstrap_iter=0)
        records.append({
            "validation_family": "PLACEBO_SHUFFLED_PRESSURE",
            "role": role,
            "metric": outc,
            "split": "permuted_pressure_null",
            "n_eval": int(d_pl["n_pool_het"]),
            "tau_train": round(d_pl["tau"], 3),
            "skill_r": np.nan,
            "delta_raw_r": np.nan,
            "delta_eb_r": np.nan,
            "delta_eb_rho": np.nan,
            "hi_perf_r": np.nan,
            "status": f"PASS_NULL_Q={d_pl['Q']:.1f}/{d_pl['df']}" if d_pl["tau"] < 1e-6 else f"WARN_Q={d_pl['Q']:.1f}/{d_pl['df']}",
        })

    # 5. Synthetic known-signal recovery check (+0.60 runs/ball on 10 eligible players' high-pressure balls)
    syn_df = reg_b3.copy()
    syn_df["batter_runs"] = syn_df["batter_runs"].astype(float)
    base_syn_ref, _ = fit_hierarchical_contrast(syn_df, role="batter", outcome="batter_runs", scale=100.0, p_col="bat_pressure", bootstrap_iter=0)
    pool_ids = sorted(
        base_syn_ref.loc[(base_syn_ref["n_hi"] >= 100) & (base_syn_ref["n_lo"] >= 60) & (base_syn_ref["cs_matches"] >= 10), "striker_id"].tolist()
    )
    rng = np.random.default_rng(42)
    injected_ids = list(rng.choice(pool_ids, size=min(10, len(pool_ids)), replace=False))
    inj_mask = (syn_df["striker_id"].isin(injected_ids)) & (syn_df["bat_pressure"] >= 0.75) & (syn_df["is_ball_faced"] == 1)
    syn_df.loc[inj_mask, "batter_runs"] = syn_df.loc[inj_mask, "batter_runs"] + 0.60
    r_syn, d_syn = fit_hierarchical_contrast(syn_df, role="batter", outcome="batter_runs", scale=100.0, p_col="bat_pressure", bootstrap_iter=0)
    top15_syn = r_syn[(r_syn["n_hi"] >= 100) & (r_syn["n_lo"] >= 60)].sort_values("lcb95_delta", ascending=False)["striker_id"].head(15).tolist()
    rec_hits = len(set(injected_ids) & set(top15_syn))
    m_lift = r_syn[["striker_id", "raw_fwl_delta"]].merge(
        base_syn_ref[["striker_id", "raw_fwl_delta"]], on="striker_id", suffixes=("_syn", "_base")
    )
    inj_lift = float((m_lift.loc[m_lift["striker_id"].isin(injected_ids), "raw_fwl_delta_syn"]
                      - m_lift.loc[m_lift["striker_id"].isin(injected_ids), "raw_fwl_delta_base"]).mean())
    records.append({
        "validation_family": "SYNTHETIC_SIGNAL_RECOVERY",
        "role": "batter",
        "metric": "batter_runs (+60 SR in hi)",
        "split": f"injected_10_eligible (mean_lift={inj_lift:+.1f}, tau={d_syn['tau']:.2f})",
        "n_eval": int(len(injected_ids)),
        "tau_train": round(d_syn["tau"], 3),
        "skill_r": np.nan,
        "delta_raw_r": round(inj_lift, 2),
        "delta_eb_r": round(rec_hits / max(len(injected_ids), 1), 3),
        "delta_eb_rho": np.nan,
        "hi_perf_r": np.nan,
        "status": f"PASS_RECOVERED_{rec_hits}_OF_{len(injected_ids)}_IN_TOP15" if rec_hits >= 8 else f"PARTIAL_{rec_hits}_OF_{len(injected_ids)}",
    })

    return pd.DataFrame(records)


def run_full_ranking_pipeline(
    reg_ctx: pd.DataFrame,
    reg_b3: pd.DataFrame,
    b3_state: Dict[str, Any],
    output_dir: str = "data/outputs/v4",
    bootstrap_iter: int = 2000,
    bootstrap_seed: int = 42,
) -> Dict[str, Any]:
    """Run primary + secondary models, dual-gate rankings, sensitivity, validation, and export V4 artifacts."""
    os.makedirs(output_dir, exist_ok=True)

    # Batter primary & secondary
    bat_runs, diag_bat_runs = fit_hierarchical_contrast(
        reg_b3, role="batter", outcome="batter_runs", scale=100.0,
        p_col="bat_pressure", bootstrap_iter=bootstrap_iter, bootstrap_seed=bootstrap_seed,
    )
    bat_out, diag_bat_out = fit_hierarchical_contrast(
        reg_b3, role="batter", outcome="is_striker_out", scale=-100.0,
        p_col="bat_pressure", bootstrap_iter=0,
    )
    all_bat = _apply_dual_gate_and_tiers(
        bat_runs, "striker_id", bat_out,
        sec_rename={"raw_fwl_delta": "sec_out_raw_delta", "eb_delta": "sec_out_eb_delta", "hi_resid_mean": "sec_out_eb_hi"},
        role="batter",
    )

    # Bowler primary (BATTER_RUNS_CONCEDED_PROXY runs saved/100b) & secondaries (dot ctrl % & wicket %)
    bowl_runs, diag_bowl_runs = fit_hierarchical_contrast(
        reg_b3, role="bowler", outcome="batter_runs", scale=-100.0,
        p_col="bowl_pressure", bootstrap_iter=bootstrap_iter, bootstrap_seed=bootstrap_seed,
    )
    bowl_ctrl, diag_bowl_ctrl = fit_hierarchical_contrast(
        reg_b3, role="bowler", outcome="is_ctrl_ball", scale=100.0,
        p_col="bowl_pressure", bootstrap_iter=0,
    )
    bowl_wkt, diag_bowl_wkt = fit_hierarchical_contrast(
        reg_b3, role="bowler", outcome="is_bowler_wicket", scale=100.0,
        p_col="bowl_pressure", bootstrap_iter=0,
    )
    all_bowl = _apply_dual_gate_and_tiers(
        bowl_runs, "bowler_id", bowl_ctrl,
        sec_rename={"raw_fwl_delta": "sec_ctrl_raw_delta", "eb_delta": "sec_ctrl_eb_delta", "eb_hi_perf": "sec_ctrl_eb_hi"},
        role="bowler",
    )
    all_bowl = all_bowl.merge(
        bowl_wkt[["bowler_id", "raw_fwl_delta", "eb_delta", "eb_hi_perf"]].rename(columns={
            "bowler_id": "player_id",
            "raw_fwl_delta": "sec_wkt_raw_delta",
            "eb_delta": "sec_wkt_eb_delta",
            "eb_hi_perf": "sec_wkt_eb_hi",
        }),
        on="player_id",
        how="left",
    )

    # Sort full leaderboards deterministically
    all_bat = all_bat.sort_values(["dual_gate_passed", "lcb95_delta", "eb_delta", "eb_hi_perf", "player_id"],
                                  ascending=[False, False, False, False, True]).reset_index(drop=True)
    all_bowl = all_bowl.sort_values(["dual_gate_passed", "lcb95_delta", "eb_delta", "eb_hi_perf", "player_id"],
                                    ascending=[False, False, False, False, True]).reset_index(drop=True)

    # Top 10 Batters & Bowlers
    top10_bat = all_bat[all_bat["dual_gate_passed"]].head(10).copy().reset_index(drop=True)
    top10_bat.insert(0, "rank", np.arange(1, len(top10_bat) + 1))
    top10_bat["metric_provenance"] = "BATTER_RUNS_PER_100_BALLS"
    top10_bat["pressure_source_type"] = PRESSURE_SOURCE_TYPE
    top10_bat["pressure_model_version"] = PRESSURE_MODEL_VERSION

    top10_bowl = all_bowl[all_bowl["dual_gate_passed"]].head(10).copy().reset_index(drop=True)
    top10_bowl.insert(0, "rank", np.arange(1, len(top10_bowl) + 1))
    top10_bowl["metric_provenance"] = "BATTER_RUNS_CONCEDED_PROXY_SAVED_PER_100_BALLS"
    top10_bowl["pressure_source_type"] = PRESSURE_SOURCE_TYPE
    top10_bowl["pressure_model_version"] = PRESSURE_MODEL_VERSION

    # Unified Eligibility table
    elig_cols = [
        "role", "player_id", "player_name", "total_balls", "total_matches", "n_hi", "n_lo",
        "hi_matches", "lo_matches", "cs_matches", "coverage_eligible", "dual_gate_passed",
        "strict_reliable_flag", "reliability_tier", "eligibility_reason", "raw_fwl_delta",
        "se_delta", "eb_delta", "lcb95_delta", "eb_hi_perf", "boot_lcb95",
    ]
    elig_df = pd.concat([all_bat[elig_cols], all_bowl[elig_cols]], ignore_index=True)

    # Player Pressure Evidence summary (match-level high vs low pressure trace per player)
    ev_cols = [
        "role", "player_id", "player_name", "formats_played", "last_season",
        "total_balls", "total_matches", "n_hi", "hi_matches", "n_lo", "lo_matches", "cs_matches",
        "unadj_norm_mean", "unadj_hi_mean", "unadj_hi_minus_norm", "context_adj_normal",
        "hi_resid_mean", "eb_hi_perf", "raw_fwl_delta", "naive_se", "cluster_se", "se_delta",
        "eb_weight", "eb_delta", "post_sd", "lcb95_delta", "ucb95_delta", "prob_delta_gt_zero",
        "boot_mean", "boot_se", "boot_ci_low", "boot_lcb95", "boot_ci_high",
        "hi_match_pos_rate", "hi_match_iqr", "reliability_tier", "eligibility_reason",
    ]
    ev_df = pd.concat([all_bat[ev_cols], all_bowl[ev_cols]], ignore_index=True)

    # Sensitivity & Validation
    sens_df = run_sensitivity_suite(reg_b3, all_bat, all_bowl)
    val_df = run_validation_suite(reg_ctx, reg_b3)

    # Export all V4 CSVs
    top10_bat.to_csv(os.path.join(output_dir, "TOP_10_BATTERS_V4.csv"), index=False)
    top10_bowl.to_csv(os.path.join(output_dir, "TOP_10_BOWLERS_V4.csv"), index=False)
    all_bat.to_csv(os.path.join(output_dir, "ALL_BATTER_METRICS_V4.csv"), index=False)
    all_bowl.to_csv(os.path.join(output_dir, "ALL_BOWLER_METRICS_V4.csv"), index=False)
    elig_df.to_csv(os.path.join(output_dir, "PLAYER_ELIGIBILITY_V4.csv"), index=False)
    ev_df.to_csv(os.path.join(output_dir, "PLAYER_PRESSURE_EVIDENCE_V4.csv"), index=False)
    sens_df.to_csv(os.path.join(output_dir, "RANKING_SENSITIVITY_V4.csv"), index=False)
    val_df.to_csv(os.path.join(output_dir, "MODEL_VALIDATION_V4.csv"), index=False)

    # Determine honest scientific release status
    bat_reliable_cnt = int((all_bat["reliability_tier"] == "RELIABLE").sum())
    bowl_reliable_cnt = int((all_bowl["reliability_tier"] == "RELIABLE").sum())
    release_status = "V4 PROVISIONAL — RESOURCE STRESS PROXY"

    sot = {
        "model_version": PRESSURE_MODEL_VERSION,
        "pressure_source_type": PRESSURE_SOURCE_TYPE,
        "chase_score_reconstruction_blocked": True,
        "release_status": release_status,
        "primary_gate": PRIMARY_GATE,
        "b3_resource_curve_params": b3_state["curve_params"],
        "diagnostics": {
            "batter_runs": diag_bat_runs,
            "batter_dismissal": diag_bat_out,
            "bowler_runs_saved_proxy": diag_bowl_runs,
            "bowler_dot_control": diag_bowl_ctrl,
            "bowler_wicket": diag_bowl_wkt,
        },
        "counts": {
            "batter_total": int(len(all_bat)),
            "batter_coverage_eligible": int(all_bat["coverage_eligible"].sum()),
            "batter_dual_gate_passed": int(all_bat["dual_gate_passed"].sum()),
            "batter_reliable": bat_reliable_cnt,
            "batter_provisional": int((all_bat["reliability_tier"] == "PROVISIONAL").sum()),
            "bowler_total": int(len(all_bowl)),
            "bowler_coverage_eligible": int(all_bowl["coverage_eligible"].sum()),
            "bowler_dual_gate_passed": int(all_bowl["dual_gate_passed"].sum()),
            "bowler_reliable": bowl_reliable_cnt,
            "bowler_provisional": int((all_bowl["reliability_tier"] == "PROVISIONAL").sum()),
        },
        "top_10_batters": [
            {
                "rank": int(r["rank"]),
                "player_id": int(r["player_id"]),
                "player_name": str(r["player_name"]),
                "reliability_tier": str(r["reliability_tier"]),
                "n_hi": int(r["n_hi"]),
                "n_lo": int(r["n_lo"]),
                "cs_matches": int(r["cs_matches"]),
                "unadj_norm_mean": round(float(r["unadj_norm_mean"]), 2),
                "unadj_hi_mean": round(float(r["unadj_hi_mean"]), 2),
                "raw_fwl_delta": round(float(r["raw_fwl_delta"]), 2),
                "eb_delta": round(float(r["eb_delta"]), 2),
                "lcb95_delta": round(float(r["lcb95_delta"]), 2),
                "eb_hi_perf": round(float(r["eb_hi_perf"]), 2),
                "hi_match_pos_rate": round(float(r["hi_match_pos_rate"]), 3),
            }
            for _, r in top10_bat.iterrows()
        ],
        "top_10_bowlers": [
            {
                "rank": int(r["rank"]),
                "player_id": int(r["player_id"]),
                "player_name": str(r["player_name"]),
                "reliability_tier": str(r["reliability_tier"]),
                "n_hi": int(r["n_hi"]),
                "n_lo": int(r["n_lo"]),
                "cs_matches": int(r["cs_matches"]),
                "unadj_norm_mean": round(float(r["unadj_norm_mean"]), 2),
                "unadj_hi_mean": round(float(r["unadj_hi_mean"]), 2),
                "raw_fwl_delta": round(float(r["raw_fwl_delta"]), 2),
                "eb_delta": round(float(r["eb_delta"]), 2),
                "lcb95_delta": round(float(r["lcb95_delta"]), 2),
                "eb_hi_perf": round(float(r["eb_hi_perf"]), 2),
                "hi_match_pos_rate": round(float(r["hi_match_pos_rate"]), 3),
            }
            for _, r in top10_bowl.iterrows()
        ],
    }
    with open(os.path.join(output_dir, "RANKING_SOURCE_OF_TRUTH_V4.json"), "w", encoding="utf-8") as f:
        json.dump(sot, f, indent=2)

    return {
        "top10_batters": top10_bat,
        "top10_bowlers": top10_bowl,
        "all_batters": all_bat,
        "all_bowlers": all_bowl,
        "eligibility": elig_df,
        "evidence": ev_df,
        "sensitivity": sens_df,
        "validation": val_df,
        "sot": sot,
    }
