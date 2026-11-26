
import pandas as pd
import operator


OPERATORS = {
    "equals": operator.eq,
    "not_equals": operator.ne,
    "greater_than": operator.gt,
    "less_than": operator.lt,
    "greater_equal": operator.ge,
    "less_equal": operator.le
}


def select_columns(df, columns):
    """Return selected columns."""

    if not columns:
        raise ValueError("Select at least one column.")

    invalid = [col for col in columns if col not in df.columns]

    if invalid:
        raise ValueError(f"Invalid columns: {invalid}")

    return df[columns].copy()


def rename_columns(df, rename_mapping):
    """Rename columns using a dictionary."""

    invalid = [
        col for col in rename_mapping
        if col not in df.columns
    ]

    if invalid:
        raise ValueError(f"Columns not found: {invalid}")

    new_names = list(rename_mapping.values())

    if any(not str(name).strip() for name in new_names):
        raise ValueError("New column names cannot be empty.")

    if len(set(new_names)) != len(new_names):
        raise ValueError("New column names must be unique.")

    result = df.copy()

    result = result.rename(columns=rename_mapping)

    if not result.columns.is_unique:
        raise ValueError("Renaming creates duplicate column names.")

    return result


def filter_data(df, column, condition, value):
    """Filter rows using a comparison operator."""

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    if condition not in OPERATORS:
        raise ValueError("Unsupported filter condition.")

    series = df[column]

    if condition in ["greater_than", "less_than",
                     "greater_equal", "less_equal"]:
        try:
            value = float(value)

            if pd.api.types.is_integer_dtype(series.dtype):
                value = int(value)

        except (ValueError, TypeError):
            raise ValueError("Enter a valid numeric filter value.")

    try:
        mask = OPERATORS[condition](series, value)
    except (TypeError, ValueError):
        raise ValueError(
            "Filter value is incompatible with the selected column."
        )

    return df.loc[mask.fillna(False)].copy()


def sort_data(df, column, ascending=True):
    """Sort rows by a selected column."""

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found.")

    return df.sort_values(
        by=column,
        ascending=ascending,
        na_position="last"
    ).reset_index(drop=True)


def create_calculated_column(df, new_column, column1, operation,
                             column2=None, constant=None):
    """Create a new calculated column."""

    if column1 not in df.columns:
        raise ValueError(f"Column '{column1}' not found.")

    if not new_column or new_column in df.columns:
        raise ValueError("New column name must be valid and unique.")

    if not pd.api.types.is_numeric_dtype(df[column1]):
        raise ValueError("First column must be numeric.")

    result = df.copy()

    if operation in ["add", "subtract", "multiply", "divide"]:

        if column2 not in df.columns:
            raise ValueError("Select a valid second column.")

        if not pd.api.types.is_numeric_dtype(df[column2]):
            raise ValueError("Second column must be numeric.")

        if operation == "add":
            result[new_column] = result[column1] + result[column2]

        elif operation == "subtract":
            result[new_column] = result[column1] - result[column2]

        elif operation == "multiply":
            result[new_column] = result[column1] * result[column2]

        elif operation == "divide":
            result[new_column] = (
                result[column1] / result[column2].replace(0, float("nan"))
            )

    elif operation == "add_constant":
        result[new_column] = result[column1] + float(constant)

    elif operation == "multiply_constant":
        result[new_column] = result[column1] * float(constant)

    else:
        raise ValueError("Unsupported calculation.")

    return result


def drop_columns(df, columns):
    """Drop selected columns."""

    if not columns:
        raise ValueError("Select at least one column.")

    invalid = [col for col in columns if col not in df.columns]

    if invalid:
        raise ValueError(f"Columns not found: {invalid}")

    if len(columns) >= len(df.columns):
        raise ValueError("Cannot remove every column.")

    return df.drop(columns=columns).copy()


def remove_duplicates(df):
    """Remove exact duplicate rows."""

    return df.drop_duplicates().copy().reset_index(drop=True)
