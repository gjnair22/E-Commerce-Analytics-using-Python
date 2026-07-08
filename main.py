"""
E-Commerce Customer & Sales Analytics
--------------------------------------
Exploratory data analysis of the Olist Brazilian E-Commerce dataset.

Sections:
    1. Import Libraries
    2. Load Dataset & Config
    3. Data Understanding
    4. Data Cleaning
    5. Feature Engineering
    6. Data Analysis (master table)
    7. Customer Analysis
    8. Product Analysis
    9. Sales Analysis
    10. Payment Analysis
    11. Delivery Analysis
    12. Business Insights
    13. Conclusion
"""

# =============================================================================
# 1. IMPORT LIBRARIES
# =============================================================================
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any

pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)

# Configure modern, premium plotting styles
def setup_plot_style():
    sns.set_theme(style='white', rc={
        'axes.facecolor': '#fafafa',
        'figure.facecolor': '#ffffff',
        'grid.color': '#eaeaea',
        'grid.linestyle': '--',
        'axes.grid': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.spines.left': True,
        'axes.spines.bottom': True,
        'xtick.color': '#333333',
        'ytick.color': '#333333',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'sans-serif'],
    })
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['savefig.dpi'] = 200

setup_plot_style()


# =============================================================================
# 2. LOAD DATASET
# =============================================================================
# File mapping to local names in dataset folder
FILES = {
    'customers': 'olist_customers_dataset.csv',
    'orders': 'olist_orders_dataset.csv',
    'payments': 'olist_order_payments_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'reviews': 'olist_order_reviews_dataset.csv',
    'category_translation': 'product_category_name_translation.csv',
}

def locate_data_dir() -> Path:
    """Locate dataset folder, looking locally or at the OneDrive default path."""
    local_path = Path('data')
    if local_path.exists() and any(local_path.glob('*.csv')):
        return local_path
        
    onedrive_path = Path(r'C:\Users\Gowri J Nair\OneDrive\Desktop\GitPro\SQL\E-commerce customer and Sales Analytics\Dataset')
    if onedrive_path.exists():
        return onedrive_path
        
    raise FileNotFoundError(
        f"Could not locate dataset folder. Checked:\n"
        f"  - {local_path.resolve()}\n"
        f"  - {onedrive_path.resolve()}\n"
        f"Please check your directories and try again."
    )

def load_data(data_dir: Path, files: dict) -> dict:
    """Load every CSV listed in `files` into a dict of dataframes."""
    data = {}
    print(f"Dataset source directory: {data_dir.resolve()}\n")
    for name, filename in files.items():
        file_path = data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")
        print(f"Loading {name:<20} from {filename}...")
        data[name] = pd.read_csv(file_path)
    print(f"\nSuccessfully loaded {len(data)} datasets.")
    return data


# =============================================================================
# 3. DATA UNDERSTANDING
# =============================================================================
def inspect_dataset(df: pd.DataFrame, name: str) -> None:
    """Print a standardized profile of a dataframe: preview, structure,
    summary statistics, shape, columns, and missing values.
    """
    print(f"\n{'=' * 80}")
    print(f"{name.upper()} DATASET PROFILE")
    print(f"{'=' * 80}")

    print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")

    print("\nColumns:")
    print(list(df.columns))

    print("\nPreview (First 3 rows):")
    print(df.head(3))

    print("\nMissing values:")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    print(missing if not missing.empty else "No missing values.")

    print("\nSummary statistics (numeric columns):")
    print(df.describe())


def inspect_all(data: dict) -> None:
    """Run inspect_dataset() over every dataframe in `data`."""
    for name, df in data.items():
        inspect_dataset(df, name)


