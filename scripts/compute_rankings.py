"""Compute dual pressure classifications, player roles, dual leaderboards, and sensitivity analysis."""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from src.config import FEATURES_DIR, OUTPUTS_DIR, REPORTS_DIR, DATA_DIR, BALL_BY_BALL_CSV, PLAYING_ELEVEN_CSV, MAPPING_CSV
from src.classification.role_classifier import build_player_name_aliases, classify_player_roles
from src.pressure_engine.pressure_model import classify_dual_pressure, get_tier_breakdown
from src.ranking_engine.pressure_rankings import (
    rank_batters_comprehensive,
    rank_bowlers_comprehensive,
    get_lower_order_pressure_batters,
    get_emerging_and_part_time_bowlers,
    SENSITIVITY_CONFIGS,
    BOWL_PRIMARY_MIN_CRISIS,
)

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

print("1. Loading context data...")
df = pd.read_parquet(FEATURES_DIR / 'ball_by_ball_with_context.parquet')
print(f"Loaded {len(df)} deliveries with {len(df.columns)} columns")

# ── Phase 4: Dual Pressure Classification ──────────────────────────────────
print("\n=== PHASE 4: DUAL PRESSURE CLASSIFICATION ===")
df = classify_dual_pressure(df)

# Save master pressure dataset
df.to_parquet(FEATURES_DIR / 'ball_by_ball_with_pressure.parquet', index=False)
print(f"Saved master ball_by_ball_with_pressure.parquet ({len(df)} rows)")

# Save dedicated batting pressure feature dataset
bat_cols = [c for c in df.columns if 'bat' in c or 'striker' in c or c in [
    'match_id', 'innings', 'overid', 'innings_ball_num', 'runs', 'is_wicket',
    'wickets_fallen_before', 'is_pressure_delivery', 'pressure_score'
]]
df[bat_cols].to_parquet(FEATURES_DIR / 'batting_pressure_features.parquet', index=False)

# Save dedicated bowling pressure feature dataset
bowl_cols = [c for c in df.columns if 'bowl' in c or c in [
    'match_id', 'innings', 'overid', 'innings_ball_num', 'runs', 'is_wicket',
    'batting_wickets_remaining', 'boundaries_in_last_12_legal_balls', 'dots_in_last_12_legal_balls',
    'is_legal_ball', 'is_bowler_wicket'
]]
df[bowl_cols].to_parquet(FEATURES_DIR / 'bowling_pressure_features.parquet', index=False)
print("Saved batting_pressure_features.parquet and bowling_pressure_features.parquet")

# Pressure tier breakdowns
bat_summary = get_tier_breakdown(df, 'batting_pressure_tier')
bowl_summary = get_tier_breakdown(df, 'bowling_pressure_tier')

print("\n--- Batting Crisis Pressure Distribution ---")
print(bat_summary.to_string(index=False))

print("\n--- Bowling Defensive Pressure Distribution ---")
print(bowl_summary.to_string(index=False))

# Save validation summary
val_summary = pd.concat([
    bat_summary.assign(model='Batting Crisis Proxy'),
    bowl_summary.assign(model='Bowling Defensive Proxy')
], ignore_index=True)
val_summary.to_csv(OUTPUTS_DIR / 'PRESSURE_MODEL_VALIDATION.csv', index=False)
val_summary.to_csv(PROJECT_ROOT / 'PRESSURE_MODEL_VALIDATION.csv', index=False)

# ── Role Classification & Canonical Name Standardization ───────────────────
print("\n=== BUILDING ROLE CLASSIFICATION & CANONICAL ALIASES ===")
p11_df = pd.read_csv(PLAYING_ELEVEN_CSV)
map_df = pd.read_csv(MAPPING_CSV)

aliases_df = build_player_name_aliases(map_df, df)
roles_df = classify_player_roles(p11_df, df, aliases_df)

