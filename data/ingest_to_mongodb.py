import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from config.settings import DB_NAME, COLLECTION_NAME, BASE_DIR
from database.mongo_client import get_mongo_client
from database.validation_setup import apply_schema_validation

DATA_DIR = BASE_DIR / "data" / "raw"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataIngestion")


def clean_and_transform_retail_data(excel_path: Path):
    logger.info(f"Loading raw retail transactions from {excel_path}...")
    df = pd.read_excel(excel_path)
    logger.info(f"Loaded raw dataset with {len(df):,} records.")

    # 1. Clean missing customer IDs
    df = df.dropna(subset=["CustomerID"])
    df["CustomerID"] = df["CustomerID"].astype(int).astype(str)

    # 2. Filter out cancellations (Invoices starting with 'C') and non-positive values
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df = df[~df["InvoiceNo"].str.startswith("C")]
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]

    # 3. Clean strings & timestamps
    df["Description"] = df["Description"].fillna("UNKNOWN").astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["Country"] = df["Country"].astype(str).str.strip()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["LineTotal"] = (df["Quantity"] * df["UnitPrice"]).round(2)

    logger.info(f"Cleaned dataset: {len(df):,} valid purchase items across {df['CustomerID'].nunique():,} unique customers.")

    # 4. Group by Customer to construct Customer 360 nested documents
    logger.info("Transforming tabular rows into Customer 360 nested documents...")
    customer_docs = []

    grouped_customers = df.groupby("CustomerID")

    for cust_id, cust_group in grouped_customers:
        orders = []
        cust_group_sorted = cust_group.sort_values(by="InvoiceDate")
        country = cust_group_sorted["Country"].iloc[-1]  # Most recent country
        first_purchase = cust_group_sorted["InvoiceDate"].iloc[0].to_pydatetime()
        last_purchase = cust_group_sorted["InvoiceDate"].iloc[-1].to_pydatetime()

        for inv_no, inv_group in cust_group_sorted.groupby("InvoiceNo", sort=False):
            inv_date = inv_group["InvoiceDate"].iloc[0].to_pydatetime()
            items = []
            for _, row in inv_group.iterrows():
                items.append({
                    "stock_code": row["StockCode"],
                    "description": row["Description"],
                    "quantity": int(row["Quantity"]),
                    "unit_price": float(row["UnitPrice"]),
                    "line_total": float(row["LineTotal"]),
                })
            
            order_total = round(float(inv_group["LineTotal"].sum()), 2)
            orders.append({
                "invoice_no": inv_no,
                "invoice_date": inv_date,
                "order_total": order_total,
                "items_count": len(items),
                "items": items,
            })

        customer_docs.append({
            "customer_id": cust_id,
            "country": country,
            "first_purchase_date": first_purchase,
            "last_purchase_date": last_purchase,
            "total_orders_count": len(orders),
            "orders": orders,
        })

    logger.info(f"Constructed {len(customer_docs):,} Customer 360 documents.")
    return customer_docs


def ingest_to_mongodb(customer_docs, drop_existing: bool = True):
    client = get_mongo_client()
    db = client[DB_NAME]
    coll = db[COLLECTION_NAME]

    if drop_existing:
        logger.info(f"Dropping collection '{COLLECTION_NAME}' for fresh ingestion...")
        coll.drop()

    # Apply schema validation
    logger.info("Applying $jsonSchema validation rules...")
    apply_schema_validation(client=client, enforce_strict=True)

    # Bulk insert documents in batches
    batch_size = 500
    total = len(customer_docs)
    logger.info(f"Ingesting {total:,} Customer 360 documents into MongoDB in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = customer_docs[i:i + batch_size]
        coll.insert_many(batch)
        logger.info(f"Inserted batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size} ({min(i + batch_size, total)}/{total})")

    logger.info("Ingestion completed successfully!")


if __name__ == "__main__":
    from data.download_dataset import get_dataset
    dataset_path = get_dataset()
    docs = clean_and_transform_retail_data(dataset_path)
    ingest_to_mongodb(docs)
