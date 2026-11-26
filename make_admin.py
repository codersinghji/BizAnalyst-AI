
from auth.auth_database import (
    initialize_auth_database,
    get_connection
)

initialize_auth_database()

print("\n===== BIZANALYST AI: ADMIN SETUP =====")

email = input("Enter your registered email address: ").strip().lower()

connection = get_connection()

try:
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, name, email, role FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()

    if not user:
        print("\nUser not found. Register this account first.")
    else:
        print("\nAccount found:")
        print("Name:", user["name"])
        print("Email:", user["email"])
        print("Current role:", user["role"])

        confirmation = input(
            "\nType MAKE ADMIN to promote this account: "
        ).strip()

        if confirmation == "MAKE ADMIN":
            cursor.execute(
                "UPDATE users SET role = 'Admin' WHERE email = ?",
                (email,)
            )
            connection.commit()
            print("\nSUCCESS: Admin role assigned!")
        else:
            print("\nCancelled. No changes made.")

finally:
    connection.close()
