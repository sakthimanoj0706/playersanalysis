"""Unit & statistical methodology tests for SupeRR Intelligence V4.2."""

from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.linalg as la

from src.v4_2.consistency_and_decomposition import (
    build_like_for_like_decomposition,
    compute_match_level_consistency_and_lomo,
)
from src.v4_2.fwl_estimator import (
    _build_full_nuisance_and_interaction,
    _solve_complete_penalized_fwl,
    average_ranks_desc,
    fit_v42_option_a_fwl,
    fractional_top_k_membership,
    run_v42_match_cluster_bootstrap,
)
from src.v4_2.pressure_revalidation import (
    BATTING_PROXY_PRIMARY_NAME,
    BOWLING_PROXY_PRIMARY_NAME,
    CHASE_SCORE_RECONSTRUCTION_BLOCKED,
    describe_pressure_proxy_trace,
)
from src.v4_2.score_enrichment_v42 import compute_innings_score_and_legal_balls


def _make_synthetic_cricket_panel(
    n_matches: int = 30,
    n_players: int = 16,
    n_opps: int = 10,
    seed: int = 2026,
    true_tau: float = 18.0,
    true_mu: float = 5.0,
) -> tuple[pd.DataFrame, dict[str, float]]:
    rng = np.random.default_rng(seed)
    true_deltas = {f"P{i:02d}": float(true_mu + rng.normal(0.0, true_tau)) for i in range(n_players)}
    match_fe = {f"M{m:03d}": float(rng.normal(0.0, 10.0)) for m in range(n_matches)}
    player_fe = {f"P{i:02d}": float(rng.normal(125.0, 12.0)) for i in range(n_players)}
    opp_fe = {f"O{o:02d}": float(rng.normal(0.0, 8.0)) for o in range(n_opps)}

    rows = []
    for m in range(n_matches):
        mid = f"M{m:03d}"
        fmt = "IPL" if m % 2 == 0 else "T20I"
        season = "2023" if m < 15 else "2024"
        for i in range(n_players):
            pid = f"P{i:02d}"
            # Include correlated nuisance confounding so incomplete FWL would be biased
            opp = f"O{(i + m) % n_opps:02d}"
            for inn in (1, 2):
                for ph in ("powerplay", "middle", "death"):
                    # Two extreme balls + middle balls inside match
                    p_list = [0.10, 0.15, 0.50, 0.85, 0.90]
                    for p in p_list:
                        state_eff = (10.0 if ph == "death" else (-8.0 if ph == "powerplay" else 0.0)) + (4.0 if inn == 2 else 0.0)
                        beta_i = true_deltas[pid] / 0.75
                        mu_y = 115.0 + state_eff + match_fe[mid] + player_fe[pid] + opp_fe[opp] + (p - 0.5) * beta_i
                        y = float(mu_y + rng.normal(0.0, 12.0))
                        rows.append(
                            {
                                "match_id": mid,
                                "match_date": f"{season}-04-0{(m % 9) + 1}",
                                "innings": inn,
                                "phase": ph,
                                "match_format": fmt,
                                "season": season,
                                "striker_id": pid,
                                "bowler_id": opp,
                                "p_syn": float(np.clip(p + rng.normal(0.0, 0.02), 0.01, 0.99)),
                                "y_syn": y,
                                "weight": 1.0,
                            }
                        )
    df = pd.DataFrame(rows)
    return df, true_deltas


def test_unpenalized_fwl_matches_exact_full_ols() -> None:
    """For unpenalized design, Schur-exact FWL, residual-FWL, and full [Z, W] OLS must agree < 1e-8."""
    df, _ = _make_synthetic_cricket_panel(n_matches=18, n_players=8, n_opps=5, seed=7)
    design = _build_full_nuisance_and_interaction(
        df=df,
        player_col="striker_id",
        opp_col="bowler_id",
        p_col="p_syn",
        y_col="y_syn",
        lam_state=0.0,
        lam_match=0.0,
        lam_player=0.0,
        lam_opp=0.0,
        use_cs_mask=True,
    )
    fwl = _solve_complete_penalized_fwl(design, span=0.75)

    # Independent direct full OLS regression on stacked [Z, W]
    ZW_full = np.hstack([design["Z"].toarray(), design["W"].toarray()])
    coef_full, *_ = la.lstsq(ZW_full, design["y"], cond=1e-12)
    beta_full = coef_full[design["Z"].shape[1]:]

    max_diff_schur = float(np.max(np.abs(fwl["beta_fwl"] - beta_full)))
    max_diff_res = float(np.max(np.abs(fwl["beta_res"] - beta_full)))
    assert max_diff_schur < 1e-8, f"Schur FWL vs full OLS diff={max_diff_schur}"
    assert max_diff_res < 1e-8, f"Residual FWL vs full OLS diff={max_diff_res}"
    assert fwl["reg_gap_max_delta"] < 1e-8


