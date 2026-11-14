"""Compute all cricket intelligence stats and save to parquet."""
import sys
sys.path.insert(0, 'D:/rrhackthon')

import pandas as pd
from src.config import FEATURES_DIR, PROCESSED_DIR, DATA_DIR
from src.cricket_engine.batter_analysis import (
    compute_batter_stats, compute_batter_phase_stats, compute_batter_vs_bowling_type
)
from src.cricket_engine.bowler_analysis import (
    compute_bowler_stats, compute_bowler_phase_stats
)
from src.cricket_engine.matchup_analysis import compute_matchups
from src.cricket_engine.venue_analysis import compute_venue_stats

FEATURES_DIR.mkdir(parents=True, exist_ok=True)

print("Loading context data...")
df = pd.read_parquet(FEATURES_DIR / 'ball_by_ball_with_context.parquet')
matches = pd.read_csv(DATA_DIR / 'matches_ipl_t20i.csv')
print(f"Loaded {len(df)} deliveries")

print("\n=== BATTER STATS ===")
batter_stats = compute_batter_stats(df)
print(f"Batters with 50+ balls: {len(batter_stats)}")
batter_stats.to_parquet(FEATURES_DIR / 'batter_stats.parquet', index=False)
print("\nTop 15 by runs:")
print(batter_stats[['player_name', 'matches', 'innings', 'runs', 'balls_faced', 'strike_rate', 'average', 'boundary_pct', 'dot_pct']].head(15).to_string(index=False))

print("\n=== BATTER PHASE STATS ===")
batter_phase = compute_batter_phase_stats(df)
print(f"Batter-phase records: {len(batter_phase)}")
batter_phase.to_parquet(FEATURES_DIR / 'batter_phase_stats.parquet', index=False)

print("\n=== BATTER VS BOWLING TYPE ===")
batter_vs_type = compute_batter_vs_bowling_type(df)
print(f"Batter vs type records: {len(batter_vs_type)}")
batter_vs_type.to_parquet(FEATURES_DIR / 'batter_vs_bowling_type.parquet', index=False)

print("\n=== BOWLER STATS ===")
bowler_stats = compute_bowler_stats(df)
print(f"Bowlers with 60+ legal balls: {len(bowler_stats)}")
bowler_stats.to_parquet(FEATURES_DIR / 'bowler_stats.parquet', index=False)
print("\nTop 15 by wickets:")
print(bowler_stats[['player_name', 'matches', 'overs', 'wickets', 'bowler_strike_rate', 'dot_pct', 'provisional_economy']].head(15).to_string(index=False))

print("\n=== BOWLER PHASE STATS ===")
bowler_phase = compute_bowler_phase_stats(df)
print(f"Bowler-phase records: {len(bowler_phase)}")
bowler_phase.to_parquet(FEATURES_DIR / 'bowler_phase_stats.parquet', index=False)

print("\n=== MATCHUPS ===")
matchups = compute_matchups(df)
print(f"Matchup pairs with 6+ balls: {len(matchups)}")
matchups.to_parquet(FEATURES_DIR / 'matchups.parquet', index=False)

print("\n=== VENUE STATS ===")
venue_stats = compute_venue_stats(df, matches)
print(f"Venues: {len(venue_stats)}")
venue_stats.to_parquet(FEATURES_DIR / 'venue_stats.parquet', index=False)
print("\nTop 10 venues by matches:")
cols = ['venue_id', 'venue_country', 'matches', 'avg_innings_runs', 'pace_wicket_pct']
print(venue_stats[cols].head(10).to_string(index=False))

print("\n=== ALL CRICKET STATS SAVED ===")
