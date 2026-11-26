
"""Dataset-agnostic Business Analyst Agent.
Uses instant local Python analytics first, then Ollama for complex questions.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import numpy as np
import pandas as pd
import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
REQUEST_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "90"))
MAX_CONTEXT_ROWS = 500


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return None if np.isnan(value) else float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if value is None or value is pd.NA:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _format_number(value: Any) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _find_column(df: pd.DataFrame, question: str, numeric_only=False):
    """Find a dataset column explicitly mentioned in the question."""

    normalized_question = _normalize(question)

    candidates = (
        df.select_dtypes(include="number").columns.tolist()
        if numeric_only
        else df.columns.tolist()
    )

    matches = []

    for column in candidates:
        normalized_column = _normalize(str(column))

        if not normalized_column:
            continue

        if normalized_column in normalized_question:
            matches.append(column)

    if matches:
        return max(matches, key=lambda col: len(_normalize(str(col))))

    return None


# ---------------------------------------------------------
# INSTANT PYTHON ANALYTICS
# ---------------------------------------------------------

def answer_with_python(df: pd.DataFrame, question: str):
    """
    Answer common questions without Ollama.
    Returns None when the question needs an AI-generated explanation.
    """

    q = str(question).strip().lower()
    normalized_q = _normalize(q)

    row_words = [
        "row", "rows", "record", "records", "entries",
        "data points"
    ]

    column_words = [
        "column", "columns", "feature", "features",
        "field", "fields"
    ]

    # 1. Total rows and columns
    asks_rows = any(word in normalized_q for word in row_words)
    asks_columns = any(word in normalized_q for word in column_words)

    if asks_rows and asks_columns:
        return (
            "Your dataset contains "
            f"{len(df):,} rows and {len(df.columns):,} columns."
        )

    # 2. Total rows
    if asks_rows and any(
        word in normalized_q
        for word in ["how many", "total", "number", "count"]
    ):
        return f"Your dataset contains {len(df):,} rows."

    # 3. Total columns
    if asks_columns and any(
        word in normalized_q
        for word in ["how many", "total", "number", "count"]
    ):
        return f"Your dataset contains {len(df.columns):,} columns."

    # 4. Missing values
    missing_words = [
        "missing", "null", "nulls", "na values",
        "empty values", "missing values"
    ]

    if any(word in normalized_q for word in missing_words):
        column = _find_column(df, question)

        if column is not None:
            count = int(df[column].isna().sum())
            percentage = (
                count / len(df) * 100 if len(df) else 0
            )

            return (
                f"Column '{column}' contains {count:,} missing values "
                f"({percentage:.2f}% of its rows)."
            )

        missing = df.isna().sum()
        missing = missing[missing > 0].sort_values(ascending=False)

        if missing.empty:
            return "Your dataset has no missing values."

        lines = [
            f"{col}: {int(count):,}"
            for col, count in missing.head(15).items()
        ]

        return (
            f"Your dataset contains {int(missing.sum()):,} "
            "missing cells.\n\n"
            + "\n".join(lines)
        )

    # 5. Duplicate records
    if any(
        word in normalized_q
        for word in ["duplicate", "duplicates", "repeated rows"]
    ):
        count = int(df.duplicated().sum())

        return f"Your dataset contains {count:,} duplicate rows."

    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    # 6. Numeric column statistics
    stat_column = _find_column(
        df,
        question,
        numeric_only=True
    )

    average_words = [
        "average", "mean", "avg"
    ]

    total_words = [
        "total", "sum", "overall"
    ]

    maximum_words = [
        "maximum", "max", "highest", "largest", "biggest"
    ]

    minimum_words = [
        "minimum", "min", "lowest", "smallest"
    ]

    median_words = ["median"]
    mode_words = ["mode", "most common"]

    if stat_column is not None:
        series = pd.to_numeric(
            df[stat_column],
            errors="coerce"
        ).dropna()

        if series.empty:
            return f"Column '{stat_column}' has no valid numeric values."

        if any(word in normalized_q for word in average_words):
            return (
                f"The average of '{stat_column}' is "
                f"{_format_number(series.mean())}."
            )

        if any(word in normalized_q for word in total_words):
            return (
                f"The total of '{stat_column}' is "
                f"{_format_number(series.sum())}."
            )

        if any(word in normalized_q for word in maximum_words):
            return (
                f"The maximum value of '{stat_column}' is "
                f"{_format_number(series.max())}."
            )

        if any(word in normalized_q for word in minimum_words):
            return (
                f"The minimum value of '{stat_column}' is "
                f"{_format_number(series.min())}."
            )

        if any(word in normalized_q for word in median_words):
            return (
                f"The median of '{stat_column}' is "
                f"{_format_number(series.median())}."
            )

        if any(word in normalized_q for word in mode_words):
            modes = series.mode()

            if not modes.empty:
                return (
                    f"The most common value of '{stat_column}' is "
                    f"{_format_number(modes.iloc[0])}."
                )

    # 7. Highest or lowest category by numeric measure
    category_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    if numeric_columns and category_columns:
        category_column = _find_column(df, question)

        if category_column in category_columns and stat_column is not None:
            asks_highest = any(
                word in normalized_q
                for word in maximum_words
            )

            asks_lowest = any(
                word in normalized_q
                for word in minimum_words
            )

            if asks_highest or asks_lowest:
                grouped = (
                    df.groupby(category_column, dropna=True)[stat_column]
                    .mean()
                    .dropna()
                )

                if not grouped.empty:
                    selected = (
                        grouped.idxmax()
                        if asks_highest
                        else grouped.idxmin()
                    )

                    direction = (
                        "highest"
                        if asks_highest
                        else "lowest"
                    )

                    return (
                        f"'{selected}' has the {direction} average "
                        f"'{stat_column}' value: "
                        f"{_format_number(grouped.loc[selected])}."
                    )

    # 8. General dataset overview
    if any(
        word in normalized_q
        for word in ["dataset overview", "data overview", "summarize dataset"]
    ):
        return (
            f"Dataset overview:\n"
            f"- Rows: {len(df):,}\n"
            f"- Columns: {len(df.columns):,}\n"
            f"- Numeric columns: {len(numeric_columns)}\n"
            f"- Categorical columns: {len(category_columns)}\n"
            f"- Missing cells: {int(df.isna().sum().sum()):,}\n"
            f"- Duplicate rows: {int(df.duplicated().sum()):,}"
        )

    # No simple rule matched: use Ollama.
    return None


# ---------------------------------------------------------
# DATASET CONTEXT
# ---------------------------------------------------------

def prepare_business_context(df: pd.DataFrame) -> dict:
    """Build a compact summary for any tabular dataset."""

    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Upload a non-empty dataset first.")

    sample = df.head(MAX_CONTEXT_ROWS)

    numeric_cols = sample.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_cols = sample.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    numeric_summary = {}

    for col in numeric_cols[:12]:
        series = pd.to_numeric(
            sample[col],
            errors="coerce"
        ).dropna()

        if not series.empty:
            numeric_summary[str(col)] = {
                "count": int(series.count()),
                "mean": round(float(series.mean()), 3),
                "median": round(float(series.median()), 3),
                "min": round(float(series.min()), 3),
                "max": round(float(series.max()), 3),
                "sum": round(float(series.sum()), 3),
            }

    category_summary = {}

    for col in categorical_cols[:8]:
        counts = (
            sample[col]
            .astype("string")
            .fillna("<missing>")
            .value_counts()
            .head(5)
        )

        category_summary[str(col)] = {
            str(k): int(v)
            for k, v in counts.items()
        }

    context = {
        "dataset": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": [str(c) for c in df.columns[:30]],
            "duplicate_rows": int(df.duplicated().sum()),
            "total_missing_cells": int(df.isna().sum().sum()),
            "missing_by_column": {
                str(k): int(v)
                for k, v in (
                    df.isna().sum()
                    .sort_values(ascending=False)
                    .head(15)
                    .items()
                )
                if v
            },
            "data_types": {
                str(k): str(v)
                for k, v in df.dtypes.items()
            },
        },
        "numeric_summary": numeric_summary,
        "top_categories": category_summary,
    }

    return context


# ---------------------------------------------------------
# OLLAMA AI AGENT
# ---------------------------------------------------------

def ask_business_agent(
    df: pd.DataFrame,
    question: str,
    context: dict | None = None
) -> str:
    """
    First use instant Python analytics.
    If the question is complex, use local Ollama.
    """

    if not question or not str(question).strip():
        return "Please enter a question about your dataset."

    if not isinstance(df, pd.DataFrame) or df.empty:
        return "Please upload a non-empty dataset first."

    question = str(question).strip()

    # STEP 1: Instant Python fallback
    try:
        local_answer = answer_with_python(df, question)

        if local_answer is not None:
            return local_answer

    except Exception as exc:
        print("Local analytics fallback error:", exc)

    # STEP 2: Prepare compact context
    try:
        if context is None:
            context = prepare_business_context(df)

        compact_context = json.dumps(
            context,
            ensure_ascii=False,
            default=str
        )[:12000]

    except Exception as exc:
        return f"Could not prepare dataset context: {exc}"

    # STEP 3: Ask Ollama for complex questions
    prompt = f"""
You are BizAnalyst AI, a careful senior data analyst.

Answer using only the supplied dataset facts.

Rules:
- Support any dataset domain.
- Never invent data or columns.
- Distinguish correlation from causation.
- Explain missing information honestly.
- Answer in the same language as the question.
- Be concise and practical.

DATASET:
{compact_context}

QUESTION:
{question[:800]}

ANSWER:
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.2,
            "num_predict": 100,
            "num_ctx": 2048,
            "num_thread": 4,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        answer = str(
            response.json().get("response", "")
        ).strip()

        if not answer:
            return "The local AI returned an empty response."

        return answer

    except requests.exceptions.Timeout:
        return (
            "The complex AI analysis timed out. "
            "Basic analytics questions still work through "
            "the local Python analytics engine. "
            "Try asking a more specific question."
        )

    except requests.exceptions.ConnectionError:
        return (
            "Cannot connect to Ollama. "
            "Basic Python analytics are still available. "
            "Start Ollama for complex AI questions."
        )

    except requests.exceptions.HTTPError as exc:
        return f"Ollama HTTP error: {exc}"

    except Exception as exc:
        return f"Business AI Agent error: {exc}"
