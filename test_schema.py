
import pandas as pd
from analytics.schema_detector import detect_schema, get_schema_summary

# Example dataset: employee information
data = {
    "Employee_ID": [101, 102, 103, 104, 105],
    "Employee_Name": ["Rahul", "Priya", "Amit", "Neha", "Arjun"],
    "Department": ["IT", "HR", "IT", "Finance", "HR"],
    "Salary": [40000, 50000, 45000, 60000, 55000],
    "Joining_Date": [
        "2022-01-10",
        "2021-05-15",
        "2023-03-20",
        "2020-11-01",
        "2022-08-12"
    ]
}

df = pd.DataFrame(data)

# Detect schema
result = detect_schema(df)

print("\nDATASET SUMMARY")
print(result["dataset_summary"])

print("\nDETECTED ROLES")
print(result["detected_roles"])

print("\nFULL SCHEMA REPORT")
print(get_schema_summary(df))