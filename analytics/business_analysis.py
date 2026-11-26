
import pandas as pd

def monthly_sales_analysis(df):

    data = df.copy()

    data["order_date"] = pd.to_datetime(
        data["order_date"],
        errors="coerce"
    )

    data = data.dropna(subset=["order_date"])

    monthly = (
        data.groupby(
            data["order_date"].dt.to_period("M")
        )
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique")
        )
        .reset_index()
    )

    monthly["order_date"] = (
        monthly["order_date"].astype(str)
    )

    monthly["revenue_growth"] = (
        monthly["revenue"].pct_change() * 100
    ).round(2)

    return monthly

def regional_analysis(df):

    return (
        df.groupby("region")
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique")
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )

def category_analysis(df):

    return (
        df.groupby("category")
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            quantity=("quantity", "sum")
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )

def top_products_analysis(df, limit=10):

    return (
        df.groupby("product_name")
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            quantity=("quantity", "sum")
        )
        .reset_index()
        .sort_values("profit", ascending=False)
        .head(limit)
    )

def discount_analysis(df):

    return (
        df.groupby("discount")
        .agg(
            average_profit=("profit", "mean"),
            total_revenue=("sales", "sum"),
            total_profit=("profit", "sum")
        )
        .reset_index()
        .sort_values("discount")
    )