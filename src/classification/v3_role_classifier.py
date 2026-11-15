"""Five-State Evidence-Based Role Classification Engine for V3.

Replaces legacy granular heuristics with five mutually exclusive, mathematically defensible classes:
1. BAT_SPECIALIST: Top/middle order batters and specialist wicketkeepers who rarely or never bowl.
2. BOWL_SPECIALIST: Frontline pace and spin bowlers who bat in the lower order / tail.
3. BAT_PRIMARY_AR: Batting-dominant all-rounders who regular bat in the top 7 and bowl substantial overs.
4. BOWL_PRIMARY_AR: Bowling-dominant all-rounders who bowl frontline overs and contribute in the lower-middle order.
5. UNRESOLVED: Low-sample players, emerging squad members, or candidates lacking sufficient evidence.

Guarantees:
- Strict role exclusivity.
- Primary key is stable integer player_id.
- Fully independent of pressure metrics.
- Hard leaderboard gating: batters can only be BAT_SPECIALIST or BAT_PRIMARY_AR;
  bowlers can only be BOWL_SPECIALIST or BOWL_PRIMARY_AR.
"""
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from src.classification.role_classifier import CANONICAL_NAME_MAP
from src.identity.player_identity import PlayerIdentityResolver


class V3RoleClassifier:
    """Five-state role classifier using multi-dimensional workload and positioning evidence."""

    VALID_ROLES = {
        'BAT_SPECIALIST',
        'BOWL_SPECIALIST',
        'BAT_PRIMARY_AR',
        'BOWL_PRIMARY_AR',
        'UNRESOLVED',
    }

    # Minimum workload thresholds for evidence sufficiency
    MIN_MATCHES_EVIDENCE = 3
    MIN_TOTAL_DELIVERIES = 30  # combined balls faced + legal balls bowled

    @classmethod
    def classify_roster(
        cls,
        p11_df: pd.DataFrame,
        bbb_df: pd.DataFrame,
        mapping_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Classify all players in the dataset into the 5 mutually exclusive states."""
        # 0. Canonical Player Identity Resolution
        resolver = PlayerIdentityResolver()
        p11_df = resolver.resolve_playing_eleven(p11_df)
        bbb_df = resolver.resolve_deliveries(bbb_df)
        if mapping_df is not None:
            mapping_df = resolver.resolve_mapping(mapping_df)
        
        # 1. Batting order profile from playing eleven (filter to active played rows and deduplicate key collisions)
        p11_active = p11_df[p11_df['is_played'] == True].copy() if 'is_played' in p11_df.columns else p11_df.copy()
        dedup_cols = ['match_id', 'team_id', 'player_id'] if 'team_id' in p11_active.columns else ['match_id', 'player_id']
        if all(c in p11_active.columns for c in dedup_cols):
            p11_active = p11_active.drop_duplicates(subset=dedup_cols, keep='first')

        p11_valid = p11_active[p11_active['batting_order'].notna() & (p11_active['batting_order'] > 0)].copy()
        
        def _get_order_stats(s):
            if len(s) == 0:
                return pd.Series({'modal_order': 10, 'mean_order': 10.0, 'top7_ratio': 0.0, 'p11_appearances': 0})
            m = int(s.mode().iloc[0])
            avg = float(s.mean())
            top7 = (s <= 7).sum()
            ratio = top7 / len(s)
            return pd.Series({'modal_order': m, 'mean_order': round(avg, 2), 'top7_ratio': round(ratio, 3), 'p11_appearances': len(s)})

        order_stats = p11_valid.groupby('player_id')['batting_order'].apply(_get_order_stats).unstack().reset_index()

        # 2. Wicketkeeper duty detection
        wk_stats = p11_active.groupby('player_id').agg(
            wk_matches=('is_wk', lambda x: (x == True).sum()),
            total_matches=('match_id', 'nunique')
        ).reset_index()
        wk_stats['is_wicketkeeper'] = (wk_stats['wk_matches'] >= 3) & ((wk_stats['wk_matches'] / np.maximum(1, wk_stats['total_matches'])) >= 0.30)

        # 3. Batting workload (balls faced, excluding Super Overs innings > 2 if present)
        bbb_reg = bbb_df[bbb_df['innings'].isin([1, 2])].copy() if 'innings' in bbb_df.columns else bbb_df.copy()
        faced = bbb_reg[bbb_reg['is_ball_faced']].copy() if 'is_ball_faced' in bbb_reg.columns else bbb_reg.copy()
        bat_agg = faced.groupby('striker_id').agg(
            balls_faced=('runs', 'count'),
            total_runs=('runs', 'sum'),
            bat_matches=('match_id', 'nunique')
        ).reset_index().rename(columns={'striker_id': 'player_id'})

        # 4. Bowling workload (legal balls)
        legal = bbb_reg[bbb_reg['is_legal_ball']].copy() if 'is_legal_ball' in bbb_reg.columns else bbb_reg.copy()
        bowl_agg = legal.groupby('bowler_id').agg(
            legal_balls_bowled=('runs', 'count'),
            wickets=('is_bowler_wicket' if 'is_bowler_wicket' in legal.columns else 'is_wicket', 'sum'),
            bowl_matches=('match_id', 'nunique'),
            bowling_style=('pace_or_spin', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown') if 'pace_or_spin' in legal.columns else ('runs', lambda x: 'Unknown')
        ).reset_index().rename(columns={'bowler_id': 'player_id'})

        # 5. Master Player Pool
        all_pids = set(p11_df['player_id'].unique()) | set(faced['striker_id'].unique()) | set(legal['bowler_id'].unique())
        if mapping_df is not None:
            all_pids |= set(mapping_df['player_id'].unique())
            name_map = mapping_df.groupby('player_id')['player_name'].agg(lambda x: x.mode().iloc[0]).to_dict()
        else:
            name_map = {}

        master = pd.DataFrame({'player_id': list(all_pids)})
        master = master.merge(order_stats, on='player_id', how='left')
        master = master.merge(wk_stats[['player_id', 'is_wicketkeeper', 'total_matches']], on='player_id', how='left')
        master = master.merge(bat_agg, on='player_id', how='left')
        master = master.merge(bowl_agg, on='player_id', how='left')

        # Fill missing values
        for int_col, default_val in [
            ('modal_order', 10), ('p11_appearances', 0), ('total_matches', 0),
            ('balls_faced', 0), ('total_runs', 0), ('bat_matches', 0),
            ('legal_balls_bowled', 0), ('wickets', 0), ('bowl_matches', 0)
        ]:
            master[int_col] = pd.to_numeric(master[int_col], errors='coerce').fillna(default_val).astype(int)
        master['mean_order'] = pd.to_numeric(master['mean_order'], errors='coerce').fillna(10.0).astype(float)
        master['top7_ratio'] = pd.to_numeric(master['top7_ratio'], errors='coerce').fillna(0.0).astype(float)
        master['is_wicketkeeper'] = master['is_wicketkeeper'].where(master['is_wicketkeeper'].notna(), False).astype(bool)
        master['bowling_style'] = master['bowling_style'].fillna('Unknown')

        # Compute combined match exposure
        master['match_count'] = np.maximum(
            master['total_matches'],
            np.maximum(master['bat_matches'], master['bowl_matches'])
        )
        master['combined_workload'] = master['balls_faced'] + master['legal_balls_bowled']

        # Canonical display name
        def _get_name(pid):
            if pid in CANONICAL_NAME_MAP:
                return CANONICAL_NAME_MAP[pid]
            res_name = resolver.resolve_name(pid)
            if res_name and not res_name.startswith("Player_"):
                return res_name
            return name_map.get(pid, f"Player_{pid}")

        master['player_name'] = master['player_id'].map(_get_name)
        master['canonical_player_id'] = master['player_id']

        # 6. Apply Five-State Classification Rules
        roles = []
        confidences = []
        reasons = []

        for _, row in master.iterrows():
            m_order = row['modal_order']
            top7_r = row['top7_ratio']
            bf = row['balls_faced']
            bb = row['legal_balls_bowled']
            m_count = row['match_count']
            comb = row['combined_workload']
            is_wk = row['is_wicketkeeper']

            # Insufficient evidence rule
            if m_count < cls.MIN_MATCHES_EVIDENCE or comb < cls.MIN_TOTAL_DELIVERIES:
                roles.append('UNRESOLVED')
                confidences.append('LOW')
                reasons.append(f"Insufficient sample: {m_count} matches, {comb} total deliveries.")
                continue

            # Specialist Wicketkeeper: always BAT_SPECIALIST if batting workload exceeds bowling
            if is_wk and bf >= bb:
                roles.append('BAT_SPECIALIST')
                confidences.append('HIGH' if m_count >= 5 else 'MEDIUM')
                reasons.append(f"Wicketkeeper with {bf} balls faced vs {bb} balls bowled.")
                continue

            # Case A: Regular Top 7 Batter (top7_ratio >= 0.50 or modal_order <= 7)
            if top7_r >= 0.50 or m_order <= 7:
                # Sub-check for Dual All-Rounder capability
                # A batter who bowls substantial overs: >= 120 legal balls bowled and >= 120 balls faced
                if bb >= 120 and bf >= 120:
                    # Determine primary focus based on workload ratio
                    if bf >= bb * 0.8:
                        roles.append('BAT_PRIMARY_AR')
                        confidences.append('HIGH')
                        reasons.append(f"Top 7 regular (pos {m_order}) with dual high workload: {bf} balls faced, {bb} bowled.")
                    else:
                        roles.append('BOWL_PRIMARY_AR')
                        confidences.append('HIGH')
                        reasons.append(f"Top 7 regular but higher bowling workload: {bb} bowled vs {bf} faced.")
                elif bb >= 40 and bf >= 60:
                    # Moderate dual volume: if modal order <= 5, Bat-Primary AR, else check ratio
                    if m_order <= 5 or bf > bb:
                        roles.append('BAT_PRIMARY_AR')
                        confidences.append('MEDIUM')
                        reasons.append(f"Top/middle order batter (pos {m_order}) with supporting bowling: {bb} bowled.")
                    else:
                        roles.append('BOWL_PRIMARY_AR')
                        confidences.append('MEDIUM')
                        reasons.append(f"Batting order {m_order} with active bowling volume: {bb} bowled.")
                elif bb >= 60 and bf < 60:
                    # Lower-middle order player whose primary match workload is bowling
                    roles.append('BOWL_PRIMARY_AR')
                    confidences.append('MEDIUM')
                    reasons.append(f"Order {m_order} player with primary bowling workload: {bb} bowled vs {bf} faced.")
                else:
                    # Specialist Batter (negligible bowling)
                    roles.append('BAT_SPECIALIST')
                    confidences.append('HIGH' if bf >= 60 else 'MEDIUM')
                    reasons.append(f"Specialist batter at pos {m_order} (Top7: {top7_r:.1%}), {bf} balls faced, only {bb} bowled.")

            # Case B: Lower Order / Tailender (modal_order >= 8, top7_ratio < 0.50)
            else:
                # Sub-check for Bowling All-Rounder vs Specialist Bowler
                # Require genuine batting involvement (pos <= 8 or top7 >= 15%, plus >= 2.5 balls faced/match or >= 15% of balls bowled)
                if bb >= 100 and bf >= 80 and (m_order <= 8 or top7_r >= 0.15) and (bf / max(1, m_count) >= 2.5 or bf >= bb * 0.15):
                    roles.append('BOWL_PRIMARY_AR')
                    confidences.append('HIGH')
                    reasons.append(f"Lower order (pos {m_order}) with high bowling ({bb}b) and genuine batting volume ({bf}b across {m_count}m).")
                elif bb >= 60:
                    roles.append('BOWL_SPECIALIST')
                    confidences.append('HIGH' if bb >= 120 else 'MEDIUM')
                    reasons.append(f"Frontline bowler (pos {m_order}) with {bb} legal balls bowled.")
                elif bf >= 60 and bb < 30:
                    # Rare lower-order specialist batter / pinch-hitter
                    roles.append('BAT_SPECIALIST')
                    confidences.append('MEDIUM')
                    reasons.append(f"Lower-order batter with {bf} balls faced and negligible bowling.")
                else:
                    roles.append('UNRESOLVED')
                    confidences.append('LOW')
                    reasons.append(f"Lower order with borderline evidence: {bf} faced, {bb} bowled.")

        master['v3_role'] = roles
        master['role_confidence'] = confidences
        master['role_evidence'] = reasons

        # Leaderboard Eligibility Flags
        master['eligible_for_bat_leaderboard'] = master['v3_role'].isin(['BAT_SPECIALIST', 'BAT_PRIMARY_AR'])
        master['eligible_for_bowl_leaderboard'] = master['v3_role'].isin(['BOWL_SPECIALIST', 'BOWL_PRIMARY_AR'])

        cols = [
            'player_id', 'canonical_player_id', 'player_name', 'v3_role', 'role_confidence',
            'modal_order', 'mean_order', 'top7_ratio', 'balls_faced',
            'legal_balls_bowled', 'wickets', 'is_wicketkeeper', 'match_count',
            'eligible_for_bat_leaderboard', 'eligible_for_bowl_leaderboard',
            'role_evidence'
        ]
        return master[cols].sort_values(['v3_role', 'player_name']).reset_index(drop=True)
