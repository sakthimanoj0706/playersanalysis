"""CSV loading with validation for SupeRR Intelligence platform."""
import json
import logging
from typing import Dict

import pandas as pd

from src.config import (
    BALL_BY_BALL_CSV, MATCHES_CSV, PLAYING_ELEVEN_CSV,
    MAPPING_CSV, COMPETITIONS_CSV, TEAMS_CSV,
    VALIDATION_COUNTS_JSON, BBB_DTYPE_OVERRIDES,
)

logger = logging.getLogger(__name__)

# Files and their dict keys
_FILE_MAP = {
    'ball_by_ball': BALL_BY_BALL_CSV,
    'matches': MATCHES_CSV,
    'playing_eleven': PLAYING_ELEVEN_CSV,
    'mapping': MAPPING_CSV,
    'competitions': COMPETITIONS_CSV,
    'teams': TEAMS_CSV,
}

# Expected row counts from VALIDATION_COUNTS.json (key mapping)
_VALIDATION_KEY_MAP = {
    'ball_by_ball': 'balls',
    'matches': 'matches',
    'playing_eleven': 'playing_eleven',
    'mapping': 'mapping',
    'competitions': 'competitions',
    'teams': 'teams',
}


def _validate_files_exist() -> None:
    """Raise FileNotFoundError if any source CSV is missing."""
    missing = [name for name, path in _FILE_MAP.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing source files: {', '.join(missing)}"
        )


def _validate_row_counts(
    dataframes: Dict[str, pd.DataFrame],
) -> Dict[str, dict]:
    """Compare loaded row counts against VALIDATION_COUNTS.json.

    Returns a dict per table: {expected, actual, match}.
    """
    if not VALIDATION_COUNTS_JSON.exists():
        logger.warning("VALIDATION_COUNTS.json not found; skipping row count validation.")
        return {}

    with open(VALIDATION_COUNTS_JSON, 'r') as f:
        expected = json.load(f)

    results = {}
    for key, df in dataframes.items():
        vc_key = _VALIDATION_KEY_MAP.get(key)
        if vc_key and vc_key in expected:
            exp = expected[vc_key]
            act = len(df)
            ok = exp == act
            results[key] = {'expected': exp, 'actual': act, 'match': ok}
            if not ok:
                logger.warning(
                    "Row count mismatch for %s: expected %d, got %d",
                    key, exp, act,
                )
            else:
                logger.info("Row count OK for %s: %d", key, act)
    return results


def load_all_data() -> Dict[str, pd.DataFrame]:
    """Load all 6 source CSVs and return as a dict of DataFrames.

    Keys: ball_by_ball, matches, playing_eleven, mapping, competitions, teams.

    Applies:
    - File existence validation
    - Explicit dtype for column 36 (season) to suppress DtypeWarning
    - Date parsing for match_date columns
    - Row count validation against VALIDATION_COUNTS.json
    """
    _validate_files_exist()

    dataframes: Dict[str, pd.DataFrame] = {}

    # ── ball_by_ball (largest table, needs dtype override) ────────────
    dataframes['ball_by_ball'] = pd.read_csv(
        BALL_BY_BALL_CSV,
        dtype=BBB_DTYPE_OVERRIDES,
    )

    # ── matches (parse match_date) ───────────────────────────────────
    dataframes['matches'] = pd.read_csv(MATCHES_CSV)
    dataframes['matches']['match_date'] = pd.to_datetime(
        dataframes['matches']['match_date'], dayfirst=True, errors='coerce',
    )

    # ── playing_eleven ───────────────────────────────────────────────
    dataframes['playing_eleven'] = pd.read_csv(PLAYING_ELEVEN_CSV)

    # ── mapping ──────────────────────────────────────────────────────
    dataframes['mapping'] = pd.read_csv(MAPPING_CSV)

    # ── competitions ─────────────────────────────────────────────────
    dataframes['competitions'] = pd.read_csv(COMPETITIONS_CSV)

    # ── teams ────────────────────────────────────────────────────────
    dataframes['teams'] = pd.read_csv(TEAMS_CSV)

    # ── Parse match_date in ball_by_ball if present ──────────────────
    if 'match_date' in dataframes['ball_by_ball'].columns:
        dataframes['ball_by_ball']['match_date'] = pd.to_datetime(
            dataframes['ball_by_ball']['match_date'],
            dayfirst=True, errors='coerce',
        )

    # ── Validate row counts ──────────────────────────────────────────
    validation = _validate_row_counts(dataframes)
    dataframes['_validation'] = validation  # attach for callers to inspect

    logger.info(
        "Loaded %d tables. Row counts: %s",
        len(dataframes) - 1,
        {k: len(v) for k, v in dataframes.items() if k != '_validation'},
    )

    return dataframes
