"""Run SupeRR Intelligence V5.0 Universal T20 Pressure Performance Engine."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v5_0.config import DEFAULT_V50_CONFIG
from src.v5_0.pipeline import run_v5_0_pipeline


def main() -> None:
    res = run_v5_0_pipeline(DEFAULT_V50_CONFIG)
    print("=== PHASE 0: RECALCULATED COUNTS ===")
    print(res["counts"])

    print(f"\n=== PHASE 1: ASYMMETRIC RIDGE TUNING (Selected 1-SE: alpha_main={res['sel_main']}, alpha_int={res['sel_int']}) ===")
    print(res["tune_df"].to_string(index=False))
    print(f"\nChronological OOT (>2024): MSE={res['oot_mse']:.6f}, RMSE={res['oot_rmse']:.6f}")

    print("\n=== PHASE 5: ARCHETYPE COUNTS (ELIGIBLE) ===")
    for role in ("batter", "bowler"):
        tbl = res["bat_df"] if role == "batter" else res["bowl_df"]
        el = tbl[tbl["eligible"]]
        print(f"{role} (n={len(el)}):", el["archetype"].value_counts().to_dict())

    print("\n=== PHASE 10: 50-SPLIT STABILITY ===")
    print(res["stab_df"].to_string(index=False))

    print("\n=== PHASE 10: MODEL COMPARISON ===")
    print(res["cmp_df"].to_string(index=False))


if __name__ == "__main__":
    main()
