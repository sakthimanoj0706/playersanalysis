"""Automated tests & mathematical invariants for V4.3 Phases 0-3."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from src.v4_3.config import DEFAULT_CONFIG
from src.v4_3.data_audit import run_phase0_data_audit
from src.v4_3.expected_runs import evaluate_phase2_expected_runs, fit_eb_par_model, fit_er_model, predict_er
from src.v4_3.score_reconstruction import build_innings_state_and_score_audit
from src.v4_3.win_probability import (
    _build_inn1_features,
    _build_inn2_features,
    _fit_predict_logistic,
    compute_pre_match_elo,
    evaluate_phase3_win_probability,
)


def test_phase0_and_phase1_invariants() -> None:
    """Verify scale, Super Over isolation, score monotonicity, legal-ball rules, and reconstruction block."""
    audit_df, p0 = run_phase0_data_audit(DEFAULT_CONFIG)
    assert p0["counts"]["regular_matches"] == 837
    assert p0["counts"]["regular_innings"] == 1652
    assert p0["counts"]["regular_delivery_rows"] == 193988
    assert p0["counts"]["regular_legal_deliveries"] == 185951
    assert p0["extras_audit"]["extras1_codebook_mismatches"] == 0

    reg, so, sr_audit, p1 = build_innings_state_and_score_audit(DEFAULT_CONFIG)

    # 1. Super Overs stay separate
    assert set(reg["innings"].unique()) == {1, 2}
    assert set(so["innings"].unique()).issubset({3, 4})
    assert len(so) == 26

    # 2. Score never decreases within (match_id, innings)
    diffs_bat = reg.groupby(["match_id", "innings"])["batter_runs_before"].diff().dropna()
    diffs_lb = reg.groupby(["match_id", "innings"])["min_team_score_before_lb"].diff().dropna()
    assert (diffs_bat >= 0).all()
    assert (diffs_lb >= 0).all()

    # 3. Wickets remain within valid limits [0, 9] pre-delivery
    assert (reg["wkts_before"] >= 0).all() and (reg["wkts_before"] <= 9).all()
    assert (reg["wkts_rem_before"] >= 1).all() and (reg["wkts_rem_before"] <= 10).all()

    # 4. Wides and Oversteps do not consume legal balls
    wides_nb = reg[reg["extras_category"].isin(["wide", "Overstep"])]
    assert (wides_nb["legal_ball_inc"] == 0).all()
    assert (sr_audit["legal_balls"] <= sr_audit["delivery_rows"]).all()

    # 5. Score reconstruction never fabricates exact totals when extras exist
    blocked = sr_audit[~sr_audit["score_verified"]]
    assert blocked["reconstructed_innings_total"].isna().all()
    verified = sr_audit[sr_audit["score_verified"]]
    assert (verified["any_extra_events"] == 0).all()
    assert verified["reconstructed_innings_total"].notna().all()
    assert p1["score_dependent_wp_blocked"] is True


def test_phase2_eb_par_and_er_invariants() -> None:
    """Verify EB shrinkage pulls small-sample venues toward format prior and ER(B, W) >= 0."""
    reg, _, _, _ = build_innings_state_and_score_audit(DEFAULT_CONFIG)
    eb = fit_eb_par_model(reg, DEFAULT_CONFIG)
    fv = eb["format_venue_table"]
    small_v = fv[fv["n"] == 1]
    large_v = fv[fv["n"] >= 20]
    if len(small_v) > 0 and len(large_v) > 0:
        assert small_v["eb_weight"].mean() < large_v["eb_weight"].mean()

    er_state = fit_er_model(reg.iloc[:15000], DEFAULT_CONFIG)
    preds = predict_er(reg.iloc[:1000], er_state)
    assert np.all(np.isfinite(preds))
    assert np.all(preds >= 0.0)


def test_phase3_wp_invariants_and_zero_leakage() -> None:
    """Verify WP in [0, 1], unified perspective, no future leakage in Elo, and no match overlap in CV."""
    reg, _, _, _ = build_innings_state_and_score_audit(DEFAULT_CONFIG)

    # Zero-leakage test for pre-match Elo: mutating future match outcomes must not alter earlier Elo
    elo_orig = compute_pre_match_elo(reg, DEFAULT_CONFIG)
    reg_mut = reg.copy()
    last_year = reg_mut["year"].max()
    reg_mut.loc[reg_mut["year"] == last_year, "win_team_id"] = np.nan
    elo_mut = compute_pre_match_elo(reg_mut, DEFAULT_CONFIG)
    early_mask = reg["year"] < last_year
    assert np.allclose(
        elo_orig.loc[early_mask, "elo_diff_bat_minus_bowl"].values,
        elo_mut.loc[early_mask, "elo_diff_bat_minus_bowl"].values,
    )

    # Match-grouped CV non-overlap check
    gkf = GroupKFold(n_splits=5)
    for tr_idx, te_idx in gkf.split(reg.iloc[:5000], groups=reg.iloc[:5000]["match_id"]):
        tr_m = set(reg.iloc[tr_idx]["match_id"].unique())
        te_m = set(reg.iloc[te_idx]["match_id"].unique())
        assert len(tr_m & te_m) == 0

    # Synthetic verified-score WP perspective & bounds test
    rng = np.random.default_rng(2026)
    n_m = 40
    rows = []
    for m in range(n_m):
        inn1_win = int(m % 2 == 0)
        for inn in (1, 2):
            for b in range(1, 21):
                rows.append(
                    {
                        "match_id": m,
                        "innings": inn,
                        "balls_rem_before": 120 - b * 5,
                        "sched_balls": 120.0,
                        "wkts_rem_before": 10 - (b // 4),
                        "match_format": "IPL",
                        "elo_diff_bat_minus_bowl": 0.1 if inn == 1 else -0.1,
                        "eb_venue_par_factor": 1.0,
                        "eb_venue_par_bat_runs": 160.0,
                        "min_team_score_before_lb": float(b * 7 + (15 if inn1_win and inn == 1 else 0)),
                        "legal_balls_before": b * 5,
                        "inn1_min_total_lb": 170.0 if inn1_win else 140.0,
                        "inn1_team_won": inn1_win,
                        "batting_team_won": inn1_win if inn == 1 else (1 - inn1_win),
                    }
                )
    syn = pd.DataFrame(rows)
    for inn in (1, 2):
        sub = syn[syn["innings"] == inn].copy()
        y = (sub["inn1_team_won"] if inn == 1 else sub["batting_team_won"]).values
        X = (
            _build_inn1_features(sub, np.full(len(sub), 80.0), include_score=True)
            if inn == 1
            else _build_inn2_features(sub, include_score=True)
        )
        probs, _, _ = _fit_predict_logistic(X, y, X)
        p_inn1 = probs if inn == 1 else (1.0 - probs)
        assert np.all((p_inn1 >= 0.0) & (p_inn1 <= 1.0))
        # Positive correlation with inn1_team_won proves consistent perspective in BOTH innings
        corr = float(np.corrcoef(p_inn1, sub["inn1_team_won"].values)[0, 1])
        assert corr > 0.2, f"Innings {inn} perspective correlation too low: {corr}"
