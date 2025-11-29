from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
import random

app = Flask(__name__)
DB_PATH = 'database.db'

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

def init_db():
    # create DB + table if missing (safe)
    if not os.path.exists(DB_PATH):
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT,
                due_time TEXT,
                reminder_dt TEXT
            )
        ''')
        conn.commit()
        conn.close()

# ensure table exists (no-op if already present)
init_db()

@app.route('/')
def index():
    now = datetime.now()
    server_time = now.strftime("%Y-%m-%d %H:%M:%S")
    server_date = now.strftime("%A, %d %B %Y")
    quote = random.choice(QUOTES)

    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY id').fetchall()
    conn.close()
    return render_template('index.html',
                           tasks=tasks,
                           server_time=server_time,
                           server_date=server_date,
                           quote=quote)

@app.route('/add', methods=['POST'])
def add_task():
    desc = request.form.get('task', '').strip()
    due_date = request.form.get('due_date') or None
    due_time = request.form.get('due_time') or None
    # reminder in HTML datetime-local format: "YYYY-MM-DDTHH:MM"
    reminder_dt = request.form.get('reminder_dt') or None

    if desc:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO tasks (description, due_date, due_time, reminder_dt) VALUES (?, ?, ?, ?)',
            (desc, due_date, due_time, reminder_dt)
        )
        conn.commit()
        conn.close()

    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    conn = get_db_connection()
    conn.execute("UPDATE tasks SET status='Completed' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/set_reminder/<int:task_id>', methods=['POST'])
def set_reminder(task_id):
    # If remove button submitted with value "", this will be empty string
    # We transform empty string to None to remove
    val = request.form.get('reminder_dt')
    reminder_dt = val if val else None
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET reminder_dt = ? WHERE id = ?', (reminder_dt, task_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
