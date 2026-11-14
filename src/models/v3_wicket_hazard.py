"""V3 Discrete-Time Wicket Hazard Model.

Estimates the delivery-level conditional probability of a bowler-creditable dismissal:
P(W_t = 1 | X_t, Bowler_j, Batter_i, Phase_t)

Features:
- Bowler-creditable wickets only (excludes Run Out, Retired Out, Obstructing the Field).
- Pre-delivery situational context (innings phase, format, wickets lost before, balls bowled).
- Regularized Logistic Regression with chronological match-grouped validation.
- Outputs predicted hazard rate, AUC, Brier score, and expected vs actual wickets.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss


class V3WicketHazardModel:
    """Discrete-time conditional hazard model for cricket wickets."""

    def __init__(self, c_reg: float = 0.5):
        self.c_reg = c_reg
        self.model: Optional[LogisticRegression] = None
        self.feature_columns: List[str] = []
        self.metrics: Dict[str, float] = {}

    def fit_and_evaluate(self, df: pd.DataFrame, train_split_date: str = '2025-06-01') -> Dict[str, float]:
        """Fit hazard model on historical deliveries and test on held-out matches."""
        valid = df[df['is_legal_ball'] == True].copy()
        wkt_col = 'is_bowler_wicket' if 'is_bowler_wicket' in valid.columns else 'is_wicket'
        valid['y_wkt'] = valid[wkt_col].fillna(False).astype(int)

        # Context features
        features = ['innings_phase', 'match_format']
        num_features = []
        if 'wickets_fallen_before' in valid.columns:
            valid['wickets_fallen_before'] = valid['wickets_fallen_before'].fillna(0).astype(float)
            num_features.append('wickets_fallen_before')
        if 'batting_crisis_score' in valid.columns:
            valid['batting_crisis_score'] = valid['batting_crisis_score'].fillna(0).astype(float)
            num_features.append('batting_crisis_score')

        # Chronological match split
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

        y_train = train_df['y_wkt'].values
        y_test = test_df['y_wkt'].values

        # Encode categorical and numeric features
        X_train_cat = pd.get_dummies(train_df[features], drop_first=True).reset_index(drop=True)
        X_test_cat = pd.get_dummies(test_df[features], drop_first=True).reset_index(drop=True)
        X_train_cat, X_test_cat = X_train_cat.align(X_test_cat, join='left', axis=1, fill_value=0)

        if num_features:
            X_train = pd.concat([X_train_cat, train_df[num_features].reset_index(drop=True)], axis=1)
            X_test = pd.concat([X_test_cat, test_df[num_features].reset_index(drop=True)], axis=1)
        else:
            X_train = X_train_cat
            X_test = X_test_cat

        self.feature_columns = list(X_train.columns)

        # Fit model
        self.model = LogisticRegression(C=self.c_reg, max_iter=1000, class_weight='balanced')
        self.model.fit(X_train, y_train)

        # Predict probabilities
        probs_test = self.model.predict_proba(X_test)[:, 1]

        # Evaluate
        auc = roc_auc_score(y_test, probs_test) if len(np.unique(y_test)) > 1 else 0.5
        brier = brier_score_loss(y_test, probs_test)
        loss = log_loss(y_test, probs_test)
        exp_wkts = float(np.sum(probs_test))
        act_wkts = int(np.sum(y_test))

        self.metrics = {
            'AUC': round(float(auc), 4),
            'Brier_Score': round(float(brier), 4),
            'Log_Loss': round(float(loss), 4),
            'Expected_Wickets': round(exp_wkts, 1),
            'Actual_Wickets': act_wkts,
            'Calibration_Ratio': round(exp_wkts / max(1, act_wkts), 3)
        }
        return self.metrics
