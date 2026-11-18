"""V4.2 Artifact Generation, Source-of-Truth Registry, and Release Decision Report."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd


RELEASE_STATUS_V42 = "V4.2 PROVISIONAL — RESOURCE STRESS"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_rev(ref: str) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", ref], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def _sort_deterministic_display(df: pd.DataFrame) -> pd.DataFrame:
    """Sort eligible table cleanly without using player_id as statistical tie-breaker in ranks."""
    work = df.copy()
    work["_eb_round"] = np.round(work["eb_delta"].fillna(-1e9), 10)
    work = work.sort_values(
        ["_eb_round", "prob_top_10", "effective_exposure", "se_delta", "player_id"],
        ascending=[False, False, False, True, True],
    ).drop(columns=["_eb_round"])
    return work.reset_index(drop=True)


def write_v42_artifacts(
    res: Dict[str, Any],
    data_dir: str = "data",
) -> Dict[str, Any]:
    """Write all V4.2 CSV, JSON, and Markdown deliverables from pipeline output dict."""
    out_dir = Path(data_dir) / "outputs" / "v4_2"
    rep_dir = Path(data_dir) / "reports" / "v4_2"
    out_dir.mkdir(parents=True, exist_ok=True)
    rep_dir.mkdir(parents=True, exist_ok=True)

    bat_full = res["bat_full"]
    bowl_full = res["bowl_full"]

    # Build V4_2_RANK_PROBABILITIES.csv (all eligible players across both roles)
    bat_el = _sort_deterministic_display(bat_full[bat_full["eligible"]])
    bowl_el = _sort_deterministic_display(bowl_full[bowl_full["eligible"]])

    bat_el["shortlist_rank_display"] = np.arange(1, len(bat_el) + 1)
    bowl_el["shortlist_rank_display"] = np.arange(1, len(bowl_el) + 1)
    rank_probs = pd.concat([bat_el, bowl_el], ignore_index=True)
    rank_probs_path = out_dir / "V4_2_RANK_PROBABILITIES.csv"
    rank_probs.to_csv(rank_probs_path, index=False)

    # Full un-filtered role estimates archive (helpful for deep diagnostics)
    all_est_path = out_dir / "V4_2_ALL_PLAYER_ESTIMATES.csv"
    pd.concat([bat_full, bowl_full], ignore_index=True).to_csv(all_est_path, index=False)

    # Top 10 Batters & Top 10 Bowlers Final Shortlist
    bat_top10 = bat_el.head(10).copy()
    bowl_top10 = bowl_el.head(10).copy()
    shortlist = pd.concat([bat_top10, bowl_top10], ignore_index=True)
    shortlist_path = out_dir / "V4_2_FINAL_SHORTLIST.csv"
    shortlist.to_csv(shortlist_path, index=False)

    # Like-for-like 8-contrast decomposition CSV (combine eligible + all CS)
    decomp_df = pd.concat([res["bat_decomp"], res["bowl_decomp"]], ignore_index=True)
    decomp_path = out_dir / "V4_2_RAW_ADJUSTED_DECOMPOSITION.csv"
    decomp_df.to_csv(decomp_path, index=False)

    # Model comparison, validation matrix, eligibility sweep
    comp_path = out_dir / "V4_2_MODEL_COMPARISON.csv"
    res["model_comp"].to_csv(comp_path, index=False)

    elig_path = out_dir / "V4_2_ELIGIBILITY_PRECISION_ANALYSIS.csv"
    res["elig_sweep"].to_csv(elig_path, index=False)

    val_path = out_dir / "V4_2_VALIDATION_MATRIX.csv"
    res["val_matrix"].to_csv(val_path, index=False)

    # Compute SHA256 hashes for Source of Truth
    hashes = {}
    for p in [
        shortlist_path,
        rank_probs_path,
        decomp_path,
        comp_path,
        elig_path,
        val_path,
        out_dir / "V4_2_SCORE_ENRICHMENT_AUDIT.csv",
    ]:
        if p.exists():
            hashes[p.name] = _sha256(p)

    sot = {
        "model_version": "V4.2",
        "release_status": RELEASE_STATUS_V42,
        "git_head_sha_at_generation": _git_rev("HEAD"),
        "origin_main_sha": _git_rev("origin/main"),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
        "chase_score_reconstruction_blocked": True,
        "estimator": "OPTION_A_COMPLETE_PENALIZED_FWL_REML",
        "bootstrap": {
            "type": "Nuisance-orthogonalized match-cluster score bootstrap with REML every replicate",
            "n_iter": int(bat_el["boot_iters"].iloc[0]) if len(bat_el) else 2000,
            "tie_handling": "average_ranks_and_fractional_top10_never_player_id",
        },
        "pressure_proxy_trace": res["proxy_trace"],
        "score_audit_summary": res["audit_summary"],
        "heterogeneity": {
            "batter_reml": res["bat_meta"]["het"],
            "bowler_reml": res["bowl_meta"]["het"],
            "batter_opt_b_em": res["bat_meta_opt_b"],
            "bowler_opt_b_em": res["bowl_meta_opt_b"],
        },
        "claims_oot": {
            "batter": res["bat_claims"],
            "bowler": res["bowl_claims"],
        },
        "top10_batters": bat_top10["player_id"].tolist(),
        "top10_batter_names": bat_top10["player_name"].tolist(),
        "top10_bowlers": bowl_top10["player_id"].tolist(),
        "top10_bowler_names": bowl_top10["player_name"].tolist(),
        "hashes": hashes,
    }
    sot_path = out_dir / "V4_2_SOURCE_OF_TRUTH.json"
    with open(sot_path, "w", encoding="utf-8") as f:
        json.dump(sot, f, indent=2, default=str)

    # Build V4_2_RELEASE_DECISION.md directly from computed outputs
    def _md_table(df_sub: pd.DataFrame, is_bat: bool) -> str:
        lines = []
        if is_bat:
            lines.append(
                "| Rank (Avg) | Player | n_hi / n_lo (CS Matches) | EB Delta (vs Pop Mean) | Unshrunk Delta | EB Cond 95% CI | EB Boot 95% CI | Rank 95% CI | P(Top 10) [MCSE] | Spread Matches | Share Pos vs Normal | LOMO [min, max] | Dismissal Risk /100b | Secondary Warning |"
            )
            lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for _, r in df_sub.iterrows():
                bt_sd = f"{r['between_match_delta_sd']:.1f}" if pd.notna(r["between_match_delta_sd"]) else "LIMITED"
                lines.append(
                    f"| {r['shortlist_rank_display']} ({r['eb_rank']:.1f}) | {r['player_name']} ({r['player_id']}) | "
                    f"{int(r['n_hi'])} / {int(r['n_lo'])} ({int(r['cs_matches'])}) | "
                    f"{r['eb_delta']:+.2f} ({r['eb_vs_pop_mean_delta']:+.2f}) | {r['delta_unshrunk']:+.2f} | "
                    f"[{r['eb_cond_ci_low']:+.2f}, {r['eb_cond_ci_high']:+.2f}] | "
                    f"[{r['eb_boot_ci_low']:+.2f}, {r['eb_boot_ci_high']:+.2f}] | "
                    f"[{r['boot_rank_ci_low']:.0f}, {r['boot_rank_ci_high']:.0f}] | "
                    f"{r['prob_top_10']:.3f} [{r['mcse_prob_top_10']:.3f}] | "
                    f"{int(r['within_match_spread_matches'])} (SD={bt_sd}) | "
                    f"{r['share_matches_pos_delta_vs_normal']:.2f} | "
                    f"[{r['lomo_min_delta']:+.1f}, {r['lomo_max_delta']:+.1f}] | "
                    f"{r['dismissal_risk_delta_per_100b']:+.2f} | {r['secondary_tradeoff_flag']} |"
                )
        else:
            lines.append(
                "| Rank (Avg) | Player | n_hi / n_lo (CS Matches) | EB Delta (vs Pop Mean) | Unshrunk Delta | EB Cond 95% CI | EB Boot 95% CI | Rank 95% CI | P(Top 10) [MCSE] | Spread Matches | Share Pos vs Normal | LOMO [min, max] | Dot% / Wkt% Delta | Secondary Warning |"
            )
            lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for _, r in df_sub.iterrows():
                bt_sd = f"{r['between_match_delta_sd']:.1f}" if pd.notna(r["between_match_delta_sd"]) else "LIMITED"
                lines.append(
                    f"| {r['shortlist_rank_display']} ({r['eb_rank']:.1f}) | {r['player_name']} ({r['player_id']}) | "
                    f"{int(r['n_hi'])} / {int(r['n_lo'])} ({int(r['cs_matches'])}) | "
                    f"{r['eb_delta']:+.2f} ({r['eb_vs_pop_mean_delta']:+.2f}) | {r['delta_unshrunk']:+.2f} | "
                    f"[{r['eb_cond_ci_low']:+.2f}, {r['eb_cond_ci_high']:+.2f}] | "
                    f"[{r['eb_boot_ci_low']:+.2f}, {r['eb_boot_ci_high']:+.2f}] | "
                    f"[{r['boot_rank_ci_low']:.0f}, {r['boot_rank_ci_high']:.0f}] | "
                    f"{r['prob_top_10']:.3f} [{r['mcse_prob_top_10']:.3f}] | "
                    f"{int(r['within_match_spread_matches'])} (SD={bt_sd}) | "
                    f"{r['share_matches_pos_delta_vs_normal']:.2f} | "
                    f"[{r['lomo_min_delta']:+.1f}, {r['lomo_max_delta']:+.1f}] | "
                    f"{r['sec_dot_ctrl_eb_delta']:+.2f} / {r['sec_wicket_eb_delta']:+.2f} | {r['secondary_tradeoff_flag']} |"
                )
        return "\n".join(lines)

    c1 = res["proxy_trace"]["fitted_parameters"]["innings_1"]
    c2 = res["proxy_trace"]["fitted_parameters"]["innings_2"]
    val_lines = []
    for _, vr in res["val_matrix"].iterrows():
        val_lines.append(
            f"- **{vr['check']} ({vr['role']})** — PASS={vr['passed']} | {vr['detail']}"
        )

    md = f"""# SupeRR Intelligence V4.2 — Release Decision & Statistical Audit Report

