
import sqlite3
from pathlib import Path

from auth.auth_database import (
    initialize_auth_database,
    get_connection
)

from database.model import User

class DatabaseManager:

    def __init__(self):
        initialize_auth_database()

    def get_user(self, email):
        """Find a user by email."""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE email = ?",
                (email.strip().lower(),)
            )

            row = cursor.fetchone()

            return User.from_database_row(row)

        finally:
            connection.close()

    def get_user_by_id(self, user_id):
        """Find a user by ID."""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )

            row = cursor.fetchone()

            return User.from_database_row(row)

        finally:
            connection.close()

    def get_all_users(self):
        """Return all users."""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT * FROM users
                ORDER BY created_at DESC
            """)

            rows = cursor.fetchall()

            return [
                User.from_database_row(row)
                for row in rows
            ]

        finally:
            connection.close()

    def update_user_role(self, user_id, role):
        """Change a user's role."""

        if role not in ("Admin", "Analyst"):
            raise ValueError("Invalid user role.")

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE users
                SET role = ?
                WHERE id = ?
            """, (role, user_id))

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()

    def update_user_status(self, user_id, is_active):
        """Enable or disable a user."""

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE users
                SET is_active = ?
                WHERE id = ?
            """, (int(is_active), user_id))

            connection.commit()

            return cursor.rowcount > 0

        finally:
            connection.close()