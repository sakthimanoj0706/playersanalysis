"""Track A: Cricsheet JSON Ingestion, Crosswalk & Numeric Extras Reconciliation for V4.4."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from src.config import BBB_DTYPE_OVERRIDES
from src.ingestion.adapters.rr_data_adapter import RRDataAdapter
from src.v4_4.config import DEFAULT_V44_CONFIG, V44Config

TEAM_ALIASES: Dict[str, str] = {
    "royal challengers bangalore": "royal challengers bengaluru",
    "kings xi punjab": "punjab kings",
    "delhi daredevils": "delhi capitals",
    "rising pune supergiants": "rising pune supergiant",
    "u.a.e.": "united arab emirates",
    "uae": "united arab emirates",
    "u.s.a.": "united states of america",
    "usa": "united states of america",
    "p.n.g.": "papua new guinea",
    "png": "papua new guinea",
    "czech rep.": "czech republic",
}


def _norm_team(name: Any) -> str:
    if pd.isna(name):
        return ""
    s = re.sub(r"\s+", " ", str(name).strip().lower())
    return TEAM_ALIASES.get(s, s)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_cricsheet_zips(cfg: V44Config = DEFAULT_V44_CONFIG, force: bool = False) -> Dict[str, Any]:
    """Download Cricsheet IPL and Men's T20I JSON archives if not present and record provenance."""
    cfg.ensure_dirs()
    prov: Dict[str, Any] = {
        "retrieval_utc": datetime.now(timezone.utc).isoformat(),
        "archives": {},
    }
    for key, url, fname in [
        ("ipl_json", cfg.ipl_json_url, "ipl_json.zip"),
        ("t20s_male_json", cfg.t20i_json_url, "t20s_male_json.zip"),
    ]:
        dest = cfg.cricsheet_dir / fname
        if force or not dest.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
                out.write(resp.read())
        prov["archives"][key] = {
            "url": url,
            "local_path": str(dest),
            "size_bytes": int(dest.stat().st_size),
            "sha256": _sha256_file(dest),
        }
    return prov


def _load_cricsheet_index(
    zip_paths: List[Tuple[str, Path]],
    min_date: str = "2022-01-01",
    max_date: str = "2026-11-10",
) -> Tuple[List[Dict[str, Any]], Dict[str, Tuple[Path, str]]]:
    """Index Cricsheet JSON match headers within the target date window."""
    records: List[Dict[str, Any]] = []
    file_loc: Dict[str, Tuple[Path, str]] = {}
    data_versions: set = set()

    for source_tag, zp in zip_paths:
        with zipfile.ZipFile(zp, "r") as zf:
            for member in zf.namelist():
                if not member.endswith(".json"):
                    continue
                with zf.open(member) as f:
                    doc = json.load(f)
                info = doc.get("info", {})
                dates = info.get("dates", [])
                if not dates:
                    continue
                m_date = str(dates[0])[:10]
                if m_date < min_date or m_date > max_date:
                    continue
                teams = info.get("teams", [])
                if len(teams) != 2:
                    continue
                cs_id = Path(member).stem
                data_versions.add(str(doc.get("meta", {}).get("data_version", "unknown")))
                file_loc[cs_id] = (zp, member)
                records.append(
                    {
                        "cs_match_id": cs_id,
                        "cs_source": source_tag,
                        "cs_date": m_date,
                        "cs_team1": teams[0],
                        "cs_team2": teams[1],
                        "cs_team_pair": frozenset([_norm_team(teams[0]), _norm_team(teams[1])]),
                        "cs_event": info.get("event", {}).get("name", ""),
                        "cs_match_number": info.get("event", {}).get("match_number", np.nan),
                        "cs_venue": info.get("venue", ""),
                        "cs_city": info.get("city", ""),
                        "cs_match_type": info.get("match_type", ""),
                        "cs_gender": info.get("gender", ""),
                        "cs_season": str(info.get("season", "")),
                        "cs_outcome": json.dumps(info.get("outcome", {})),
                        "cs_n_innings": len(doc.get("innings", [])),
                    }
                )
    return records, file_loc


