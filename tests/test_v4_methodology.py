"""Automated verification suite for SupeRR Intelligence V4 (Phases A–G)."""
from __future__ import annotations

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from src.v4.data_audit import run_data_audit
from src.v4.hierarchical_model import estimate_heterogeneity, fit_hierarchical_contrast
from src.v4.pressure_proxy import (
    PRESSURE_SOURCE_TYPE,
    apply_b3_resource_stress,
    build_pre_delivery_context,
    fit_b3_resource_stress,
)
from src.v4.ranking_and_validation import run_full_ranking_pipeline


@pytest.fixture(scope="module")
def v4_context():
    reg_ctx, so_ctx = build_pre_delivery_context("data")
    b3_state = fit_b3_resource_stress(reg_ctx)
    reg_b3 = apply_b3_resource_stress(reg_ctx, b3_state)
    return reg_ctx, so_ctx, b3_state, reg_b3


def test_01_data_reconciliation_and_scope():
    with tempfile.TemporaryDirectory() as tmp:
        summary = run_data_audit("data", output_dir=tmp, report_dir=tmp)
        assert summary["scoped_rows"] == 194014
        assert summary["regular_rows"] == 193988
        assert summary["super_over_rows"] == 26
        assert summary["reconcil_diff"] == 26
        assert summary["chase_score_reconstruction_blocked"] is True
        rec = pd.read_csv(os.path.join(tmp, "DATA_RECONCILIATION.csv"))
        assert len(rec) >= 8


def test_02_dls_revised_overs_stored_in_balls(v4_context):
    reg_ctx, _, _, _ = v4_context
    dl = reg_ctx[reg_ctx["first_inn_revised_overs"].notna() & (reg_ctx["innings"] == 1)]
    assert (dl["first_inn_revised_overs"] > 20).all()
    assert (dl["sched_balls"] == dl["first_inn_revised_overs"]).all()


def test_03_extras_and_super_over_isolation(v4_context):
    reg_ctx, so_ctx, _, _ = v4_context
    assert set(reg_ctx["innings"].unique()) == {1, 2}
    assert set(so_ctx["innings"].unique()).issubset({3, 4})
    assert (reg_ctx.loc[reg_ctx["extras_type"] == "wide", "batter_runs"] == 0).all()


def test_04_pre_delivery_outcome_invariance(v4_context):
    reg_ctx, _, b3_state, _ = v4_context
    sample_matches = reg_ctx["match_id"].drop_duplicates().head(10)
    sub = reg_ctx[reg_ctx["match_id"].isin(sample_matches)].copy()
    applied_orig = apply_b3_resource_stress(sub, b3_state)

    sub_mut = sub.copy()
    # Mutate current-delivery realized runs on every 5th ball
    sub_mut.iloc[::5, sub_mut.columns.get_loc("batter_runs")] = 6
    applied_mut = apply_b3_resource_stress(sub_mut, b3_state)

    assert np.allclose(applied_orig["bat_pressure"].values, applied_mut["bat_pressure"].values)
    assert np.allclose(applied_orig["bowl_pressure"].values, applied_mut["bowl_pressure"].values)


def test_05_train_only_b3_chronological_no_leakage(v4_context):
    reg_ctx, _, _, _ = v4_context
    tr = reg_ctx[reg_ctx["year"] <= 2024]
    te = reg_ctx[reg_ctx["year"] >= 2025]
    state = fit_b3_resource_stress(tr)
    te_applied = apply_b3_resource_stress(te, state)
    assert te_applied["bat_pressure"].between(0.0, 1.0).all()
    assert te_applied["bowl_pressure"].between(0.0, 1.0).all()
    # Bat pressure increases strictly with wickets lost
    by_w = te_applied.groupby("wkts_before")["bat_pressure"].mean()
    assert by_w.loc[6] > by_w.loc[2] > by_w.loc[0]
    # Bowler threat higher in death than middle
    by_ph = te_applied.groupby("phase")["bowl_pressure"].mean()
    assert by_ph["death"] > by_ph["middle"]


def test_06_duplicate_names_strictly_id_keyed(v4_context):
    _, _, _, reg_b3 = v4_context
    sub = reg_b3[reg_b3["striker_name"] == "Abdul Samad"]
    assert sub["striker_id"].nunique() >= 2
    bat_df, _ = fit_hierarchical_contrast(reg_b3, role="batter", outcome="batter_runs", bootstrap_iter=0)
    assert bat_df.loc[bat_df["player_name"] == "Abdul Samad", "striker_id"].nunique() >= 2


def test_07_cluster_se_bootstrap_and_eb_properties(v4_context):
    _, _, _, reg_b3 = v4_context
    res, diag = fit_hierarchical_contrast(
        reg_b3, role="bowler", outcome="batter_runs", scale=-100.0, p_col="bowl_pressure",
        bootstrap_iter=2000, bootstrap_seed=42,
    )
    elig = res[(res["n_hi"] >= 100) & (res["n_lo"] >= 60) & (res["cs_matches"] >= 10)].copy()
    assert (elig["se_delta"] >= elig["naive_se"] - 1e-12).all()
    assert ((elig["eb_weight"] >= 0.0) & (elig["eb_weight"] <= 1.0)).all()
    assert diag["tau"] >= 0.0
    boot_ok = elig["boot_ci_low"].notna()
    assert boot_ok.sum() >= 50
    assert (elig.loc[boot_ok, "boot_ci_low"] < elig.loc[boot_ok, "boot_ci_high"]).all()
    # REML estimator consistency
    het_reml = estimate_heterogeneity(elig["raw_fwl_delta"].values, elig["se_delta"].values, method="reml")
    assert het_reml["tau2"] >= 0.0


