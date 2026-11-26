
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


MAX_TRAIN_ROWS = 50000


def optimize_dataframe_memory(df):
    """Reduce memory usage without changing the original DataFrame."""

    result = df.copy()

    for column in result.columns:

        if pd.api.types.is_integer_dtype(result[column]):
            result[column] = pd.to_numeric(
                result[column],
                downcast="integer"
            )

        elif pd.api.types.is_float_dtype(result[column]):
            result[column] = pd.to_numeric(
                result[column],
                downcast="float"
            )

    return result


def detect_prediction_type(series):

    if (
        pd.api.types.is_object_dtype(series)
        or isinstance(series.dtype, pd.CategoricalDtype)
        or pd.api.types.is_bool_dtype(series)
    ):
        return "classification"

    unique_count = series.nunique()

    if unique_count <= 10:
        return "classification"

    return "regression"



def prepare_features(df, target):

    if target not in df.columns:
        raise ValueError("Target column not found.")

    data = df.dropna(subset=[target]).copy()

    if len(data) < 20:
        raise ValueError("At least 20 valid rows are required.")

    y = data[target]
    X = data.drop(columns=[target])

    usable_columns = []

    for column in X.columns:

        # Exclude identifier columns
        column_name = str(column).lower().replace(" ", "_")

        identifier_names = [
            "id",
            "employee_id",
            "customer_id",
            "product_id",
            "order_id",
            "transaction_id",
            "record_id",
            "user_id"
        ]

        if (
            column_name in identifier_names
            or column_name.endswith("_id")
            or column_name.startswith("id_")
        ):
            continue

        # Exclude constant columns
        if X[column].nunique(dropna=True) <= 1:
            continue

        # Exclude datetime columns
        if pd.api.types.is_datetime64_any_dtype(X[column]):
            continue

        # Exclude high-cardinality text columns
        if (
            X[column].dtype == "object"
            or isinstance(X[column].dtype, pd.CategoricalDtype)
        ):

            unique_ratio = (
                X[column].nunique(dropna=True) / max(len(X), 1)
            )

            if unique_ratio > 0.80:
                continue

        usable_columns.append(column)

    X = X[usable_columns]

    if X.empty:
        raise ValueError("No usable feature columns found.")

    return X, y



def train_prediction_model(
    df,
    target,
    task_type="auto"
):

    df = optimize_dataframe_memory(df)

    X, y = prepare_features(df, target)

    if task_type == "auto":
        task_type = detect_prediction_type(y)

    if task_type not in ["classification", "regression"]:
        raise ValueError("Invalid prediction type.")

    if task_type == "classification" and y.nunique() < 2:
        raise ValueError("Classification requires at least two target classes.")

    # Use a representative sample for large datasets.
    if len(X) > MAX_TRAIN_ROWS:

        sample_df = pd.concat(
            [X, y.rename(target)],
            axis=1
        )

        if task_type == "classification":
            sample_df = (
                sample_df.groupby(
                    target,
                    group_keys=False,
                    observed=True
                )
                .apply(
                    lambda group: group.sample(
                        n=min(
                            len(group),
                            max(
                                2,
                                int(MAX_TRAIN_ROWS * len(group) / len(df))
                            )
                        ),
                        random_state=42
                    )
                )
            )

            sample_df = sample_df.sample(
                n=min(MAX_TRAIN_ROWS, len(sample_df)),
                random_state=42
            )

        else:
            sample_df = sample_df.sample(
                n=MAX_TRAIN_ROWS,
                random_state=42
            )

        X = sample_df.drop(columns=[target])
        y = sample_df[target]

    numeric_columns = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_columns = X.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    transformers = []

    if numeric_columns:

        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median"))
        ])

        transformers.append(
            ("numeric", numeric_pipeline, numeric_columns)
        )

    if categorical_columns:

        categorical_pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="most_frequent")
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    max_categories=50
                )
            )
        ])

        transformers.append(
            ("categorical", categorical_pipeline, categorical_columns)
        )

    if not transformers:
        raise ValueError("No supported numeric or categorical features.")

    preprocessor = ColumnTransformer(
        transformers=transformers
    )

    if task_type == "classification":

        class_counts = y.value_counts()

        stratify = (
            y
            if class_counts.min() >= 2
            and len(class_counts) * 2 <= len(y)
            else None
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=stratify
        )

        if y_train.nunique() < 2:
            raise ValueError(
                "Training data contains only one class. "
                "Upload more examples for each target class."
            )

        model = RandomForestClassifier(
            n_estimators=30,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=1,
            random_state=42
        )

    else:

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42
        )

        model = RandomForestRegressor(
            n_estimators=30,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=1,
            random_state=42
        )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    if task_type == "classification":

        metrics = {
            "accuracy": accuracy_score(y_test, predictions),
            "precision_weighted": precision_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0
            ),
            "recall_weighted": recall_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0
            ),
            "f1_weighted": f1_score(
                y_test,
                predictions,
                average="weighted",
                zero_division=0
            )
        }

    else:

        metrics = {
            "MAE": mean_absolute_error(y_test, predictions),
            "RMSE": np.sqrt(mean_squared_error(y_test, predictions)),
            "R2": r2_score(y_test, predictions)
        }

    try:

        feature_names = pipeline.named_steps[
            "preprocessor"
        ].get_feature_names_out()

        importances = pipeline.named_steps[
            "model"
        ].feature_importances_

        feature_importance = pd.DataFrame({
            "Feature": feature_names,
            "Importance": importances
        }).sort_values(
            "Importance",
            ascending=False
        )

    except Exception:

        feature_importance = pd.DataFrame(
            columns=["Feature", "Importance"]
        )

    results = pd.DataFrame({
        "Actual": y_test.to_numpy(),
        "Predicted": predictions
    })

    bundle = {
        "model": pipeline,
        "target": target,
        "task_type": task_type,
        "feature_columns": X.columns.tolist(),
        "metrics": metrics,
        "feature_importance": feature_importance
    }

    return {
        "model_bundle": bundle,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "prediction_results": results,
        "task_type": task_type
    }


def predict_new_data(model_bundle, new_data):

    model = model_bundle["model"]

    feature_columns = model_bundle["feature_columns"]

    missing_columns = [
        column
        for column in feature_columns
        if column not in new_data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    X = new_data[feature_columns].copy()

    predictions = model.predict(X)

    result = new_data.copy()

    result["AI_Prediction"] = predictions

    if model_bundle["task_type"] == "classification":

        probabilities = model.predict_proba(X)

        classes = model.named_steps["model"].classes_

        for index, class_name in enumerate(classes):

            result[
                f"Probability_{class_name}"
            ] = probabilities[:, index]

    return result


def get_model_information(model_bundle):

    return {
        "target": model_bundle["target"],
        "task_type": model_bundle["task_type"],
        "feature_columns": model_bundle["feature_columns"],
        "metrics": model_bundle["metrics"]
    }
