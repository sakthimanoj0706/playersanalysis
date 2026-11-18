"""Run SupeRR Intelligence V4.4 (Track A: Cricsheet Score-Aware Pipeline & Track B: Observable Bridge)."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4_4.config import DEFAULT_V44_CONFIG
from src.v4_4.ingest_cricsheet_extras import run_track_a_cricsheet_ingestion
from src.v4_4.leverage_index import compute_track_a_leverage_index
from src.v4_4.observable_resource_pressure import run_track_b_observable_resource_pressure
from src.v4_4.pressure_joint_rapm import run_track_a_pressure_joint_rapm
from src.v4_4.score_aware_wp import prepare_verified_score_state, run_track_a_score_aware_wp
from src.v4_4.total_run_value import compute_track_a_total_run_value


def main() -> None:
    cfg = DEFAULT_V44_CONFIG
    cfg.ensure_dirs()
    (cfg.artifacts_dir / "v4_4_reproducibility_config.json").write_text(
        json.dumps(
            {
                "random_seed": cfg.random_seed,
                "n_cv_folds": cfg.n_cv_folds,
                "oot_cutoff_year": cfg.oot_cutoff_year,
                "standard_t20_balls": cfg.standard_t20_balls,
                "li_thresholds": list(cfg.li_thresholds),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=== TRACK A.1: CRICSHEET INGESTION & EXTRAS RECONCILIATION ===")
    ing = run_track_a_cricsheet_ingestion(cfg, force_download=False)
    print("Match joins:", ing["provenance"]["match_join_counts"])
    print("Innings reconciliation:", ing["provenance"]["innings_reconciliation_counts"])

    print("\n=== TRACK A.2: SCORE-AWARE TWO-INNINGS WIN PROBABILITY ===")
    ver_df = prepare_verified_score_state(ing["reg_enriched"], cfg)
    wp_res = run_track_a_score_aware_wp(ver_df, cfg)
    print("First Innings WP:\n", wp_res["inn1_df"].to_string(index=False))
    print("\nSecond Innings WP:\n", wp_res["inn2_df"].to_string(index=False))

    print("\n=== TRACK A.3: TRUE EXPECTED LEVERAGE INDEX ===")
    li_res = compute_track_a_leverage_index(wp_res, cfg)
    print("LI Distribution:\n", li_res["dist_df"].to_string(index=False))
    print("\nLI Threshold Comparison:\n", li_res["thresh_df"].to_string(index=False))

    print("\n=== TRACK A.4: TOTAL-RUN CONTEXT-ADJUSTED VALUE (DeltaRE_total) ===")
    df_trv, trv_audit = compute_track_a_total_run_value(li_res, cfg)
    print("Total-Run Value Audit:\n", trv_audit.to_string(index=False))

    print("\n=== TRACK A.5: PRESSURE-INTERACTION JOINT RIDGE RAPM ===")
    rapm_res = run_track_a_pressure_joint_rapm(df_trv, cfg, n_boot=150, n_splits=10)
    print(f"Optimal Alpha: {rapm_res['best_alpha']}")
    print("Pressure Interactions:\n", rapm_res["pres_df"].to_string(index=False))
    print("\nRanking Stability:\n", rapm_res["stab_df"].to_string(index=False))
    print("\nModel Comparison (V4.4 vs V4.3 & V4.2):\n", rapm_res["comp_df"].to_string(index=False))

    print("\n=== TRACK B: OBSERVABLE RESOURCE PRESSURE BRIDGE ===")
    tb = run_track_b_observable_resource_pressure(cfg, n_boot=100, n_splits=10)
    print(f"Track B P75 Cutoff: {tb['p75_cutoff']:.4f}")
    print("Track B Comparison:\n", tb["comp_df"].to_string(index=False))


if __name__ == "__main__":
    main()
