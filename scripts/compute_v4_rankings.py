"""Orchestrate complete SupeRR Intelligence V4 rebuild, outputs, and reports."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4.data_audit import run_data_audit
from src.v4.pressure_proxy import (
    apply_b3_resource_stress,
    build_pre_delivery_context,
    export_pressure_deliveries_parquet,
    fit_b3_resource_stress,
)
from src.v4.ranking_and_validation import run_full_ranking_pipeline
from src.v4.reporting import generate_v4_reports


def main() -> None:
    print("[V4] Step 1/5: Phase A Data Audit & Reconciliation...")
    audit_summary = run_data_audit(
        data_dir="data",
        output_dir="data/outputs/v4",
        report_dir="data/reports/v4",
    )
    print(f"     Regular={audit_summary['regular_rows']:,}, Super Over={audit_summary['super_over_rows']}, "
          f"CHASE_SCORE_RECONSTRUCTION_BLOCKED={audit_summary['chase_score_reconstruction_blocked']}")

    print("[V4] Step 2/5: Phase B Pre-Delivery Context & B3 Resource Stress Proxies...")
    reg_ctx, _ = build_pre_delivery_context(data_dir="data")
    b3_state = fit_b3_resource_stress(reg_ctx)
    reg_b3 = apply_b3_resource_stress(reg_ctx, b3_state)
    pq_path = export_pressure_deliveries_parquet(reg_b3, output_dir="data/outputs/v4")
    print(f"     Exported {pq_path} ({len(reg_b3):,} rows)")

    print("[V4] Step 3/5: Phase C-F Hierarchical Model, Bootstrap, Sensitivity & Validation...")
    pipeline_out = run_full_ranking_pipeline(
        reg_ctx=reg_ctx,
        reg_b3=reg_b3,
        b3_state=b3_state,
        output_dir="data/outputs/v4",
        bootstrap_iter=2000,
        bootstrap_seed=42,
    )

    print("[V4] Step 4/5: Phase G Generating V4 Markdown Reports...")
    generate_v4_reports(audit_summary=audit_summary, pipeline_out=pipeline_out, report_dir="data/reports/v4")

    sot = pipeline_out["sot"]
    print(f"[V4] Step 5/5: Complete! Status = {sot['release_status']}")
    print("Top 10 Batters:", [r["player_name"] for r in sot["top_10_batters"]])
    print("Top 10 Bowlers:", [r["player_name"] for r in sot["top_10_bowlers"]])


if __name__ == "__main__":
    main()
