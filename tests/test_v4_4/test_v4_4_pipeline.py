"""Automated mathematical invariant & governance tests for SupeRR Intelligence V4.4."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.v4_4.config import DEFAULT_V44_CONFIG
from src.v4_4.leverage_index import OUTCOME_CATS, _fit_outcome_probs


def test_v44_crosswalk_and_extras_invariants() -> None:
    """Verify 1-to-1 match crosswalk, numeric extras identities, and zero forced ambiguous joins."""
    cw = pd.read_csv(DEFAULT_V44_CONFIG.output_dir / "V4_4_MATCH_CROSSWALK.csv")
    exact = cw[cw["join_status"] == "EXACT_MATCH"]
    assert exact["match_id"].is_unique
    assert exact["cs_match_id"].is_unique

    deliv = pd.read_parquet(DEFAULT_V44_CONFIG.output_dir / "V4_4_DELIVERY_CROSSWALK.parquet")
    matched_d = deliv[deliv["cs_match_id"].notna()]
    assert bool(matched_d["cs_runs_sum_ok"].all())
    assert bool(matched_d["cs_extras_sum_ok"].all())

    # Check numeric extras reconciliation identity
    tot_calc = matched_d["cs_batter_runs"] + matched_d["cs_total_extras"]
    assert np.allclose(matched_d["cs_total_runs"].values, tot_calc.values)


def test_v44_wp_leverage_and_total_run_value_invariants() -> None:
    """Verify WP in [0,1], LI >= 0 with mean ~1.0, and DeltaRE_total accounting."""
    trv = pd.read_parquet(DEFAULT_V44_CONFIG.output_dir / "V4_4_TOTAL_RUN_VALUE.parquet")
    assert np.all((trv["wp_inn1_team_oof"] >= 0.0) & (trv["wp_inn1_team_oof"] <= 1.0))
    assert np.all(trv["leverage_index"] >= 0.0)
    assert abs(float(trv["leverage_index"].mean()) - 1.0) < 1e-6

    # Team opposite-sign invariant
    assert np.allclose(trv["delta_re_total"].values, -trv["bowling_team_delta_re_total"].values)

    # Exact DeltaRE_total & player attribution separation
    calc = trv["actual_total_runs"].astype(float) + trv["er_total_after"] - trv["er_total_before"]
    assert np.allclose(trv["delta_re_total"].values, calc.values, atol=1e-12)
    assert np.allclose(
        trv["delta_re_player_attrib"].values,
        trv["delta_re_total"].values - trv["non_bowler_extras"].values,
        atol=1e-12,
    )

    # Outcome probability table sums to 1.0
    reg_enr = pd.read_parquet(DEFAULT_V44_CONFIG.artifacts_dir / "v4_4_regular_deliveries_enriched.parquet")
    sub = reg_enr[reg_enr["score_verified"] == True].iloc[:5000].copy()
    sub["wicket_inc"] = (sub["is_wicket"] == True).astype(int)
    sub["actual_total_runs"] = sub["cs_total_runs"].astype(float)
    prob_map, _ = _fit_outcome_probs(sub)
    for k, probs in prob_map.items():
        assert len(probs) == len(OUTCOME_CATS)
        assert abs(float(np.sum(probs)) - 1.0) < 1e-12


def test_v44_track_b_separation() -> None:
    """Verify Track B outputs are explicitly labeled as batter-runs-only observable resource pressure."""
    tb_bat = pd.read_csv(DEFAULT_V44_CONFIG.output_dir / "V4_4_TRACK_B_RESOURCE_PRESSURE_BATTER.csv")
    assert (tb_bat["model_label"] == "OBSERVABLE_RESOURCE_PRESSURE_RAPM_BATTER_RUNS_ONLY").all()
