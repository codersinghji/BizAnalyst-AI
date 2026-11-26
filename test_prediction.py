
import pandas as pd

from analytics.prediction_engine import (
    train_prediction_model,
    predict_new_data
)

# Example employee dataset
df = pd.DataFrame({
    "Employee_ID": range(1, 21),
    "Age": [22, 25, 28, 30, 35, 40, 24, 27, 32, 38,
            23, 29, 34, 41, 26, 31, 36, 39, 28, 33],
    "Department": [
        "IT", "HR", "IT", "Sales", "HR",
        "IT", "Sales", "HR", "IT", "Sales",
        "IT", "HR", "Sales", "IT", "HR",
        "Sales", "IT", "HR", "Sales", "IT"
    ],
    "Salary": [
        30000, 35000, 45000, 40000, 50000,
        60000, 32000, 38000, 55000, 62000,
        33000, 42000, 48000, 65000, 37000,
        52000, 58000, 39000, 49000, 61000
    ],
    "Experience": [
        1, 2, 4, 3, 7, 10, 1, 3, 6, 9,
        2, 4, 6, 11, 2, 5, 8, 3, 5, 9
    ],
    "Attrition": [
        "Yes", "No", "No", "Yes", "No",
        "No", "Yes", "No", "No", "No",
        "Yes", "No", "Yes", "No", "No",
        "No", "No", "Yes", "No", "No"
    ]
})

result = train_prediction_model(
    df,
    target="Attrition",
    task_type="auto"
)

print("\nPREDICTION TYPE")
print(result["task_type"])

print("\nMODEL METRICS")
print(result["metrics"])

print("\nFEATURE IMPORTANCE")
print(result["feature_importance"])

print("\nPREDICTION RESULTS")
print(result["prediction_results"])

# Predict an example new employee
new_employee = pd.DataFrame({
    "Age": [26],
    "Department": ["IT"],
    "Salary": [35000],
    "Experience": [2]
})

predictions = predict_new_data(
    result["model_bundle"],
    new_employee
)

print("\nNEW EMPLOYEE PREDICTION")
print(predictions)