import logging
import sqlite3
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ImageRecord:
    id: int
    path: str
    filename: str
    extension: str
    size_bytes: int
    width: int
    height: int
    area: int
    hash: str | None = None
    created_at: float = 0.0
    modified_at: float = 0.0


class DatabaseManager:
    def __init__(self, db_path: str = "astral_mariner.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database with high-performance settings."""
        conn = self.get_connection()
        try:
            # Enable WAL mode for better concurrency and performance
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA cache_size=-64000;")  # 64MB cache

            # Create images table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    area INTEGER GENERATED ALWAYS AS (width * height) VIRTUAL,
                    hash TEXT,
                    created_at REAL,
                    modified_at REAL
                )
            """)

            # Create indexes for common query patterns
            conn.execute("CREATE INDEX IF NOT EXISTS idx_images_extension ON images(extension);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_images_size ON images(size_bytes);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_images_area ON images(area);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_images_path ON images(path);")

            # Create space_savings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS space_savings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL DEFAULT (strftime('%s', 'now')),
                    action_type TEXT NOT NULL,
                    saved_bytes INTEGER NOT NULL,
                    original_path TEXT
                )
            """)

            conn.commit()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            conn.close()

    def record_saving(self, action_type: str, saved_bytes: int, path: str):
        """Record a space saving event."""
        if saved_bytes <= 0:
            return

        conn = self.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO space_savings (action_type, saved_bytes, original_path)
                VALUES (?, ?, ?)
            """,
                (action_type, saved_bytes, path),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to record saving: {e}")
        finally:
            conn.close()

    def get_total_savings(self) -> int:
        """Get total bytes saved."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(saved_bytes) FROM space_savings")
            result = cursor.fetchone()[0]
            return result if result else 0
        finally:
            conn.close()

    def get_savings_history(self, limit: int = 1000) -> list[dict[str, Any]]:
        """Get recent savings history."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, action_type, saved_bytes, original_path
                FROM space_savings
                ORDER BY id DESC
                LIMIT ?
            """,
                (limit,),
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_image(self, path: str):
        """Remove a single image from the database."""
        conn = self.get_connection()
        try:
            conn.execute("DELETE FROM images WHERE path = ?", (path,))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
        finally:
            conn.close()

    def upsert_image(self, data: dict[str, Any]):
        """Insert or update a single image record."""
        conn = self.get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO images 
                (path, filename, extension, size_bytes, width, height, created_at, modified_at)
                VALUES (:path, :filename, :extension, :size_bytes, :width, :height, :created_at, :modified_at)
            """,
                data,
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to upsert image: {e}")
        finally:
            conn.close()

    def bulk_insert_images(self, images: list[dict[str, Any]]):
        """
        Insert multiple image records efficiently.
        images: List of dictionaries matching ImageRecord fields (excluding id)
        """
        if not images:
            return

        conn = self.get_connection()
        try:
            conn.executemany(
                """
                INSERT OR IGNORE INTO images 
                (path, filename, extension, size_bytes, width, height, created_at, modified_at)
                VALUES (:path, :filename, :extension, :size_bytes, :width, :height, :created_at, :modified_at)
            """,
                images,
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics directly from DB."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            stats = {}

            # Total count
            cursor.execute("SELECT COUNT(*) FROM images")
            stats["total_images"] = cursor.fetchone()[0]

            # Total size
            cursor.execute("SELECT SUM(size_bytes) FROM images")
            stats["total_size_bytes"] = cursor.fetchone()[0] or 0

            # Format breakdown
            cursor.execute("""
                SELECT extension, COUNT(*) as count 
                FROM images 
                GROUP BY extension 
                ORDER BY count DESC
            """)
            stats["formats"] = dict(cursor.fetchall())

            return stats
        finally:
            conn.close()

    def get_area_histogram(self, num_buckets: int = 20) -> dict[str, list[float]]:
        """Calculate area distribution for histogram."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Get min/max area to calculate buckets
            cursor.execute("SELECT MIN(area), MAX(area) FROM images")
            min_area, max_area = cursor.fetchone()

            if min_area is None:
                return {"bins": [], "counts": []}

            step = (max_area - min_area) / num_buckets

            # This is a basic implementation. For 1M rows, we might want to do grouping in SQL
            # or just fetch the 'area' column and histogram it in numpy if memory allows (1M ints is small ~8MB)
            cursor.execute("SELECT area FROM images")
            areas = [row[0] for row in cursor.fetchall()]

            return {"raw_areas": areas}  # Let the analytics engine handle the binning with numpy
        finally:
            conn.close()

    def clear_database(self):
        conn = self.get_connection()
        conn.execute("DELETE FROM images")
        # Do not clear space_savings! This should persist across scans.
        conn.commit()
        conn.close()
