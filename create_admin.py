
from getpass import getpass
from auth.auth_database import (
    initialize_auth_database,
    get_user_by_email,
    create_user
)
from auth.auth_service import hash_password


def create_admin():

    initialize_auth_database()

    print("\n===== BizAnalyst-AI Admin Setup =====")

    name = input("Enter admin name: ").strip()
    email = input("Enter admin email: ").strip().lower()

    if not name or not email:
        print("Name and email are required.")
        return

    if get_user_by_email(email):
        print("An account with this email already exists.")
        return

    # Visible input fallback for terminals where getpass does not work.
    print("\nEnter your password twice.")
    password = input("Create admin password: ")
    confirm_password = input("Confirm admin password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match. Please try again.")
        return

    password_hash = hash_password(password)

    create_user(
        name=name,
        email=email,
        password_hash=password_hash,
        role="Admin"
    )

    print("\nAdmin account created successfully!")
    print("Name:", name)
    print("Email:", email)
    print("Role: Admin")


if __name__ == "__main__":
    create_admin()
