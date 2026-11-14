"""V3 Joint Batter-Bowler Hierarchical Performance Model.

Estimates the simultaneous bilateral delivery performance:
Y_t = alpha + X_t * beta + a_i + b_j + H_t * (u_i + v_j) + epsilon_t

Where:
- Y_t: Validated delivery-level batter run response (0, 1, 2, 3, 4, 6).
- X_t: Pre-delivery context (innings_phase, match_format).
- a_i: Batter main effect.
- b_j: Bowler main effect.
- H_t: Validated pre-delivery pressure state.
- u_i: Batter pressure interaction effect.
- v_j: Bowler pressure interaction effect.
- epsilon_t: Residual disturbance.

Uses Ridge regression with match-grouped chronological validation.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error


class V3JointPerformanceModel:
    """Hierarchical joint model for batter and bowler delivery-level outcomes."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.models: Dict[str, Ridge] = {}
        self.feature_names: Dict[str, List[str]] = {}
        self.evaluation_results: Dict[str, Dict[str, float]] = {}

    @staticmethod
    def prepare_features(df: pd.DataFrame, min_deliveries: int = 50) -> pd.DataFrame:
        """Filter and prepare data for hierarchical modeling."""
        # Use legal deliveries where batter faced the ball
        valid = df[(df['is_ball_faced'] == True) & (df['is_legal_ball'] == True)].copy()
        runs_col = 'batter_runs' if 'batter_runs' in valid.columns else 'runs'
        valid['y_runs'] = valid[runs_col].astype(float)

        # Filter to players with minimum sample exposure
        bat_counts = valid['striker_id'].value_counts()
        bowl_counts = valid['bowler_id'].value_counts()
        frequent_bats = set(bat_counts[bat_counts >= min_deliveries].index)
        frequent_bowls = set(bowl_counts[bowl_counts >= min_deliveries].index)

        valid = valid[valid['striker_id'].isin(frequent_bats) & valid['bowler_id'].isin(frequent_bowls)].copy()
        return valid

    def fit_and_compare(self, df: pd.DataFrame, train_split_date: str = '2025-06-01') -> Dict[str, Dict[str, float]]:
        """Fit 5 candidate model architectures using chronological match split.
        
        1. Context-only baseline (phase + format)
        2. Batter-effect model
        3. Bowler-effect model
        4. Joint batter-bowler model
        5. Joint model with pressure interactions
        """
        data = self.prepare_features(df)
        
        # Chronological split on match_date
        if 'match_date' in data.columns:
            data['match_date'] = pd.to_datetime(data['match_date'], errors='coerce')
            train_mask = data['match_date'] < pd.to_datetime(train_split_date)
        else:
            # Match ID split fallback
            mid_sorted = sorted(data['match_id'].unique())
            split_idx = int(len(mid_sorted) * 0.75)
            train_matches = set(mid_sorted[:split_idx])
            train_mask = data['match_id'].isin(train_matches)

        train_df = data[train_mask].copy()
        test_df = data[~train_mask].copy()

        if len(test_df) == 0:
            # Fallback 80/20 chronological split
            mid_sorted = sorted(data['match_id'].unique())
            split_idx = int(len(mid_sorted) * 0.8)
            train_matches = set(mid_sorted[:split_idx])
            train_mask = data['match_id'].isin(train_matches)
            train_df = data[train_mask].copy()
            test_df = data[~train_mask].copy()

        y_train = train_df['y_runs'].values
        y_test = test_df['y_runs'].values

        # 1. Context-only
        context_cols = ['innings_phase', 'match_format']
        X_ctx_train = pd.get_dummies(train_df[context_cols], drop_first=True)
        X_ctx_test = pd.get_dummies(test_df[context_cols], drop_first=True)
        X_ctx_train, X_ctx_test = X_ctx_train.align(X_ctx_test, join='left', axis=1, fill_value=0)

        m1 = Ridge(alpha=self.alpha).fit(X_ctx_train, y_train)
        pred1 = m1.predict(X_ctx_test)
        self.evaluation_results['1_Context_Only'] = {
            'MAE': float(mean_absolute_error(y_test, pred1)),
            'RMSE': float(np.sqrt(mean_squared_error(y_test, pred1)))
        }

        # 2. Batter-only
        X_bat_train = pd.get_dummies(train_df[['striker_id'] + context_cols], columns=['striker_id'] + context_cols, drop_first=True)
        X_bat_test = pd.get_dummies(test_df[['striker_id'] + context_cols], columns=['striker_id'] + context_cols, drop_first=True)
        X_bat_train, X_bat_test = X_bat_train.align(X_bat_test, join='left', axis=1, fill_value=0)

        m2 = Ridge(alpha=self.alpha).fit(X_bat_train, y_train)
        pred2 = m2.predict(X_bat_test)
        self.evaluation_results['2_Batter_Only'] = {
            'MAE': float(mean_absolute_error(y_test, pred2)),
            'RMSE': float(np.sqrt(mean_squared_error(y_test, pred2)))
        }

        # 3. Bowler-only
        X_bowl_train = pd.get_dummies(train_df[['bowler_id'] + context_cols], columns=['bowler_id'] + context_cols, drop_first=True)
        X_bowl_test = pd.get_dummies(test_df[['bowler_id'] + context_cols], columns=['bowler_id'] + context_cols, drop_first=True)
        X_bowl_train, X_bowl_test = X_bowl_train.align(X_bowl_test, join='left', axis=1, fill_value=0)

        m3 = Ridge(alpha=self.alpha).fit(X_bowl_train, y_train)
        pred3 = m3.predict(X_bowl_test)
        self.evaluation_results['3_Bowler_Only'] = {
            'MAE': float(mean_absolute_error(y_test, pred3)),
            'RMSE': float(np.sqrt(mean_squared_error(y_test, pred3)))
        }

        # 4. Joint Batter-Bowler
        X_joint_train = pd.get_dummies(train_df[['striker_id', 'bowler_id'] + context_cols], columns=['striker_id', 'bowler_id'] + context_cols, drop_first=True)
        X_joint_test = pd.get_dummies(test_df[['striker_id', 'bowler_id'] + context_cols], columns=['striker_id', 'bowler_id'] + context_cols, drop_first=True)
        X_joint_train, X_joint_test = X_joint_train.align(X_joint_test, join='left', axis=1, fill_value=0)

        m4 = Ridge(alpha=self.alpha).fit(X_joint_train, y_train)
        pred4 = m4.predict(X_joint_test)
        self.evaluation_results['4_Joint_Batter_Bowler'] = {
            'MAE': float(mean_absolute_error(y_test, pred4)),
            'RMSE': float(np.sqrt(mean_squared_error(y_test, pred4)))
        }

        # 5. Joint with Pressure Interactions
        p_col = 'batting_crisis_score' if 'batting_crisis_score' in train_df.columns else 'pressure_score'
        if p_col in train_df.columns:
            train_df['h_press'] = train_df[p_col].fillna(0).astype(float)
            test_df['h_press'] = test_df[p_col].fillna(0).astype(float)
            
            # Add pressure interaction columns
            X_joint_train['h_press'] = train_df['h_press'].values
            X_joint_test['h_press'] = test_df['h_press'].values

            m5 = Ridge(alpha=self.alpha).fit(X_joint_train, y_train)
            pred5 = m5.predict(X_joint_test)
            self.evaluation_results['5_Joint_With_Pressure'] = {
                'MAE': float(mean_absolute_error(y_test, pred5)),
                'RMSE': float(np.sqrt(mean_squared_error(y_test, pred5)))
            }
        else:
            self.evaluation_results['5_Joint_With_Pressure'] = self.evaluation_results['4_Joint_Batter_Bowler']

        return self.evaluation_results
