
import pandas as pd

from analytics.data_profiling import generate_data_profile

data = {
    "Employee_ID": [101, 102, 103, 104, 105, 105],
    "Employee_Name": [
        "Rahul", "Priya", "Amit", "Neha", "Arjun", "Arjun"
    ],
    "Department": [
        "IT", "HR", "IT", "Finance", None, None
    ],
    "Salary": [40000, 50000, 45000, 60000, 55000, 55000],
    "Joining_Date": [
        "2022-01-10",
        "2021-05-15",
        "2023-03-20",
        "2020-11-01",
        "2022-08-12",
        "2022-08-12"
    ]
}

df = pd.DataFrame(data)

profile = generate_data_profile(df)

print("\nDATASET OVERVIEW")
print(profile["overview"])

print("\nMISSING VALUE REPORT")
print(profile["missing_report"])

print("\nNUMERIC SUMMARY")
print(profile["numeric_summary"])

print("\nCATEGORICAL SUMMARY")
print(profile["categorical_summary"])

print("\nOUTLIER REPORT")
print(profile["outlier_report"])