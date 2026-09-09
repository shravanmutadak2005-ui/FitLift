import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fitlift.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_1rm(weight, reps):
    """Calculate Estimated 1-Rep Max using the Epley formula: Weight * (1 + Reps / 30)"""
    if reps <= 1:
        return float(weight)
    return round(float(weight) * (1.0 + float(reps) / 30.0), 1)

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT,
            email TEXT,
            password_hash TEXT,
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

    # Safe migrations for users
    user_migrations = [
        "ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN dietary_preference TEXT DEFAULT 'Non-Vegetarian'",
        "ALTER TABLE users ADD COLUMN allergies TEXT DEFAULT 'None'",
        "ALTER TABLE users ADD COLUMN meal_schedule TEXT DEFAULT 'Standard (4-5 Meals)'",
        "ALTER TABLE users ADD COLUMN username TEXT",
        "ALTER TABLE users ADD COLUMN email TEXT",
        "ALTER TABLE users ADD COLUMN password_hash TEXT"
    ]

    for mig in user_migrations:
        try:
            cursor.execute(mig)
        except sqlite3.OperationalError:
            pass  # Column already exists

    cursor.execute("UPDATE users SET created_at = datetime('now', 'localtime') WHERE created_at IS NULL")
    cursor.execute("UPDATE users SET dietary_preference = 'Non-Vegetarian' WHERE dietary_preference IS NULL")
    cursor.execute("UPDATE users SET allergies = 'None' WHERE allergies IS NULL")
    cursor.execute("UPDATE users SET meal_schedule = 'Standard (4-5 Meals)' WHERE meal_schedule IS NULL")

    # Backfill username & default password for existing users if missing
    cursor.execute("SELECT id, name, username FROM users")
    existing_users = cursor.fetchall()
    used_usernames = set()
    for row in existing_users:
        u_id = row[0]
        u_name = row[1] or f"user{u_id}"
        u_username = row[2]
        if not u_username:
            base = "".join(c for c in u_name.lower() if c.isalnum()) or f"user{u_id}"
            candidate = base
            counter = 1
            while candidate in used_usernames:
                candidate = f"{base}{counter}"
                counter += 1
            used_usernames.add(candidate)
            default_hash = generate_password_hash("fitlift123")
            cursor.execute("""
                UPDATE users 
                SET username = ?, email = ?, password_hash = ? 
                WHERE id = ?
            """, (candidate, f"{candidate}@fitlift.local", default_hash, u_id))
        else:
            used_usernames.add(u_username)

    # Unique index on username
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username) WHERE username IS NOT NULL")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    # 2. Exercise Records & Progress Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercise_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exercise_name TEXT NOT NULL,
            category TEXT NOT NULL,
            weight_lifted REAL NOT NULL,
            reps INTEGER NOT NULL,
            sets INTEGER DEFAULT 1,
            estimated_1rm REAL,
            notes TEXT DEFAULT '',
            logged_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercise_user ON exercise_records(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercise_name ON exercise_records(exercise_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercise_category ON exercise_records(category)")

    # 3. Chat Messages Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sender TEXT NOT NULL,
            situation_tag TEXT DEFAULT 'general',
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id)")

    conn.commit()
    conn.close()

    seed_starter_records()

def seed_starter_records():
    """Seeds initial exercise progress records for the first user if records are empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM exercise_records")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1")
        user_row = cursor.fetchone()
        default_user_id = user_row["id"] if user_row else None

        starter_lifts = [
            ("Barbell Bench Press", "Chest", 90.0, 5, 3, "Hit smooth reps, ready to try 92.5kg", "2026-09-01"),
            ("Barbell Back Squat", "Legs", 130.0, 5, 4, "Deep depth, belt on set 3 and 4", "2026-09-03"),
            ("Conventional Deadlift", "Back", 160.0, 3, 3, "New all-time PR! Good chalk grip", "2026-09-05"),
            ("Overhead Barbell Press", "Shoulders", 60.0, 6, 3, "Strict standing press, locked core", "2026-09-06"),
            ("Barbell Bicep Curl", "Arms", 37.5, 8, 3, "Clean form against the wall", "2026-09-07"),
            ("Incline Dumbbell Press", "Chest", 34.0, 8, 3, "Per dumbbell (34kg each)", "2026-09-08"),
            ("Romanian Deadlift", "Legs", 110.0, 8, 3, "Great hamstring stretch and cueing", "2026-09-08"),
            ("Weighted Pull-Up", "Back", 20.0, 6, 3, "20kg weight belt attached", "2026-09-09"),
        ]

        for name, cat, weight, reps, sets, notes, date in starter_lifts:
            e1rm = calculate_1rm(weight, reps)
            cursor.execute("""
                INSERT INTO exercise_records 
                (user_id, exercise_name, category, weight_lifted, reps, sets, estimated_1rm, notes, logged_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (default_user_id, name, cat, weight, reps, sets, e1rm, notes, date))

        conn.commit()

    conn.close()

# ==============================================================================
# Authentication & User Management Queries
# ==============================================================================

def register_user(name, username, password, email=None):
    """
    Registers a new user.
    Returns (user_dict, error_message).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    name = name.strip()
    username = username.strip().lower()
    email = email.strip().lower() if email else f"{username}@fitlift.local"

    if len(username) < 3:
        conn.close()
        return None, "Username must be at least 3 characters long."

    if len(password) < 6:
        conn.close()
        return None, "Password must be at least 6 characters long."

    # Check for existing username
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return None, "This username is already taken. Please choose another."

    # Check for existing email if provided
    if email and not email.endswith("@fitlift.local"):
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return None, "An account with this email already exists."

    password_hash = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (name, username, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
    """, (name, username, email, password_hash))

    new_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE id = ?", (new_id,))
    new_user = dict(cursor.fetchone())
    conn.close()

    return new_user, None

