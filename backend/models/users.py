from config.db_pool import query

def create_users():
    sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(100) UNIQUE,
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                reading_speed INTEGER DEFAULT 2,
                daily_reading_time INTEGER DEFAULT 30,
                preferred_genres TEXT,
                preferred_language VARCHAR(50) DEFAULT 'Հայերեն',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    query(sql)