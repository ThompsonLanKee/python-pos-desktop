
import sqlite3

from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Database directory and file
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "pos.db"


class Database:

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def connect(self):

        connection = sqlite3.connect(DATABASE_PATH)

        # Enable foreign key constraints
        connection.execute("PRAGMA foreign_keys = ON")

        # Return rows as dictionary-like objects
        connection.row_factory = sqlite3.Row

        return connection

    def initialize(self):

        with self.connect() as connection:

            connection.executescript("""

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                        CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS roles (
                    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT NOT NULL UNIQUE,
                    description TEXT
                );

                CREATE TABLE IF NOT EXISTS permissions (
                    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    permission_code TEXT NOT NULL UNIQUE,
                    description TEXT
                );

                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,

                    PRIMARY KEY (user_id, role_id),

                    FOREIGN KEY (user_id)
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (role_id)
                        REFERENCES roles(role_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id INTEGER NOT NULL,
                    permission_id INTEGER NOT NULL,

                    PRIMARY KEY (role_id, permission_id),

                    FOREIGN KEY (role_id)
                        REFERENCES roles(role_id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (permission_id)
                        REFERENCES permissions(permission_id)
                        ON DELETE CASCADE
                );

            """)

        print("Database initialized successfully!")


if __name__ == "__main__":

    database = Database()
    database.initialize()
