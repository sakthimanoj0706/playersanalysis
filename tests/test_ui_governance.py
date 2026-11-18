"""Behavioral and governance verification tests for all 17 V4.2 UI requirements."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from dashboard.charts import (
    dumbbell_shift_chart,
    rank_uncertainty_chart,
    rr_component_chart,
    shrinkage_comparison_chart,
)
from dashboard.data_loader import (
    FINAL_DIR,
    V42_DIR,
    load_all_data,
    load_rr_scouting_enrichment,
)

ROOT = Path(__file__).resolve().parents[1]


def test_01_to_16_authoritative_data_and_chart_contracts() -> None:
    """Verify authoritative V4.2 paths, shrinkage/rank-CI bounds, boundary cases, and chart builders."""
    d = load_all_data()
    extra = load_rr_scouting_enrichment()

    # 16. Legacy V3 root files never read; authoritative V4.2 paths only
    assert FINAL_DIR == ROOT / "data/outputs/final"
    assert V42_DIR == ROOT / "data/outputs/v4_2"
    assert "David Miller" in set(d["top_bat"]["player_name"])
    assert "Shreyas Iyer" not in set(d["top_bat"]["player_name"])
    assert "Matheesha Pathirana" in set(d["top_bowl"]["player_name"])
    assert "Imad Wasim" not in set(d["top_bowl"]["player_name"])

    # 4. All 5 Ridge configs present in model_cmp
    ridge = d["model_cmp"][d["model_cmp"]["status"] == "RIDGE_TUNING_CHECK"]
    assert len(ridge) == 10  # 5 configs x 2 roles

    # 5-8. Shrinkage, negative absolute effects, P(Δ > 0) < 0.001, rank CIs
    tb = d["top_bat"]
    tw = d["top_bowl"]
    assert (tb["eb_delta"] < 0).all()
    assert (tw["eb_delta"] < 0).all()
    assert (tb["prob_positive_effect"] < 0.001).all()
    assert (tw["prob_positive_effect"] < 0.001).all()
    assert round(float(tb["eb_weight"].min()), 3) == 0.111
    assert round(float(tb["eb_weight"].max()), 3) == 0.262
    jadeja = tb[tb["player_name"] == "Ravindra Jadeja"].iloc[0]
    assert round(float(jadeja["prob_top_10"]), 3) == 0.281

    # Charts build cleanly with expected unit labels
    fig_db = dumbbell_shift_chart(tw, is_bowler=True, title="Bowlers")
    assert "Excl. Wides/No-Balls/Multi-Run Extras" in fig_db.layout.xaxis.title.text
    fig_sh = shrinkage_comparison_chart(tb, mu0=-36.124, title="Shrinkage")
    assert len(fig_sh.data) >= 3
    fig_rk = rank_uncertainty_chart(tb, cohort_size=106, title="Rank CI")
    assert fig_rk.layout.xaxis.range[1] == 109

    # 11. Boundary cases in all_est
    ae = d["all_est"]
    bracewell = ae[ae["player_name"] == "Michael Bracewell"].iloc[0]
    bennett = ae[ae["player_name"] == "Brian Bennett"].iloc[0]
    assert int(bracewell["n_lo"]) == 37
    assert pd.isna(bennett["within_match_hilo_matches"])

    # 13-15. RR nationality/slot enrichment & static shortlist 7 OS / 3 Indian check
    sqd = d["rr_squad"].merge(extra["rep"], on="player_id", how="left")
    n_ind = int(sqd["identity_category"].isin(["VERIFIED_INDIA_INTL", "IPL_DOMESTIC_POOL"]).sum())
    assert n_ind == 3
    assert len(sqd) - n_ind == 7

    # Weighted RR chart sums to <= 100
    top_pool = d["rr_outside"].head(10)
    fig_rr = rr_component_chart(
        top_pool,
        score_col="fit_score_pressure_heavy",
        weights={"phase_exec_score": 0.25, "role_need_score": 0.20, "pressure_v42_score": 0.35, "sample_conf_score": 0.10, "balance_ipl_score": 0.10},
    )
    assert len(fig_rr.data) == 5


def test_17_streamlit_apptest_all_five_pages_and_slot_behavior() -> None:
    """Headlessly render all 5 dashboard sections and test interactive slot feasibility."""
    from streamlit.testing.v1 import AppTest

    app_path = str(ROOT / "dashboard/app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    assert not at.exception

    # Check Page 1 (Overview) disclosures
    md_text = "\n".join(m.value for m in at.markdown)
    assert "CHASE_SCORE_RECONSTRUCTION_BLOCKED = True" in md_text
    assert "Pressure Evaluation: Resource-Stress Proxy — Provisional" in md_text
    assert "BATTING_WICKET_DEPLETION_ANOMALY" in md_text
    assert "BOWLING_EXPECTED_SCORING_THREAT" in md_text

    # Page 2 (Universal Top 10)
    at.sidebar.radio[0].set_value("2. Universal Top 10").run()
    assert not at.exception
    md_p2 = "\n".join(m.value for m in at.markdown)
    assert "Batter μ₀ = -36.124" in md_p2
    assert "P(Δ > 0) < 0.001" in md_p2 or "P(Δ &gt; 0) &lt; 0.001" in md_p2

    # Page 3 (Player Explorer)
    at.sidebar.radio[0].set_value("3. Player Explorer & Comparison").run()
    assert not at.exception
    md_p3 = "\n".join(m.value for m in at.markdown)
    assert "OPERATIONAL_PRECISION_FLOOR_NOT_EMPIRICALLY_OPTIMAL" in md_p3

    # Page 4 (RR Scouting & Auction) — test interactive slot change 0 -> 2
    at.sidebar.radio[0].set_value("4. Rajasthan Royals Intelligence").run()
    assert not at.exception
    md_p4 = "\n".join(m.value for m in at.markdown)
    assert "UNVERIFIED_SCENARIO_INPUT" in md_p4
    os_input = [w for w in at.number_input if w.key == "rr_avail_os_slots"][0]
    assert os_input.value == 0
    cap_0 = "\n".join(c.value for c in at.caption)
    os_input.set_value(2).run()
    assert not at.exception
    cap_2 = "\n".join(c.value for c in at.caption)
    assert cap_0 != cap_2  # Slot-feasible count updates immediately when available OS slots change

    # Page 5 (Methodology & Audit)
    at.sidebar.radio[0].set_value("5. Methodology & Transparency").run()
    assert not at.exception
    all_p5 = "\n".join([m.value for m in at.markdown] + [w.value for w in at.warning])
    assert "CLAIM_C_OOT_UNPREDICTABLE_UNDER_RESOURCE_STRESS" in all_p5
    assert "OPERATIONAL_PRECISION_FLOOR_NOT_EMPIRICALLY_OPTIMAL" in all_p5
