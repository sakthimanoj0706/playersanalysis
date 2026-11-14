"""Rajasthan Royals squad scouting engine.

Analyses player suitability for specific tactical squad roles based on
empirical cricket evidence. Evaluates:
1. Explosive No. 4/5 middle-order batter
2. Experienced Indian pace depth (separating verified international caps from domestic IPL pool)
3. Reliable powerplay fast bowler
4. Middle-over pace support
5. Spin support (alongside Jadeja/Bishnoi)
6. Death-over bowling reliability
7. Batting combos: Riyan Parag, Donovan Ferreira, Ravindra Jadeja

NOTE: Scouting suitability indices are kept strictly separate from the
Top 10 pressure rankings to prevent role bias in the core hackathon rankings.
"""
import numpy as np
import pandas as pd
from src.config import DATA_DIR, OUTPUTS_DIR


# ── VERIFIED PLAYER IDENTITY METADATA ──────────────────────────────────────

def get_player_representation_metadata() -> pd.DataFrame:
    """Build verified competition and representation metadata per player.

    Separates:
    - India T20I representation (verified from match data)
    - Overseas T20I representation (verified foreign national team appearances)
    - IPL franchise participation (domestic league presence)
    """
    mapping_path = DATA_DIR / 'competition_team_player_mapping_ipl_t20i.csv'
    if not mapping_path.exists():
        return pd.DataFrame()

    mapping = pd.read_csv(mapping_path)

    ipl_teams = {
        'Chennai Super Kings', 'Mumbai Indians', 'Rajasthan Royals', 'Punjab Kings',
        'Royal Challengers Bengaluru', 'Delhi Capitals', 'Kolkata Knight Riders',
        'Sunrisers Hyderabad', 'Gujarat Titans', 'Lucknow Super Giants'
    }

    foreign_nations = set(mapping[mapping['match_format'] == 'T20I']['team_name'].unique()) - {'India'}

    # Aggregate player participation
    india_intl_pids = set(mapping[mapping['team_name'] == 'India']['player_id'].unique())
    foreign_intl_pids = set(mapping[mapping['team_name'].isin(foreign_nations)]['player_id'].unique())
    ipl_pids = set(mapping[mapping['team_name'].isin(ipl_teams)]['player_id'].unique())

    all_pids = mapping[['player_id', 'player_name']].drop_duplicates('player_id')
    all_pids['represented_india_t20i'] = all_pids['player_id'].isin(india_intl_pids)
    all_pids['represented_foreign_t20i'] = all_pids['player_id'].isin(foreign_intl_pids)
    all_pids['played_ipl'] = all_pids['player_id'].isin(ipl_pids)

    # Classification
    conditions = [
        all_pids['represented_india_t20i'],
        all_pids['represented_foreign_t20i'],
        all_pids['played_ipl'] & (~all_pids['represented_foreign_t20i']),
    ]
    choices = [
        'VERIFIED_INDIA_INTL',
        'VERIFIED_OVERSEAS_INTL',
        'IPL_DOMESTIC_POOL',
    ]
    all_pids['identity_category'] = np.select(conditions, choices, default='UNCLASSIFIED')

    return all_pids


# ── ROLE 1: EXPLOSIVE NO. 4/5 MIDDLE-ORDER BATTER ──────────────────────────

