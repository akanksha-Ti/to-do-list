# migrate_add_due.py
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

    conn.commit()
    conn.close()
    print("Migration finished successfully.")
except sqlite3.OperationalError as e:
    print("SQLite OperationalError:", e)
    sys.exit(1)
except Exception as e:
    print("Error:", e)
    sys.exit(1)
