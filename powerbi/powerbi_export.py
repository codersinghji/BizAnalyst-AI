
"""Power BI export utilities for BizAnalyst-AI."""

from io import BytesIO
import json

import numpy as np
import pandas as pd

def prepare_powerbi_data(df):
    """Prepare a safe copy of a DataFrame for Power BI export."""

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Please provide a valid pandas DataFrame.")

    if df.empty:
        raise ValueError("The dataset is empty.")

    export_df = df.copy()

    # Make column names strings and ensure they are unique.
    new_columns = []
    used_names = set()

    for index, column in enumerate(export_df.columns):
        name = str(column).strip() or f"Column_{index + 1}"
        candidate = name
        suffix = 1

        while candidate in used_names:
            candidate = f"{name}_{suffix}"
            suffix += 1

        used_names.add(candidate)
        new_columns.append(candidate)

    export_df.columns = new_columns

    # Convert complex values into JSON strings.
    for column in export_df.columns:
        if export_df[column].dtype == "object":
            export_df[column] = export_df[column].apply(
                lambda value: json.dumps(value, default=str)
                if isinstance(value, (dict, list, tuple, set))
                else value
            )

    # Replace infinite values with missing values.
    export_df = export_df.replace([np.inf, -np.inf], np.nan)

    # Remove timezone information for Excel compatibility.
    for column in export_df.columns:
        if isinstance(export_df[column].dtype, pd.DatetimeTZDtype):
            export_df[column] = export_df[column].dt.tz_localize(None)

    return export_df

def export_powerbi_csv(df):
    """Return UTF-8 CSV bytes."""

    export_df = prepare_powerbi_data(df)

    return export_df.to_csv(
        index=False
    ).encode("utf-8-sig")

def export_powerbi_excel(df):
    """Return an Excel workbook with data and export information."""

    export_df = prepare_powerbi_data(df)
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(
            writer,
            sheet_name="PowerBI_Data",
            index=False
        )

        metadata = pd.DataFrame({
            "Property": [
                "Application",
                "Export Purpose",
                "Total Rows",
                "Total Columns",
                "Missing Values",
                "Duplicate Rows"
            ],
            "Value": [
                "BizAnalyst-AI",
                "Power BI Import",
                len(export_df),
                len(export_df.columns),
                int(export_df.isna().sum().sum()),
                int(export_df.duplicated().sum())
            ]
        })

        metadata.to_excel(
            writer,
            sheet_name="Export_Info",
            index=False
        )

    output.seek(0)
    return output.getvalue()

def get_powerbi_export_info(df):
    """Return dataset details before exporting."""

    export_df = prepare_powerbi_data(df)

    return {
        "total_rows": int(export_df.shape[0]),
        "total_columns": int(export_df.shape[1]),
        "columns": export_df.columns.tolist(),
        "missing_values": int(export_df.isna().sum().sum()),
        "duplicate_rows": int(export_df.duplicated().sum()),
        "memory_usage_mb": round(
            export_df.memory_usage(deep=True).sum() / (1024 * 1024),
            2
        )
    }