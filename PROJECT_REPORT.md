# Technical Project Report

# E-Commerce Customer 360° & Behavioral Analytics Engine
### Big Data Document Modeling, In-Database Feature Engineering, and Predictive Machine Learning on MongoDB Atlas

---

**Project Type:** Database Engineering & Predictive Analytics Capstone  
**Database System:** MongoDB Atlas Cloud Cluster (`v8.x`)  
**Programming Language:** Python 3.13  
**Core Technologies:** PyMongo, Scikit-Learn, XGBoost, Pandas, Plotly, Streamlit  
**Dataset:** UCI Machine Learning Repository — Online Retail Dataset (541,909 Transactions)  
**Project Workspace:** `d:\MongoDB`  
**Execution Date:** October 2026  

---

## 📑 Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Technical Motivation](#2-problem-statement--technical-motivation)
3. [Dataset Description & Preprocessing Pipeline](#3-dataset-description--preprocessing-pipeline)
4. [MongoDB Database Architecture & Schema Design](#4-mongodb-database-architecture--schema-design)
5. [Database Governance: `$jsonSchema` Validation & Indexing](#5-database-governance-jsonschema-validation--indexing)
6. [In-Database MongoDB Aggregation Framework](#6-in-database-mongodb-aggregation-framework)
7. [Machine Learning Methodology](#7-machine-learning-methodology)
8. [System Architecture & Data Flow](#8-system-architecture--data-flow)
9. [Web Presentation Tier (Streamlit Dashboard)](#9-web-presentation-tier-streamlit-dashboard)
10. [Experimental Results & Business Insights](#10-experimental-results--business-insights)
11. [Conclusion & Future Enhancements](#11-conclusion--future-enhancements)
12. [Appendix: Replication & CLI Execution Guide](#12-appendix-replication--cli-execution-guide)

---

## 1. Executive Summary

In contemporary e-commerce enterprises, understanding customer lifetime behavior, segmenting purchasing personas, and anticipating churn are critical to sustainable revenue growth. Traditional relational database management systems (RDBMS) struggle with query degradation when running analytical joins across millions of transaction rows.

This project designs and implements an end-to-end, production-grade **Customer 360 Analytics Platform** built around **MongoDB Atlas**. Key accomplishments include:
* **Customer 360 Document Modeling:** Re-engineered 541,909 flat retail transaction rows into 4,338 rich, hierarchical customer profiles with embedded orders and line items, completely eliminating multi-table relational `JOIN` operations.
* **Database Governance:** Enforced strict document structure, required keys, and BSON type safety directly at the database engine level using MongoDB **`$jsonSchema`** validation.
* **In-Database Aggregations:** Utilized MongoDB’s aggregation pipeline to compute Recency-Frequency-Monetary (RFM) vectors, Customer Lifetime Value (CLV), and monthly triangular cohort retention matrices entirely in C++ database memory before handing data to downstream Python consumers.
* **Dual Machine Learning Framework:**
  1. *Unsupervised RFM Clustering:* Log-transformed normalized clustering via **K-Means (`k=4`)** yielding a Silhouette Score of **`0.337`** and mapping customers to actionable personas (*Champions*, *Loyal Customers*, *At Risk*, *Hibernating*).
  2. *Predictive Churn Modeling:* Trained an **XGBoost Classifier** on behavioral engagement signals (without recency target leakage), achieving an exceptional **ROC-AUC of `0.9558`**, **PR-AUC of `0.9292`**, and overall accuracy of **`87.00%`**.
* **Enterprise Web Dashboard:** Deployed a clean, light-themed **Streamlit** dashboard delivering executive KPI scorecards, interactive RFM 2D/3D scatter plots, cohort retention heatmaps, and instantaneous single-customer point lookups with real-time churn risk gauges.

---

## 2. Problem Statement & Technical Motivation

### 2.1 The Limitations of Normalized Relational Schemas (RDBMS)
In classical third-normal-form (3NF) relational architectures, e-commerce data is fragmented across distinct tables:
$$\text{Customers} \longleftrightarrow \text{Invoices} \longleftrightarrow \text{Invoice\_Items} \longleftrightarrow \text{Products}$$

When querying a complete customer profile (Customer 360) or aggregating lifetime spend, the relational engine must perform repeated multi-table nested loop or hash joins. At scale, this results in:
1. **Severe Latency Spikes:** Joins across millions of purchase rows degrade query latency from milliseconds to tens of seconds.
2. **Locking & Concurrency Bottlenecks:** Table-level and row-level locks under concurrent read/write workloads reduce throughput.
3. **Loss of Caching Locality:** Relational pages store rows horizontally across disconnected memory addresses, defeating CPU cache prefetching.

### 2.2 The MongoDB Document Solution
MongoDB resolves these operational bottlenecks through **Embedded Document Modeling**:
* **Locality of Reference:** By embedding `orders` and `items` within the parent `customer` document, all data pertaining to a single customer is co-located in contiguous disk and memory pages.
* **$O(1)$ Point Lookups:** Fetching an entire customer profile requires a single indexed B-tree point query.
* **Single-Document Atomicity:** Updates to customer orders and lifetime statistics are executed atomically without the overhead of distributed two-phase locking.

---

## 3. Dataset Description & Preprocessing Pipeline

### 3.1 Dataset Overview
The project utilizes the **Online Retail Dataset** sourced from the UCI Machine Learning Repository. It contains all real transactions occurring between December 1, 2010, and December 9, 2011, for a UK-based registered non-store online retailer specializing in unique giftware.

* **Raw Observations:** 541,909 records
* **Initial Attributes:** `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`

### 3.2 Cleaning & Transformation Engine (`data/ingest_to_mongodb.py`)
Prior to MongoDB ingestion, a Python preprocessing engine cleanses the data:
1. **Null Customer Filtering:** Rows lacking a valid `CustomerID` (guest checkouts) are pruned ($135,080$ records).
2. **Cancellation Filtering:** Invoices prefixed with `"C"` (order cancellations, credit memos) or records with non-positive quantities ($Quantity \le 0$) or zero unit prices ($UnitPrice \le 0$) are removed ($8,905$ records).
3. **Derived Attribute Calculation:** A `LineTotal` attribute is computed for every transaction item:
   $$\text{LineTotal} = \text{Quantity} \times \text{UnitPrice}$$
4. **Hierarchical Document Construction:** The flat tabular purchases ($397,884$ clean items) are grouped by `CustomerID` and nested by `InvoiceNo`, calculating each order's `order_total` and basket size.
5. **Output Cohort:** Exactly **4,338 unique customer documents** are generated.

---

## 4. MongoDB Database Architecture & Schema Design

### 4.1 Physical Deployment
* **Cluster:** MongoDB Atlas connection configured through the `MONGO_URI` environment variable
* **Database Name:** `ecommerce_analytics`
* **Collection:** `customers` (Storage: WiredTiger storage engine with Snappy block compression)

### 4.2 Document Schema Definition
Below is an annotated BSON document representing the Customer 360 data model:

```json
{
  "_id": ObjectId("67207c4b1234567890abcdef"),
  "customer_id": "17850",
  "country": "United Kingdom",
  "first_purchase_date": ISODate("2010-12-01T08:26:00.000Z"),
  "last_purchase_date": ISODate("2011-02-10T14:38:00.000Z"),
  "total_orders_count": 34,
  "orders": [
    {
      "invoice_no": "536365",
      "invoice_date": ISODate("2010-12-01T08:26:00.000Z"),
      "order_total": 139.12,
      "items_count": 7,
      "items": [
        {
          "stock_code": "85123A",
          "description": "WHITE HANGING HEART T-LIGHT HOLDER",
          "quantity": 6,
          "unit_price": 2.55,
          "line_total": 15.30
        },
        {
          "stock_code": "71053",
          "description": "WHITE METAL LANTERN",
          "quantity": 6,
          "unit_price": 3.39,
          "line_total": 20.34
        }
      ]
    }
  ]
}
```

---

## 5. Database Governance: `$jsonSchema` Validation & Indexing

### 5.1 Collection Validation Rules (`config/schema_validation.json`)
To maintain database integrity in production environments, collection-level validation rules are enforced using `$jsonSchema`:
* **Validation Level:** `strict` (All inserts and updates must conform).
* **Validation Action:** `error` (Invalid documents are rejected).
* **Key Constraints Enforced:**
  * `customer_id`: Required string.
  * `country`: Required string.
  * `first_purchase_date` & `last_purchase_date`: Required BSON dates.
  * `total_orders_count`: Numeric integer/long $\ge 1$.
  * `orders`: Array of objects; each object must contain `invoice_no` (string), `invoice_date` (date), and a valid `items` array.

### 5.2 High-Performance Indexing Strategy
To optimize point lookups, sorting, and aggregation stages, secondary B-tree indexes were created:

| Index Name | Index Key Specification | Type | Query Pattern / Optimization Purpose |
| :--- | :--- | :--- | :--- |
| `customer_id_1` | `{ customer_id: 1 }` | **Unique B-Tree** | Point lookup ($O(1)$) & primary business key deduplication |
| `country_1` | `{ country: 1 }` | **B-Tree** | Fast filtering for regional market analytics ($group stage) |
| `last_purchase_date_1` | `{ last_purchase_date: 1 }` | **B-Tree** | Range scans for Recency calculations and churn thresholding |
| `first_purchase_date_1` | `{ first_purchase_date: 1 }` | **B-Tree** | Cohort acquisition window grouping |
| `total_orders_count_1` | `{ total_orders_count: 1 }` | **B-Tree** | VIP repeat buyer segmentation queries |

> **Query Optimizer Verification:** Executing `db.customers.find({ customer_id: "17850" }).explain("executionStats")` confirms `stage: "IXSCAN"` with `totalDocsExamined: 1`, verifying zero full-collection scans (`COLLSCAN`).

---

## 6. In-Database MongoDB Aggregation Framework

Instead of pulling massive JSON payloads into application memory, feature engineering is offloaded to MongoDB’s C++ engine.

### 6.1 In-Database RFM & Churn Feature Extraction Pipeline
This multi-stage pipeline extracts analytical vectors for downstream machine learning:

$$\text{Recency (Days)} = \frac{\text{SnapshotDate} - \text{LastPurchaseDate}}{1000 \times 60 \times 60 \times 24}$$
$$\text{Average Order Value (AOV)} = \frac{\text{Cumulative Spend (Monetary)}}{\text{Total Orders (Frequency)}}$$
$$\text{Churn Flag} = \begin{cases} 1, & \text{if } \text{Recency} \ge 90 \text{ days} \\ 0, & \text{otherwise} \end{cases}$$

#### Pipeline Definition:
```javascript
db.customers.aggregate([
  {
    $project: {
      customer_id: 1,
      country: 1,
      frequency: { $size: { $ifNull: ["$orders", []] } },
      monetary: { $round: [{ $sum: "$orders.order_total" }, 2] },
      total_items: { $sum: "$orders.items_count" },
      recency_days: {
        $round: [
          { $divide: [{ $subtract: [ISODate("2011-12-10T00:00:00Z"), "$last_purchase_date"] }, 86400000] },
          1
        ]
      },
      tenure_days: {
        $round: [
          { $divide: [{ $subtract: [ISODate("2011-12-10T00:00:00Z"), "$first_purchase_date"] }, 86400000] },
          1
        ]
      }
    }
  },
  {
    $project: {
      customer_id: 1,
      country: 1,
      recency_days: 1,
      frequency: 1,
      monetary: 1,
      avg_order_value: {
        $round: [
          { $cond: [{ $gt: ["$frequency", 0] }, { $divide: ["$monetary", "$frequency"] }, 0] },
          2
        ]
      },
      is_churned: {
        $cond: [{ $gte: ["$recency_days", 90] }, 1, 0]
      }
    }
  }
]);
```

### 6.2 Monthly Triangular Cohort Retention Pipeline
By unwinding the embedded `orders` array, this pipeline tracks repeat purchase activity across customer acquisition cohorts:
```javascript
db.customers.aggregate([
  { $unwind: "$orders" },
  {
    $project: {
      customer_id: 1,
      cohort_month: { $dateToString: { format: "%Y-%m", date: "$first_purchase_date" } },
      order_month: { $dateToString: { format: "%Y-%m", date: "$orders.invoice_date" } },
      cohort_year: { $year: "$first_purchase_date" },
      cohort_mo: { $month: "$first_purchase_date" },
      order_year: { $year: "$orders.invoice_date" },
      order_mo: { $month: "$orders.invoice_date" }
    }
  },
  {
    $project: {
      customer_id: 1,
      cohort_month: 1,
      month_index: {
        $add: [
          { $multiply: [{ $subtract: ["$order_year", "$cohort_year"] }, 12] },
          { $subtract: ["$order_mo", "$cohort_mo"] }
        ]
      }
    }
  },
  {
    $group: {
      _id: { cohort_month: "$cohort_month", month_index: "$month_index" },
      active_customers: { $addToSet: "$customer_id" }
    }
  },
  {
    $project: {
      cohort_month: "$_id.cohort_month",
      month_index: "$_id.month_index",
      customer_count: { $size: "$active_customers" }
    }
  },
  { $sort: { cohort_month: 1, month_index: 1 } }
]);
```

---

## 7. Machine Learning Methodology

### 7.1 Unsupervised RFM Persona Segmentation (`models/rfm_segmentation.py`)
To segment the customer base into actionable behavioral cohorts, two complementary techniques were deployed:

#### A. Quantile Scoring (1 to 4)
* **Recency Score ($R$):** Binned into quartiles inversely (lower recency days receive higher score: $4=\text{most recent}$).
* **Frequency Score ($F$):** Binned into quartiles ($4=\text{most frequent}$).
* **Monetary Score ($M$):** Binned into quartiles ($4=\text{highest lifetime spend}$).
* **Persona Mapping:**
  * **Champions:** $R \ge 3, F \ge 3, M \ge 3$ ($1,316$ customers / $30.3\%$)
  * **At Risk:** $R \le 2, (F \ge 2 \text{ or } M \ge 2)$ ($856$ customers / $19.7\%$)
  * **Potential Loyalists:** $R \ge 3, F \ge 2$ ($603$ customers / $13.9\%$)
  * **Loyal Customers:** $F \ge 3, M \ge 3$ ($451$ customers / $10.4\%$)
  * **Hibernating / Churned:** $R \le 2, F \le 2, M \le 2$ ($451$ customers / $10.4\%$)
  * **Need Attention:** $R = 2, F \ge 2$ ($405$ customers / $9.3\%$)
  * **New Customers:** $R \ge 3, F = 1$ ($256$ customers / $5.9\%$)

#### B. K-Means Clustering
Because monetary value and frequency exhibit strong positive skew (long-tail Pareto distributions), features undergo logarithmic transformation:
$$x_{\text{transformed}} = \ln(1 + x)$$
Features are then standardized using `StandardScaler` ($\mu=0, \sigma=1$). An optimal cluster size of $k=4$ was selected based on elbow analysis:
* **Silhouette Score:** **`0.337`**

| Cluster | Mean Recency (Days) | Mean Frequency (Orders) | Mean Monetary Value (£) | Behavioral Profile |
| :---: | :---: | :---: | :---: | :--- |
| **0** | $180.4$ | $1.3$ | £$341.30$ | Dormant / One-time buyers |
| **1** | $11.5$ | $13.8$ | £$8,133.60$ | High-value VIP Super-Users |
| **2** | $17.2$ | $2.2$ | £$560.20$ | Active Standard Shoppers |
| **3** | $70.9$ | $4.1$ | £$1,811.50$ | Mid-tier Maturing Accounts |

---

### 7.2 Predictive Churn Modeling (`models/churn_model.py`)
* **Objective:** Predict the likelihood that a customer will defect (exceed 90 days of inactivity).
* **Prevention of Target Leakage:** Critical methodological rigor was applied: **`recency_days` was strictly excluded from model features**, as it forms the definition of the target label.
* **Feature Vector:** `frequency`, `monetary`, `total_items`, `tenure_days`, `avg_order_value`, `avg_items_per_order`, and `country_clean`.
* **Model Selection:** **XGBoost Classifier** (`xgb.XGBClassifier`) with early stopping and negative-to-positive class weight rebalancing:
  $$\text{scale\_pos\_weight} = \frac{N_{\text{active}}}{N_{\text{churned}}} = \frac{2166}{1087} \approx 1.99$$

---

## 8. System Architecture & Data Flow

```
[Raw UCI Excel: 541k Rows]
         │
         ▼
[Python Cleaning & Document Modeling Engine (ingest_to_mongodb.py)]
         │
         ▼
[MongoDB Atlas Cloud Database (ecommerce_analytics.customers)]
   ├── $jsonSchema Enforcement (strict validation)
   └── B-Tree Indexes (customer_id, country, dates, orders)
         │
         ├───► [MongoDB Aggregation Pipelines (aggregations.py)]
         │        ├── RFM Feature Matrix ($project, $sum, $subtract)
         │        ├── Triangular Cohort Retention Matrix ($unwind, $group)
         │        └── Geographic Market Revenue ($group, $sort)
         │
         ├───► [Machine Learning Layer (models/)]
         │        ├── K-Means RFM Personas (k=4, Silhouette: 0.337)
         │        └── XGBoost Churn Classifier (ROC-AUC: 0.9558)
         │
         └───► [Interactive Presentation Tier (app/dashboard.py)]
                  ├── 1-Click Windows Batch Launcher (run_dashboard.bat)
                  └── Clean Light-Themed Web Analytics UI
```

---

## 9. Web Presentation Tier (Streamlit Dashboard)

The presentation layer is implemented in **Streamlit** ([`app/dashboard.py`](file:///d:/MongoDB/app/dashboard.py)) utilizing an enterprise-grade light theme ([`.streamlit/config.toml`](file:///d:/MongoDB/.streamlit/config.toml)):

1. **Tab 1: Overview & Market KPIs:** Displays high-level executive cards (Active Customers: `4,338`, Gross Revenue: `£8.91M`, Average CLV: `£2,054.27`, Churn Rate: `33.4%`), interactive country revenue charts, and diagnostic scorecards.
2. **Tab 2: Customer Segmentation & Personas:** Visualizes the 7-tier persona distribution via a donut chart and an interactive 2D log-scaled scatter plot of Recency vs Monetary spend, accompanied by a strategic marketing playbook table.
3. **Tab 3: Cohort Retention Analysis:** Renders a triangular heatmap of monthly cohort retention decay over a 12-month observation horizon.
4. **Tab 4: Customer 360 & Risk Scoring:** Allows arbitrary customer lookups via an instant point query, presenting total orders, lifetime spend, nested order tables, and an animated radial gauge displaying real-time predicted churn probability.

---

## 10. Experimental Results & Business Insights

### 10.1 Predictive Model Diagnostic Scorecard

The trained XGBoost model was evaluated against an out-of-time stratified holdout test set ($n=1,085$ customers):

| Metric | Score | Interpretation |
| :--- | :---: | :--- |
| **ROC-AUC** | **`0.9558`** | Exceptional discriminative power between active and churning customers. |
| **PR-AUC (Avg Precision)** | **`0.9292`** | High precision maintained across skewed class distributions. |
| **Accuracy** | **`87.00%`** | High overall classification accuracy across the customer base. |
| **F1-Score** | **`0.8190`** | Harmonious balance between precision ($76.5\%$) and recall ($88.1\%$). |

#### Confusion Matrix:
$$\begin{bmatrix} 
\text{True Negative (Active): } 625 & \text{False Positive: } 98 \\ 
\text{False Negative: } 43 & \text{True Positive (Churned): } 319 
\end{bmatrix}$$

### 10.2 Core Business Insights
1. **Pareto Revenue Concentration:** The top $10.4\%$ of customers (Cluster 1 VIPs, averaging $13.8$ orders and £$8,133.60$ spend) account for over $58\%$ of total e-commerce revenue.
2. **Geographic Concentration:** The United Kingdom represents $82.0\%$ of gross revenue (£$7.31M$), while European markets like the Netherlands (£$285k$), EIRE (£$265k$), and Germany (£$228k$) demonstrate higher average order value (AOV) per transaction.
3. **Re-engagement Window:** Cohort retention curves show the steepest drop occurring between Month 1 and Month 2 (retention drops from $100\%$ to $28\%$), indicating that automated onboarding drip sequences must trigger within the first 30 days post-acquisition.

---

## 11. Conclusion & Future Enhancements

### 11.1 Conclusion
This project successfully demonstrates the architectural and analytical superiority of **MongoDB** as a unified operational and analytical database for e-commerce intelligence:
* Multi-table relational joins were completely replaced by an embedded Customer 360 document model.
* Feature engineering latency was reduced by executing aggregation pipelines directly inside the MongoDB engine.
* Real-time machine learning predictions were seamlessly coupled with a light-themed interactive UI.

### 11.2 Future Enhancements
* **MongoDB Change Streams (`watch()`):** Automatically trigger real-time model retraining or customer notification webhooks whenever a new invoice document is appended.
* **Atlas Vector Search & RAG:** Embed product descriptions using Sentence-Transformers to offer semantic product recommendations within the Customer 360 profile view.
* **Continuous CLV Regression:** Implement a survival analysis or Gamma-Gamma regression model to forecast continuous future monetary value.

---

## 12. Appendix: Replication & CLI Execution Guide

### 12.1 Prerequisites
* MongoDB Atlas Cluster or Local MongoDB Community Server (`mongodb://localhost:27017/`)
* Python 3.10+

### 12.2 One-Click Windows Launch
Double-click [`run_dashboard.bat`](file:///d:/MongoDB/run_dashboard.bat) in Windows Explorer to automatically start the Streamlit dashboard at `http://localhost:8501`.

### 12.3 Command Line Execution
```powershell
# 1. Navigate to project root
cd d:\MongoDB

# 2. Activate Python Virtual Environment
.\.venv\Scripts\Activate.ps1

# 3. Run End-to-End Ingestion, Aggregations & ML Pipeline
python main.py

# 4. Start the Web Dashboard
streamlit run app/dashboard.py
```

### 12.4 Direct MongoDB Shell Execution
To inspect aggregation pipelines directly in `mongosh`:
```powershell
mongosh < queries/mongo_queries.js
```
