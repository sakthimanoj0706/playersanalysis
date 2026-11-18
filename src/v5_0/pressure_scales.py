"""Phase 2: Two Independent Pressure Scales (LI_global & LI_innings) for V5.0."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from src.v5_0.config import DEFAULT_V50_CONFIG, V50Config


def load_track_a_with_pressure_scales(cfg: V50Config = DEFAULT_V50_CONFIG) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load verified Track A deliveries from V4.4 and compute:
      - LI_global  = RawL_t / Mean(RawL_all_valid_reference)
      - LI_innings = RawL_t / Mean(RawL_same_innings_reference)
    Also dynamically recalculates Phase 0 counts without hardcoding.
    """
    cfg.ensure_dirs()
    trv = pd.read_parquet(cfg.v44_dir / "V4_4_TOTAL_RUN_VALUE.parquet")
    enr = pd.read_parquet(cfg.v44_dir / "artifacts" / "v4_4_regular_deliveries_enriched.parquet")
    v43 = pd.read_parquet(cfg.v43_dir / "V4_3_DELIVERY_VALUE_BATTER.parquet")
    rec = pd.read_csv(cfg.v44_dir / "V4_4_EXTRAS_RECONCILIATION.csv")

    # Merge pre-delivery state & team/batting_order metadata onto Track A deliveries
    meta_cols = [
        "match_id",
        "innings",
        "event_index_in_innings",
        "batting_team_id",
        "bowling_team_id",
        "innings_phase",
        "is_ball_faced",
        "batting_order",
        "dismissed_player_id",
    ]
    df = trv.merge(enr[meta_cols], on=["match_id", "innings", "event_index_in_innings"], how="left")

    # Reconstruct pre-delivery balls/wickets/score/elo from V4.4 verified state
    df = df.sort_values(["match_id", "innings", "event_index_in_innings"]).reset_index(drop=True)
    matches = pd.read_csv(cfg.data_dir / "matches_ipl_t20i.csv")
    df = df.merge(
        matches[["match_id", "venue_id", "home_team_id", "away_team_id", "first_inn_revised_overs", "second_inn_revised_overs", "win_team_id"]],
        on="match_id",
        how="left",
    )
    df["match_date_dt"] = pd.to_datetime(df["match_date"], errors="coerce")
    season_yr = pd.to_numeric(df["season"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    df["year"] = df["match_date_dt"].dt.year.fillna(season_yr).astype(int)

    rev1 = pd.to_numeric(df["first_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev2 = pd.to_numeric(df["second_inn_revised_overs"], errors="coerce").fillna(0.0)
    df["sched_balls"] = np.where(
        df["innings"] == 1,
        np.where(rev1 > 0, np.where(rev1 <= 20.0, rev1 * 6.0, rev1), 120.0),
        np.where(rev2 > 0, np.where(rev2 <= 20.0, rev2 * 6.0, rev2), 120.0),
    )
    g = df.groupby(["match_id", "innings"], sort=False)
    df["legal_balls_before"] = (g["legal_ball_inc"].cumsum() - df["legal_ball_inc"]).astype(int)
    df["balls_rem_before"] = np.maximum(df["sched_balls"] - df["legal_balls_before"], 0.0)
    df["wkts_before"] = (g["wicket_inc"].cumsum() - df["wicket_inc"]).clip(0, 9).astype(int)
    df["wkts_rem_before"] = (10 - df["wkts_before"]).astype(int)
    df["actual_score_before"] = (g["actual_total_runs"].cumsum() - df["actual_total_runs"]).astype(float)
    inn1_team = df[df["innings"] == 1].groupby("match_id")["batting_team_id"].first().rename("inn1_batting_team_id")
    df = df.merge(inn1_team, on="match_id", how="left")

    # Realized WP swing (for threshold diagnostics)
    df["wp_after_actual"] = g["wp_inn1_team_oof"].shift(-1)
    df["realized_wp_swing"] = np.abs(df["wp_after_actual"] - df["wp_inn1_team_oof"])

    # Two independent pressure scales
    raw_l = df["raw_expected_wp_swing"].values.astype(float)
    mean_raw_global = float(np.mean(raw_l))
    df["LI_global"] = raw_l / max(mean_raw_global, 1e-9)

    inn_means = df.groupby("innings")["raw_expected_wp_swing"].transform("mean").values.astype(float)
    df["LI_innings"] = raw_l / np.maximum(inn_means, 1e-9)
    df["reference_population_version"] = "V5_0_CRICSHEET_VERIFIED_IPL_T20I_2022_2026"

    # Recalculated Phase 0 counts
    counts = {
        "track_a_verified_deliveries": int(len(df)),
        "track_a_verified_matches": int(df["match_id"].nunique()),
        "track_b_regular_deliveries": int(len(v43)),
        "track_b_regular_matches": int(v43["match_id"].nunique()),
        "verified_innings": int(rec["score_verified"].sum()),
        "blocked_innings": int((~rec["score_verified"]).sum()),
        "mean_raw_global": mean_raw_global,
        "mean_raw_inn1": float(df.loc[df["innings"] == 1, "raw_expected_wp_swing"].mean()),
        "mean_raw_inn2": float(df.loc[df["innings"] == 2, "raw_expected_wp_swing"].mean()),
    }

    # Export innings-level pressure scale summary
    sum_rows: List[Dict[str, Any]] = []
    for inn in (1, 2):
        sub = df[df["innings"] == inn]
        hp_g = sub["LI_global"] >= cfg.li_global_hp_threshold
        hp_i = sub["LI_innings"] >= cfg.li_global_hp_threshold
        sum_rows.append(
            {
                "innings": inn,
                "total_deliveries": int(len(sub)),
                "legal_deliveries": int(sub["legal_ball_inc"].sum()),
                "mean_raw_leverage": round(float(sub["raw_expected_wp_swing"].mean()), 6),
                "hp_count_li_global_150": int(hp_g.sum()),
                "hp_rate_li_global_150": round(float(hp_g.mean()), 4),
                "hp_count_li_innings_150": int(hp_i.sum()),
                "hp_rate_li_innings_150": round(float(hp_i.mean()), 4),
                "wicket_rate_all": round(float(sub["wicket_inc"].mean()), 4),
                "wicket_rate_hp_global": round(float(sub.loc[hp_g, "wicket_inc"].mean()), 4) if hp_g.sum() > 0 else np.nan,
                "realized_wp_swing_mean": round(float(sub["realized_wp_swing"].mean()), 5),
                "share_powerplay": round(float((sub["innings_phase"] == "powerplay").mean()), 4),
                "share_middle": round(float((sub["innings_phase"] == "middle").mean()), 4),
                "share_death": round(float((sub["innings_phase"] == "death").mean()), 4),
                "share_t20_ipl": round(float((sub["match_format"] == "T20").mean()), 4),
                "share_t20i": round(float((sub["match_format"] == "T20I").mean()), 4),
            }
        )
    pd.DataFrame(sum_rows).to_csv(cfg.output_dir / "V5_0_PRESSURE_SCALES_SUMMARY.csv", index=False)

    # Export threshold sensitivity on LI_global and LI_innings
    th_rows: List[Dict[str, Any]] = []
    for scale_col in ("LI_global", "LI_innings"):
        p75 = float(df[scale_col].quantile(0.75))
        for label, mask in [
            (">= 1.00", df[scale_col] >= 1.00),
            (">= 1.25", df[scale_col] >= 1.25),
            (">= 1.50", df[scale_col] >= 1.50),
            (">= 1.75", df[scale_col] >= 1.75),
            (">= 2.00", df[scale_col] >= 2.00),
            (f"Top 25% (>= {p75:.3f})", df[scale_col] >= p75),
        ]:
            sub_t = df[mask]
            th_rows.append(
                {
                    "scale": scale_col,
                    "threshold": label,
                    "n_deliveries": int(len(sub_t)),
                    "coverage_pct": round(100.0 * len(sub_t) / len(df), 2),
                    "inn1_share_pct": round(100.0 * (sub_t["innings"] == 1).mean(), 2),
                    "inn2_share_pct": round(100.0 * (sub_t["innings"] == 2).mean(), 2),
                    "wicket_rate_pct": round(100.0 * sub_t["wicket_inc"].mean(), 3),
                    "mean_realized_wp_swing": round(float(sub_t["realized_wp_swing"].mean()), 5),
                }
            )
    pd.DataFrame(th_rows).to_csv(cfg.output_dir / "V5_0_LI_THRESHOLDS.csv", index=False)

    return df, counts
