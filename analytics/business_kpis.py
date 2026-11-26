
def calculate_business_kpis(df):

    required_columns = [
        "sales", "profit", "order_id",
        "customer_id", "quantity"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Required columns missing: {missing}"
        )

    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    total_orders = df["order_id"].nunique()
    total_customers = df["customer_id"].nunique()
    total_quantity = df["quantity"].sum()

    profit_margin = (
        (total_profit / total_sales) * 100
        if total_sales else 0
    )

    average_order_value = (
        total_sales / total_orders
        if total_orders else 0
    )

    return {
        "Total Revenue": round(total_sales, 2),
        "Total Profit": round(total_profit, 2),
        "Total Orders": int(total_orders),
        "Total Customers": int(total_customers),
        "Units Sold": int(total_quantity),
        "Profit Margin (%)": round(profit_margin, 2),
        "Average Order Value": round(
            average_order_value, 2
        )
    }