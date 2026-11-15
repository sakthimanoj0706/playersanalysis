"""Compute and persist all SupeRR Intelligence V4.2 rankings, diagnostics, and reports."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4_2.reporting_v42 import RELEASE_STATUS_V42, write_v42_artifacts
from src.v4_2.validation_and_pipeline import run_full_v42_pipeline


def main() -> None:
    print(f"Running SupeRR Intelligence V4.2 pipeline ({RELEASE_STATUS_V42})...")
    res = run_full_v42_pipeline(data_dir="data", boot_iters=2000, seed=42)
    paths = write_v42_artifacts(res, data_dir="data")
    print(f"Completed in {res['elapsed_sec']:.1f}s")
    for k, v in paths.items():
        print(f"  {k}: {v}")
    print("\nTop 10 Batters:", ", ".join(
        res["bat_full"][res["bat_full"]["eligible"]]
        .sort_values(["eb_delta", "prob_top_10", "effective_exposure"], ascending=[False, False, False])
        .head(10).apply(lambda r: f"{r['player_name']} ({r['player_id']})", axis=1).tolist()
    ))
    print("Top 10 Bowlers:", ", ".join(
        res["bowl_full"][res["bowl_full"]["eligible"]]
        .sort_values(["eb_delta", "prob_top_10", "effective_exposure"], ascending=[False, False, False])
        .head(10).apply(lambda r: f"{r['player_name']} ({r['player_id']})", axis=1).tolist()
    ))


if __name__ == "__main__":
    main()
