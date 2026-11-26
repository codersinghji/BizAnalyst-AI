
import pandas as pd

from analytics.schema_detector import detect_schema

def generate_summary(df):
    """Generate a basic summary of the uploaded dataset."""

    if df is None or df.empty:
        return {
            "total_rows": 0,
            "total_columns": 0,
            "duplicate_rows": 0,
            "memory_usage_mb": 0
        } 

    return {
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_mb": round(
            df.memory_usage(deep=True).sum() / (1024 * 1024), 2
        )
    }

def generate_data_profile(df):
    """Generate a detailed profile of the dataset."""

    if df is None or df.empty:
        return {
            "overview": generate_summary(df),
            "missing_report": pd.DataFrame(),
            "numeric_summary": pd.DataFrame(),
            "categorical_summary": pd.DataFrame(),
            "outlier_report": pd.DataFrame(),
            "schema": {}
        }

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    missing_report = pd.DataFrame({
        "Missing Values": df.isnull().sum(),
        "Missing Percentage": (
            df.isnull().mean() * 100
        ).round(2)
    })

    numeric_summary = (
        df[numeric_columns].describe().T
        if numeric_columns
        else pd.DataFrame()
    )

    categorical_summary = (
        df[categorical_columns].describe().T
        if categorical_columns
        else pd.DataFrame()
    )

    outlier_data = []

    for column in numeric_columns:
        series = df[column].dropna()

        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower_limit = q1 - 1.5 * iqr
        upper_limit = q3 + 1.5 * iqr

        outlier_count = int(
            ((series < lower_limit) | (series > upper_limit)).sum()
        )

        outlier_data.append({
            "Column": column,
            "Outlier Count": outlier_count,
            "Lower Limit": lower_limit,
            "Upper Limit": upper_limit
        })

    outlier_report = pd.DataFrame(outlier_data)

    try:
        schema = detect_schema(df)
    except Exception:
        schema = {}

    return {
        "overview": generate_summary(df),
        "missing_report": missing_report,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "outlier_report": outlier_report,
        "schema": schema
    }