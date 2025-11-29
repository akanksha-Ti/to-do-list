from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
import random

app = Flask(__name__)

# -------------------------------------------------
# DATABASE PATH (SQLite only)
#  - Local: ./tasks_v3.db
#  - Vercel: /tmp/tasks_v3.db (writable)
# -------------------------------------------------
IS_VERCEL = bool(
    os.environ.get("VERCEL")
    or os.environ.get("VERCEL_URL")
    or os.environ.get("VERCEL_ENV")
)

if IS_VERCEL:
    DB_PATH = "/tmp/tasks_v3.db"   # NEW NAME so old DB is ignored
else:
    DB_PATH = "tasks_v3.db"


QUOTES = [
    "Do it with passion or not at all.",
    "Small steps every day.",
    "Make each day your masterpiece.",
    "Focus on progress, not perfection.",
    "Start where you are. Use what you have. Do what you can.",
    "Simplicity is the ultimate sophistication.",
    "One thing at a time — make it count."
]


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def recreate_tasks_table():
    """Drop and recreate tasks table with the correct schema."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS tasks;")
    cur.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TEXT,
            due_time TEXT,
            reminder_dt TEXT
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def init_db():
    """Ensure DB file exists and tasks table has correct columns."""
    # If DB file doesn't exist, just recreate everything.
    if not os.path.exists(DB_PATH):
        recreate_tasks_table()
        return

    # If it exists, try to select reminder_dt.
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(tasks);")
        cols = [row[1] for row in cur.fetchall()]
        if "reminder_dt" not in cols or "due_time" not in cols or "due_date" not in cols:
            # Wrong schema -> recreate
            recreate_tasks_table()
    except sqlite3.OperationalError:
        # Table doesn't exist or broken -> recreate
        recreate_tasks_table()
    finally:
        cur.close()
        conn.close()


# Run once at import
init_db()


@app.route("/")
def index():
    now = datetime.now()
    server_time = now.strftime("%Y-%m-%d %H:%M:%S")
    server_date = now.strftime("%A, %d %B %Y")
    quote = random.choice(QUOTES)

    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    conn.close()

    return render_template(
        "index.html",
        tasks=tasks,
        server_time=server_time,
        server_date=server_date,
        quote=quote,
    )


@app.route("/add", methods=["POST"])
def add_task():
    desc = request.form.get("task", "").strip()
    due_date = request.form.get("due_date") or None
    due_time = request.form.get("due_time") or None
    reminder_dt = request.form.get("reminder_dt") or None  # "YYYY-MM-DDTHH:MM"

    if not desc:
        return redirect(url_for("index"))

    # Try insert. If schema is wrong (no reminder_dt), fix & retry once.
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO tasks (description, due_date, due_time, reminder_dt)
            VALUES (?, ?, ?, ?);
            """,
            (desc, due_date, due_time, reminder_dt),
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        # If this is the classic error, fix schema and retry once.
        if "no column named reminder_dt" in str(e):
            conn.close()
            recreate_tasks_table()
            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO tasks (description, due_date, due_time, reminder_dt)
                VALUES (?, ?, ?, ?);
                """,
                (desc, due_date, due_time, reminder_dt),
            )
            conn.commit()
        else:
            conn.close()
            raise
    finally:
        conn.close()

    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    conn = get_db_connection()
    conn.execute("UPDATE tasks SET status='Completed' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/set_reminder/<int:task_id>", methods=["POST"])
def set_reminder(task_id):
    val = request.form.get("reminder_dt")
    reminder_dt = val if val else None

    conn = get_db_connection()
    conn.execute(
        "UPDATE tasks SET reminder_dt = ? WHERE id = ?",
        (reminder_dt, task_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
