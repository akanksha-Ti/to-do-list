from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os
import random

from dotenv import load_dotenv

# Load .env for local dev (harmless on Vercel)
load_dotenv()

app = Flask(__name__)

# -----------------------------
# Environment / DB mode
# -----------------------------
IS_VERCEL = bool(os.environ.get("VERCEL_URL") or os.environ.get("VERCEL"))
USE_POSTGRES = IS_VERCEL  # Vercel -> Postgres (Supabase), Local -> SQLite

if USE_POSTGRES:
    # Postgres / Supabase
    import psycopg2
    from psycopg2.extras import RealDictCursor

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. For Vercel, add it in Project Settings -> Environment Variables."
        )
else:
    # Local SQLite
    import sqlite3
    DB_PATH = "database.db"

QUOTES = [
    "Do it with passion or not at all.",
    "Small steps every day.",
    "Make each day your masterpiece.",
    "Focus on progress, not perfection.",
    "Start where you are. Use what you have. Do what you can.",
    "Simplicity is the ultimate sophistication.",
    "One thing at a time — make it count."
]

# -----------------------------
# DB helpers
# -----------------------------
def get_db_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    if USE_POSTGRES:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          SERIAL PRIMARY KEY,
                description TEXT NOT NULL,
                status      TEXT DEFAULT 'Pending',
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                due_date    TEXT,
                due_time    TEXT,
                reminder_dt TEXT
            );
            """
        )
    else:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
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

# create table on startup
init_db()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    now = datetime.now()
    server_time = now.strftime("%Y-%m-%d %H:%M:%S")
    server_date = now.strftime("%A, %d %B %Y")
    quote = random.choice(QUOTES)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks ORDER BY id;")
    tasks = cur.fetchall()
    cur.close()
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

    if desc:
        conn = get_db_connection()
        cur = conn.cursor()

        if USE_POSTGRES:
            cur.execute(
                """
                INSERT INTO tasks (description, due_date, due_time, reminder_dt)
                VALUES (%s, %s, %s, %s);
                """,
                (desc, due_date, due_time, reminder_dt),
            )
        else:
            cur.execute(
                """
                INSERT INTO tasks (description, due_date, due_time, reminder_dt)
                VALUES (?, ?, ?, ?);
                """,
                (desc, due_date, due_time, reminder_dt),
            )

        conn.commit()
        cur.close()
        conn.close()

    return redirect(url_for("index"))

@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if USE_POSTGRES:
        cur.execute(
            "UPDATE tasks SET status = 'Completed' WHERE id = %s;",
            (task_id,),
        )
    else:
        cur.execute(
            "UPDATE tasks SET status = 'Completed' WHERE id = ?;",
            (task_id,),
        )

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if USE_POSTGRES:
        cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
    else:
        cur.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))

@app.route("/set_reminder/<int:task_id>", methods=["POST"])
def set_reminder(task_id):
    val = request.form.get("reminder_dt")
    reminder_dt = val if val else None

    conn = get_db_connection()
    cur = conn.cursor()

    if USE_POSTGRES:
        cur.execute(
            "UPDATE tasks SET reminder_dt = %s WHERE id = %s;",
            (reminder_dt, task_id),
        )
    else:
        cur.execute(
            "UPDATE tasks SET reminder_dt = ? WHERE id = ?;",
            (reminder_dt, task_id),
        )

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