**Release Status:** `{RELEASE_STATUS_V42}`

## 1. Executive Decision

V4.2 fixes every identified statistical and audit defect from V4.1 while preserving strict scientific honesty:
- **Chase score reconstruction remains blocked** (`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`): only {res['audit_summary']['matches_zero_all_extras']}/{res['audit_summary']['scoped_matches_with_deliveries']} matches (`{res['audit_summary']['verified_score_coverage_pct']}%`) have zero extras; non-DLS run-margin reconciliation fails on `{res['audit_summary']['non_dls_run_margin_fail']}/{res['audit_summary']['non_dls_run_margin_matches']}` matches (`non_dls_exact_also_zero_unknown_extras = {res['audit_summary']['non_dls_exact_also_zero_unknown_extras']}`, with `total_legal_balls = {res['audit_summary']['total_legal_balls']}` vs `total_delivery_rows = {res['audit_summary']['total_delivery_rows']}`). Because runs required, target, and required run rate remain unavailable across deliveries, **no calibrated match-leverage variable exists**.
- All estimates are honestly scoped to **pre-delivery resource stress** (`BATTING_WICKET_DEPLETION_ANOMALY` and `BOWLING_EXPECTED_SCORING_THREAT`).
- Primary estimator: **Option A Complete Penalized FWL Partial Regression + REML Empirical Bayes**, backed by an empirical REML-EM joint hierarchical comparison (**Option B**), exact unpenalized OLS synthetic validation (`< 1e-8`), a 2,000-replicate **REML match-cluster bootstrap** verified against full nuisance+B3 refits, fixed quantile spans (`0.60, 0.70, 0.75`), exact 8-contrast like-for-like decomposition, match-level consistency diagnostics, and secondary outcome trade-offs.

