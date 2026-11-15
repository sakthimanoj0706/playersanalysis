"""Verify all SupeRR Intelligence V4.1 artifacts, statistical invariants, V4/V3 preservation & determinism."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4.pressure_proxy import apply_b3_resource_stress, build_pre_delivery_context, fit_b3_resource_stress
from src.v4_1.eligibility_and_validation import run_full_v41_pipeline
from src.v4_1.score_enrichment import run_score_enrichment_audit

REQUIRED_OUTPUTS = [
    "V4_1_RAW_ADJUSTED_DECOMPOSITION.csv",
    "V4_1_ELIGIBILITY_PRECISION_ANALYSIS.csv",
    "V4_1_RANK_PROBABILITIES.csv",
    "V4_1_MODEL_COMPARISON.csv",
    "V4_1_FINAL_SHORTLIST.csv",
    "V4_1_SCORE_ENRICHMENT_AUDIT.csv",
    "V4_1_VALIDATION_MATRIX.csv",
    "V4_1_SOURCE_OF_TRUTH.json",
]

REQUIRED_REPORTS = [
    "V4_1_STATISTICAL_CORRECTIONS.md",
    "V4_1_RELEASE_DECISION.md",
]

MANDATORY_10_COLS = [
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


def verify_artifacts(output_dir: str = "data/outputs/v4_1", report_dir: str = "data/reports/v4_1") -> None:
    for fn in REQUIRED_OUTPUTS:
        p = os.path.join(output_dir, fn)
        assert os.path.exists(p), f"Missing V4.1 output: {p}"
    for fn in REQUIRED_REPORTS:
        p = os.path.join(report_dir, fn)
        assert os.path.exists(p), f"Missing V4.1 report: {p}"
        assert os.path.getsize(p) > 400, f"Report unexpectedly small: {p}"

    short = pd.read_csv(os.path.join(output_dir, "V4_1_FINAL_SHORTLIST.csv"))
    decomp = pd.read_csv(os.path.join(output_dir, "V4_1_RAW_ADJUSTED_DECOMPOSITION.csv"))
    for c in MANDATORY_10_COLS:
        assert c in short.columns, f"Missing mandatory column {c} in V4_1_FINAL_SHORTLIST.csv"
        assert c in decomp.columns, f"Missing mandatory column {c} in V4_1_RAW_ADJUSTED_DECOMPOSITION.csv"

    assert len(short[short["role"] == "batter"]) == 10
    assert len(short[short["role"] == "bowler"]) == 10
    assert "raw_fwl_delta" not in short.columns

    # Exact additive bridge check
    bridge = (
        decomp["raw_observed_delta"]
        + decomp["delta_shift_phase_fmt_season"]
        + decomp["delta_shift_pressure_wkt_state"]
        + decomp["delta_shift_match_par"]
        + decomp["delta_shift_opponent_quality"]
        + decomp["delta_shift_continuous_fwl_vs_discrete"]
    )
    max_err = float(np.nanmax(np.abs(bridge.values - decomp["context_adjusted_delta"].values)))
    assert max_err < 1e-6, f"Decomposition identity error={max_err}"

    # Verify V4 and V3 preserved untouched
    assert os.path.exists("data/outputs/v4/TOP_10_BATTERS_V4.csv")
    assert os.path.exists("data/outputs/v4/TOP_10_BOWLERS_V4.csv")
    assert os.path.exists("data/outputs/v3/TOP_10_BATTERS.csv")
    assert os.path.exists("data/outputs/v3/TOP_10_BOWLERS.csv")

    with open(os.path.join(output_dir, "V4_1_SOURCE_OF_TRUTH.json"), "r", encoding="utf-8") as f:
        sot = json.load(f)
    assert sot["release_status"] == "V4.1 PROVISIONAL — RESOURCE STRESS"
    assert sot["chase_score_reconstruction_blocked"] is True
    print("[Verify V4.1] Artifact, decomposition & V3/V4 preservation checks PASSED.")


def verify_determinism() -> None:
    _, score_audit = run_score_enrichment_audit("data", output_dir=tempfile.mkdtemp(prefix="v41_sc_"))
    reg_ctx, _ = build_pre_delivery_context("data")
    b3_state = fit_b3_resource_stress(reg_ctx)
    reg_b3 = apply_b3_resource_stress(reg_ctx, b3_state)

    t1 = tempfile.mkdtemp(prefix="v41_det1_")
    t2 = tempfile.mkdtemp(prefix="v41_det2_")
    try:
        run_full_v41_pipeline(reg_ctx, reg_b3, score_audit, output_dir=t1, bootstrap_iter=1000, bootstrap_seed=42)
        run_full_v41_pipeline(reg_ctx, reg_b3, score_audit, output_dir=t2, bootstrap_iter=1000, bootstrap_seed=42)
        for fn in ["V4_1_FINAL_SHORTLIST.csv", "V4_1_RANK_PROBABILITIES.csv", "V4_1_SOURCE_OF_TRUTH.json"]:
            with open(os.path.join(t1, fn), "rb") as f1, open(os.path.join(t2, fn), "rb") as f2:
                assert f1.read() == f2.read(), f"Non-deterministic V4.1 output in {fn}"
        print("[Verify V4.1] Double-run determinism check PASSED.")
    finally:
        shutil.rmtree(t1, ignore_errors=True)
        shutil.rmtree(t2, ignore_errors=True)


if __name__ == "__main__":
    verify_artifacts()
    verify_determinism()
    print("[Verify V4.1] ALL VERIFICATION GATES PASSED.")
