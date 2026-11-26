
import pandas as pd

from powerbi.powerbi_export import (
    export_powerbi_csv,
    export_powerbi_excel,
    get_powerbi_export_info
)

df = pd.DataFrame({
    "Employee": ["Rahul", "Priya", "Amit", "Neha"],
    "Department": ["IT", "HR", "IT", "Sales"],
    "Salary": [30000, 45000, 35000, 50000],
    "Age": [22, 25, 28, 30]
})

print("\n===== POWER BI EXPORT TEST =====")

print("\nDATASET INFORMATION:")
print(get_powerbi_export_info(df))

csv_data = export_powerbi_csv(df)

with open("powerbi_export.csv", "wb") as file:
    file.write(csv_data)

print("\nCSV EXPORT: SUCCESS")

excel_data = export_powerbi_excel(df)

with open("powerbi_export.xlsx", "wb") as file:
    file.write(excel_data)

print("EXCEL EXPORT: SUCCESS")

print("\nALL POWER BI EXPORT TESTS COMPLETED!")