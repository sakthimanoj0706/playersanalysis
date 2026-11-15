"""V4.1 Section 3 — Score Enrichment Coverage & Delivery-to-Scorecard Reconciliation Audit."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd


def run_score_enrichment_audit(
    data_dir: str = "data",
    output_dir: str = "data/outputs/v4_1",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Audit all 837 matches with deliveries (and all 1,667 regular innings) using stable
    (match_id, innings) keys to quantify whether any reliable scorecard enrichment exists.
    Never infers numeric extras from categorical extras1_runs or undocumented extras_2_runs.
    """
    os.makedirs(output_dir, exist_ok=True)
    bbb = pd.read_csv(os.path.join(data_dir, "ball_by_ball_ipl_t20i.csv"), low_memory=False)
    matches = pd.read_csv(os.path.join(data_dir, "matches_ipl_t20i.csv"))

    reg = bbb[bbb["innings"].isin([1, 2])].copy()
    for et in ("wide", "Overstep", "legbyes", "byes", "other", "Penalty"):
        reg[f"cnt_{et}"] = (reg["extras_type"] == et).astype(int)
    reg["min_penalty_extra"] = reg["extras_type"].isin(["wide", "Overstep"]).astype(int)
    reg["min_reconstructed_run"] = reg["runs"].astype(float) + reg["min_penalty_extra"].astype(float)

    inn = reg.groupby(["match_id", "innings"], as_index=False).agg(
        original_batter_runs=("runs", "sum"),
        min_reconstructed_score=("min_reconstructed_run", "sum"),
        legal_balls=("is_wicket", "size"),
        wide_events=("cnt_wide", "sum"),
        overstep_events=("cnt_Overstep", "sum"),
        legbye_events=("cnt_legbyes", "sum"),
        bye_events=("cnt_byes", "sum"),
        other_events=("cnt_other", "sum"),
        penalty_events=("cnt_Penalty", "sum"),
        extras2_nonzero=("extras_2_runs", lambda s: int((pd.to_numeric(s, errors="coerce").fillna(0) != 0).sum())),
    )
    inn["unknown_extra_events"] = (
        inn["legbye_events"] + inn["bye_events"] + inn["other_events"] + inn["penalty_events"]
    )
    inn["any_extra_events"] = inn["wide_events"] + inn["overstep_events"] + inn["unknown_extra_events"]

    m_meta = matches[["match_id", "match_date", "match_format", "season", "revised_target", "result"]].copy()
    m_meta["is_dl"] = m_meta["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True)
    m_meta["stated_run_margin"] = (
        m_meta["result"].fillna("").str.extract(r"by\s+(\d+)\s+run", flags=re.IGNORECASE)[0].astype(float)
    )

    p_inn = inn.pivot(index="match_id", columns="innings")
    match_lvl = pd.DataFrame({"match_id": p_inn.index})
    for col in ("original_batter_runs", "min_reconstructed_score", "unknown_extra_events", "any_extra_events"):
        match_lvl[f"{col}_inn1"] = p_inn[col].get(1, np.nan).values
        match_lvl[f"{col}_inn2"] = p_inn[col].get(2, np.nan).values
    match_lvl = match_lvl.merge(m_meta, on="match_id", how="left")
    match_lvl["min_calc_margin"] = match_lvl["min_reconstructed_score_inn1"] - match_lvl["min_reconstructed_score_inn2"]
    match_lvl["margin_difference"] = match_lvl["min_calc_margin"] - match_lvl["stated_run_margin"]

    non_dls_run = (~match_lvl["is_dl"]) & match_lvl["stated_run_margin"].notna()
    match_lvl["match_validation_status"] = np.where(
        (match_lvl["any_extra_events_inn1"] == 0) & (match_lvl["any_extra_events_inn2"] == 0),
        "VERIFIED_NO_EXTRAS",
        np.where(
            non_dls_run & (match_lvl["margin_difference"] == 0)
            & (match_lvl["unknown_extra_events_inn1"] == 0) & (match_lvl["unknown_extra_events_inn2"] == 0),
            "VERIFIED_EXACT_MARGIN_ZERO_UNKNOWN_EXTRAS",
            np.where(
                non_dls_run & (match_lvl["margin_difference"] == 0),
                "EXACT_MARGIN_BY_CANCELLATION_UNVERIFIED_TOTALS",
                np.where(
                    non_dls_run,
                    "MARGIN_MISMATCH_BLOCKED",
                    "NO_RUN_MARGIN_OR_DLS_UNVERIFIED",
                ),
            ),
        ),
    )

    audit_df = inn.merge(
        match_lvl[[
            "match_id", "match_date", "match_format", "season", "revised_target",
            "result", "is_dl", "stated_run_margin", "min_calc_margin",
            "margin_difference", "match_validation_status",
        ]],
        on="match_id",
        how="left",
    )
    audit_df["scorecard_score"] = np.where(
        (audit_df["innings"] == 2) & audit_df["revised_target"].notna(),
        audit_df["revised_target"] - 1.0,
        np.nan,
    )
    audit_df["scorecard_difference"] = audit_df["min_reconstructed_score"] - audit_df["scorecard_score"]
    audit_df["source"] = "supplied_hackathon_csv_only (no external scorecard keyed by match_id)"
    audit_df["validation_status"] = np.where(
        audit_df["any_extra_events"] == 0,
        "EXACT_ZERO_EXTRAS",
        np.where(
            audit_df["unknown_extra_events"] == 0,
            "MISSING_MULTI_RUN_WIDE_OVERSTEP_AMOUNTS",
            "BLOCKED_UNQUANTIFIED_EXTRAS",
        ),
    )

    out_cols = [
        "match_id", "innings", "match_date", "match_format", "season",
        "original_batter_runs", "min_reconstructed_score", "scorecard_score",
        "scorecard_difference", "stated_run_margin", "min_calc_margin",
        "margin_difference", "wide_events", "overstep_events",
        "legbye_events", "bye_events", "other_events", "penalty_events",
        "extras2_nonzero", "revised_target", "source",
        "match_validation_status", "validation_status",
    ]
    audit_out = audit_df[out_cols].sort_values(["match_id", "innings"]).reset_index(drop=True)
    audit_out.to_csv(os.path.join(output_dir, "V4_1_SCORE_ENRICHMENT_AUDIT.csv"), index=False)

    n_matches = int(len(match_lvl))
    n_non_dls_run = int(non_dls_run.sum())
    n_margin_exact = int((non_dls_run & (match_lvl["margin_difference"] == 0)).sum())
    n_margin_exact_clean = int(
        (non_dls_run & (match_lvl["margin_difference"] == 0)
         & (match_lvl["unknown_extra_events_inn1"] == 0)
         & (match_lvl["unknown_extra_events_inn2"] == 0)).sum()
    )
    n_zero_unknown_both = int(
        ((match_lvl["unknown_extra_events_inn1"] == 0) & (match_lvl["unknown_extra_events_inn2"] == 0)).sum()
    )
    n_zero_any_both = int(
        ((match_lvl["any_extra_events_inn1"] == 0) & (match_lvl["any_extra_events_inn2"] == 0)).sum()
    )

    summary = {
        "scoped_matches_with_deliveries": n_matches,
        "scoped_regular_innings": int(len(audit_out)),
        "external_scorecard_matched_by_stable_id": 0,
        "revised_target_populated_matches": int(m_meta["revised_target"].notna().sum()),
        "matches_zero_all_extras": n_zero_any_both,
        "matches_zero_unknown_extras": n_zero_unknown_both,
        "non_dls_run_margin_matches": n_non_dls_run,
        "non_dls_run_margin_exact": n_margin_exact,
        "non_dls_run_margin_fail": n_non_dls_run - n_margin_exact,
        "non_dls_exact_also_zero_unknown_extras": n_margin_exact_clean,
        "non_dls_exact_accidental_cancellation": n_margin_exact - n_margin_exact_clean,
        "chase_score_reconstruction_blocked": True,
        "verified_score_coverage_pct": round(100.0 * n_zero_any_both / max(n_matches, 1), 3),
    }
    return audit_out, summary
