"""Data cleaning and filtering for SupeRR Intelligence platform."""
import logging

import pandas as pd

from src.config import (
    EXTRAS_TYPE_MAP,
    NON_BOWLER_DISMISSALS,
    SUPER_OVER_INNINGS,
    PHASE_OVERS,
    PLAYING_XI_CONFLICT_MATCHES,
)

logger = logging.getLogger(__name__)


def filter_scope(bbb_df: pd.DataFrame, matches_df: pd.DataFrame) -> pd.DataFrame:
    """Filter ball-by-ball to IPL + T20I matches only.

    The data should already be scoped, but we verify and log.
    Uses match_format column in bbb_df (already merged from matches).
    """
    if 'match_format' in bbb_df.columns:
        valid_formats = {'T20', 'T20I'}
        mask = bbb_df['match_format'].isin(valid_formats)
        excluded = (~mask).sum()
        if excluded > 0:
            logger.warning("Excluding %d rows with non-T20/T20I format", excluded)
        return bbb_df[mask].copy()

    # Fallback: join with matches to get comp_id / match_format
    ipl_t20i_matches = matches_df[
        matches_df['match_format'].isin({'T20', 'T20I'})
    ]['match_id']
    before = len(bbb_df)
    result = bbb_df[bbb_df['match_id'].isin(ipl_t20i_matches)].copy()
    logger.info("filter_scope: %d -> %d rows", before, len(result))
    return result


def separate_super_overs(
    bbb_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into regular innings and super over deliveries.

    Returns (regular_df, super_over_df).
    """
    is_super = bbb_df['innings'].isin(SUPER_OVER_INNINGS)
    regular_df = bbb_df[~is_super].copy()
    super_over_df = bbb_df[is_super].copy()
    logger.info(
        "Separated: %d regular, %d super-over deliveries",
        len(regular_df), len(super_over_df),
    )
    return regular_df, super_over_df


def classify_extras(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Add 'extras_category' column mapping extras1_runs codes to names.

    Uses EXTRAS_TYPE_MAP. Unmapped codes become 'Unknown'.
    """
    bbb_df = bbb_df.copy()
    bbb_df['extras_category'] = bbb_df['extras1_runs'].map(EXTRAS_TYPE_MAP).fillna('Unknown')
    return bbb_df


def identify_balls_faced(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Add 'is_ball_faced' column.

    True for all deliveries except wides. No-balls (Overstep) count as faced.
    """
    bbb_df = bbb_df.copy()
    bbb_df['is_ball_faced'] = bbb_df['extras_category'] != 'wide'
    return bbb_df


def identify_legal_balls(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Add 'is_legal_ball' column.

    True for balls that are not wides and not no-balls (Overstep).
    """
    bbb_df = bbb_df.copy()
    bbb_df['is_legal_ball'] = ~bbb_df['extras_category'].isin({'wide', 'Overstep'})
    return bbb_df


def validate_boundaries(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Validate boundary flags against runs scored while preserving original fields.

    Audits the 23 known discrepancies (20 fours, 3 sixes) where runs==4/6
    occurred with false boundary flags. Adds validated boolean columns.
    """
    bbb_df = bbb_df.copy()
    if 'extras_category' in bbb_df.columns:
        bat_hit = bbb_df['extras_category'].isin({'None', 'Overstep'})
    else:
        bat_hit = pd.Series(True, index=bbb_df.index)
    bbb_df['is_four_validated'] = bbb_df['is_four'] | ((bbb_df['runs'] == 4) & bat_hit)
    bbb_df['is_six_validated'] = bbb_df['is_six'] | ((bbb_df['runs'] == 6) & bat_hit)
    bbb_df['boundary_validated'] = bbb_df['is_four_validated'] | bbb_df['is_six_validated']
    bbb_df['has_boundary_discrepancy'] = (
        (bbb_df['is_four'] != bbb_df['is_four_validated']) |
        (bbb_df['is_six'] != bbb_df['is_six_validated'])
    )
    return bbb_df


def classify_bowler_wickets(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Add 'is_bowler_wicket' column.

    True only for wickets where dismissal_type is NOT in NON_BOWLER_DISMISSALS.
    Dismissals on wides (stumpings, hit wicket) are credited to bowler, while
    run outs on wides are not.
    """
    bbb_df = bbb_df.copy()
    is_wicket = bbb_df['is_wicket'] == True  # noqa: E712
    is_non_bowler = bbb_df['dismissal_type'].isin(NON_BOWLER_DISMISSALS)
    bbb_df['is_bowler_wicket'] = is_wicket & ~is_non_bowler
    return bbb_df


def add_innings_phase(bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Add 'innings_phase' column based on overid.

    powerplay: overs 1-6, middle: overs 7-15, death: overs 16-20.
    """
    bbb_df = bbb_df.copy()

    conditions = []
    choices = []
    for phase, (start, end) in PHASE_OVERS.items():
        conditions.append(
            (bbb_df['overid'] >= start) & (bbb_df['overid'] <= end)
        )
        choices.append(phase)

    import numpy as np
    bbb_df['innings_phase'] = np.select(conditions, choices, default='unknown')
    return bbb_df


def resolve_playing_xi_conflicts(pe_df: pd.DataFrame) -> pd.DataFrame:
    """For conflict matches, keep the row with the lower batting_order.

    Deduplicates on (match_id, team_id, player_id) keeping the row
    with the smallest batting_order value.
    """
    pe_df = pe_df.copy()
    before = len(pe_df)

    # Sort by batting_order ascending, then drop duplicates keeping first
    pe_df = pe_df.sort_values('batting_order', ascending=True)
    pe_df = pe_df.drop_duplicates(
        subset=['match_id', 'team_id', 'player_id'], keep='first',
    )

    removed = before - len(pe_df)
    if removed > 0:
        logger.info(
            "Resolved playing XI conflicts: removed %d duplicate rows", removed,
        )
    return pe_df


def clean_all(
    bbb_df: pd.DataFrame, matches_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the full cleaning pipeline on ball-by-ball data.

    Returns (cleaned_regular_df, super_over_df).
    """
    logger.info("Starting cleaning pipeline on %d rows", len(bbb_df))

    # 1. Scope filter
    bbb_df = filter_scope(bbb_df, matches_df)

    # 2. Classify extras (needed before balls faced / legal balls)
    bbb_df = classify_extras(bbb_df)

    # 3. Ball-faced and legal-ball flags
    bbb_df = identify_balls_faced(bbb_df)
    bbb_df = identify_legal_balls(bbb_df)

    # 4. Boundary audit and validation
    bbb_df = validate_boundaries(bbb_df)

    # 5. Bowler wicket classification
    bbb_df = classify_bowler_wickets(bbb_df)

    # 6. Innings phase
    bbb_df = add_innings_phase(bbb_df)

    # 7. Separate super overs (last, so all flags are set on both subsets)
    regular_df, super_over_df = separate_super_overs(bbb_df)

    logger.info(
        "Cleaning complete: %d regular, %d super-over deliveries",
        len(regular_df), len(super_over_df),
    )

    return regular_df, super_over_df