def _extract_cs_deliveries(doc: Dict[str, Any], cs_match_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract ordered delivery events and innings-level penalty runs from a Cricsheet JSON."""
    deliv_rows: List[Dict[str, Any]] = []
    inn_meta_rows: List[Dict[str, Any]] = []

    for inn_idx, inn_obj in enumerate(doc.get("innings", []), start=1):
        if inn_obj.get("super_over", False) or inn_idx > 2:
            continue
        bat_team = inn_obj.get("team", "")
        pen = inn_obj.get("penalty_runs", {}) or {}
        pen_pre = int(pen.get("pre", 0) or 0)
        pen_post = int(pen.get("post", 0) or 0)
        target_obj = inn_obj.get("target", {}) or {}
        cs_target_runs = target_obj.get("runs", np.nan)
        cs_target_overs = target_obj.get("overs", np.nan)

        event_idx = 0
        for over_obj in inn_obj.get("overs", []):
            over_zero = int(over_obj.get("over", 0))
            for d_obj in over_obj.get("deliveries", []):
                runs_obj = d_obj.get("runs", {}) or {}
                ext_obj = d_obj.get("extras", {}) or {}
                wkts_list = d_obj.get("wickets", []) or []

                batter_runs = int(runs_obj.get("batter", 0) or 0)
                total_extras = int(runs_obj.get("extras", 0) or 0)
                total_runs = int(runs_obj.get("total", 0) or 0)

                wides = int(ext_obj.get("wides", 0) or 0)
                noballs = int(ext_obj.get("noballs", 0) or 0)
                byes = int(ext_obj.get("byes", 0) or 0)
                legbyes = int(ext_obj.get("legbyes", 0) or 0)
                del_penalty = int(ext_obj.get("penalty", 0) or 0)

                is_wkt = len(wkts_list) > 0
                wkt_kind = str(wkts_list[0].get("kind", "")) if is_wkt else ""
                wkt_player = str(wkts_list[0].get("player_out", "")) if is_wkt else ""

                deliv_rows.append(
                    {
                        "cs_match_id": cs_match_id,
                        "innings": inn_idx,
                        "event_index_in_innings": event_idx,
                        "cs_overid": over_zero + 1,
                        "cs_batting_team": bat_team,
                        "cs_batter": d_obj.get("batter", ""),
                        "cs_non_striker": d_obj.get("non_striker", ""),
                        "cs_bowler": d_obj.get("bowler", ""),
                        "cs_batter_runs": batter_runs,
                        "cs_total_extras": total_extras,
                        "cs_wides": wides,
                        "cs_noballs": noballs,
                        "cs_byes": byes,
                        "cs_legbyes": legbyes,
                        "cs_delivery_penalty": del_penalty,
                        "cs_total_runs": total_runs,
                        "cs_is_wicket": is_wkt,
                        "cs_wicket_kind": wkt_kind,
                        "cs_player_out": wkt_player,
                        "cs_runs_sum_ok": (total_runs == batter_runs + total_extras),
                        "cs_extras_sum_ok": (total_extras == wides + noballs + byes + legbyes + del_penalty),
                    }
                )
                event_idx += 1

        inn_meta_rows.append(
            {
                "cs_match_id": cs_match_id,
                "innings": inn_idx,
                "cs_batting_team": bat_team,
                "cs_n_deliveries": event_idx,
                "cs_penalty_pre": pen_pre,
                "cs_penalty_post": pen_post,
                "cs_target_runs": float(cs_target_runs) if pd.notna(cs_target_runs) else np.nan,
                "cs_target_overs": float(cs_target_overs) if pd.notna(cs_target_overs) else np.nan,
            }
        )

    return pd.DataFrame(deliv_rows), pd.DataFrame(inn_meta_rows)


def run_track_a_cricsheet_ingestion(
    cfg: V44Config = DEFAULT_V44_CONFIG,
    force_download: bool = False,
) -> Dict[str, Any]:
    """
    Execute Track A:
      1) Download & verify Cricsheet IPL + Men's T20I JSONs
      2) Strict 1-to-1 match crosswalk (never forcing ambiguous joins)
      3) Ordered event-index delivery crosswalk & numeric extras extraction
      4) Scorecard & extras reconciliation audit
    """
    cfg.ensure_dirs()
    prov = download_cricsheet_zips(cfg, force=force_download)

    matches = pd.read_csv(cfg.data_dir / "matches_ipl_t20i.csv")
    bbb = pd.read_csv(
        cfg.data_dir / "ball_by_ball_ipl_t20i.csv",
        dtype=BBB_DTYPE_OVERRIDES,
        low_memory=False,
    )
    adapter = RRDataAdapter(quarantine_unknown_extras=True)
    cleaned = adapter.transform_deliveries(bbb)
    reg, _ = adapter.separate_cohorts(cleaned)
    reg = reg.sort_values(["match_id", "innings", "overid", "over_ball_num", "innings_ball_num"]).reset_index(drop=True)
    reg["event_index_in_innings"] = reg.groupby(["match_id", "innings"]).cumcount()

    zip_paths = [
        ("ipl_json", cfg.cricsheet_dir / "ipl_json.zip"),
        ("t20s_male_json", cfg.cricsheet_dir / "t20s_male_json.zip"),
    ]
    cs_records, file_loc = _load_cricsheet_index(zip_paths)
    cs_idx = pd.DataFrame(cs_records)

    # Index Cricsheet by (date, team_pair)
    by_key: Dict[Tuple[str, frozenset], List[Dict[str, Any]]] = {}
    for rec in cs_records:
        key = (rec["cs_date"], rec["cs_team_pair"])
        by_key.setdefault(key, []).append(rec)

    matches["match_date_str"] = pd.to_datetime(matches["match_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    matches["is_dl"] = matches["result"].fillna("").str.contains("D/L|DLS", case=False, regex=True)

    cw_rows: List[Dict[str, Any]] = []
    unmatched_rows: List[Dict[str, Any]] = []
    ambiguous_rows: List[Dict[str, Any]] = []
    matched_cs_ids: set = set()

    for _, m in matches.iterrows():
        mid = int(m["match_id"])
        m_date = str(m["match_date_str"])
        pair = frozenset([_norm_team(m["home_team"]), _norm_team(m["away_team"])])
        cands = by_key.get((m_date, pair), [])

        if len(cands) == 1:
            c = cands[0]
            if c["cs_match_id"] in matched_cs_ids:
                status = "AMBIGUOUS_DUPLICATE_CS_TARGET"
                ambiguous_rows.append({"match_id": mid, "match_date": m_date, "home_team": m["home_team"], "away_team": m["away_team"], "n_candidates": 1, "candidate_cs_ids": c["cs_match_id"], "reason": "cs_match_id_already_claimed"})
            else:
                matched_cs_ids.add(c["cs_match_id"])
                status = "EXACT_MATCH"
                cw_rows.append(
                    {
                        "match_id": mid,
                        "cs_match_id": c["cs_match_id"],
                        "cs_source": c["cs_source"],
                        "match_date": m_date,
                        "match_format": m["match_format"],
                        "home_team": m["home_team"],
                        "away_team": m["away_team"],
                        "cs_venue": c["cs_venue"],
                        "cs_event": c["cs_event"],
                        "join_status": status,
                    }
                )
                continue
        elif len(cands) > 1:
            ambiguous_rows.append(
                {
                    "match_id": mid,
                    "match_date": m_date,
                    "home_team": m["home_team"],
                    "away_team": m["away_team"],
                    "n_candidates": len(cands),
                    "candidate_cs_ids": ",".join(x["cs_match_id"] for x in cands),
                    "reason": "multiple_cricsheet_matches_same_date_and_teams",
                }
            )
            status = "AMBIGUOUS_MATCH"
        else:
            unmatched_rows.append(
                {
                    "match_id": mid,
                    "match_date": m_date,
                    "match_format": m["match_format"],
                    "home_team": m["home_team"],
                    "away_team": m["away_team"],
                    "result": m["result"],
                    "reason": "no_exact_date_and_team_pair_in_cricsheet",
                }
            )
            status = "MISSING_MATCH"

        cw_rows.append(
            {
                "match_id": mid,
                "cs_match_id": "",
                "cs_source": "",
                "match_date": m_date,
                "match_format": m["match_format"],
                "home_team": m["home_team"],
                "away_team": m["away_team"],
                "cs_venue": "",
                "cs_event": "",
                "join_status": status,
            }
        )

    match_cw = pd.DataFrame(cw_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)
    ambiguous_df = pd.DataFrame(ambiguous_rows)

    match_cw.to_csv(cfg.output_dir / "V4_4_MATCH_CROSSWALK.csv", index=False)
    unmatched_df.to_csv(cfg.output_dir / "V4_4_UNMATCHED_MATCHES.csv", index=False)
    ambiguous_df.to_csv(cfg.output_dir / "V4_4_AMBIGUOUS_MATCHES.csv", index=False)

    # Extract deliveries for all EXACT_MATCH matches
    exact_cw = match_cw[match_cw["join_status"] == "EXACT_MATCH"].copy()
    all_cs_deliv: List[pd.DataFrame] = []
    all_cs_inn: List[pd.DataFrame] = []

    open_zips: Dict[Path, zipfile.ZipFile] = {}
    try:
        for _, r in exact_cw.iterrows():
            cs_id = r["cs_match_id"]
            mid = int(r["match_id"])
            zp, member = file_loc[cs_id]
            if zp not in open_zips:
                open_zips[zp] = zipfile.ZipFile(zp, "r")
            with open_zips[zp].open(member) as f:
                doc = json.load(f)
            d_df, i_df = _extract_cs_deliveries(doc, cs_id)
            if len(d_df) > 0:
                d_df["match_id"] = mid
                all_cs_deliv.append(d_df)
            if len(i_df) > 0:
                i_df["match_id"] = mid
                all_cs_inn.append(i_df)
    finally:
        for zf in open_zips.values():
            zf.close()

    cs_deliv_df = pd.concat(all_cs_deliv, ignore_index=True) if all_cs_deliv else pd.DataFrame()
    cs_inn_df = pd.concat(all_cs_inn, ignore_index=True) if all_cs_inn else pd.DataFrame()

    # Merge regular deliveries with Cricsheet deliveries on (match_id, innings, event_index_in_innings)
    reg_joined = reg.merge(
        cs_deliv_df,
        on=["match_id", "innings", "event_index_in_innings"],
        how="left",
    )

    # Check per-(match_id, innings) reconciliation
    reg_inn = reg.groupby(["match_id", "innings"], as_index=False).agg(
        repo_deliveries=("batter_runs", "size"),
        repo_legal_balls=("is_legal_ball", "sum"),
        repo_batter_runs=("batter_runs", "sum"),
        repo_wickets=("is_wicket", "sum"),
    )
    cs_inn_agg = (
        cs_deliv_df.groupby(["match_id", "innings"], as_index=False).agg(
            cs_deliveries=("cs_total_runs", "size"),
            cs_batter_runs=("cs_batter_runs", "sum"),
            cs_total_extras=("cs_total_extras", "sum"),
            cs_wides=("cs_wides", "sum"),
            cs_noballs=("cs_noballs", "sum"),
            cs_byes=("cs_byes", "sum"),
            cs_legbyes=("cs_legbyes", "sum"),
            cs_delivery_penalty=("cs_delivery_penalty", "sum"),
            cs_total_runs=("cs_total_runs", "sum"),
            cs_wickets=("cs_is_wicket", "sum"),
            cs_runs_sum_ok_all=("cs_runs_sum_ok", "all"),
            cs_extras_sum_ok_all=("cs_extras_sum_ok", "all"),
        )
        if len(cs_deliv_df) > 0
        else pd.DataFrame()
    )

    # Check delivery-level batter_runs & overid agreement on joined rows
    joined_only = reg_joined[reg_joined["cs_match_id"].notna()].copy()
    joined_only["deliv_batter_runs_match"] = joined_only["batter_runs"] == joined_only["cs_batter_runs"]
    joined_only["deliv_over_match"] = joined_only["overid"] == joined_only["cs_overid"]
    joined_only["deliv_wkt_match"] = (joined_only["is_wicket"] == True) == joined_only["cs_is_wicket"]

    deliv_agree = joined_only.groupby(["match_id", "innings"], as_index=False).agg(
        all_batter_runs_match=("deliv_batter_runs_match", "all"),
        all_over_match=("deliv_over_match", "all"),
        all_wicket_match=("deliv_wkt_match", "all"),
    )

    rec = (
        reg_inn.merge(match_cw[["match_id", "cs_match_id", "join_status"]], on="match_id", how="left")
        .merge(matches[["match_id", "match_date", "match_format", "is_dl", "revised_target", "result"]], on="match_id", how="left")
        .merge(cs_inn_df[["match_id", "innings", "cs_penalty_pre", "cs_penalty_post", "cs_target_runs", "cs_target_overs"]], on=["match_id", "innings"], how="left")
        .merge(cs_inn_agg, on=["match_id", "innings"], how="left")
        .merge(deliv_agree, on=["match_id", "innings"], how="left")
    )

    rec["cs_innings_total_with_penalties"] = (
        rec["cs_total_runs"] + rec["cs_penalty_pre"].fillna(0) + rec["cs_penalty_post"].fillna(0)
    )
    rec["counts_match"] = rec["repo_deliveries"] == rec["cs_deliveries"]
    rec["batter_runs_total_match"] = rec["repo_batter_runs"] == rec["cs_batter_runs"]
    rec["wickets_match"] = rec["repo_wickets"] == rec["cs_wickets"]

    is_exact_ok = (
        (rec["join_status"] == "EXACT_MATCH")
        & rec["counts_match"].fillna(False)
        & rec["batter_runs_total_match"].fillna(False)
        & rec["all_batter_runs_match"].fillna(False)
        & rec["all_over_match"].fillna(False)
        & rec["cs_runs_sum_ok_all"].fillna(False)
        & rec["cs_extras_sum_ok_all"].fillna(False)
    )
    rec["reconciliation_status"] = np.where(
        is_exact_ok & rec["is_dl"].fillna(False),
        "VERIFIED_DLS_CRICSHEET_EXACT",
        np.where(
            is_exact_ok,
            "VERIFIED_CRICSHEET_EXACT",
            np.where(
                rec["join_status"] != "EXACT_MATCH",
                "UNVERIFIED_" + rec["join_status"].astype(str),
                "UNVERIFIED_DELIVERY_OR_SCORE_MISMATCH",
            ),
        ),
    )
    rec["score_verified"] = rec["reconciliation_status"].isin(
        ["VERIFIED_CRICSHEET_EXACT", "VERIFIED_DLS_CRICSHEET_EXACT"]
    )

    # Save reconciliation & audit tables
    rec.to_csv(cfg.output_dir / "V4_4_EXTRAS_RECONCILIATION.csv", index=False)
    rec[
        [
            "match_id",
            "innings",
            "cs_match_id",
            "match_date",
            "match_format",
            "is_dl",
            "repo_deliveries",
            "cs_deliveries",
            "repo_legal_balls",
            "repo_batter_runs",
            "cs_batter_runs",
            "cs_total_extras",
            "cs_penalty_pre",
            "cs_penalty_post",
            "cs_innings_total_with_penalties",
            "cs_target_runs",
            "revised_target",
            "reconciliation_status",
            "score_verified",
        ]
    ].to_csv(cfg.output_dir / "V4_4_SCORECARD_RECONSTRUCTION_AUDIT.csv", index=False)

    # Save compact delivery crosswalk parquet + summary CSV
    cw_deliv_cols = [
        "match_id",
        "innings",
        "event_index_in_innings",
        "cs_match_id",
        "overid",
        "cs_overid",
        "striker_id",
        "striker_name",
        "cs_batter",
        "bowler_id",
        "bowler_name",
        "cs_bowler",
        "batter_runs",
        "cs_batter_runs",
        "cs_total_extras",
        "cs_wides",
        "cs_noballs",
        "cs_byes",
        "cs_legbyes",
        "cs_delivery_penalty",
        "cs_total_runs",
        "cs_runs_sum_ok",
        "cs_extras_sum_ok",
    ]
    reg_joined[cw_deliv_cols].to_parquet(cfg.output_dir / "V4_4_DELIVERY_CROSSWALK.parquet", index=False)
    reg_joined[cw_deliv_cols].head(500).to_csv(cfg.output_dir / "V4_4_DELIVERY_CROSSWALK.csv", index=False)

    # Attach verified innings flag & save full enriched regular deliveries parquet
    reg_enriched = reg_joined.merge(
        rec[["match_id", "innings", "reconciliation_status", "score_verified", "cs_penalty_pre", "cs_penalty_post", "cs_target_runs"]],
        on=["match_id", "innings"],
        how="left",
    )
    reg_enriched.to_parquet(cfg.artifacts_dir / "v4_4_regular_deliveries_enriched.parquet", index=False)

    prov["cricsheet_matches_indexed_window"] = int(len(cs_idx))
    prov["match_join_counts"] = match_cw["join_status"].value_counts().to_dict()
    prov["innings_reconciliation_counts"] = rec["reconciliation_status"].value_counts().to_dict()
    prov["verified_innings"] = int(rec["score_verified"].sum())
    prov["total_regular_innings"] = int(len(rec))
    (cfg.output_dir / "V4_4_SOURCE_PROVENANCE.json").write_text(
        json.dumps(prov, indent=2), encoding="utf-8"
    )
    return {
        "provenance": prov,
        "match_cw": match_cw,
        "rec": rec,
        "reg_enriched": reg_enriched,
    }
