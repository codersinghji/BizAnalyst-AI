import os
import io
import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# IMPORTS: EXISTING PROJECT MODULES
# ==========================================

from auth.auth_ui import show_auth_page, logout_user


from analytics.prediction_engine import (
    train_prediction_model,
    predict_new_data
)


from powerbi.powerbi_export import (
    export_powerbi_csv,
    export_powerbi_excel,
    get_powerbi_export_info
)

from analytics.data_loader import load_dataset
from analytics.data_profiling import (
    generate_data_profile,
    generate_summary
)
from analytics.schema_detector import detect_schema
from analytics.data_cleaning import clean_data, detect_outliers
from analytics.data_manipulation import (
    filter_data,
    sort_data,
    rename_columns,
    create_calculated_column
)
from analytics.aggregation_engine import aggregate_data
from analytics.statistical_analysis import calculate_statistics
from analytics.sql_analysis import execute_sql_query

from analytics.visualization_engine import (
    get_visualization_options,
    generate_auto_charts,
    create_bar_chart,
    create_histogram,
    create_line_chart,
    create_scatter_chart,
    create_pie_chart,
    create_correlation_heatmap
)

# Existing business analytics
from analytics.rfm_analysis import (
    create_rfm,
    segment_customers,
    get_customer_summary
)

from analytics.business_kpis import calculate_business_kpis

from analytics.business_analysis import (
    monthly_sales_analysis,
    regional_analysis,
    category_analysis,
    top_products_analysis,
    discount_analysis
)

from analytics.business_insights import generate_business_insights

# Existing AI agent
from agents.business_analyst_agent import ask_business_agent, prepare_business_context
from agents.voice_agent import transcribe_audio, text_to_speech, get_voice_status


def load_css():
    """Load the external dashboard stylesheet, if it exists."""
    css_path = os.path.join("frontend", "styles.css")

    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as file:
            css = file.read()

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True
        )
    else:
        st.warning("CSS file not found: frontend/styles.css")


@st.cache_data(show_spinner=False, ttl=600)
def get_cached_business_context(dataframe):
    """Cache dataset summaries for 10 minutes to avoid recalculating per question."""
    return prepare_business_context(dataframe)


# ==========================================
# POWER BI DASHBOARD HELPER FUNCTIONS
# ==========================================

def find_column_by_keywords(dataframe, keywords, numeric_only=False):
    """Find a column using common business column names."""

    for column in dataframe.columns:
        name = str(column).lower().replace(" ", "_")

        if any(keyword in name for keyword in keywords):
            if numeric_only and not pd.api.types.is_numeric_dtype(dataframe[column]):
                continue
            return column

    return None

