from __future__ import annotations

import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path


def create_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            path TEXT PRIMARY KEY,
            filename TEXT,
            extension TEXT,
            size_bytes INTEGER,
            width INTEGER,
            height INTEGER,
            area INTEGER,
            created_at REAL,
            modified_at REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS space_savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT,
            saved_bytes INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_path TEXT
        )
    """)


def seed_data(db_path: str) -> None:
    print(f"Seeding test data into {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    create_schema(cursor)

    # Clean existing data
    cursor.execute("DELETE FROM images")
    cursor.execute("DELETE FROM space_savings")

    # Add sample images
    extensions = [".jpg", ".png", ".webp", ".gif", ".tif"]
    sample_images = []

    for i in range(150):
        ext = random.choice(extensions)
        w = random.randint(800, 4000)
        h = random.randint(600, 3000)
        size = int((w * h * 3) / random.uniform(10, 50))
        path = f"C:/Photos/test_image_{i}{ext}"
        sample_images.append(
            (
                path,
                f"test_image_{i}{ext}",
                ext,
                size,
                w,
                h,
                w * h,
                time.time() - random.randint(0, 5000000),
                time.time(),
            )
        )

    cursor.executemany(
        """
        INSERT INTO images 
        (path, filename, extension, size_bytes, width, height, area, created_at, modified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        sample_images,
    )

    # Add sample savings history
    history = []
    now = datetime.now()
    for i in range(50):
        saved = random.randint(1024 * 1024, 100 * 1024 * 1024)
        date = now - timedelta(days=50 - i)
        ts = date.timestamp()
        history.append(("Compress", saved, ts, f"dummy_path_{i}.jpg"))

    cursor.executemany(
        """
        INSERT INTO space_savings (action_type, saved_bytes, timestamp, original_path)
        VALUES (?, ?, ?, ?)
    """,
        history,
    )

    conn.commit()
    conn.close()
    print("Seeding complete!")


if __name__ == "__main__":
    db_file = Path("image_analyze_bcor.db")
    seed_data(str(db_file))
