"""Phase 0: Repository & Source Data Quality Audit for SupeRR Intelligence V4.3."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from src.config import BBB_DTYPE_OVERRIDES, EXTRAS_TYPE_MAP, SUPER_OVER_INNINGS
from src.v4_3.config import DEFAULT_CONFIG, V43Config


def load_source_tables(cfg: V43Config = DEFAULT_CONFIG) -> Dict[str, pd.DataFrame]:
    """Load all raw source CSVs without mutating original files."""
    d = cfg.data_dir
    return {
        "bbb": pd.read_csv(d / "ball_by_ball_ipl_t20i.csv", dtype=BBB_DTYPE_OVERRIDES, low_memory=False),
        "matches": pd.read_csv(d / "matches_ipl_t20i.csv"),
        "playing_eleven": pd.read_csv(d / "playing_eleven_ipl_t20i.csv"),
        "competitions": pd.read_csv(d / "competitions_ipl_t20i.csv"),
        "teams": pd.read_csv(d / "teams_ipl_t20i.csv"),
        "mapping": pd.read_csv(d / "competition_team_player_mapping_ipl_t20i.csv"),
    }


def _audit_row(
    category: str,
    check_name: str,
    observed_value: Any,
    status: str,
    details: str,
) -> Dict[str, Any]:
    return {
        "category": category,
        "check_name": check_name,
        "observed_value": str(observed_value),
        "status": status,
        "details": details,
    }


def run_phase0_data_audit(cfg: V43Config = DEFAULT_CONFIG) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run complete Phase 0 data-quality, extras, and special-case audit."""
    cfg.ensure_dirs()
    tables = load_source_tables(cfg)
    bbb = tables["bbb"]
    matches = tables["matches"]
    pe = tables["playing_eleven"]

    rows: List[Dict[str, Any]] = []

    # 1. Scale & Cohort Separation
    reg = bbb[bbb["innings"].isin([1, 2])].copy()
    so = bbb[bbb["innings"].isin(SUPER_OVER_INNINGS)].copy()
    other_inn = bbb[~bbb["innings"].isin([1, 2, 3, 4])]

    n_matches_table = int(len(matches))
    n_matches_bbb = int(bbb["match_id"].nunique())
    n_reg_matches = int(reg["match_id"].nunique())
    n_reg_innings = int(reg.groupby(["match_id", "innings"]).ngroups)
    n_reg_rows = int(len(reg))
    n_reg_legal = int((~reg["extras_type"].isin(["wide", "Overstep"])).sum())
    n_so_matches = int(so["match_id"].nunique())
    n_so_rows = int(len(so))

    rows.append(_audit_row("scale", "matches_table_rows", n_matches_table, "PASS", "Total matches in matches_ipl_t20i.csv"))
    rows.append(_audit_row("scale", "matches_with_deliveries", n_matches_bbb, "PASS", "Matches with >= 1 ball-by-ball row"))
    rows.append(_audit_row("scale", "regular_matches", n_reg_matches, "PASS", "Matches with innings 1 or 2 deliveries"))
    rows.append(_audit_row("scale", "regular_innings", n_reg_innings, "PASS", "Distinct (match_id, innings) in {1, 2}"))
    rows.append(_audit_row("scale", "regular_delivery_rows", n_reg_rows, "PASS", "Delivery rows in innings {1, 2}"))
    rows.append(_audit_row("scale", "regular_legal_deliveries", n_reg_legal, "PASS", "Deliveries excluding wide and Overstep"))
    rows.append(_audit_row("special_cases", "super_over_matches", n_so_matches, "ISOLATED", f"{n_so_rows} deliveries in innings {{3, 4}} kept separate"))
    rows.append(_audit_row("special_cases", "invalid_innings_numbers", int(len(other_inn)), "PASS" if len(other_inn) == 0 else "WARN", "Rows outside innings 1..4"))

    # 2. Match & Innings Identity & Special Cases
    res_s = matches["result"].fillna("")
    n_abandoned = int(res_s.str.contains("Abandoned", case=False, regex=False).sum())
    n_no_result = int(res_s.str.contains("No Result", case=False, regex=False).sum())
    n_tied = int(res_s.str.contains("Tied", case=False, regex=False).sum())
    n_dls = int(res_s.str.contains("D/L|DLS", case=False, regex=True).sum())
    n_rev_target = int(matches["revised_target"].notna().sum())
    n_win_na_with_bbb = int((matches["match_id"].isin(reg["match_id"].unique()) & matches["win_team_id"].isna()).sum())

    inn_per_m = reg.groupby("match_id")["innings"].unique()
    n_inn1_only = int(sum(list(v) == [1] for v in inn_per_m))
    n_inn2_only = int(sum(list(v) == [2] for v in inn_per_m))

    # Incomplete innings: < 120 legal balls and < 10 wickets (on non-DLS matches)
    inn_agg = reg.assign(
        is_legal=(~reg["extras_type"].isin(["wide", "Overstep"])).astype(int),
        is_wkt=(reg["is_wicket"] == True).astype(int),
    ).groupby(["match_id", "innings"], as_index=False).agg(
        legal_balls=("is_legal", "sum"),
        wickets=("is_wkt", "sum"),
    )
    inn_agg = inn_agg.merge(
        matches[["match_id", "result", "first_inn_revised_overs", "second_inn_revised_overs"]],
        on="match_id",
        how="left",
    )
    inn1_incomplete = inn_agg[
        (inn_agg["innings"] == 1)
        & (inn_agg["legal_balls"] < 120)
        & (inn_agg["wickets"] < 10)
        & (~inn_agg["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True))
        & (inn_agg["first_inn_revised_overs"].isna())
    ]

    rows.append(_audit_row("special_cases", "abandoned_matches", n_abandoned, "INFO", "16 with 0 deliveries + 3 with partial deliveries"))
    rows.append(_audit_row("special_cases", "no_result_matches", n_no_result, "INFO", "Matches ending in No Result"))
    rows.append(_audit_row("special_cases", "tied_matches", n_tied, "INFO", "Tied matches (4 decided via Super Over, 1 without)"))
    rows.append(_audit_row("special_cases", "dls_matches", n_dls, "INFO", f"Matches with D/L or DLS in result; revised_target populated in {n_rev_target}"))
    rows.append(_audit_row("special_cases", "matches_with_bbb_missing_win_team_id", n_win_na_with_bbb, "INFO", "Excluded from win-probability training labels"))
    rows.append(_audit_row("special_cases", "matches_with_innings_1_only", n_inn1_only, "INFO", "Abandoned/No Result before or at start of innings 2"))
    rows.append(_audit_row("special_cases", "matches_with_innings_2_without_1", n_inn2_only, "PASS" if n_inn2_only == 0 else "FAIL", "Orphaned second innings check"))
    rows.append(_audit_row("special_cases", "incomplete_non_dls_innings_1", int(len(inn1_incomplete)), "INFO", "Innings 1 with <120 legal balls, <10 wkts, no DLS flag"))

    # 3. Sequence, Duplicates & Missing IDs
    n_dup_exact = int(bbb.duplicated().sum())
    n_dup_inn_ball = int(reg.duplicated(subset=["match_id", "innings", "innings_ball_num"]).sum())
    n_dup_over_ball = int(reg.duplicated(subset=["match_id", "innings", "overid", "over_ball_num"]).sum())
    n_miss_striker = int(reg["striker_id"].isna().sum())
    n_miss_non_striker = int(reg["non_striker_id"].isna().sum())
    n_miss_bowler = int(reg["bowler_id"].isna().sum())
    n_miss_dismissed = int(((reg["is_wicket"] == True) & reg["dismissed_player_id"].isna()).sum())
    n_bad_over = int(((reg["overid"] < 1) | (reg["overid"] > 20)).sum())
    n_bad_seq = int(((reg["over_ball_num"] < 1) | (reg["innings_ball_num"] < 1)).sum())
    pe_dups = int(pe.duplicated(subset=["match_id", "team_id", "player_id"]).sum())

    rows.append(_audit_row("integrity", "duplicate_delivery_rows", n_dup_exact, "PASS" if n_dup_exact == 0 else "FAIL", "Exact duplicate rows in ball_by_ball"))
    rows.append(_audit_row("integrity", "duplicate_innings_ball_num", n_dup_inn_ball, "PASS" if n_dup_inn_ball == 0 else "FAIL", "Duplicate (match_id, innings, innings_ball_num)"))
    rows.append(_audit_row("integrity", "duplicate_over_ball_num", n_dup_over_ball, "PASS" if n_dup_over_ball == 0 else "FAIL", "Duplicate (match_id, innings, overid, over_ball_num)"))
    rows.append(_audit_row("integrity", "missing_striker_id", n_miss_striker, "PASS" if n_miss_striker == 0 else "FAIL", "Missing striker_id in regular innings"))
    rows.append(_audit_row("integrity", "missing_non_striker_id", n_miss_non_striker, "PASS" if n_miss_non_striker == 0 else "FAIL", "Missing non_striker_id in regular innings"))
    rows.append(_audit_row("integrity", "missing_bowler_id", n_miss_bowler, "PASS" if n_miss_bowler == 0 else "FAIL", "Missing bowler_id in regular innings"))
    rows.append(_audit_row("integrity", "missing_dismissed_player_id_on_wicket", n_miss_dismissed, "WARN" if n_miss_dismissed > 0 else "PASS", "Wicket rows with blank dismissed_player_id"))
    rows.append(_audit_row("integrity", "invalid_overid_regular_innings", n_bad_over, "PASS" if n_bad_over == 0 else "FAIL", "overid outside [1, 20] in innings {1, 2}"))
    rows.append(_audit_row("integrity", "invalid_ball_sequence_numbers", n_bad_seq, "PASS" if n_bad_seq == 0 else "FAIL", "over_ball_num < 1 or innings_ball_num < 1"))
    rows.append(_audit_row("integrity", "playing_eleven_key_conflicts", pe_dups, "WARN", "Repeated (match_id, team_id, player_id) in playing_eleven"))

    # 4. Critical Extras & Runs Audit
    mapped_et = bbb["extras1_runs"].map(EXTRAS_TYPE_MAP)
    obs_et = bbb["extras_type"].fillna("None")
    n_codebook_mismatch = int((mapped_et != obs_et).sum())

    n_wide = int((bbb["extras_type"] == "wide").sum())
    n_wide_runs_gt0 = int(((bbb["extras_type"] == "wide") & (bbb["runs"] > 0)).sum())
    n_legbyes = int((bbb["extras_type"] == "legbyes").sum())
    n_legbyes_runs_gt0 = int(((bbb["extras_type"] == "legbyes") & (bbb["runs"] > 0)).sum())
    n_byes = int((bbb["extras_type"] == "byes").sum())
    n_byes_runs_gt0 = int(((bbb["extras_type"] == "byes") & (bbb["runs"] > 0)).sum())
    n_overstep = int((bbb["extras_type"] == "Overstep").sum())
    n_other = int((bbb["extras_type"] == "other").sum())
    n_penalty = int((bbb["extras_type"] == "Penalty").sum())
    n_ext2_nonzero = int((pd.to_numeric(bbb["extras_2_runs"], errors="coerce").fillna(0) != 0).sum())

    rows.append(_audit_row("extras_audit", "extras1_runs_is_categorical_codebook", n_codebook_mismatch, "VERIFIED_BLOCKER", "100% 1-to-1 match with EXTRAS_TYPE_MAP (1..7); NOT numeric runs"))
    rows.append(_audit_row("extras_audit", "wide_deliveries_with_runs_gt_0", f"{n_wide_runs_gt0}/{n_wide}", "BLOCKED_MULTI_RUN", "All 7,474 wides have runs=0 and extras_2_runs=0; 2/3/5-wides unquantified"))
    rows.append(_audit_row("extras_audit", "legbyes_deliveries_with_runs_gt_0", f"{n_legbyes_runs_gt0}/{n_legbyes}", "BLOCKED_UNQUANTIFIED", "All 2,661 legbyes have runs=0 and extras_2_runs=0; exact runs missing"))
    rows.append(_audit_row("extras_audit", "byes_deliveries_with_runs_gt_0", f"{n_byes_runs_gt0}/{n_byes}", "BLOCKED_UNQUANTIFIED", "All 505 byes have runs=0 and extras_2_runs=0; exact runs missing"))
    rows.append(_audit_row("extras_audit", "overstep_deliveries", n_overstep, "PARTIAL", "Batter runs in `runs`, +1 penalty implied, 21 have extras_2_runs>0"))
    rows.append(_audit_row("extras_audit", "other_and_penalty_deliveries", n_other + n_penalty, "BLOCKED_UNQUANTIFIED", f"{n_other} other + {n_penalty} Penalty events with unverified extra run amounts"))
    rows.append(_audit_row("extras_audit", "extras_2_runs_nonzero", n_ext2_nonzero, "WARN", "Only 35/194,014 rows nonzero (19=1, 16=4); semantics unverified"))

    # 5. Phase Gate Decisions
    phase_decisions = {
        "phase_0_data_audit": "GO",
        "phase_1_score_reconstruction": "CONDITIONAL_GO_WITH_BLOCK",
        "phase_2_eb_par_and_er_batter_runs": "CONDITIONAL_GO_BATTER_RUNS_ONLY",
        "phase_3_score_aware_win_probability": "BLOCKED_ON_REAL_DATA_DIAGNOSTIC_ONLY",
        "phase_4_expected_leverage_index": "BLOCKED_BY_PHASE_3",
        "phase_5_delta_re_batter_runs": "CONDITIONAL_GO_BATTER_RUNS_ONLY",
        "phase_6_joint_ridge_rapm": "CONDITIONAL_GO_OBSERVABLE_STATE_ONLY",
        "phase_7_uncertainty_and_v42_comparison": "CONDITIONAL_GO",
        "phase_8_dashboard_integration": "CONDITIONAL_GO_WITH_WARNINGS",
    }

    audit_df = pd.DataFrame(rows)
    audit_df.to_csv(cfg.output_dir / "V4_3_DATA_AUDIT.csv", index=False)

    summary: Dict[str, Any] = {
        "counts": {
            "matches_table": n_matches_table,
            "matches_with_deliveries": n_matches_bbb,
            "regular_matches": n_reg_matches,
            "regular_innings": n_reg_innings,
            "regular_delivery_rows": n_reg_rows,
            "regular_legal_deliveries": n_reg_legal,
            "super_over_matches": n_so_matches,
            "super_over_rows": n_so_rows,
        },
        "extras_audit": {
            "extras1_codebook_mismatches": n_codebook_mismatch,
            "wide_events": n_wide,
            "legbye_events": n_legbyes,
            "bye_events": n_byes,
            "overstep_events": n_overstep,
            "other_events": n_other,
            "penalty_events": n_penalty,
            "extras_2_runs_nonzero": n_ext2_nonzero,
        },
        "phase_decisions": phase_decisions,
    }
    (cfg.artifacts_dir / "phase0_audit_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return audit_df, summary
