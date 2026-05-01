import sqlite3
import os
from datetime import datetime
try:
    from backend.config import TEMP_DIR
except ImportError:
    from config import TEMP_DIR

DB_PATH = os.path.join(os.path.dirname(__file__), "veera_logs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            media_type TEXT,
            filename TEXT,
            panic_score REAL,
            alert BOOLEAN,
            detections_count INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def log_analysis(media_type, filename, panic_score, alert, detections_count):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_logs (media_type, filename, panic_score, alert, detections_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (media_type, filename, panic_score, alert, detections_count))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging to database: {e}")

def get_logs(limit=50):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM analysis_logs ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        logs = [dict(row) for row in rows]
        conn.close()
        return logs
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

# Initialize database on module load
init_db()
