"""Verify SupeRR Intelligence V4.2 artifact integrity, SHA256 hashes, identities, and invariants."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    out_dir = Path("data/outputs/v4_2")
    rep_dir = Path("data/reports/v4_2")
    sot_path = out_dir / "V4_2_SOURCE_OF_TRUTH.json"
    assert sot_path.exists(), "Missing V4_2_SOURCE_OF_TRUTH.json"
    sot = json.loads(sot_path.read_text(encoding="utf-8"))

    assert sot["release_status"] == "V4.2 PROVISIONAL — RESOURCE STRESS"
    assert sot["chase_score_reconstruction_blocked"] is True

    for fname, expected_hash in sot["hashes"].items():
        p = out_dir / fname
        assert p.exists(), f"Missing hashed output {fname}"
        assert _sha256(p) == expected_hash, f"Hash mismatch for {fname}"

    sl = pd.read_csv(out_dir / "V4_2_FINAL_SHORTLIST.csv")
    assert (sl["role"] == "batter").sum() == 10
    assert (sl["role"] == "bowler").sum() == 10
    assert sl[sl["role"] == "batter"]["player_id"].tolist() == sot["top10_batters"]
    assert sl[sl["role"] == "bowler"]["player_id"].tolist() == sot["top10_bowlers"]

    rp = pd.read_csv(out_dir / "V4_2_RANK_PROBABILITIES.csv")
    for role in ("batter", "bowler"):
        sub = rp[rp["role"] == role]
        # Fractional Top-10 probabilities must sum to 10.0 within Monte Carlo / float rounding
        assert abs(sub["prob_top_10"].sum() - 10.0) < 1e-4, f"{role} prob_top_10 sum={sub['prob_top_10'].sum()}"

    dec = pd.read_csv(out_dir / "V4_2_RAW_ADJUSTED_DECOMPOSITION.csv")
    assert dec["nuisance_identity_residual"].abs().max() < 1e-6
    assert dec["bridge_identity_residual"].abs().max() < 1e-6

    val = pd.read_csv(out_dir / "V4_2_VALIDATION_MATRIX.csv")
    spans = val[val["check"].str.startswith("quant_span_")][["check", "span"]].drop_duplicates()
    assert set(spans["span"].round(4)) == {0.60, 0.70, 0.75}, f"Unexpected spans: {spans}"
    assert bool(val["passed"].all()), f"Failed checks:\n{val[~val['passed']]}"

    audit = pd.read_csv(out_dir / "V4_2_SCORE_ENRICHMENT_AUDIT.csv")
    assert (audit["legal_balls"] <= audit["delivery_rows"]).all()

    assert (rep_dir / "V4_2_RELEASE_DECISION.md").exists()
    print("ALL V4.2 ARTIFACT & MATHEMATICAL VERIFICATIONS PASSED!")


if __name__ == "__main__":
    main()