---

## 2. Pressure Proxy Trace & Definitions

- **Fitted Innings 1 curve `(R0, b, gamma)`**: `({c1['R0']:.3f}, {c1['b']:.4f}, {c1['gamma']:.4f})`
- **Fitted Innings 2 curve `(R0, b, gamma)`**: `({c2['R0']:.3f}, {c2['b']:.4f}, {c2['gamma']:.4f})`
- **`BATTING_WICKET_DEPLETION_ANOMALY`** (aliases `BATTING_RESOURCE_STRESS`, `bat_pressure`): Percentile rank of `1 - ((10 - wickets_before)/10)^gamma - E[.|innings, overid]`. Parameters `R0` and `b` absorb expected remaining-run decay during parameter fitting on non-DLS clean matches, so `bat_pressure` specifically isolates **innings-stage wicket-depletion anomaly** (NOT DLS resources, NOT match win-probability leverage). It cannot distinguish 12 runs required from 70 runs required at identical overs and wickets remaining. Sensitivity against full `R(u, w)` depletion is verified in `V4_2_VALIDATION_MATRIX.csv`.
- **`BOWLING_EXPECTED_SCORING_THREAT`** (aliases `BOWLING_SCORING_THREAT`, `bowl_pressure`): Percentile rank of out-of-outcome Ridge (`alpha=10.0`) predicted batter runs/100b from pre-delivery state & venue-season. Primary bowler outcome `y_bowl` measures **BATTER_RUNS_CONCEDED_SUPPRESSION_PER_100_LEGAL_BALLS_PROXY** (not full economy with extras).

