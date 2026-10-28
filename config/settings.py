import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "ecommerce_analytics"
COLLECTION_NAME = "customers"

# Model & Artifact configuration
MODEL_DIR = BASE_DIR / "models" / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CHURN_MODEL_PATH = MODEL_DIR / "churn_xgb.json"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.joblib"
KMEANS_MODEL_PATH = MODEL_DIR / "kmeans_rfm.joblib"
METRICS_PATH = MODEL_DIR / "evaluation_metrics.json"

RANDOM_STATE = 42

# Churn threshold: customers who have not purchased in the last 90 days of the observation window
CHURN_DAYS_THRESHOLD = 90
