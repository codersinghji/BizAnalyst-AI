
import pandas as pd
import numpy as np

from analytics.schema_detector import detect_schema

def calculate_statistics(df):
    """Calculate descriptive statistics for numeric measures."""

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Please provide a valid DataFrame.")

    if df.empty:
        raise ValueError("Dataset is empty.")

    # Detect identifier columns
    schema = detect_schema(df)

    identifier_columns = schema["detected_roles"].get(
        "identifier", []
    )

    # Select numeric columns, excluding identifiers
    numeric_columns = [
        column
        for column in df.select_dtypes(include=np.number).columns
        if column not in identifier_columns
    ]

    if not numeric_columns:
        return {
            "summary": pd.DataFrame(),
            "correlation": pd.DataFrame(),
            "message": "No numeric measure columns found."
        }

    numeric_df = df[numeric_columns]

    summary = []

    for column in numeric_columns:

        series = numeric_df[column].dropna()

        if series.empty:
            continue

        modes = series.mode()

        summary.append({
            "Column": column,
            "Count": int(series.count()),
            "Missing": int(df[column].isna().sum()),
            "Mean": float(series.mean()),
            "Median": float(series.median()),
            "Mode": (
                float(modes.iloc[0])
                if not modes.empty else None
            ),
            "Standard Deviation": float(series.std()),
            "Variance": float(series.var()),
            "Minimum": float(series.min()),
            "Maximum": float(series.max()),
            "25th Percentile": float(series.quantile(0.25)),
            "50th Percentile": float(series.quantile(0.50)),
            "75th Percentile": float(series.quantile(0.75)),
            "90th Percentile": float(series.quantile(0.90)),
            "95th Percentile": float(series.quantile(0.95)),
            "Skewness": float(series.skew()),
            "Kurtosis": float(series.kurt())
        })

    summary_df = pd.DataFrame(summary)

    # Correlation matrix
    correlation = numeric_df.corr().round(3)

    return {
        "summary": summary_df,
        "correlation": correlation,
        "message": "Statistical analysis completed successfully."
    }

def calculate_column_statistics(df, column):
    """Calculate statistics for one selected numeric column."""

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError("Selected column must be numeric.")

    series = df[column].dropna()

    if series.empty:
        raise ValueError("Selected column has no valid values.")

    return {
        "column": column,
        "count": int(series.count()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "standard_deviation": float(series.std()),
        "variance": float(series.var()),
        "minimum": float(series.min()),
        "maximum": float(series.max()),
        "percentiles": {
            str(p): float(series.quantile(p / 100))
            for p in [25, 50, 75, 90, 95]
        }
    }