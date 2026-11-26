
import sqlite3
import pandas as pd
import re

def create_sql_connection(df, table_name="uploaded_data"):
    """Load a DataFrame into an in-memory SQLite database."""

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Please provide a valid DataFrame.")

    if df.empty:
        raise ValueError("Dataset is empty.")

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
        raise ValueError("Invalid table name.")

    connection = sqlite3.connect(":memory:")

    df.to_sql(
        table_name,
        connection,
        index=False,
        if_exists="replace"
    )

    return connection

def execute_sql_query(df, query, table_name="uploaded_data"):
    """Execute a read-only SQL query on uploaded data."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("SQL query cannot be empty.")

    cleaned_query = query.strip()

    # Only allow SELECT and WITH queries.
    if not re.match(r"^(SELECT|WITH)\b", cleaned_query, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")

    # Allow one SQL statement only.
    if ";" in cleaned_query.rstrip(";"):
        raise ValueError("Only one SQL statement is allowed.")

    connection = create_sql_connection(df, table_name)

    try:
        connection.execute("PRAGMA query_only = ON")

        result = pd.read_sql_query(
            cleaned_query,
            connection
        )

        return {
            "success": True,
            "data": result,
            "rows_returned": len(result),
            "message": "SQL query executed successfully."
        }

    except Exception as error:
        raise ValueError(f"SQL execution failed: {error}")

    finally:
        connection.close()

def get_sql_table_info(df, table_name="uploaded_data"):
    """Return available SQL table columns."""

    connection = create_sql_connection(df, table_name)

    try:
        cursor = connection.execute(
            f'PRAGMA table_info("{table_name}")'
        )

        columns = cursor.fetchall()

        return pd.DataFrame(
            columns,
            columns=[
                "Column ID",
                "Column Name",
                "Data Type",
                "Not Null",
                "Default Value",
                "Primary Key"
            ]
        )

    finally:
        connection.close()