aliases_df.to_csv(OUTPUTS_DIR / 'PLAYER_NAME_ALIASES.csv', index=False)
aliases_df.to_csv(PROJECT_ROOT / 'PLAYER_NAME_ALIASES.csv', index=False)
roles_df.to_csv(OUTPUTS_DIR / 'PLAYER_ROLE_CLASSIFICATION.csv', index=False)
roles_df.to_csv(PROJECT_ROOT / 'PLAYER_ROLE_CLASSIFICATION.csv', index=False)
print(f"Generated {len(aliases_df)} player name aliases and {len(roles_df)} role classifications.")

# ── Phase 5: Player Rankings ───────────────────────────────────────────────
print("\n=== PHASE 5: COMPREHENSIVE BATTING RANKINGS ===")
all_batters, top10_batters = rank_batters_comprehensive(df, role_df=roles_df)
lower_order_batters = get_lower_order_pressure_batters(all_batters)

print(f"Total Batters Evaluated: {len(all_batters)}")
print(f"Eligible Batters: {(all_batters['eligibility_status'] == 'ELIGIBLE').sum()}")
print(f"Primary Top 10 Batters Qualified: {len(top10_batters)}")
print(f"Lower-Order Pressure Impact Batters: {len(lower_order_batters)}")

# Export Batting Rankings
all_batters.to_csv(OUTPUTS_DIR / 'ALL_BATTER_RANKINGS.csv', index=False)
all_batters.to_csv(PROJECT_ROOT / 'ALL_BATTER_RANKINGS.csv', index=False)
all_batters.to_csv(OUTPUTS_DIR / 'all_batter_rankings.csv', index=False)
all_batters.to_parquet(OUTPUTS_DIR / 'batting_pressure_rankings.parquet', index=False)
all_batters.to_csv(OUTPUTS_DIR / 'batting_pressure_rankings.csv', index=False)

top10_batters.to_csv(OUTPUTS_DIR / 'FINAL_TOP_10_BATTERS.csv', index=False)
top10_batters.to_csv(PROJECT_ROOT / 'FINAL_TOP_10_BATTERS.csv', index=False)
top10_batters.to_csv(OUTPUTS_DIR / 'top_10_batters.csv', index=False)

lower_order_batters.to_csv(OUTPUTS_DIR / 'LOWER_ORDER_PRESSURE_IMPACT.csv', index=False)
lower_order_batters.to_csv(PROJECT_ROOT / 'LOWER_ORDER_PRESSURE_IMPACT.csv', index=False)

print("\n=== FINAL PRIMARY TOP 10 BATTERS UNDER PRESSURE (POSITIONS 1-7) ===")
bat_display_cols = ['rank', 'canonical_display_name', 'primary_role', 'modal_batting_position',
                    'crisis_balls', 'crisis_matches', 'crisis_sr', 'norm_sr', 'sr_maintenance',
                    'consistency_score', 'batting_pri']
print(top10_batters[bat_display_cols].to_string(index=False))

print("\n=== TOP 5 LOWER-ORDER PRESSURE IMPACT BATTERS ===")
low_display_cols = ['lower_order_rank', 'canonical_display_name', 'primary_role', 'modal_batting_position',
                    'crisis_balls', 'crisis_sr', 'batting_pri', 'eligibility_status']
print(lower_order_batters[low_display_cols].head(5).to_string(index=False))


print("\n\n=== PHASE 5: COMPREHENSIVE BOWLING RANKINGS ===")
all_bowlers, top10_bowlers = rank_bowlers_comprehensive(df, role_df=roles_df)
emerging_bowlers = get_emerging_and_part_time_bowlers(all_bowlers)

print(f"Total Bowlers Evaluated: {len(all_bowlers)}")
print(f"Eligible Bowlers: {(all_bowlers['eligibility_status'] == 'ELIGIBLE').sum()}")
print(f"Primary Top 10 Bowlers Qualified (min {BOWL_PRIMARY_MIN_CRISIS} balls): {len(top10_bowlers)}")
print(f"Emerging & Part-Time Bowlers: {len(emerging_bowlers)}")

