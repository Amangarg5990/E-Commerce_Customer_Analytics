import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
import xgboost as xgb
import shap

from config.settings import (
    CHURN_MODEL_PATH,
    PREPROCESSOR_PATH,
    METRICS_PATH,
    RANDOM_STATE,
    MODEL_DIR,
)
from database.aggregations import load_rfm_dataframe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ChurnModel")


def build_preprocessor(categorical_features, numeric_features):
    numeric_transformer = Pipeline(steps=[
        ("scaler", StandardScaler()),
    ])

    categorical_transformer = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )


def train_churn_model(df: pd.DataFrame = None):
    if df is None:
        df = load_rfm_dataframe()

    logger.info(f"Loaded {len(df):,} customer records for churn predictive modeling.")

    # Target variable: is_churned (1 if recency >= 90 days, else 0)
    y = df["is_churned"].astype(int)

    # Top countries grouping (collapse infrequent countries into 'Other' to avoid high dimensionality)
    top_countries = df["country"].value_counts().head(5).index.tolist()
    df["country_clean"] = df["country"].apply(lambda c: c if c in top_countries else "Other")

    # Features: Exclude 'recency_days' to prevent data leakage!
    # Behavioral features predict churn without leaking the label definition.
    feature_cols = [
        "frequency",
        "monetary",
        "total_items",
        "tenure_days",
        "avg_order_value",
        "avg_items_per_order",
        "country_clean",
    ]

    X = df[feature_cols].copy()
    numeric_features = [
        "frequency",
        "monetary",
        "total_items",
        "tenure_days",
        "avg_order_value",
        "avg_items_per_order",
    ]
    categorical_features = ["country_clean"]

    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )

    # Preprocessor
    preprocessor = build_preprocessor(categorical_features, numeric_features)
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_names = list(cat_encoder.get_feature_names_out(categorical_features))
    all_feature_names = numeric_features + cat_names

    # Imbalance ratio
    neg_count = sum(y_train == 0)
    pos_count = sum(y_train == 1)
    scale_pos_weight = neg_count / max(1, pos_count)
    logger.info(f"Class distribution: {neg_count} active vs {pos_count} churned (scale_pos_weight={scale_pos_weight:.2f})")

    # Train XGBoost Classifier
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight,
        random_state=RANDOM_STATE,
        eval_metric="auc",
        early_stopping_rounds=20,
    )

    model.fit(
        X_train_proc,
        y_train,
        eval_set=[(X_test_proc, y_test)],
        verbose=False,
    )

    # Evaluation
    y_prob = model.predict_proba(X_test_proc)[:, 1]
    y_pred = (y_prob >= 0.50).astype(int)

    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": cm,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_names": all_feature_names,
        "raw_features": feature_cols,
        "top_countries": top_countries,
    }

    logger.info("--- Churn Model Evaluation ---")
    logger.info(f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | F1: {f1:.4f} | Accuracy: {acc:.4f}")
    logger.info(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")

    # Save artifacts
    model.save_model(str(CHURN_MODEL_PATH))
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    return model, preprocessor, metrics


if __name__ == "__main__":
    train_churn_model()
