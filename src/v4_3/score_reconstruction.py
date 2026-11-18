"""Phase 1: Score Reconstruction Audit & Leak-Free Innings-State Builder for V4.3."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.config import BBB_DTYPE_OVERRIDES
from src.ingestion.adapters.rr_data_adapter import RRDataAdapter
from src.v4_3.config import DEFAULT_CONFIG, V43Config


def build_innings_state_and_score_audit(
    cfg: V43Config = DEFAULT_CONFIG,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Separate Super Overs, construct strictly pre-delivery innings state,
    and audit innings-level score reconstruction without fabricating missing extras.
    """
    cfg.ensure_dirs()
    bbb = pd.read_csv(
        cfg.data_dir / "ball_by_ball_ipl_t20i.csv",
        dtype=BBB_DTYPE_OVERRIDES,
        low_memory=False,
    )
    matches = pd.read_csv(cfg.data_dir / "matches_ipl_t20i.csv")

    adapter = RRDataAdapter(quarantine_unknown_extras=True)
    cleaned = adapter.transform_deliveries(bbb)
    reg, so = adapter.separate_cohorts(cleaned)

    m_meta = matches[
        [
            "match_id",
            "match_date",
            "match_format",
            "season",
            "venue_id",
            "venue_country",
            "home_team_id",
            "away_team_id",
            "first_inn_revised_overs",
            "second_inn_revised_overs",
            "revised_target",
            "knock_out",
            "win_team_id",
            "result",
        ]
    ].copy()
    m_meta["is_dl"] = m_meta["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True)
    m_meta["stated_run_margin"] = (
        m_meta["result"].fillna("").str.extract(r"by\s+(\d+)\s+run", flags=re.IGNORECASE)[0].astype(float)
    )

    reg = reg.merge(
        m_meta.drop(columns=["match_format", "season", "match_date", "venue_country"]),
        on="match_id",
        how="left",
    )
    reg["match_date_dt"] = pd.to_datetime(reg["match_date"], errors="coerce")
    season_yr = pd.to_numeric(reg["season"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    reg["year"] = reg["match_date_dt"].dt.year.fillna(season_yr).astype(int)

    reg = reg.sort_values(
        ["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]
    ).reset_index(drop=True)

    # Scheduled balls: revised_overs is stored in balls (30..114) when <=120, or overs if <=20
    rev1 = pd.to_numeric(reg["first_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev2 = pd.to_numeric(reg["second_inn_revised_overs"], errors="coerce").fillna(0.0)
    rev1_balls = np.where(rev1 > 0, np.where(rev1 <= 20.0, rev1 * 6.0, rev1), float(cfg.standard_t20_balls))
    rev2_balls = np.where(rev2 > 0, np.where(rev2 <= 20.0, rev2 * 6.0, rev2), float(cfg.standard_t20_balls))
    reg["sched_balls"] = np.where(reg["innings"] == 1, rev1_balls, rev2_balls)

    # Strictly pre-delivery cumulative state
    g = reg.groupby(["match_id", "innings"], sort=False)
    reg["legal_ball_inc"] = reg["is_legal_ball"].astype(int)
    reg["legal_balls_before"] = (g["legal_ball_inc"].cumsum() - reg["legal_ball_inc"]).astype(int)
    reg["balls_rem_before"] = np.maximum(reg["sched_balls"] - reg["legal_balls_before"], 0.0)

    reg["wicket_inc"] = (reg["is_wicket"] == True).astype(int)
    reg["wkts_before"] = (g["wicket_inc"].cumsum() - reg["wicket_inc"]).clip(0, 9).astype(int)
    reg["wkts_rem_before"] = (10 - reg["wkts_before"]).astype(int)

    # Batter runs (verified) and lower-bound team runs (explicitly labeled as unverified lower bound)
    reg["batter_runs_before"] = (g["batter_runs"].cumsum() - reg["batter_runs"]).astype(float)
    reg["min_penalty_extra"] = reg["extras_category"].isin(["wide", "Overstep"]).astype(float)
    reg["min_delivery_runs_lb"] = reg["batter_runs"].astype(float) + reg["min_penalty_extra"]
    reg["min_team_score_before_lb"] = (g["min_delivery_runs_lb"].cumsum() - reg["min_delivery_runs_lb"]).astype(float)

    # Remaining batter runs from pre-delivery state onward (including current delivery)
    inn_tot_bat = g["batter_runs"].transform("sum").astype(float)
    reg["rem_batter_runs"] = inn_tot_bat - reg["batter_runs_before"]
    reg["rem_batter_runs_after"] = reg["rem_batter_runs"] - reg["batter_runs"].astype(float)

    # Match outcome perspective: ALWAYS first-batting team win indicator where result is decided
    inn1_team = (
        reg[reg["innings"] == 1]
        .groupby("match_id")["batting_team_id"]
        .first()
        .rename("inn1_batting_team_id")
    )
    reg = reg.merge(inn1_team, on="match_id", how="left")
    reg["inn1_team_won"] = np.where(
        reg["win_team_id"].isna() | reg["inn1_batting_team_id"].isna(),
        np.nan,
        (reg["win_team_id"] == reg["inn1_batting_team_id"]).astype(float),
    )
    reg["batting_team_won"] = np.where(
        reg["win_team_id"].isna(),
        np.nan,
        (reg["win_team_id"] == reg["batting_team_id"]).astype(float),
    )

    # Innings-level score reconstruction audit
    for et in ("wide", "Overstep", "legbyes", "byes", "other", "Penalty"):
        reg[f"_cnt_{et}"] = (reg["extras_category"] == et).astype(int)
    reg["_ext2_nz"] = (pd.to_numeric(reg["extras_2_runs"], errors="coerce").fillna(0) != 0).astype(int)

    inn = reg.groupby(["match_id", "innings"], as_index=False).agg(
        delivery_rows=("is_wicket", "size"),
        legal_balls=("legal_ball_inc", "sum"),
        wickets_lost=("wicket_inc", "sum"),
        batter_runs_total=("batter_runs", "sum"),
        min_reconstructed_score=("min_delivery_runs_lb", "sum"),
        wide_events=("_cnt_wide", "sum"),
        overstep_events=("_cnt_Overstep", "sum"),
        legbye_events=("_cnt_legbyes", "sum"),
        bye_events=("_cnt_byes", "sum"),
        other_events=("_cnt_other", "sum"),
        penalty_events=("_cnt_Penalty", "sum"),
        extras2_nonzero=("_ext2_nz", "sum"),
    )
    reg.drop(columns=[f"_cnt_{et}" for et in ("wide", "Overstep", "legbyes", "byes", "other", "Penalty")] + ["_ext2_nz"], inplace=True)

    inn["unknown_extra_events"] = (
        inn["legbye_events"] + inn["bye_events"] + inn["other_events"] + inn["penalty_events"]
    )
    inn["any_extra_events"] = inn["wide_events"] + inn["overstep_events"] + inn["unknown_extra_events"]

    # Match-level margin cross-check
    p_inn = inn.pivot(index="match_id", columns="innings")
    match_lvl = pd.DataFrame({"match_id": p_inn.index})
    for col in ("min_reconstructed_score", "unknown_extra_events", "any_extra_events"):
        match_lvl[f"{col}_inn1"] = p_inn[col].get(1, np.nan).values
        match_lvl[f"{col}_inn2"] = p_inn[col].get(2, np.nan).values
    match_lvl = match_lvl.merge(
        m_meta[["match_id", "match_date", "match_format", "season", "revised_target", "result", "is_dl", "stated_run_margin"]],
        on="match_id",
        how="left",
    )
    match_lvl["min_calc_margin"] = match_lvl["min_reconstructed_score_inn1"] - match_lvl["min_reconstructed_score_inn2"]
    match_lvl["margin_difference"] = match_lvl["min_calc_margin"] - match_lvl["stated_run_margin"]

    non_dls_run = (~match_lvl["is_dl"]) & match_lvl["stated_run_margin"].notna()
    match_lvl["match_validation_status"] = np.where(
        (match_lvl["any_extra_events_inn1"] == 0) & (match_lvl["any_extra_events_inn2"] == 0),
        "VERIFIED_NO_EXTRAS",
        np.where(
            non_dls_run
            & (match_lvl["margin_difference"] == 0)
            & (match_lvl["unknown_extra_events_inn1"] == 0)
            & (match_lvl["unknown_extra_events_inn2"] == 0),
            "MARGIN_MATCH_ZERO_UNKNOWN_EXTRAS",
            np.where(
                non_dls_run & (match_lvl["margin_difference"] == 0),
                "EXACT_MARGIN_BY_CANCELLATION_UNVERIFIED",
                np.where(non_dls_run, "MARGIN_MISMATCH_BLOCKED", "NO_RUN_MARGIN_OR_DLS_UNVERIFIED"),
            ),
        ),
    )

    audit = inn.merge(
        match_lvl[
            [
                "match_id",
                "match_date",
                "match_format",
                "season",
                "revised_target",
                "result",
                "is_dl",
                "stated_run_margin",
                "min_calc_margin",
                "margin_difference",
                "match_validation_status",
            ]
        ],
        on="match_id",
        how="left",
    )

    # Exact total only when ZERO extras events exist; otherwise NaN (never fabricate)
    audit["reconstructed_innings_total"] = np.where(
        audit["any_extra_events"] == 0,
        audit["batter_runs_total"].astype(float),
        np.nan,
    )
    audit["available_reference_total"] = np.where(
        (audit["innings"] == 2) & audit["revised_target"].notna(),
        audit["revised_target"] - 1.0,
        np.nan,
    )
    audit["difference"] = np.where(
        audit["available_reference_total"].notna(),
        audit["min_reconstructed_score"] - audit["available_reference_total"],
        np.nan,
    )
    audit["exact_match_status"] = np.where(
        audit["any_extra_events"] == 0,
        "EXACT_ZERO_EXTRAS",
        np.where(
            audit["available_reference_total"].notna() & (audit["difference"] == 0),
            "REF_TARGET_MINUS_1_MATCHES_LOWER_BOUND",
            np.where(
                audit["available_reference_total"].notna(),
                "REF_MISMATCH",
                "NO_INNINGS_TOTAL_REFERENCE",
            ),
        ),
    )
    audit["reconstruction_method"] = np.where(
        audit["any_extra_events"] == 0,
        "exact_batter_runs_zero_extras",
        "blocked_lower_bound_only (batter_runs + 1*wide_or_overstep)",
    )
    audit["score_verified"] = audit["any_extra_events"] == 0
    audit["confidence_status"] = np.where(
        audit["score_verified"],
        "VERIFIED_EXACT",
        np.where(
            audit["unknown_extra_events"] == 0,
            "BLOCKED_MISSING_MULTI_RUN_WIDE_OVERSTEP",
            "BLOCKED_UNQUANTIFIED_EXTRAS",
        ),
    )
    audit["failure_reason"] = np.where(
        audit["score_verified"],
        "NONE",
        np.where(
            audit["unknown_extra_events"] == 0,
            "multi_run_wides_or_oversteps_unquantified_and_no_scorecard_ref",
            "legbyes_byes_other_penalty_runs_unrecorded_in_source_csv",
        ),
    )

    out_cols = [
        "match_id",
        "innings",
        "match_date",
        "match_format",
        "season",
        "delivery_rows",
        "legal_balls",
        "wickets_lost",
        "batter_runs_total",
        "reconstructed_innings_total",
        "min_reconstructed_score",
        "available_reference_total",
        "difference",
        "exact_match_status",
        "reconstruction_method",
        "confidence_status",
        "score_verified",
        "failure_reason",
        "stated_run_margin",
        "min_calc_margin",
        "margin_difference",
        "match_validation_status",
        "wide_events",
        "overstep_events",
        "legbye_events",
        "bye_events",
        "other_events",
        "penalty_events",
        "unknown_extra_events",
        "any_extra_events",
        "extras2_nonzero",
    ]
    audit_out = audit[out_cols].sort_values(["match_id", "innings"]).reset_index(drop=True)
    audit_out.to_csv(cfg.output_dir / "V4_3_SCORE_RECONSTRUCTION_AUDIT.csv", index=False)

    # Attach score_verified flag to delivery rows
    reg = reg.merge(
        audit_out[["match_id", "innings", "score_verified"]],
        on=["match_id", "innings"],
        how="left",
    )

    n_inn = int(len(audit_out))
    n_verified_inn = int(audit_out["score_verified"].sum())
    n_verified_matches = int(
        (match_lvl["match_validation_status"] == "VERIFIED_NO_EXTRAS").sum()
    )
    n_non_dls_run = int(non_dls_run.sum())
    n_margin_exact = int((non_dls_run & (match_lvl["margin_difference"] == 0)).sum())

    summary = {
        "regular_innings_total": n_inn,
        "verified_exact_innings": n_verified_inn,
        "verified_exact_matches": n_verified_matches,
        "blocked_innings": n_inn - n_verified_inn,
        "non_dls_run_margin_matches": n_non_dls_run,
        "non_dls_run_margin_exact": n_margin_exact,
        "non_dls_run_margin_fail": n_non_dls_run - n_margin_exact,
        "score_dependent_wp_blocked": n_verified_matches < 50,
    }
    (cfg.artifacts_dir / "phase1_score_reconstruction_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return reg, so, audit_out, summary
