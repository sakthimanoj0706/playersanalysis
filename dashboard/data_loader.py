"""Cached data loading, safe formatting, and HTML-escaping helpers for SupeRR Intelligence."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "data/outputs/final"
V42_DIR = ROOT / "data/outputs/v4_2"
V3_DIR = ROOT / "data/outputs/v3"

NAVY = "#0B1B3D"
NAVY_MID = "#1E3A6D"
RR_PINK = "#EA1A85"
SLATE_BG = "#F8FAFC"
CARD_BORDER = "#E2E8F0"
TEXT_MAIN = "#0F172A"
TEXT_MUTED = "#475569"
TEAL_POS = "#0F766E"
AMBER_WARN = "#B45309"

BAT_MU0 = -36.124
BOWL_MU0 = -50.884


def esc(val: Any) -> str:
    """Escape dynamic text before interpolating into HTML."""
    return html.escape("" if val is None else str(val), quote=True)


def fmt_num(val: Any, fmt: str = "{:.2f}", unavailable: str = "Unavailable") -> str:
    """Format numeric value safely without ever turning NaN/None into 0."""
    if val is None or pd.isna(val):
        return unavailable
    try:
        return fmt.format(float(val))
    except (TypeError, ValueError):
        return unavailable


def fmt_int(val: Any, unavailable: str = "Unavailable") -> str:
    if val is None or pd.isna(val):
        return unavailable
    try:
        return f"{int(round(float(val))):,}"
    except (TypeError, ValueError):
        return unavailable


def initials_badge(name: str) -> str:
    parts = [p for p in str(name).strip().split() if p]
    if not parts:
        initials = "?"
    elif len(parts) == 1:
        initials = parts[0][:2].upper()
    else:
        initials = (parts[0][0] + parts[-1][0]).upper()
    return f'<span class="avatar-circle">{esc(initials)}</span>'


@st.cache_data(show_spinner=False)
def load_all_data() -> dict[str, Any]:
    """Load all authoritative V4.2, RR, and audit artifacts safely."""
    required_csvs = {
        "top_bat": FINAL_DIR / "FINAL_TOP_10_BATTERS.csv",
        "top_bowl": FINAL_DIR / "FINAL_TOP_10_BOWLERS.csv",
        "all_est": FINAL_DIR / "ALL_PLAYER_FINAL_ESTIMATES.csv",
        "rr_req": FINAL_DIR / "RR_TEAM_REQUIREMENTS.csv",
        "rr_top10": FINAL_DIR / "RR_TOP10_CANDIDATE_FIT.csv",
        "rr_outside": FINAL_DIR / "RR_BEST_OUTSIDE_TOP10_CANDIDATES.csv",
        "rr_squad": FINAL_DIR / "RR_RECOMMENDED_SQUAD.csv",
        "star_audit": ROOT / "STAR_PLAYER_ELIGIBILITY_AUDIT.csv",
        "method_cmp": ROOT / "PRESSURE_METHODOLOGY_COMPARISON.csv",
        "val_matrix": V42_DIR / "V4_2_VALIDATION_MATRIX.csv",
        "model_cmp": V42_DIR / "V4_2_MODEL_COMPARISON.csv",
        "elig_prec": V42_DIR / "V4_2_ELIGIBILITY_PRECISION_ANALYSIS.csv",
        "score_audit": V42_DIR / "V4_2_SCORE_ENRICHMENT_AUDIT.csv",
        "rr_2026_str": V3_DIR / "rr_2026_team_strengths.csv",
        "rr_2026_wk": V3_DIR / "rr_2026_team_weaknesses.csv",
        "rr_2026_contrib": V3_DIR / "rr_2026_player_contribution.csv",
    }
    sot_path = FINAL_DIR / "FINAL_RANKING_SOURCE_OF_TRUTH.json"
    if not sot_path.exists():
        raise FileNotFoundError("Authoritative source-of-truth manifest is missing.")

    data: dict[str, Any] = {"sot": json.loads(sot_path.read_text(encoding="utf-8"))}
    for key, path in required_csvs.items():
        if not path.exists():
            raise FileNotFoundError(f"Required dataset artifact '{path.name}' is missing.")
        data[key] = pd.read_csv(path)
    return data


CONFIDENCE_LABELS = {
    "HIGH": "High",
    "MODERATE": "Moderate",
    "PROVISIONAL_BOUNDARY": "Provisional (Boundary)",
}

TRADEOFF_LABELS = {
    "none": "Clean",
    "MODERATE_OR_NEUTRAL_TRADEOFF": "Neutral Tradeoff",
    "MIXED_SECONDARY_PROFILE": "Mixed Secondary",
}

POOL_LABELS = {
    "UNIVERSAL_TOP_10": "Universal Top 10",
    "OUTSIDE_TOP_10_ELIGIBLE_POOL": "Outside Top 10",
    "PRIMARY_TARGET": "Primary Target",
    "TACTICAL_FIT_TARGET": "Tactical Fit",
}

IDENTITY_LABELS = {
    "VERIFIED_INDIA_INTL": "India (Intl)",
    "IPL_DOMESTIC_POOL": "India (IPL Pool)",
    "VERIFIED_OVERSEAS_INTL": "Overseas",
    "UNCLASSIFIED": "Unclassified",
}


def humanize_code(val: Any, mapping: dict[str, str], default: str = "—") -> str:
    if val is None or pd.isna(val):
        return default
    s = str(val).strip()
    if s in mapping:
        return mapping[s]
    return s.replace("_", " ").title()


@st.cache_data(show_spinner=False)
def load_rr_scouting_enrichment() -> dict[str, Any]:
    """Load RR auction assumptions, domestic/overseas tags, and phase/matchup splits."""
    assumptions_path = ROOT / "data/reference/rr_2027_auction_assumptions.csv"
    assumptions: dict[str, str] = {}
    if assumptions_path.exists():
        adf = pd.read_csv(assumptions_path)
        assumptions = dict(zip(adf["parameter"], adf["value"]))

    from src.scouting_engine.rr_scouting import get_player_representation_metadata

    rep = get_player_representation_metadata()
    if not rep.empty:
        rep = rep[["player_id", "identity_category"]].drop_duplicates("player_id")
        # Known overseas IPL-only players without 2022-26 T20I caps (e.g., Sunil Narine, ID 781)
        rep.loc[rep["player_id"].isin([781, 161, 319, 1074]), "identity_category"] = "VERIFIED_OVERSEAS_INTL"
    else:
        rep = pd.DataFrame(columns=["player_id", "identity_category"])

    bbb_path = ROOT / "data/ball_by_ball_ipl_t20i.csv"
    bat_splits = pd.DataFrame(columns=["player_id", "pace_sr", "spin_sr"])
    bowl_splits = pd.DataFrame(columns=["player_id", "pp_econ", "mid_econ", "death_econ"])
    if bbb_path.exists():
        cols = ["innings", "overid", "striker_id", "bowler_id", "runs", "extras_type", "pace_or_spin"]
        bbb = pd.read_csv(bbb_path, usecols=cols, low_memory=False)
        reg = bbb[bbb["innings"].isin([1, 2])].copy()
        reg["is_faced"] = (reg["extras_type"] != "wide").astype(int)
        reg["is_legal"] = (~reg["extras_type"].isin(["wide", "Overstep"])).astype(int)
        reg["phase"] = reg["overid"].map(lambda o: "pp" if o <= 6 else ("mid" if o <= 15 else "death"))
        reg["pos_clean"] = reg["pace_or_spin"].astype(str).str.strip().str.lower()

        bf = reg[reg["is_faced"] == 1]
        bs = bf.groupby(["striker_id", "pos_clean"], as_index=False).agg(runs=("runs", "sum"), balls=("is_faced", "sum"))
        bs = bs[bs["balls"] >= 30]
        bs["sr"] = (100.0 * bs["runs"] / bs["balls"]).round(1)
        bp = bs.pivot(index="striker_id", columns="pos_clean", values="sr").reset_index().rename(columns={"striker_id": "player_id"})
        bat_splits = pd.DataFrame({"player_id": bp["player_id"], "pace_sr": bp.get("pace"), "spin_sr": bp.get("spin")})

        bl = reg[reg["is_legal"] == 1]
        ws = bl.groupby(["bowler_id", "phase"], as_index=False).agg(runs=("runs", "sum"), balls=("is_legal", "sum"))
        ws = ws[ws["balls"] >= 30]
        ws["econ"] = (6.0 * ws["runs"] / ws["balls"]).round(2)
        wp = ws.pivot(index="bowler_id", columns="phase", values="econ").reset_index().rename(columns={"bowler_id": "player_id"})
        bowl_splits = pd.DataFrame(
            {"player_id": wp["player_id"], "pp_econ": wp.get("pp"), "mid_econ": wp.get("mid"), "death_econ": wp.get("death")}
        )

    return {
        "assumptions": assumptions,
        "rep": rep,
        "bat_splits": bat_splits,
        "bowl_splits": bowl_splits,
    }
