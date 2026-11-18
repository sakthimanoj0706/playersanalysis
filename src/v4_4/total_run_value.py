"""Track A: Total-Run Context-Adjusted Value (DeltaRE_total) & Attribution Accounting for V4.4."""
from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from src.v4_4.config import DEFAULT_V44_CONFIG, V44Config
from src.v4_4.score_aware_wp import fit_total_er_model, predict_total_er


def compute_track_a_total_run_value(
    li_res: Dict[str, Any],
    cfg: V44Config = DEFAULT_V44_CONFIG,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute cross-fitted ER_total(B, W) and DeltaRE_total = actual_total_runs + ER_after - ER_before.
    Separately classifies batter runs, bowler-chargeable extras, non-bowler extras, and dismissals.
    """
    cfg.ensure_dirs()
    df = li_res["valid_df"].copy().reset_index(drop=True)

    df["legal_balls_after"] = df["legal_balls_before"] + df["legal_ball_inc"]
    df["balls_rem_after"] = np.maximum(df["sched_balls"] - df["legal_balls_after"], 0.0)
    df["wkts_after"] = np.minimum(df["wkts_before"] + df["wicket_inc"], 10).astype(int)
    df["wkts_rem_after"] = (10 - df["wkts_after"]).astype(int)

    gkf = GroupKFold(n_splits=cfg.n_cv_folds)
    er_before = np.zeros(len(df), dtype=float)
    er_after = np.zeros(len(df), dtype=float)
    par_fac = np.ones(len(df), dtype=float)

    for tr_idx, te_idx in gkf.split(df, groups=df["match_id"]):
        er_st = fit_total_er_model(df.iloc[tr_idx], cfg)
        te_f = df.iloc[te_idx]
        er_b, _, fac_b = predict_total_er(te_f, er_st)

        after_f = te_f[
            ["match_id", "innings", "match_format", "venue_id", "balls_rem_after", "wkts_rem_after"]
        ].rename(columns={"balls_rem_after": "balls_rem_before", "wkts_rem_after": "wkts_rem_before"})
        er_a, _, _ = predict_total_er(after_f, er_st)
        term = (te_f["balls_rem_after"].values <= 0) | (te_f["wkts_rem_after"].values <= 0)
        er_a[term] = 0.0

        er_before[te_idx] = er_b
        er_after[te_idx] = er_a
        par_fac[te_idx] = fac_b

    df["eb_venue_par_factor_oof"] = par_fac
    df["er_total_before"] = er_before
    df["er_total_after"] = er_after

    # Team-level total-run value (batting team perspective; bowling team = -delta_re_total)
    df["delta_re_total"] = df["actual_total_runs"].astype(float) + df["er_total_after"] - df["er_total_before"]
    df["bowling_team_delta_re_total"] = -df["delta_re_total"]

    # Separate extra & dismissal attribution components
    df["bowler_chargeable_extras"] = df["cs_wides"].fillna(0).astype(float) + df["cs_noballs"].fillna(0).astype(float)
    df["non_bowler_extras"] = (
        df["cs_byes"].fillna(0).astype(float)
        + df["cs_legbyes"].fillna(0).astype(float)
        + df["cs_delivery_penalty"].fillna(0).astype(float)
    )
    # Player-attribution target removes non-bowler extras (byes/legbyes/delivery_penalty)
    df["delta_re_player_attrib"] = df["delta_re_total"] - df["non_bowler_extras"]

    # Audit summary by event type
    df["event_class"] = np.where(
        df["is_non_bowler_dismissal"] == True,
        "non_bowler_dismissal",
        np.where(
            df["is_bowler_wicket"] == True,
            "bowler_wicket",
            np.where(
                df["bowler_chargeable_extras"] > 0,
                "bowler_chargeable_extra",
                np.where(df["non_bowler_extras"] > 0, "non_bowler_extra", "normal_bat_delivery"),
            ),
        ),
    )
    audit_df = (
        df.groupby("event_class", as_index=False)
        .agg(
            n_deliveries=("delta_re_total", "size"),
            mean_actual_total_runs=("actual_total_runs", "mean"),
            mean_batter_runs=("batter_runs", "mean"),
            mean_bowler_extras=("bowler_chargeable_extras", "mean"),
            mean_non_bowler_extras=("non_bowler_extras", "mean"),
            mean_delta_re_total=("delta_re_total", "mean"),
            mean_delta_re_player_attrib=("delta_re_player_attrib", "mean"),
        )
        .sort_values("n_deliveries", ascending=False)
    )
    audit_df.to_csv(cfg.output_dir / "V4_4_TOTAL_RUN_VALUE_AUDIT.csv", index=False)

    export_cols = [
        "match_id",
        "innings",
        "event_index_in_innings",
        "overid",
        "match_date",
        "match_format",
        "season",
        "striker_id",
        "striker_name",
        "bowler_id",
        "bowler_name",
        "batter_runs",
        "cs_total_extras",
        "bowler_chargeable_extras",
        "non_bowler_extras",
        "actual_total_runs",
        "legal_ball_inc",
        "wicket_inc",
        "is_bowler_wicket",
        "is_non_bowler_dismissal",
        "wp_inn1_team_oof",
        "raw_expected_wp_swing",
        "leverage_index",
        "er_total_before",
        "er_total_after",
        "delta_re_total",
        "bowling_team_delta_re_total",
        "delta_re_player_attrib",
        "event_class",
    ]
    df[export_cols].to_parquet(cfg.output_dir / "V4_4_TOTAL_RUN_VALUE.parquet", index=False)
    return df, audit_df
