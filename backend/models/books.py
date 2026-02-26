from config.db_pool import query

def create_books_table():
    sql = """
    CREATE TABLE IF NOT EXISTS books (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(500) NOT NULL,
        author VARCHAR(300) NOT NULL,
        type ENUM('book', 'ebook', 'audiobook', 'comic', 'magazine') NOT NULL DEFAULT 'book',
        genre VARCHAR(100),
        pages SMALLINT UNSIGNED,
        language CHAR(5) NOT NULL DEFAULT 'ru',
        publication_year SMALLINT UNSIGNED,
        link VARCHAR(1000),
        description TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        FULLTEXT INDEX ft_title_author (title, author),
        INDEX idx_genre_year_lang (genre, publication_year, language),
        INDEX idx_year (publication_year),
        INDEX idx_type (type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    query(sql)



def create_tables_if_not_exist():
    """Ավտոմատ ստեղծել աղյուսակները, եթե չկան"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Ստեղծել users աղյուսակը with password and preferred_language
        cursor.execute(
        
        # Ստեղծել reading_sessions աղյուսակը
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reading_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_id INTEGER,
                start_time DATETIME,
                end_time DATETIME,
                pages_read INTEGER,
                session_duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ստեղծել book_comments աղյուսակը
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS book_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_id INTEGER,
                comment_text TEXT,
                rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (book_id) REFERENCES books(id)
            )
        """)
        
        # Ստեղծել creative_works աղյուսակը
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creative_works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title VARCHAR(255),
                content_type VARCHAR(50),
                content TEXT,
                genre VARCHAR(100),
                description TEXT,
                is_public BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Ստեղծել creative_work_comments աղյուսակը
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creative_work_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creative_work_id INTEGER,
                user_id INTEGER,
                comment_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creative_work_id) REFERENCES creative_works(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Ստեղծել reminders աղյուսակը
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reading_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reminder_time TIME,
                is_active BOOLEAN DEFAULT TRUE,
                days_of_week VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error creating tables: {e}")
        return False

# Database connection
def get_connection():
    return sqlite3.connect('reading_app.db', check_same_thread=False)

