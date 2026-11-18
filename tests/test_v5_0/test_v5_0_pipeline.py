"""Automated invariant, governance, and UI tests for SupeRR Intelligence V5.0."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize

from src.v5_0.asymmetric_pressure_rapm import build_asymmetric_blocks, solve_block_ridge
from src.v5_0.config import DEFAULT_V50_CONFIG
from src.v5_0.player_archetypes import classify_player_archetypes

ROOT = Path(__file__).resolve().parents[2]


def test_block_penalized_ridge_exactness() -> None:
    """Verify scaled Ridge(alpha=1.0) matches direct block-penalized quadratic objective."""
    rng = np.random.default_rng(2026)
    n = 120
    df = pd.DataFrame(
        {
            "striker_id": [f"B{i % 6}" for i in range(n)],
            "bowler_id": [f"W{i % 5}" for i in range(n)],
            "innings": [1 if i % 2 == 0 else 2 for i in range(n)],
            "match_format": ["T20" if i % 3 == 0 else "T20I" for i in range(n)],
            "innings_phase": [["powerplay", "middle", "death"][i % 3] for i in range(n)],
            "season": ["2024" if i < 60 else "2025" for i in range(n)],
            "balls_rem_before": rng.integers(1, 120, size=n).astype(float),
            "sched_balls": np.full(n, 120.0),
            "wkts_rem_before": rng.integers(1, 10, size=n),
            "elo_diff_bat_minus_bowl": rng.normal(0, 1, size=n),
            "is_non_bowler_dismissal": np.zeros(n, dtype=bool),
            "H_global_150": (rng.random(n) > 0.8).astype(int),
            "delta_re_player_attrib": rng.normal(0, 2.0, size=n),
        }
    )
    blocks = build_asymmetric_blocks(df, "H_global_150")
    am, ai, ac = 250.0, 1500.0, 250.0
    fit = solve_block_ridge(blocks, am, ai, ac, tol=1e-10)

    Xm, Xp, Xc, y = blocks["X_main"].toarray(), blocks["X_pressure"].toarray(), blocks["X_context"].toarray(), blocks["y"]
    nm, np_, nc = Xm.shape[1], Xp.shape[1], Xc.shape[1]

    def obj(params: np.ndarray) -> float:
        b0 = params[0]
        th = params[1 : 1 + nm]
        dl = params[1 + nm : 1 + nm + np_]
        gm = params[1 + nm + np_ :]
        res = y - (b0 + Xm @ th + Xp @ dl + Xc @ gm)
        return float(np.sum(res ** 2) + am * np.sum(th ** 2) + ai * np.sum(dl ** 2) + ac * np.sum(gm ** 2))

    x0 = np.zeros(1 + nm + np_ + nc)
    opt = optimize.minimize(obj, x0, method="BFGS")
    assert np.allclose(fit["theta"], opt.x[1 : 1 + nm], atol=1e-4)
    assert np.allclose(fit["delta"], opt.x[1 + nm : 1 + nm + np_], atol=1e-4)


def test_v50_outputs_and_archetype_invariants() -> None:
    """Verify V5.0 scales, paired HP identity, mutual exclusivity, and exposure definitions."""
    scales = pd.read_csv(DEFAULT_V50_CONFIG.output_dir / "V5_0_PRESSURE_SCALES_SUMMARY.csv")
    assert set(scales["innings"]) == {1, 2}
    assert scales["hp_count_li_global_150"].sum() > 0
    assert scales["hp_count_li_innings_150"].sum() > 0

    for fname in ("V5_0_GLOBAL_BATTER_PRESSURE.csv", "V5_0_GLOBAL_BOWLER_PRESSURE.csv"):
        df = pd.read_csv(DEFAULT_V50_CONFIG.output_dir / fname)
        # Exact combined_hp_per100 == main + pressure_interaction
        assert np.allclose(
            df["combined_hp_per100"].values,
            df["main_effect_per100"].values + df["pressure_interaction_per100"].values,
            atol=1e-10,
        )
        # Ineligible players must never be forced into an active archetype
        inelig = df[~df["eligible"]]
        assert (inelig["archetype"] == "UNCLASSIFIED / INSUFFICIENT EVIDENCE").all()
        # Eligibility gate exact check
        gate_calc = (df["n_hp_global"] >= 100) & (df["total_opportunities"] >= 300) & (df["m_hp"] >= 12)
        assert (df["eligible"] == gate_calc).all()


def test_v50_dashboard_renders_both_engines() -> None:
    """Verify dashboard renders V4.2 by default and switches cleanly across all 5 V5.0 pages."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    at.run()
    assert not at.exception
    at.sidebar.selectbox[0].set_value("V5.0 Universal T20 Pressure Engine (Track A)").run()
    assert not at.exception

    for page in ("1. Overview", "2. Team Analysis", "3. Player Explorer", "4. Match Explorer", "5. Pressure Analytics"):
        nav = [r for r in at.sidebar.radio if r.key == "v50_nav_page"][0]
        nav.set_value(page).run()
        assert not at.exception, f"Exception on V5.0 page {page}: {at.exception}"

    # Verify competition filter changes active scope without error
    comp = [s for s in at.sidebar.selectbox if s.key == "v50_comp_flt"][0]
    comp.set_value("IPL (T20)").run()
    assert not at.exception


