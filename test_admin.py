
from auth.auth_database import get_user_by_email

email = input("Enter admin email to verify: ").strip().lower()

user = get_user_by_email(email)

if user:
    print("\nADMIN ACCOUNT FOUND")
    print("Name:", user["name"])
    print("Email:", user["email"])
    print("Role:", user["role"])
    print("Active:", bool(user["is_active"]))
else:
    print("Admin account not found.")
