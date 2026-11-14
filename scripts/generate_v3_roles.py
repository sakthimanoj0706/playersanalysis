"""Generate V3 player roles on the full dataset."""
import sys
from pathlib import Path
import logging
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.adapters.rr_data_adapter import RRDataAdapter
from src.classification.v3_role_classifier import V3RoleClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUTS_V3 = DATA_DIR / "outputs" / "v3"
REPORTS_V3 = DATA_DIR / "reports" / "v3"
OUTPUTS_V3.mkdir(parents=True, exist_ok=True)
REPORTS_V3.mkdir(parents=True, exist_ok=True)

def main():
    logging.info("Loading raw tables for V3 role classification...")
    raw_bbb = pd.read_csv(DATA_DIR / "ball_by_ball_ipl_t20i.csv", dtype={'season': str})
    p11 = pd.read_csv(DATA_DIR / "playing_eleven_ipl_t20i.csv")
    mapping = pd.read_csv(DATA_DIR / "competition_team_player_mapping_ipl_t20i.csv")

    adapter = RRDataAdapter()
    bbb = adapter.transform_deliveries(raw_bbb)

    logging.info("Classifying full roster with V3RoleClassifier...")
    roles_df = V3RoleClassifier.classify_roster(p11, bbb, mapping)

    output_path = OUTPUTS_V3 / "player_roles.csv"
    roles_df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(roles_df)} classified players to {output_path}")

    # Summary
    print("\n--- V3 ROLE DISTRIBUTION ---")
    print(roles_df['v3_role'].value_counts())
    print("\n--- LEADERBOARD ELIGIBILITY ---")
    print("Eligible for Bat Leaderboard:", roles_df['eligible_for_bat_leaderboard'].sum())
    print("Eligible for Bowl Leaderboard:", roles_df['eligible_for_bowl_leaderboard'].sum())
    both = roles_df[roles_df['eligible_for_bat_leaderboard'] & roles_df['eligible_for_bowl_leaderboard']]
    print("Eligible for BOTH Leaderboards (MUST BE 0):", len(both))

if __name__ == '__main__':
    main()
