
import pandas as pd

from agents.business_analyst_agent import (
    answer_with_python,
    ask_business_agent
)

# Temporary test dataset
df = pd.DataFrame({
    "Employee": ["Rahul", "Priya", "Amit", "Neha", "Arjun"],
    "Department": ["IT", "HR", "IT", "Sales", "HR"],
    "Salary": [30000, 45000, 35000, 50000, 40000],
    "Age": [22, 25, 28, 30, 26]
})

questions = [
    "How many rows and columns are in my dataset?",
    "What is the average salary?",
    "What is the total salary?",
    "What is the highest salary?",
    "What is the lowest salary?",
    "Which department has the highest salary?"
]

print("\n===== TESTING PYTHON ANALYTICS =====")

for question in questions:
    print("\nQUESTION:", question)

    answer = answer_with_python(df, question)

    if answer is None:
        answer = "Question requires AI analysis."

    print("ANSWER:", answer)

print("\n===== TESTING AGENT CONNECTION =====")

print(
    ask_business_agent(
        df,
        "How many rows and columns are in my dataset?"
    )
)