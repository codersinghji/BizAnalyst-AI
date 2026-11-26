
import pandas as pd

from analytics.aggregation_engine import (
    aggregate_data,
    aggregate_multiple,
    calculate_total
)

data = {
    "Employee_ID": [101, 102, 103, 104, 105, 106],
    "Employee_Name": [
        "Rahul", "Priya", "Amit", "Neha", "Arjun", "Riya"
    ],
    "Department": [
        "IT", "HR", "IT", "Finance", "HR", "Finance"
    ],
    "Salary": [
        40000, 50000, 45000, 60000, 55000, 65000
    ],
    "Bonus": [
        4000, 5000, 4500, 6000, 5500, 6500
    ]
}

df = pd.DataFrame(data)

print("\nORIGINAL DATA")
print(df)

print("\n1. AVERAGE SALARY BY DEPARTMENT")
print(
    aggregate_data(
        df,
        group_columns=["Department"],
        value_columns=["Salary"],
        aggregation="mean"
    )
)

print("\n2. TOTAL SALARY BY DEPARTMENT")
print(
    aggregate_data(
        df,
        group_columns=["Department"],
        value_columns=["Salary"],
        aggregation="sum"
    )
)

print("\n3. MULTIPLE AGGREGATIONS")
print(
    aggregate_multiple(
        df,
        group_columns=["Department"],
        value_columns=["Salary", "Bonus"],
        aggregations=["sum", "mean", "min", "max"]
    )
)

print("\n4. OVERALL AVERAGE SALARY")
print(calculate_total(df, "Salary", "mean"))

print("\n5. TOTAL BONUS")
print(calculate_total(df, "Bonus", "sum"))