def test_synthetic_hierarchical_recovery_and_bootstrap_coverage() -> None:
    """Synthetic known-effect test verifying REML heterogeneity, estimator correlation, and CI coverage."""
    df, true_deltas = _make_synthetic_cricket_panel(n_matches=30, n_players=16, n_opps=10, seed=42, true_tau=18.0)
    gate = {"min_hi_balls": 10, "min_lo_balls": 10, "min_cs_matches": 5, "max_se_delta": 50.0}
    est_df, meta = fit_v42_option_a_fwl(
        df, "striker_id", "bowler_id", "p_syn", "y_syn",
        lam_state=5.0, lam_match=5.0, lam_player=5.0, lam_opp=5.0,
        span=0.75, eligibility_gate=gate,
    )
    boot_df = run_v42_match_cluster_bootstrap(
        pd.DataFrame({"player_id": meta["design"]["cs_pids"]}),
        meta["fwl"],
        eligible_mask=est_df.set_index("player_id").loc[meta["design"]["cs_pids"], "eligible"].values,
        n_iter=250,
        seed=99,
    )
    merged = est_df.merge(boot_df, on="player_id")
    merged["true_delta"] = merged["player_id"].map(true_deltas)

    # Strong recovery of injected player-specific slopes (after EB pooling)
    r_unsh = float(np.corrcoef(merged["delta_unshrunk"], merged["true_delta"])[0, 1])
    r_eb = float(np.corrcoef(merged["eb_delta"], merged["true_delta"])[0, 1])
    assert r_unsh > 0.90, f"Low unshrunk correlation: {r_unsh}"
    assert r_eb > 0.92, f"Low EB correlation: {r_eb}"
    assert meta["het"]["tau"] > 5.0

    # Empirical coverage of unshrunk bootstrap CIs against true synthetic deltas should be reasonable (~95%)
    covered = (merged["unshrunk_boot_ci_low"] <= merged["true_delta"]) & (
        merged["true_delta"] <= merged["unshrunk_boot_ci_high"]
    )
    assert float(covered.mean()) >= 0.70, f"Low synthetic coverage: {covered.mean()}"
    # Sum of fractional Top-10 probabilities equals 10.0 identically
    assert abs(float(merged["prob_top_10"].sum()) - 10.0) < 1e-6


def test_tied_eb_average_ranks_and_fractional_top10_never_uses_player_id() -> None:
    """Zero-heterogeneity ties must receive identical average ranks and fractional Top-10 shares."""
    # Case 1: All 20 players tied (tau2 == 0)
    all_tied = np.full(20, 1.25)
    ranks = average_ranks_desc(all_tied)
    mem = fractional_top_k_membership(all_tied, k=10)
    assert np.allclose(ranks, 10.5)
    assert np.allclose(mem, 0.5)
    assert abs(mem.sum() - 10.0) < 1e-12

    # Case 2: 8 strictly ahead, 4 tied at cutoff, 4 strictly below
    scores = np.array([20, 19, 18, 17, 16, 15, 14, 13, 10, 10, 10, 10, 5, 4, 3, 2], dtype=float)
    r2 = average_ranks_desc(scores)
    m2 = fractional_top_k_membership(scores, k=10)
    assert np.allclose(r2[8:12], 10.5)  # ranks 9,10,11,12 average to 10.5
    assert np.allclose(m2[:8], 1.0)
    assert np.allclose(m2[8:12], 0.5)   # 2 remaining slots / 4 tied = 0.5 each
    assert np.allclose(m2[12:], 0.0)
    assert abs(m2.sum() - 10.0) < 1e-12

    # Permuting player ordering produces permutation-equivariant ranks & memberships
    rev = scores[::-1]
    assert np.allclose(average_ranks_desc(rev)[::-1], r2)
    assert np.allclose(fractional_top_k_membership(rev, k=10)[::-1], m2)


