"""V3 Rajasthan Royals Tactical Squad Analysis Module.

Synthesizes RR 2026 season performance, role coverage, and tactical priorities.
Establishes the empirical gap baselines against which external candidates are evaluated.
"""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class V3RRSquadAnalyzer:
    """Analyzes RR 2026 squad balance, bench depth, and phase coverage."""

    @staticmethod
    def audit_phase_coverage(bowl_stats_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Evaluate legal balls and wicket distribution across PP, Middle, and Death."""
        pp_balls = bowl_stats_df['pp_legal_balls'].sum()
        pp_wkts = bowl_stats_df['pp_wickets'].sum()
        
        mid_balls = bowl_stats_df['middle_legal_balls'].sum()
        mid_wkts = bowl_stats_df['middle_wickets'].sum()
        
        dth_balls = bowl_stats_df['death_legal_balls'].sum()
        dth_wkts = bowl_stats_df['death_wickets'].sum()

        return {
            'powerplay': {'legal_balls': int(pp_balls), 'wickets': int(pp_wkts), 'wkt_rate': round(pp_wkts / max(1, pp_balls) * 100, 2)},
            'middle': {'legal_balls': int(mid_balls), 'wickets': int(mid_wkts), 'wkt_rate': round(mid_wkts / max(1, mid_balls) * 100, 2)},
            'death': {'legal_balls': int(dth_balls), 'wickets': int(dth_wkts), 'wkt_rate': round(dth_wkts / max(1, dth_balls) * 100, 2)},
        }

    @staticmethod
    def identify_underperforming_contracts(contrib_df: pd.DataFrame, min_price_cr: float = 3.0) -> pd.DataFrame:
        """Flag high-salary players whose output contribution fell below tactical expectations."""
        high_price = contrib_df[contrib_df['contract_price_cr'] >= min_price_cr].copy()
        # High salary but low run share (<3%) and low wicket share (<5%)
        underperformed = high_price[(high_price['runs_share_pct'] < 3.0) & (high_price['wickets_share_pct'] < 5.0)].copy()
        return underperformed
