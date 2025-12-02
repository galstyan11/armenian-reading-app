# config/db.py
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "reading-app.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def get_cursor() -> sqlite3.Cursor:
    return get_connection().cursor()

# This is the correct way to make it work with "with" statement
@contextmanager
def with_cursor() -> Generator[sqlite3.Cursor, None, None]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
