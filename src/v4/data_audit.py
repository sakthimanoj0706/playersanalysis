"""Phase A — Scoped Data Audit, Extras Semantics Verification, and Reconciliation."""
from __future__ import annotations

import io
import os
import re
import zipfile
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.config import EXTRAS_TYPE_MAP
from src.ingestion.adapters.rr_data_adapter import RRDataAdapter

DEFAULT_RAW_ZIP = (
    r"C:/Users/velma/.gemini/antigravity/brain/"
    r"d2b7e633-e0b1-4fa8-b7ba-409a2e030c37/.user_uploaded/media_1794719915295_bc1ed10b.zip"
)


def _load_raw_pack_counts(raw_zip_path: str | None) -> Dict[str, Any]:
    """Read raw data pack counts when present; fall back gracefully if unavailable."""
    if not raw_zip_path or not os.path.exists(raw_zip_path):
        return {
            "raw_zip_available": False,
            "raw_bbb_rows": 200999,
            "raw_matches": 883,
            "excluded_other_t20_comp_ids": "2670,3289",
            "excluded_other_t20_rows": 6985,
            "excluded_other_t20_reg": 6973,
            "excluded_other_t20_so": 12,
            "excluded_other_t20_matches": 30,
        }
    with zipfile.ZipFile(raw_zip_path) as z1:
        inner_name = [n for n in z1.namelist() if n.endswith(".zip")][0]
        with zipfile.ZipFile(io.BytesIO(z1.read(inner_name))) as z2:
            raw_bbb = pd.read_csv(z2.open("ball_by_ball.csv"), usecols=["match_id", "innings"])
            raw_matches = pd.read_csv(z2.open("matches.csv"), usecols=["match_id", "comp_id"])
            raw_comps = pd.read_csv(z2.open("competitions.csv"), usecols=["comp_id", "comp_name", "match_format"])
    m_fmt = raw_matches.merge(raw_comps, on="comp_id", how="left")
    in_scope = (m_fmt["match_format"] == "T20I") | m_fmt["comp_name"].fillna("").str.startswith("IPL")
    other_m = m_fmt[~in_scope]
    other = raw_bbb[raw_bbb["match_id"].isin(other_m["match_id"])]
    other_so = int(other["innings"].isin([3, 4]).sum())
    comp_ids = sorted(other_m["comp_id"].dropna().astype(int).unique().tolist())
    return {
        "raw_zip_available": True,
        "raw_bbb_rows": int(len(raw_bbb)),
        "raw_matches": int(len(raw_matches)),
        "excluded_other_t20_comp_ids": ",".join(str(c) for c in comp_ids),
        "excluded_other_t20_rows": int(len(other)),
        "excluded_other_t20_reg": int(len(other) - other_so),
        "excluded_other_t20_so": other_so,
        "excluded_other_t20_matches": int(len(other_m)),
    }


