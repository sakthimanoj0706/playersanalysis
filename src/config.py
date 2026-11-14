"""Project configuration constants for SupeRR Intelligence platform."""
from pathlib import Path

# ── Directory paths (Project-relative, fully portable) ────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
OUTPUTS_DIR = DATA_DIR / "outputs"
REPORTS_DIR = DATA_DIR / "reports"

# ── Source CSV file paths ────────────────────────────────────────────────
BALL_BY_BALL_CSV = DATA_DIR / "ball_by_ball_ipl_t20i.csv"
MATCHES_CSV = DATA_DIR / "matches_ipl_t20i.csv"
PLAYING_ELEVEN_CSV = DATA_DIR / "playing_eleven_ipl_t20i.csv"
MAPPING_CSV = DATA_DIR / "competition_team_player_mapping_ipl_t20i.csv"
COMPETITIONS_CSV = DATA_DIR / "competitions_ipl_t20i.csv"
TEAMS_CSV = DATA_DIR / "teams_ipl_t20i.csv"
VALIDATION_COUNTS_JSON = DATA_DIR / "VALIDATION_COUNTS.json"

# ── Extras type mapping (categorical codes, NOT run counts) ──────────────
EXTRAS_TYPE_MAP = {
    1: 'Overstep',
    2: 'wide',
    3: 'legbyes',
    4: 'byes',
    5: 'other',
    6: 'None',
    7: 'Penalty',
}

# ── Dismissal filtering ─────────────────────────────────────────────────
# These dismissal types must NOT be credited as bowler wickets.
# Note: source data contains both 'Obstracting the field' (typo) and
# 'Obstructing the field'; we match both variants.
NON_BOWLER_DISMISSALS = [
    'Run Out', 'RunOut',
    'Retired Out', 'Retire Out',
    'Obstructing the field', 'Obstracting the field',
]

# ── Super Over innings ──────────────────────────────────────────────────
SUPER_OVER_INNINGS = [3, 4]

# ── T20 innings phases (over ranges, inclusive) ──────────────────────────
PHASE_OVERS = {
    'powerplay': (1, 6),
    'middle': (7, 15),
    'death': (16, 20),
}

# ── Known data-quality issues ───────────────────────────────────────────
PLAYING_XI_CONFLICT_MATCHES = [13613, 21176, 28962]

# ── Column 36 (season) has mixed types; explicit dtype spec for loading ──
BBB_DTYPE_OVERRIDES = {
    'season': str,
}
