import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from config.settings import KMEANS_MODEL_PATH, RANDOM_STATE
from database.aggregations import load_rfm_dataframe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RFMSegmentation")


def assign_rfm_persona(row: pd.Series) -> str:
    """Assigns business-friendly personas based on R, F, M quartile scores (1-4)."""
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
    
    if r >= 3 and f >= 3 and m >= 3:
        return "Champions"
    elif f >= 3 and m >= 3:
        return "Loyal Customers"
    elif r >= 3 and f >= 2:
        return "Potential Loyalists"
    elif r >= 3 and f == 1:
        return "New Customers"
    elif r == 2 and f >= 2:
        return "Need Attention"
    elif r <= 2 and (f >= 2 or m >= 2):
        return "At Risk"
    else:
        return "Hibernating / Churned"


def compute_rfm_segmentation(df: pd.DataFrame = None):
    """
    Performs dual RFM Segmentation:
    1. Quantile-based RFM Scoring & Personas
    2. Unsupervised K-Means Clustering on log-transformed normalized features
    """
    if df is None:
        df = load_rfm_dataframe()

    logger.info(f"Computing RFM segmentation for {len(df):,} customers...")

    # Filter out any non-positive monetary/frequency values if present
    df = df[df["monetary"] > 0].copy()

    # 1. Quantile Scoring (1 to 4)
    # Recency: lower is better (so reverse scoring)
    df["R_Score"] = pd.qcut(df["recency_days"], q=4, labels=[4, 3, 2, 1], duplicates="drop").astype(int)
    # Frequency: higher is better
    df["F_Score"] = pd.qcut(df["frequency"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
    # Monetary: higher is better
    df["M_Score"] = pd.qcut(df["monetary"], q=4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)

    df["RFM_Segment"] = df["R_Score"].astype(str) + df["F_Score"].astype(str) + df["M_Score"].astype(str)
    df["RFM_Score"] = df["R_Score"] + df["F_Score"] + df["M_Score"]
    df["Customer_Persona"] = df.apply(assign_rfm_persona, axis=1)

    # 2. Unsupervised K-Means Clustering
    # Log-transform to handle high positive skew in e-commerce spend
    rfm_features = ["recency_days", "frequency", "monetary"]
    rfm_log = np.log1p(df[rfm_features])

    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm_log)

    k = 4
    kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    df["KMeans_Cluster"] = kmeans.fit_predict(rfm_scaled)

    sil_score = silhouette_score(rfm_scaled, df["KMeans_Cluster"])
    logger.info(f"Fitted KMeans ({k} clusters) with Silhouette Score: {sil_score:.3f}")

    # Cluster summary
    cluster_summary = df.groupby("KMeans_Cluster")[rfm_features].mean().round(1)
    logger.info(f"K-Means Cluster Profiling:\n{cluster_summary}")

    # Save artifacts
    artifacts = {
        "scaler": scaler,
        "kmeans": kmeans,
        "silhouette_score": sil_score,
        "rfm_features": rfm_features,
    }
    joblib.dump(artifacts, KMEANS_MODEL_PATH)
    logger.info(f"Saved KMeans clustering pipeline to {KMEANS_MODEL_PATH}")

    return df, cluster_summary


if __name__ == "__main__":
    df, summary = compute_rfm_segmentation()
    print("Persona Distribution:")
    print(df["Customer_Persona"].value_counts())
