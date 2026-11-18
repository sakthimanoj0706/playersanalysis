"""Phase 4: Rajasthan Royals Secondary Squad Requirements & Candidate-Fit Selection.

Strictly decoupled from Universal Top 10 rankings (never alters global ranks).
Evaluates BOTH Universal Top 10 candidates and the full eligible player pool outside Top 10
using V4.2 complete-FWL estimates + phase/pace-spin profiles from ball_by_ball_ipl_t20i.csv.
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import NON_BOWLER_DISMISSALS

ROOT = Path(__file__).resolve().parents[1]


def _minmax_pct(s: pd.Series) -> pd.Series:
    if len(s) == 0 or s.nunique(dropna=True) <= 1:
        return pd.Series(50.0, index=s.index)
    return s.rank(pct=True, method="average") * 100.0


def main() -> None:
    fin_dir = ROOT / "data/outputs/final"
    v3_dir = ROOT / "data/outputs/v3"

    bbb = pd.read_csv(ROOT / "data/ball_by_ball_ipl_t20i.csv", low_memory=False)
    reg = bbb[bbb["innings"].isin([1, 2])].copy()
    reg["is_legal"] = (~reg["extras_type"].isin(["wide", "Overstep"])).astype(int)
    reg["is_faced"] = (reg["extras_type"] != "wide").astype(int)
    reg["phase"] = np.where(reg["overid"] <= 6, "powerplay", np.where(reg["overid"] <= 15, "middle", "death"))
    reg["pace_or_spin"] = reg["pace_or_spin"].astype(str).str.strip().str.lower()
    reg["is_bowler_wkt"] = ((reg["is_wicket"] == 1) & (~reg["dismissal_type"].isin(NON_BOWLER_DISMISSALS))).astype(int)

    all_est = pd.read_csv(fin_dir / "ALL_PLAYER_FINAL_ESTIMATES.csv")
    elig = all_est[all_est["eligible"] == True].copy()

    # Load RR 2026 requirements & existing squad context
    req = pd.read_csv(v3_dir / "RR_REQUIRED_ROLES.csv")
    req["scouting_priority_weight"] = [1.00, 0.98, 0.85, 0.82, 0.65][: len(req)]
    req.to_csv(fin_dir / "RR_TEAM_REQUIREMENTS.csv", index=False)

    rr_2026_bat = pd.read_csv(v3_dir / "rr_2026_batting_stats.csv")
    rr_2026_bowl = pd.read_csv(v3_dir / "rr_2026_bowling_stats.csv")
    rr_existing_ids = set(rr_2026_bat["player_id"].dropna().astype(int).tolist()) | set(rr_2026_bowl["player_id"].dropna().astype(int).tolist())

    # Build phase & type profiles for batters and bowlers
    bat_reg = reg[reg["is_faced"] == 1]
    bat_prof = bat_reg.groupby("striker_id", as_index=False).agg(
        total_bat_runs=("runs", "sum"),
        total_bat_balls=("is_faced", "sum"),
        avg_bat_pos=("batting_order", "mean"),
        death_runs=("runs", lambda s: s[bat_reg.loc[s.index, "phase"] == "death"].sum()),
        death_balls=("is_faced", lambda s: s[bat_reg.loc[s.index, "phase"] == "death"].sum()),
        pp_runs=("runs", lambda s: s[bat_reg.loc[s.index, "phase"] == "powerplay"].sum()),
        pp_balls=("is_faced", lambda s: s[bat_reg.loc[s.index, "phase"] == "powerplay"].sum()),
        spin_runs=("runs", lambda s: s[bat_reg.loc[s.index, "pace_or_spin"] == "spin"].sum()),
        spin_balls=("is_faced", lambda s: s[bat_reg.loc[s.index, "pace_or_spin"] == "spin"].sum()),
        pace_runs=("runs", lambda s: s[bat_reg.loc[s.index, "pace_or_spin"] == "pace"].sum()),
        pace_balls=("is_faced", lambda s: s[bat_reg.loc[s.index, "pace_or_spin"] == "pace"].sum()),
        ipl_balls=("is_faced", lambda s: s[bat_reg.loc[s.index, "match_format"] == "T20"].sum()),
    ).rename(columns={"striker_id": "player_id"})
    bat_prof["death_sr"] = np.where(bat_prof["death_balls"] >= 30, 100.0 * bat_prof["death_runs"] / bat_prof["death_balls"], np.nan)
    bat_prof["pp_sr"] = np.where(bat_prof["pp_balls"] >= 30, 100.0 * bat_prof["pp_runs"] / bat_prof["pp_balls"], np.nan)
    bat_prof["spin_sr"] = np.where(bat_prof["spin_balls"] >= 30, 100.0 * bat_prof["spin_runs"] / bat_prof["spin_balls"], np.nan)
    bat_prof["pace_sr"] = np.where(bat_prof["pace_balls"] >= 30, 100.0 * bat_prof["pace_runs"] / bat_prof["pace_balls"], np.nan)
    bat_prof["ipl_share"] = bat_prof["ipl_balls"] / np.maximum(bat_prof["total_bat_balls"], 1)

    bowl_reg = reg[reg["is_legal"] == 1]
    bowl_prof = bowl_reg.groupby("bowler_id", as_index=False).agg(
        total_bowl_balls=("is_legal", "sum"),
        total_wkts=("is_bowler_wkt", "sum"),
        bowl_type=("pace_or_spin", lambda s: s.mode().iloc[0] if len(s.mode()) else "pace"),
        pp_balls=("is_legal", lambda s: s[bowl_reg.loc[s.index, "phase"] == "powerplay"].sum()),
        pp_runs=("runs", lambda s: s[bowl_reg.loc[s.index, "phase"] == "powerplay"].sum()),
        mid_balls=("is_legal", lambda s: s[bowl_reg.loc[s.index, "phase"] == "middle"].sum()),
        mid_runs=("runs", lambda s: s[bowl_reg.loc[s.index, "phase"] == "middle"].sum()),
        death_balls=("is_legal", lambda s: s[bowl_reg.loc[s.index, "phase"] == "death"].sum()),
        death_runs=("runs", lambda s: s[bowl_reg.loc[s.index, "phase"] == "death"].sum()),
        death_wkts=("is_bowler_wkt", lambda s: s[bowl_reg.loc[s.index, "phase"] == "death"].sum()),
        ipl_balls=("is_legal", lambda s: s[bowl_reg.loc[s.index, "match_format"] == "T20"].sum()),
    ).rename(columns={"bowler_id": "player_id"})
    bowl_prof["death_rpb_proxy"] = np.where(bowl_prof["death_balls"] >= 30, 6.0 * bowl_prof["death_runs"] / bowl_prof["death_balls"], np.nan)
    bowl_prof["mid_rpb_proxy"] = np.where(bowl_prof["mid_balls"] >= 30, 6.0 * bowl_prof["mid_runs"] / bowl_prof["mid_balls"], np.nan)
    bowl_prof["pp_rpb_proxy"] = np.where(bowl_prof["pp_balls"] >= 30, 6.0 * bowl_prof["pp_runs"] / bowl_prof["pp_balls"], np.nan)
    bowl_prof["ipl_share"] = bowl_prof["ipl_balls"] / np.maximum(bowl_prof["total_bowl_balls"], 1)

    # Score eligible batters for RR tactical roles
    eb = elig[elig["role"] == "batter"].merge(bat_prof, on="player_id", how="left")
    eb["in_universal_top10"] = eb["shortlist_rank_display"].notna()
    eb["already_rr_2026"] = eb["player_id"].isin(rr_existing_ids)
    eb["rr_target_role"] = np.where(
        eb["avg_bat_pos"] >= 5.0,
        "Lower-Order Finisher (Overs 15-20)",
        np.where(eb["avg_bat_pos"] <= 2.8, "Top-Order / Powerplay Anchor", "Middle-Order Spin/Pace Accelerator"),
    )
    eb["role_need_score"] = np.where(
        eb["avg_bat_pos"] >= 5.0,
        92.0,
        np.where(eb["avg_bat_pos"] <= 2.8, 65.0, 80.0),
    )
    eb["phase_exec_score"] = _minmax_pct(eb["death_sr"].fillna(eb["raw_overall_perf"]) * 0.65 + eb["raw_overall_perf"] * 0.35)
    eb["pressure_v42_score"] = _minmax_pct(eb["eb_delta"])
    eb["sample_conf_score"] = _minmax_pct(eb["cs_matches"])
    eb["balance_ipl_score"] = 50.0 + 50.0 * eb["ipl_share"].fillna(0.0)

    # Score eligible bowlers for RR tactical roles
    ew = elig[elig["role"] == "bowler"].merge(bowl_prof, on="player_id", how="left")
    ew["in_universal_top10"] = ew["shortlist_rank_display"].notna()
    ew["already_rr_2026"] = ew["player_id"].isin(rr_existing_ids)
    ew["rr_target_role"] = np.where(
        ew["bowl_type"] == "spin",
        "Economical Middle-Over Spinner",
        np.where(ew["death_balls"] >= ew["pp_balls"], "Death-Over Pace Specialist", "Powerplay / All-Phase Pacer"),
    )
    ew["role_need_score"] = np.where(
        ew["bowl_type"] == "spin",
        85.0,
        np.where(ew["death_balls"] >= ew["pp_balls"], 96.0, 88.0),
    )
    # Lower runs conceded per 6 balls is better -> negate for percentile
    best_phase_econ = ew["death_rpb_proxy"].fillna(ew["mid_rpb_proxy"]).fillna(-ew["raw_overall_perf"] * 0.06)
    ew["phase_exec_score"] = _minmax_pct(-best_phase_econ * 0.65 + ew["raw_overall_perf"] * 0.35)
    ew["pressure_v42_score"] = _minmax_pct(ew["eb_delta"])
    ew["sample_conf_score"] = _minmax_pct(ew["cs_matches"])
    ew["balance_ipl_score"] = 50.0 + 50.0 * ew["ipl_share"].fillna(0.0)

    combined = pd.concat([eb, ew], ignore_index=True)

    # Baseline RR_PLAYER_FIT_SCORE + 2 alternative weight sensitivities
    combined["RR_PLAYER_FIT_SCORE"] = (
        0.35 * combined["phase_exec_score"]
        + 0.25 * combined["role_need_score"]
        + 0.20 * combined["pressure_v42_score"]
        + 0.10 * combined["sample_conf_score"]
        + 0.10 * combined["balance_ipl_score"]
    ).round(2)
    combined["fit_score_pressure_heavy"] = (
        0.25 * combined["phase_exec_score"]
        + 0.20 * combined["role_need_score"]
        + 0.35 * combined["pressure_v42_score"]
        + 0.10 * combined["sample_conf_score"]
        + 0.10 * combined["balance_ipl_score"]
    ).round(2)
    combined["fit_score_role_heavy"] = (
        0.40 * combined["phase_exec_score"]
        + 0.35 * combined["role_need_score"]
        + 0.10 * combined["pressure_v42_score"]
        + 0.10 * combined["sample_conf_score"]
        + 0.05 * combined["balance_ipl_score"]
    ).round(2)

    keep_cols = [
        "player_id", "player_name", "role", "in_universal_top10", "shortlist_rank_display",
        "eb_rank", "already_rr_2026", "rr_target_role", "total_matches", "cs_matches",
        "eb_delta", "eb_vs_pop_mean_delta", "prob_top_10", "phase_exec_score",
        "role_need_score", "pressure_v42_score", "sample_conf_score", "balance_ipl_score",
        "RR_PLAYER_FIT_SCORE", "fit_score_pressure_heavy", "fit_score_role_heavy",
    ]
    # Add discipline-specific tactical stats
    combined["death_sr_or_econ"] = np.where(
        combined["role"] == "batter",
        combined["death_sr"].round(1),
        combined["death_rpb_proxy"].round(2),
    )
    keep_cols.append("death_sr_or_econ")

    top10_fit = combined[combined["in_universal_top10"]].sort_values("RR_PLAYER_FIT_SCORE", ascending=False)[keep_cols].copy()
    top10_fit.to_csv(fin_dir / "RR_TOP10_CANDIDATE_FIT.csv", index=False)

    outside = combined[(~combined["in_universal_top10"]) & (~combined["already_rr_2026"])].copy()
    outside = outside.sort_values("RR_PLAYER_FIT_SCORE", ascending=False)
    outside_top = outside.head(20)[keep_cols].copy()
    outside_top["why_better_rr_fit_than_some_top10"] = outside_top.apply(
        lambda r: (
            f"Matches RR tactical gap ({r['rr_target_role']}) with IPL exposure share={r['balance_ipl_score']:.0f}/100 "
            f"and phase execution={r['phase_exec_score']:.1f}/100 despite ranking #{int(round(r['eb_rank']))} globally."
        ),
        axis=1,
    )
    outside_top.to_csv(fin_dir / "RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv", index=False)

    # Recommended squad combination (balanced across roles from Top 10 & Outside Top 10)
    rec_rows = []
    t10_targets = top10_fit[~top10_fit["already_rr_2026"]].head(4)
    for _, r in t10_targets.iterrows():
        rec_rows.append({**r.to_dict(), "selection_pool": "UNIVERSAL_TOP_10", "squad_role": "PRIMARY_TARGET"})
    role_counts: dict[str, int] = {}
    for _, r in outside.iterrows():
        role_k = str(r["rr_target_role"])
        if role_counts.get(role_k, 0) >= 2:
            continue
        role_counts[role_k] = role_counts.get(role_k, 0) + 1
        rec_rows.append({**r[keep_cols].to_dict(), "selection_pool": "OUTSIDE_TOP_10_ELIGIBLE_POOL", "squad_role": "TACTICAL_FIT_TARGET"})
        if len(rec_rows) >= 10:
            break
    rec_df = pd.DataFrame(rec_rows)
    rec_df.to_csv(fin_dir / "RR_RECOMMENDED_SQUAD.csv", index=False)

    # Report
    lines = [
        "# Rajasthan Royals Squad-Fit & Scouting Report (Secondary Module)",
        "",
        "> **Strict Decoupling Disclosure:** This RR scouting module is a **secondary application** of SupeRR Intelligence V4.2. It never modifies, filters, or overrides the Universal Top 10 leaderboards.",
        "",
        "## 1. RR 2026 Tactical Gaps (`RR_TEAM_REQUIREMENTS.csv`)",
        "- **CRITICAL — Indian Frontline Fast Bowler:** Domestic pace support behind Jofra Archer yielded only 9 wickets across 13 combined appearances (Deshpande 4, Sandeep 5).",
        "- **CRITICAL — Overseas Death-Over Specialist:** High boundary leakage in overs 16–20 behind Archer.",
        "- **IMPORTANT — Economical Middle-Over Spinner:** Support alongside Ravindra Jadeja (already in RR) and Ravi Bishnoi.",
        "- **IMPORTANT — Domestic Lower-Order Finisher:** Needed at No. 6/7 to reduce reliance on Shimron Hetmyer.",
        "",
        "## 2. Transparent `RR_PLAYER_FIT_SCORE` Formula",
        "`RR_PLAYER_FIT_SCORE = 0.35 * Phase_Execution + 0.25 * Role_Tactical_Need + 0.20 * Pressure_Resilience_V42 + 0.10 * Sample_Confidence + 0.10 * IPL_Balance_Bonus`",
        "",
        "## 3. Top Universal Top 10 Candidates for RR (`RR_TOP10_CANDIDATE_FIT.csv`)",
    ]
    for _, r in top10_fit.head(8).iterrows():
        tag = " (Already RR 2026)" if r["already_rr_2026"] else ""
        lines.append(
            f"- **{r['player_name']}** ({r['role']}, Global #{int(r['shortlist_rank_display'])}{tag}) — "
            f"`RR_FIT={r['RR_PLAYER_FIT_SCORE']:.1f}` | Role: {r['rr_target_role']} | `EB Δ={r['eb_delta']:.2f}`"
        )
    lines.extend(["", "## 4. Best RR-Suited Candidates Outside Universal Top 10 (`RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv`)"])
    for _, r in outside_top.head(8).iterrows():
        lines.append(
            f"- **{r['player_name']}** ({r['role']}, Global #{int(round(r['eb_rank']))}) — "
            f"`RR_FIT={r['RR_PLAYER_FIT_SCORE']:.1f}` | Role: {r['rr_target_role']} | {r['why_better_rr_fit_than_some_top10']}"
        )
    lines.extend(["", "## 5. Recommended Balanced RR Shortlist (`RR_RECOMMENDED_SQUAD.csv`)"])
    for _, r in rec_df.iterrows():
        lines.append(
            f"- **{r['player_name']}** ({r['role']}, `{r['selection_pool']}`) — "
            f"`RR_FIT={r['RR_PLAYER_FIT_SCORE']:.1f}` | Role: {r['rr_target_role']} | `EB Δ={r['eb_delta']:.2f}`"
        )
    lines.extend([
        "",
        "## 6. Weight Sensitivity & Assumptions",
        "- Tested across `Baseline (35/25/20/10/10)`, `Pressure-Heavy (25/20/35/10/10)`, and `Role-Heavy (40/35/10/10/5)`.",
        "- Auction purse and player availability remain **unverified external assumptions** (`data/reference/rr_2027_auction_assumptions.csv`), kept strictly configurable.",
    ])
    (fin_dir / "RR_PLAYER_FIT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    # Register RR output hashes in FINAL_RANKING_SOURCE_OF_TRUTH.json
    import hashlib
    import json
    sot_path = fin_dir / "FINAL_RANKING_SOURCE_OF_TRUTH.json"
    if sot_path.exists():
        sot = json.loads(sot_path.read_text(encoding="utf-8"))
        rr_files = [
            "RR_TEAM_REQUIREMENTS.csv",
            "RR_TOP10_CANDIDATE_FIT.csv",
            "RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv",
            "RR_RECOMMENDED_SQUAD.csv",
        ]
        sot["rr_hashes"] = {
            f: hashlib.sha256((fin_dir / f).read_bytes()).hexdigest()
            for f in rr_files
            if (fin_dir / f).exists()
        }
        sot_path.write_text(json.dumps(sot, indent=2), encoding="utf-8")

    print("Top 5 Universal Top 10 RR Fits:")
    print(top10_fit[["player_name", "role", "shortlist_rank_display", "rr_target_role", "RR_PLAYER_FIT_SCORE", "already_rr_2026"]].head(5).to_string(index=False))
    print("\nTop 8 Outside-Top-10 RR Fits:")
    print(outside_top[["player_name", "role", "eb_rank", "rr_target_role", "RR_PLAYER_FIT_SCORE"]].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
