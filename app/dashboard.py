import sys
from pathlib import Path

# Add project root to sys.path so 'config', 'database', 'models' can be imported anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import joblib
import xgboost as xgb

from config.settings import (
    METRICS_PATH,
    CHURN_MODEL_PATH,
    PREPROCESSOR_PATH,
    KMEANS_MODEL_PATH,
)
from database.mongo_client import get_customers_collection
from database.aggregations import (
    load_rfm_dataframe,
    get_cohort_retention_data,
    get_country_level_summary,
)
from models.rfm_segmentation import compute_rfm_segmentation

st.set_page_config(
    page_title="E-Commerce Analytics & Customer 360",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Clean, modern, light SaaS CSS theme (Stripe / Linear / Notion inspired)
LIGHT_THEME_CSS = """
<style>
/* Base typography and background */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
}

/* Hide default streamlit top header line & footer */
header[data-testid="stHeader"] {
    background: #ffffff;
    border-bottom: 1px solid #f1f5f9;
}

footer {
    display: none;
}

/* Clean White Card Containers */
.clean-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
    margin-bottom: 1rem;
}

.clean-card-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.25rem;
}

.clean-card-subtitle {
    font-size: 0.85rem;
    color: #64748b;
    margin-bottom: 1rem;
}

/* Metric styling */
[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}

[data-testid="stMetricLabel"] {
    color: #64748b;
    font-size: 0.82rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

[data-testid="stMetricValue"] {
    color: #0f172a;
    font-size: 1.75rem;
    font-weight: 700;
}

/* Tab Bar Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 2px;
}

.stTabs [data-baseweb="tab"] {
    padding: 10px 18px;
    font-weight: 500;
    font-size: 14px;
    color: #64748b;
    background-color: transparent;
    border-radius: 6px;
    border: none;
    transition: all 0.15s ease-in-out;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #1e293b;
    background-color: #f8fafc;
}

.stTabs [aria-selected="true"] {
    color: #2563eb !important;
    background-color: #eff6ff !important;
    font-weight: 600 !important;
}

/* Light Pills / Badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
}
.badge-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.badge-green { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.badge-amber { background: #fefce8; color: #a16207; border: 1px solid #fef08a; }
.badge-red { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.badge-slate { background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }

/* Custom clean table */
.clean-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
.clean-table th {
    background-color: #f8fafc;
    color: #475569;
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
    border-bottom: 1px solid #e2e8f0;
}
.clean-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
}
</style>
"""

st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=120)
def fetch_rfm_and_segments():
    df = load_rfm_dataframe()
    if df.empty:
        return df, None
    df, summary = compute_rfm_segmentation(df)
    return df, summary


@st.cache_data(ttl=120)
def fetch_cohort_matrix():
    return get_cohort_retention_data()


@st.cache_data(ttl=120)
def fetch_country_summary():
    return get_country_level_summary()


@st.cache_resource
def load_churn_model():
    if not CHURN_MODEL_PATH.exists() or not PREPROCESSOR_PATH.exists():
        return None, None, None
    model = xgb.XGBClassifier()
    model.load_model(str(CHURN_MODEL_PATH))
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
    return model, preprocessor, metrics


df_rfm, cluster_summary = fetch_rfm_and_segments()
model, preprocessor, metrics = load_churn_model()

if df_rfm.empty:
    st.warning("No customer records found in MongoDB. Please run `main.py` first to ingest the dataset.")
    st.stop()

