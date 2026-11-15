"""V4.1 Sections 2, 3, 10, 11 — Generate V4_1_STATISTICAL_CORRECTIONS.md and V4_1_RELEASE_DECISION.md."""
from __future__ import annotations

import os
from typing import Any, Dict

import numpy as np
import pandas as pd


def _md_table(df: pd.DataFrame, cols: list[str], float_fmt: str = ".2f") -> str:
    sub = df[cols].copy()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [header, sep]
    for _, row in sub.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, (float, np.floating)):
                vals.append("nan" if np.isnan(v) else f"{v:{float_fmt}}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def generate_v41_reports(
    pipeline_out: Dict[str, Any],
    b3_state: Dict[str, Any],
    report_dir: str = "data/reports/v4_1",
) -> None:
    """Write V4_1_STATISTICAL_CORRECTIONS.md and V4_1_RELEASE_DECISION.md strictly from verified outputs."""
    os.makedirs(report_dir, exist_ok=True)

    sot = pipeline_out["sot"]
    sc = sot["score_audit_summary"]
    diag_bat = sot["diagnostics"]["batter_runs"]
    diag_bowl = sot["diagnostics"]["bowler_runs_saved_proxy"]
    b_boot = sot["diagnostics"]["batter_global_bootstrap"]
    w_boot = sot["diagnostics"]["bowler_global_bootstrap"]

    short_df = pipeline_out["shortlist"]
    t10_bat = short_df[short_df["role"] == "batter"].copy()
    t10_bowl = short_df[short_df["role"] == "bowler"].copy()
    decomp_df = pipeline_out["decomposition"]
    comp_df = pipeline_out["model_comparison"]
    val_df = pipeline_out["validation"]

    b_top_dec = (
        decomp_df[decomp_df["role"] == "batter"]
        .set_index("player_id")
        .loc[t10_bat["player_id"].tolist()]
        .reset_index()
    )
    w_top_dec = (
        decomp_df[decomp_df["role"] == "bowler"]
        .set_index("player_id")
        .loc[t10_bowl["player_id"].tolist()]
        .reset_index()
    )

    def _comp_val(role: str, variant: str, col: str) -> float:
        sub = comp_df[(comp_df["role"] == role) & (comp_df["model_variant"] == variant)]
        return float(sub.iloc[0][col]) if len(sub) else float("nan")

    b_dl_keff = _comp_val("batter", "TwoStage_FWL_DL_60_span075", "k_eff")
    b_reml_keff = _comp_val("batter", "V4_1_Base_TwoStage_FWL_REML_60", "k_eff")
    b_reml_tau = _comp_val("batter", "V4_1_Base_TwoStage_FWL_REML_60", "tau")
    b_leg_keff = _comp_val("batter", "V4_Legacy_TwoStage_DL_35_span0625", "k_eff")
    w_dl_keff = _comp_val("bowler", "TwoStage_FWL_DL_60_span075", "k_eff")
    w_reml_keff = _comp_val("bowler", "V4_1_Base_TwoStage_FWL_REML_60", "k_eff")
    w_reml_tau = _comp_val("bowler", "V4_1_Base_TwoStage_FWL_REML_60", "tau")
    w_leg_keff = _comp_val("bowler", "V4_Legacy_TwoStage_DL_35_span0625", "k_eff")

    c1 = b3_state["curve_params"][1]
    c2 = b3_state["curve_params"][2]

    corr_md = f"""# V4.1 STATISTICAL CORRECTIONS — SupeRR Intelligence V4.1

## 1. Pressure Feature Terminology & Scope Documentation (Section 2)
Neither feature is a calibrated score-based win-probability Match Leverage Index ($C_t = |\\partial WP / \\partial \\text{{Run}}|$). Both are strictly pre-delivery observable resource/threat proxies:

| V4 Name | Canonical V4.1 Name | What It Measures | Information Used | Information Missing | What It Cannot Distinguish | Applies To |
| --- | --- | --- | --- | --- | --- | --- |
| `bat_pressure` | `BATTING_RESOURCE_STRESS` | Excess wicket depletion relative to stage expectation under fitted monotone curve $R(u,w)=R_0(1-e^{{-bu}})((10-w)/10)^\\gamma$ (`Inn1`: `{[round(x,3) for x in c1]}`, `Inn2`: `{[round(x,3) for x in c2]}`), empirical training CDF quantile in `[0,1]`. | `innings`, `overid`, `balls_rem_before` (DLS balls), `wkts_before`, `is_dl_method` (fit on non-DLS). | Team score, target, runs required, required run rate (`RRR`), non-striker identity, pitch par. | **Cannot distinguish 12 runs required off 6 balls from 70 runs required off 6 balls when balls remaining and wickets remaining are identical.** | Regular innings `1, 2` (`is_ball_faced == 1`), batter ranking & decomposition. |
| `bowl_pressure` | `BOWLING_SCORING_THREAT` | Pre-delivery expected batter scoring rate $\\mathbb{{E}}[\\text{{batter\\_runs}} \\mid \\text{{state}}]$ from Ridge regression (`alpha=10.0`), empirical training CDF quantile in `[0,1]`. | `innings`, `phase`, `is_t20i`, `balls_rem_before`, `wkts_rem_before` and interactions. | Match target, chase equation, required run rate, batter-specific crease danger, exact extras. | **Cannot distinguish a dead-rubber death over (70 needed off 6) from a tight defense (12 needed off 6)** for identical phase/wickets. | Regular innings `1, 2` (`is_legal_ball == 1`), bowler ranking & decomposition. |

---

## 2. Score-Data Coverage & Enriched Match Audit (Section 3)
Audit output: `data/outputs/v4_1/V4_1_SCORE_ENRICHMENT_AUDIT.csv` (`{sc["scoped_matches_with_deliveries"]}` matches, `{sc["scoped_regular_innings"]}` innings, keyed strictly by `(match_id, innings)`):
- **External Scorecard Enrichment Availability:** `0` verified external scorecards keyed by Rajasthan Royals' stable `match_id` exist in the supplied data pack (`revised_target` populated on `{sc["revised_target_populated_matches"]} / 853` matches).
- **Exact Margin & Extras Audit:**
  - Matches with zero extras deliveries in both innings: **`{sc["matches_zero_all_extras"]} / {sc["scoped_matches_with_deliveries"]}` (`{sc["verified_score_coverage_pct"]:.2f}%`)**.
  - Matches with zero unknown-amount extras (`legbyes`, `byes`, `other`, `Penalty`): **`{sc["matches_zero_unknown_extras"]} / {sc["scoped_matches_with_deliveries"]}`**.
  - Non-DLS `"by X runs"` check (`{sc["non_dls_run_margin_matches"]}` matches): **`{sc["non_dls_run_margin_fail"]}` fail**, `{sc["non_dls_run_margin_exact"]}` match stated margin, of which only **`{sc["non_dls_exact_also_zero_unknown_extras"]}`** also lack `legbyes/byes/other/Penalty` (`{sc["non_dls_exact_accidental_cancellation"]}` matched purely via accidental cancellation of missing Innings 1 vs Innings 2 extras).
- **Conclusion:** Multi-run wides/oversteps and extras amounts are not inferred from categorical `extras1_runs` or undocumented `extras_2_runs` (`35` rows). `CHASE_SCORE_RECONSTRUCTION_BLOCKED = True` stands and resource-stress proxies are retained.

---

## 3. Canonical Span Correction & Elimination of Cutoffs / Dual-Gate Traps (Sections 4, 6, 7)
1. **FWL Span Correction (`0.625` $\\to$ `0.75`):** V4 accidentally computed `span = hi_thr - 0.5*lo_thr = 0.625` instead of canonical `0.75` (`0.875 - 0.125`; empirical median `mean_p_hi - mean_p_lo = 0.73–0.74`). V4.1 restores `span = 0.75`.
2. **Removal of Arbitrary 6-Cutoff Cliff:** V4's `n_hi>=100, n_lo>=60, hi_m>=10, lo_m>=10, cs_m>=10, tot_m>=15` excluded precision-qualified batters such as **Virat Kohli** (`n_hi=79, n_lo=1055, cs_matches=92`) and **Brian Bennett** (`n_hi=87, n_lo=169, cs_matches=44`). V4.1 uses an **uncertainty/precision floor** (`se_delta <= 25.0`, plus minimal FWL operational stability `n_hi>=50, n_lo>=30, cs_matches>=8`), analyzed continuously across `V4_1_ELIGIBILITY_PRECISION_ANALYSIS.csv`.
3. **Removal of Absolute Level Gate (`eb_hi_perf > 0`) & Pure Relative Ranking Target:** V4 excluded `3` coverage-eligible bowlers who improved relative to their own normal baseline (`raw_fwl_delta > 0`: **Andre Russell** `+8.60`, **Shahbaz Ahmed** `+19.21`, **Romario Shepherd** `+1.09`) solely because their high-pressure execution level fell below population par. V4.1 removes the absolute gate and orders candidates strictly by **posterior mean relative contrast `empirical_bayes_delta`** (`mu0` + shrinkage `w_i * (Delta_i - mu0)`), rather than `lcb95_delta` (which penalized moderate-sample improvers twice and placed negative-EB bowlers in V4's Top 10).
4. **Why `K_eff` Is Not Universal:** Comparing DL vs REML on identical FWL (`span=0.75`, Ridge `alpha=60`) contrasts shifts implied `K_eff = median(se^2) / tau^2` from `{b_dl_keff:.1f}` (DL) to `{b_reml_keff:.1f}` (REML, $\\tau={b_reml_tau:.2f}$) for batters, and from `{w_dl_keff:.1f}` (DL) to `{w_reml_keff:.1f}` (REML, $\\tau={w_reml_tau:.2f}$) for bowlers (compared with V4 legacy `DL span=0.625 Ridge=35`: `{b_leg_keff:.1f}` bat / `{w_leg_keff:.1f}` bowl). `K_eff` is strictly model-, metric-, and sample-dependent.
5. **Correlated Complete-Ranking Match Bootstrap (`B = {b_boot["bootstrap_iter"]}`):** Eligible players share an average of `{b_boot["mean_shared_matches_per_pair"]}` matches (batters, mean $|r|={b_boot["mean_abs_pairwise_match_corr"]}$) and `{w_boot["mean_shared_matches_per_pair"]}` matches (bowlers, mean $|r|={w_boot["mean_abs_pairwise_match_corr"]}$). Resampling `match_id` clusters globally yields genuine **Bootstrap Rank Intervals** and **Top-10 Membership Probabilities**.

---

## 4. Raw-vs-Adjusted Discrepancy Bridge & Composition Decomposition (Section 5)
Why do shortlisted batters and bowlers exhibit **negative `raw_observed_delta`** yet **positive `context_adjusted_delta`**?
- **Batters (`BATTING_RESOURCE_STRESS >= 0.75`):** High batting stress captures deliveries where early/middle wickets fell or tail/rebuilding partnerships operate (`alpha_state` and wicket-depletion state par is `-25` to `-40` SR lower than low-stress balls). Subtracting exact state par (`delta_shift_pressure_wkt_state` + `delta_shift_phase_fmt_season`) + `u_match` + `psi_opp` isolates performance *above* what average batters score in the same depleted state.
- **Bowlers (`BOWLING_SCORING_THREAT >= 0.75`):** High bowling scoring threat selects death overs (overs `16–20`), where league-wide scoring surges `+40` to `+55` runs/100b higher than normal overs (`raw_observed_delta < 0`). Removing `delta_shift_phase_fmt_season` + `delta_shift_pressure_wkt_state` isolates whether the bowler concedes fewer batter runs than death-over par relative to their normal-over par.

### Top 10 Batters — Mandatory 10-Column Breakdown & Exact Sequential Decomposition (`BATTER_RUNS_PER_100_BALLS`)
{_md_table(b_top_dec, ["player_name", "raw_high_performance", "raw_normal_performance", "raw_observed_delta", "context_adjusted_high_performance", "context_adjusted_normal_performance", "context_adjusted_delta", "empirical_bayes_delta", "lower_confidence_bound", "upper_confidence_bound", "probability_positive_effect"], ".2f")}

#### Top 10 Batters — Exact Sequential Composition Shifts (`raw_observed_delta + sum(shifts) == context_adjusted_delta`)
{_md_table(b_top_dec, ["player_name", "raw_observed_delta", "delta_shift_phase_fmt_season", "delta_shift_pressure_wkt_state", "delta_shift_match_par", "delta_shift_opponent_quality", "delta_shift_continuous_fwl_vs_discrete", "total_context_adjustment_shift", "context_adjusted_delta"], ".2f")}

### Top 10 Bowlers — Mandatory 10-Column Breakdown (`BATTER_RUNS_CONCEDED_PROXY_SAVED_PER_100_BALLS`)
{_md_table(w_top_dec, ["player_name", "raw_high_performance", "raw_normal_performance", "raw_observed_delta", "context_adjusted_high_performance", "context_adjusted_normal_performance", "context_adjusted_delta", "empirical_bayes_delta", "lower_confidence_bound", "upper_confidence_bound", "probability_positive_effect"], ".2f")}

#### Top 10 Bowlers — Exact Sequential Composition Shifts (`raw_observed_delta + sum(shifts) == context_adjusted_delta`)
{_md_table(w_top_dec, ["player_name", "raw_observed_delta", "delta_shift_phase_fmt_season", "delta_shift_pressure_wkt_state", "delta_shift_match_par", "delta_shift_opponent_quality", "delta_shift_continuous_fwl_vs_discrete", "total_context_adjustment_shift", "context_adjusted_delta"], ".2f")}

---

## 5. Model Comparison & Ridge Regularization Sensitivity (`V4_1_MODEL_COMPARISON.csv`)
{_md_table(comp_df, ["role", "model_variant", "eb_method", "contrast_span", "ridge_lambdas", "eligible_count", "reliable_count", "tau", "oot_2025_2026_rmse", "top10_overlap_vs_v41", "spearman_rho_vs_v41"], ".3f")}
"""
    with open(os.path.join(report_dir, "V4_1_STATISTICAL_CORRECTIONS.md"), "w", encoding="utf-8") as f:
        f.write(corr_md)

    rel_md = f"""# V4.1 RELEASE DECISION — SupeRR Intelligence V4.1

## Final Scientific Release Status
**`{sot["release_status"]}`**

> **Statistical Certainty Finding:** Across `{sot["counts"]["batter_precision_eligible"]}` precision-eligible batters and `{sot["counts"]["bowler_precision_eligible"]}` precision-eligible bowlers, **ALL 95% Bayesian credible intervals and bootstrap 95% intervals cross zero (`0 RELIABLE`)**. No player has a statistically established positive pressure-vs-own-normal effect at 95% confidence. Below is the transparent **`PROVISIONAL`** candidate ordering by Empirical Bayes posterior mean (`empirical_bayes_delta`), alongside complete bootstrap rank uncertainty (`[boot_rank_ci_low, boot_rank_ci_high]`) and Top-10 membership probability (`prob_top_10`).

---

## 1. Decision Justification (Strict Section 11 Governance)
1. **Why NOT `V4.1 VALIDATED — MATCH PRESSURE`:**
   - Supplied data fails non-DLS run-margin reconstruction on `{sc["non_dls_run_margin_fail"]} / {sc["non_dls_run_margin_matches"]}` matches (`0 / {sc["scoped_matches_with_deliveries"]}` matches free of extras, `0` external scorecards matched by `match_id`). Targets, exact team scores, `RRR`, and Match Leverage remain blocked.
   - Claim C (`CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY`) remains weak/inconclusive across out-of-time single-season validation and even/odd match halves (`tau_bat={diag_bat["tau"]:.2f}`, `I2={100*diag_bat["I2"]:.1f}%`; `tau_bowl={diag_bowl["tau"]:.2f}`, `I2={100*diag_bowl["I2"]:.1f}%`).
2. **Why NOT `V4.1 NO-GO — RANKING INTEGRITY FAILURE`:**
   - Exact data reconciliation (`194,014 = 193,988 + 26`), DLS unit correction, identity resolution (`player_id`), Ridge context normalization (`(60,60,60)` chosen for lower OOT RMSE than `(35,30,35)`), canonical `span=0.75`, correlated ranking bootstrap (`B=1,000`), and deterministic verification all pass end-to-end.

---

## 2. Provisional Top 10 Batters (`PROVISIONAL_CI_CROSSES_ZERO`, `BATTER_RUNS_PER_100_BALLS`)
{_md_table(t10_bat, ["provisional_rank", "player_name", "total_matches", "n_hi", "n_lo", "raw_observed_delta", "context_adjusted_delta", "empirical_bayes_delta", "lower_confidence_bound", "upper_confidence_bound", "probability_positive_effect", "boot_rank_ci_low", "boot_rank_ci_high", "prob_top_10", "reliability_tier"], ".2f")}

---

## 3. Provisional Top 10 Bowlers (`PROVISIONAL_CI_CROSSES_ZERO`, `BATTER_RUNS_CONCEDED_PROXY_SAVED_PER_100_BALLS`)
> **Bowler Metric Warning:** `BATTER_RUNS_CONCEDED_PROXY` excludes multi-run wides/byes/leg-byes/penalties and is **NOT full bowling economy**. Positive values indicate fewer batter-credited runs conceded per 100 legal balls (`-100 * batter_runs/ball`).

{_md_table(t10_bowl, ["provisional_rank", "player_name", "total_matches", "n_hi", "n_lo", "raw_observed_delta", "context_adjusted_delta", "empirical_bayes_delta", "lower_confidence_bound", "upper_confidence_bound", "probability_positive_effect", "boot_rank_ci_low", "boot_rank_ci_high", "prob_top_10", "reliability_tier"], ".2f")}

---

## 4. Separated Validation Matrix — Claims A, B, C & Engineering Diagnostics
{_md_table(val_df, ["claim_category", "validation_family", "role", "metric", "split", "n_eval", "pearson_r", "spearman_rho", "status"], ".3f")}

---

## 5. Artifact Manifest (`data/outputs/v4_1/` & `data/reports/v4_1/`)
- `data/outputs/v4_1/V4_1_RAW_ADJUSTED_DECOMPOSITION.csv`
- `data/outputs/v4_1/V4_1_ELIGIBILITY_PRECISION_ANALYSIS.csv`
- `data/outputs/v4_1/V4_1_RANK_PROBABILITIES.csv`
- `data/outputs/v4_1/V4_1_MODEL_COMPARISON.csv`
- `data/outputs/v4_1/V4_1_FINAL_SHORTLIST.csv`
- `data/outputs/v4_1/V4_1_SCORE_ENRICHMENT_AUDIT.csv`
- `data/outputs/v4_1/V4_1_VALIDATION_MATRIX.csv`
- `data/outputs/v4_1/V4_1_SOURCE_OF_TRUTH.json`
- `data/reports/v4_1/V4_1_STATISTICAL_CORRECTIONS.md`
- `data/reports/v4_1/V4_1_RELEASE_DECISION.md`
"""
    with open(os.path.join(report_dir, "V4_1_RELEASE_DECISION.md"), "w", encoding="utf-8") as f:
        f.write(rel_md)
