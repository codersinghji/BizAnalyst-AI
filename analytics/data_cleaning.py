
import pandas as pd
import numpy as np

from analytics.schema_detector import detect_schema

def inspect_data(df):
    """Inspect dataset quality without modifying the original."""

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Please provide a valid DataFrame.")

    if df.empty:
        raise ValueError("Dataset is empty.")

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicates": int(df.duplicated().sum()),
        "missing_values": {
            str(column): int(count)
            for column, count in df.isna().sum().items()
        },
        "data_types": {
            str(column): str(dtype)
            for column, dtype in df.dtypes.items()
        }
    }

def detect_outliers(df):
    """Detect numeric outliers using the IQR method."""

    numeric_columns = df.select_dtypes(include=np.number).columns
    report = []

    schema = detect_schema(df)
    identifier_columns = schema["detected_roles"].get(
        "identifier", []
    )

    for column in numeric_columns:

        if column in identifier_columns:
            continue

        series = df[column].dropna()

        if len(series) < 4:
            count = 0
            lower = None
            upper = None
        else:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            lower = float(q1 - 1.5 * iqr)
            upper = float(q3 + 1.5 * iqr)

            count = int(
                ((series < lower) | (series > upper)).sum()
            )

        report.append({
            "column": column,
            "outlier_count": count,
            "lower_limit": lower,
            "upper_limit": upper
        })

    return report

def clean_data(
    df,
    numeric_strategy="median",
    categorical_strategy="mode",
    remove_duplicates=False,
    date_columns=None
):
    """
    Clean a copy of the original DataFrame.

    Numeric strategies:
        median, mean, zero, none

    Categorical strategies:
        mode, unknown, none

    Duplicates are removed only when explicitly requested.
    Date conversion is applied only to selected columns.
    Outliers are detected but never automatically deleted.
    """

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Please provide a valid DataFrame.")

    if df.empty:
        raise ValueError("Dataset is empty.")

    valid_numeric = ["median", "mean", "zero", "none"]
    valid_categorical = ["mode", "unknown", "none"]

    if numeric_strategy not in valid_numeric:
        raise ValueError(
            f"Invalid numeric strategy. Choose from {valid_numeric}"
        )

    if categorical_strategy not in valid_categorical:
        raise ValueError(
            f"Invalid categorical strategy. Choose from {valid_categorical}"
        )

    # Preserve the source dataset
    cleaned_df = df.copy(deep=True)

    before = inspect_data(cleaned_df)

    schema = detect_schema(cleaned_df)

    identifier_columns = schema["detected_roles"].get(
        "identifier", []
    )

    numeric_columns = cleaned_df.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = cleaned_df.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    cleaning_actions = []

    # 1. Fill numeric missing values.
    # Identifier columns are deliberately excluded.
    for column in numeric_columns:

        if column in identifier_columns:
            continue

        if cleaned_df[column].isna().sum() == 0:
            continue

        if numeric_strategy == "median":
            fill_value = cleaned_df[column].median()

        elif numeric_strategy == "mean":
            fill_value = cleaned_df[column].mean()

        elif numeric_strategy == "zero":
            fill_value = 0

        else:
            continue

        # All-null columns cannot be filled using mean or median.
        if pd.isna(fill_value):
            continue

        missing_count = int(cleaned_df[column].isna().sum())

        cleaned_df[column] = cleaned_df[column].fillna(fill_value)

        cleaning_actions.append({
            "column": column,
            "action": f"Filled {missing_count} missing values",
            "strategy": numeric_strategy,
            "fill_value": float(fill_value)
        })

    # 2. Fill categorical missing values.
    for column in categorical_columns:

        if cleaned_df[column].isna().sum() == 0:
            continue

        if categorical_strategy == "mode":

            modes = cleaned_df[column].mode(dropna=True)

            if modes.empty:
                continue

            fill_value = modes.iloc[0]

        elif categorical_strategy == "unknown":
            fill_value = "Unknown"

        else:
            continue

        missing_count = int(cleaned_df[column].isna().sum())

        cleaned_df[column] = cleaned_df[column].fillna(fill_value)

        cleaning_actions.append({
            "column": column,
            "action": f"Filled {missing_count} missing values",
            "strategy": categorical_strategy,
            "fill_value": str(fill_value)
        })

    # 3. Convert only user-selected date columns.
    date_columns = date_columns or []

    for column in date_columns:

        if column not in cleaned_df.columns:
            raise ValueError(
                f"Date column '{column}' does not exist."
            )

        converted = pd.to_datetime(
            cleaned_df[column],
            errors="coerce"
        )

        cleaned_df[column] = converted

        cleaning_actions.append({
            "column": column,
            "action": "Converted column to datetime",
            "strategy": "to_datetime"
        })

    # 4. Remove duplicates only with user approval.
    removed_duplicates = 0

    if remove_duplicates:
        before_count = len(cleaned_df)

        cleaned_df = cleaned_df.drop_duplicates().copy()

        removed_duplicates = before_count - len(cleaned_df)

        cleaning_actions.append({
            "column": "All columns",
            "action": f"Removed {removed_duplicates} duplicate rows",
            "strategy": "drop_duplicates"
        })

    # 5. Detect outliers without deleting them.
    outlier_report = detect_outliers(cleaned_df)

    after = inspect_data(cleaned_df)

    report = {
        "before": before,
        "after": after,
        "cleaning_actions": cleaning_actions,
        "removed_duplicates": removed_duplicates,
        "remaining_missing_values": int(
            cleaned_df.isna().sum().sum()
        ),
        "outliers": outlier_report,
        "original_preserved": True
    }

    return cleaned_df, report