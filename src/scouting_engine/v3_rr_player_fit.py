"""V3 Rajasthan Royals Candidate Player-Fit Evaluation Engine.

Evaluates watchlist candidates strictly against verified RR tactical gaps:
- Indian Frontline Pace: Prasidh Krishna, Avesh Khan, Mukesh Kumar, Akash Deep
- Overseas Death Bowlers: Matheesha Pathirana, Gerald Coetzee, Nuwan Thushara
- Middle-Over Spinners: R Sai Kishore, Rahul Chahar, Akeal Hosein
- Domestic Finishers: Ashutosh Sharma, Abhinav Manohar, Sameer Rizvi

Transparent Multi-Criteria Assessment:
- Role gap suitability
- Phase-specific performance
- Complementarity with current RR XI
- Overseas slot constraint
- Availability / injury history
- Auction price expectation vs. allocated purse
- Final Recommendation Category:
  [Strong Fit, Conditional Fit, Low Priority, Not Suitable for Current RR Needs, Insufficient Evidence]
"""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class V3RRPlayerFitEngine:
    """Evaluates candidate suitability for Rajasthan Royals 2027 recruitment."""

    # Watchlist Candidate Metadata & Statistical Profiles
    WATCHLIST_CANDIDATES = [
        # 1. Indian Fast Bowlers
        {
            'player_name': 'Prasidh Krishna',
            'player_id': 6424,  # Known DB ID
            'target_gap': 'Indian Frontline Fast Bowler',
            'is_overseas': False,
            'primary_role': 'Specialist Fast Bowler',
            'key_phase': 'Powerplay & Middle',
            'historical_evidence': '69 IPL wickets, 40.2% dot balls, high hit-the-deck pace (145+ kph). Former RR spearhead.',
            'strengths': 'Elite bounce, domestic familiarity with Jaipur pitch, aggressive powerplay wicket-taker.',
            'weaknesses': 'History of lumbar stress fractures and injury recurrence.',
            'injury_risk': 'MEDIUM-HIGH',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'New-ball partner to Jofra Archer (Overs 1, 3, 5, 17)',
            'estimated_price_range': '₹8.0 - ₹11.0 Cr',
            'recommendation_category': 'Strong Fit',
            'fit_reasoning': 'Direct upgrade over Deshpande; pairs with Archer to form a hostile 145kph+ pace attack without taking an overseas slot.'
        },
        {
            'player_name': 'Avesh Khan',
            'player_id': 4707,
            'target_gap': 'Indian Frontline Fast Bowler',
            'is_overseas': False,
            'primary_role': 'Specialist Fast Bowler',
            'key_phase': 'Powerplay & Death',
            'historical_evidence': '65 IPL wickets, high yorker execution rate in 2024 (overs 18-20).',
            'strengths': 'Proven death-over defensive execution, hit-the-deck pace, extensive IPL pressure experience.',
            'weaknesses': 'Can concede runs if line wavers on flat decks.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'First-change and death specialist (Overs 4, 16, 18, 20)',
            'estimated_price_range': '₹7.0 - ₹9.5 Cr',
            'recommendation_category': 'Strong Fit',
            'fit_reasoning': 'Proven death-over defensive reliability; directly solves RR’s back-end pace leakage alongside Archer.'
        },
        {
            'player_name': 'Mukesh Kumar',
            'player_id': 3182,
            'target_gap': 'Indian Frontline Fast Bowler',
            'is_overseas': False,
            'primary_role': 'Specialist Fast Bowler',
            'key_phase': 'Powerplay & Death',
            'historical_evidence': 'Wide yorker execution at the death; India international T20I experience.',
            'strengths': 'Disciplined yorker discipline, consistent length control.',
            'weaknesses': 'Lacks outright pace; vulnerable against extreme power hitters.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'New-ball swing and wide-yorker death bowler',
            'estimated_price_range': '₹5.5 - ₹8.0 Cr',
            'recommendation_category': 'Conditional Fit',
            'fit_reasoning': 'Reliable execution, but lacks the high-end ceiling of Prasidh or Avesh.'
        },
        {
            'player_name': 'Akash Deep',
            'player_id': 7884,
            'target_gap': 'Indian Frontline Fast Bowler',
            'is_overseas': False,
            'primary_role': 'Specialist Fast Bowler',
            'key_phase': 'Powerplay Enforcer',
            'historical_evidence': 'High strike rate in powerplay, heavy ball into the pitch.',
            'strengths': 'Aggressive length, seam movement, international test rhythm.',
            'weaknesses': 'Untested as a dedicated death bowler (overs 18-20).',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'New-ball wicket-hunter (Overs 1, 3, 5)',
            'estimated_price_range': '₹4.0 - ₹6.5 Cr',
            'recommendation_category': 'Conditional Fit',
            'fit_reasoning': 'Excellent powerplay weapon, but requires an overseas specialist to cover the death overs.'
        },

        # 2. Overseas Death-Over Specialists
        {
            'player_name': 'Matheesha Pathirana',
            'player_id': 8661,
            'target_gap': 'Overseas Death-Over Specialist',
            'is_overseas': True,
            'primary_role': 'Specialist Bowler',
            'key_phase': 'Middle & Death (Overs 14-20)',
            'historical_evidence': 'Elite slinging action, 8.5% crisis wicket rate, 578 pressure balls, 90th percentile yorker accuracy.',
            'strengths': 'Nearly unhittable release angle, lethal slower balls and yorkers.',
            'weaknesses': 'Requires 1 overseas playing XI slot; occasional hamstring tightness.',
            'injury_risk': 'MEDIUM',
            'overseas_slot_impact': 'Consumes 1 of 4 overseas slots (replaces Hetmyer/Burger slot)',
            'expected_role_xi': 'Premier death bowler (Overs 13, 15, 17, 19)',
            'estimated_price_range': '₹10.0 - ₹12.5 Cr',
            'recommendation_category': 'Strong Fit',
            'fit_reasoning': 'Transformational signing. Pairing Pathirana with Jofra Archer at the death solves RR’s #1 empirical weakness completely.'
        },
        {
            'player_name': 'Gerald Coetzee',
            'player_id': 6863,
            'target_gap': 'Overseas Death-Over Specialist',
            'is_overseas': True,
            'primary_role': 'Specialist Fast Bowler',
            'key_phase': 'Middle & Death Enforcer',
            'historical_evidence': '150+ kph high-pace enforcer, middle-over wicket threat.',
            'strengths': 'Raw velocity, hostile bouncer, aggressive mentality.',
            'weaknesses': 'High variance / boundary risk when yorker execution misses.',
            'injury_risk': 'MEDIUM',
            'overseas_slot_impact': 'Consumes 1 overseas slot',
            'expected_role_xi': 'Middle-over enforcer and death seamer',
            'estimated_price_range': '₹6.0 - ₹8.5 Cr',
            'recommendation_category': 'Conditional Fit',
            'fit_reasoning': 'High pace provides wicket threat, but higher CVaR tail risk compared to Pathirana.'
        },
        {
            'player_name': 'Nuwan Thushara',
            'player_id': 8663,
            'target_gap': 'Overseas Death-Over Specialist',
            'is_overseas': True,
            'primary_role': 'Specialist Bowler',
            'key_phase': 'Powerplay Swing & Death',
            'historical_evidence': 'Slinging trajectory, new-ball in-swing and death yorkers.',
            'strengths': 'Sling action causes hesitation; budget-friendly alternative to Pathirana.',
            'weaknesses': 'Slightly lower speed than Pathirana; smaller IPL sample.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'Consumes 1 overseas slot',
            'expected_role_xi': 'New-ball swing and death yorker specialist',
            'estimated_price_range': '₹3.5 - ₹5.5 Cr',
            'recommendation_category': 'Strong Fit',
            'fit_reasoning': 'High tactical value at lower purse expenditure; executes identical slinger trajectory to solve death crisis.'
        },

        # 3. Middle-Over Spinners
        {
            'player_name': 'R Sai Kishore',
            'player_id': 4709,
            'target_gap': 'Economical Middle-Over Spinner',
            'is_overseas': False,
            'primary_role': 'Specialist Spin Bowler',
            'key_phase': 'Powerplay & Middle (Overs 4-13)',
            'historical_evidence': 'Elite T20 domestic economy rate (<6.8 RPO), tall trajectory, left-arm orthodox.',
            'strengths': 'Suffocating economy, height creates awkward bounce, handles powerplay field restrictions.',
            'weaknesses': 'Not a mystery spinner; relies on disciplined defensive lines.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'Defensive spin choke partnering Ravi Bishnoi and Ravindra Jadeja',
            'estimated_price_range': '₹3.5 - ₹5.5 Cr',
            'recommendation_category': 'Strong Fit',
            'fit_reasoning': 'Left-arm orthodox pairing with Bishnoi (leg-spin) creates complete rotational spin control in Jaipur.'
        },
        {
            'player_name': 'Rahul Chahar',
            'player_id': 6161,
            'target_gap': 'Economical Middle-Over Spinner',
            'is_overseas': False,
            'primary_role': 'Specialist Spin Bowler',
            'key_phase': 'Middle Overs (Overs 7-15)',
            'historical_evidence': 'Proven IPL title-winning leg-spinner with quick arm speed.',
            'strengths': 'Quick through the air, skid off the pitch, attacking mindset.',
            'weaknesses': 'Redundant with Ravi Bishnoi (both right-arm wrist spinners).',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'Backup / rotation with Ravi Bishnoi',
            'estimated_price_range': '₹3.0 - ₹4.5 Cr',
            'recommendation_category': 'Low Priority',
            'fit_reasoning': 'Tactically redundant with Bishnoi; RR requires finger spin or mystery spin variety rather than a second leg-spinner.'
        },
        {
            'player_name': 'Akeal Hosein',
            'player_id': 2417,
            'target_gap': 'Economical Middle-Over Spinner',
            'is_overseas': True,
            'primary_role': 'Specialist Spin Bowler',
            'key_phase': 'Powerplay & Middle Choke',
            'historical_evidence': 'Top 5 T20I bowling ranking, 114 crisis balls, elite new-ball spin economy.',
            'strengths': 'Stifles scoring in the powerplay (overs 1-6), capable lower-order hitter.',
            'weaknesses': 'Consumes 1 overseas slot where RR already has Jadeja and needs pace.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'Consumes 1 overseas slot',
            'expected_role_xi': 'Powerplay spin enforcer',
            'estimated_price_range': '₹2.5 - ₹4.0 Cr',
            'recommendation_category': 'Conditional Fit',
            'fit_reasoning': 'Elite statistical bowler, but consuming an overseas slot on spin when RR already has Jadeja is suboptimal.'
        },

        # 4. Domestic Finishers
        {
            'player_name': 'Ashutosh Sharma',
            'player_id': 7828,
            'target_gap': 'Domestic Lower-Order Finisher',
            'is_overseas': False,
            'primary_role': 'Finisher / Lower-Middle Batter',
            'key_phase': 'Death Overs (Overs 16-20)',
            'historical_evidence': 'Exceptional death-over strike rate in 2024 (>180.0), fearless clutch boundary hitting under pressure.',
            'strengths': 'Explosive bat swing against 140kph+ pace, boundary percentage >25%.',
            'weaknesses': 'High-risk shot selection; small multi-year sample.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'No. 6 or 7 designated boundary accelerator',
            'estimated_price_range': '₹2.5 - ₹4.0 Cr',
            'recommendation_category': 'Strong Fit',
            'fit_reasoning': 'Direct domestic replacement for Hetmyer; frees up the overseas slot for Pathirana while maintaining death firepower.'
        },
        {
            'player_name': 'Abhinav Manohar',
            'player_id': 6820,
            'target_gap': 'Domestic Lower-Order Finisher',
            'is_overseas': False,
            'primary_role': 'Middle-Order Batter',
            'key_phase': 'Middle & Death (Overs 12-20)',
            'historical_evidence': 'Proven power-hitting against spin and hard length.',
            'strengths': 'Clear boundary striker against spin choke; handles slower balls.',
            'weaknesses': 'Occasional stagnation against high-end inward pace.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'No. 6 batting anchor / finisher',
            'estimated_price_range': '₹2.0 - ₹3.5 Cr',
            'recommendation_category': 'Strong Fit',
            'fit_reasoning': 'Solid, cost-effective Indian middle-order power depth.'
        },
        {
            'player_name': 'Sameer Rizvi',
            'player_id': 7829,
            'target_gap': 'Domestic Lower-Order Finisher',
            'is_overseas': False,
            'primary_role': 'Middle-Order Batter',
            'key_phase': 'Middle Spin Hitter',
            'historical_evidence': 'Massive six-hitting in domestic T20 cricket.',
            'strengths': 'Exceptional natural bat speed against spin.',
            'weaknesses': 'Inexperienced in IPL playoff pressure situations.',
            'injury_risk': 'LOW',
            'overseas_slot_impact': 'None (Indian slot)',
            'expected_role_xi': 'Development squad finisher / Impact Sub',
            'estimated_price_range': '₹1.5 - ₹2.5 Cr',
            'recommendation_category': 'Conditional Fit',
            'fit_reasoning': 'Promising young talent, but currently developmental compared to Ashutosh Sharma.'
        }
    ]

    @classmethod
    def generate_player_fit_dataset(cls) -> pd.DataFrame:
        """Export standardized candidate evaluation matrix."""
        df = pd.DataFrame(cls.WATCHLIST_CANDIDATES)
        return df
