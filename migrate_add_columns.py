# migrate_add_columns.py
import sqlite3
import sys
DB_PATH = 'database.db'

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols

try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create table if it doesn't exist at all (safety)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Add columns if missing
    if not column_exists(c, 'tasks', 'due_date'):
        c.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
        print("Added column: due_date")
    else:
        print("Column due_date already exists")

    if not column_exists(c, 'tasks', 'due_time'):
        c.execute("ALTER TABLE tasks ADD COLUMN due_time TEXT")
        print("Added column: due_time")
    else:
        print("Column due_time already exists")

    if not column_exists(c, 'tasks', 'reminder_dt'):
        c.execute("ALTER TABLE tasks ADD COLUMN reminder_dt TEXT")
        print("Added column: reminder_dt")
    else:
        print("Column reminder_dt already exists")

    conn.commit()
    conn.close()
    print("Migration finished successfully.")
except Exception as e:
    print("Migration failed:", e)
    sys.exit(1)
