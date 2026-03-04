# modules/db.py
import mysql.connector
from mysql.connector import Error
import json
import os
from dotenv import load_dotenv
from streamlit import cursor

load_dotenv()

def get_connection():
    try:
        conn = mysql.connector.connect(
            host       = os.getenv("DB_HOSTNAME", "127.0.0.1"),
            port       = int(os.getenv("DB_PORT", 3306)),
            user       = os.getenv("DB_USERNAME", "root"),
            password   = os.getenv("DB_PASSWORD", ""),
            database   = os.getenv("DB_DBNAME", "reading_app"),
            charset    = 'utf8mb4',
            autocommit = True
        )

        return conn
    except Error as e:
        print(f"DB connection error: {e}")
        return None

from contextlib import contextmanager

@contextmanager
def get_cursor():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor, conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()  # safe here — outside the query

def query(sql, params=(), fetch=False, one=False):
    with get_cursor() as (cursor, conn):
        cursor.execute(sql, params)

        if fetch:
            rows = cursor.fetchall()
            return rows[0] if one and rows else rows

        affected = cursor.rowcount
        last_id = cursor.lastrowid

        if "INSERT" in sql.upper() and last_id and last_id != 0:
            return last_id
        return affected > 0
    
def json_str(obj):
    """list/dict → JSON string safe for MySQL"""
    return json.dumps(obj, ensure_ascii=False) if obj is not None else None


def json_obj(s):
    """JSON string from DB → python object (default [])"""
    if not s:
        return []
    try:
        return json.loads(s)
    except:
        return []