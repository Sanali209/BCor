import sqlite3
import json
import os

db_path = "src/apps/experemental/boruscraper/data.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

import sys
from pathlib import Path

# Add root to sys.path
sys.path.append(str(Path(__file__).parent))

from src.apps.experemental.boruscraper.common.schemas import ScraperSettings

print("--- Projects ---")
projects = cursor.execute("SELECT * FROM projects").fetchall()
for p in projects:
    print(f"ID: {p['id']}, Name: {p['name']}")
    settings_json = p['settings_json']
    print(f"  Settings JSON: {settings_json}")
    try:
        settings_dict = json.loads(settings_json)
        print("  Attempting to instantiate ScraperSettings...")
        settings = ScraperSettings.from_dict(settings_dict)
        print("  Successfully instantiated ScraperSettings")
        print(f"  Start URLs: {settings.start_urls}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n--- Queue ---")
# The table name is project_queue
queue = cursor.execute("SELECT * FROM project_queue").fetchall()
for q in queue:
    print(f"ID: {q['id']}, Project ID: {q['project_id']}, Status: {q['status']}")

conn.close()