# Export Bowling Rankings
all_bowlers.to_csv(OUTPUTS_DIR / 'ALL_BOWLER_RANKINGS.csv', index=False)
all_bowlers.to_csv(PROJECT_ROOT / 'ALL_BOWLER_RANKINGS.csv', index=False)
all_bowlers.to_csv(OUTPUTS_DIR / 'all_bowler_rankings.csv', index=False)
all_bowlers.to_parquet(OUTPUTS_DIR / 'bowling_pressure_rankings.parquet', index=False)
all_bowlers.to_csv(OUTPUTS_DIR / 'bowling_pressure_rankings.csv', index=False)

top10_bowlers.to_csv(OUTPUTS_DIR / 'FINAL_TOP_10_BOWLERS.csv', index=False)
top10_bowlers.to_csv(PROJECT_ROOT / 'FINAL_TOP_10_BOWLERS.csv', index=False)
top10_bowlers.to_csv(OUTPUTS_DIR / 'top_10_bowlers.csv', index=False)

emerging_bowlers.to_csv(OUTPUTS_DIR / 'EMERGING_AND_PART_TIME_BOWLERS.csv', index=False)
emerging_bowlers.to_csv(PROJECT_ROOT / 'EMERGING_AND_PART_TIME_BOWLERS.csv', index=False)

print("\n=== FINAL PRIMARY TOP 10 BOWLERS UNDER DEFENSIVE PRESSURE ===")
bowl_display_cols = ['rank', 'canonical_display_name', 'primary_role', 'crisis_balls',
                     'crisis_matches', 'crisis_wicket_rate', 'norm_wicket_rate', 'crisis_dot_pct',
                     'consistency_score', 'bowling_pri']
print(top10_bowlers[bowl_display_cols].to_string(index=False))

print("\n=== TOP 5 EMERGING & PART-TIME BOWLERS UNDER PRESSURE ===")
em_display_cols = ['emerging_rank', 'canonical_display_name', 'primary_role', 'crisis_balls',
                   'crisis_wicket_rate', 'bowling_pri']
print(emerging_bowlers[em_display_cols].head(5).to_string(index=False))


# ── Eligibility & Audit Reports ────────────────────────────────────────────
def get_exclusion_reason(row, min_crisis=40, min_total=120, min_matches=5, min_norm=30):
    if row['eligibility_status'] == 'ELIGIBLE':
        return 'None (Meets all sample criteria)'
    reasons = []
    if row['crisis_balls'] < min_crisis:
        reasons.append(f"Crisis balls {int(row['crisis_balls'])} < {min_crisis}")
    if row['total_balls'] < min_total:
        reasons.append(f"Total balls {int(row['total_balls'])} < {min_total}")
    if row['crisis_matches'] < min_matches:
        reasons.append(f"Crisis matches {int(row['crisis_matches'])} < {min_matches}")
    if row['norm_balls'] < min_norm:
        reasons.append(f"Normal balls {int(row['norm_balls'])} < {min_norm}")
    return "; ".join(reasons) if reasons else "Sample below confidence threshold"

bat_elig = all_batters[['striker_id', 'canonical_display_name', 'primary_role', 'total_balls',
                        'crisis_balls', 'crisis_matches', 'norm_balls', 'eligibility_status']].rename(
    columns={'striker_id': 'player_id', 'canonical_display_name': 'player_name', 'primary_role': 'player_role'}
).assign(discipline='Batting')
bat_elig['exclusion_reason'] = bat_elig.apply(get_exclusion_reason, axis=1)

bowl_elig = all_bowlers[['bowler_id', 'canonical_display_name', 'primary_role', 'total_legal_balls',
                         'crisis_balls', 'crisis_matches', 'norm_balls', 'eligibility_status']].rename(
    columns={'bowler_id': 'player_id', 'canonical_display_name': 'player_name', 'primary_role': 'player_role', 'total_legal_balls': 'total_balls'}
).assign(discipline='Bowling')
bowl_elig['exclusion_reason'] = bowl_elig.apply(get_exclusion_reason, axis=1)

