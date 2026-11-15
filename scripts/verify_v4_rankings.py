"""Verify all SupeRR Intelligence V4 artifacts, invariants, and double-run determinism."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4.pressure_proxy import apply_b3_resource_stress, build_pre_delivery_context, fit_b3_resource_stress
from src.v4.ranking_and_validation import run_full_ranking_pipeline

REQUIRED_OUTPUTS = [
    "TOP_10_BATTERS_V4.csv",
    "TOP_10_BOWLERS_V4.csv",
    "ALL_BATTER_METRICS_V4.csv",
    "ALL_BOWLER_METRICS_V4.csv",
    "PLAYER_ELIGIBILITY_V4.csv",
    "PLAYER_PRESSURE_EVIDENCE_V4.csv",
    "PRESSURE_INDEX_DELIVERIES_V4.parquet",
    "RANKING_SENSITIVITY_V4.csv",
    "DATA_RECONCILIATION.csv",
    "MODEL_VALIDATION_V4.csv",
    "RANKING_SOURCE_OF_TRUTH_V4.json",
]

REQUIRED_REPORTS = [
    "DATA_AUDIT_V4.md",
    "PRESSURE_METHODOLOGY_V4.md",
    "PLAYER_RELATIVE_PERFORMANCE_V4.md",
    "VALIDATION_REPORT_V4.md",
    "FINAL_TOP_10_JUSTIFICATION_V4.md",
    "V4_RELEASE_READINESS.md",
]


def verify_artifacts(output_dir: str = "data/outputs/v4", report_dir: str = "data/reports/v4") -> None:
    for fname in REQUIRED_OUTPUTS:
        p = os.path.join(output_dir, fname)
        assert os.path.exists(p), f"Missing V4 output: {p}"
    for fname in REQUIRED_REPORTS:
        p = os.path.join(report_dir, fname)
        assert os.path.exists(p), f"Missing V4 report: {p}"
        assert os.path.getsize(p) > 200, f"Report unexpectedly small: {p}"

    t10_bat = pd.read_csv(os.path.join(output_dir, "TOP_10_BATTERS_V4.csv"))
    t10_bowl = pd.read_csv(os.path.join(output_dir, "TOP_10_BOWLERS_V4.csv"))
    assert len(t10_bat) == 10, f"Expected 10 batters, got {len(t10_bat)}"
    assert len(t10_bowl) == 10, f"Expected 10 bowlers, got {len(t10_bowl)}"
    assert t10_bat["player_id"].is_unique
    assert t10_bowl["player_id"].is_unique
    assert all(t10_bat["n_hi"] >= 100) and all(t10_bat["n_lo"] >= 60)
    assert all(t10_bowl["n_hi"] >= 100) and all(t10_bowl["n_lo"] >= 60)
    assert all(t10_bat["eb_hi_perf"] > 0) and all(t10_bowl["eb_hi_perf"] > 0)

    with open(os.path.join(output_dir, "RANKING_SOURCE_OF_TRUTH_V4.json"), "r", encoding="utf-8") as f:
        sot = json.load(f)
    assert sot["chase_score_reconstruction_blocked"] is True
    assert sot["pressure_source_type"] == "RESOURCE_STRESS_PROXY"
    assert [r["player_id"] for r in sot["top_10_batters"]] == t10_bat["player_id"].tolist()
    assert [r["player_id"] for r in sot["top_10_bowlers"]] == t10_bowl["player_id"].tolist()

    # Check V3 archive untouched
    assert os.path.exists("data/outputs/v3/TOP_10_BATTERS.csv")
    assert os.path.exists("data/outputs/v3/TOP_10_BOWLERS.csv")

    print("[Verify] Artifact & source-of-truth parity checks PASSED.")


def verify_determinism() -> None:
    reg_ctx, _ = build_pre_delivery_context("data")
    b3_state = fit_b3_resource_stress(reg_ctx)
    reg_b3 = apply_b3_resource_stress(reg_ctx, b3_state)

    tmp1 = tempfile.mkdtemp(prefix="v4_det1_")
    tmp2 = tempfile.mkdtemp(prefix="v4_det2_")
    try:
        run_full_ranking_pipeline(reg_ctx, reg_b3, b3_state, output_dir=tmp1, bootstrap_iter=2000, bootstrap_seed=42)
        run_full_ranking_pipeline(reg_ctx, reg_b3, b3_state, output_dir=tmp2, bootstrap_iter=2000, bootstrap_seed=42)
        for fn in ["TOP_10_BATTERS_V4.csv", "TOP_10_BOWLERS_V4.csv", "RANKING_SOURCE_OF_TRUTH_V4.json"]:
            with open(os.path.join(tmp1, fn), "rb") as f1, open(os.path.join(tmp2, fn), "rb") as f2:
                assert f1.read() == f2.read(), f"Non-deterministic output detected in {fn}"
        print("[Verify] Double-run determinism check PASSED.")
    finally:
        shutil.rmtree(tmp1, ignore_errors=True)
        shutil.rmtree(tmp2, ignore_errors=True)


if __name__ == "__main__":
    verify_artifacts()
    verify_determinism()
    print("[Verify] ALL V4 VERIFICATION GATES PASSED.")
