import argparse
import logging
from database.mongo_client import get_mongo_client, get_customers_collection
from database.aggregations import load_rfm_dataframe, get_country_level_summary
from models.rfm_segmentation import compute_rfm_segmentation
from models.churn_model import train_churn_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ECommerce-Master-Pipeline")


def run_pipeline(reingest: bool = False):
    client = get_mongo_client()
    coll = get_customers_collection(client)
    count = coll.count_documents({})

    logger.info(f"MongoDB Collection 'customers' has {count:,} documents.")

    if count == 0 or reingest:
        logger.info("Executing dataset extraction and ingestion into MongoDB...")
        from data.download_dataset import get_dataset
        from data.ingest_to_mongodb import clean_and_transform_retail_data, ingest_to_mongodb
        dataset_path = get_dataset()
        docs = clean_and_transform_retail_data(dataset_path)
        ingest_to_mongodb(docs, drop_existing=True)

    # Step 1: In-Database RFM Feature Aggregation
    logger.info("Step 1: Running MongoDB Aggregation Pipeline for RFM & Customer 360 features...")
    df_rfm = load_rfm_dataframe(client)
    logger.info(f"Aggregated {len(df_rfm):,} customer profiles.")

    # Step 2: RFM Segmentation & K-Means Clustering
    logger.info("Step 2: Performing RFM Persona mapping & Unsupervised K-Means clustering...")
    df_rfm, cluster_summary = compute_rfm_segmentation(df_rfm)
    logger.info("\n--- RFM Persona Breakdown ---")
    logger.info(f"\n{df_rfm['Customer_Persona'].value_counts()}")

    # Step 3: Predictive Churn Modeling (XGBoost)
    logger.info("Step 3: Training XGBoost Churn Prediction Classifier...")
    model, preprocessor, metrics = train_churn_model(df_rfm)
    logger.info(f"Churn Model ROC-AUC: {metrics['roc_auc']} | PR-AUC: {metrics['pr_auc']} | F1: {metrics['f1_score']}")

    # Step 4: Top Country Highlights
    logger.info("Step 4: Executing Country-Level Revenue & Churn Aggregation...")
    country_stats = get_country_level_summary(client)[:5]
    logger.info("Top 5 Countries by Revenue:")
    for c in country_stats:
        logger.info(f"  - {c['country']}: Revenue £{c['total_revenue']:,} | Customers: {c['total_customers']:,} | Churn Rate: {c['churn_rate_pct']}%")

    logger.info("\n🎉 All pipeline stages completed successfully!")
    logger.info("You can now launch the dashboard: .\\.venv\\Scripts\\streamlit.exe run app/dashboard.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-Commerce Customer 360 & Churn Pipeline")
    parser.add_argument("--reingest", action="store_true", help="Force re-ingestion of raw dataset")
    args = parser.parse_args()

    run_pipeline(reingest=args.reingest)
