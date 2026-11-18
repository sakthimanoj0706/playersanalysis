"""Automated tests for V4.3 Phases 3.5, 5, 6, 7 and Task 5."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.v4_3.config import DEFAULT_CONFIG
from src.v4_3.delta_re_batter import compute_phase5_delta_re_batter
from src.v4_3.joint_rapm import build_joint_rapm_design, fit_ridge_rapm
from src.v4_3.score_reconstruction import build_innings_state_and_score_audit
from src.v4_3.scorecard_diagnostic import run_scorecard_recovery_diagnostic


def test_phase5_delta_re_transitions_and_identity() -> None:
    """Verify legal-ball transitions, terminal ER=0, and exact DeltaRE_batter identity."""
    reg, _, sr_audit, _ = build_innings_state_and_score_audit(DEFAULT_CONFIG)
    df_p5, val_df, _ = compute_phase5_delta_re_batter(reg, DEFAULT_CONFIG, n_boot=50)

    # 1. Exact DeltaRE_batter identity
    calc = df_p5["batter_runs"].astype(float) + df_p5["er_after_batter"] - df_p5["er_before_batter"]
    assert np.allclose(df_p5["delta_re_batter"].values, calc.values, atol=1e-12)

    # 2. Wides and Oversteps do NOT reduce balls_rem_after
    illegal = df_p5[df_p5["extras_category"].isin(["wide", "Overstep"])]
    assert np.allclose(illegal["balls_rem_after"].values, illegal["balls_rem_before"].values)

    # 3. Legal deliveries reduce balls_rem_after by 1 (when balls_rem_before >= 1)
    legal = df_p5[(df_p5["legal_ball_inc"] == 1) & (df_p5["balls_rem_before"] >= 1)]
    assert np.allclose(legal["balls_rem_after"].values, legal["balls_rem_before"].values - 1.0)

    # 4. Terminal states have er_after_batter == 0.0
    term = df_p5[(df_p5["balls_rem_after"] <= 0) | (df_p5["wkts_rem_after"] <= 0)]
    assert np.allclose(term["er_after_batter"].values, 0.0)

    # 5. ER_batter outperforms historical-rate baseline on OOF MAE
    oof = val_df[val_df["evaluation_split"] == "MatchGrouped_5Fold_OOF"].set_index("model_name")
    assert oof.loc["ER_batter_BW_EB_Par", "mae"] < oof.loc["Historical_Rate_Baseline", "mae"]

    # 6. Scorecard diagnostic never fabricates external scorecards
    sc_df, sc_sum = run_scorecard_recovery_diagnostic(sr_audit, DEFAULT_CONFIG)
    assert sc_sum["external_scorecard_files_found"] == 0
    assert (sc_df["verification_status"] == "UNRESOLVED_NO_INDEPENDENT_SCORECARD").sum() > 1600


def test_phase6_rapm_attribution_and_reproducibility() -> None:
    """Verify non-bowler dismissal separation and deterministic Ridge RAPM fits."""
    reg, _, _, _ = build_innings_state_and_score_audit(DEFAULT_CONFIG)
    sub = reg.iloc[:15000].copy().reset_index(drop=True)
    sub["eb_venue_par_factor_oof"] = 1.0
    sub["elo_diff_bat_minus_bowl"] = 0.0
    sub["delta_re_batter"] = sub["batter_runs"].astype(float) - 1.2 - 5.0 * sub["wicket_inc"].astype(float)

    design = build_joint_rapm_design(sub)
    assert "is_non_bowler_dismissal_sep" in design["ctrl_names"]
    assert "is_unresolved_wicket_sep" in design["ctrl_names"]

    fit1 = fit_ridge_rapm(design, alpha=250.0, seed=2026)
    fit2 = fit_ridge_rapm(design, alpha=250.0, seed=2026)
    assert np.allclose(fit1["bat_effect_per100"], fit2["bat_effect_per100"])
    assert np.allclose(fit1["bowl_defensive_per100"], fit2["bowl_defensive_per100"])
    # Mean-centering identifiability check
    assert abs(float(np.mean(fit1["bat_effect_per100"]))) < 1e-10
    assert abs(float(np.mean(fit1["bowl_defensive_per100"]))) < 1e-10
