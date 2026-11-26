
import pandas as pd

from analytics.data_cleaning import clean_data, inspect_data

data = {
    "Employee_ID": [101, 102, 103, 104, 105, 105],
    "Employee_Name": [
        "Rahul", "Priya", "Amit", "Neha", "Arjun", "Arjun"
    ],
    "Department": [
        "IT", "HR", "IT", "Finance", None, None
    ],
    "Salary": [40000, 50000, None, 60000, 55000, 55000],
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

print("\nORIGINAL DATA")
print(inspect_data(df))

cleaned_df, report = clean_data(
    df,
    numeric_strategy="median",
    categorical_strategy="mode",
    remove_duplicates=True,
    date_columns=["Joining_Date"]
)

print("\nCLEANED DATA")
print(cleaned_df)

print("\nCLEANING REPORT")
print(report)

print("\nVERIFY ORIGINAL DATA IS UNCHANGED")
print(df)