import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from config.settings import CHURN_DAYS_THRESHOLD
from database.mongo_client import get_customers_collection


def get_latest_transaction_date(client=None) -> datetime:
    """Finds the maximum invoice date in the database to use as the analysis snapshot date."""
    coll = get_customers_collection(client)
    res = list(coll.find({}, {"last_purchase_date": 1}).sort("last_purchase_date", -1).limit(1))
    if res and "last_purchase_date" in res[0]:
        return res[0]["last_purchase_date"]
    return datetime(2011, 12, 10)


def get_rfm_feature_pipeline(snapshot_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    MongoDB Aggregation Pipeline that computes RFM metrics and predictive churn features
    entirely at the database engine level.
    """
    if snapshot_date is None:
        snapshot_date = datetime(2011, 12, 10)

    return [
        {
            "$project": {
                "customer_id": 1,
                "country": 1,
                "first_purchase_date": 1,
                "last_purchase_date": 1,
                "frequency": {"$size": {"$ifNull": ["$orders", []]}},
                "monetary": {
                    "$round": [
                        {"$sum": "$orders.order_total"},
                        2
                    ]
                },
                "total_items": {
                    "$sum": "$orders.items_count"
                },
                # Recency in days from snapshot date
                "recency_days": {
                    "$round": [
                        {
                            "$divide": [
                                {"$subtract": [snapshot_date, "$last_purchase_date"]},
                                1000 * 60 * 60 * 24
                            ]
                        },
                        1
                    ]
                },
                # Customer tenure in days (days since first order)
                "tenure_days": {
                    "$round": [
                        {
                            "$divide": [
                                {"$subtract": [snapshot_date, "$first_purchase_date"]},
                                1000 * 60 * 60 * 24
                            ]
                        },
                        1
                    ]
                },
            }
        },
        {
            "$project": {
                "customer_id": 1,
                "country": 1,
                "recency_days": 1,
                "frequency": 1,
                "monetary": 1,
                "total_items": 1,
                "tenure_days": 1,
                # Average Order Value (AOV)
                "avg_order_value": {
                    "$round": [
                        {
                            "$cond": [
                                {"$gt": ["$frequency", 0]},
                                {"$divide": ["$monetary", "$frequency"]},
                                0
                            ]
                        },
                        2
                    ]
                },
                # Average items per order
                "avg_items_per_order": {
                    "$round": [
                        {
                            "$cond": [
                                {"$gt": ["$frequency", 0]},
                                {"$divide": ["$total_items", "$frequency"]},
                                0
                            ]
                        },
                        1
                    ]
                },
                # Churn Label: 1 if customer hasn't purchased in the last 90 days, else 0
                "is_churned": {
                    "$cond": [
                        {"$gte": ["$recency_days", CHURN_DAYS_THRESHOLD]},
                        1,
                        0
                    ]
                }
            }
        }
    ]


def load_rfm_dataframe(client=None) -> pd.DataFrame:
    """Executes the RFM aggregation pipeline and returns a cleaned Pandas DataFrame."""
    coll = get_customers_collection(client)
    latest_date = get_latest_transaction_date(client)
    pipeline = get_rfm_feature_pipeline(snapshot_date=latest_date)
    cursor = coll.aggregate(pipeline)
    df = pd.DataFrame(list(cursor))
    if "_id" in df.columns:
        df.drop(columns=["_id"], inplace=True)
    return df


def get_cohort_retention_data(client=None) -> pd.DataFrame:
    """
    MongoDB Aggregation Pipeline that unwinds customer orders to build
    a cohort retention matrix (Cohort Month vs Purchase Month Index).
    """
    coll = get_customers_collection(client)
    pipeline = [
        {"$unwind": "$orders"},
        {
            "$project": {
                "customer_id": 1,
                "cohort_month": {
                    "$dateToString": {"format": "%Y-%m", "date": "$first_purchase_date"}
                },
                "order_month": {
                    "$dateToString": {"format": "%Y-%m", "date": "$orders.invoice_date"}
                },
                "cohort_year": {"$year": "$first_purchase_date"},
                "cohort_mo": {"$month": "$first_purchase_date"},
                "order_year": {"$year": "$orders.invoice_date"},
                "order_mo": {"$month": "$orders.invoice_date"},
            }
        },
        {
            "$project": {
                "customer_id": 1,
                "cohort_month": 1,
                "order_month": 1,
                "month_index": {
                    "$add": [
                        {"$multiply": [{"$subtract": ["$order_year", "$cohort_year"]}, 12]},
                        {"$subtract": ["$order_mo", "$cohort_mo"]}
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "cohort_month": "$cohort_month",
                    "month_index": "$month_index"
                },
                "active_customers": {"$addToSet": "$customer_id"}
            }
        },
        {
            "$project": {
                "cohort_month": "$_id.cohort_month",
                "month_index": "$_id.month_index",
                "customer_count": {"$size": "$active_customers"}
            }
        },
        {"$sort": {"cohort_month": 1, "month_index": 1}}
    ]

    records = list(coll.aggregate(pipeline))
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df.drop(columns=["_id"], inplace=True, errors="ignore")

    # Pivot into triangular matrix: Cohort Month vs Month Index
    pivot_table = df.pivot(index="cohort_month", columns="month_index", values="customer_count")
    # Calculate retention rates as percentage of month 0
    cohort_sizes = pivot_table.iloc[:, 0]
    retention_matrix = pivot_table.divide(cohort_sizes, axis=0) * 100
    return retention_matrix.round(1)


def get_country_level_summary(client=None) -> List[Dict[str, Any]]:
    """MongoDB aggregation grouping customers by country with CLV & churn metrics."""
    coll = get_customers_collection(client)
    latest_date = get_latest_transaction_date(client)
    pipeline = [
        {
            "$project": {
                "country": 1,
                "total_orders": "$total_orders_count",
                "monetary": {"$sum": "$orders.order_total"},
                "recency_days": {
                    "$divide": [
                        {"$subtract": [latest_date, "$last_purchase_date"]},
                        1000 * 60 * 60 * 24
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$country",
                "total_customers": {"$sum": 1},
                "total_revenue": {"$sum": "$monetary"},
                "avg_orders_per_customer": {"$avg": "$total_orders"},
                "churned_customers": {
                    "$sum": {"$cond": [{"$gte": ["$recency_days", CHURN_DAYS_THRESHOLD]}, 1, 0]}
                }
            }
        },
        {
            "$project": {
                "country": "$_id",
                "total_customers": 1,
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "avg_orders_per_customer": {"$round": ["$avg_orders_per_customer", 1]},
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$churned_customers", "$total_customers"]}, 100]},
                        1
                    ]
                }
            }
        },
        {"$sort": {"total_revenue": -1}}
    ]
    return list(coll.aggregate(pipeline))