def test_like_for_like_decomposition_and_consistency_identities() -> None:
    """Verify all 8 contrast columns and exact additive nuisance/bridge identities (< 1e-6)."""
    df, _ = _make_synthetic_cricket_panel(n_matches=16, n_players=8, n_opps=4, seed=11)
    est_df, meta = fit_v42_option_a_fwl(
        df, "striker_id", "bowler_id", "p_syn", "y_syn",
        lam_state=10.0, lam_match=10.0, lam_player=10.0, lam_opp=10.0, span=0.75,
    )
    dec = build_like_for_like_decomposition(
        df, "striker_id", "p_syn", "y_syn", meta["design"], meta["fwl"], est_df, role="batter"
    )
    req_cols = [
        "raw_high_performance",
        "raw_low_performance",
        "raw_all_non_high_performance",
        "raw_hi_minus_lo_delta",
        "raw_hi_minus_all_non_high_delta",
        "discrete_context_adjusted_hi_minus_lo_delta",
        "discrete_context_adjusted_hi_minus_all_non_high_delta",
        "continuous_p875_minus_p125_adjusted_delta",
    ]
    for col in req_cols:
        assert col in dec.columns, f"Missing contrast column {col}"
    assert float(dec["nuisance_identity_residual"].abs().max()) < 1e-6
    assert float(dec["bridge_identity_residual"].abs().max()) < 1e-6

    cons = compute_match_level_consistency_and_lomo(
        df, "striker_id", "p_syn", "y_syn", meta["design"], meta["fwl"], est_df, min_spread_matches=5
    )
    assert (cons["consistency_status"] == "ESTIMATED").all()
    assert (cons["between_match_delta_sd"].notna()).all()
    assert (cons["lomo_min_delta"] <= cons["lomo_max_delta"]).all()

    # Check LIMITED_WITHIN_MATCH_SPREAD warning triggers cleanly when < min_spread_matches
    cons_strict = compute_match_level_consistency_and_lomo(
        df, "striker_id", "p_syn", "y_syn", meta["design"], meta["fwl"], est_df, min_spread_matches=999
    )
    assert (cons_strict["consistency_status"] == "LIMITED_WITHIN_MATCH_SPREAD").all()
    assert cons_strict["between_match_delta_sd"].isna().all()


def test_legal_balls_audit_excludes_wides_and_no_balls() -> None:
    """Section 10 (P2): Verify wides and Overstep no-balls do not increase legal_balls."""
    bbb = pd.DataFrame(
        [
            {"match_id": 1, "innings": 1, "runs": 1, "extras_type": "None", "is_wicket": False, "extras_2_runs": 0},
            {"match_id": 1, "innings": 1, "runs": 0, "extras_type": "wide", "is_wicket": False, "extras_2_runs": 0},
            {"match_id": 1, "innings": 1, "runs": 4, "extras_type": "Overstep", "is_wicket": False, "extras_2_runs": 0},
            {"match_id": 1, "innings": 1, "runs": 0, "extras_type": "legbyes", "is_wicket": False, "extras_2_runs": 0},
            {"match_id": 1, "innings": 1, "runs": 2, "extras_type": "None", "is_wicket": True, "extras_2_runs": 0},
        ]
    )
    inn = compute_innings_score_and_legal_balls(bbb)
    assert int(inn["delivery_rows"].iloc[0]) == 5
    assert int(inn["legal_balls"].iloc[0]) == 3  # Excludes 1 wide + 1 Overstep
    assert int(inn["wide_events"].iloc[0]) == 1
    assert int(inn["overstep_events"].iloc[0]) == 1


def test_v41_span_bug_fixed_in_source() -> None:
    """Section 4 (P0): Verify V4.1 quantile span fix uses exact q_hi - q_lo in source."""
    import inspect
    import src.v4_1.eligibility_and_validation as ev

    src_text = inspect.getsource(ev.run_v41_validation_matrix)
    assert "0.5 * q_lo" not in src_text
    assert "q_hi - q_lo" in src_text


def test_proxy_revalidation_honest_trace() -> None:
    """Section 6: Verify honest naming and blocked chase score trace."""
    assert CHASE_SCORE_RECONSTRUCTION_BLOCKED is True
    assert BATTING_PROXY_PRIMARY_NAME == "BATTING_WICKET_DEPLETION_ANOMALY"
    assert BOWLING_PROXY_PRIMARY_NAME == "BOWLING_EXPECTED_SCORING_THREAT"
    dummy_state = {"curve_params": {1: [160.0, 1.5, 0.85], 2: [155.0, 1.6, 0.80]}}
    trace = describe_pressure_proxy_trace(dummy_state)
    assert trace["chase_score_reconstruction_blocked"] is True
    assert trace["proxies"][BATTING_PROXY_PRIMARY_NAME]["is_calibrated_match_leverage"] is False
    assert trace["proxies"][BATTING_PROXY_PRIMARY_NAME]["is_dls_resources"] is False
    assert "R0" in trace["parameter_role_trace"]
    assert "b" in trace["parameter_role_trace"]
    assert "gamma" in trace["parameter_role_trace"]