# =============================================================================
# 4. DATA CLEANING
# =============================================================================
def clean_data(data: dict) -> dict:
    """Apply cleaning steps: datetime conversion, category translation,
    duplicate removal, and missing-value handling."""
    data = data.copy()
    orders = data['orders'].copy()
    products = data['products'].copy()
    category_translation = data['category_translation'].copy()
    reviews = data['reviews'].copy()

    # --- Datetime conversions ---
    order_date_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in order_date_cols:
        orders[col] = pd.to_datetime(orders[col], errors='coerce')

    reviews['review_creation_date'] = pd.to_datetime(reviews['review_creation_date'], errors='coerce')
    reviews['review_answer_timestamp'] = pd.to_datetime(reviews['review_answer_timestamp'], errors='coerce')

    # --- Category name translation ---
    products = products.merge(category_translation, on='product_category_name', how='left')
    products['product_category_name_english'] = (
        products['product_category_name_english'].fillna('unknown')
    )

    # --- Drop duplicates ---
    print("\n--- Removing Duplicates ---")
    for name in ['customers', 'orders', 'payments', 'products', 'order_items', 'reviews']:
        before = len(data[name])
        data[name] = data[name].drop_duplicates()
        after = len(data[name])
        if before != after:
            print(f"{name}: removed {before - after} duplicate rows")

    # --- Fill non-critical missing text fields ---
    reviews['review_comment_title'] = reviews['review_comment_title'].fillna('No Title')
    reviews['review_comment_message'] = reviews['review_comment_message'].fillna('No Comment')

    # --- Drop rows with missing product physical attributes (small % of data) ---
    products = products.dropna(subset=['product_weight_g', 'product_length_cm',
                                        'product_height_cm', 'product_width_cm'])

    data['orders'] = orders
    data['products'] = products
    data['reviews'] = reviews

    print("Data cleaning complete.")
    return data


# =============================================================================
# 5. FEATURE ENGINEERING
# =============================================================================
def engineer_features(data: dict) -> dict:
    """Add derived columns used by the downstream analysis:
    delivery time, delivery delay, on-time flag, order month/year,
    and per-item order value."""
    data = data.copy()
    orders = data['orders'].copy()
    order_items = data['order_items'].copy()

    orders['delivery_time_days'] = (
        orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']
    ).dt.days

    orders['delivery_delay_days'] = (
        orders['order_delivered_customer_date'] - orders['order_estimated_delivery_date']
    ).dt.days

    # Explicit handling for undelivered order delay (stays NaN, not True/False)
    orders['on_time_delivery'] = np.where(
        orders['delivery_delay_days'].isna(),
        np.nan,
        orders['delivery_delay_days'] <= 0
    )

    orders['order_month'] = orders['order_purchase_timestamp'].dt.to_period('M').astype(str)
    orders['order_year'] = orders['order_purchase_timestamp'].dt.year

    order_items['item_total_value'] = order_items['price'] + order_items['freight_value']

    data['orders'] = orders
    data['order_items'] = order_items

    print("Feature engineering complete.")
    return data


# =============================================================================
# 6. DATA ANALYSIS (MASTER TABLE)
# =============================================================================
def build_master_table(data: dict) -> pd.DataFrame:
    """Merge cleaned tables into one denormalized dataframe.
    Note: To prevent duplication of order lines, payments are analyzed
    separately, and reviews are averaged at the order level.
    """
    # Average review score per order to avoid duplicating items if order has multiple reviews
    reviews_agg = data['reviews'].groupby('order_id', as_index=False)['review_score'].mean()

    master = (
        data['order_items']
        .merge(data['orders'], on='order_id', how='left')
        .merge(data['customers'], on='customer_id', how='left')
        .merge(data['products'], on='product_id', how='left')
        .merge(reviews_agg, on='order_id', how='left')
    )
    print(f"Master table build complete. Shape: {master.shape[0]} rows, {master.shape[1]} columns")
    return master