def prepare_dashboard_data(dataframe):
    """Identify date, category, numeric and geographic columns."""

    data = dataframe.copy()

    date_columns = []
    category_columns = []
    numeric_columns = []

    for column in data.columns:

        series = data[column]
        name = str(column).lower()

        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(column)

        elif any(word in name for word in ["date", "time", "month", "year"]):
            converted = pd.to_datetime(series, errors="coerce")

            if converted.notna().sum() > 0:
                data[column] = converted
                date_columns.append(column)

        elif pd.api.types.is_numeric_dtype(series):
            numeric_columns.append(column)

        elif series.nunique(dropna=True) <= min(100, max(20, len(data) // 2)):
            category_columns.append(column)

    latitude = find_column_by_keywords(
        data,
        ["latitude", "lat"]
    )

    longitude = find_column_by_keywords(
        data,
        ["longitude", "lon", "lng"]
    )

    country = find_column_by_keywords(
        data,
        ["country"]
    )

    return {
        "data": data,
        "dates": date_columns,
        "categories": category_columns,
        "numeric": numeric_columns,
        "latitude": latitude,
        "longitude": longitude,
        "country": country
    }

def create_dashboard_kpis(dataframe, numeric_columns):

    metrics = []

    # Always available
    metrics.append(("Total Records", f"{len(dataframe):,}"))

    customer_column = find_column_by_keywords(
        dataframe,
        ["customer_id", "customerid", "customer"]
    )

    order_column = find_column_by_keywords(
        dataframe,
        ["order_id", "orderid", "invoice_id"]
    )

    if customer_column:
        metrics.append((
            "Unique Customers",
            f"{dataframe[customer_column].nunique():,}"
        ))

    if order_column:
        metrics.append((
            "Unique Orders",
            f"{dataframe[order_column].nunique():,}"
        ))

    revenue_column = find_column_by_keywords(
        dataframe,
        ["revenue", "sales", "total_amount", "amount"],
        numeric_only=True
    )

    profit_column = find_column_by_keywords(
        dataframe,
        ["profit", "net_income", "earnings"],
        numeric_only=True
    )

    quantity_column = find_column_by_keywords(
        dataframe,
        ["quantity", "units_sold", "units"],
        numeric_only=True
    )

    if revenue_column:
        metrics.append((
            "Total Revenue / Sales",
            f"{dataframe[revenue_column].sum():,.2f}"
        ))

    if profit_column:
        metrics.append((
            "Total Profit",
            f"{dataframe[profit_column].sum():,.2f}"
        ))

    if quantity_column:
        metrics.append((
            "Total Quantity",
            f"{dataframe[quantity_column].sum():,.2f}"
        ))

    if profit_column and revenue_column:
        revenue = dataframe[revenue_column].sum()

        if revenue != 0:
            margin = (
                dataframe[profit_column].sum() / revenue
            ) * 100

            metrics.append((
                "Profit Margin",
                f"{margin:.2f}%"
            ))

    # Generic KPI for datasets without business-specific fields
    if len(metrics) < 4 and numeric_columns:
        column = numeric_columns[0]

        metrics.append((
            f"Average {column}",
            f"{dataframe[column].mean():,.2f}"
        ))

    return metrics

def apply_dashboard_slicers(dataframe, date_columns, category_columns):

    filtered = dataframe.copy()

    st.subheader("🎛️ Interactive Slicers")

    # Date filter
    if date_columns:

        date_column = st.selectbox(
            "Select Date Field",
            date_columns,
            key="bi_date_column"
        )

        valid_dates = filtered[date_column].dropna()

        if not valid_dates.empty:

            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

            selected_dates = st.date_input(
                "Filter Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="bi_date_range"
            )

            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:

                start_date, end_date = selected_dates

                filtered = filtered[
                    filtered[date_column].between(
                        pd.Timestamp(start_date),
                        pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                    )
                ]

    # Categorical filters
    usable_categories = [
        column for column in category_columns
        if filtered[column].nunique(dropna=True) <= 100
    ]

    if usable_categories:

        selected_categories = st.multiselect(
            "Choose categories / regions / departments",
            usable_categories,
            default=[],
            key="bi_category_slicers"
        )

        for column in selected_categories:

            values = filtered[column].dropna().unique().tolist()

            selected_values = st.multiselect(
                f"Filter {column}",
                values,
                default=values,
                key=f"bi_filter_{column}"
            )

            filtered = filtered[
                filtered[column].isin(selected_values)
            ]

    return filtered

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="BizAnalyst AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load the external dashboard stylesheet after page configuration.
load_css()

# ==========================================
# AUTHENTICATION GATE
# ==========================================

if not show_auth_page():
    st.stop()
# ==========================================
# 2. CUSTOM CSS
# ==========================================

st.markdown("""
<style>

.main-header {
    font-size: 36px;
    font-weight: 800;
    color: #2563eb;
}

.sub-header {
    font-size: 16px;
    color: #64748b;
}

div[data-testid="stMetric"] {
    background-color: rgba(128, 128, 128, 0.08);
    padding: 15px;
    border-radius: 12px;
    border: 1px solid rgba(128, 128, 128, 0.15);
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HEADER
# ==========================================

st.markdown(
    '<div class="main-header">📊 BizAnalyst AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-header">Universal Intelligent Data Analytics Platform</div>',
    unsafe_allow_html=True
)

st.caption(
    "Upload data | Clean data | Analyze | Visualize | Discover insights"
)

st.divider()


# ==========================================
# 4. SIDEBAR AND ACCOUNT
# ==========================================

st.sidebar.title("⚙️ BizAnalyst AI")

current_user = st.session_state.get("user", {})

user_name = current_user.get("name", "User")
user_role = current_user.get("role", "Analyst")

st.sidebar.markdown("### 👤 Account")
st.sidebar.write(f"**Name:** {user_name}")
st.sidebar.write(f"**Role:** {user_role}")
st.sidebar.write("DEBUG ROLE:", user_role)

# ==========================================
# 5. LOGOUT
# ==========================================

if st.sidebar.button(
    "🚪 Logout",
    key="sidebar_logout_button",
    use_container_width=True
):
    logout_user()
    st.rerun()

st.sidebar.divider()

# ==========================================
# 6. ADMIN WORKSPACE
# ==========================================

if user_role.strip().lower() == "admin":

    workspace = st.sidebar.radio(
        "Select Workspace",
        ["Analytics Dashboard", "Admin Dashboard"],
        key="admin_workspace_radio"
    )

    if workspace == "Admin Dashboard":

        from auth.admin_panel import show_admin_panel

        show_admin_panel()
        st.stop()

else:
    workspace = "Analytics Dashboard"

# ==========================================
# 7. DATASET UPLOAD
# ==========================================

st.sidebar.subheader("📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    key="main_dataset_uploader"
)

# ==========================================
# 8. WELCOME SCREEN
# ==========================================

if uploaded_file is None:

    st.info(
        "Welcome to BizAnalyst AI! Upload a CSV or Excel dataset to begin."
    )

    st.subheader("Platform Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🧹 Data Cleaning")
        st.write("Inspect missing values, duplicates and outliers.")

    with col2:
        st.markdown("### 📊 Data Analytics")
        st.write("Perform aggregation, statistics and SQL analysis.")

    with col3:
        st.markdown("### 📈 Visualization")
        st.write("Generate interactive charts and explore patterns.")

    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("### 🤖 AI Analyst")
        st.write("Ask questions about your dataset using AI.")

    with col5:
        st.markdown("### 👥 Customer Analytics")
        st.write("Perform RFM customer segmentation when supported.")

    with col6:
        st.markdown("### 📥 Export")
        st.write("Download processed datasets and analysis results.")

    st.stop()

# ==========================================
# 6. LOAD DATASET
# ==========================================

try:

    df = load_dataset(uploaded_file)

    if not isinstance(df, pd.DataFrame):
        st.error("The uploaded file did not produce a valid DataFrame.")
        st.stop()

    if df.empty:
        st.error("The uploaded dataset is empty.")
        st.stop()

    # Preserve original uploaded data
    original_df = df.copy(deep=True)

    # Working dataset
    df = original_df.copy(deep=True)

    st.sidebar.success("Dataset uploaded successfully!")

except Exception as error:

    st.error(f"Dataset loading failed: {error}")
    st.stop()

# ==========================================
# 7. DATASET SCHEMA DETECTION
# ==========================================

try:

    schema_report = detect_schema(df)

    roles = schema_report["detected_roles"]

except Exception as error:

    st.error(f"Schema detection failed: {error}")
    st.stop()

# ==========================================
# 8. DATASET INFORMATION
# ==========================================

st.sidebar.divider()

st.sidebar.subheader("Dataset Information")

st.sidebar.write(f"Rows: {len(df):,}")
st.sidebar.write(f"Columns: {len(df.columns)}")

st.sidebar.write(
    f"Missing values: {int(df.isna().sum().sum()):,}"
)

# ==========================================
# 9. BUSINESS DATASET DETECTION
# ==========================================

normalized_columns = {
    str(column).strip().lower(): column
    for column in df.columns
}

business_required = [
    "sales",
    "profit",
    "order_id",
    "customer_id",
    "quantity",
    "region",
    "category",
    "product_name",
    "discount",
    "order_date"
]

is_business_dataset = all(
    column in normalized_columns
    for column in business_required
)

# Normalize legacy business dataset column names
if is_business_dataset:

    rename_map = {
        old: new
        for new, old in normalized_columns.items()
        if old != new
    }

    if rename_map:
        df = df.rename(columns=rename_map)


# ==========================================
# ADMIN WORKSPACE SELECTION
# ==========================================

if user_role.strip().lower() == "admin":

    workspace = st.sidebar.radio(
        "Select Workspace",
        ["Analytics Dashboard", "Admin Dashboard"],
        key="workspace_selection"
    )

    # Show Admin Dashboard
    if workspace == "Admin Dashboard":

        from auth.admin_panel import show_admin_panel

        show_admin_panel()
        st.stop()

else:
    workspace = "Analytics Dashboard"


# ==========================================
# 10. ANALYTICS NAVIGATION
# ==========================================

pages = [
    "Overview",
    "Power BI Dashboard",
    "Data Quality",
    "Data Cleaning",
    "Data Manipulation",
    "Aggregation",
    "Statistical Analysis",
    "SQL Analysis",
    "ML Predictions",
    "Visualizations",
    "AI Business Insights",
    "AI Business Analyst",
    "Export Data"
]

if is_business_dataset:

    pages.extend([
        "Sales Analysis",
        "Regional Analysis",
        "Product Analysis",
        "Discount Analysis",
        "Customer Analytics"
    ])

page = st.sidebar.radio(
    "Navigate Dashboard",
    pages,
    key="analytics_navigation"
)


# ==========================================
# 11. OVERVIEW
# ==========================================

if page == "Overview":

    st.header("📊 Dataset Overview")

    # ==========================================
    # DATASET KPI CARDS
    # ==========================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Records",
        f"{len(df):,}"
    )

    c2.metric(
        "Total Columns",
        len(df.columns)
    )

    c3.metric(
        "Missing Values",
        f"{int(df.isna().sum().sum()):,}"
    )

    c4.metric(
        "Duplicate Rows",
        f"{int(df.duplicated().sum()):,}"
    )

    st.divider()

    # ==========================================
    # DETECTED DATASET SCHEMA
    # ==========================================

    st.subheader("🔍 Detected Dataset Schema")

    schema_rows = []

    for role, columns in roles.items():

        if isinstance(columns, (list, tuple)):

            for column in columns:

                if column in df.columns:

                    schema_rows.append({
                        "Column": column,
                        "Detected Role": role,
                        "Data Type": str(df[column].dtype)
                    })

    if schema_rows:

        schema_table = pd.DataFrame(schema_rows)

        st.dataframe(
            schema_table,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No dataset schema information available.")

    st.divider()

    # ==========================================
    # DATASET PREVIEW
    # ==========================================

    st.subheader("📋 Dataset Preview")

    st.dataframe(
        df.head(100),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ==========================================
    # AUTOMATIC CHART RECOMMENDATIONS
    # ==========================================

    st.subheader("📈 Automatic Chart Recommendations")

    try:

        recommendations = generate_auto_charts(df)

        if recommendations:

            for recommendation in recommendations:

                st.write(
                    f"**{recommendation.get('type', 'Chart').title()}**: "
                    f"{recommendation.get('title', 'Recommended chart')}"
                )

        else:

            st.info(
                "No suitable automatic chart recommendations found."
            )

    except Exception as error:

        st.warning(
            f"Unable to generate automatic charts: {error}"
        )

# ==========================================
# POWER BI DASHBOARD
# ==========================================

elif page == "Power BI Dashboard":

    st.header("📊 Interactive Business Intelligence Dashboard")

    st.caption(
        "Explore your dataset using dynamic filters, KPIs, "
        "interactive charts and geographic analysis."
    )

    # Prepare dashboard data
    dashboard = prepare_dashboard_data(df)

    dashboard_df = dashboard["data"]
    date_columns = dashboard["dates"]
    category_columns = dashboard["categories"]
    numeric_columns = dashboard["numeric"]

    if dashboard_df.empty:
        st.warning("No data available for the dashboard.")

    else:

        # ------------------------------------------
        # INTERACTIVE FILTERS
        # ------------------------------------------

        filtered_df = dashboard_df.copy()

        st.subheader("🎛️ Dashboard Filters")

        filter_col1, filter_col2 = st.columns(2)

        # Date filter
        if date_columns:

            with filter_col1:

                date_column = st.selectbox(
                    "Date Column",
                    date_columns,
                    key="powerbi_date_column"
                )

                valid_dates = dashboard_df[date_column].dropna()

                if not valid_dates.empty:

                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()

                    date_range = st.date_input(
                        "Select Date Range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key="powerbi_date_range"
                    )

                    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:

                        start_date, end_date = date_range

                        filtered_df = filtered_df[
                            filtered_df[date_column].between(
                                pd.Timestamp(start_date),
                                pd.Timestamp(end_date)
                                + pd.Timedelta(days=1)
                                - pd.Timedelta(microseconds=1)
                            )
                        ]

        # Category filter
        if category_columns:

            with filter_col2:

                category_column = st.selectbox(
                    "Category / Region / Department",
                    ["All"] + category_columns,
                    key="powerbi_category_column"
                )

                if category_column != "All":

                    available_values = (
                        filtered_df[category_column]
                        .dropna()
                        .unique()
                        .tolist()
                    )

                    selected_values = st.multiselect(
                        f"Select {category_column}",
                        available_values,
                        default=available_values,
                        key="powerbi_category_values"
                    )

                    filtered_df = filtered_df[
                        filtered_df[category_column].isin(selected_values)
                    ]

        st.divider()

        # ------------------------------------------
        # KPI CARDS
        # ------------------------------------------

        st.subheader("📌 Key Performance Indicators")

        kpis = create_dashboard_kpis(
            filtered_df,
            numeric_columns
        )

        kpi_columns = st.columns(min(4, max(1, len(kpis))))

        for index, (label, value) in enumerate(kpis):

            with kpi_columns[index % len(kpi_columns)]:

                st.metric(
                    label=label,
                    value=value
                )

        st.divider()

        # ------------------------------------------
        # REVENUE AND PROFIT ANALYSIS
        # ------------------------------------------

        st.subheader("📈 Business Performance")

        revenue_column = find_column_by_keywords(
            filtered_df,
            ["revenue", "sales", "total_amount", "amount"],
            numeric_only=True
        )

        profit_column = find_column_by_keywords(
            filtered_df,
            ["profit", "net_income", "earnings"],
            numeric_only=True
        )

        quantity_column = find_column_by_keywords(
            filtered_df,
            ["quantity", "units_sold", "units"],
            numeric_only=True
        )

        if revenue_column and category_columns:

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:

                selected_category = st.selectbox(
                    "Revenue Analysis Category",
                    category_columns,
                    key="powerbi_revenue_category"
                )

                revenue_chart_data = (
                    filtered_df
                    .groupby(selected_category, dropna=False)[revenue_column]
                    .sum()
                    .reset_index()
                    .sort_values(revenue_column, ascending=False)
                    .head(15)
                )

                fig = px.bar(
                    revenue_chart_data,
                    x=selected_category,
                    y=revenue_column,
                    title="Revenue by Category",
                    text_auto=".2s"
                )

                fig.update_layout(
                    xaxis_title=selected_category,
                    yaxis_title=revenue_column
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            with chart_col2:

                if profit_column:

                    profit_chart_data = (
                        filtered_df
                        .groupby(selected_category, dropna=False)[profit_column]
                        .sum()
                        .reset_index()
                        .sort_values(profit_column, ascending=False)
                        .head(15)
                    )

                    fig = px.bar(
                        profit_chart_data,
                        x=selected_category,
                        y=profit_column,
                        title="Profit by Category",
                        text_auto=".2s"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                elif quantity_column:

                    quantity_chart_data = (
                        filtered_df
                        .groupby(selected_category, dropna=False)[quantity_column]
                        .sum()
                        .reset_index()
                    )

                    fig = px.bar(
                        quantity_chart_data,
                        x=selected_category,
                        y=quantity_column,
                        title="Quantity by Category"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                else:

                    st.info(
                        "A profit or quantity column was not detected."
                    )

        elif numeric_columns and category_columns:

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:

                selected_category = st.selectbox(
                    "Select Category",
                    category_columns,
                    key="powerbi_generic_category"
                )

            with chart_col2:

                selected_measure = st.selectbox(
                    "Select Numeric Measure",
                    numeric_columns,
                    key="powerbi_generic_measure"
                )

            chart_data = (
                filtered_df
                .groupby(selected_category, dropna=False)[selected_measure]
                .sum()
                .reset_index()
                .sort_values(selected_measure, ascending=False)
                .head(15)
            )

            fig = px.bar(
                chart_data,
                x=selected_category,
                y=selected_measure,
                title=f"{selected_measure} by {selected_category}"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Category and numeric columns are needed "
                "for category-based performance charts."
            )

        st.divider()

        # ------------------------------------------
        # TIME SERIES ANALYSIS
        # ------------------------------------------

        st.subheader("📅 Time-Based Analysis")

        if date_columns and numeric_columns:

            time_col1, time_col2 = st.columns(2)

            with time_col1:

                selected_date = st.selectbox(
                    "Select Date Field",
                    date_columns,
                    key="powerbi_trend_date"
                )

            with time_col2:

                default_measure = (
                    revenue_column
                    if revenue_column
                    else numeric_columns[0]
                )

                selected_time_measure = st.selectbox(
                    "Select Measure",
                    numeric_columns,
                    index=numeric_columns.index(default_measure),
                    key="powerbi_trend_measure"
                )

            trend_data = filtered_df[
                [selected_date, selected_time_measure]
            ].dropna()

            if not trend_data.empty:

                trend_data = (
                    trend_data
                    .groupby(selected_date)[selected_time_measure]
                    .sum()
                    .reset_index()
                    .sort_values(selected_date)
                )

                fig = px.line(
                    trend_data,
                    x=selected_date,
                    y=selected_time_measure,
                    markers=True,
                    title=f"{selected_time_measure} Trend"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info("No valid date records are available.")

        else:

            st.info(
                "A date column and numeric measure are required "
                "for time-based analysis."
            )

        st.divider()

        # ------------------------------------------
        # CATEGORY DISTRIBUTION
        # ------------------------------------------

        st.subheader("🍩 Category Distribution")

        if category_columns:

            distribution_column = st.selectbox(
                "Choose Distribution Column",
                category_columns,
                key="powerbi_distribution_column"
            )

            distribution_data = (
                filtered_df[distribution_column]
                .fillna("Missing")
                .value_counts()
                .head(15)
                .reset_index()
            )

            distribution_data.columns = [
                distribution_column,
                "Records"
            ]

            fig = px.pie(
                distribution_data,
                names=distribution_column,
                values="Records",
                hole=0.45,
                title=f"Distribution by {distribution_column}"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info("No categorical columns were detected.")

        st.divider()

        # ------------------------------------------
        # CORRELATION ANALYSIS
        # ------------------------------------------

        st.subheader("🔗 Numeric Correlation Analysis")

        if len(numeric_columns) >= 2:

            correlation_data = filtered_df[
                numeric_columns
            ].corr()

            fig = px.imshow(
                correlation_data,
                text_auto=".2f",
                aspect="auto",
                title="Correlation Heatmap",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "At least two numeric columns are required "
                "for correlation analysis."
            )

        st.divider()

        # ------------------------------------------
        # GEOGRAPHIC ANALYSIS
        # ------------------------------------------

        st.subheader("🌍 Geographic Analysis")

        latitude = dashboard["latitude"]
        longitude = dashboard["longitude"]
        country = dashboard["country"]

        if latitude and longitude:

            map_data = filtered_df[
                [latitude, longitude]
            ].copy()

            map_data[latitude] = pd.to_numeric(
                map_data[latitude],
                errors="coerce"
            )

            map_data[longitude] = pd.to_numeric(
                map_data[longitude],
                errors="coerce"
            )

            map_data = map_data.dropna()

            map_data = map_data[
                map_data[latitude].between(-90, 90)
                & map_data[longitude].between(-180, 180)
            ]

            if not map_data.empty:

                fig = px.scatter_map(
                    map_data,
                    lat=latitude,
                    lon=longitude,
                    zoom=1,
                    title="Geographic Data Distribution"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info("No valid geographic coordinates were found.")

        elif country and revenue_column:

            country_data = (
                filtered_df
                .groupby(country, dropna=False)[revenue_column]
                .sum()
                .reset_index()
            )

            fig = px.choropleth(
                country_data,
                locations=country,
                locationmode="country names",
                color=revenue_column,
                title="Revenue by Country"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info(
                "Geographic charts require latitude/longitude "
                "or country and revenue columns."
            )

        st.divider()

        # ------------------------------------------
        # FILTERED DATA
        # ------------------------------------------

        st.subheader("📋 Filtered Dashboard Dataset")

        st.write(
            f"Showing {len(filtered_df):,} records "
            f"out of {len(dashboard_df):,}."
        )

        st.dataframe(
            filtered_df,
            use_container_width=True
        )

        # ------------------------------------------
        # DASHBOARD EXPORT
        # ------------------------------------------

        st.subheader("📥 Export Dashboard Data")

        export_col1, export_col2 = st.columns(2)

        with export_col1:

            st.download_button(
                "Download Filtered CSV",
                data=filtered_df.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                file_name="bizanalyst_dashboard_data.csv",
                mime="text/csv",
                key="powerbi_dashboard_csv",
                use_container_width=True
            )

        with export_col2:

            try:

                excel_buffer = io.BytesIO()

                with pd.ExcelWriter(
                    excel_buffer,
                    engine="openpyxl"
                ) as writer:

                    filtered_df.to_excel(
                        writer,
                        index=False,
                        sheet_name="Dashboard Data"
                    )

                st.download_button(
                    "Download Filtered Excel",
                    data=excel_buffer.getvalue(),
                    file_name="bizanalyst_dashboard_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="powerbi_dashboard_excel",
                    use_container_width=True
                )

            except Exception as error:

                st.warning(f"Excel export unavailable: {error}")




# ==========================================
# 12. DATA QUALITY
# ==========================================

elif page == "Data Quality":

    st.header("🧹 Data Quality and Profiling")

    summary = generate_summary(df)

    if isinstance(summary, dict):

        st.subheader("Dataset Summary")

        st.json(summary)

    profile = generate_data_profile(df)

    if isinstance(profile, dict):

        st.subheader("Complete Data Profile")

        for key, value in profile.items():

            st.markdown(
                f"**{key.replace('_', ' ').title()}**"
            )

            if isinstance(value, pd.DataFrame):

                st.dataframe(
                    value,
                    use_container_width=True
                )

            elif isinstance(value, dict):

                st.json(value)

            else:

                st.write(value)

    else:

        st.subheader("Column Profile")

        st.dataframe(
            profile,
            use_container_width=True
        )

    st.subheader("Missing Value Report")

    missing_report = pd.DataFrame({
        "Column": df.columns,
        "Missing Values": df.isna().sum().values,
        "Missing Percentage": (
            df.isna().mean().values * 100
        ).round(2)
    })

    st.dataframe(
        missing_report,
        use_container_width=True
    )

    st.subheader("Outlier Report")

    try:

        outlier_report = detect_outliers(df)

        st.dataframe(
            outlier_report,
            use_container_width=True
        )

    except Exception as error:

        st.warning(f"Outlier analysis unavailable: {error}")

# ==========================================
# 13. DATA CLEANING
# ==========================================

elif page == "Data Cleaning":

    st.header("🧹 Interactive Data Cleaning")

    st.info(
        "The original uploaded dataset remains unchanged. "
        "Cleaning creates a separate processed copy."
    )

    numeric_strategy = st.selectbox(
        "Numeric Missing Value Strategy",
        ["median", "mean", "zero", "none"]
    )

    categorical_strategy = st.selectbox(
        "Categorical Missing Value Strategy",
        ["mode", "unknown", "none"]
    )

    remove_duplicates = st.checkbox(
        "Remove Duplicate Rows",
        value=False
    )

    if st.button(
        "Clean Dataset",
        type="primary"
    ):

        try:

            cleaned_df, cleaning_report = clean_data(
                df.copy(),
                numeric_strategy=numeric_strategy,
                categorical_strategy=categorical_strategy,
                remove_duplicates=remove_duplicates
            )

            st.session_state["cleaned_df"] = cleaned_df
            st.session_state["cleaning_report"] = cleaning_report

            st.success("Dataset cleaning completed!")

        except Exception as error:

            st.error(f"Cleaning failed: {error}")

    if "cleaned_df" in st.session_state:

        cleaned_df = st.session_state["cleaned_df"]

        st.subheader("Cleaning Report")

        st.write(
            st.session_state["cleaning_report"]
        )

        st.subheader("Cleaned Dataset Preview")

        st.dataframe(
            cleaned_df,
            use_container_width=True
        )

        st.download_button(
            "Download Cleaned CSV",
            cleaned_df.to_csv(index=False).encode("utf-8"),
            "cleaned_dataset.csv",
            "text/csv"
        )

        st.metric(
            "Remaining Missing Values",
            int(cleaned_df.isna().sum().sum())
        )

        st.metric(
            "Remaining Duplicate Rows",
            int(cleaned_df.duplicated().sum())
        )

# ==========================================
# 14. DATA MANIPULATION
# ==========================================

elif page == "Data Manipulation":

    st.header("⚙️ Data Manipulation Workspace")

    operation = st.selectbox(
        "Select Operation",
        [
            "Filter Data",
            "Sort Data",
            "Rename Column",
            "Create Calculated Column"
        ]
    )

    result_df = df.copy()

    if operation == "Filter Data":

        column = st.selectbox(
            "Select Column",
            df.columns.tolist()
        )

        condition = st.selectbox(
            "Condition",
            [
                "equals",
                "not_equals",
                "greater_than",
                "less_than",
                "greater_equal",
                "less_equal"
            ]
        )

        value = st.text_input("Enter Value")

        if st.button("Apply Filter"):

            try:

                result_df = filter_data(
                    df,
                    column,
                    condition,
                    value
                )

                st.session_state["manipulated_df"] = result_df

            except Exception as error:

                st.error(str(error))

    elif operation == "Sort Data":

        column = st.selectbox(
            "Sort Column",
            df.columns.tolist()
        )

        ascending = st.checkbox(
            "Ascending Order",
            value=True
        )

        if st.button("Sort Dataset"):

            result_df = sort_data(
                df,
                column,
                ascending
            )

            st.session_state["manipulated_df"] = result_df

    elif operation == "Rename Column":

        column = st.selectbox(
            "Existing Column",
            df.columns.tolist()
        )

        new_name = st.text_input("New Column Name")

        if st.button("Rename Column"):

            try:

                result_df = rename_columns(
                    df,
                    {column: new_name}
                )

                st.session_state["manipulated_df"] = result_df

            except Exception as error:

                st.error(str(error))

    elif operation == "Create Calculated Column":

        numeric_columns = df.select_dtypes(
            include="number"
        ).columns.tolist()

        numeric_columns = [
            column
            for column in numeric_columns
            if column not in roles.get("identifier", [])
        ]

        if numeric_columns:

            col1 = st.selectbox(
                "First Numeric Column",
                numeric_columns
            )

            calculation = st.selectbox(
                "Operation",
                [
                    "add",
                    "subtract",
                    "multiply",
                    "divide",
                    "add_constant",
                    "multiply_constant"
                ]
            )

            if calculation in [
                "add_constant",
                "multiply_constant"
            ]:

                constant = st.number_input(
                    "Enter Constant",
                    value=0.0
                )

                if st.button("Create Calculated Column"):

                    result_df = create_calculated_column(
                        df,
                        "Calculated_Value",
                        col1,
                        calculation,
                        constant=constant
                    )

                    st.session_state["manipulated_df"] = result_df

            elif len(numeric_columns) >= 2:

                col2 = st.selectbox(
                    "Second Numeric Column",
                    [
                        column
                        for column in numeric_columns
                        if column != col1
                    ]
                )

                if st.button("Create Calculated Column"):

                    result_df = create_calculated_column(
                        df,
                        "Calculated_Value",
                        col1,
                        calculation,
                        column2=col2
                    )

                    st.session_state["manipulated_df"] = result_df

        else:

            st.warning("No numeric measure columns found.")

    if "manipulated_df" in st.session_state:

        st.subheader("Manipulated Dataset")

        result_df = st.session_state["manipulated_df"]

        st.dataframe(
            result_df,
            use_container_width=True
        )

        st.download_button(
            "Download Manipulated CSV",
            result_df.to_csv(index=False).encode("utf-8"),
            "manipulated_dataset.csv",
            "text/csv"
        )

# ==========================================
# 15. AGGREGATION
# ==========================================

elif page == "Aggregation":

    st.header("📊 Aggregation Engine")

    category_columns = (
        roles.get("category", [])
        + roles.get("text", [])
    )

    numeric_columns = [
        column
        for column in df.select_dtypes(include="number").columns
        if column not in roles.get("identifier", [])
    ]

    if category_columns and numeric_columns:

        group_columns = st.multiselect(
            "Group By Columns",
            category_columns
        )

        value_columns = st.multiselect(
            "Numeric Measure Columns",
            numeric_columns
        )

        aggregation = st.selectbox(
            "Aggregation Function",
            [
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
        )

        if st.button("Run Aggregation", type="primary"):

            try:

                if not group_columns or not value_columns:

                    st.warning(
                        "Select at least one group column "
                        "and one measure column."
                    )

                else:

                    result = aggregate_data(
                        df,
                        group_columns,
                        value_columns,
                        aggregation
                    )

                    st.subheader("Aggregation Results")

                    st.dataframe(
                        result,
                        use_container_width=True
                    )

                    st.download_button(
                        "Download Aggregation CSV",
                        result.to_csv(index=False).encode("utf-8"),
                        "aggregation_results.csv",
                        "text/csv"
                    )

            except Exception as error:

                st.error(f"Aggregation failed: {error}")

    else:

        st.warning(
            "This dataset needs category and numeric measure columns."
        )

# ==========================================
# 16. STATISTICAL ANALYSIS
# ==========================================

elif page == "Statistical Analysis":

    st.header("📈 Statistical Analysis")

    try:

        result = calculate_statistics(df)

        st.subheader("Descriptive Statistics")

        if not result["summary"].empty:

            st.dataframe(
                result["summary"],
                use_container_width=True
            )

        else:

            st.info(result["message"])

        st.subheader("Correlation Matrix")

        if not result["correlation"].empty:

            st.dataframe(
                result["correlation"],
                use_container_width=True
            )

        else:

            st.info("Correlation analysis is not available.")

    except Exception as error:

        st.error(f"Statistical analysis failed: {error}")

# ==========================================
# 17. SQL ANALYSIS
# ==========================================

elif page == "SQL Analysis":

    st.header("🗃️ SQL Analysis Workspace")

    st.info(
        "Your uploaded dataset is available as the SQL table "
        "`uploaded_data`."
    )

    st.code(
        "SELECT * FROM uploaded_data LIMIT 10",
        language="sql"
    )

    query = st.text_area(
        "Write your SQL query",
        value="SELECT * FROM uploaded_data LIMIT 10",
        height=150
    )

    if st.button("Execute SQL", type="primary"):

        try:

            result = execute_sql_query(
                df,
                query
            )

            st.success(result["message"])

            st.dataframe(
                result["data"],
                use_container_width=True
            )

            st.caption(
                f"Rows returned: {result['rows_returned']}"
            )

            st.download_button(
                "Download SQL Results",
                result["data"].to_csv(index=False).encode("utf-8"),
                "sql_results.csv",
                "text/csv"
            )

        except Exception as error:

            st.error(str(error))

# ==========================================
# 18. VISUALIZATION STUDIO
# ==========================================

elif page == "ML Predictions":

    st.title("Machine Learning Predictions")
    st.write(
        "Train machine learning models and predict outcomes "
        "using your uploaded dataset."
    )

    # Select prediction target
    target = st.selectbox(
        "Select the column you want to predict",
        df.columns
    )

    task_type = st.selectbox(
        "Prediction type",
        ["auto", "classification", "regression"]
    )

    if st.button("Train Machine Learning Model"):
        try:
            with st.spinner("Training your ML model..."):

                result = train_prediction_model(
                    df,
                    target=target,
                    task_type=task_type
                )

                st.session_state["ml_model_bundle"] = (
                    result["model_bundle"]
                )

                st.session_state["ml_result"] = result

            st.success("Model trained successfully!")

        except Exception as error:
            st.error(f"Model training failed: {error}")

    # Display results after training
    if "ml_result" in st.session_state:

        result = st.session_state["ml_result"]

        st.subheader("Model Performance")

       
        metrics = result.get("metrics", {})
        prediction_task = result.get("task_type", "classification")

        if prediction_task == "classification":
            cols = st.columns(4)
            cols[0].metric("Accuracy", f"{metrics.get('accuracy', 0):.2%}")
            cols[1].metric("Precision", f"{metrics.get('precision_weighted', 0):.2%}")
            cols[2].metric("Recall", f"{metrics.get('recall_weighted', 0):.2%}")
            cols[3].metric("F1 Score", f"{metrics.get('f1_weighted', 0):.2%}")

        elif prediction_task == "regression":
            cols = st.columns(3)
            mae_value = metrics.get("MAE", metrics.get("mae"))
            rmse_value = metrics.get("RMSE", metrics.get("rmse"))
            r2_value = metrics.get("R2", metrics.get("r2"))

            if mae_value is not None:
                cols[0].metric("MAE", f"{mae_value:.3f}")
            if rmse_value is not None:
                cols[1].metric("RMSE", f"{rmse_value:.3f}")
            if r2_value is not None:
                cols[2].metric("R² Score", f"{r2_value:.3f}")

        else:
            st.warning(f"Unknown prediction task: {prediction_task}")

        st.write("**Prediction task:**", prediction_task)
        training_rows = result.get("training_rows")
        testing_rows = result.get("testing_rows")
        if training_rows is not None:
            st.write(f"**Training records:** {training_rows:,}")
        if testing_rows is not None:
            st.write(f"**Testing records:** {testing_rows:,}")


        st.divider()

        st.subheader("Feature Importance")

        importance = result["feature_importance"]

        fig = px.bar(
            importance.head(15),
            x="Importance",
            y="Feature",
            orientation="h",
            title="Most Important Features"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Actual vs Predicted")

        predictions = result["prediction_results"]

        st.dataframe(predictions, use_container_width=True)

        csv = predictions.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Prediction Results",
            data=csv,
            file_name="ml_predictions.csv",
            mime="text/csv"
        )

        st.divider()

        st.subheader("Predict New Records")

        new_file = st.file_uploader(
            "Upload a CSV containing new records",
            type=["csv"],
            key="new_prediction_file"
        )

        if new_file is not None:

            new_data = pd.read_csv(new_file)

            st.write("New records preview")
            st.dataframe(new_data.head())

            if st.button("Predict New Records"):

                try:
                    bundle = st.session_state["ml_model_bundle"]

                    predicted_data = predict_new_data(
                        bundle,
                        new_data
                    )

                    st.success("Predictions generated!")

                    st.dataframe(
                        predicted_data,
                        use_container_width=True
                    )

                    st.download_button(
                        "Download New Predictions",
                        data=predicted_data.to_csv(
                            index=False
                        ).encode("utf-8"),
                        file_name="new_predictions.csv",
                        mime="text/csv"
                    )

                except Exception as error:
                    st.error(f"Prediction failed: {error}")

elif page == "Visualizations":

    st.header("📊 Interactive Visualization Studio")

    try:

        options = get_visualization_options(df)

        chart_type = st.selectbox(
            "Select Visualization",
            [
                "Bar Chart",
                "Histogram",
                "Line Chart",
                "Scatter Plot",
                "Pie Chart",
                "Correlation Heatmap",
                "Automatic Recommendations"
            ]
        )

        fig = None

        if chart_type == "Bar Chart":

            if options["category_columns"] and options["numeric_columns"]:

                category = st.selectbox(
                    "Category Column",
                    options["category_columns"]
                )

                measure = st.selectbox(
                    "Numeric Measure",
                    options["numeric_columns"]
                )

                aggregation = st.selectbox(
                    "Aggregation",
                    ["sum", "mean", "median", "count"]
                )

                fig = create_bar_chart(
                    df,
                    category,
                    measure,
                    aggregation
                )

            else:

                st.warning("Suitable columns are not available.")

        elif chart_type == "Histogram":

            if options["numeric_columns"]:

                column = st.selectbox(
                    "Numeric Column",
                    options["numeric_columns"]
                )

                fig = create_histogram(df, column)

            else:

                st.warning("No numeric measure columns found.")

        elif chart_type == "Line Chart":

            if options["date_columns"] and options["numeric_columns"]:

                date_column = st.selectbox(
                    "Date Column",
                    options["date_columns"]
                )

                value_column = st.selectbox(
                    "Numeric Column",
                    options["numeric_columns"]
                )

                fig = create_line_chart(
                    df,
                    date_column,
                    value_column
                )

            else:

                st.warning(
                    "Date and numeric measure columns are required."
                )

        elif chart_type == "Scatter Plot":

            if len(options["numeric_columns"]) >= 2:

                x = st.selectbox(
                    "X Axis",
                    options["numeric_columns"]
                )

                y = st.selectbox(
                    "Y Axis",
                    [
                        column
                        for column in options["numeric_columns"]
                        if column != x
                    ]
                )

                fig = create_scatter_chart(
                    df,
                    x,
                    y
                )

            else:

                st.warning(
                    "At least two numeric measure columns are required."
                )

        elif chart_type == "Pie Chart":

            if options["category_columns"]:

                category = st.selectbox(
                    "Category Column",
                    options["category_columns"]
                )

                fig = create_pie_chart(
                    df,
                    category
                )

            else:

                st.warning("No category columns found.")

        elif chart_type == "Correlation Heatmap":

            if len(options["numeric_columns"]) >= 2:

                fig = create_correlation_heatmap(df)

            else:

                st.warning(
                    "At least two numeric measure columns are required."
                )

        elif chart_type == "Automatic Recommendations":

            recommendations = generate_auto_charts(df)

            if recommendations:

                for recommendation in recommendations:

                    st.write(
                        f"**{recommendation['type'].title()}** — "
                        f"{recommendation['title']}"
                    )

            else:

                st.info("No automatic charts are available.")

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    except Exception as error:

        st.error(f"Visualization failed: {error}")

# ==========================================
# 19. AI BUSINESS INSIGHTS
# ==========================================

elif page == "AI Business Insights":

    st.header("🤖 Automated Business Insights")

    st.write(
        "Generate analytical findings using Python-based "
        "business intelligence."
    )

    if st.button(
        "Generate Business Insights",
        type="primary"
    ):

        try:

            if is_business_dataset:

                insights = generate_business_insights(df)

                for index, insight in enumerate(
                    insights,
                    start=1
                ):

                    st.info(
                        f"**Insight {index}:** {insight}"
                    )

            else:

                stats = calculate_statistics(df)

                st.subheader("Automatic Dataset Insights")

                st.write(
                    f"Your dataset contains {len(df):,} rows "
                    f"and {len(df.columns)} columns."
                )

                st.write(
                    f"Missing cells: {int(df.isna().sum().sum())}"
                )

                st.write(
                    f"Duplicate records: {int(df.duplicated().sum())}"
                )

                if not stats["summary"].empty:

                    st.write("Numeric measure summary:")

                    st.dataframe(
                        stats["summary"],
                        use_container_width=True
                    )

        except Exception as error:

            st.error(f"Insight generation failed: {error}")

# ==========================================
# 20. AI BUSINESS ANALYST + VOICE ASSISTANT
# ==========================================

elif page == "AI Business Analyst":

    st.header("🤖 BizAnalyst AI Agent")
    st.write("Ask questions about any uploaded dataset using local Ollama AI.")
    st.caption("Text and bilingual voice assistant | English and Hindi | Local processing")

    try:
        with st.spinner("Preparing dataset summary (cached for repeated questions)..."):
            business_context = get_cached_business_context(df)
    except Exception as error:
        business_context = None
        st.warning(f"Dataset context could not be prepared: {error}")

    st.subheader("💬 Ask by Text")
    examples = [
        "Summarize this dataset in simple words.",
        "Which numeric column has the highest average?",
        "What are the most important patterns in this dataset?",
        "Are there missing values or unusual records?",
        "Give me three practical recommendations based on this data."
    ]
    with st.expander("Example questions", expanded=False):
        for index, example in enumerate(examples):
            if st.button(example, key=f"agent_example_{index}"):
                st.session_state["agent_question"] = example

    question = st.text_area(
        "Ask your AI Business Analyst",
        key="agent_question",
        placeholder="Example: What are the key findings in this dataset?",
        height=90
    )

    if st.button("Ask Business AI", type="primary", key="ask_business_ai"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Ollama is generating a concise answer..."):
                answer = ask_business_agent(df, question, context=business_context)
            st.session_state["business_agent_answer"] = answer
            st.session_state["business_agent_answer_language"] = (
                "Hindi" if any("\u0900" <= ch <= "\u097f" for ch in answer) else "English"
                
            )

    if st.session_state.get("business_agent_answer"):
        st.subheader("AI Analyst Response")
        st.markdown(st.session_state["business_agent_answer"])

        speak_text_answer = st.checkbox("Speak this answer aloud", key="speak_text_answer")
        if speak_text_answer and st.button("Generate Speech", key="speak_text_answer_button"):
            try:
                spoken_language = st.session_state.get("business_agent_answer_language", "English")
                with st.spinner("Creating speech with your system voice..."):
                    speech_bytes = text_to_speech(
                        st.session_state["business_agent_answer"],
                        language=spoken_language
                    )
                st.audio(speech_bytes, format="audio/wav")
            except Exception as error:
                st.warning(f"Text-to-speech unavailable: {error}")

    st.divider()
    st.subheader("🎙️ Two-Way Voice Assistant")
    st.write("Record a question in English or Hindi. The agent transcribes it, analyzes your dataset, and can speak the answer.")

    voice_language = st.selectbox(
        "Speech recognition language",
        ["Auto detect", "English", "Hindi"],
        key="voice_input_language"
    )
    voice_audio = None
    if hasattr(st, "audio_input"):
        voice_audio = st.audio_input("Record your question", key="bizanalyst_voice_input")
    else:
        voice_audio = st.file_uploader(
            "Upload a voice recording (WAV, MP3, M4A, or WebM)",
            type=["wav", "mp3", "m4a", "webm", "ogg"],
            key="bizanalyst_voice_upload"
        )

    if voice_audio is not None:
        st.audio(voice_audio)

    if st.button("Process Voice Question", type="primary", key="process_voice_question"):
        if voice_audio is None:
            st.warning("Please record or upload your voice question first.")
        else:
            try:
                with st.spinner("1/3 Converting speech to text..."):
                    transcript = transcribe_audio(voice_audio, language=voice_language)
                st.session_state["voice_transcript"] = transcript

                with st.spinner("2/3 Asking the local Business AI..."):
                    voice_answer = ask_business_agent(
                        df,
                        transcript,
                        context=business_context
                    )
                st.session_state["voice_answer"] = voice_answer

                answer_language = "Hindi" if (
                    voice_language == "Hindi"
                    or (voice_language == "Auto detect" and any("\u0900" <= ch <= "\u097f" for ch in transcript))
                ) else "English"
                st.session_state["voice_answer_language"] = answer_language
                st.success("Voice question processed successfully.")
            except Exception as error:
                st.error(f"Voice assistant error: {error}")

    if st.session_state.get("voice_transcript"):
        st.markdown("**Recognized question:**")
        st.info(st.session_state["voice_transcript"])

    if st.session_state.get("voice_answer"):
        st.markdown("**Business AI response:**")
        st.markdown(st.session_state["voice_answer"])

        if st.button("🔊 Speak Voice Answer", key="speak_voice_answer"):
            try:
                with st.spinner("Generating spoken answer..."):
                    speech_bytes = text_to_speech(
                        st.session_state["voice_answer"],
                        language=st.session_state.get("voice_answer_language", "English")
                    )
                st.audio(speech_bytes, format="audio/wav")
            except Exception as error:
                st.warning(
                    "Could not generate speech. Check whether a suitable English/Hindi "
                    f"Windows voice is installed. Details: {error}"
                )

    with st.expander("Voice engine status"):
        try:
            status = get_voice_status()
            st.write(f"Speech recognition: {status['speech_to_text']}")
            st.write(f"Speech output: {status['text_to_speech']}")
            st.write(f"Installed system voices: {status['voice_count']}")
            st.write(f"Hindi voice detected: {'Yes' if status['hindi_voice_available'] else 'No'}")
            st.write(f"English voice detected: {'Yes' if status['english_voice_available'] else 'No'}")
            if not status["hindi_voice_available"]:
                st.caption("Hindi speech recognition can still work. Hindi spoken output requires a Hindi voice installed in Windows.")
        except Exception as error:
            st.caption(f"Voice status unavailable: {error}")

# ==========================================
# 21. LEGACY SALES ANALYSIS
# ==========================================

elif page == "Sales Analysis":

    st.header("📈 Monthly Sales Analysis")

    monthly = monthly_sales_analysis(df)

    col1, col2 = st.columns(2)

    with col1:

        fig = px.line(
            monthly,
            x="order_date",
            y="revenue",
            markers=True,
            title="Monthly Revenue"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.bar(
            monthly,
            x="order_date",
            y="profit",
            title="Monthly Profit"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.dataframe(
        monthly,
        use_container_width=True
    )

# ==========================================
# 22. LEGACY REGIONAL ANALYSIS
# ==========================================

elif page == "Regional Analysis":

    st.header("🌍 Regional Performance")

    regional = regional_analysis(df)

    fig = px.bar(
        regional,
        x="region",
        y="revenue",
        color="profit",
        title="Revenue by Region"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        regional,
        use_container_width=True
    )

# ==========================================
# 23. LEGACY PRODUCT ANALYSIS
# ==========================================

elif page == "Product Analysis":

    st.header("🏆 Product Performance")

    category = category_analysis(df)

    fig = px.pie(
        category,
        names="category",
        values="revenue",
        title="Revenue by Category"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    products = top_products_analysis(
        df,
        limit=10
    )

    fig = px.bar(
        products,
        x="profit",
        y="product_name",
        orientation="h",
        title="Top Profitable Products"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        products,
        use_container_width=True
    )

# ==========================================
# 24. LEGACY DISCOUNT ANALYSIS
# ==========================================

elif page == "Discount Analysis":

    st.header("💰 Discount Analysis")

    discounts = discount_analysis(df)

    fig = px.scatter(
        discounts,
        x="discount",
        y="average_profit",
        size="total_revenue",
        title="Discount vs Average Profit"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        discounts,
        use_container_width=True
    )

# ==========================================
# 25. LEGACY CUSTOMER ANALYTICS
# ==========================================

elif page == "Customer Analytics":

    st.header("👥 Customer Intelligence Dashboard")

    try:

        rfm = create_rfm(df)

        rfm_segmented, cluster_summary = segment_customers(
            rfm,
            n_clusters=4
        )

        summary = get_customer_summary(rfm_segmented)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Customers",
            summary["total_customers"]
        )

        c2.metric(
            "Champions",
            summary["champions"]
        )

        c3.metric(
            "Loyal Customers",
            summary["loyal_customers"]
        )

        c4.metric(
            "At Risk",
            summary["at_risk"]
        )

        st.subheader("Customer Segments")

        segment_counts = (
            rfm_segmented["segment"]
            .value_counts()
            .reset_index()
        )

        segment_counts.columns = [
            "Segment",
            "Customers"
        ]

        fig = px.pie(
            segment_counts,
            names="Segment",
            values="Customers",
            hole=0.45
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("Customer Value Analysis")

        fig = px.scatter(
            rfm_segmented,
            x="frequency",
            y="monetary",
            color="segment",
            hover_data=["customer_id", "recency"]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("Customer Details")

        st.dataframe(
            rfm_segmented,
            use_container_width=True
        )

        st.download_button(
            "Download Customer Segmentation",
            rfm_segmented.to_csv(index=False).encode("utf-8"),
            "customer_segmentation.csv",
            "text/csv"
        )

    except Exception as error:

        st.error(f"Customer analysis failed: {error}")

# ==========================================
# 26. EXPORT DATA
# ==========================================

# ==========================================
# 26. EXPORT DATA + POWER BI EXPORT
# ==========================================

elif page == "Export Data":

    st.header("📥 Export Center")

    st.write(
        "Download your original or cleaned dataset "
        "in CSV, Excel and Power BI formats."
    )

    # ==========================================
    # SELECT DATASET
    # ==========================================

    export_choice = st.radio(
        "Select Dataset",
        ["Original Dataset", "Cleaned Dataset"],
        key="export_dataset_choice"
    )

    if export_choice == "Cleaned Dataset":

        if "cleaned_df" in st.session_state:

            export_df = st.session_state["cleaned_df"]

        else:

            st.warning(
                "Clean the dataset first using the Data Cleaning page."
            )

            export_df = None

    else:

        export_df = original_df

    # ==========================================
    # EXPORT OPTIONS
    # ==========================================

    if export_df is not None and not export_df.empty:

        st.divider()

        st.subheader("📁 Standard Data Export")

        # CSV EXPORT
        st.write("### Export CSV")

        csv_bytes = export_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="📥 Download CSV",
            data=csv_bytes,
            file_name="bizanalyst_dataset.csv",
            mime="text/csv",
            key="download_standard_csv",
            width="stretch"
        )

        # EXCEL EXPORT
        st.write("### Export Excel")

        try:

            excel_buffer = io.BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl"
            ) as writer:

                export_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Dataset"
                )

            st.download_button(
                label="📥 Download Excel",
                data=excel_buffer.getvalue(),
                file_name="bizanalyst_dataset.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_standard_excel",
                width="stretch"
            )

        except Exception as error:

            st.error(f"Excel export failed: {error}")

        # ==========================================
        # POWER BI EXPORT CENTER
        # ==========================================

        st.divider()

        st.subheader("📊 Power BI Export Center")

        st.write(
            "Prepare your dataset for Microsoft Power BI Desktop."
        )

        try:

            export_info = get_powerbi_export_info(export_df)

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total Rows",
                f"{export_info['total_rows']:,}"
            )

            col2.metric(
                "Total Columns",
                export_info["total_columns"]
            )

            col3.metric(
                "Missing Values",
                export_info["missing_values"]
            )

            col4.metric(
                "Duplicate Rows",
                export_info["duplicate_rows"]
            )

            with st.expander("Preview Power BI columns"):

                st.write(export_info["columns"])

                st.write(
                    f"Memory usage: "
                    f"{export_info['memory_usage_mb']} MB"
                )

            powerbi_col1, powerbi_col2 = st.columns(2)

            # POWER BI CSV
            with powerbi_col1:

                powerbi_csv = export_powerbi_csv(export_df)

                st.download_button(
                    label="📥 Download Power BI CSV",
                    data=powerbi_csv,
                    file_name="bizanalyst_powerbi_data.csv",
                    mime="text/csv",
                    key="download_powerbi_csv",
                    width="stretch"
                )

            # POWER BI EXCEL
            with powerbi_col2:

                powerbi_excel = export_powerbi_excel(export_df)

                st.download_button(
                    label="📥 Download Power BI Excel",
                    data=powerbi_excel,
                    file_name="bizanalyst_powerbi_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_powerbi_excel",
                    width="stretch"
                )

            st.success(
                "Your dataset is ready for Power BI import!"
            )

        except Exception as error:

            st.error(
                f"Power BI export failed: {error}"
            )

    elif export_df is not None:

        st.warning("The selected dataset is empty.")

# ==========================================
# 27. FOOTER
# ==========================================

st.sidebar.divider()

st.sidebar.caption(
    "BizAnalyst AI | Universal Analytics Platform"
)

st.sidebar.caption(
    "Python | Pandas | Plotly | Streamlit | SQLite | Ollama"
)

st.divider()

st.caption(
    "BizAnalyst AI — Intelligent Data Analytics Platform"
)
