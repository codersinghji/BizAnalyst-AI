
import pandas as pd
import numpy as np

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def normalize_name(name):
    return str(name).strip().lower().replace(" ", "_").replace("-", "_")

def find_column(df, possible_names):
    """Find a column without depending on capitalization."""
    columns = {
        normalize_name(column): column
        for column in df.columns
    }

    for name in possible_names:
        if normalize_name(name) in columns:
            return columns[normalize_name(name)]

    return None

def get_numeric_columns(df):
    """Find useful numeric columns and exclude identifiers."""
    numeric_columns = df.select_dtypes(include=np.number).columns.tolist()

    excluded_words = [
        "id", "zip", "postal", "phone", "mobile",
        "pincode", "code"
    ]

    return [
        col for col in numeric_columns
        if not any(word in normalize_name(col) for word in excluded_words)
    ]

def detect_date_column(df):
    """Detect a likely date column."""
    for col in df.columns:
        name = normalize_name(col)

        if any(word in name for word in ["date", "time", "month", "year"]):
            return col

    return None

# ==========================================
# MAIN BUSINESS INSIGHTS ENGINE
# ==========================================

def generate_business_insights(df):

    insights = []

    if df is None or df.empty:
        return ["No data available for business insights."]

    try:
        rows, columns = df.shape

        # ----------------------------------
        # 1. DATASET OVERVIEW
        # ----------------------------------

        insights.append(
            f"The dataset contains {rows:,} records "
            f"and {columns} columns."
        )

        duplicate_count = int(df.duplicated().sum())

        if duplicate_count > 0:
            insights.append(
                f"{duplicate_count:,} duplicate records were detected. "
                "Review them before removing any data."
            )
        else:
            insights.append("No duplicate records were detected.")

        missing_total = int(df.isnull().sum().sum())

        if missing_total > 0:
            insights.append(
                f"The dataset contains {missing_total:,} missing values. "
                "Review missing data before performing analysis."
            )

            missing_columns = (
                df.isnull()
                .sum()
                .sort_values(ascending=False)
            )

            for col, count in missing_columns.head(5).items():
                if count > 0:
                    percentage = count / max(rows, 1) * 100

                    insights.append(
                        f"Column '{col}' has {count} missing values "
                        f"({percentage:.2f}%)."
                    )
        else:
            insights.append("No missing values were detected.")

        # ----------------------------------
        # 2. NUMERIC ANALYSIS
        # ----------------------------------

        numeric_columns = get_numeric_columns(df)

        for col in numeric_columns[:8]:

            series = pd.to_numeric(
                df[col],
                errors="coerce"
            ).dropna()

            if series.empty:
                continue

            average = float(series.mean())
            minimum = float(series.min())
            maximum = float(series.max())
            median = float(series.median())

            insights.append(
                f"'{col}' has an average of {average:.2f}, "
                f"median of {median:.2f}, "
                f"minimum of {minimum:.2f}, "
                f"and maximum of {maximum:.2f}."
            )

            if minimum < 0:
                insights.append(
                    f"'{col}' contains negative values. "
                    "Check whether these values are expected."
                )

        # ----------------------------------
        # 3. CATEGORY ANALYSIS
        # ----------------------------------

        categorical_columns = df.select_dtypes(
            include=["object", "category", "string"]
        ).columns.tolist()

        for col in categorical_columns[:5]:

            unique_count = df[col].nunique(dropna=True)

            if unique_count == 0 or unique_count > 100:
                continue

            top_values = (
                df[col]
                .value_counts(dropna=True)
                .head(3)
            )

            if not top_values.empty:

                top_value = str(top_values.index[0])
                top_count = int(top_values.iloc[0])

                insights.append(
                    f"In '{col}', the most frequent category is "
                    f"'{top_value}' with {top_count} records."
                )

        # ----------------------------------
        # 4. DATE / TIME TREND ANALYSIS
        # ----------------------------------

        date_column = detect_date_column(df)

        if date_column:

            dates = pd.to_datetime(
                df[date_column],
                errors="coerce"
            )

            valid_dates = dates.dropna()

            if len(valid_dates) >= 2:

                insights.append(
                    f"The date range is from "
                    f"{valid_dates.min().date()} to "
                    f"{valid_dates.max().date()}."
                )

                if len(valid_dates) >= 3:

                    date_data = pd.DataFrame({
                        "date": dates,
                        "value": 1
                    }).dropna()

                    date_data["period"] = (
                        date_data["date"].dt.to_period("M")
                    )

                    monthly_counts = (
                        date_data.groupby("period")["value"].sum()
                    )

                    if len(monthly_counts) >= 2:

                        previous = monthly_counts.iloc[-2]
                        current = monthly_counts.iloc[-1]

                        if previous > 0:

                            change = (
                                (current - previous) / previous
                            ) * 100

                            insights.append(
                                f"Record volume changed by "
                                f"{change:.2f}% in the latest month "
                                "compared with the previous month."
                            )

        # ----------------------------------
        # 5. CORRELATION ANALYSIS
        # ----------------------------------

        if len(numeric_columns) >= 2:

            correlation = df[numeric_columns].corr()

            pairs = []

            for i in range(len(correlation.columns)):
                for j in range(i + 1, len(correlation.columns)):

                    value = correlation.iloc[i, j]

                    if pd.notna(value):
                        pairs.append((
                            abs(float(value)),
                            correlation.columns[i],
                            correlation.columns[j],
                            float(value)
                        ))

            pairs.sort(reverse=True)

            for _, col1, col2, value in pairs[:3]:

                if abs(value) >= 0.7:
                    strength = "strong"
                elif abs(value) >= 0.4:
                    strength = "moderate"
                else:
                    strength = "weak"

                direction = (
                    "positive" if value > 0 else "negative"
                )

                insights.append(
                    f"'{col1}' and '{col2}' show a "
                    f"{strength} {direction} correlation "
                    f"({value:.2f}). Correlation does not prove causation."
                )

        # ----------------------------------
        # 6. SALES / PROFIT ANALYSIS
        # ----------------------------------

        sales_col = find_column(
            df,
            ["sales", "revenue", "amount", "total_amount"]
        )

        profit_col = find_column(
            df,
            ["profit", "net_profit", "earnings"]
        )

        if sales_col:

            sales = pd.to_numeric(
                df[sales_col],
                errors="coerce"
            ).dropna()

            if not sales.empty:

                insights.append(
                    f"Total '{sales_col}' is "
                    f"{sales.sum():,.2f}."
                )

                insights.append(
                    f"Average '{sales_col}' per record is "
                    f"{sales.mean():,.2f}."
                )

        if profit_col:

            profit = pd.to_numeric(
                df[profit_col],
                errors="coerce"
            ).dropna()

            if not profit.empty:

                total_profit = profit.sum()

                insights.append(
                    f"Total '{profit_col}' is "
                    f"{total_profit:,.2f}."
                )

                negative_count = int((profit < 0).sum())

                if negative_count > 0:
                    insights.append(
                        f"{negative_count} records have negative "
                        f"'{profit_col}' values and should be reviewed."
                    )

        # ----------------------------------
        # 7. CUSTOMER ANALYSIS
        # ----------------------------------

        customer_col = find_column(
            df,
            ["customer_id", "customer", "client_id", "client"]
        )

        order_col = find_column(
            df,
            ["order_id", "transaction_id", "invoice_id"]
        )

        if customer_col:

            total_customers = int(
                df[customer_col].nunique(dropna=True)
            )

            insights.append(
                f"The dataset contains {total_customers:,} "
                "unique customers."
            )

            if order_col:

                customer_orders = (
                    df.groupby(customer_col)[order_col]
                    .nunique()
                )

                repeat_customers = int(
                    (customer_orders > 1).sum()
                )

                repeat_rate = (
                    repeat_customers / total_customers * 100
                    if total_customers else 0
                )

                insights.append(
                    f"{repeat_rate:.2f}% of customers "
                    "have more than one distinct order."
                )

    except Exception as error:
        insights.append(
            f"Some insights could not be calculated: {str(error)}"
        )

    if not insights:
        insights.append(
            "The dataset was loaded, but no additional insights "
            "could be generated."
        )

    return insights