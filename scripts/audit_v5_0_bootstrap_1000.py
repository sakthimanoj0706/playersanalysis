"""Phase 5 Audit: Compare V5.0 Archetype Stability at B=200 vs B=1,000 Bootstrap Repetitions."""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4_3.config import DEFAULT_CONFIG as V43_CFG
from src.v4_3.win_probability import compute_pre_match_elo
from src.v5_0.asymmetric_pressure_rapm import build_asymmetric_blocks, solve_block_ridge
from src.v5_0.config import DEFAULT_V50_CONFIG
from src.v5_0.player_archetypes import classify_player_archetypes
from src.v5_0.pressure_scales import load_track_a_with_pressure_scales


def main() -> None:
    cfg = DEFAULT_V50_CONFIG
    audit_dir = cfg.output_dir / "final_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    df, _ = load_track_a_with_pressure_scales(cfg)
    df = compute_pre_match_elo(df, V43_CFG)
    df["H_global_150"] = (df["LI_global"] >= cfg.li_global_hp_threshold).astype(int)

    blocks = build_asymmetric_blocks(df, "H_global_150")
    fit = solve_block_ridge(blocks, 250.0, 4000.0, cfg.alpha_context, cfg.random_seed)

    m_groups = df.groupby("match_id", sort=False).indices
    idx_lists = [m_groups[k] for k in m_groups]
    n_m = len(idx_lists)
    n_bat, n_bowl = blocks["n_bat"], blocks["n_bowl"]

    n_boot = 1000
    b_m, b_p, b_hp = np.empty((n_boot, n_bat)), np.empty((n_boot, n_bat)), np.empty((n_boot, n_bat))
    w_m, w_p, w_hp = np.empty((n_boot, n_bowl)), np.empty((n_boot, n_bowl)), np.empty((n_boot, n_bowl))

    rng = np.random.default_rng(cfg.random_seed)
    X_m, X_p, X_c, y_all = blocks["X_main"], blocks["X_pressure"], blocks["X_context"], blocks["y"]
    for b in range(n_boot):
        chosen = rng.integers(0, n_m, size=n_m)
        r_idx = np.concatenate([idx_lists[i] for i in chosen])
        sub_b = {"X_main": X_m[r_idx], "X_pressure": X_p[r_idx], "X_context": X_c[r_idx], "y": y_all[r_idx], "n_bat": n_bat, "n_bowl": n_bowl}
        fb = solve_block_ridge(sub_b, 250.0, 4000.0, cfg.alpha_context, cfg.random_seed, tol=1e-4)
        b_m[b], b_p[b], b_hp[b] = fb["bat_main"], fb["bat_pres"], fb["bat_hp"]
        w_m[b], w_p[b], w_hp[b] = fb["bowl_main"], fb["bowl_pres"], fb["bowl_hp"]

    rows = []
    for role, fname, pids, m_eff, p_eff, hp_eff, mb, pb, hpb in [
        ("batter", "V5_0_GLOBAL_BATTER_PRESSURE.csv", blocks["batter_ids"], fit["bat_main"], fit["bat_pres"], fit["bat_hp"], b_m, b_p, b_hp),
        ("bowler", "V5_0_GLOBAL_BOWLER_PRESSURE.csv", blocks["bowler_ids"], fit["bowl_main"], fit["bowl_pres"], fit["bowl_hp"], w_m, w_p, w_hp),
    ]:
        orig = pd.read_csv(cfg.output_dir / fname)
        t = pd.DataFrame(
            {
                "player_id": pids,
                "main_effect_per100": m_eff,
                "pressure_interaction_per100": p_eff,
                "combined_hp_per100": hp_eff,
                "ci_low_main": np.percentile(mb, 2.5, axis=0),
                "ci_high_main": np.percentile(mb, 97.5, axis=0),
                "ci_low_pres": np.percentile(pb, 2.5, axis=0),
                "ci_high_pres": np.percentile(pb, 97.5, axis=0),
                "ci_low_hp": np.percentile(hpb, 2.5, axis=0),
                "ci_high_hp": np.percentile(hpb, 97.5, axis=0),
            }
        ).merge(orig[["player_id", "player_name", "eligible", "archetype"]], on="player_id", how="inner")
        t_new = classify_player_archetypes(t, tol=cfg.clutch_non_inferiority_tol)
        # Note: t has original 'archetype' overwritten by classify_player_archetypes; compare via merge
        comp = orig[orig["eligible"]][["player_id", "player_name", "archetype"]].merge(
            t_new[["player_id", "archetype"]], on="player_id", suffixes=("_b200", "_b1000")
        )
        same = int((comp["archetype_b200"] == comp["archetype_b1000"]).sum())
        rows.append({"role": role, "n_eligible": len(comp), "exact_agreement_b200_vs_b1000": same, "agreement_pct": round(100.0 * same / len(comp), 2)})
        comp[comp["archetype_b200"] != comp["archetype_b1000"]].to_csv(audit_dir / f"archetype_shifts_{role}_b1000.csv", index=False)

    res_df = pd.DataFrame(rows)
    res_df.to_csv(audit_dir / "V5_0_ARCHETYPE_STABILITY_B1000.csv", index=False)
    print(res_df.to_string(index=False))


if __name__ == "__main__":
    main()
