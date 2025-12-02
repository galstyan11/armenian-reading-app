from config.db import with_cursor, get_cursor

if __name__ == "__main__":
    print("Step 1: Creating table 'demo' and inserting one row...")
    
    with with_cursor() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS demo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL
            )
        """)
        c.execute("INSERT INTO demo (message) VALUES (?)", ("Բարև Ձեզ Հայաստանից!",))
        demo_id = c.lastrowid
        print(f"Inserted row with ID: {demo_id}")

    print("\nStep 2: Reading it back...")
    cursor = get_cursor()
    cursor.execute("SELECT * FROM demo")
    row = cursor.fetchone()
    print(f"Found: {row['message']} (ID: {row['id']})")

    print("\nStep 3: Deleting the row...")
    with with_cursor() as c:
        c.execute("DELETE FROM demo WHERE id = ?", (demo_id,))
        print(f"Deleted {c.rowcount} row(s)")

    print("\nStep 4: Confirm it's gone...")
    cursor = get_cursor()
    cursor.execute("SELECT * FROM demo")
    if cursor.fetchone() is None:
        print("Perfect! Table is clean again.")