# =============================================================================
# 7. CUSTOMER ANALYSIS
# =============================================================================
def customer_analysis(customers: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    # Distinct count of customers per state (correcting for transaction level duplicates)
    top_states = (
        customers.groupby('customer_state')['customer_unique_id']
        .nunique()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10, 5))
    colors = sns.color_palette("ch:start=.2,rot=-.3", 10)[::-1]  # Premium custom palette
    ax = sns.barplot(x=top_states.values, y=top_states.index, hue=top_states.index, legend=False, palette=colors)
    
    # Add values on top of bars
    for i, v in enumerate(top_states.values):
        ax.text(v + (v * 0.01), i, f"{v:,}", va='center', fontweight='bold', color='#444444')

    plt.title('Top 10 Brazilian States by Number of Customers', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Number of Unique Customers', fontsize=11, labelpad=10)
    plt.ylabel('State', fontsize=11)
    plt.tight_layout()
    
    output_path = output_dir / 'output_top_states.png'
    plt.savefig(output_path)
    plt.close()
    print(f"Saved customer state chart to {output_path}")

    # Repeat purchase rate
    repeat_customers = customers['customer_unique_id'].value_counts()
    repeat_rate = (repeat_customers > 1).mean() * 100
    
    return {
        'total_customers': int(customers['customer_unique_id'].nunique()),
        'repeat_rate': repeat_rate,
        'top_state': top_states.index[0],
        'top_state_count': int(top_states.values[0])
    }


# =============================================================================
# 8. PRODUCT ANALYSIS
# =============================================================================
def product_analysis(master: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    top_categories = (
        master.groupby('product_category_name_english')['item_total_value']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10, 5))
    colors = sns.color_palette("viridis", 10)[::-1]  # Premium viridis theme
    ax = sns.barplot(x=top_categories.values / 1e6, y=top_categories.index, hue=top_categories.index, legend=False, palette=colors)
    
    # Add values on top of bars
    for i, v in enumerate(top_categories.values):
        ax.text(v/1e6 + 0.05, i, f"R$ {v/1e6:.2f}M", va='center', fontweight='bold', color='#444444')

    plt.title('Top 10 Product Categories by Revenue (BRL)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Revenue (Millions BRL)', fontsize=11, labelpad=10)
    plt.ylabel('Category', fontsize=11)
    plt.tight_layout()
    
    output_path = output_dir / 'output_top_categories.png'
    plt.savefig(output_path)
    plt.close()
    print(f"Saved product category chart to {output_path}")

    avg_price_by_category = (
        master.groupby('product_category_name_english')['price']
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )
    
    return {
        'top_category': top_categories.index[0],
        'top_category_revenue': float(top_categories.values[0]),
        'highest_avg_price_category': avg_price_by_category.index[0],
        'highest_avg_price': float(avg_price_by_category.values[0])
    }


# =============================================================================
# 9. SALES ANALYSIS
# =============================================================================
def sales_analysis(master: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    # Group by month and calculate revenue
    monthly_sales = master.groupby('order_month')['item_total_value'].sum().sort_index()

    # Filter out partial edge-months (e.g. 2016-09 and 2018-09/10 if data is highly incomplete)
    # Most records are from 2017-01 to 2018-08
    full_months_sales = monthly_sales.loc['2017-01':'2018-08']

    plt.figure(figsize=(11, 5))
    plt.plot(full_months_sales.index, full_months_sales.values / 1000, marker='o', 
             linewidth=2.5, color='#e65c00', markerfacecolor='#333333', markersize=6)
    
    plt.title('Monthly Revenue Trend (Jan 2017 - Aug 2018)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Month', fontsize=11, labelpad=10)
    plt.ylabel('Revenue (Thousands BRL)', fontsize=11, labelpad=10)
    plt.xticks(rotation=45)
    
    # Format Y axis to comma-separated thousands
    ax = plt.gca()
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{int(x):,}k"))
    
    plt.tight_layout()
    output_path = output_dir / 'output_monthly_revenue.png'
    plt.savefig(output_path)
    plt.close()
    print(f"Saved monthly revenue trend line chart to {output_path}")

    total_revenue = float(master['item_total_value'].sum())
    total_orders = int(master['order_id'].nunique())

    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': total_revenue / total_orders
    }


# =============================================================================
# 10. PAYMENT ANALYSIS
# =============================================================================
def payment_analysis(payments: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    payment_type_dist = payments['payment_type'].value_counts()

    plt.figure(figsize=(10, 5))
    colors = ['#5b2c6f', '#1a5276', '#117a65', '#9a7d0a', '#a04000']
    ax = sns.barplot(x=payment_type_dist.index, y=payment_type_dist.values, hue=payment_type_dist.index, legend=False, palette=colors[:len(payment_type_dist)])
    
    # Add values on top of bars
    for i, v in enumerate(payment_type_dist.values):
        ax.text(i, v + (v * 0.01), f"{v:,}", ha='center', fontweight='bold', color='#444444')

    plt.title('Payment Type Distribution', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Payment Method', fontsize=11, labelpad=10)
    plt.ylabel('Number of Transactions', fontsize=11)
    plt.tight_layout()
    
    output_path = output_dir / 'output_payment_types.png'
    plt.savefig(output_path)
    plt.close()
    print(f"Saved payment type chart to {output_path}")

    avg_installments = payments.groupby('payment_type')['payment_installments'].mean()
    avg_payment_value = float(payments['payment_value'].mean())
    credit_card_share = (payments[payments['payment_type'] == 'credit_card'].shape[0] / len(payments)) * 100

    return {
        'credit_card_share': credit_card_share,
        'avg_payment_value': avg_payment_value,
        'avg_cc_installments': float(avg_installments.get('credit_card', 0.0))
    }


# =============================================================================
# 11. DELIVERY ANALYSIS
# =============================================================================
def delivery_analysis(orders: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    # Focus only on completed/delivered orders to get true delivery metrics
    delivered = orders.dropna(subset=['order_delivered_customer_date', 'delivery_time_days']).copy()
    
    avg_delivery_time = float(delivered['delivery_time_days'].mean())
    
    # Calculate late delivery rate specifically on delivered orders
    late_delivery_rate = float((delivered['on_time_delivery'] == False).mean() * 100)

    plt.figure(figsize=(10, 5))
    # Restrict to orders under 60 days to see detail (cutting long tail outliers)
    sns.histplot(delivered[delivered['delivery_time_days'] <= 60]['delivery_time_days'], 
                 bins=30, kde=True, color='#880e4f', edgecolor='white')
    
    plt.axvline(avg_delivery_time, color='black', linestyle='--', linewidth=1.5, 
                label=f'Avg Delivery: {avg_delivery_time:.1f} days')
    
    plt.title('Distribution of Delivery Times (<= 60 Days)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Delivery Time (days)', fontsize=11, labelpad=10)
    plt.ylabel('Number of Orders', fontsize=11)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    
    output_path = output_dir / 'output_delivery_times.png'
    plt.savefig(output_path)
    plt.close()
    print(f"Saved delivery time distribution chart to {output_path}")

    return {
        'avg_delivery_time': avg_delivery_time,
        'late_delivery_rate': late_delivery_rate
    }


# =============================================================================
# 12. BUSINESS INSIGHTS
# =============================================================================
def print_business_insights(metrics: dict) -> None:
    """
    Summarize actual, calculated findings from the Olist dataset.
    """
    insights = [
        f"Customer Concentration: Customers are heavily clustered in {metrics['top_state']} "
        f"which accounts for {metrics['top_state_count']:,} of unique customers. Focus regional marketing "
        f"and setup hubs in SP to reduce logistics costs.",
        
        f"Product Mix: '{metrics['top_category']}' is the highest revenue category generating "
        f"R$ {metrics['top_category_revenue']/1e6:.2f}M. The highest average unit price is in "
        f"'{metrics['highest_avg_price_category']}' (R$ {metrics['highest_avg_price']:.2f}).",
        
        f"Repeat Purchases: The customer repeat rate is {metrics['repeat_rate']:.2f}%. Olist is mostly a "
        f"single-purchase platform; implementing retention marketing and loyalty programs could drive "
        f"substantial LTV gains.",
        
        f"Payments: Credit card represents the primary transaction channel, accounting for {metrics['credit_card_share']:.1f}% "
        f"of payment counts. Purchases on credit card are paid in {metrics['avg_cc_installments']:.1f} installments on average.",
        
        f"Delivery Performance: The average delivery time is {metrics['avg_delivery_time']:.1f} days. "
        f"The late-delivery rate is {metrics['late_delivery_rate']:.2f}%. Logistics speed and delivery reliability "
        f"should be audited as they are critical drivers of customer reviews.",
    ]
    
    print("\n" + "=" * 100)
    print("DYNAMICAL BUSINESS INSIGHTS")
    print("=" * 100)
    for point in insights:
        print(f"- {point}")


# =============================================================================
# 13. CONCLUSION
# =============================================================================
def print_conclusion(metrics: dict) -> None:
    print("\n" + "=" * 100)
    print("CONCLUSION & KEY METRICS")
    print("=" * 100)
    print(
        f"This E-commerce Analytics pipeline processed {metrics['total_orders']:,} orders "
        f"representing R$ {metrics['total_revenue']/1e6:.2f}M in total transaction volume across "
        f"{metrics['total_customers']:,} unique customers.\n\n"
        "Summary of Key Findings:\n"
        f"  - Average Order Value (AOV): {metrics['avg_order_value']:.2f} BRL\n"
        f"  - Customer Loyalty (Repeat Rate): {metrics['repeat_rate']:.2f}%\n"
        f"  - Logistics Speed (Avg delivery): {metrics['avg_delivery_time']:.1f} days\n"
        f"  - Late Delivery Incident Rate: {metrics['late_delivery_rate']:.2f}%\n\n"
        "Recommendations:\n"
        "  1. Launch email-campaigns/personalized-recommendations for high-value categories.\n"
        "  2. Address delivery delay rates, specifically targeting regions outside Southeast Brazil.\n"
        "  3. Introduce multi-item bundles to push up the average AOV from the current baseline."
    )


import json

def export_dashboard_json(metrics: dict, data: dict, master: pd.DataFrame, output_dir: Path) -> None:
    """Export computed analytics metrics and binned data to JSON for the web dashboard."""
    # 1. State customer distribution (top 10)
    state_counts = (
        data['customers'].groupby('customer_state')['customer_unique_id']
        .nunique()
        .sort_values(ascending=False)
        .head(10)
    )
    states_chart = {
        "labels": list(state_counts.index),
        "values": [int(x) for x in state_counts.values]
    }

    # 2. Top categories by revenue (top 10)
    top_categories = (
        master.groupby('product_category_name_english')['item_total_value']
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    categories_chart = {
        "labels": list(top_categories.index),
        "values": [float(x) for x in top_categories.values]
    }

    # 3. Monthly revenue trend
    monthly_sales = master.groupby('order_month')['item_total_value'].sum().sort_index()
    full_months = monthly_sales.loc['2017-01':'2018-08']
    sales_chart = {
        "labels": list(full_months.index),
        "values": [float(x) for x in full_months.values]
    }

    # 4. Payment types
    pay_dist = data['payments']['payment_type'].value_counts()
    payment_chart = {
        "labels": list(pay_dist.index),
        "values": [int(x) for x in pay_dist.values]
    }

    # 5. Delivery times binned histogram (0 to 40 days, bin size 2)
    delivered = data['orders'].dropna(subset=['order_delivered_customer_date', 'delivery_time_days']).copy()
    delivery_times = delivered['delivery_time_days']
    delivery_times_filtered = delivery_times[(delivery_times >= 0) & (delivery_times <= 40)]
    bins = list(range(0, 42, 2))
    counts, bin_edges = np.histogram(delivery_times_filtered, bins=bins)
    bin_labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]
    delivery_chart = {
        "labels": bin_labels,
        "values": [int(x) for x in counts]
    }

    export_data = {
        "kpis": metrics,
        "charts": {
            "states": states_chart,
            "categories": categories_chart,
            "monthly_revenue": sales_chart,
            "payment_types": payment_chart,
            "delivery_times": delivery_chart
        }
    }

    json_path = output_dir.parent / 'dashboard_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=4, ensure_ascii=False)
    print(f"Exported dashboard JSON data to: {json_path.resolve()}")


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    print("==========================================================")
    print("STARTING OLIST E-COMMERCE CUSTOMER & SALES ANALYTICS PIPELINE")
    print("==========================================================\n")
    
    # Establish project directories
    project_root = Path(__file__).resolve().parent
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)
    
    # Locate data source
    try:
        data_dir = locate_data_dir()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    # Pipeline stages
    data = load_data(data_dir, FILES)
    
    # Run structural profiling for dataset files
    print("\n--- Running Dataset Inspections ---")
    inspect_all(data)

    print("\n--- Cleaning Data ---")
    data = clean_data(data)
    
    print("\n--- Feature Engineering ---")
    data = engineer_features(data)

    print("\n--- Building Denormalized Master Table ---")
    master = build_master_table(data)

    print("\n--- Executing Component Analyses & Generating Visuals ---")
    metrics = {}
    
    cust_metrics = customer_analysis(data['customers'], output_dir)
    prod_metrics = product_analysis(master, output_dir)
    sales_metrics = sales_analysis(master, output_dir)
    pay_metrics = payment_analysis(data['payments'], output_dir)
    del_metrics = delivery_analysis(data['orders'], output_dir)
    
    # Merge metrics from components
    metrics.update(cust_metrics)
    metrics.update(prod_metrics)
    metrics.update(sales_metrics)
    metrics.update(pay_metrics)
    metrics.update(del_metrics)

    # Export dashboard JSON data for the web interface
    export_dashboard_json(metrics, data, master, output_dir)

    # Print results
    print_business_insights(metrics)
    print_conclusion(metrics)
    print("\nAnalytics run successfully. All output charts saved to: ", output_dir.resolve())


if __name__ == '__main__':
    main()
