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
    """Verify dashboard renders V4.2 by default and switches cleanly to V5.0."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=30)
    at.run()
    assert not at.exception
    at.sidebar.selectbox[0].set_value("V5.0 Universal T20 Pressure Engine (Track A)").run()
    assert not at.exception
