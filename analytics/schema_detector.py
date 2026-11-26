
import pandas as pd
import numpy as np

# Possible column-name patterns
IDENTIFIER_WORDS = [
    "id", "code", "number", "no", "zip", "postal",
    "phone", "account", "invoice", "customer_id",
    "product_id", "employee_id"
]

DATE_WORDS = [
    "date", "time", "timestamp", "created_at",
    "updated_at", "dob", "birth"
]

MEASURE_WORDS = [
    "sales", "revenue", "profit", "price", "amount",
    "salary", "income", "cost", "expense", "quantity",
    "total", "score", "value", "balance", "age",
    "weight", "temperature", "pressure"
]

CATEGORY_WORDS = [
    "category", "type", "region", "city", "country",
    "department", "status", "gender", "segment",
    "class", "group"
]

def normalize_column_name(column):
    """Convert a column name into a standard format."""
    return str(column).strip().lower().replace(" ", "_").replace("-", "_")


def detect_column_role(column, series):
    """Detect a column's likely business role."""

    name = normalize_column_name(column)
    non_null = series.dropna()

    unique_count = non_null.nunique()
    total_count = len(non_null)

    if total_count == 0:
        return "empty"

    # Date detection
    if any(word in name for word in DATE_WORDS):
        return "date"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    # Identifier detection
    if (
        name in IDENTIFIER_WORDS
        or name.endswith("_id")
        or name.endswith("_code")
        or name.endswith("_number")
    ):
        return "identifier"

    # Boolean detection
    if pd.api.types.is_bool_dtype(series):
        return "category"

    # Numeric detection
    if pd.api.types.is_numeric_dtype(series):

        if any(word in name for word in MEASURE_WORDS):
            return "measure"

        if unique_count <= 10:
            return "category"

        return "measure"

    # Text, string and categorical detection
    if (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series.dtype)
        or isinstance(series.dtype, pd.CategoricalDtype)
    ):

        if any(word in name for word in CATEGORY_WORDS):
            return "category"

        if unique_count <= 30:
            return "category" if unique_count < total_count else "text"

        return "text"

    return "other"

def detect_schema(df):
    """
    Analyze any uploaded DataFrame and identify:
    - Data types
    - Likely business roles
    - Missing values
    - Unique values
    - Suggested analysis columns
    """

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Please provide a valid pandas DataFrame.")

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    column_details = []

    for column in df.columns:
        series = df[column]

        role = detect_column_role(column, series)

        sample_values = (
            series.dropna()
            .astype(str)
            .head(5)
            .tolist()
        )

        column_details.append({
            "column": str(column),
            "data_type": str(series.dtype),
            "role": role,
            "missing_values": int(series.isna().sum()),
            "unique_values": int(series.nunique(dropna=True)),
            "sample_values": sample_values
        })

    # Collect columns by their detected roles
    role_groups = {}

    for detail in column_details:
        role = detail["role"]
        role_groups.setdefault(role, []).append(detail["column"])

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    date_columns = role_groups.get("date", [])
    category_columns = role_groups.get("category", [])
    identifier_columns = role_groups.get("identifier", [])
    measure_columns = role_groups.get("measure", [])

    return {
        "dataset_summary": {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage_mb": float(round(
           df.memory_usage(deep=True).sum() / (1024 * 1024), 2
          ))
        },

        "columns": column_details,

        "detected_roles": role_groups,

        "suggestions": {
            "numeric_columns": numeric_columns,
            "measure_columns": measure_columns,
            "category_columns": category_columns,
            "date_columns": date_columns,
            "identifier_columns": identifier_columns
        }
    }

def get_schema_summary(df):
    """Return a simple human-readable schema report."""

    schema = detect_schema(df)

    lines = [
        f"Rows: {schema['dataset_summary']['total_rows']}",
        f"Columns: {schema['dataset_summary']['total_columns']}",
        "",
        "Detected columns:"
    ]

    for detail in schema["columns"]:
        lines.append(
            f"{detail['column']} -> {detail['role']} "
            f"({detail['data_type']})"
        )

    return "\n".join(lines)