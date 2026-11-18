"""Run SupeRR Intelligence V4.3 Phases 3.5, 5, 6, 7 and Task 5 Scorecard Diagnostic."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.v4_3.config import DEFAULT_CONFIG
from src.v4_3.delta_re_batter import compute_phase5_delta_re_batter
from src.v4_3.joint_rapm import run_phase6_joint_rapm
from src.v4_3.score_reconstruction import build_innings_state_and_score_audit
from src.v4_3.scorecard_diagnostic import run_scorecard_recovery_diagnostic
from src.v4_3.uncertainty_and_comparison import run_phase7_uncertainty_and_comparison
from src.v4_3.wp_evaluation_audit import run_phase3_5_evaluation_audit


def main() -> None:
    cfg = DEFAULT_CONFIG
    cfg.ensure_dirs()

    # Save reproducibility config
    cfg_dict = {
        "random_seed": cfg.random_seed,
        "n_cv_folds": cfg.n_cv_folds,
        "oot_cutoff_year": cfg.oot_cutoff_year,
        "standard_t20_balls": cfg.standard_t20_balls,
        "team_elo_base": cfg.team_elo_base,
        "team_elo_k": cfg.team_elo_k,
    }
    (cfg.artifacts_dir / "v4_3_reproducibility_config.json").write_text(
        json.dumps(cfg_dict, indent=2), encoding="utf-8"
    )

    print("=== LOADING PHASE 1 STATE (PRESERVING PHASE 0-3 OUTPUTS) ===")
    reg, _, sr_audit, _ = build_innings_state_and_score_audit(cfg)

    print("\n=== TASK 1: PHASE 3.5 WP EVALUATION AUDIT ===")
    wp_audit, wp_ckpt, _ = run_phase3_5_evaluation_audit(reg, cfg, n_boot=300)
    print(wp_audit.to_string(index=False))

    print("\n=== TASK 2: PHASE 5 BATTER-RUN EXPECTED VALUE (DeltaRE_batter) ===")
    df_p5, p5_val, p5_audit = compute_phase5_delta_re_batter(reg, cfg, n_boot=300)
    print(p5_val.to_string(index=False))

    print("\n=== TASK 3: PHASE 6 EXPERIMENTAL JOINT BATTER-BOWLER RIDGE RAPM ===")
    bat_df, bowl_df, tune_df, rapm_meta = run_phase6_joint_rapm(df_p5, cfg)
    print(f"Optimal alpha={rapm_meta['best_alpha']} | n_bat={rapm_meta['n_batters']} | n_bowl={rapm_meta['n_bowlers']}")
    print("Alpha tuning:\n", tune_df.to_string(index=False))

    print("\n=== TASK 4: PHASE 7 UNCERTAINTY & V4.2 COMPARISON ===")
    p7 = run_phase7_uncertainty_and_comparison(bat_df, bowl_df, rapm_meta, cfg, n_boot=200, n_splits=10)
    print("Ranking stability:\n", p7["stab_df"].to_string(index=False))
    print("\nV4.2 vs V4.3 Comparison:\n", p7["comp_df"].to_string(index=False))

    print("\n=== TASK 5: SCORECARD RECOVERY DIAGNOSTIC ===")
    _, sc_sum = run_scorecard_recovery_diagnostic(sr_audit, cfg)
    print("Scorecard Recovery Summary:", sc_sum)


if __name__ == "__main__":
    main()