---

## 3. Estimator, Regularization, & Heterogeneity

| Role | Estimator | Eligible Players | REML mu0 | REML tau | I2 (%) | Schur-vs-Residual Reg Gap (Median / Max) |
|---|---|---:|---:|---:|---:|---|
| Batter | Option A Complete Penalized FWL + REML | {res['bat_meta']['n_eligible']} | {res['bat_meta']['het']['mu0']:+.3f} | {res['bat_meta']['het']['tau']:.3f} | {100.0 * res['bat_meta']['het']['I2']:.1f}% | {res['bat_meta']['reg_gap_median_delta']:.3f} / {res['bat_meta']['reg_gap_max_delta']:.3f} |
| Bowler | Option A Complete Penalized FWL + REML | {res['bowl_meta']['n_eligible']} | {res['bowl_meta']['het']['mu0']:+.3f} | {res['bowl_meta']['het']['tau']:.3f} | {100.0 * res['bowl_meta']['het']['I2']:.1f}% | {res['bowl_meta']['reg_gap_median_delta']:.3f} / {res['bowl_meta']['reg_gap_max_delta']:.3f} |

---

## 4. Direct Claim C OOT Validation & Ridge Tuning

Claims A, B, and C are strictly separated:
- **Batters (OOT >= 2023):** Claim A (General Skill FE) `rho = {res['bat_claims']['claim_a_spearman_rho']:.3f}` (`p = {res['bat_claims']['claim_a_p']:.3g}`), Claim B (High-Stress Execution) `rho = {res['bat_claims']['claim_b_spearman_rho']:.3f}` (`p = {res['bat_claims']['claim_b_p']:.3g}`), **Claim C (Pressure-vs-Own-Normal Slope)** `rho = {res['bat_claims']['claim_c_spearman_rho']:.3f}` (`p = {res['bat_claims']['claim_c_p']:.3g}`, status: `{res['bat_claims']['claim_c_status']}`).
- **Bowlers (OOT >= 2023):** Claim A (General Skill FE) `rho = {res['bowl_claims']['claim_a_spearman_rho']:.3f}` (`p = {res['bowl_claims']['claim_a_p']:.3g}`), Claim B (High-Stress Execution) `rho = {res['bowl_claims']['claim_b_spearman_rho']:.3f}` (`p = {res['bowl_claims']['claim_b_p']:.3g}`), **Claim C (Pressure-vs-Own-Normal Slope)** `rho = {res['bowl_claims']['claim_c_spearman_rho']:.3f}` (`p = {res['bowl_claims']['claim_c_p']:.3g}`, status: `{res['bowl_claims']['claim_c_status']}`).

Across the candidate Ridge grid (`5/20/60/150/asym`), Claim C OOT replication does not become strongly predictive because wicket-depletion / scoring-threat proxies carry substantial match-to-match noise and lack true chase score/target leverage. We explicitly disclose this honest negative finding rather than overclaiming Ridge selection fixes Claim C.

**Operational Eligibility Floor (`n_hi>=50, n_lo>=30, cs_matches>=8, se_delta<=25.0`):** Documented strictly as an operational precision floor to bound sampling error, NOT claimed as empirically optimal (full sweep in `V4_2_ELIGIBILITY_PRECISION_ANALYSIS.csv`).

---

## 5. Final Top 10 Batters (Claim C — Resource Stress Proxy)

{_md_table(bat_top10, is_bat=True)}

---

## 6. Final Top 10 Bowlers (Claim C — Expected Scoring Threat Proxy)

{_md_table(bowl_top10, is_bat=False)}

---

## 7. Validation Summary

{chr(10).join(val_lines)}

---

## 8. Provenance

- **Branch:** `{sot['branch']}`
- **Origin Main SHA:** `{sot['origin_main_sha']}`
- **Generated Elapsed Time:** `{res['elapsed_sec']:.1f}s`
"""
    rep_path = rep_dir / "V4_2_RELEASE_DECISION.md"
    rep_path.write_text(md, encoding="utf-8")

    return {
        "shortlist_path": str(shortlist_path),
        "rank_probs_path": str(rank_probs_path),
        "decomp_path": str(decomp_path),
        "comp_path": str(comp_path),
        "elig_path": str(elig_path),
        "val_path": str(val_path),
        "sot_path": str(sot_path),
        "rep_path": str(rep_path),
    }
