
import pandas as pd

from analytics.visualization_engine import (
    get_visualization_options,
    create_bar_chart,
    create_histogram,
    create_scatter_chart,
    create_pie_chart,
    create_correlation_heatmap,
    generate_auto_charts
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
    "Salary": [40000, 50000, 45000, 60000, 55000, 65000],
    "Bonus": [4000, 5000, 4500, 6000, 5500, 6500]
}

df = pd.DataFrame(data)

print("\n1. VISUALIZATION OPTIONS")
print(get_visualization_options(df))

print("\n2. BAR CHART")
fig = create_bar_chart(
    df, "Department", "Salary", "mean"
)
print("Bar chart created:", fig is not None)

print("\n3. HISTOGRAM")
fig = create_histogram(df, "Salary")
print("Histogram created:", fig is not None)

print("\n4. SCATTER CHART")
fig = create_scatter_chart(df, "Salary", "Bonus")
print("Scatter chart created:", fig is not None)

print("\n5. PIE CHART")
fig = create_pie_chart(df, "Department")
print("Pie chart created:", fig is not None)

print("\n6. CORRELATION HEATMAP")
fig = create_correlation_heatmap(df)
print("Heatmap created:", fig is not None)

print("\n7. AUTOMATIC CHART RECOMMENDATIONS")
charts = generate_auto_charts(df)

for chart in charts:
    print(chart)

print("\nVisualization tests completed.")