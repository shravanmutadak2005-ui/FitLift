import sqlite3

def create_database():
    conn = sqlite3.connect("fitlift.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            goal TEXT,
            target_weight REAL,
            activity_level TEXT,
            dietary_preference TEXT DEFAULT 'Non-Vegetarian',
            allergies TEXT DEFAULT 'None',
            meal_schedule TEXT DEFAULT 'Standard (4-5 Meals)',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe migrations for existing databases
    migrations = [
        "ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN dietary_preference TEXT DEFAULT 'Non-Vegetarian'",
        "ALTER TABLE users ADD COLUMN allergies TEXT DEFAULT 'None'",
        "ALTER TABLE users ADD COLUMN meal_schedule TEXT DEFAULT 'Standard (4-5 Meals)'"
    ]

    for mig in migrations:
        try:
            cursor.execute(mig)
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Backfill nulls
    cursor.execute("UPDATE users SET created_at = datetime('now', 'localtime') WHERE created_at IS NULL")
    cursor.execute("UPDATE users SET dietary_preference = 'Non-Vegetarian' WHERE dietary_preference IS NULL")
    cursor.execute("UPDATE users SET allergies = 'None' WHERE allergies IS NULL")
    cursor.execute("UPDATE users SET meal_schedule = 'Standard (4-5 Meals)' WHERE meal_schedule IS NULL")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()