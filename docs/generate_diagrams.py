import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def create_architecture_diagram(save_path: Path):
    fig, ax = plt.subplots(figsize=(15, 8), dpi=200)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 8)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")

    # Title
    ax.text(
        7.5, 7.5,
        "End-to-End System Architecture & Data Flow",
        ha="center", va="center",
        fontsize=18, fontweight="bold", color="#0f172a",
        family="sans-serif"
    )
    ax.text(
        7.5, 7.15,
        "From 541k+ Raw Transactions to MongoDB Customer 360 and Predictive ML",
        ha="center", va="center",
        fontsize=11, color="#64748b",
        family="sans-serif"
    )

    # Stages data
    stages = [
        {
            "col": 1.5,
            "title": "1. Data Acquisition",
            "subtitle": "Raw Transactions",
            "items": ["• UCI Online Retail", "• 541,909 Purchases", "• 37 Global Markets", "• data/raw/"],
            "color": "#eff6ff",
            "border": "#3b82f6",
            "tag": "EXCEL SOURCE",
            "tag_color": "#1d4ed8",
        },
        {
            "col": 4.5,
            "title": "2. ETL & Validation",
            "subtitle": "Document Modeling",
            "items": ["• Filter Cancellations", "• Group by Customer", "• Nest Orders & Items", "• $jsonSchema Check"],
            "color": "#f0fdf4",
            "border": "#22c55e",
            "tag": "PYTHON PIPELINE",
            "tag_color": "#15803d",
        },
        {
            "col": 7.5,
            "title": "3. MongoDB 360",
            "subtitle": "Core Database",
            "items": ["• db: ecommerce_analytics", "• coll: customers", "• 4,338 Documents", "• 5 B-Tree Indexes"],
            "color": "#f0fdfa",
            "border": "#14b8a6",
            "tag": "MONGODB ENGINE",
            "tag_color": "#0f766e",
        },
        {
            "col": 10.5,
            "title": "4. Aggregations",
            "subtitle": "In-Engine Pipelines",
            "items": ["• RFM Calculation", "• Cohort Matrix", "• Geographic Revenue", "• Zero Python Wrangles"],
            "color": "#fefce8",
            "border": "#eab308",
            "tag": "AGGREGATION",
            "tag_color": "#a16207",
        },
        {
            "col": 13.5,
            "title": "5. ML & UI Tier",
            "subtitle": "Analytics & Inference",
            "items": ["• XGBoost (AUC 0.956)", "• K-Means RFM Personas", "• Real-Time Churn Gauge", "• Streamlit Light UI"],
            "color": "#faf5ff",
            "border": "#a855f7",
            "tag": "PREDICTIVE UI",
            "tag_color": "#7e22ce",
        },
    ]

    # Draw Stage Cards
    for s in stages:
        x = s["col"] - 1.2
        y = 1.6
        w = 2.4
        h = 4.8

        # Main Box
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1,rounding_size=0.15",
            facecolor=s["color"],
            edgecolor=s["border"],
            linewidth=1.8,
            zorder=2
        )
        ax.add_patch(rect)

        # Tag Pill
        tag_rect = patches.FancyBboxPatch(
            (s["col"] - 0.9, y + h - 0.45), 1.8, 0.35,
            boxstyle="round,pad=0.05,rounding_size=0.1",
            facecolor="#ffffff",
            edgecolor=s["border"],
            linewidth=1.0,
            zorder=3
        )
        ax.add_patch(tag_rect)
        ax.text(
            s["col"], y + h - 0.28, s["tag"],
            ha="center", va="center", fontsize=8, fontweight="bold",
            color=s["tag_color"], zorder=4
        )

        # Card Title
        ax.text(
            s["col"], y + h - 0.85, s["title"],
            ha="center", va="center", fontsize=11, fontweight="bold",
            color="#0f172a", zorder=3
        )
        ax.text(
            s["col"], y + h - 1.15, s["subtitle"],
            ha="center", va="center", fontsize=9, color="#64748b", zorder=3
        )

        # Divider line inside card
        ax.plot([x + 0.2, x + w - 0.2], [y + h - 1.4, y + h - 1.4], color=s["border"], alpha=0.3, lw=1, zorder=3)

        # Card Items
        item_y = y + h - 1.8
        for it in s["items"]:
            ax.text(x + 0.25, item_y, it, ha="left", va="center", fontsize=9, color="#334155", zorder=3)
            item_y -= 0.65

    # Connective Flow Arrows
    arrow_props = dict(
        arrowstyle="-|>,head_width=0.4,head_length=0.6",
        color="#94a3b8",
        lw=2.5,
    )
    for i in range(len(stages) - 1):
        x1 = stages[i]["col"] + 1.25
        x2 = stages[i+1]["col"] - 1.25
        ax.annotate("", xy=(x2, 4.0), xytext=(x1, 4.0), arrowprops=arrow_props, zorder=5)

    # Bottom summary banner
    summary_rect = patches.FancyBboxPatch(
        (0.5, 0.4), 14.0, 0.7,
        boxstyle="round,pad=0.08,rounding_size=0.1",
        facecolor="#f8fafc",
        edgecolor="#cbd5e1",
        linewidth=1,
        zorder=2
    )
    ax.add_patch(summary_rect)
    ax.text(
        7.5, 0.75,
        "Core Advantage: Single-Document Atomicity • Zero Relational Joins • Server-Side Aggregation Optimization",
        ha="center", va="center", fontsize=9.5, fontweight="600", color="#475569", zorder=3
    )

    plt.tight_layout()
    plt.savefig(str(save_path), bbox_inches="tight", dpi=200)
    plt.close()
    print(f"Architecture diagram saved to {save_path}")