eligibility_report = pd.concat([bat_elig, bowl_elig], ignore_index=True)
eligibility_report.to_csv(OUTPUTS_DIR / 'PLAYER_ELIGIBILITY_REPORT.csv', index=False)
eligibility_report.to_csv(PROJECT_ROOT / 'PLAYER_ELIGIBILITY_REPORT.csv', index=False)
eligibility_report.to_csv(OUTPUTS_DIR / 'player_eligibility_report.csv', index=False)

# Export PRI Details
all_batters.to_csv(OUTPUTS_DIR / 'batting_pri_details.csv', index=False)
all_batters.to_csv(PROJECT_ROOT / 'batting_pri_details.csv', index=False)
all_bowlers.to_csv(OUTPUTS_DIR / 'bowling_pri_details.csv', index=False)
all_bowlers.to_csv(PROJECT_ROOT / 'bowling_pri_details.csv', index=False)

# Export Pressure Distribution Report
val_summary.to_csv(OUTPUTS_DIR / 'pressure_distribution_report.csv', index=False)
val_summary.to_csv(PROJECT_ROOT / 'pressure_distribution_report.csv', index=False)

# PRI Component Analysis
pri_components = pd.concat([
    top10_batters[['rank', 'canonical_display_name', 'primary_role', 'norm_maint', 'norm_abs', 'norm_cons', 'norm_sample', 'batting_pri']].rename(
        columns={'canonical_display_name': 'player_name', 'primary_role': 'player_role', 'batting_pri': 'pri'}
    ).assign(discipline='Batting'),
    top10_bowlers[['rank', 'canonical_display_name', 'primary_role', 'norm_maint', 'norm_abs', 'norm_cons', 'norm_sample', 'bowling_pri']].rename(
        columns={'canonical_display_name': 'player_name', 'primary_role': 'player_role', 'bowling_pri': 'pri'}
    ).assign(discipline='Bowling'),
], ignore_index=True)
pri_components.to_csv(OUTPUTS_DIR / 'pri_component_analysis.csv', index=False)

# Consistency Analysis
consistency_df = pd.concat([
    all_batters[all_batters['eligibility_status'] == 'ELIGIBLE'][['canonical_display_name', 'primary_role', 'total_matches', 'crisis_matches', 'mean_match_sr', 'cv', 'consistency_score']].rename(
        columns={'canonical_display_name': 'player_name', 'primary_role': 'player_role', 'mean_match_sr': 'mean_performance'}
    ).assign(discipline='Batting'),
    all_bowlers[all_bowlers['eligibility_status'] == 'ELIGIBLE'][['canonical_display_name', 'primary_role', 'total_matches', 'crisis_matches', 'mean_control', 'cv', 'consistency_score']].rename(
        columns={'canonical_display_name': 'player_name', 'primary_role': 'player_role', 'mean_control': 'mean_performance'}
    ).assign(discipline='Bowling'),
], ignore_index=True)
consistency_df.to_csv(OUTPUTS_DIR / 'match_consistency_analysis.csv', index=False)

# PRI Sensitivity Analysis across configs
sens_cols = ['canonical_display_name', 'primary_role'] + [f'pri_{cfg}' for cfg in SENSITIVITY_CONFIGS.keys()]
bat_sens = top10_batters[sens_cols].rename(columns={'canonical_display_name': 'player_name', 'primary_role': 'player_role'}).assign(discipline='Batting')
bowl_sens = top10_bowlers[sens_cols].rename(columns={'canonical_display_name': 'player_name', 'primary_role': 'player_role'}).assign(discipline='Bowling')
pri_sensitivity = pd.concat([bat_sens, bowl_sens], ignore_index=True)
pri_sensitivity.to_csv(OUTPUTS_DIR / 'PRI_SENSITIVITY_ANALYSIS.csv', index=False)
pri_sensitivity.to_csv(PROJECT_ROOT / 'PRI_SENSITIVITY_ANALYSIS.csv', index=False)
pri_sensitivity.to_csv(OUTPUTS_DIR / 'pri_sensitivity_analysis.csv', index=False)

print("\n=== ALL RANKINGS AND DUAL LEADERBOARD REPORTS EXPORTED SUCCESSFULLY ===")