def authenticate_user(username_or_email, password):
    """
    Authenticates a user via username/email and password.
    Returns user_dict if valid, else None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query_val = username_or_email.strip().lower()
    cursor.execute("""
        SELECT * FROM users 
        WHERE LOWER(username) = ? OR LOWER(email) = ?
    """, (query_val, query_val))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        return None

    user = dict(user_row)
    if not user.get("password_hash"):
        return None

    if check_password_hash(user["password_hash"], password):
        return user
    return None

def get_user_by_id(user_id):
    """Fetches user dict by primary key ID."""
    if not user_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_profile(user_id, age, gender, height, weight, goal, target_weight, activity_level, dietary_preference, allergies, meal_schedule):
    """Updates body metrics & preferences for the logged-in user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET
            age = ?,
            gender = ?,
            height = ?,
            weight = ?,
            goal = ?,
            target_weight = ?,
            activity_level = ?,
            dietary_preference = ?,
            allergies = ?,
            meal_schedule = ?
        WHERE id = ?
    """, (age, gender, height, weight, goal, target_weight, activity_level, dietary_preference, allergies, meal_schedule, user_id))
    conn.commit()
    conn.close()

# ==============================================================================
# Exercise & Progress Queries (Scoped to User)
# ==============================================================================

def log_exercise_record(user_id, exercise_name, category, weight_lifted, reps, sets, notes, logged_date):
    """Log an exercise lift scoped to user_id. Returns (new_id, is_new_pr, old_pr_weight)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    weight_lifted = float(weight_lifted)
    reps = int(reps)
    sets = int(sets) if sets else 1
    estimated_1rm = calculate_1rm(weight_lifted, reps)

    # Check prior highest weight for this exercise for this user
    if user_id:
        cursor.execute("""
            SELECT MAX(weight_lifted) FROM exercise_records 
            WHERE exercise_name = ? AND user_id = ?
        """, (exercise_name, user_id))
    else:
        cursor.execute("""
            SELECT MAX(weight_lifted) FROM exercise_records 
            WHERE exercise_name = ?
        """, (exercise_name,))

    prev_max_row = cursor.fetchone()
    old_pr_weight = prev_max_row[0] if prev_max_row and prev_max_row[0] is not None else 0.0

    is_new_pr = weight_lifted > old_pr_weight

    cursor.execute("""
        INSERT INTO exercise_records 
        (user_id, exercise_name, category, weight_lifted, reps, sets, estimated_1rm, notes, logged_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, exercise_name, category, weight_lifted, reps, sets, estimated_1rm, notes, logged_date))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return new_id, is_new_pr, old_pr_weight

def get_personal_records(user_id=None, category=None):
    """
    Returns personal records (highest weight lifted) scoped to user_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if user_id is not None:
        conditions.append("user_id = ?")
        params.append(user_id)
    if category and category != "All":
        conditions.append("category = ?")
        params.append(category)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT er.*, total_logs.log_count
        FROM exercise_records er
        INNER JOIN (
            SELECT exercise_name, MAX(weight_lifted) AS max_weight
            FROM exercise_records
            {where_clause}
            GROUP BY exercise_name
        ) top ON er.exercise_name = top.exercise_name AND er.weight_lifted = top.max_weight
        LEFT JOIN (
            SELECT exercise_name, COUNT(*) AS log_count
            FROM exercise_records
            {where_clause}
            GROUP BY exercise_name
        ) total_logs ON er.exercise_name = total_logs.exercise_name
        {where_clause}
        GROUP BY er.exercise_name
        ORDER BY er.weight_lifted DESC, er.estimated_1rm DESC
    """

    cursor.execute(query, params * 3 if where_clause else [])
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_exercise_history(user_id=None, category=None, limit=100):
    """Returns workout log history in reverse chronological order for user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if user_id is not None:
        conditions.append("user_id = ?")
        params.append(user_id)
    if category and category != "All":
        conditions.append("category = ?")
        params.append(category)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT er.*, u.name as user_name
        FROM exercise_records er
        LEFT JOIN users u ON er.user_id = u.id
        {where_clause}
        ORDER BY er.logged_date DESC, er.id DESC
        LIMIT ?
    """
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_progress_stats(user_id=None):
    """Calculates overall progress metrics scoped to user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()

    user_filter = "WHERE user_id = ?" if user_id is not None else ""
    params = [user_id] if user_id is not None else []

    cursor.execute(f"SELECT COUNT(*) FROM exercise_records {user_filter}", params)
    total_logs = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(DISTINCT exercise_name) FROM exercise_records {user_filter}", params)
    unique_exercises = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT exercise_name, weight_lifted, reps, category, logged_date 
        FROM exercise_records {user_filter}
        ORDER BY weight_lifted DESC LIMIT 1
    """, params)
    heaviest_row = cursor.fetchone()
    heaviest_lift = dict(heaviest_row) if heaviest_row else None

    prs = get_personal_records(user_id=user_id)
    top_prs = prs[:4] if prs else []

    conn.close()

    return {
        "total_logs": total_logs,
        "unique_exercises": unique_exercises,
        "heaviest_lift": heaviest_lift,
        "top_prs": top_prs,
        "total_prs": len(prs)
    }

def delete_exercise_record(record_id, user_id=None):
    """Deletes an exercise record by ID, verifying user ownership."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM exercise_records WHERE id = ? AND user_id = ?", (record_id, user_id))
    else:
        cursor.execute("DELETE FROM exercise_records WHERE id = ?", (record_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ==============================================================================
# Chat Queries (Scoped to User)
# ==============================================================================

def save_chat_message(user_id, sender, message, situation_tag="general"):
    """Persist a chat message to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_messages (user_id, sender, situation_tag, message)
        VALUES (?, ?, ?, ?)
    """, (user_id, sender, situation_tag, message))
    conn.commit()
    conn.close()

def get_chat_history(user_id=None, limit=50):
    """Retrieve recent chat messages scoped to user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("""
            SELECT * FROM chat_messages 
            WHERE user_id = ?
            ORDER BY id ASC LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM chat_messages 
            ORDER BY id ASC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_chat_history(user_id=None):
    """Clear chat messages for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Database initialized, migrated, and users backfilled.")