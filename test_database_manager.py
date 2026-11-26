
from database.db_manager import DatabaseManager

db = DatabaseManager()

print("\n===== DATABASE MANAGER TEST =====")

users = db.get_all_users()

for user in users:
    print(user.to_dict())

print("\nTotal users:", len(users))

admin = db.get_user("singhravishekh09@gmail.com")

if admin:
    print("\nAdmin found!")
    print("Name:", admin.name)
    print("Role:", admin.role)
else:
    print("\nAdmin not found.")