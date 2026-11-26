
import pandas as pd
import numpy as np
import plotly.express as px

from analytics.schema_detector import detect_schema


def get_visualization_options(df):
    """Identify columns suitable for different chart types."""

    if df is None or df.empty:
        raise ValueError("Dataset is empty.")

    schema = detect_schema(df)
    roles = schema["detected_roles"]

    numeric_columns = [
        column
        for column in df.select_dtypes(include=np.number).columns
        if column not in roles.get("identifier", [])
    ]

    category_columns = [
        column
        for column in (
            roles.get("category", [])
            + roles.get("text", [])
        )
        if column not in numeric_columns
        and column not in roles.get("identifier", [])
    ]

    return {
        "numeric_columns": numeric_columns,
        "category_columns": category_columns,
        "date_columns": roles.get("date", [])
    }

def create_bar_chart(df, category_column, value_column, aggregation="sum"):
    if category_column not in df.columns:
        raise ValueError("Category column not found.")

    if value_column not in df.columns:
        raise ValueError("Value column not found.")

    if not pd.api.types.is_numeric_dtype(df[value_column]):
        raise ValueError("Value column must be numeric.")

    grouped = (
        df.groupby(category_column, dropna=False)[value_column]
        .agg(aggregation)
        .reset_index()
    )

    return px.bar(
        grouped,
        x=category_column,
        y=value_column,
        title=f"{aggregation.title()} of {value_column} by {category_column}",
        text_auto=True
    )

def create_histogram(df, column):
    if column not in df.columns:
        raise ValueError("Column not found.")

    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError("Histogram requires a numeric column.")

    return px.histogram(
        df,
        x=column,
        title=f"Distribution of {column}",
        marginal="box"
    )

def create_line_chart(df, date_column, value_column):
    if date_column not in df.columns:
        raise ValueError("Date column not found.")

    if value_column not in df.columns:
        raise ValueError("Value column not found.")

    data = df.copy()
    data[date_column] = pd.to_datetime(
        data[date_column],
        errors="coerce"
    )

    data = data.dropna(subset=[date_column])

    grouped = (
        data.groupby(date_column)[value_column]
        .sum()
        .reset_index()
        .sort_values(date_column)
    )

    return px.line(
        grouped,
        x=date_column,
        y=value_column,
        markers=True,
        title=f"{value_column} over time"
    )


def create_scatter_chart(df, x_column, y_column):
    for column in [x_column, y_column]:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError("Scatter plot requires numeric columns.")

    clean_df = df[[x_column, y_column]].dropna()

    return px.scatter(
        clean_df,
        x=x_column,
        y=y_column,
        title=f"{y_column} vs {x_column}"
    )

def create_pie_chart(df, category_column):
    if category_column not in df.columns:
        raise ValueError("Category column not found.")

    counts = (
        df[category_column]
        .fillna("Missing")
        .astype(str)
        .value_counts()
        .reset_index()
    )

    counts.columns = [category_column, "Count"]

    return px.pie(
        counts,
        names=category_column,
        values="Count",
        title=f"Distribution of {category_column}"
    )

def create_correlation_heatmap(df):
    options = get_visualization_options(df)
    numeric_columns = options["numeric_columns"]

    if len(numeric_columns) < 2:
        raise ValueError(
            "At least two numeric measure columns are required."
        )

    correlation = df[numeric_columns].corr()

    return px.imshow(
        correlation,
        text_auto=True,
        aspect="auto",
        title="Correlation Heatmap",
        color_continuous_scale="RdBu"
    )

def generate_auto_charts(df):
    """Generate a list of suitable chart recommendations."""

    options = get_visualization_options(df)

    charts = []

    numeric = options["numeric_columns"]
    categories = options["category_columns"]
    dates = options["date_columns"]

    for category in categories[:2]:
        for measure in numeric[:2]:
            charts.append({
                "type": "bar",
                "title": f"{measure} by {category}",
                "category": category,
                "value": measure
            })

    for measure in numeric[:3]:
        charts.append({
            "type": "histogram",
            "title": f"Distribution of {measure}",
            "column": measure
        })

    if numeric and categories:
        charts.append({
            "type": "pie",
            "title": f"Distribution of {categories[0]}",
            "category": categories[0]
        })

    if numeric and dates:
        charts.append({
            "type": "line",
            "title": f"{numeric[0]} over time",
            "date": dates[0],
            "value": numeric[0]
        })

    if len(numeric) >= 2:
        charts.append({
            "type": "scatter",
            "title": f"{numeric[1]} vs {numeric[0]}",
            "x": numeric[0],
            "y": numeric[1]
        })

        charts.append({
            "type": "correlation",
            "title": "Correlation Heatmap"
        })

    return charts