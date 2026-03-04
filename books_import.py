# books_import.py
import pandas as pd
from modules.db import query   # ← your existing database connection / query function

def import_books_from_csv_to_db():
    url = "https://raw.githubusercontent.com/galstyan11/armenian-reading-app/refs/heads/main/reading_app_db.csv"
    
    print("Loading CSV...")
    try:
        df = pd.read_csv(
            url,
            encoding='utf-8-sig',
            engine='python',
            quoting=1,
            doublequote=True,
            escapechar='\\',
            on_bad_lines='warn'
        )
        df.columns = df.columns.str.strip()
        
        print(f"Loaded {len(df)} rows from CSV")
        
        # Basic cleaning
        df['id'] = df['id'].astype(str).str.strip()
        df['title'] = df['title'].astype(str).str.strip()
        for col in ['author', 'type', 'genre', 'language', 'link', 'description']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().replace(['', 'nan', 'NaN'], None)
        
        for col in ['pages', 'publication_year']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
    except Exception as e:
        print(f"CSV loading failed: {e}")
        return

    inserted = 0
    updated = 0
    errors = 0

    print("Starting import to MySQL...")
    for idx, row in df.iterrows():
        try:
            query("""
                INSERT INTO books (
                    id, title, author, type, genre, language,
                    pages, publication_year, link, description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title             = VALUES(title),
                    author            = VALUES(author),
                    type              = VALUES(type),
                    genre             = VALUES(genre),
                    language          = VALUES(language),
                    pages             = VALUES(pages),
                    publication_year  = VALUES(publication_year),
                    link              = VALUES(link),
                    description       = VALUES(description)
            """, (
                row['id'],
                row['title'] or "Անվերնագիր",
                row.get('author'),
                row.get('type'),
                row.get('genre'),
                row.get('language'),
                int(row['pages']) if pd.notna(row['pages']) else None,
                int(row['publication_year']) if pd.notna(row['publication_year']) else None,
                row.get('link'),
                row.get('description')
            ))
            
            # Very simple insert vs update detection (not perfect, but good enough)
            inserted += 1
            
        except Exception as e:
            print(f"Error on row {idx} (id={row.get('id', 'unknown')}): {e}")
            errors += 1

    print("\n" + "="*50)
    print(f"Import finished:")
    print(f"  • Processed rows: {len(df)}")
    print(f"  • Inserted/updated: {inserted}")
    print(f"  • Errors: {errors}")
    print("="*50)

if __name__ == "__main__":
    import_books_from_csv_to_db()