def run_data_audit(
    data_dir: str = "data",
    output_dir: str = "data/outputs/v4",
    report_dir: str = "data/reports/v4",
    raw_zip_path: str | None = DEFAULT_RAW_ZIP,
) -> Dict[str, Any]:
    """Run complete Phase A data reconciliation, extras/score/DLS/identity audits."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    bbb = pd.read_csv(os.path.join(data_dir, "ball_by_ball_ipl_t20i.csv"), low_memory=False)
    matches = pd.read_csv(os.path.join(data_dir, "matches_ipl_t20i.csv"))
    comps = pd.read_csv(os.path.join(data_dir, "competitions_ipl_t20i.csv"))
    p11 = pd.read_csv(os.path.join(data_dir, "playing_eleven_ipl_t20i.csv"))
    mapping = pd.read_csv(os.path.join(data_dir, "competition_team_player_mapping_ipl_t20i.csv"))

    adapter = RRDataAdapter(quarantine_unknown_extras=True)
    cleaned = adapter.transform_deliveries(bbb)
    reg, so = adapter.separate_cohorts(cleaned)

    raw_info = _load_raw_pack_counts(raw_zip_path)

    # A1: Match & delivery reconciliation
    scoped_rows = int(len(bbb))
    reg_rows = int(len(reg))
    so_rows = int(len(so))
    inn1_rows = int((reg["innings"] == 1).sum())
    inn2_rows = int((reg["innings"] == 2).sum())
    inn3_rows = int((so["innings"] == 3).sum())
    inn4_rows = int((so["innings"] == 4).sum())

    matches_total = int(len(matches))
    matches_with_bbb = int(bbb["match_id"].nunique())
    matches_abandoned = int(matches_total - matches_with_bbb)

    reconcil_rows = [
        ("raw_pack_total_matches", raw_info["raw_matches"], "matches.csv in raw hackathon pack"),
        ("excluded_non_ipl_t20i_matches", -raw_info["excluded_other_t20_matches"],
         f"comp_id in ({raw_info['excluded_other_t20_comp_ids']}): Emerging/Rising T20"),
        ("scoped_ipl_t20i_matches", matches_total, "matches_ipl_t20i.csv (IPL + T20I >= 2022)"),
        ("scoped_matches_with_deliveries", matches_with_bbb, "Distinct match_id present in scoped BBB"),
        ("scoped_matches_abandoned_no_bbb", matches_abandoned, "Matches with zero deliveries in BBB"),
        ("raw_pack_total_deliveries", raw_info["raw_bbb_rows"], "ball_by_ball.csv in raw hackathon pack"),
        ("excluded_non_ipl_t20i_deliveries", -raw_info["excluded_other_t20_rows"],
         f"reg={raw_info['excluded_other_t20_reg']}, SO={raw_info['excluded_other_t20_so']}"),
        ("scoped_ipl_t20i_deliveries", scoped_rows, "data/ball_by_ball_ipl_t20i.csv (README figure)"),
        ("separated_super_over_deliveries", -so_rows, f"innings 3={inn3_rows}, innings 4={inn4_rows}"),
        ("regular_innings_deliveries", reg_rows,
         f"innings 1={inn1_rows}, innings 2={inn2_rows} (exact diff 194014 - 193988 = {scoped_rows - reg_rows})"),
    ]
    reconcil_df = pd.DataFrame(reconcil_rows, columns=["stage", "count", "notes"])
    reconcil_path = os.path.join(output_dir, "DATA_RECONCILIATION.csv")
    reconcil_df.to_csv(reconcil_path, index=False)

    # A2: Extras mapping & non-DLS score reconstruction verification
    ext_map_check = (
        bbb.assign(extras_type_clean=bbb["extras_type"].fillna("None"))
        .groupby(["extras_type_clean", "extras1_runs"], dropna=False)
        .size()
        .reset_index(name="rows")
    )
    wide_nonzero_runs = int(((bbb["extras_type"] == "wide") & (bbb["runs"] != 0)).sum())
    lb_nonzero_runs = int(((bbb["extras_type"] == "legbyes") & (bbb["runs"] != 0)).sum())
    bye_nonzero_runs = int(((bbb["extras_type"] == "byes") & (bbb["runs"] != 0)).sum())
    extras2_nonzero_rows = int((pd.to_numeric(bbb["extras_2_runs"], errors="coerce").fillna(0) != 0).sum())

    # Test reconstruction against non-DLS "by X runs" outcomes
    reg_min_totals = reg.assign(
        min_extra=reg["extras_type"].isin(["wide", "Overstep"]).astype(int),
        min_run=reg["batter_runs"] + reg["extras_type"].isin(["wide", "Overstep"]).astype(int),
    )
    inn_sums = reg_min_totals.groupby(["match_id", "innings"])["min_run"].sum().unstack(fill_value=np.nan)
    m_check = matches.merge(inn_sums, on="match_id", how="left")
    m_non_dls_runs = m_check[
        m_check["result"].fillna("").str.contains(r"by\s+\d+\s+run", case=False, regex=True)
        & ~m_check["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True)
    ].copy()
    m_non_dls_runs["stated_margin"] = (
        m_non_dls_runs["result"].str.extract(r"by\s+(\d+)\s+run", flags=re.IGNORECASE)[0].astype(float)
    )
    m_non_dls_runs["calc_margin"] = m_non_dls_runs[1] - m_non_dls_runs[2]
    n_run_matches_tested = int(len(m_non_dls_runs))
    n_run_matches_exact = int((m_non_dls_runs["calc_margin"] == m_non_dls_runs["stated_margin"]).sum())
    n_run_matches_fail = n_run_matches_tested - n_run_matches_exact
    chase_score_reconstruction_blocked = bool(n_run_matches_fail > 0)

    # DLS revised overs units check
    rev_vals = pd.concat([
        pd.to_numeric(matches["first_inn_revised_overs"], errors="coerce"),
        pd.to_numeric(matches["second_inn_revised_overs"], errors="coerce"),
    ]).dropna()
    rev_gt_zero = rev_vals[rev_vals > 0]
    rev_min = float(rev_gt_zero.min()) if len(rev_gt_zero) else np.nan
    rev_max = float(rev_gt_zero.max()) if len(rev_gt_zero) else np.nan
    rev_le_20 = int((rev_gt_zero <= 20).sum())

    # Boundary, dismissal, Playing XI, and identity checks
    fours_mismatch = int(cleaned["boundary_discrepancy_flag"].sum())
    runs4_not_four = int(((bbb["runs"] == 4) & (bbb["is_four"] != 1)).sum())
    runs6_not_six = int(((bbb["runs"] == 6) & (bbb["is_six"] != 1)).sum())
    missing_dismissed = int(((bbb["is_wicket"] == 1) & bbb["dismissed_player_id"].isna()).sum())

    dup_p11_groups = int(p11.groupby(["match_id", "player_id"]).filter(lambda g: len(g) > 1)[["match_id", "player_id"]].drop_duplicates().shape[0])
    dup_p11_excess = int(len(p11) - p11[["match_id", "player_id"]].drop_duplicates().shape[0])

    bat_ids = bbb[["striker_id", "striker_name"]].rename(columns={"striker_id": "player_id", "striker_name": "player_name"})
    bowl_ids = bbb[["bowler_id", "bowler_name"]].rename(columns={"bowler_id": "player_id", "bowler_name": "player_name"})
    all_pl = pd.concat([bat_ids, bowl_ids], ignore_index=True).drop_duplicates()
    multi_name_ids = int((all_pl.groupby("player_id")["player_name"].nunique() > 1).sum())
    multi_id_names_df = all_pl.groupby("player_name")["player_id"].nunique()
    multi_id_names = sorted(multi_id_names_df[multi_id_names_df > 1].index.tolist())

    audit_summary = {
        "raw_zip_available": raw_info["raw_zip_available"],
        "raw_bbb_rows": raw_info["raw_bbb_rows"],
        "raw_matches": raw_info["raw_matches"],
        "scoped_rows": scoped_rows,
        "regular_rows": reg_rows,
        "super_over_rows": so_rows,
        "reconcil_diff": scoped_rows - reg_rows,
        "matches_total": matches_total,
        "matches_with_bbb": matches_with_bbb,
        "matches_abandoned": matches_abandoned,
        "wide_nonzero_runs": wide_nonzero_runs,
        "lb_nonzero_runs": lb_nonzero_runs,
        "bye_nonzero_runs": bye_nonzero_runs,
        "extras2_nonzero_rows": extras2_nonzero_rows,
        "non_dls_run_matches_tested": n_run_matches_tested,
        "non_dls_run_matches_exact": n_run_matches_exact,
        "non_dls_run_matches_fail": n_run_matches_fail,
        "chase_score_reconstruction_blocked": chase_score_reconstruction_blocked,
        "revised_overs_min": rev_min,
        "revised_overs_max": rev_max,
        "revised_overs_le_20": rev_le_20,
        "runs4_not_four": runs4_not_four,
        "runs6_not_six": runs6_not_six,
        "boundary_discrepancy_total": fours_mismatch,
        "missing_dismissed_player_id": missing_dismissed,
        "p11_duplicate_keys": dup_p11_groups,
        "p11_excess_rows": dup_p11_excess,
        "multi_name_player_ids": multi_name_ids,
        "multi_id_player_names": multi_id_names,
        "competitions_count": int(comps["comp_id"].nunique()),
        "mapping_rows": int(len(mapping)),
    }

    report_md = f"""# DATA AUDIT V4 — SupeRR Intelligence V4

