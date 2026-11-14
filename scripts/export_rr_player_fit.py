"""Export RR Player Fit evaluation table to CSV."""
from pathlib import Path
import pandas as pd
from src.scouting_engine.v3_rr_player_fit import V3RRPlayerFitEngine

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_V3 = ROOT / "data" / "outputs" / "v3"
OUTPUTS_V3.mkdir(parents=True, exist_ok=True)

def main():
    fit_df = V3RRPlayerFitEngine.generate_player_fit_dataset()
    out_path = OUTPUTS_V3 / "RR_PLAYER_FIT.csv"
    fit_df.to_csv(out_path, index=False)
    print(f"Saved RR_PLAYER_FIT.csv with {len(fit_df)} evaluated candidates.")

if __name__ == '__main__':
    main()
