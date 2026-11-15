"""End-to-end SupeRR Intelligence V4.1 execution script (preserves V3 & V4 artifacts intact)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4.pressure_proxy import apply_b3_resource_stress, build_pre_delivery_context, fit_b3_resource_stress
from src.v4_1.eligibility_and_validation import run_full_v41_pipeline
from src.v4_1.reporting_v41 import generate_v41_reports
from src.v4_1.score_enrichment import run_score_enrichment_audit


def main() -> None:
    print("[V4.1] Step 1/4: Score Enrichment Coverage & Margin Reconciliation Audit...")
    _, score_audit = run_score_enrichment_audit("data", output_dir="data/outputs/v4_1")
    print(
        f"       Matches={score_audit['scoped_matches_with_deliveries']}, "
        f"ZeroAllExtras={score_audit['matches_zero_all_extras']}, "
        f"NonDLSFail={score_audit['non_dls_run_margin_fail']}/{score_audit['non_dls_run_margin_matches']}, "
        f"AccidentalCancel={score_audit['non_dls_exact_accidental_cancellation']}"
    )

    print("[V4.1] Step 2/4: Leak-Free Pre-Delivery Context & B3 Resource Stress / Threat Aliases...")
    reg_ctx, _ = build_pre_delivery_context("data")
    b3_state = fit_b3_resource_stress(reg_ctx)
    reg_b3 = apply_b3_resource_stress(reg_ctx, b3_state)

    print("[V4.1] Step 3/4: Two-Stage REML, Joint Hierarchical, Global B=1000 Bootstrap & Validation...")
    out = run_full_v41_pipeline(
        reg_ctx, reg_b3, score_audit,
        output_dir="data/outputs/v4_1", bootstrap_iter=1000, bootstrap_seed=42,
    )

    print("[V4.1] Step 4/4: Generating V4.1 Reports...")
    generate_v41_reports(out, b3_state, report_dir="data/reports/v4_1")

    sot = out["sot"]
    print(f"[V4.1] Complete! Status = {sot['release_status']}")
    print("Shortlist Batters (PROVISIONAL):", [r["player_name"] for r in sot["shortlist_batters"]])
    print("Shortlist Bowlers (PROVISIONAL):", [r["player_name"] for r in sot["shortlist_bowlers"]])


if __name__ == "__main__":
    main()
