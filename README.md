# E-Commerce Customer & Sales Analytics
This project implements a complete, robust exploratory data analysis (EDA) pipeline for the **Olist Brazilian E-Commerce dataset**. It reads the datasets, handles data cleaning and feature engineering, builds an optimized denormalized master table, generates key sales and customer charts, and extracts data-driven business insights.

## Project Structure
```
ecommerce_analytics/
├── main.py       # Core analytics pipeline
├── README.md     # Project documentation
└── output/       # Generated charts and visualizations (created automatically)
    ├── output_top_states.png
    ├── output_top_categories.png
    ├── output_monthly_revenue.png
    ├── output_payment_types.png
    └── output_delivery_times.png
```

## Setup & Running the Script
Ensure you have the required packages installed in your Python environment:
```bash
pip install pandas numpy matplotlib seaborn
```

To run the analytics pipeline:
```bash
python main.py
```

The script will automatically search for the dataset CSV files in:
1. A local `data/` subdirectory.
2. The default OneDrive dataset path: `C:\Users\Gowri J Nair\OneDrive\Desktop\GitPro\SQL\E-commerce customer and Sales Analytics\Dataset`.

## Bug Fixes & Improvements

1. **Dataset Loader**: Fixed the runtime `TypeError` caused by reading DataFrames directly inside the file mapping dictionary definition before passing them to the path merger. The loader now correctly maps dataset names to filenames and loads them dynamically.
2. **Revenue Inflation Fix**: Excluded the `payments` table from the item-level denormalized master table. An order can have multiple payment methods, causing a cartesian product that duplicates items and inflates revenue calculations when summing. Additionally, aggregated the `reviews` table by `order_id` (using the mean score) to prevent similar duplication issues.
3. **Customer Count Metric**: Fixed the customer state bar chart which counted transactions (`customer_id`) rather than actual unique customers (`customer_unique_id`) per state.
4. **Delivery Analysis Correction**: Fixed the calculation of the late delivery rate to filter out `NaN` values (orders that were cancelled or are still shipping) which were previously incorrectly flagged as "late".
5. **Modern Plot Aesthetics**: Upgraded visualizations with customized, high-contrast, professional color palettes, value labels, and despine layouts.
6. **Dynamic Insights**: Replaced static placeholders with live figures calculated from the actual dataset (such as repeat rate, top revenue categories, late delivery rates, and average delivery time).