def test_v50_official_top10_tables_and_drilldown() -> None:
    """Verify Top 10 Batters/Bowlers integrity, 100/300/12 gate, no duplicates, and drill-down."""
    from streamlit.testing.v1 import AppTest
    from dashboard.v5_0_panel import get_official_top10

    bat_raw = pd.read_csv(DEFAULT_V50_CONFIG.output_dir / "V5_0_GLOBAL_BATTER_PRESSURE.csv")
    bowl_raw = pd.read_csv(DEFAULT_V50_CONFIG.output_dir / "V5_0_GLOBAL_BOWLER_PRESSURE.csv")

    t10_b = get_official_top10(bat_raw, "All Competitions", n=10)
    t10_w = get_official_top10(bowl_raw, "All Competitions", n=10)

    assert len(t10_b) == 10
    assert len(t10_w) == 10
    assert t10_b["player_id"].is_unique
    assert t10_w["player_id"].is_unique
    assert bool(t10_b["eligible"].all())
    assert bool(t10_w["eligible"].all())
    assert t10_b["rank_hp"].tolist() == list(range(1, 11))
    assert t10_w["rank_hp"].tolist() == list(range(1, 11))
    assert t10_b["player_id"].tolist() == bat_raw[bat_raw["eligible"]].sort_values("rank_hp").head(10)["player_id"].tolist()
    assert t10_w["player_id"].tolist() == bowl_raw[bowl_raw["eligible"]].sort_values("rank_hp").head(10)["player_id"].tolist()

    # Headless UI test: click Open Batter Profile -> from Overview Top 10
    at = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    at.run()
    at.sidebar.selectbox[0].set_value("V5.0 Universal T20 Pressure Engine (Track A)").run()
    assert not at.exception
    md_ov = "\n".join(m.value for m in at.markdown)
    assert "TOP 10 PLAYERS" in md_ov
    assert t10_b["player_name"].iloc[0] in md_ov
    assert t10_w["player_name"].iloc[0] in md_ov

    # Select 2nd batter in Top 10 and drill down to Player Explorer
    pick = [s for s in at.selectbox if s.key == "v50_ov_t10_bat_pick"][0]
    pick.set_value(t10_b["player_name"].iloc[1]).run()
    btn = [b for b in at.button if b.key == "v50_ov_t10_bat_go_pe"][0]
    btn.click().run()
    assert not at.exception
    assert at.session_state["v50_nav_page"] == "3. Player Explorer"
    assert at.session_state["v50_selected_player_name"] == t10_b["player_name"].iloc[1]


def test_v50_justifications_and_player_comparison() -> None:
    """Verify justifications, missing CIs, mixed-role rejection, and comparison chart updates."""
    import pytest
    from streamlit.testing.v1 import AppTest
    from dashboard.v5_0_panel import build_player_justification, get_official_top10, get_same_role_comparison_df

    bat_raw = pd.read_csv(DEFAULT_V50_CONFIG.output_dir / "V5_0_GLOBAL_BATTER_PRESSURE.csv")
    bowl_raw = pd.read_csv(DEFAULT_V50_CONFIG.output_dir / "V5_0_GLOBAL_BOWLER_PRESSURE.csv")
    t10_b = get_official_top10(bat_raw, "All Competitions", n=10)
    t10_w = get_official_top10(bowl_raw, "All Competitions", n=10)

    # 1-4: Justifications for all Top 10 batters & bowlers, positive & negative pressure
    for role_lbl, t10 in [("Batter", t10_b), ("Bowler", t10_w)]:
        assert len(t10) == 10
        for i, row in t10.iterrows():
            prev_r = t10.iloc[i - 1] if i > 0 else None
            txt = build_player_justification(row, role_lbl, prev_r)
            assert f"#{int(row['rank_hp'])}" in txt
            assert f"{row['combined_hp_per100']:+.2f}" in txt
            assert f"{int(row['n_hp_global']):,}" in txt
            if row["pressure_interaction_per100"] > 0:
                assert "increased by" in txt
            elif row["pressure_interaction_per100"] < 0:
                assert "reduced by" in txt
            if prev_r is not None:
                assert "lower than #" in txt or "equal to #" in txt

    # 5: Missing confidence intervals show N/A
    row_na = t10_b.iloc[0].copy()
    row_na["ci_low_hp"] = np.nan
    row_na["ci_high_hp"] = np.nan
    assert "95% CI is N/A" in build_player_justification(row_na, "Batter")

    # 6-7: Player Comparison rejects mixed/invalid roles and matches CSV rows
    with pytest.raises(ValueError):
        get_same_role_comparison_df("Mixed", ["Vaibhav Sooryavanshi", "Sunil Narine"], bat_raw, bowl_raw)
    cmp_b = get_same_role_comparison_df("Batter", t10_b["player_name"].head(3).tolist(), bat_raw, bowl_raw)
    assert len(cmp_b) == 3
    assert np.allclose(cmp_b["combined_hp_per100"].values, t10_b["combined_hp_per100"].head(3).values)

    # 8-10: Headless UI test for Overview flow & Player Comparison interaction
    at = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    at.run()
    at.sidebar.selectbox[0].set_value("V5.0 Universal T20 Pressure Engine (Track A)").run()
    assert not at.exception
    md_all = "\n".join(m.value for m in at.markdown)
    assert "WHY THESE PLAYERS ARE TOP 10?" in md_all or any("WHY THESE PLAYERS" in e.label for e in at.expander)
    assert "PLAYER COMPARISON" in md_all

    # Switch comparison role to Bowler and verify update
    cmp_radio = [r for r in at.radio if r.key == "v50_ov_cmp_role"][0]
    cmp_radio.set_value("Bowler").run()
    assert not at.exception
