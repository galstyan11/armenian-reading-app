# config/db_pool.py
import logging
from contextlib import contextmanager
from typing import Any, Generator

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import Error
from mysql.connector.cursor import MySQLCursor

from config.settings import Config

logger = logging.getLogger(__name__)

# =============================================================================
# Один раз создаём пул соединений
# =============================================================================
_pool = MySQLConnectionPool(
    pool_name="simple_pool",
    pool_size=10,
    pool_reset_session=True,
    host=Config.DB_HOSTNAME,
    port=Config.DB_PORT or 3306,
    user=Config.DB_USERNAME,
    password=Config.DB_PASSWORD,
    database=Config.DB_DATNAME,
    autocommit=True,
    charset="utf8mb4",
    collation="utf8mb4_unicode_ci",
    use_pure=True,
)

@contextmanager
def _cursor() -> Generator[MySQLCursor, None, None]:
    conn = None
    cur = None
    try:
        conn = _pool.get_connection()
        cur = conn.cursor(dictionary=True)
        yield cur
        conn.commit()
    except Error as err:
        if conn and conn.is_connected():
            conn.rollback()
        logger.error(f"DB Error: {err}")
        raise
    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()  # возвращает соединение в пул

# ─────────────────────────────────────────────────────────────────────────────
# Главная функция — просто передаёшь SQL-строку и всё
# ─────────────────────────────────────────────────────────────────────────────
def query(sql: str, params: tuple | dict | None = None) -> list[dict] | None:
    """
    Универсальная функция для любого SQL-запроса.

    Возвращает:
        - list[dict] — если запрос возвращает строки (SELECT)
        - None       — если это INSERT/UPDATE/DELETE и т.д.

    Пример использования:
        users = query("SELECT * FROM users WHERE active = %s", (1,))
        query("INSERT INTO logs (message) VALUES (%s)", ("hello",))
    """
    with _cursor() as cur:
        cur.execute(sql, params or ())
        
        # Если есть результат — возвращаем его
        if cur.with_rows:
            return cur.fetchall()
        
        # Иначе просто подтверждаем, что запрос прошёл
        return None