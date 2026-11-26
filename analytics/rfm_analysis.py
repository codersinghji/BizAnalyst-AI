
import pandas as pd
import numpy as np

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def create_rfm(df):

    data = df.copy()

    required = [
        "customer_id",
        "order_id",
        "order_date",
        "sales"
    ]

    missing = [
        col for col in required
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    data["order_date"] = pd.to_datetime(
        data["order_date"],
        errors="coerce"
    )

    data["sales"] = pd.to_numeric(
        data["sales"],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "customer_id",
            "order_id",
            "order_date",
            "sales"
        ]
    )

    if data.empty:
        raise ValueError("No valid customer transactions found.")

    # Reference date: one day after the latest transaction
    reference_date = (
        data["order_date"].max()
        + pd.Timedelta(days=1)
    )

    # Calculate RFM metrics
    rfm = data.groupby("customer_id").agg(
        recency=(
            "order_date",
            lambda x: (reference_date - x.max()).days
        ),
        frequency=(
            "order_id",
            "nunique"
        ),
        monetary=(
            "sales",
            "sum"
        )
    ).reset_index()

    return rfm

def segment_customers(rfm, n_clusters=4):

    result = rfm.copy()

    if len(result) < 2:
        raise ValueError(
            "At least 2 customers are required for clustering."
        )

    # Use log transformation for highly skewed monetary values
    features = result[
        ["recency", "frequency", "monetary"]
    ].copy()

    features["monetary"] = np.log1p(
        features["monetary"].clip(lower=0)
    )

    # Standardize features before K-Means
    scaler = StandardScaler()

    scaled_features = scaler.fit_transform(features)

    # Use fewer clusters if the dataset has fewer customers
    clusters = min(n_clusters, len(result))

    model = KMeans(
        n_clusters=clusters,
        random_state=42,
        n_init=10
    )

    result["cluster"] = model.fit_predict(
        scaled_features
    )

    # Calculate average RFM values for each cluster
    cluster_summary = result.groupby("cluster").agg(
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        customer_count=("customer_id", "count")
    )

    # Create a relative customer-value score.
    # Lower recency is better; higher frequency and
    # monetary value are better.
    cluster_summary["value_score"] = (
        cluster_summary["avg_frequency"].rank(pct=True)
        + cluster_summary["avg_monetary"].rank(pct=True)
        + (1 - cluster_summary["avg_recency"].rank(pct=True))
    )

    ordered_clusters = (
        cluster_summary["value_score"]
        .sort_values(ascending=False)
        .index.tolist()
    )

    segment_names = [
        "Champions",
        "Loyal Customers",
        "Potential Customers",
        "At Risk"
    ]

    segment_mapping = {}

    for i, cluster_id in enumerate(ordered_clusters):

        if i < len(segment_names):
            segment_mapping[cluster_id] = segment_names[i]
        else:
            segment_mapping[cluster_id] = f"Segment {i + 1}"

    result["segment"] = result["cluster"].map(
        segment_mapping
    )

    return result, cluster_summary

def get_customer_summary(rfm):

    return {
        "total_customers": int(
            rfm["customer_id"].nunique()
        ),
        "champions": int(
            (rfm["segment"] == "Champions").sum()
        ),
        "loyal_customers": int(
            (rfm["segment"] == "Loyal Customers").sum()
        ),
        "potential_customers": int(
            (rfm["segment"] == "Potential Customers").sum()
        ),
        "at_risk": int(
            (rfm["segment"] == "At Risk").sum()
        )
    }