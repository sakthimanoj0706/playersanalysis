"""Phase 1 validation: load, clean, validate, and save processed data."""
import sys
import logging
sys.path.insert(0, 'D:/rrhackthon')

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from src.config import PROCESSED_DIR, FEATURES_DIR, OUTPUTS_DIR, REPORTS_DIR
from src.ingestion.loader import load_all_data
from src.preprocessing.cleaner import clean_all, resolve_playing_xi_conflicts

# ── Ensure output directories exist ─────────────────────────────────────
for d in [PROCESSED_DIR, FEATURES_DIR, OUTPUTS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
    print(f"Directory ready: {d}")

# ══════════════════════════════════════════════════════════════════════════
# 1. Load all data
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("STEP 1: Loading all data")
print("="*70)

data = load_all_data()
validation = data.pop('_validation', {})

print("\nRow counts:")
for key, df in data.items():
    print(f"  {key:20s}: {len(df):>8,} rows, {len(df.columns):>3} columns")

print("\nValidation against VALIDATION_COUNTS.json:")
for key, v in validation.items():
    status = "✓ PASS" if v['match'] else "✗ FAIL"
    print(f"  {key:20s}: expected={v['expected']:>8,}  actual={v['actual']:>8,}  {status}")

# ══════════════════════════════════════════════════════════════════════════
# 2. Run cleaning pipeline
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("STEP 2: Running cleaning pipeline")
print("="*70)

bbb = data['ball_by_ball']
matches = data['matches']

regular_df, super_over_df = clean_all(bbb, matches)

# ══════════════════════════════════════════════════════════════════════════
# 3. Report counts
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("STEP 3: Validation report")
print("="*70)

print(f"\nRegular deliveries:     {len(regular_df):>8,}")
print(f"Super-over deliveries:  {len(super_over_df):>8,}")

# Extras by type
print("\nExtras by type:")
extras_counts = regular_df['extras_category'].value_counts().sort_index()
for cat, count in extras_counts.items():
    print(f"  {cat:15s}: {count:>7,}")

# Wickets by dismissal type
print("\nWickets by dismissal type:")
wicket_rows = regular_df[regular_df['is_wicket'] == True]
dismissal_counts = wicket_rows['dismissal_type'].value_counts()
for dtype, count in dismissal_counts.items():
    print(f"  {str(dtype):30s}: {count:>5,}")

# Bowler wickets
bowler_wickets = regular_df['is_bowler_wicket'].sum()
total_wickets = wicket_rows.shape[0]
non_bowler_wickets = total_wickets - bowler_wickets
print(f"\nTotal wickets:        {total_wickets:>6,}")
print(f"Bowler wickets:       {bowler_wickets:>6,}")
print(f"Non-bowler wickets:   {non_bowler_wickets:>6,}")

# Deliveries per phase
print("\nDeliveries per innings phase:")
phase_counts = regular_df['innings_phase'].value_counts()
for phase in ['powerplay', 'middle', 'death', 'unknown']:
    if phase in phase_counts.index:
        print(f"  {phase:15s}: {phase_counts[phase]:>8,}")

# Balls faced / legal balls
balls_faced = regular_df['is_ball_faced'].sum()
legal_balls = regular_df['is_legal_ball'].sum()
print(f"\nBalls faced (excl wides):      {balls_faced:>8,}")
print(f"Legal balls (excl wides+NB):   {legal_balls:>8,}")

# ══════════════════════════════════════════════════════════════════════════
# 4. Clean playing XI and save
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("STEP 4: Clean playing XI and save processed data")
print("="*70)

pe_df = data['playing_eleven']
print(f"Playing XI before dedup: {len(pe_df):>7,}")
pe_clean = resolve_playing_xi_conflicts(pe_df)
print(f"Playing XI after dedup:  {len(pe_clean):>7,}")
print(f"Rows removed:            {len(pe_df) - len(pe_clean):>7,}")

# Save to parquet
bbb_out = PROCESSED_DIR / "ball_by_ball_cleaned.parquet"
pe_out = PROCESSED_DIR / "playing_eleven_cleaned.parquet"
so_out = PROCESSED_DIR / "super_overs.parquet"

regular_df.to_parquet(bbb_out, index=False)
print(f"\nSaved: {bbb_out} ({len(regular_df):,} rows)")

pe_clean.to_parquet(pe_out, index=False)
print(f"Saved: {pe_out} ({len(pe_clean):,} rows)")

super_over_df.to_parquet(so_out, index=False)
print(f"Saved: {so_out} ({len(super_over_df):,} rows)")

print("\n" + "="*70)
print("Phase 1 COMPLETE")
print("="*70)
