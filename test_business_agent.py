
import pandas as pd

from analytics.business_insights import generate_business_insights
from agents.business_analyst_agent import (
    prepare_business_context,
    ask_business_agent
)

# Employee dataset test
df = pd.DataFrame({
    "Employee_ID": [101, 102, 103, 104, 105, 106],
    "Department": ["IT", "HR", "IT", "Sales", "HR", "Sales"],
    "Age": [25, 30, 28, 35, 27, 32],
    "Salary": [30000, 45000, 40000, 50000, 35000, 48000],
    "Experience": [2, 5, 3, 8, 2, 6]
})

print("\n========== AUTOMATIC INSIGHTS ==========")

for insight in generate_business_insights(df):
    print("-", insight)

print("\n========== BUSINESS CONTEXT ==========")

context = prepare_business_context(df)

print(context)

print("\n========== OLLAMA AI RESPONSE ==========")

answer = ask_business_agent(
    df,
    "Which department has the highest average salary? "
    "Explain the findings and give recommendations."
)

print(answer)