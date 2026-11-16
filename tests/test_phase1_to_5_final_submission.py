"""Regression tests for Phases 1-5 final submission artifacts and dashboard."""

from __future__ import annotations

import hashlib
import json
import py_compile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIN_DIR = ROOT / "data/outputs/final"
V42_DIR = ROOT / "data/outputs/v4_2"


def test_phase1_star_player_audit_and_cummins_alias() -> None:
    df = pd.read_csv(ROOT / "STAR_PLAYER_ELIGIBILITY_AUDIT.csv")
    assert len(df) == 21
    cummins = df[df["player_name"].str.contains("Cummins", case=False, na=False)]
    assert len(cummins) == 1
    assert int(cummins.iloc[0]["canonical_player_id"]) == 1758
    assert bool(cummins.iloc[0]["eligible"]) is True
    jaiswal = df[df["player_name"] == "Yashasvi Jaiswal"]
    assert len(jaiswal) == 1
    assert bool(jaiswal.iloc[0]["eligible"]) is False


def test_phase2_methodology_comparison_present() -> None:
    df = pd.read_csv(ROOT / "PRESSURE_METHODOLOGY_COMPARISON.csv")
    assert len(df) >= 5
    assert (df["selection_status"] == "SELECTED_PRIMARY_BASELINE").sum() == 2
    assert "Calibrated_Chase_Leverage_WPA_Blocked" in set(df["methodology_id"])


def test_phase3_final_outputs_match_source_of_truth_and_v42() -> None:
    sot = json.loads((FIN_DIR / "FINAL_RANKING_SOURCE_OF_TRUTH.json").read_text(encoding="utf-8"))
    for fname, expected_hash in sot["hashes"].items():
        actual_hash = hashlib.sha256((FIN_DIR / fname).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}"
    for fname, expected_hash in sot["rr_hashes"].items():
        actual_hash = hashlib.sha256((FIN_DIR / fname).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}"

    top_bat = pd.read_csv(FIN_DIR / "FINAL_TOP_10_BATTERS.csv")
    top_bowl = pd.read_csv(FIN_DIR / "FINAL_TOP_10_BOWLERS.csv")
    v42_short = pd.read_csv(V42_DIR / "V4_2_FINAL_SHORTLIST.csv")

    v42_bat_ids = v42_short[v42_short["role"] == "batter"].sort_values("shortlist_rank_display")["player_id"].tolist()
    v42_bowl_ids = v42_short[v42_short["role"] == "bowler"].sort_values("shortlist_rank_display")["player_id"].tolist()
    assert top_bat.sort_values("shortlist_rank_display")["player_id"].tolist() == v42_bat_ids
    assert top_bowl.sort_values("shortlist_rank_display")["player_id"].tolist() == v42_bowl_ids


def test_phase4_rr_spinners_and_decoupling() -> None:
    rr_top = pd.read_csv(FIN_DIR / "RR_TOP10_CANDIDATE_FIT.csv")
    rr_out = pd.read_csv(FIN_DIR / "RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv")
    for spinner in ["Noor Ahmad", "Maheesh Theekshana"]:
        row = rr_top[rr_top["player_name"] == spinner]
        assert len(row) == 1
        assert row.iloc[0]["rr_target_role"] == "Economical Middle-Over Spinner"
    narine = rr_out[rr_out["player_name"] == "Sunil Narine"]
    assert len(narine) == 1
    assert narine.iloc[0]["rr_target_role"] == "Economical Middle-Over Spinner"


def test_phase5_dashboard_compiles_and_nan_not_zero() -> None:
    for fname in ["dashboard/app.py", "dashboard/data_loader.py", "dashboard/charts.py"]:
        py_compile.compile(str(ROOT / fname), doraise=True)
    loader_src = (ROOT / "dashboard/data_loader.py").read_text(encoding="utf-8")
    assert "data/outputs/final" in loader_src
    assert 'unavailable: str = "Unavailable"' in loader_src
    assert '"RANKING_SOURCE_OF_TRUTH.json"' not in loader_src

    from dashboard.data_loader import esc, fmt_num, load_all_data

    assert fmt_num(float("nan")) == "Unavailable"
    assert fmt_num(None) == "Unavailable"
    assert "&lt;script&gt;" in esc("<script>")
    loaded = load_all_data()
    assert len(loaded["top_bat"]) == 10
    assert len(loaded["top_bowl"]) == 10