def scout_explosive_middle_order(df: pd.DataFrame, min_innings: int = 10) -> pd.DataFrame:
    """Find explosive No. 4/5 middle-order batters using empirical metrics.

    Calculates:
    - strike_rate: runs / balls faced * 100
    - boundary_pct: (fours + sixes) / balls faced * 100
    - batting_average: runs / dismissals (conventional batting average)
    - runs_per_innings: runs / innings
    """
    faced = df[(df['is_ball_faced']) & (df['batting_order'].isin([4, 5]))].copy()

    fours_col = 'is_four_validated' if 'is_four_validated' in faced.columns else 'is_four'
    sixes_col = 'is_six_validated' if 'is_six_validated' in faced.columns else 'is_six'

    agg = faced.groupby('striker_id').agg(
        player_name=('striker_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        innings=('match_id', 'nunique'),
        balls_faced=('runs', 'count'),
        runs=('runs', 'sum'),
        fours=(fours_col, 'sum'),
        sixes=(sixes_col, 'sum'),
    ).reset_index()

    # Dismissals at No. 4/5
    if 'is_wicket' in df.columns:
        wkt_sub = df[(df['is_wicket']) & (df['batting_order'].isin([4, 5]))]
        dis_col = 'dismissed_player_id' if 'dismissed_player_id' in wkt_sub.columns else 'striker_id'
        dismissals = wkt_sub.groupby(dis_col).size().reset_index(name='dismissals')
        dismissals = dismissals.rename(columns={dis_col: 'striker_id'})
        agg = agg.merge(dismissals, on='striker_id', how='left')
    else:
        agg['dismissals'] = 0
    agg['dismissals'] = agg['dismissals'].fillna(0).astype(int)

    agg = agg[agg['innings'] >= min_innings].copy()
    agg['strike_rate'] = np.where(agg['balls_faced'] > 0, (agg['runs'] / agg['balls_faced'] * 100.0).round(2), 0.0)
    agg['boundary_pct'] = np.where(agg['balls_faced'] > 0, ((agg['fours'] + agg['sixes']) / agg['balls_faced'] * 100.0).round(2), 0.0)
    agg['batting_average'] = np.where(agg['dismissals'] > 0, (agg['runs'] / agg['dismissals']).round(2), np.nan)
    agg['runs_per_innings'] = (agg['runs'] / agg['innings']).round(2)

    # Transparent Suitability Index (0-100)
    def _norm(s):
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else 0.5

    sr_score = _norm(agg['strike_rate'])
    bnd_score = _norm(agg['boundary_pct'])
    avg_score = _norm(agg['runs_per_innings'])

    # 40% Strike Rate, 35% Boundary %, 25% Scoring Volume
    agg['suitability_index'] = ((sr_score * 0.40 + bnd_score * 0.35 + avg_score * 0.25) * 100.0).round(1)
    agg['suitability'] = agg['suitability_index']  # alias

    return agg.sort_values('suitability_index', ascending=False).reset_index(drop=True)


# ── ROLE 2: EXPERIENCED INDIAN FAST BOWLER ──────────────────────────────────

def scout_indian_fast_bowlers(df: pd.DataFrame, min_matches: int = 12) -> pd.DataFrame:
    """Find experienced pace bowlers from verified India international or IPL domestic pool."""
    meta = get_player_representation_metadata()
    if meta.empty:
        # Fallback if mapping missing
        pace_df = df[df['pace_or_spin'] == 'Pace'].copy()
        pace_df['identity_category'] = 'UNCLASSIFIED'
    else:
        pace_ids = meta[meta['identity_category'].isin(['VERIFIED_INDIA_INTL', 'IPL_DOMESTIC_POOL'])]
        pace_df = df[(df['pace_or_spin'] == 'Pace') & (df['bowler_id'].isin(pace_ids['player_id']))].copy()
        pace_df = pace_df.merge(meta[['player_id', 'identity_category']].rename(columns={'player_id': 'bowler_id'}),
                                on='bowler_id', how='left')

    agg = pace_df.groupby('bowler_id').agg(
        player_name=('bowler_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        identity_category=('identity_category', lambda x: x.iloc[0]),
        matches=('match_id', 'nunique'),
        legal_balls=('is_legal_ball', 'sum'),
        wickets=('is_bowler_wicket', 'sum'),
    ).reset_index()

    if 'dot_ball' in pace_df.columns:
        dots = pace_df[pace_df['is_legal_ball']].groupby('bowler_id')['dot_ball'].sum().reset_index(name='dot_balls')
    else:
        dots = pace_df[pace_df['is_legal_ball']].groupby('bowler_id')['runs'].agg(lambda s: (s == 0).sum()).reset_index(name='dot_balls')
    agg = agg.merge(dots, on='bowler_id', how='left')
    agg['dot_balls'] = agg['dot_balls'].fillna(0).astype(int)

    agg = agg[agg['matches'] >= min_matches].copy()
    agg['overs'] = (agg['legal_balls'] // 6).astype(str) + '.' + (agg['legal_balls'] % 6).astype(str)
    agg['dot_pct'] = np.where(agg['legal_balls'] > 0, (agg['dot_balls'] / agg['legal_balls'] * 100.0).round(2), 0.0)
    agg['bowler_strike_rate'] = np.where(agg['wickets'] > 0, (agg['legal_balls'] / agg['wickets']).round(2), np.nan)

    def _norm(s):
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else 0.5

    wkt_score = _norm(agg['wickets'])
    dot_score = _norm(agg['dot_pct'])
    safe_sr = agg['bowler_strike_rate'].fillna(50.0).clip(upper=40.0)
    sr_score = 1.0 - _norm(safe_sr)

    # 40% Wickets, 30% Dot %, 30% Strike Rate
    agg['suitability_index'] = ((wkt_score * 0.40 + dot_score * 0.30 + sr_score * 0.30) * 100.0).round(1)
    agg['suitability'] = agg['suitability_index']

    return agg.sort_values('suitability_index', ascending=False).reset_index(drop=True)


# ── ROLE 3 & 4: PHASE SPECIALISTS ──────────────────────────────────────────

def scout_phase_bowlers(df: pd.DataFrame, phase: str, pace_or_spin: str = None,
                        min_balls: int = 60) -> pd.DataFrame:
    """Find bowlers suited for a specific phase (powerplay, middle, death)."""
    phase_df = df[df['innings_phase'] == phase].copy()
    if pace_or_spin:
        phase_df = phase_df[phase_df['pace_or_spin'] == pace_or_spin]

    agg = phase_df.groupby('bowler_id').agg(
        player_name=('bowler_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        matches=('match_id', 'nunique'),
        legal_balls=('is_legal_ball', 'sum'),
        wickets=('is_bowler_wicket', 'sum'),
    ).reset_index()

    if 'dot_ball' in phase_df.columns:
        dots = phase_df[phase_df['is_legal_ball']].groupby('bowler_id')['dot_ball'].sum().reset_index(name='dot_balls')
    else:
        dots = phase_df[phase_df['is_legal_ball']].groupby('bowler_id')['runs'].agg(lambda s: (s == 0).sum()).reset_index(name='dot_balls')
    agg = agg.merge(dots, on='bowler_id', how='left')
    agg['dot_balls'] = agg['dot_balls'].fillna(0).astype(int)

    agg = agg[agg['legal_balls'] >= min_balls].copy()
    agg['overs'] = (agg['legal_balls'] // 6).astype(str) + '.' + (agg['legal_balls'] % 6).astype(str)
    agg['dot_pct'] = np.where(agg['legal_balls'] > 0, (agg['dot_balls'] / agg['legal_balls'] * 100.0).round(2), 0.0)
    agg['bowler_strike_rate'] = np.where(agg['wickets'] > 0, (agg['legal_balls'] / agg['wickets']).round(2), np.nan)

    def _norm(s):
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else 0.5

    wkt_score = _norm(agg['wickets'])
    dot_score = _norm(agg['dot_pct'])
    safe_sr = agg['bowler_strike_rate'].fillna(50.0).clip(upper=40.0)
    sr_score = 1.0 - _norm(safe_sr)

    if phase == 'powerplay':
        agg['suitability_index'] = ((dot_score * 0.45 + wkt_score * 0.30 + sr_score * 0.25) * 100.0).round(1)
    elif phase == 'death':
        agg['suitability_index'] = ((wkt_score * 0.40 + dot_score * 0.35 + sr_score * 0.25) * 100.0).round(1)
    else:
        agg['suitability_index'] = ((wkt_score * 0.35 + dot_score * 0.35 + sr_score * 0.30) * 100.0).round(1)

    agg['suitability'] = agg['suitability_index']
    return agg.sort_values('suitability_index', ascending=False).reset_index(drop=True)


# ── ROLE 5: SPIN SUPPORT FOR JADEJA & BISHNOI ───────────────────────────────

def scout_spin_support(df: pd.DataFrame, min_matches: int = 15) -> pd.DataFrame:
    """Find spin support bowlers (excluding Ravindra Jadeja 152 and Ravi Bishnoi 7503)."""
    spin_df = df[df['pace_or_spin'] == 'Spin'].copy()
    spin_df = spin_df[~spin_df['bowler_id'].isin([152, 7503])]

    agg = spin_df.groupby('bowler_id').agg(
        player_name=('bowler_name', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        bowling_type=('bowling_type', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        matches=('match_id', 'nunique'),
        legal_balls=('is_legal_ball', 'sum'),
        wickets=('is_bowler_wicket', 'sum'),
    ).reset_index()

    if 'dot_ball' in spin_df.columns:
        dots = spin_df[spin_df['is_legal_ball']].groupby('bowler_id')['dot_ball'].sum().reset_index(name='dot_balls')
    else:
        dots = spin_df[spin_df['is_legal_ball']].groupby('bowler_id')['runs'].agg(lambda s: (s == 0).sum()).reset_index(name='dot_balls')
    agg = agg.merge(dots, on='bowler_id', how='left')
    agg['dot_balls'] = agg['dot_balls'].fillna(0).astype(int)

    agg = agg[agg['matches'] >= min_matches].copy()
    agg['overs'] = (agg['legal_balls'] // 6).astype(str) + '.' + (agg['legal_balls'] % 6).astype(str)
    agg['dot_pct'] = np.where(agg['legal_balls'] > 0, (agg['dot_balls'] / agg['legal_balls'] * 100.0).round(2), 0.0)
    agg['bowler_strike_rate'] = np.where(agg['wickets'] > 0, (agg['legal_balls'] / agg['wickets']).round(2), np.nan)

    def _norm(s):
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else 0.5

    wkt_score = _norm(agg['wickets'])
    dot_score = _norm(agg['dot_pct'])
    safe_sr = agg['bowler_strike_rate'].fillna(50.0).clip(upper=40.0)
    sr_score = 1.0 - _norm(safe_sr)

    agg['suitability_index'] = ((wkt_score * 0.40 + dot_score * 0.30 + sr_score * 0.30) * 100.0).round(1)
    agg['suitability'] = agg['suitability_index']
    return agg.sort_values('suitability_index', ascending=False).reset_index(drop=True)


# ── COMBINATION ANALYSIS: PARAG, FERREIRA, JADEJA ──────────────────────────

def scout_batting_combinations(df: pd.DataFrame) -> dict:
    """Analyze individual profile and partnership evidence for Parag, Ferreira, Jadeja."""
    target_ids = {
        'Riyan Parag': 6423,
        'Donovan Ferreira': 8182,
        'Ravindra Jadeja': 152,
    }

    fours_col = 'is_four_validated' if 'is_four_validated' in df.columns else 'is_four'
    sixes_col = 'is_six_validated' if 'is_six_validated' in df.columns else 'is_six'

    profiles = []
    for name, pid in target_ids.items():
        faced = df[(df['is_ball_faced']) & (df['striker_id'] == pid)]
        if len(faced) == 0:
            profiles.append({'player_name': name, 'balls_faced': 0, 'runs': 0, 'strike_rate': 0.0, 'innings': 0, 'boundary_pct': 0.0, 'avg_position': 0.0, 'pp_balls': 0, 'middle_balls': 0, 'death_balls': 0})
            continue

        runs = faced['runs'].sum()
        bf = len(faced)
        fours = faced[fours_col].sum()
        sixes = faced[sixes_col].sum()
        inns = faced[['match_id', 'innings']].drop_duplicates().shape[0]

        pp_balls = len(faced[faced['innings_phase'] == 'powerplay'])
        mid_balls = len(faced[faced['innings_phase'] == 'middle'])
        dth_balls = len(faced[faced['innings_phase'] == 'death'])

        profiles.append({
            'player_name': name,
            'player_id': pid,
            'innings': inns,
            'balls_faced': bf,
            'runs': runs,
            'strike_rate': round(runs / bf * 100.0, 2) if bf > 0 else 0.0,
            'boundary_pct': round((fours + sixes) / bf * 100.0, 2) if bf > 0 else 0.0,
            'avg_position': round(faced['batting_order'].mean(), 1),
            'pp_balls': pp_balls,
            'middle_balls': mid_balls,
            'death_balls': dth_balls,
        })

    profile_df = pd.DataFrame(profiles)

    # Observed In-Match Partnerships
    pair_records = []
    faced_all = df[df['is_ball_faced']].copy()
    for p1_name, p1_id in target_ids.items():
        for p2_name, p2_id in target_ids.items():
            if p1_id >= p2_id:
                continue
            pair_deliveries = faced_all[
                ((faced_all['striker_id'] == p1_id) & (faced_all['non_striker_id'] == p2_id)) |
                ((faced_all['striker_id'] == p2_id) & (faced_all['non_striker_id'] == p1_id))
            ]
            if len(pair_deliveries) > 0:
                p1_balls = len(pair_deliveries[pair_deliveries['striker_id'] == p1_id])
                p1_runs = pair_deliveries[pair_deliveries['striker_id'] == p1_id]['runs'].sum()
                p2_balls = len(pair_deliveries[pair_deliveries['striker_id'] == p2_id])
                p2_runs = pair_deliveries[pair_deliveries['striker_id'] == p2_id]['runs'].sum()

                pair_records.append({
                    'pair': f"{p1_name} & {p2_name}",
                    'deliveries_together': len(pair_deliveries),
                    'runs_scored': pair_deliveries['runs'].sum(),
                    'combined_sr': round(pair_deliveries['runs'].sum() / len(pair_deliveries) * 100.0, 2),
                    f'{p1_name}_contribution': f"{p1_runs} ({p1_balls}b)",
                    f'{p2_name}_contribution': f"{p2_runs} ({p2_balls}b)",
                })

    pair_df = pd.DataFrame(pair_records) if pair_records else pd.DataFrame(columns=['pair', 'deliveries_together', 'runs_scored', 'combined_sr'])

    return {
        'profiles': profile_df,
        'partnerships': pair_df,
    }


def run_all_scouting(df: pd.DataFrame) -> dict:
    """Run all scouting pipelines and export evidence tables."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    middle_order = scout_explosive_middle_order(df)
    middle_order.to_csv(OUTPUTS_DIR / 'scouting_explosive_middle_order.csv', index=False)

    indian_pace = scout_indian_fast_bowlers(df)
    indian_pace.to_csv(OUTPUTS_DIR / 'scouting_indian_fast_bowlers.csv', index=False)

    pp_pace = scout_phase_bowlers(df, 'powerplay', 'Pace')
    pp_pace.to_csv(OUTPUTS_DIR / 'scouting_powerplay_pace.csv', index=False)

    mid_pace = scout_phase_bowlers(df, 'middle', 'Pace')
    mid_pace.to_csv(OUTPUTS_DIR / 'scouting_middle_over_pace.csv', index=False)

    death_bowl = scout_phase_bowlers(df, 'death')
    death_bowl.to_csv(OUTPUTS_DIR / 'scouting_death_bowlers.csv', index=False)

    spin_support = scout_spin_support(df)
    spin_support.to_csv(OUTPUTS_DIR / 'scouting_spin_support.csv', index=False)

    combos = scout_batting_combinations(df)
    combos['profiles'].to_csv(OUTPUTS_DIR / 'scouting_batting_combo_profiles.csv', index=False)
    combos['partnerships'].to_csv(OUTPUTS_DIR / 'scouting_batting_combo_partnerships.csv', index=False)

    # Master Consolidated Scouting Report
    scouting_summary = pd.DataFrame([
        {'Role': 'Explosive No. 4/5 Batter', 'Top Candidate': middle_order.iloc[0]['player_name'], 'Key Evidence': f"{middle_order.iloc[0]['strike_rate']} SR, {middle_order.iloc[0]['boundary_pct']}% Bnd", 'Suitability Index': middle_order.iloc[0]['suitability_index']},
        {'Role': 'Experienced Indian Pace', 'Top Candidate': indian_pace.iloc[0]['player_name'], 'Key Evidence': f"{indian_pace.iloc[0]['wickets']} wkts, {indian_pace.iloc[0]['dot_pct']}% dots ({indian_pace.iloc[0]['identity_category']})", 'Suitability Index': indian_pace.iloc[0]['suitability_index']},
        {'Role': 'Powerplay Pace Specialist', 'Top Candidate': pp_pace.iloc[0]['player_name'], 'Key Evidence': f"{pp_pace.iloc[0]['dot_pct']}% dots, {pp_pace.iloc[0]['wickets']} PP wkts", 'Suitability Index': pp_pace.iloc[0]['suitability_index']},
        {'Role': 'Death-Over Bowling Reliability', 'Top Candidate': death_bowl.iloc[0]['player_name'], 'Key Evidence': f"{death_bowl.iloc[0]['wickets']} death wkts, {death_bowl.iloc[0]['bowler_strike_rate']} SR", 'Suitability Index': death_bowl.iloc[0]['suitability_index']},
        {'Role': 'Spin Support (Jadeja/Bishnoi)', 'Top Candidate': spin_support.iloc[0]['player_name'], 'Key Evidence': f"{spin_support.iloc[0]['bowling_type']}, {spin_support.iloc[0]['wickets']} wkts, {spin_support.iloc[0]['dot_pct']}% dots", 'Suitability Index': spin_support.iloc[0]['suitability_index']},
    ])
    scouting_summary.to_csv(OUTPUTS_DIR / 'RR_SQUAD_SCOUTING_REPORT.csv', index=False)

    return {
        'explosive_middle_order': middle_order,
        'indian_fast_bowlers': indian_pace,
        'powerplay_pace': pp_pace,
        'middle_over_pace': mid_pace,
        'death_bowlers': death_bowl,
        'spin_support': spin_support,
        'combo_profiles': combos['profiles'],
        'combo_partnerships': combos['partnerships'],
        'master_report': scouting_summary,
    }
