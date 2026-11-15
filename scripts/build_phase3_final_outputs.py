"""Phase 3: Build authoritative final outputs under data/outputs/final/ from verified V4.2."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _exclusion_reason(r: pd.Series) -> str:
    if bool(r["eligible"]):
        return "ELIGIBLE"
    reasons = []
    if float(r["n_hi"]) < 50:
        reasons.append(f"n_hi={int(r['n_hi'])}<50")
    if float(r["n_lo"]) < 30:
        reasons.append(f"n_lo={int(r['n_lo'])}<30")
    if float(r["cs_matches"]) < 8:
        reasons.append(f"cs_matches={int(r['cs_matches'])}<8")
    if pd.isna(r["se_delta"]) or float(r["se_delta"]) > 25.0:
        se_s = "NaN" if pd.isna(r["se_delta"]) else f"{float(r['se_delta']):.2f}"
        reasons.append(f"se_delta={se_s}>25.0")
    return "; ".join(reasons) if reasons else "INELIGIBLE"


def _sample_confidence(r: pd.Series) -> str:
    if not bool(r["eligible"]):
        return "LOW_INSUFFICIENT_EXPOSURE"
    if int(r["cs_matches"]) >= 50 and float(r["se_delta"]) <= 16.0:
        return "HIGH"
    if int(r["cs_matches"]) >= 30 and float(r["se_delta"]) <= 21.0:
        return "MODERATE"
    return "PROVISIONAL_BOUNDARY"


def main() -> None:
    v42_dir = ROOT / "data/outputs/v4_2"
    fin_dir = ROOT / "data/outputs/final"
    fin_dir.mkdir(parents=True, exist_ok=True)

    sl = pd.read_csv(v42_dir / "V4_2_FINAL_SHORTLIST.csv")
    all_est = pd.read_csv(v42_dir / "V4_2_ALL_PLAYER_ESTIMATES.csv")
    rp = pd.read_csv(v42_dir / "V4_2_RANK_PROBABILITIES.csv")
    v42_sot = json.loads((v42_dir / "V4_2_SOURCE_OF_TRUTH.json").read_text(encoding="utf-8"))

    # Merge rank probabilities & shortlist rank onto ALL_PLAYER_FINAL_ESTIMATES without _x/_y duplicates
    extra_rp_cols = [c for c in [
        "eb_rank", "boot_rank_ci_low", "boot_rank_median",
        "boot_rank_ci_high", "prob_top_10", "mcse_prob_top_10",
        "eb_boot_ci_low", "eb_boot_ci_high",
    ] if c not in all_est.columns]
    merged = all_est.merge(rp[["role", "player_id"] + extra_rp_cols], on=["role", "player_id"], how="left") if extra_rp_cols else all_est.copy()
    sl_ranks = sl[["role", "player_id", "shortlist_rank_display"]].copy()
    merged = merged.merge(sl_ranks, on=["role", "player_id"], how="left")
    merged["exclusion_reason"] = merged.apply(_exclusion_reason, axis=1)
    merged["sample_confidence"] = merged.apply(_sample_confidence, axis=1)
    merged.to_csv(fin_dir / "ALL_PLAYER_FINAL_ESTIMATES.csv", index=False)

    # Top 10 Batters
    bat_top = sl[sl["role"] == "batter"].copy().sort_values("shortlist_rank_display")
    bat_top["sample_confidence"] = bat_top.apply(_sample_confidence, axis=1)
    bat_top["player_explanation"] = bat_top.apply(
        lambda r: (
            f"Rank #{int(r['shortlist_rank_display'])} of 106 eligible batters under BATTING_WICKET_DEPLETION_ANOMALY: "
            f"EB Delta={float(r['eb_delta']):.2f} ({float(r['eb_vs_pop_mean_delta']):+.2f} vs pop mean -36.12), "
            f"P(Top 10)={float(r['prob_top_10']):.3f}, CS={int(r['cs_matches'])} matches."
        ),
        axis=1,
    )
    bat_top.to_csv(fin_dir / "FINAL_TOP_10_BATTERS.csv", index=False)

    # Top 10 Bowlers
    bowl_top = sl[sl["role"] == "bowler"].copy().sort_values("shortlist_rank_display")
    bowl_top["sample_confidence"] = bowl_top.apply(_sample_confidence, axis=1)
    bowl_top["player_explanation"] = bowl_top.apply(
        lambda r: (
            f"Rank #{int(r['shortlist_rank_display'])} of 136 eligible bowlers under BOWLING_EXPECTED_SCORING_THREAT "
            f"(batter-runs suppression proxy): EB Delta={float(r['eb_delta']):.2f} ({float(r['eb_vs_pop_mean_delta']):+.2f} "
            f"vs pop mean -50.88), P(Top 10)={float(r['prob_top_10']):.3f}, CS={int(r['cs_matches'])} matches."
        ),
        axis=1,
    )
    bowl_top.to_csv(fin_dir / "FINAL_TOP_10_BOWLERS.csv", index=False)

    # Copy documentation artifacts cleanly
    shutil.copyfile(ROOT / "data/reports/v4_2/V4_2_PLAYER_JUSTIFICATIONS.md", fin_dir / "FINAL_PLAYER_JUSTIFICATIONS.md")
    shutil.copyfile(ROOT / "METHODOLOGY_REPORT.md", fin_dir / "FINAL_METHODOLOGY_REPORT.md")

    hashes = {
        fname: _sha256(fin_dir / fname)
        for fname in [
            "FINAL_TOP_10_BATTERS.csv",
            "FINAL_TOP_10_BOWLERS.csv",
            "ALL_PLAYER_FINAL_ESTIMATES.csv",
        ]
    }
    sot_final = {
        "authoritative_output_dir": "data/outputs/final",
        "model_version": "V4.2",
        "release_status": v42_sot["release_status"],
        "chase_score_reconstruction_blocked": v42_sot["chase_score_reconstruction_blocked"],
        "estimator": v42_sot["estimator"],
        "derived_from_v42_source_of_truth": "data/outputs/v4_2/V4_2_SOURCE_OF_TRUTH.json",
        "v42_shortlist_sha256": v42_sot["hashes"]["V4_2_FINAL_SHORTLIST.csv"],
        "top10_batters": v42_sot["top10_batters"],
        "top10_batter_names": v42_sot["top10_batter_names"],
        "top10_bowlers": v42_sot["top10_bowlers"],
        "top10_bowler_names": v42_sot["top10_bowler_names"],
        "hashes": hashes,
    }
    (fin_dir / "FINAL_RANKING_SOURCE_OF_TRUTH.json").write_text(json.dumps(sot_final, indent=2), encoding="utf-8")
    print("Phase 3 authoritative outputs built in data/outputs/final/:")
    for k, v in hashes.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
