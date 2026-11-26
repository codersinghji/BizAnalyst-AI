
from auth.auth_database import initialize_auth_database, DATABASE_PATH

initialize_auth_database()

print("Authentication database created successfully!")
print("Database location:", DATABASE_PATH)
