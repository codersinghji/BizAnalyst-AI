
import pandas as pd

SUPPORTED_AGGREGATIONS = [
    "sum",
    "mean",
    "median",
    "count",
    "min",
    "max",
    "std",
    "var",
    "nunique"
]

def aggregate_data(
    df,
    group_columns,
    value_columns,
    aggregation="sum"
):
    """
    Perform universal group-by aggregation.

    Example:
        Group by Department
        Calculate average Salary
    """

    if df is None or df.empty:
        raise ValueError("Dataset is empty.")

    if not group_columns:
        raise ValueError("Select at least one grouping column.")

    if not value_columns:
        raise ValueError("Select at least one value column.")

    if aggregation not in SUPPORTED_AGGREGATIONS:
        raise ValueError(
            f"Unsupported aggregation. Choose from {SUPPORTED_AGGREGATIONS}"
        )

    for column in group_columns + value_columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

    # Prevent accidental aggregation of grouping columns
    if set(group_columns) & set(value_columns):
        raise ValueError(
            "Grouping columns and value columns must be different."
        )

    selected = df[group_columns + value_columns].copy()

    if aggregation in [
        "sum", "mean", "median", "std", "var"
    ]:
        non_numeric = [
            column for column in value_columns
            if not pd.api.types.is_numeric_dtype(selected[column])
        ]

        if non_numeric:
            raise ValueError(
                f"These columns must be numeric: {non_numeric}"
            )

    result = selected.groupby(
        group_columns,
        dropna=False,
        observed=True
    )[value_columns].agg(aggregation)

    return result.reset_index()

def aggregate_multiple(
    df,
    group_columns,
    value_columns,
    aggregations=None
):
    """
    Apply multiple aggregation functions at once.

    Example:
        Salary -> mean, min, max
        Bonus -> sum, mean
    """

    if df is None or df.empty:
        raise ValueError("Dataset is empty.")

    if not group_columns or not value_columns:
        raise ValueError("Select grouping and value columns.")

    aggregations = aggregations or ["sum", "mean", "count"]

    invalid = [
        agg for agg in aggregations
        if agg not in SUPPORTED_AGGREGATIONS
    ]

    if invalid:
        raise ValueError(f"Invalid aggregation functions: {invalid}")

    for column in group_columns + value_columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

    if set(group_columns) & set(value_columns):
        raise ValueError(
            "Grouping columns and value columns must be different."
        )

    selected = df[group_columns + value_columns].copy()

    # Validate numeric requirements
    numeric_aggregations = {
        "sum", "mean", "median", "std", "var"
    }

    if numeric_aggregations.intersection(aggregations):
        non_numeric = [
            column for column in value_columns
            if not pd.api.types.is_numeric_dtype(selected[column])
        ]

        if non_numeric:
            raise ValueError(
                f"Numeric columns required for these operations: {non_numeric}"
            )

    result = selected.groupby(
        group_columns,
        dropna=False,
        observed=True
    )[value_columns].agg(aggregations)

    return result.reset_index()

def calculate_total(df, column, operation="sum"):
    """Calculate an overall statistic for one column."""

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    if operation not in SUPPORTED_AGGREGATIONS:
        raise ValueError("Unsupported aggregation.")

    series = df[column]

    if operation in [
        "sum", "mean", "median", "std", "var"
    ]:
        if not pd.api.types.is_numeric_dtype(series):
            raise ValueError("This operation requires numeric data.")

    if operation == "sum":
        return series.sum()

    if operation == "mean":
        return series.mean()

    if operation == "median":
        return series.median()

    if operation == "count":
        return series.count()

    if operation == "min":
        return series.min()

    if operation == "max":
        return series.max()

    if operation == "std":
        return series.std()

    if operation == "var":
        return series.var()

    if operation == "nunique":
        return series.nunique()