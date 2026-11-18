"""Regression tests for SupeRR Intelligence V4.2 judge-readiness and documentation fixes."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from src.v4_2.pressure_revalidation import describe_pressure_proxy_trace

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def test_01_02_03_root_readme_v42_entrypoint() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "SupeRR Intelligence V4.2" in readme
    assert "V4.2 PROVISIONAL — RESOURCE STRESS" in readme
    assert "METHODOLOGY_REPORT.md" in readme
    assert "# SupeRR Intelligence V3" not in readme
    assert "Shreyas Iyer" not in readme
    assert "Imad Wasim" not in readme
    assert "Archived Baselines" in readme


def test_04_methodology_report_explains_eb_vs_pop_mu0() -> None:
    report = (ROOT / "METHODOLOGY_REPORT.md").read_text(encoding="utf-8")
    assert "EB vs Pop" in report
    assert "EB Δ − μ₀" in report
    assert "David Miller" in report
    assert "Matheesha Pathirana" in report
    assert "P(Top 10)" in report
    assert "P(Δ > 0)" in report


def test_05_06_07_08_player_justifications_completeness_and_caveats() -> None:
    just_path = ROOT / "data/reports/v4_2/V4_2_PLAYER_JUSTIFICATIONS.md"
    assert just_path.exists()
    text = just_path.read_text(encoding="utf-8")

    part_a, part_b = text.split("## Part B — Top 10 Bowlers", maxsplit=1)
    bat_headers = re.findall(r"^### \d+\. .+ \(Player ID: `\d+`\)$", part_a, flags=re.MULTILINE)
    bowl_headers = re.findall(r"^### \d+\. .+ \(Player ID: `\d+`\)$", part_b, flags=re.MULTILINE)
    assert len(bat_headers) == 10
    assert len(bowl_headers) == 10

    # Michael Bracewell 37 low-proxy-ball caveat
    assert "Michael Bracewell" in part_a
    assert "37" in part_a and "low-proxy balls" in part_a

    # Brian Bennett missing paired within-match high/low caveat
    assert "Brian Bennett" in part_a
    assert "within_match_hilo_matches" in part_a
    assert "not established" in part_a

    # Craig Young 23 common-support-match caveat
    assert "Craig Young" in part_b
    assert "23" in part_b and "[2, 75]" in part_b


def test_09_10_11_12_dashboard_filters_labels_and_explanations() -> None:
    dash = (ROOT / "dashboard/app.py").read_text(encoding="utf-8")
    audit = pd.read_csv(ROOT / "data/outputs/v4_2/V4_2_SCORE_ENRICHMENT_AUDIT.csv")

    assert "MARGIN_MISMATCH_BLOCKED" in dash
    assert "NON_DLS_RUN_MARGIN_FAIL" not in dash
    assert (audit["match_validation_status"] == "MARGIN_MISMATCH_BLOCKED").sum() > 0

    assert "Raw Hi (-Runs/100b)" in dash
    assert "Raw Lo (-Runs/100b)" in dash
    assert "Raw Hi Saved" not in dash
    assert "Raw Lo Saved" not in dash

    assert "EB vs Pop μ₀ = EB Δ − μ₀" in dash
    assert "absolute effect remains negative" in dash


def test_13_14_bowler_pressure_trace_matches_design_matrix() -> None:
    import numpy as np

    dummy_b3 = {
        "curve_params": {
            1: np.array([238.0, 1.19, 0.53]),
            2: np.array([396.5, 0.47, 0.31]),
        }
    }
    trace = describe_pressure_proxy_trace(dummy_b3)
    bowl = trace["proxies"]["BOWLING_EXPECTED_SCORING_THREAT"]

    expected_terms = [
        "pp", "mid", "death", "inn2", "fmt", "wf", "u",
        "pp * wf", "mid * wf", "death * wf", "death * (1 - wf)", "inn2 * u", "death * u",
    ]
    assert bowl["design_matrix_terms"] == expected_terms

    serialized = json.dumps(bowl)
    assert "venue_season" not in serialized
    assert "log(wickets_rem" not in serialized
    assert "overid" not in serialized


def test_15_16_source_of_truth_provenance_and_unchanged_csv_hashes() -> None:
    sot_path = ROOT / "data/outputs/v4_2/V4_2_SOURCE_OF_TRUTH.json"
    sot = json.loads(sot_path.read_text(encoding="utf-8"))

    assert sot["git_head_sha_at_generation"] == "f68c2e3c23e183af720abe66bdd7d90d576a93fe"
    assert sot["ranking_artifacts_committed_in_sha"] == "7762786f0f91c086d924642f885bf1f1f3133eda"
    assert "provenance_note" in sot

    assert sot["hashes"]["V4_2_FINAL_SHORTLIST.csv"] == "7259fa0c5bc6536eb84699271ffcaa648537b6ffee71df9b9c9abc9135dc1917"
    for fname, expected_hash in sot["hashes"].items():
        p = ROOT / "data/outputs/v4_2" / fname
        assert p.exists()
        assert _sha256(p) == expected_hash
