# modules/db.py
import mysql.connector
from mysql.connector import Error
import json
import os
import traceback
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

def get_connection():
    """Create a connection — used by context manager and init"""
    try:
        print("Connecting to DB...")
        print("HOST:", os.getenv("DB_HOSTNAME", "db"))
        print("PORT:", os.getenv("DB_PORT", "3306"))
        print("USER:", os.getenv("DB_USERNAME", "root"))
        print("DB:", os.getenv("DB_DBNAME", "reading_app"))

        conn = mysql.connector.connect(
            host=os.getenv("DB_HOSTNAME", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USERNAME", "root"),
            password=os.getenv("DB_PASSWORD", "galstyanm2311"),
            database=os.getenv("DB_DBNAME", "reading_app"),
            charset='utf8mb4',
            autocommit=True,
            connection_timeout=10,
        )
        print("DB connected successfully")
        return conn
    except Error as e:
        print("DB CONNECTION ERROR:", e)
        traceback.print_exc()
        return None


def init_database():
    """
    Create database + all tables if they don't exist.
    Safe to call multiple times (uses IF NOT EXISTS).
    """
    print("Initializing database schema...")

    # Step 1: Connect without selecting database (to create DB if missing)
    conn_no_db = None
    try:
        conn_no_db = mysql.connector.connect(
            host=os.getenv("DB_HOSTNAME", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USERNAME", "root"),
            password=os.getenv("DB_PASSWORD", "galstyanm2311"),
            charset='utf8mb4',
        )
        cursor = conn_no_db.cursor()

        # Create database if not exists
        db_name = os.getenv("DB_DBNAME", "reading_app")
        cursor.execute(f"""
            CREATE DATABASE IF NOT EXISTS {db_name}
            CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        print(f"Database '{db_name}' checked/created.")

        cursor.close()
        conn_no_db.close()
    except Error as e:
        print("Error creating database:", e)
        traceback.print_exc()
        return False

    # Step 2: Connect to the actual database and create tables
    with get_cursor() as (cursor, conn):
        try:
            # users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(80) PRIMARY KEY,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash CHAR(64) NOT NULL,
                    daily_reading_time INT DEFAULT 30,
                    reading_speed DECIMAL(4,2) DEFAULT NULL,
                    age INT DEFAULT NULL,
                    profession VARCHAR(120) DEFAULT NULL,
                    bio TEXT DEFAULT NULL,
                    preferred_genres JSON,
                    preferred_languages JSON,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # friendships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS friendships (
                    user1 VARCHAR(80) NOT NULL,
                    user2 VARCHAR(80) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user1, user2),
                    FOREIGN KEY (user1) REFERENCES users(username) ON DELETE CASCADE,
                    FOREIGN KEY (user2) REFERENCES users(username) ON DELETE CASCADE,
                    CHECK (user1 < user2)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # friend_requests
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS friend_requests (
                    sender VARCHAR(80) NOT NULL,
                    receiver VARCHAR(80) NOT NULL,
                    status ENUM('pending','accepted','rejected') DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (sender, receiver),
                    FOREIGN KEY (sender) REFERENCES users(username) ON DELETE CASCADE,
                    FOREIGN KEY (receiver) REFERENCES users(username) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # books
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(300) NOT NULL,
                    author VARCHAR(200),
                    type VARCHAR(100),
                    genre VARCHAR(100),
                    language VARCHAR(50),
                    pages INT,
                    publication_year INT,
                    description TEXT,
                    link VARCHAR(1000),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # reading_sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reading_sessions (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(80) NOT NULL,
                    book_id VARCHAR(50) NOT NULL,
                    book_title VARCHAR(255) NOT NULL,
                    pages_read INT NOT NULL,
                    session_duration INT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # book_comments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_comments (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(80) NULL,
                    book_id VARCHAR(50) NOT NULL,
                    comment_text TEXT NOT NULL,
                    rating TINYINT DEFAULT NULL CHECK (rating BETWEEN 1 AND 5),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE SET NULL ON UPDATE CASCADE,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # creative_works
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creative_works (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(80) NOT NULL,
                    username VARCHAR(80) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content_type VARCHAR(50) NOT NULL,
                    content LONGTEXT NOT NULL,
                    genre VARCHAR(100) NOT NULL DEFAULT 'Ընդհանուր',
                    description TEXT NULL,
                    is_public BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # creative_work_comments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creative_work_comments (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    creative_work_id BIGINT NOT NULL,
                    user_id VARCHAR(80) NULL,
                    comment_text TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (creative_work_id) REFERENCES creative_works(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE SET NULL ON UPDATE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    sender VARCHAR(80) NOT NULL,
                    receiver VARCHAR(80) NOT NULL,
                    content TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_chat (sender, receiver, created_at),
                    FOREIGN KEY (sender) REFERENCES users(username) ON DELETE CASCADE,
                    FOREIGN KEY (receiver) REFERENCES users(username) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # reading_reminders
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reading_reminders (
                    user_id VARCHAR(80) PRIMARY KEY,
                    reminder_time TIME NOT NULL,
                    days_of_week JSON NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # poems
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS poems (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    author VARCHAR(80) NOT NULL,
                    title VARCHAR(300) NOT NULL,
                    content MEDIUMTEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author) REFERENCES users(username) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            # poem_likes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS poem_likes (
                    poem_id BIGINT NOT NULL,
                    username VARCHAR(80) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (poem_id, username),
                    FOREIGN KEY (poem_id) REFERENCES poems(id) ON DELETE CASCADE,
                    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)

            conn.commit()
            print("All tables checked/created successfully.")
            return True

        except Error as e:
            print("Schema initialization ERROR:", e)
            traceback.print_exc()
            return False


@contextmanager
def get_cursor():
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor, conn
        conn.commit()
    except Exception as e:
        if conn.is_connected():
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


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
    return json.dumps(obj, ensure_ascii=False) if obj is not None else None


def json_obj(s):
    if not s:
        return []
    try:
        return json.loads(s)
    except:
        return []
