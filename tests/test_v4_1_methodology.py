"""Statistical integrity and methodology regression tests for SupeRR Intelligence V4.1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

V4_OUT = ROOT / "data" / "outputs" / "v4"
V4_REP = ROOT / "data" / "reports" / "v4"
V41_OUT = ROOT / "data" / "outputs" / "v4_1"
V41_REP = ROOT / "data" / "reports" / "v4_1"

MANDATORY_DECOMP_COLS = [
    "raw_high_performance",
    "raw_normal_performance",
    "raw_observed_delta",
    "context_adjusted_high_performance",
    "context_adjusted_normal_performance",
    "context_adjusted_delta",
    "empirical_bayes_delta",
    "lower_confidence_bound",
    "upper_confidence_bound",
    "probability_positive_effect",
]


def test_v41_artifacts_exist_and_v4_preserved() -> None:
    required_out = [
        "V4_1_SCORE_ENRICHMENT_AUDIT.csv",
        "V4_1_RAW_ADJUSTED_DECOMPOSITION.csv",
        "V4_1_ELIGIBILITY_PRECISION_ANALYSIS.csv",
        "V4_1_RANK_PROBABILITIES.csv",
        "V4_1_MODEL_COMPARISON.csv",
        "V4_1_FINAL_SHORTLIST.csv",
        "V4_1_VALIDATION_MATRIX.csv",
        "V4_1_SOURCE_OF_TRUTH.json",
    ]
    for fn in required_out:
        assert (V41_OUT / fn).exists(), f"Missing V4.1 output: {fn}"

    assert (V41_REP / "V4_1_STATISTICAL_CORRECTIONS.md").exists()
    assert (V41_REP / "V4_1_RELEASE_DECISION.md").exists()

    # V4 artifacts must remain untouched and distinct
    assert (V4_OUT / "TOP_10_BATTERS_V4.csv").exists()
    assert (V4_OUT / "TOP_10_BOWLERS_V4.csv").exists()
    assert (V4_OUT / "RANKING_SOURCE_OF_TRUTH_V4.json").exists()
    assert (V4_REP / "PRESSURE_METHODOLOGY_V4.md").exists()
    assert (V4_REP / "DATA_AUDIT_V4.md").exists()


def test_score_enrichment_reconciliation_invariants() -> None:
    audit = pd.read_csv(V41_OUT / "V4_1_SCORE_ENRICHMENT_AUDIT.csv")
    with open(V41_OUT / "V4_1_SOURCE_OF_TRUTH.json", "r", encoding="utf-8") as f:
        sot = json.load(f)

    assert len(audit) == 1652
    assert audit["match_id"].nunique() == 837
    sc = sot["score_audit_summary"]
    assert sc["scoped_matches_with_deliveries"] == 837
    assert sc["scoped_regular_innings"] == 1652
    assert sc["non_dls_run_margin_matches"] == 390
    assert sc["non_dls_run_margin_fail"] == 342
    assert sc["non_dls_run_margin_exact"] == 48
    assert sc["chase_score_reconstruction_blocked"] is True


def test_pressure_terminology_and_span_fix() -> None:
    with open(V41_OUT / "V4_1_SOURCE_OF_TRUTH.json", "r", encoding="utf-8") as f:
        sot = json.load(f)

    assert sot["pressure_aliases"]["bat_pressure"] == "BATTING_RESOURCE_STRESS"
    assert sot["pressure_aliases"]["bowl_pressure"] == "BOWLING_SCORING_THREAT"
    assert sot["diagnostics"]["batter_runs"]["span"] == 0.75
    assert sot["diagnostics"]["bowler_runs_saved_proxy"]["span"] == 0.75
    assert sot["release_status"] == "V4.1 PROVISIONAL — RESOURCE STRESS"

    corr_text = (V41_REP / "V4_1_STATISTICAL_CORRECTIONS.md").read_text(encoding="utf-8")
    assert "BATTING_RESOURCE_STRESS" in corr_text
    assert "BOWLING_SCORING_THREAT" in corr_text
    assert "12 runs required" in corr_text and "70 runs required" in corr_text


def test_mandatory_columns_and_exact_decomposition() -> None:
    dec = pd.read_csv(V41_OUT / "V4_1_RAW_ADJUSTED_DECOMPOSITION.csv")
    short = pd.read_csv(V41_OUT / "V4_1_FINAL_SHORTLIST.csv")

    for col in MANDATORY_DECOMP_COLS:
        assert col in dec.columns, f"Missing column in decomposition: {col}"
        assert col in short.columns, f"Missing column in shortlist: {col}"

    assert "raw_fwl_delta" not in dec.columns
    assert "raw_fwl_delta" not in short.columns

    reconstructed = (
        dec["raw_observed_delta"]
        + dec["delta_shift_phase_fmt_season"]
        + dec["delta_shift_pressure_wkt_state"]
        + dec["delta_shift_match_par"]
        + dec["delta_shift_opponent_quality"]
        + dec["delta_shift_continuous_fwl_vs_discrete"]
    )
    assert float((reconstructed - dec["context_adjusted_delta"]).abs().max()) < 1e-6

    # Check bowler proxy disclosures
    bowl_dec = dec[dec["role"] == "bowler"]
    assert bowl_dec["bowler_extras_status"].str.startswith("TOTAL_RUNS_UNAVAILABLE").all()
    assert (bowl_dec["bowler_legal_balls"] > 0).all()


def test_shortlist_ranking_order_and_bootstrap_bounds() -> None:
    short = pd.read_csv(V41_OUT / "V4_1_FINAL_SHORTLIST.csv")
    rp = pd.read_csv(V41_OUT / "V4_1_RANK_PROBABILITIES.csv")

    assert len(short) == 20
    for role in ["batter", "bowler"]:
        sub = short[short["role"] == role].reset_index(drop=True)
        assert len(sub) == 10
        assert sub["provisional_rank"].tolist() == list(range(1, 11))
        # Ordered strictly by empirical_bayes_delta
        eb_vals = sub["empirical_bayes_delta"].tolist()
        assert eb_vals == sorted(eb_vals, reverse=True)
        assert (sub["strict_reliable_flag"] == False).all()
        assert (sub["reliability_tier"] == "PROVISIONAL_CI_CROSSES_ZERO").all()

    assert (rp["boot_rank_ci_low"] <= rp["boot_rank_median"]).all()
    assert (rp["boot_rank_median"] <= rp["boot_rank_ci_high"]).all()
    assert ((rp["prob_top_10"] >= 0.0) & (rp["prob_top_10"] <= 1.0)).all()


def test_separated_validation_and_model_comparison() -> None:
    val = pd.read_csv(V41_OUT / "V4_1_VALIDATION_MATRIX.csv")
    comp = pd.read_csv(V41_OUT / "V4_1_MODEL_COMPARISON.csv")

    cats = set(val["claim_category"].unique())
    assert "CLAIM_A_GENERAL_SKILL_REPEATABILITY" in cats
    assert "CLAIM_B_HIGH_STRESS_EXECUTION_REPEATABILITY" in cats
    assert "CLAIM_C_RELATIVE_PRESSURE_DELTA_REPEATABILITY" in cats
    assert "ENGINEERING_DIAGNOSTIC_ONLY" in cats

    placebo = val[val["validation_family"] == "SHUFFLED_PRESSURE_PLACEBO_NULL"]
    assert len(placebo) == 2
    assert placebo["status"].str.startswith("DIAGNOSTIC_PASS_NULL").all()

    variants = set(comp["model_variant"].unique())
    assert "V4_1_Base_TwoStage_FWL_REML_60" in variants
    assert "TwoStage_FWL_DL_60_span075" in variants
    assert "Joint_Hierarchical_Slope_lam3500" in variants
    assert "Joint_Hierarchical_Slope_lam500" in variants
    assert "V4_Legacy_TwoStage_DL_35_span0625" in variants
