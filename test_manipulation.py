
import pandas as pd

from analytics.data_manipulation import (
    select_columns,
    rename_columns,
    filter_data,
    sort_data,
    create_calculated_column,
    drop_columns,
    remove_duplicates
)

data = {
    "Employee_ID": [101, 102, 103, 104, 105],
    "Employee_Name": ["Rahul", "Priya", "Amit", "Neha", "Arjun"],
    "Department": ["IT", "HR", "IT", "Finance", "HR"],
    "Salary": [40000, 50000, 45000, 60000, 55000],
    "Bonus": [4000, 5000, 4500, 6000, 5500]
}

df = pd.DataFrame(data)

print("\nORIGINAL DATA")
print(df)

print("\n1. SELECT COLUMNS")
print(select_columns(df, ["Employee_Name", "Salary"]))

print("\n2. RENAME COLUMNS")
print(rename_columns(df, {
    "Employee_Name": "Name",
    "Salary": "Monthly_Salary"
}))

print("\n3. FILTER DATA")
print(filter_data(df, "Salary", "greater_than", 45000))

print("\n4. SORT DATA")
print(sort_data(df, "Salary", ascending=False))

print("\n5. CREATE CALCULATED COLUMN")
calculated = create_calculated_column(
    df,
    new_column="Total_Compensation",
    column1="Salary",
    operation="add",
    column2="Bonus"
)
print(calculated)

print("\n6. DROP COLUMN")
print(drop_columns(df, ["Bonus"]))

print("\n7. REMOVE DUPLICATES")
print(remove_duplicates(df))

print("\nORIGINAL DATA REMAINS UNCHANGED")
print(df)
