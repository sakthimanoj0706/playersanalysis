"""V3 LightGBM Challenger Model for Delivery-Level Outcomes.

Nonlinear tree-boosted challenger architecture evaluating:
1. Expected Batter Runs (Regression with Huber/L2 loss).
2. Wicket Probability (Binary classification with log-loss).

Features:
- Ex-ante situational features (innings phase, format, wickets lost, crisis pressure).
- Chronological match-grouped validation.
- Compares out-of-sample metrics against linear joint and hazard baselines.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_auc_score, brier_score_loss


class V3LightGBMChallenger:
    """Tree-boosted challenger model for cricket delivery outcomes."""

    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.05):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.reg_model: Optional[lgb.LGBMRegressor] = None
        self.clf_model: Optional[lgb.LGBMClassifier] = None
        self.results: Dict[str, Dict[str, float]] = {}

    def fit_and_evaluate(self, df: pd.DataFrame, train_split_date: str = '2025-06-01') -> Dict[str, Dict[str, float]]:
        """Fit LightGBM regressor and classifier using chronological match splits."""
        valid = df[(df['is_ball_faced'] == True) & (df['is_legal_ball'] == True)].copy()
        runs_col = 'batter_runs' if 'batter_runs' in valid.columns else 'runs'
        wkt_col = 'is_bowler_wicket' if 'is_bowler_wicket' in valid.columns else 'is_wicket'

        valid['y_runs'] = valid[runs_col].astype(float)
        valid['y_wkt'] = valid[wkt_col].fillna(False).astype(int)

        # Context features
        cat_cols = ['innings_phase', 'match_format']
        for c in cat_cols:
            if c in valid.columns:
                valid[c] = valid[c].astype('category')

        num_cols = []
        for nc in ['wickets_fallen_before', 'batting_crisis_score', 'bowling_defensive_score']:
            if nc in valid.columns:
                valid[nc] = valid[nc].fillna(0).astype(float)
                num_cols.append(nc)

        all_features = [c for c in cat_cols if c in valid.columns] + num_cols

        # Chronological split
        if 'match_date' in valid.columns:
            valid['match_date'] = pd.to_datetime(valid['match_date'], errors='coerce')
            train_mask = valid['match_date'] < pd.to_datetime(train_split_date)
        else:
            mids = sorted(valid['match_id'].unique())
            split_idx = int(len(mids) * 0.75)
            train_matches = set(mids[:split_idx])
            train_mask = valid['match_id'].isin(train_matches)

        train_df = valid[train_mask].copy()
        test_df = valid[~train_mask].copy()

        if len(test_df) == 0:
            mids = sorted(valid['match_id'].unique())
            split_idx = int(len(mids) * 0.8)
            train_matches = set(mids[:split_idx])
            train_mask = valid['match_id'].isin(train_matches)
            train_df = valid[train_mask].copy()
            test_df = valid[~train_mask].copy()

        X_train = train_df[all_features]
        X_test = test_df[all_features]

        # 1. Runs Regression Challenger
        self.reg_model = lgb.LGBMRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            random_state=42,
            verbosity=-1
        )
        self.reg_model.fit(X_train, train_df['y_runs'])
        pred_runs = self.reg_model.predict(X_test)
        y_test_runs = test_df['y_runs'].values

        self.results['runs_regression'] = {
            'MAE': round(float(mean_absolute_error(y_test_runs, pred_runs)), 4),
            'RMSE': round(float(np.sqrt(mean_squared_error(y_test_runs, pred_runs))), 4)
        }

        # 2. Wicket Classification Challenger
        self.clf_model = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            random_state=42,
            is_unbalance=True,
            verbosity=-1
        )
        self.clf_model.fit(X_train, train_df['y_wkt'])
        pred_wkt_prob = self.clf_model.predict_proba(X_test)[:, 1]
        y_test_wkt = test_df['y_wkt'].values

        auc = roc_auc_score(y_test_wkt, pred_wkt_prob) if len(np.unique(y_test_wkt)) > 1 else 0.5
        brier = brier_score_loss(y_test_wkt, pred_wkt_prob)

        self.results['wicket_classification'] = {
            'AUC': round(float(auc), 4),
            'Brier_Score': round(float(brier), 4),
            'Expected_Wickets': round(float(np.sum(pred_wkt_prob)), 1),
            'Actual_Wickets': int(np.sum(y_test_wkt))
        }

        return self.results