# Header
st.markdown("""
<div style="margin-bottom: 1.5rem; margin-top: 0.5rem;">
    <h1 style="font-size: 1.85rem; font-weight: 700; color: #0f172a; margin-bottom: 0.25rem;">
        E-Commerce Customer Analytics
    </h1>
    <p style="color: #64748b; font-size: 0.95rem; margin: 0;">
        Customer 360 profiles, RFM segmentation, and predictive churn intelligence powered by MongoDB & Machine Learning
    </p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview & Market KPIs",
    "Customer Segmentation",
    "Cohort Retention",
    "Customer 360 & Risk Scoring",
])

# ----------------- TAB 1: EXECUTIVE OVERVIEW -----------------
with tab1:
    total_customers = len(df_rfm)
    total_revenue = df_rfm["monetary"].sum()
    churn_rate = (df_rfm["is_churned"].sum() / total_customers) * 100
    avg_clv = df_rfm["monetary"].mean()

    # 4 Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Customers", f"{total_customers:,}")
    m2.metric("Total Revenue", f"£{total_revenue:,.2f}")
    m3.metric("Average Customer Value", f"£{avg_clv:,.2f}")
    m4.metric("90-Day Churn Rate", f"{churn_rate:.1f}%")

    st.write("")

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown("""
        <div class="clean-card">
            <div class="clean-card-header">Top Geographic Markets by Revenue</div>
            <div class="clean-card-subtitle">Aggregated via MongoDB $group pipeline across customer order history</div>
        """, unsafe_allow_html=True)

        country_data = fetch_country_summary()
        if country_data:
            df_country = pd.DataFrame(country_data).head(8)
            fig_country = px.bar(
                df_country,
                x="country",
                y="total_revenue",
                labels={"total_revenue": "Revenue (£)", "country": "Country"},
                color_discrete_sequence=["#3b82f6"],
                template="plotly_white",
            )
            fig_country.update_layout(
                margin=dict(l=20, r=20, t=10, b=20),
                height=320,
                xaxis=dict(tickangle=-15, title=None),
                yaxis=dict(gridcolor="#f1f5f9"),
                paper_bgcolor="white",
                plot_bgcolor="white",
            )
            st.plotly_chart(fig_country, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="clean-card">
            <div class="clean-card-header">Predictive Model Diagnostics</div>
            <div class="clean-card-subtitle">XGBoost Churn Classifier calibrated on behavioral signals</div>
        """, unsafe_allow_html=True)

        if metrics:
            st.markdown(f"""
            <table class="clean-table" style="margin-top: 0.5rem;">
                <tr>
                    <td><b>Algorithm</b></td>
                    <td>XGBoost Classifier</td>
                </tr>
                <tr>
                    <td><b>ROC-AUC Score</b></td>
                    <td><span class="badge badge-green">{metrics['roc_auc']:.4f}</span></td>
                </tr>
                <tr>
                    <td><b>PR-AUC (Precision)</b></td>
                    <td><span class="badge badge-blue">{metrics['pr_auc']:.4f}</span></td>
                </tr>
                <tr>
                    <td><b>F1-Score</b></td>
                    <td><span class="badge badge-blue">{metrics['f1_score']:.4f}</span></td>
                </tr>
                <tr>
                    <td><b>Overall Accuracy</b></td>
                    <td><span class="badge badge-green">{metrics['accuracy']:.1%}</span></td>
                </tr>
                <tr>
                    <td><b>Test Observations</b></td>
                    <td>{metrics['n_test']:,} customers</td>
                </tr>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.info("Model metrics pending training.")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------- TAB 2: RFM SEGMENTATION -----------------
with tab2:
    st.markdown("""
    <div class="clean-card">
        <div class="clean-card-header">Customer RFM Persona Distribution</div>
        <div class="clean-card-subtitle">Segmented by Recency, Frequency, and Monetary metrics computed in MongoDB</div>
    """, unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        persona_counts = df_rfm["Customer_Persona"].value_counts().reset_index()
        persona_counts.columns = ["Persona", "Count"]

        # Clean corporate light color palette
        palette = ["#2563eb", "#059669", "#0891b2", "#6366f1", "#d97706", "#dc2626", "#64748b"]

        fig_pie = px.pie(
            persona_counts,
            names="Persona",
            values="Count",
            hole=0.5,
            color_discrete_sequence=palette,
            template="plotly_white",
        )
        fig_pie.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=340,
            showlegend=True,
            legend=dict(orientation="h", y=-0.1),
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_p2:
        fig_scatter = px.scatter(
            df_rfm,
            x="recency_days",
            y="monetary",
            size="frequency",
            color="Customer_Persona",
            hover_data=["customer_id", "frequency", "avg_order_value"],
            log_y=True,
            labels={"recency_days": "Days Since Last Purchase", "monetary": "Lifetime Value (£)"},
            color_discrete_sequence=palette,
            template="plotly_white",
        )
        fig_scatter.update_layout(
            margin=dict(t=10, b=20, l=20, r=20),
            height=340,
            xaxis=dict(gridcolor="#f1f5f9"),
            yaxis=dict(gridcolor="#f1f5f9"),
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Strategy Playbook
    st.markdown("""
    <div class="clean-card">
        <div class="clean-card-header">Actionable Customer Playbook</div>
        <div class="clean-card-subtitle">Targeted engagement strategies for each behavioral cluster</div>
        <table class="clean-table" style="margin-top: 0.5rem;">
            <thead>
                <tr>
                    <th style="width: 20%;">Persona</th>
                    <th style="width: 35%;">Behavior</th>
                    <th style="width: 45%;">Recommended Strategy</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="badge badge-green">Champions</span></td>
                    <td>High frequency, high monetary value, recent purchases</td>
                    <td>VIP loyalty programs, early access to new items, referral incentives</td>
                </tr>
                <tr>
                    <td><span class="badge badge-blue">Loyal Customers</span></td>
                    <td>Steady repeat buyers with solid lifetime value</td>
                    <td>Upsell premium categories, loyalty points, personalized discounts</td>
                </tr>
                <tr>
                    <td><span class="badge badge-blue">Potential Loyalists</span></td>
                    <td>Recent shoppers with above-average spend</td>
                    <td>Product recommendations based on previous orders, membership invites</td>
                </tr>
                <tr>
                    <td><span class="badge badge-amber">Need Attention</span></td>
                    <td>Moderate spenders whose recency is starting to drop</td>
                    <td>Re-engagement emails, limited-time discount vouchers</td>
                </tr>
                <tr>
                    <td><span class="badge badge-red">At Risk</span></td>
                    <td>Past high-value customers who have not ordered in &gt;60 days</td>
                    <td>Win-back campaigns, feedback surveys, special reactivation offers</td>
                </tr>
                <tr>
                    <td><span class="badge badge-slate">Hibernating</span></td>
                    <td>Infrequent buyers with high days since last order</td>
                    <td>Low-cost email newsletters or suppress to save marketing spend</td>
                </tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TAB 3: COHORT RETENTION -----------------
with tab3:
    st.markdown("""
    <div class="clean-card">
        <div class="clean-card-header">Monthly Customer Retention Heatmap</div>
        <div class="clean-card-subtitle">
            Calculated in MongoDB by grouping orders across customer cohort acquisition months
        </div>
    """, unsafe_allow_html=True)

    cohort_matrix = fetch_cohort_matrix()
    if not cohort_matrix.empty:
        # Soft blue-teal gradient (light, readable, enterprise clean)
        fig_cohort = px.imshow(
            cohort_matrix,
            labels=dict(x="Months Since First Order", y="Acquisition Cohort", color="Retention (%)"),
            x=cohort_matrix.columns,
            y=cohort_matrix.index,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale="Blues",
            template="plotly_white",
        )
        fig_cohort.update_layout(
            margin=dict(t=10, b=20, l=20, r=20),
            height=420,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        st.plotly_chart(fig_cohort, use_container_width=True)
    else:
        st.info("Cohort retention matrix is calculating...")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- TAB 4: CUSTOMER 360 & CHURN -----------------
with tab4:
    st.markdown("""
    <div class="clean-card">
        <div class="clean-card-header">Customer 360° Profile & Churn Evaluation</div>
        <div class="clean-card-subtitle">Inspect individual customer nested records from MongoDB and evaluate real-time churn risk</div>
    """, unsafe_allow_html=True)

    coll = get_customers_collection()
    cust_ids = df_rfm["customer_id"].tolist()
    search_cust = st.selectbox("Select or Search Customer ID:", cust_ids, index=0)

    if search_cust:
        cust_doc = coll.find_one({"customer_id": search_cust}, {"_id": 0})
        cust_row = df_rfm[df_rfm["customer_id"] == search_cust].iloc[0]

        # ML Prediction
        if model and preprocessor:
            top_countries = metrics.get("top_countries", [])
            country_clean = cust_row["country"] if cust_row["country"] in top_countries else "Other"

            input_dict = {
                "frequency": cust_row["frequency"],
                "monetary": cust_row["monetary"],
                "total_items": cust_row["total_items"],
                "tenure_days": cust_row["tenure_days"],
                "avg_order_value": cust_row["avg_order_value"],
                "avg_items_per_order": cust_row["avg_items_per_order"],
                "country_clean": country_clean,
            }
            df_in = pd.DataFrame([input_dict])
            X_in = preprocessor.transform(df_in)
            churn_prob = float(model.predict_proba(X_in)[0, 1])
        else:
            churn_prob = 0.5

        # Clean Customer KPI Grid
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Country", cust_doc.get("country", "Unknown"))
        k2.metric("Orders Placed", f"{cust_doc.get('total_orders_count', 0):,}")
        k3.metric("Lifetime Spend", f"£{cust_row['monetary']:,.2f}")
        k4.metric("Assigned Persona", cust_row["Customer_Persona"])

        st.write("")

        g_col, d_col = st.columns([1, 2])
        with g_col:
            # Clean, minimalist gauge (soft light theme)
            gauge_bar_color = "#dc2626" if churn_prob >= 0.60 else ("#d97706" if churn_prob >= 0.40 else "#16a34a")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=churn_prob * 100,
                title={'text': "Predicted Churn Probability (%)", 'font': {'size': 13, 'color': '#64748b'}},
                number={'suffix': "%", 'font': {'size': 28, 'color': '#0f172a'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': "#cbd5e1", 'tickwidth': 1},
                    'bar': {'color': gauge_bar_color, 'thickness': 0.6},
                    'bgcolor': "#f8fafc",
                    'borderwidth': 1,
                    'bordercolor': "#e2e8f0",
                    'steps': [
                        {'range': [0, 40], 'color': "#f0fdf4"},
                        {'range': [40, 70], 'color': "#fefce8"},
                        {'range': [70, 100], 'color': "#fef2f2"},
                    ],
                }
            ))
            fig_gauge.update_layout(
                height=220,
                margin=dict(l=20, r=20, t=30, b=10),
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with d_col:
            status_badge = (
                '<span class="badge badge-red">High Churn Risk</span>'
                if churn_prob >= 0.60
                else ('<span class="badge badge-amber">Moderate Risk</span>' if churn_prob >= 0.40 else '<span class="badge badge-green">Active & Healthy</span>')
            )
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:1rem 1.25rem; height:200px; display:flex; flex-direction:column; justify-content:center;">
                <div style="margin-bottom:0.5rem; display:flex; align-items:center; gap:0.5rem;">
                    <span style="font-weight:600; color:#0f172a;">Customer Engagement Status:</span>
                    {status_badge}
                </div>
                <div style="font-size:0.875rem; color:#475569; line-height:1.7;">
                    • <b>Days Since Last Purchase:</b> {cust_row['recency_days']:.0f} days<br>
                    • <b>Customer Relationship Age:</b> {cust_row['tenure_days']:.0f} days<br>
                    • <b>Average Order Basket (AOV):</b> £{cust_row['avg_order_value']:.2f}<br>
                    • <b>Average Items per Basket:</b> {cust_row['avg_items_per_order']:.1f} SKUs
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Order history table
        st.markdown("""
        <div class="clean-card">
            <div class="clean-card-header">Order History (MongoDB Nested Array)</div>
            <div class="clean-card-subtitle">Invoices and purchases recorded for this customer</div>
        """, unsafe_allow_html=True)

        orders_list = cust_doc.get("orders", [])
        if orders_list:
            orders_summary = []
            for o in orders_list:
                orders_summary.append({
                    "Invoice No": o.get("invoice_no"),
                    "Invoice Date": str(o.get("invoice_date")),
                    "Order Total (£)": f"£{o.get('order_total', 0):,.2f}",
                    "Unique Items": o.get("items_count", 0),
                })
            st.dataframe(pd.DataFrame(orders_summary), use_container_width=True)
        else:
            st.write("No order records found.")
        st.markdown("</div>", unsafe_allow_html=True)
