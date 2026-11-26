
import pandas as pd

from analytics.statistical_analysis import (
    calculate_statistics,
    calculate_column_statistics
)

data = {
    "Employee_ID": [101, 102, 103, 104, 105, 106],
    "Employee_Name": [
        "Rahul", "Priya", "Amit", "Neha", "Arjun", "Riya"
    ],
    "Department": [
        "IT", "HR", "IT", "Finance", "HR", "Finance"
    ],
    "Salary": [40000, 50000, 45000, 60000, 55000, 65000],
    "Bonus": [4000, 5000, 4500, 6000, 5500, 6500]
}

df = pd.DataFrame(data)

print("\n1. COMPLETE STATISTICAL ANALYSIS")

result = calculate_statistics(df)

print("\nSTATISTICAL SUMMARY")
print(result["summary"].to_string(index=False))

print("\nCORRELATION MATRIX")
print(result["correlation"])

print("\nSTATUS")
print(result["message"])

print("\n2. SALARY COLUMN STATISTICS")

salary_stats = calculate_column_statistics(df, "Salary")

print(salary_stats)