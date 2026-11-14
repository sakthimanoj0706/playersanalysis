"""Run RR squad scouting and display summary findings."""
import sys
sys.path.insert(0, 'D:/rrhackthon')

import pandas as pd
from src.config import FEATURES_DIR
from src.scouting_engine.rr_scouting import run_all_scouting

print("Loading ball_by_ball_with_pressure dataset...")
df = pd.read_parquet(FEATURES_DIR / 'ball_by_ball_with_pressure.parquet')
print(f"Loaded {len(df)} deliveries.")

results = run_all_scouting(df)

print("\n" + "="*70)
print("TOP 5 EXPLOSIVE MIDDLE-ORDER CANDIDATES (No. 4/5):")
print("="*70)
print(results['explosive_middle_order'][['player_name', 'innings', 'runs', 'balls_faced', 'strike_rate', 'boundary_pct', 'suitability']].head(5).to_string(index=False))

print("\n" + "="*70)
print("TOP 5 EXPERIENCED INDIAN FAST BOWLERS:")
print("="*70)
print(results['indian_fast_bowlers'][['player_name', 'matches', 'overs', 'wickets', 'bowler_strike_rate', 'dot_pct', 'suitability']].head(5).to_string(index=False))

print("\n" + "="*70)
print("TOP 5 POWERPLAY FAST BOWLERS:")
print("="*70)
print(results['powerplay_pace'][['player_name', 'matches', 'overs', 'wickets', 'bowler_strike_rate', 'dot_pct', 'suitability']].head(5).to_string(index=False))

print("\n" + "="*70)
print("TOP 5 DEATH-OVER BOWLERS:")
print("="*70)
print(results['death_bowlers'][['player_name', 'matches', 'overs', 'wickets', 'bowler_strike_rate', 'dot_pct', 'suitability']].head(5).to_string(index=False))

print("\n" + "="*70)
print("TOP 5 SPIN SUPPORT BOWLERS (for Jadeja & Bishnoi):")
print("="*70)
print(results['spin_support'][['player_name', 'bowling_type', 'matches', 'overs', 'wickets', 'bowler_strike_rate', 'dot_pct', 'suitability']].head(5).to_string(index=False))

print("\n" + "="*70)
print("BATTING COMBINATION PROFILES (Parag, Ferreira, Jadeja):")
print("="*70)
print(results['combo_profiles'].to_string(index=False))

if len(results['combo_partnerships']) > 0:
    print("\n" + "="*70)
    print("DIRECT PARTNERSHIPS OBSERVED:")
    print("="*70)
    print(results['combo_partnerships'].to_string(index=False))
