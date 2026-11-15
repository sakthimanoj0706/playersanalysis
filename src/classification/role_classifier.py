"""Player Role Classification Engine and Canonical Name Normalization.

Scientifically classifies cricket players into evidence-based roles:
- Top-Order Batter (Positions 1-3)
- Middle-Order Batter (Positions 4-5)
- Finisher / WK (Positions 6-7 or specialist wicketkeepers)
- Batting All-Rounder
- Bowling All-Rounder
- Specialist Fast Bowler (Positions 8-11, Pace)
- Specialist Spin Bowler (Positions 8-11, Spin)
- Specialist Bowler (Generic)
- Lower-Order Batter (Positions 8-11)
- Part-Time Bowler

Produces:
- PLAYER_ROLE_CLASSIFICATION.csv
- PLAYER_NAME_ALIASES.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

from src.config import DATA_DIR, OUTPUTS_DIR

# ── CANONICAL PLAYER NAME DICTIONARY ─────────────────────────────────────────
CANONICAL_NAME_MAP = {
    7897: "Tilak Varma",            # Namboori Tilak Varma
    8: "MS Dhoni",                  # Mahendra Singh Dhoni
    953: "KL Rahul",                # Lokesh Rahul
    305: "R Ashwin",                # Ravichandran Ashwin
    47: "Virat Kohli",
    126: "Rohit Sharma",
    1699: "Suryakumar Yadav",
    2258: "Sanju Samson",
    4117: "Ishan Kishan",
    4703: "Rishabh Pant",
    152: "Ravindra Jadeja",
    3330: "Hardik Pandya",
    2933: "Jasprit Bumrah",
    4708: "Rinku Singh",
    4812: "Harry Tector",
    3276: "Gudakesh Motie",
    2417: "Akeal Hosein",
    5379: "Mark Adair",
    3720: "Craig Young",
    2985: "Mark Wood",
    4837: "Obed McCoy",
    2320: "Trent Boult",
    5739: "Gareth Delany",
    39657: "Eshan Malinga",
    3564: "Jacob Duffy",
    2226: "Krishnappa Gowtham",
    1813: "Deepak Chahar",
    8661: "Matheesha Pathirana",
    3926: "Rahul Tewatia",
    6161: "Rahul Chahar",
    1440: "Rahul Tripathi",
    1077: "David Miller",
    7446: "Abdul Samad",
    6922: "Abdul Samad (PAK)",
    4106: "Daryl Mitchell",
    4391: "Liam Livingstone",
    796: "Matthew Wade",
    4773: "Jaker Ali Anik",
    20006: "Ramandeep Singh",
    2639: "Marcus Stoinis",
    3916: "Jitesh Sharma",
    4409: "Sam Curran",
    1596: "Moeen Ali",
    3297: "Shimron Hetmyer",
    3056: "Iftikhar Ahmed",
    2687: "Roston Chase",
    5041: "Mukesh Kumar",
    4641: "Lungi Ngidi",
    8182: "Donovan Ferreira",
    7052: "Dunith Wellalage",
    1487: "Adam Milne",
    2411: "Sandeep Sharma",
    3629: "Corbin Bosch",
    829: "Mitchell Starc",
    7741: "Gareth Delany",
    22920: "Jacob Duffy",
    7338: "Haider Ali",
    28756: "Haider Ali (UAE)",
    3083: "Mohammad Ali",
    20229: "Mohammad Ali",
    1944: "Keshav Maharaj",
}


def build_player_name_aliases(mapping_df: pd.DataFrame, bbb_df: pd.DataFrame) -> pd.DataFrame:
    """Build canonical name aliases from mapping and ball-by-ball tables."""
    names_from_map = mapping_df[['player_id', 'player_name']].drop_duplicates()
    
    strikers = bbb_df[['striker_id', 'striker_name']].rename(
        columns={'striker_id': 'player_id', 'striker_name': 'player_name'}
    ).drop_duplicates()
    
    bowlers = bbb_df[['bowler_id', 'bowler_name']].rename(
        columns={'bowler_id': 'player_id', 'bowler_name': 'player_name'}
    ).drop_duplicates()

    combined = pd.concat([names_from_map, strikers, bowlers], ignore_index=True).drop_duplicates()
    
    source_names = combined.groupby('player_id')['player_name'].agg(
        lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
    ).reset_index()
    source_names.rename(columns={'player_name': 'source_player_name'}, inplace=True)

    def _get_canonical(row):
        pid = row['player_id']
        src = str(row['source_player_name']).strip()
        if pid in CANONICAL_NAME_MAP:
            return CANONICAL_NAME_MAP[pid]
        return src

    def _get_status(row):
        pid = row['player_id']
        if pid in CANONICAL_NAME_MAP:
            return "CANONICAL_STANDARDIZED"
        return "DIRECT_MATCH"

    source_names['canonical_display_name'] = source_names.apply(_get_canonical, axis=1)
    source_names['verification_status'] = source_names.apply(_get_status, axis=1)

    return source_names.sort_values('player_id').reset_index(drop=True)


def classify_player_roles(
    p11_df: pd.DataFrame,
    bbb_df: pd.DataFrame,
    aliases_df: pd.DataFrame
) -> pd.DataFrame:
    """Empirically classify all players based on batting order, WK duties, and workload volumes."""
    # 1. Batting order distribution and top-7 ratio
    p11_valid = p11_df[p11_df['batting_order'].notna() & (p11_df['batting_order'] > 0)].copy()
    
    def _calc_order_profile(s):
        if len(s) == 0:
            return pd.Series({
                'modal_order': 10, 'avg_order': 10.0,
                'dist_str': 'No order recorded', 'inns_count': 0,
                'top7_ratio': 0.0, 'is_regular_top7': False
            })
        m = int(s.mode().iloc[0])
        avg = round(float(s.mean()), 2)
        top = int((s <= 3).sum())
        mid = int(((s >= 4) & (s <= 5)).sum())
        low_mid = int(((s >= 6) & (s <= 7)).sum())
        tail = int((s >= 8).sum())
        top7_count = top + mid + low_mid
        top7_ratio = round(top7_count / len(s), 3)
        is_reg_top7 = (top7_ratio >= 0.50) or (m <= 7)
        dist_str = f"Top(1-3):{top}, Mid(4-5):{mid}, LowMid(6-7):{low_mid}, Tail(8+):{tail}"
        return pd.Series({
            'modal_order': m, 'avg_order': avg,
            'dist_str': dist_str, 'inns_count': len(s),
            'top7_ratio': top7_ratio, 'is_regular_top7': is_reg_top7
        })

    order_profile = p11_valid.groupby('player_id')['batting_order'].apply(_calc_order_profile).unstack().reset_index()

    # 2. Genuine Wicketkeeper status: requires minimum 5 matches and >= 35% of games as WK
    wk_agg = p11_df.groupby('player_id').agg(
        wk_matches=('is_wk', lambda x: (x == True).sum()),
        total_p11=('is_played', 'count')
    ).reset_index()
    wk_agg['is_wicketkeeper'] = (wk_agg['wk_matches'] >= 5) & ((wk_agg['wk_matches'] / np.maximum(1, wk_agg['total_p11'])) >= 0.35)

    # 3. Balls faced volume and crisis faced
    faced_df = bbb_df[bbb_df['is_ball_faced']].copy() if 'is_ball_faced' in bbb_df.columns else bbb_df.copy()
    bat_vol = faced_df.groupby('striker_id').agg(
        total_batting_balls=('runs', 'count'),
        total_batting_runs=('runs', 'sum'),
    ).reset_index().rename(columns={'striker_id': 'player_id'})

    if 'is_batting_high_pressure' in faced_df.columns:
        bat_crisis = faced_df[faced_df['is_batting_high_pressure']].groupby('striker_id')['runs'].count().reset_index(
            name='pressure_deliveries_faced'
        ).rename(columns={'striker_id': 'player_id'})
    else:
        bat_crisis = pd.DataFrame(columns=['player_id', 'pressure_deliveries_faced'])

    # 4. Bowling volume, style, and crisis bowled
    legal_df = bbb_df[bbb_df['is_legal_ball']].copy() if 'is_legal_ball' in bbb_df.columns else bbb_df.copy()
    
    def _get_bowling_style(s):
        s_clean = s.dropna()
        if len(s_clean) == 0:
            return "None"
        mode_val = s_clean.mode()
        return str(mode_val.iloc[0]) if len(mode_val) > 0 else "None"

    bowl_vol = legal_df.groupby('bowler_id').agg(
        total_bowling_deliveries=('runs', 'count'),
        bowling_style=('pace_or_spin', _get_bowling_style) if 'pace_or_spin' in legal_df.columns else ('runs', lambda x: 'None'),
    ).reset_index().rename(columns={'bowler_id': 'player_id'})

    if 'is_bowling_high_pressure' in legal_df.columns:
        bowl_crisis = legal_df[legal_df['is_bowling_high_pressure']].groupby('bowler_id')['runs'].count().reset_index(
            name='pressure_deliveries_bowled'
        ).rename(columns={'bowler_id': 'player_id'})
    else:
        bowl_crisis = pd.DataFrame(columns=['player_id', 'pressure_deliveries_bowled'])

    # 5. Merge all into master classification frame
    master = aliases_df.merge(order_profile, on='player_id', how='left')
    master = master.merge(wk_agg[['player_id', 'is_wicketkeeper']], on='player_id', how='left')
    master = master.merge(bat_vol, on='player_id', how='left')
    master = master.merge(bat_crisis, on='player_id', how='left')
    master = master.merge(bowl_vol, on='player_id', how='left')
    master = master.merge(bowl_crisis, on='player_id', how='left')

    # Fill defaults
    for int_col, default_val in [
        ('modal_order', 10), ('inns_count', 0), ('total_batting_balls', 0),
        ('total_batting_runs', 0), ('pressure_deliveries_faced', 0),
        ('total_bowling_deliveries', 0), ('pressure_deliveries_bowled', 0)
    ]:
        master[int_col] = pd.to_numeric(master[int_col], errors='coerce').fillna(default_val).astype(int)
    master['avg_order'] = pd.to_numeric(master['avg_order'], errors='coerce').fillna(10.0).astype(float).round(2)
    master['dist_str'] = master['dist_str'].fillna('No order recorded')
    master['top7_ratio'] = pd.to_numeric(master['top7_ratio'], errors='coerce').fillna(0.0).astype(float)
    master['is_regular_top7'] = master['is_regular_top7'].where(master['is_regular_top7'].notna(), False).astype(bool)
    master['is_wicketkeeper'] = master['is_wicketkeeper'].where(master['is_wicketkeeper'].notna(), False).astype(bool)
    master['bowling_style'] = master['bowling_style'].fillna('None')

    # 6. Apply Empirical Role Classification
    roles = []
    sec_roles = []
    confidences = []
    evidences = []

    for _, row in master.iterrows():
        m_order = row['modal_order']
        is_wk = row['is_wicketkeeper']
        bat_b = row['total_batting_balls']
        bowl_b = row['total_bowling_deliveries']
        p_bat = row['pressure_deliveries_faced']
        p_bowl = row['pressure_deliveries_bowled']
        b_style = row['bowling_style']
        inns = row['inns_count']
        top7_r = row['top7_ratio']
        is_reg_top7 = row['is_regular_top7']

        # Rule evaluation
        if is_wk and (bat_b >= bowl_b):
            primary = "WK-Batter"
            if m_order <= 3:
                secondary = "Top-Order Batter"
            elif m_order <= 5:
                secondary = "Middle-Order Anchor"
            else:
                secondary = "Finisher"
            conf = "High" if inns >= 5 else "Medium"
            ev = f"Specialist WK in {inns} inns (Top-7 ratio: {top7_r:.1%}). Faced {bat_b} balls ({p_bat} crisis) vs {bowl_b} bowled."

        elif is_reg_top7 and m_order <= 3:
            if bowl_b >= 150 and bat_b >= 150:
                primary = "Batting All-Rounder"
                secondary = f"Top-Order Batter / {b_style} Bowler"
            else:
                primary = "Top-Order Batter"
                secondary = "Specialist Batter" if bowl_b < 50 else f"Part-Time {b_style} Bowler"
            conf = "High" if inns >= 5 else "Medium"
            ev = f"Top-order modal pos {m_order} ({row['dist_str']}). Faced {bat_b} balls ({p_bat} crisis), bowled {bowl_b} ({p_bowl} crisis)."

        elif is_reg_top7 and m_order in [4, 5]:
            if bowl_b >= 150 and bat_b >= 150:
                primary = "Batting All-Rounder"
                secondary = f"Middle-Order Batter / {b_style} Bowler"
            else:
                primary = "Middle-Order Batter"
                secondary = "Specialist Batter" if bowl_b < 50 else f"Part-Time {b_style} Bowler"
            conf = "High" if inns >= 5 else "Medium"
            ev = f"Middle-order modal pos {m_order} ({row['dist_str']}). Faced {bat_b} balls ({p_bat} crisis), bowled {bowl_b} ({p_bowl} crisis)."

        elif is_reg_top7 and m_order in [6, 7]:
            if bowl_b >= 200:
                if bat_b >= bowl_b * 0.7:
                    primary = "Batting All-Rounder"
                    secondary = f"Finisher / {b_style} Bowler"
                else:
                    primary = "Bowling All-Rounder"
                    secondary = f"Lower-Middle Order / {b_style} Bowler"
            else:
                primary = "Finisher / Lower-Middle Batter"
                secondary = "Specialist Batter" if bowl_b < 50 else f"Part-Time {b_style} Bowler"
            conf = "High" if inns >= 5 else "Medium"
            ev = f"Lower-middle modal pos {m_order} ({row['dist_str']}). Faced {bat_b} balls ({p_bat} crisis), bowled {bowl_b} ({p_bowl} crisis)."

        else: # modal_order >= 8 or tailender
            if bowl_b >= 80:
                if b_style == "Pace":
                    primary = "Specialist Fast Bowler"
                elif b_style == "Spin":
                    primary = "Specialist Spin Bowler"
                else:
                    primary = "Specialist Bowler"
                secondary = "Lower-Order Hitter" if bat_b >= 60 else "Tailender"
            elif bat_b >= 40:
                primary = "Lower-Order Batter"
                secondary = f"Part-Time {b_style} Bowler" if bowl_b >= 20 else "Tailender"
            else:
                primary = "Specialist Bowler" if bowl_b >= bat_b else "Lower-Order Batter"
                secondary = "Development Squad"
            conf = "High" if (bowl_b + bat_b) >= 100 else ("Medium" if (bowl_b + bat_b) >= 30 else "Low")
            ev = f"Lower-order modal pos {m_order} (Top-7 ratio: {top7_r:.1%}). Bowled {bowl_b} balls ({p_bowl} crisis, {b_style}), faced {bat_b} balls ({p_bat} crisis)."

        roles.append(primary)
        sec_roles.append(secondary)
        confidences.append(conf)
        evidences.append(ev)

    master['primary_role'] = roles
    master['secondary_role'] = sec_roles
    master['role_confidence'] = confidences
    master['classification_evidence'] = evidences

    cols_order = [
        'player_id', 'source_player_name', 'canonical_display_name',
        'primary_role', 'secondary_role', 'modal_batting_position',
        'batting_position_distribution', 'is_regular_top7', 'top7_ratio',
        'total_batting_balls', 'total_bowling_deliveries',
        'pressure_deliveries_faced', 'pressure_deliveries_bowled',
        'is_wicketkeeper', 'bowling_style', 'role_confidence',
        'classification_evidence'
    ]
    master.rename(columns={
        'modal_order': 'modal_batting_position',
        'dist_str': 'batting_position_distribution',
    }, inplace=True)

    return master[cols_order].sort_values(['primary_role', 'canonical_display_name']).reset_index(drop=True)
