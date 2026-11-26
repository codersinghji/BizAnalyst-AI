
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "users.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_auth_database():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Analyst',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                otp_hash TEXT,
                otp_expiry TEXT
            )
        """)

        # Migrate existing databases safely
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {
            column["name"] for column in cursor.fetchall()
        }

        if "otp_hash" not in existing_columns:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN otp_hash TEXT"
            )

        if "otp_expiry" not in existing_columns:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN otp_expiry TEXT"
            )

        connection.commit()

    finally:
        connection.close()


def get_user_by_email(email):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),)
        )
        return cursor.fetchone()

    finally:
        connection.close()


def create_user(name, email, password_hash, role="Analyst"):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (
                name, email, password_hash, role
            )
            VALUES (?, ?, ?, ?)
        """, (
            name.strip(),
            email.lower().strip(),
            password_hash,
            role
        ))

        connection.commit()
        return cursor.lastrowid

    finally:
        connection.close()


def get_all_users():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id, name, email, role, is_active, created_at
            FROM users
            ORDER BY created_at DESC
        """)

        return cursor.fetchall()

    finally:
        connection.close()


def save_password_reset_otp(email, otp_hash, expiry):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users
            SET otp_hash = ?, otp_expiry = ?
            WHERE email = ?
        """, (
            otp_hash,
            expiry,
            email.lower().strip()
        ))

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


def clear_password_reset_otp(email):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users
            SET otp_hash = NULL, otp_expiry = NULL
            WHERE email = ?
        """, (email.lower().strip(),))

        connection.commit()

    finally:
        connection.close()


def update_user_password(email, password_hash):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users
            SET password_hash = ?,
                otp_hash = NULL,
                otp_expiry = NULL
            WHERE email = ?
        """, (
            password_hash,
            email.lower().strip()
        ))

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()