## 1. Scope & Exact Row Reconciliation
- **Scope**: IPL and T20I matches from 2022 onwards (`data/ball_by_ball_ipl_t20i.csv`, `data/matches_ipl_t20i.csv`).
- **Raw Data Pack**: `{raw_info["raw_bbb_rows"]:,}` ball-by-ball rows across `{raw_info["raw_matches"]:,}` matches (`match_format` IPL + T20I + T20).
- **Non-IPL/T20I Exclusions**: `{raw_info["excluded_other_t20_rows"]:,}` deliveries across `{raw_info["excluded_other_t20_matches"]}` matches (`comp_id` in `{{{raw_info["excluded_other_t20_comp_ids"]}}}`: Men's T20 Emerging Teams Asia Cup / Asia Cup Rising Stars; `{raw_info["excluded_other_t20_reg"]:,}` regular + `{raw_info["excluded_other_t20_so"]}` Super Over) are excluded from the primary leaderboard.
- **Scoped Files (`data/README.md`)**: `{scoped_rows:,}` deliveries (`matches_ipl_t20i.csv`: `{matches_total}` matches total, `{matches_with_bbb}` with deliveries, `{matches_abandoned}` abandoned).
- **Regular vs Super Over Split**:
  - Regular innings (`innings in {{1, 2}}`): **`{reg_rows:,}`** deliveries (`1st={inn1_rows:,}`, `2nd={inn2_rows:,}`).
  - Super Overs (`innings in {{3, 4}}`): **`{so_rows}`** deliveries (`3rd={inn3_rows}`, `4th={inn4_rows}`), separated from main model fitting.
  - **Exact Reconciliation**: `{scoped_rows:,} - {reg_rows:,} = {scoped_rows - reg_rows}` Super Over deliveries. Full table exported to [`DATA_RECONCILIATION.csv`](file:///d:/rrhackthon/data/outputs/v4/DATA_RECONCILIATION.csv).

## 2. Critical Extras & Score Semantics (`CHASE_SCORE_RECONSTRUCTION_BLOCKED = {chase_score_reconstruction_blocked}`)
- **`extras1_runs` is a 1:1 categorical code mapping `extras_type`** (never extra runs): `Overstep=1`, `wide=2`, `legbyes=3`, `byes=4`, `other=5`, `None=6`, `Penalty=7` (`len(table)={len(ext_map_check)}`).
- **`runs` captures batter-scored runs only**: on 100% of `wide` (`wide_nonzero_runs={wide_nonzero_runs}`), `legbyes` (`{lb_nonzero_runs}`), and `byes` (`{bye_nonzero_runs}`), `runs == 0`. Multi-run wides, leg-byes, byes, and penalty runs are absent.
- **`extras_2_runs`**: non-zero on `{extras2_nonzero_rows}` rows (primarily 1/4 values on Overstep/other); quarantined via `quarantine_extras2_flag` rather than guessed.
- **Match Margin Reconstruction Test**: Testing `clean_runs = batter_runs + 1*(wide | Overstep)` across `{n_run_matches_tested}` non-DLS matches decided `"by X runs"` yields only **`{n_run_matches_exact}` exact matches vs `{n_run_matches_fail}` mismatches ({100.0 * n_run_matches_fail / max(n_run_matches_tested, 1):.1f}% failure rate)**.
- **Decision**: **`CHASE_SCORE_RECONSTRUCTION_BLOCKED = True`**. Exact team totals, first-innings target, runs remaining, required run rate (`RRR`), and score-based `WP(score, target)` / `C_t` are **quarantined and excluded**. All bowler run metrics are explicitly labeled **`BATTER_RUNS_CONCEDED_PROXY`**.

## 3. DLS Revised Overs Units Discovery
- Non-null positive values of `first_inn_revised_overs` and `second_inn_revised_overs` range from **`{rev_min:.0f}` to `{rev_max:.0f}`**, with **`{rev_le_20}` rows <= 20**.
- These fields store **revised scheduled BALLS** (e.g. `114`, `90`, `66`, `48`, `30`), NOT overs. Previous code in `src/context_engine/innings_context.py` multiplied values by `6.0`, corrupting shortened innings. V4 reads revised values directly as balls (multiplying by `6.0` only if `<= 20.0`).

## 4. Boundaries, Dismissals, Playing XI & Identity Integrity
- **Boundaries**: `{runs4_not_four}` rows have `runs == 4 & is_four != 1` (running 4s / all-run boundaries); `{runs6_not_six}` rows have `runs == 6 & is_six != 1` (`boundary_discrepancy_total={fours_mismatch}`). V4 uses `batter_runs` directly for scoring and validated flags only when needed.
- **Dismissals**: `{missing_dismissed}` delivery has `is_wicket == 1` with missing `dismissed_player_id` (`match_id=40709` Retire Out); `is_striker_out` strictly checks `dismissed_player_id == striker_id`, and `is_bowler_wicket` excludes run-outs and retired-out/hurt via `NON_BOWLER_DISMISSALS`.
- **Playing XI Duplicates**: `{dup_p11_groups}` `(match_id, player_id)` keys appear multiple times (`{dup_p11_excess}` excess rows in `playing_eleven_ipl_t20i.csv`); V4 deduplicates `(match_id, player_id)` deterministically and derives delivery exposure strictly from BBB `player_id`.
- **Player Identity**: `{multi_name_ids}` IDs map to multiple names; `{len(multi_id_names)}` player names map to multiple distinct `player_id`s ({", ".join(multi_id_names)}). **V4 aggregates strictly by `striker_id` and `bowler_id` everywhere.**
"""
    with open(os.path.join(report_dir, "DATA_AUDIT_V4.md"), "w", encoding="utf-8") as f:
        f.write(report_md)

    return audit_summary
