"""Phase 1 Data Quality, Player Identity & Star-Player Audit."""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    bbb = pd.read_csv(ROOT / "data/ball_by_ball_ipl_t20i.csv", low_memory=False)
    matches = pd.read_csv(ROOT / "data/matches_ipl_t20i.csv")
    p11 = pd.read_csv(ROOT / "data/playing_eleven_ipl_t20i.csv")
    cw = pd.read_csv(ROOT / "data/outputs/v3/PLAYER_IDENTITY_CROSSWALK.csv")
    all_est = pd.read_csv(ROOT / "data/outputs/v4_2/V4_2_ALL_PLAYER_ESTIMATES.csv")
    rp = pd.read_csv(ROOT / "data/outputs/v4_2/V4_2_RANK_PROBABILITIES.csv")
    sl = pd.read_csv(ROOT / "data/outputs/v4_2/V4_2_FINAL_SHORTLIST.csv")
    sot = json.loads((ROOT / "data/outputs/v4_2/V4_2_SOURCE_OF_TRUTH.json").read_text(encoding="utf-8"))

    # 1. Raw dataset quality summary
    reg = bbb[bbb["innings"].isin([1, 2])].copy()
    so = bbb[~bbb["innings"].isin([1, 2])].copy()
    dup_reg = reg.duplicated(subset=["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]).sum()
    print("=== RAW DATA VALIDATION ===")
    print(f"Matches table: {len(matches)} rows, unique match_id: {matches['match_id'].nunique()}")
    print(f"Ball-by-ball matches: {bbb['match_id'].nunique()}, total rows: {len(bbb)}")
    print(f"Regular innings rows: {len(reg)}, Super Over rows: {len(so)}")
    print(f"Unique (match_id, innings) in regular: {reg[['match_id', 'innings']].drop_duplicates().shape[0]}")
    print(f"Duplicate (match_id, innings, overid, ball_number) in regular: {dup_reg}")
    print(f"Missing striker_id: {reg['striker_id'].isna().sum()}, missing bowler_id: {reg['bowler_id'].isna().sum()}")
    print("extras_type value counts:")
    print(reg["extras_type"].fillna("NONE").value_counts().to_dict())
    dl_col = [c for c in matches.columns if "dl" in c.lower()]
    if dl_col:
        print(f"DLS matches in matches_ipl_t20i ({dl_col[0]}): {(matches[dl_col[0]] == 1).sum()}")
    print(f"Playing XI rows: {len(p11)}, unique (match_id, player_id): {p11[['match_id', 'player_id']].drop_duplicates().shape[0]}")

    # 2. Star player audit
    star_batters = [
        "Virat Kohli", "Rohit Sharma", "MS Dhoni", "David Miller", "Andre Russell",
        "Ravindra Jadeja", "Rinku Singh", "Suryakumar Yadav", "Jos Buttler",
        "Sanju Samson", "Yashasvi Jaiswal",
    ]
    star_bowlers = [
        "Jasprit Bumrah", "Jofra Archer", "Rashid Khan", "Pat Cummins",
        "Mitchell Starc", "Trent Boult", "Matheesha Pathirana", "Haris Rauf",
        "Kagiso Rabada", "Mohammed Shami",
    ]

    # Map player_id -> canonical name from crosswalk & regular deliveries
    p11_names = pd.concat([
        reg[["striker_id", "striker_name"]].rename(columns={"striker_id": "player_id", "striker_name": "player_name"}),
        reg[["bowler_id", "bowler_name"]].rename(columns={"bowler_id": "player_id", "bowler_name": "player_name"}),
    ], ignore_index=True).drop_duplicates("player_id")
    search_aliases = {
        "Pat Cummins": ["Pat Cummins", "Patrick Cummins"],
        "MS Dhoni": ["MS Dhoni", "Mahendra Singh Dhoni"],
    }

    rows = []
    for role, names in [("batter", star_batters), ("bowler", star_bowlers)]:
        role_est = all_est[all_est["role"] == role].copy()
        role_rp = rp[rp["role"] == role].copy()
        for nm in names:
            cand_names = [x.lower() for x in search_aliases.get(nm, [nm])]
            cw_hits = cw[
                cw["canonical_player_name"].astype(str).str.lower().isin(cand_names)
                | cw["source_player_name"].astype(str).str.lower().isin(cand_names)
                | cw["alias_name"].astype(str).str.lower().isin(cand_names)
            ]
            if cw_hits.empty:
                cw_hits = p11_names[p11_names["player_name"].astype(str).str.lower().isin(cand_names)]
            pids = cw_hits["canonical_player_id"].unique().tolist() if "canonical_player_id" in cw_hits.columns else cw_hits["player_id"].unique().tolist()
            # Filter estimates matching pids or name
            est_hits = role_est[role_est["player_id"].isin(pids) | role_est["player_name"].astype(str).str.lower().isin(cand_names)]
            if est_hits.empty:
                rows.append({
                    "player_name": nm,
                    "discipline": role,
                    "canonical_player_id": pids[0] if pids else np.nan,
                    "eligible": False,
                    "exclusion_reason": "NO_ESTIMATE_ROWS_OR_NO_COMMON_SUPPORT",
                })
                continue
            r = est_hits.sort_values("total_balls", ascending=False).iloc[0]
            pid = int(r["player_id"])
            rp_hit = role_rp[role_rp["player_id"] == pid]
            sl_hit = sl[(sl["role"] == role) & (sl["player_id"] == pid)]
            has_rp = not rp_hit.empty
            rk_row = rp_hit.iloc[0] if has_rp else r
            sl_rank = int(sl_hit.iloc[0]["shortlist_rank_display"]) if not sl_hit.empty else np.nan

            # Raw innings count from regular deliveries
            if role == "batter":
                inn_cnt = int(reg[reg["striker_id"] == pid][["match_id", "innings"]].drop_duplicates().shape[0])
            else:
                inn_cnt = int(reg[reg["bowler_id"] == pid][["match_id", "innings"]].drop_duplicates().shape[0])

            # Exclusion reason if ineligible
            reasons = []
            if not bool(r["eligible"]):
                if float(r["n_hi"]) < 50:
                    reasons.append(f"n_hi={int(r['n_hi'])}<50")
                if float(r["n_lo"]) < 30:
                    reasons.append(f"n_lo={int(r['n_lo'])}<30")
                if float(r["cs_matches"]) < 8:
                    reasons.append(f"cs_matches={int(r['cs_matches'])}<8")
                if pd.isna(r["se_delta"]) or float(r["se_delta"]) > 25.0:
                    se_s = "NaN" if pd.isna(r["se_delta"]) else f"{float(r['se_delta']):.2f}"
                    reasons.append(f"se_delta={se_s}>25.0")
            excl = "; ".join(reasons) if reasons else "ELIGIBLE"

            # Explanation
            if pd.notna(sl_rank) and sl_rank <= 10:
                expl = (
                    f"Shortlisted #{sl_rank} in {role}s: "
                    f"EB Delta={float(r['eb_delta']):.2f} ({float(r['eb_vs_pop_mean_delta']):+.2f} vs pop mean), "
                    f"P(Top 10)={float(rk_row['prob_top_10']):.3f}, CS={int(r['cs_matches'])} matches."
                )
            elif bool(r["eligible"]):
                avg_rk = float(rk_row["eb_rank"])
                expl = (
                    f"Eligible #{int(round(avg_rk))} of {len(role_rp)} (outside Top 10): "
                    f"EB Delta={float(r['eb_delta']):.2f} ({float(r['eb_vs_pop_mean_delta']):+.2f} vs pop mean), "
                    f"unshrunk FWL={float(r['delta_unshrunk']):+.2f}, P(Top 10)={float(rk_row['prob_top_10']):.3f}."
                )
            else:
                expl = f"Excluded by operational precision floor ({excl}); unshrunk FWL={r.get('delta_unshrunk', np.nan)}."

            rows.append({
                "player_name": nm,
                "discipline": role,
                "canonical_player_id": pid,
                "identity_ids_found": ",".join(str(x) for x in pids),
                "total_matches": int(r["total_matches"]),
                "total_innings": inn_cnt,
                "total_legal_balls": int(r["total_balls"]),
                "n_hi": int(r["n_hi"]),
                "n_lo": int(r["n_lo"]),
                "cs_matches": int(r["cs_matches"]),
                "eligible": bool(r["eligible"]),
                "exclusion_reason": excl,
                "raw_overall_perf": round(float(r["raw_overall_perf"]), 2),
                "raw_hi_perf": round(float(r["raw_hi_perf"]), 2) if pd.notna(r["raw_hi_perf"]) else np.nan,
                "raw_lo_perf": round(float(r["raw_lo_perf"]), 2) if pd.notna(r["raw_lo_perf"]) else np.nan,
                "raw_hi_minus_lo": round(float(r["raw_hi_minus_lo"]), 2) if pd.notna(r["raw_hi_minus_lo"]) else np.nan,
                "delta_unshrunk": round(float(r["delta_unshrunk"]), 2) if pd.notna(r["delta_unshrunk"]) else np.nan,
                "se_delta": round(float(r["se_delta"]), 2) if pd.notna(r["se_delta"]) else np.nan,
                "eb_delta": round(float(r["eb_delta"]), 2) if pd.notna(r["eb_delta"]) else np.nan,
                "eb_vs_pop_mean_delta": round(float(r["eb_vs_pop_mean_delta"]), 2) if pd.notna(r["eb_vs_pop_mean_delta"]) else np.nan,
                "eb_boot_ci_low": round(float(rk_row["eb_boot_ci_low"]), 2) if has_rp else np.nan,
                "eb_boot_ci_high": round(float(rk_row["eb_boot_ci_high"]), 2) if has_rp else np.nan,
                "boot_rank_ci_low": int(round(float(rk_row["boot_rank_ci_low"]))) if has_rp else np.nan,
                "boot_rank_ci_high": int(round(float(rk_row["boot_rank_ci_high"]))) if has_rp else np.nan,
                "prob_top_10": round(float(rk_row["prob_top_10"]), 4) if has_rp else 0.0,
                "eb_rank": round(float(rk_row["eb_rank"]), 1) if has_rp else np.nan,
                "shortlist_rank_display": sl_rank,
                "explanation": expl,
            })

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "STAR_PLAYER_ELIGIBILITY_AUDIT.csv", index=False)
    print("\n=== STAR PLAYER AUDIT SAVED ===")
    print(out[["player_name", "discipline", "canonical_player_id", "total_legal_balls", "n_hi", "n_lo", "cs_matches", "eligible", "eb_delta", "eb_rank", "shortlist_rank_display"]].to_string(index=False))


if __name__ == "__main__":
    main()
