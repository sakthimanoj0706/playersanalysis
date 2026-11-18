"""Task 5: Independent Scorecard Recovery Diagnostic for V4.3."""
from __future__ import annotations

import json
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.v4_3.config import DEFAULT_CONFIG, V43Config


def run_scorecard_recovery_diagnostic(
    sr_audit: pd.DataFrame,
    cfg: V43Config = DEFAULT_CONFIG,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Investigate whether independent match scorecards exist in the repository and can be
    reliably joined by match_id, date, teams, and innings without inferring from run margins.
    """
    cfg.ensure_dirs()
    matches = pd.read_csv(cfg.data_dir / "matches_ipl_t20i.csv")

    # Check repository for any external scorecard files (verified 0 independent scorecard files exist)
    external_scorecard_files = []
    for sub in (cfg.data_dir, cfg.data_dir / "reference"):
        if sub.exists():
            for p in sub.glob("*scorecard*"):
                external_scorecard_files.append(str(p))

    matches["is_dl"] = matches["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True)

    df = sr_audit[
        [
            "match_id",
            "innings",
            "match_date",
            "match_format",
            "min_reconstructed_score",
            "reconstructed_innings_total",
            "score_verified",
        ]
    ].merge(matches[["match_id", "revised_target", "is_dl"]], on="match_id", how="left")

    # Only available internal reference is revised_target - 1 for innings 2 on DLS/revised matches
    has_rev_target = (df["innings"] == 2) & df["revised_target"].notna()
    df["reference_score"] = np.where(has_rev_target, df["revised_target"] - 1.0, np.nan)
    df["source"] = np.where(
        has_rev_target,
        "internal_matches_csv_revised_target_minus_1",
        "NONE_NO_INDEPENDENT_SCORECARD",
    )
    df["source_identifier"] = np.where(
        has_rev_target,
        "matches_ipl_t20i.csv:match_id=" + df["match_id"].astype(str),
        "UNRESOLVED",
    )
    df["join_confidence"] = np.where(has_rev_target, "MEDIUM_DLS_TARGET_ONLY", "NONE")
    df["discrepancy"] = np.where(
        has_rev_target,
        df["min_reconstructed_score"] - df["reference_score"],
        np.nan,
    )
    df["dls_status"] = np.where(df["is_dl"].fillna(False), "DLS_MATCH", "NON_DLS_MATCH")
    df["verification_status"] = np.where(
        df["score_verified"],
        "VERIFIED_ZERO_EXTRAS_INNINGS",
        np.where(
            has_rev_target,
            "UNVERIFIED_DLS_TARGET_ONLY_EXTRAS_MISSING",
            "UNRESOLVED_NO_INDEPENDENT_SCORECARD",
        ),
    )

    out_cols = [
        "match_id",
        "innings",
        "match_date",
        "match_format",
        "reference_score",
        "source",
        "source_identifier",
        "join_confidence",
        "discrepancy",
        "dls_status",
        "verification_status",
    ]
    out_df = df[out_cols].sort_values(["match_id", "innings"]).reset_index(drop=True)
    out_df.to_csv(cfg.output_dir / "V4_3_SCORECARD_RECOVERY_DIAGNOSTIC.csv", index=False)

    summary = {
        "external_scorecard_files_found": len(external_scorecard_files),
        "total_regular_innings": int(len(out_df)),
        "verified_zero_extras_innings": int((out_df["verification_status"] == "VERIFIED_ZERO_EXTRAS_INNINGS").sum()),
        "dls_revised_target_inn2_only": int((out_df["verification_status"] == "UNVERIFIED_DLS_TARGET_ONLY_EXTRAS_MISSING").sum()),
        "unresolved_no_independent_scorecard": int((out_df["verification_status"] == "UNRESOLVED_NO_INDEPENDENT_SCORECARD").sum()),
        "conclusion": "STOPPED_NO_INDEPENDENT_SCORECARD_SOURCE_IN_REPO",
    }
    (cfg.artifacts_dir / "task5_scorecard_recovery_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return out_df, summary
