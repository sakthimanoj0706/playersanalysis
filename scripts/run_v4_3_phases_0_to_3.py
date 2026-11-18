"""Run SupeRR Intelligence V4.3 Phases 0-3 and print validation summaries."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4_3.config import DEFAULT_CONFIG
from src.v4_3.data_audit import run_phase0_data_audit
from src.v4_3.expected_runs import evaluate_phase2_expected_runs
from src.v4_3.score_reconstruction import build_innings_state_and_score_audit
from src.v4_3.win_probability import evaluate_phase3_win_probability


def main() -> None:
    cfg = DEFAULT_CONFIG
    print("=== PHASE 0: REPOSITORY & DATA AUDIT ===")
    audit_df, p0_sum = run_phase0_data_audit(cfg)
    print("Counts:", p0_sum["counts"])
    print("Phase Decisions:", p0_sum["phase_decisions"])

    print("\n=== PHASE 1: SCORE RECONSTRUCTION & INNINGS-STATE VALIDATION ===")
    reg, so, sr_audit, p1_sum = build_innings_state_and_score_audit(cfg)
    print("Phase 1 Summary:", p1_sum)

    print("\n=== PHASE 2: EB VENUE/FORMAT PAR & RESOURCE ER(B, W) ===")
    er_metrics, er_sub, er_state = evaluate_phase2_expected_runs(reg, cfg)
    print(er_metrics.to_string(index=False))
    print("\nSubgroup breakdown:")
    print(er_sub.to_string(index=False))

    print("\n=== PHASE 3: TWO-INNINGS WIN PROBABILITY ENGINE ===")
    inn1_df, inn2_df, cal_df, p3_sum = evaluate_phase3_win_probability(reg, cfg)
    print("First Innings WP:")
    print(inn1_df.to_string(index=False))
    print("\nSecond Innings WP:")
    print(inn2_df.to_string(index=False))


if __name__ == "__main__":
    main()