def test_08_placebo_null_and_synthetic_signal_recovery(v4_context):
    _, _, _, reg_b3 = v4_context
    _, diag_null = fit_hierarchical_contrast(
        reg_b3, role="batter", outcome="batter_runs", scale=100.0,
        p_col="bat_pressure", shuffle_pressure_seed=42, bootstrap_iter=0,
    )
    assert diag_null["tau"] < 1.0

    # Synthetic recovery check (+0.60 runs/ball in high pressure on eligible players)
    syn = reg_b3.copy()
    syn["batter_runs"] = syn["batter_runs"].astype(float)
    r_base, _ = fit_hierarchical_contrast(syn, role="batter", outcome="batter_runs", scale=100.0, bootstrap_iter=0)
    pool = sorted(r_base.loc[(r_base["n_hi"] >= 100) & (r_base["n_lo"] >= 60) & (r_base["cs_matches"] >= 10), "striker_id"].tolist())
    rng = np.random.default_rng(7)
    injected = list(rng.choice(pool, size=8, replace=False))
    mask = syn["striker_id"].isin(injected) & (syn["bat_pressure"] >= 0.75) & (syn["is_ball_faced"] == 1)
    syn.loc[mask, "batter_runs"] = syn.loc[mask, "batter_runs"] + 0.60
    r_syn, _ = fit_hierarchical_contrast(syn, role="batter", outcome="batter_runs", scale=100.0, bootstrap_iter=0)
    top15 = r_syn[(r_syn["n_hi"] >= 100) & (r_syn["n_lo"] >= 60)].sort_values("lcb95_delta", ascending=False)["striker_id"].head(15).tolist()
    assert len(set(injected) & set(top15)) >= 6


def test_09_generated_v4_artifacts_integrity_and_v3_preserved():
    assert os.path.exists("data/outputs/v3/TOP_10_BATTERS.csv")
    assert os.path.exists("data/outputs/v3/TOP_10_BOWLERS.csv")

    t10_bat = pd.read_csv("data/outputs/v4/TOP_10_BATTERS_V4.csv")
    t10_bowl = pd.read_csv("data/outputs/v4/TOP_10_BOWLERS_V4.csv")
    assert len(t10_bat) == 10 and len(t10_bowl) == 10
    assert (t10_bat["n_hi"] >= 100).all() and (t10_bat["n_lo"] >= 60).all()
    assert (t10_bowl["n_hi"] >= 100).all() and (t10_bowl["n_lo"] >= 60).all()
    assert (t10_bat["eb_hi_perf"] > 0).all() and (t10_bowl["eb_hi_perf"] > 0).all()
    assert (t10_bowl["metric_provenance"] == "BATTER_RUNS_CONCEDED_PROXY_SAVED_PER_100_BALLS").all()
    assert (t10_bat["pressure_source_type"] == PRESSURE_SOURCE_TYPE).all()

    sens = pd.read_csv("data/outputs/v4/RANKING_SENSITIVITY_V4.csv")
    for thr in (40, 60, 80, 100, 150, 200, 250):
        assert f"n_hi>={thr}" in set(sens["setting"])

    val = pd.read_csv("data/outputs/v4/MODEL_VALIDATION_V4.csv")
    assert {"B1_WP_OBS_CHRONOLOGICAL", "ROLLING_ORIGIN_TEMPORAL", "SPLIT_HALF_RELIABILITY",
            "PLACEBO_SHUFFLED_PRESSURE", "SYNTHETIC_SIGNAL_RECOVERY"}.issubset(set(val["validation_family"]))

    with open("data/outputs/v4/RANKING_SOURCE_OF_TRUTH_V4.json", "r", encoding="utf-8") as f:
        sot = json.load(f)
    assert sot["chase_score_reconstruction_blocked"] is True
    assert sot["release_status"] == "V4 PROVISIONAL — RESOURCE STRESS PROXY"
    assert [r["player_id"] for r in sot["top_10_batters"]] == t10_bat["player_id"].tolist()
    assert [r["player_id"] for r in sot["top_10_bowlers"]] == t10_bowl["player_id"].tolist()

    for rpt in [
        "DATA_AUDIT_V4.md",
        "PRESSURE_METHODOLOGY_V4.md",
        "PLAYER_RELATIVE_PERFORMANCE_V4.md",
        "VALIDATION_REPORT_V4.md",
        "FINAL_TOP_10_JUSTIFICATION_V4.md",
        "V4_RELEASE_READINESS.md",
    ]:
        assert os.path.exists(os.path.join("data/reports/v4", rpt))
