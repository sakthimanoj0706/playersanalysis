"""Build all context features and save to parquet."""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.config import PROCESSED_DIR, FEATURES_DIR, DATA_DIR
from src.ingestion.loader import load_all_data
from src.preprocessing.cleaner import clean_all
from src.context_engine.innings_context import build_innings_context
from src.context_engine.delivery_context import build_delivery_context
from src.context_engine.partnership_tracker import build_partnerships

FEATURES_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("0. Loading raw data and running validated cleaning pipeline...")
raw_data = load_all_data()
df_regular, df_so = clean_all(raw_data['ball_by_ball'], raw_data['matches'])
df_regular.to_parquet(PROCESSED_DIR / 'ball_by_ball_cleaned.parquet', index=False)
df_so.to_parquet(PROCESSED_DIR / 'super_overs.parquet', index=False)
print(f"Cleaned {len(df_regular)} regular deliveries, {len(df_so)} super overs.")

df = df_regular.copy()

print("\n1. Building innings context...")
df = build_innings_context(df)
print(f"   wickets_fallen_before range: {df['wickets_fallen_before'].min()}-{df['wickets_fallen_before'].max()}")
print(f"   New batters: {df['is_new_batter'].sum()}")
print(f"   Recent wicket clusters: {df['recent_wicket_cluster'].sum()}")

print("\n2. Building delivery context...")
df = build_delivery_context(df)
print(f"   Dot balls: {df['dot_ball'].sum()}")
print(f"   Boundaries: {df['boundary'].sum()}")
print(f"   Scoring shots: {df['scoring_shot'].sum()}")

print("\n3. Building partnerships...")
df = build_partnerships(df)
total_partnerships = df.groupby(['match_id', 'innings', 'partnership_id']).ngroups
print(f"   Total partnerships: {total_partnerships}")
# Avg partnership length
p_stats = df.groupby(['match_id', 'innings', 'partnership_id']).agg(
    balls=('is_ball_faced', 'sum'),
    runs=('runs', 'sum')
)
print(f"   Avg partnership: {p_stats['runs'].mean():.1f} runs, {p_stats['balls'].mean():.1f} balls")

print(f"\n4. Saving to {FEATURES_DIR / 'ball_by_ball_with_context.parquet'}...")
df.to_parquet(FEATURES_DIR / 'ball_by_ball_with_context.parquet', index=False)
print(f"   Saved {len(df)} rows with {len(df.columns)} columns")

# Quick validation: check a specific match
sample = df[df['match_id'] == df['match_id'].iloc[0]]
inn1 = sample[sample['innings'] == 1]
print(f"\nValidation - First match (id={inn1['match_id'].iloc[0]}), innings 1:")
print(f"   Deliveries: {len(inn1)}")
print(f"   Total wickets: {inn1['is_wicket'].sum()}")
print(f"   Last delivery wickets_fallen_before: {inn1['wickets_fallen_before'].iloc[-1]}")
print(f"   Partnerships: {inn1['partnership_id'].max()}")
print("\nAll context features built successfully.")
