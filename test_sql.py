
import pandas as pd

from analytics.sql_analysis import (
    execute_sql_query,
    get_sql_table_info
)

data = {
    "Employee_ID": [101, 102, 103, 104, 105, 106],
    "Employee_Name": [
        "Rahul", "Priya", "Amit",
        "Neha", "Arjun", "Riya"
    ],
    "Department": [
        "IT", "HR", "IT",
        "Finance", "HR", "Finance"
    ],
    "Salary": [
        40000, 50000, 45000,
        60000, 55000, 65000
    ],
    "Bonus": [
        4000, 5000, 4500,
        6000, 5500, 6500
    ]
}

df = pd.DataFrame(data)

print("\n1. SQL TABLE STRUCTURE")
print(get_sql_table_info(df))

print("\n2. SELECT ALL EMPLOYEES")
result = execute_sql_query(
    df,
    "SELECT * FROM uploaded_data"
)
print(result["data"])

print("\n3. EMPLOYEES WITH SALARY ABOVE 50000")
result = execute_sql_query(
    df,
    """
    SELECT Employee_Name, Department, Salary
    FROM uploaded_data
    WHERE Salary > 50000
    ORDER BY Salary DESC
    """
)
print(result["data"])

print("\n4. AVERAGE SALARY BY DEPARTMENT")
result = execute_sql_query(
    df,
    """
    SELECT Department, AVG(Salary) AS Average_Salary
    FROM uploaded_data
    GROUP BY Department
    ORDER BY Average_Salary DESC
    """
)
print(result["data"])

print("\n5. TOTAL SALARY")
result = execute_sql_query(
    df,
    "SELECT SUM(Salary) AS Total_Salary FROM uploaded_data"
)
print(result["data"])

print("\n6. TEST INVALID QUERY")
try:
    execute_sql_query(df, "DELETE FROM uploaded_data")
except ValueError as error:
    print(error)