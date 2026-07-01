"""
database.py
-----------
A tiny helper module that centralizes how we talk to PostgreSQL.

Why a separate file?
Keeping database code in one place means app.py doesn't need to know
HOW we connect -- it just calls get_db_connection() and gets a
ready-to-use connection object. This is a common backend pattern
called "separation of concerns".
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load variables from the .env file into the environment (os.environ)
load_dotenv()


def get_db_connection():
    """
    Opens and returns a new connection to the PostgreSQL database.

    psycopg2 is the most common Python library for talking to
    PostgreSQL. Think of a "connection" as a phone line open between
    your Python program and the database server.

    cursor_factory=RealDictCursor makes query results come back as
    Python dictionaries (e.g. {"id": 1, "username": "bob"}) instead of
    plain tuples (e.g. (1, "bob")), which is much easier to work with.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "auth_demo"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        cursor_factory=RealDictCursor,
    )
    return conn


def init_db():
    """
    Creates the users table if it doesn't already exist.
    This lets you run `python database.py` once instead of manually
    running schema.sql, if you prefer.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id              SERIAL PRIMARY KEY,
            username        VARCHAR(50)  UNIQUE NOT NULL,
            email           VARCHAR(255) UNIQUE NOT NULL,
            password_hash   TEXT NOT NULL,
            created_at      TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized: 'users' table is ready.")


if __name__ == "__main__":
    # Running `python database.py` directly will set up the table for you.
    init_db()