def create_schema_diagram(save_path: Path):
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=200)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")

    # Title
    ax.text(
        7.0, 8.0,
        "MongoDB Customer 360 Document Schema",
        ha="center", va="center",
        fontsize=18, fontweight="bold", color="#0f172a",
        family="sans-serif"
    )
    ax.text(
        7.0, 7.65,
        "Hierarchical Embedded Document Model (Collection: customers)",
        ha="center", va="center",
        fontsize=11, color="#64748b",
        family="sans-serif"
    )

    # 1. ROOT DOCUMENT: CUSTOMERS
    c_x, c_y, c_w, c_h = 0.8, 1.8, 3.8, 5.0
    r_cust = patches.FancyBboxPatch((c_x, c_y), c_w, c_h, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor="#ffffff", edgecolor="#0284c7", linewidth=2, zorder=2)
    ax.add_patch(r_cust)

    # Header bar
    h_cust = patches.FancyBboxPatch((c_x, c_y + c_h - 0.7), c_w, 0.7, boxstyle="round,pad=0.05,rounding_size=0.1", facecolor="#0284c7", edgecolor="none", zorder=3)
    ax.add_patch(h_cust)
    ax.text(c_x + c_w/2, c_y + c_h - 0.35, "ROOT: CUSTOMER DOCUMENT", ha="center", va="center", fontsize=10, fontweight="bold", color="#ffffff", zorder=4)

    cust_fields = [
        ("_id", "ObjectId", "PK (Internal Identifier)"),
        ("customer_id", "string", "UK (Unique B-Tree Index)"),
        ("country", "string", "Geographic Market Index"),
        ("first_purchase_date", "date", "Acquisition Timestamp"),
        ("last_purchase_date", "date", "Recency Boundary Index"),
        ("total_orders_count", "int", "Order Velocity Index"),
        ("orders", "Array<Order>", "Embedded Array (1:N)"),
    ]
    cy = c_y + c_h - 1.15
    for f_name, f_type, f_desc in cust_fields:
        ax.text(c_x + 0.2, cy, f_name, fontsize=9.5, fontweight="bold", color="#0f172a", zorder=3)
        ax.text(c_x + 2.0, cy, f_type, fontsize=8.5, color="#0284c7", zorder=3)
        ax.text(c_x + 0.2, cy - 0.25, f_desc, fontsize=7.5, color="#64748b", zorder=3)
        cy -= 0.58

    # 2. EMBEDDED ARRAY: ORDERS
    o_x, o_y, o_w, o_h = 5.2, 2.5, 3.8, 4.3
    r_order = patches.FancyBboxPatch((o_x, o_y), o_w, o_h, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor="#ffffff", edgecolor="#059669", linewidth=2, zorder=2)
    ax.add_patch(r_order)

    h_order = patches.FancyBboxPatch((o_x, o_y + o_h - 0.7), o_w, 0.7, boxstyle="round,pad=0.05,rounding_size=0.1", facecolor="#059669", edgecolor="none", zorder=3)
    ax.add_patch(h_order)
    ax.text(o_x + o_w/2, o_y + o_h - 0.35, "EMBEDDED: ORDER OBJECT", ha="center", va="center", fontsize=10, fontweight="bold", color="#ffffff", zorder=4)

    order_fields = [
        ("invoice_no", "string", "Transaction Reference"),
        ("invoice_date", "date", "Order Placement Date"),
        ("order_total", "double", "Sum of Line Items (£)"),
        ("items_count", "int", "Distinct Items in Basket"),
        ("items", "Array<Item>", "Embedded Line Items (1:N)"),
    ]
    oy = o_y + o_h - 1.15
    for f_name, f_type, f_desc in order_fields:
        ax.text(o_x + 0.2, oy, f_name, fontsize=9.5, fontweight="bold", color="#0f172a", zorder=3)
        ax.text(o_x + 2.0, oy, f_type, fontsize=8.5, color="#059669", zorder=3)
        ax.text(o_x + 0.2, oy - 0.25, f_desc, fontsize=7.5, color="#64748b", zorder=3)
        oy -= 0.65

    # 3. EMBEDDED ARRAY: ITEMS
    i_x, i_y, i_w, i_h = 9.6, 2.3, 3.8, 4.5
    r_item = patches.FancyBboxPatch((i_x, i_y), i_w, i_h, boxstyle="round,pad=0.1,rounding_size=0.15", facecolor="#ffffff", edgecolor="#7c3aed", linewidth=2, zorder=2)
    ax.add_patch(r_item)

    h_item = patches.FancyBboxPatch((i_x, i_y + i_h - 0.7), i_w, 0.7, boxstyle="round,pad=0.05,rounding_size=0.1", facecolor="#7c3aed", edgecolor="none", zorder=3)
    ax.add_patch(h_item)
    ax.text(i_x + i_w/2, i_y + i_h - 0.35, "EMBEDDED: PURCHASED ITEM", ha="center", va="center", fontsize=10, fontweight="bold", color="#ffffff", zorder=4)

    item_fields = [
        ("stock_code", "string", "Product Catalog SKU"),
        ("description", "string", "Product Title / Name"),
        ("quantity", "int", "Units Ordered"),
        ("unit_price", "double", "Unit Price (£)"),
        ("line_total", "double", "quantity * unit_price (£)"),
    ]
    iy = i_y + i_h - 1.15
    for f_name, f_type, f_desc in item_fields:
        ax.text(i_x + 0.2, iy, f_name, fontsize=9.5, fontweight="bold", color="#0f172a", zorder=3)
        ax.text(i_x + 2.0, iy, f_type, fontsize=8.5, color="#7c3aed", zorder=3)
        ax.text(i_x + 0.2, iy - 0.25, f_desc, fontsize=7.5, color="#64748b", zorder=3)
        iy -= 0.65

    # Relationship Arrows
    arrow_props_embed = dict(
        arrowstyle="-|>,head_width=0.35,head_length=0.55",
        color="#64748b",
        lw=2.0,
    )
    ax.annotate("", xy=(o_x - 0.05, 4.6), xytext=(c_x + c_w + 0.05, 4.6), arrowprops=arrow_props_embed, zorder=5)
    ax.text((c_x + c_w + o_x) / 2, 4.85, "embeds [ ]", ha="center", va="center", fontsize=8.5, fontweight="600", color="#0284c7", zorder=6)

    ax.annotate("", xy=(i_x - 0.05, 4.6), xytext=(o_x + o_w + 0.05, 4.6), arrowprops=arrow_props_embed, zorder=5)
    ax.text((o_x + o_w + i_x) / 2, 4.85, "embeds [ ]", ha="center", va="center", fontsize=8.5, fontweight="600", color="#059669", zorder=6)

    # Bottom Callout: Indexing and Validation Summary
    callout = patches.FancyBboxPatch(
        (0.8, 0.4), 12.6, 0.9,
        boxstyle="round,pad=0.08,rounding_size=0.1",
        facecolor="#f8fafc",
        edgecolor="#cbd5e1",
        linewidth=1,
        zorder=2
    )
    ax.add_patch(callout)
    ax.text(
        7.1, 0.95,
        "Database Engine Features Active:",
        ha="center", va="center", fontsize=10, fontweight="bold", color="#0f172a", zorder=3
    )
    ax.text(
        7.1, 0.62,
        "• $jsonSchema Validator: Strict type enforcement on required fields  |  • B-Tree Indexes: customer_id (Unique), country, dates  |  • Atomic Document Updates",
        ha="center", va="center", fontsize=8.5, color="#475569", zorder=3
    )

    plt.tight_layout()
    plt.savefig(str(save_path), bbox_inches="tight", dpi=200)
    plt.close()
    print(f"Schema diagram saved to {save_path}")


if __name__ == "__main__":
    create_architecture_diagram(DOCS_DIR / "architecture_flow.png")
    create_schema_diagram(DOCS_DIR / "database_schema.png")
