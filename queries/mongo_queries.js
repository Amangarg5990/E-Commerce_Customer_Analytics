/**
 * MongoDB Aggregation & Query Portfolio
 * Database: ecommerce_analytics
 * Collection: customers
 * 
 * You can execute these queries in `mongosh` or copy pipeline stages into MongoDB Compass.
 */

// Switch to the project database
use ecommerce_analytics;

// ==============================================================================
// 1. VERIFY SCHEMA VALIDATION & INDEXES
// ==============================================================================

// Inspect the active $jsonSchema validation rules applied to the collection
db.getCollectionInfos({ name: "customers" })[0].options.validator;

// List all performance indexes created on the collection
db.customers.getIndexes();


// ==============================================================================
// 2. QUERY: CUSTOMER 360 SINGLE LOOKUP
// ==============================================================================

// Retrieve a full Customer 360 profile with nested order history
db.customers.findOne(
  { customer_id: "17850" },
  { _id: 0, customer_id: 1, country: 1, total_orders_count: 1, first_purchase_date: 1, last_purchase_date: 1, "orders.invoice_no": 1, "orders.order_total": 1 }
);


// ==============================================================================
// 3. AGGREGATION PIPELINE: IN-DATABASE RFM & CHURN FEATURE EXTRACTION
// ==============================================================================

// Uses $project, date arithmetic ($subtract), $sum, and $cond to compute
// Recency (days), Frequency, Monetary (CLV), AOV, and 90-day Churn Label in-engine.
db.customers.aggregate([
  {
    $project: {
      customer_id: 1,
      country: 1,
      first_purchase_date: 1,
      last_purchase_date: 1,
      frequency: { $size: { $ifNull: ["$orders", []] } },
      monetary: {
        $round: [{ $sum: "$orders.order_total" }, 2]
      },
      total_items: { $sum: "$orders.items_count" },
      recency_days: {
        $round: [
          {
            $divide: [
              { $subtract: [ISODate("2011-12-10T00:00:00Z"), "$last_purchase_date"] },
              1000 * 60 * 60 * 24
            ]
          },
          1
        ]
      },
      tenure_days: {
        $round: [
          {
            $divide: [
              { $subtract: [ISODate("2011-12-10T00:00:00Z"), "$first_purchase_date"] },
              1000 * 60 * 60 * 24
            ]
          },
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
      total_items: 1,
      tenure_days: 1,
      avg_order_value: {
        $round: [
          {
            $cond: [
              { $gt: ["$frequency", 0] },
              { $divide: ["$monetary", "$frequency"] },
              0
            ]
          },
          2
        ]
      },
      is_churned: {
        $cond: [{ $gte: ["$recency_days", 90] }, 1, 0]
      }
    }
  },
  { $sort: { monetary: -1 } },
  { $limit: 10 }
]);


// ==============================================================================
// 4. AGGREGATION PIPELINE: MONTHLY TRIANGULAR COHORT RETENTION
// ==============================================================================

// Unwinds the nested orders array, calculates monthly index relative to
// customer acquisition month, and groups by month index to track retention decay.
db.customers.aggregate([
  { $unwind: "$orders" },
  {
    $project: {
      customer_id: 1,
      cohort_month: {
        $dateToString: { format: "%Y-%m", date: "$first_purchase_date" }
      },
      order_month: {
        $dateToString: { format: "%Y-%m", date: "$orders.invoice_date" }
      },
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
      order_month: 1,
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
      _id: {
        cohort_month: "$cohort_month",
        month_index: "$month_index"
      },
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


// ==============================================================================
// 5. AGGREGATION PIPELINE: GEOGRAPHIC MARKET REVENUE & CHURN DENSITY
// ==============================================================================

// Computes gross merchandise value (GMV), customer counts, and territorial churn
// rates grouped by country.
db.customers.aggregate([
  {
    $project: {
      country: 1,
      total_orders: "$total_orders_count",
      monetary: { $sum: "$orders.order_total" },
      recency_days: {
        $divide: [
          { $subtract: [ISODate("2011-12-10T00:00:00Z"), "$last_purchase_date"] },
          1000 * 60 * 60 * 24
        ]
      }
    }
  },
  {
    $group: {
      _id: "$country",
      total_customers: { $sum: 1 },
      total_revenue: { $sum: "$monetary" },
      avg_orders_per_customer: { $avg: "$total_orders" },
      churned_customers: {
        $sum: { $cond: [{ $gte: ["$recency_days", 90] }, 1, 0] }
      }
    }
  },
  {
    $project: {
      country: "$_id",
      total_customers: 1,
      total_revenue: { $round: ["$total_revenue", 2] },
      avg_orders_per_customer: { $round: ["$avg_orders_per_customer", 1] },
      churn_rate_pct: {
        $round: [
          { $multiply: [{ $divide: ["$churned_customers", "$total_customers"] }, 100] },
          1
        ]
      }
    }
  },
  { $sort: { total_revenue: -1 } }
]);


// ==============================================================================
// 6. QUERY EXECUTION EXPLAIN PLAN (INDEX VERIFICATION)
// ==============================================================================

// Verifies that index customer_id_1 is used for O(1) B-tree point lookups
db.customers.find({ customer_id: "17850" }).explain("executionStats");

