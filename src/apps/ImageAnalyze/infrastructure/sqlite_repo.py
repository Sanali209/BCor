from __future__ import annotations

import logging
import sqlite3
from typing import Any

from ..domain.models import ImageAnalysisRecord, ProcessingResult

logger = logging.getLogger(__name__)


class SqliteImageRepo:
    """Высокопроизводительный репозиторий для хранения метаданных изображений и статистики."""

    def __init__(self, db_path: str = "astral_mariner.db") -> None:
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Инициализация БД с оптимизациями производительности."""
        try:
            with self.get_connection() as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA cache_size=-64000;")

                # Таблица изображений
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

                # Индексы
                conn.execute("CREATE INDEX IF NOT EXISTS idx_images_extension ON images(extension);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_images_size ON images(size_bytes);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_images_area ON images(area);")

                # Таблица экономии места
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
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def bulk_insert(self, records: list[ImageAnalysisRecord]) -> None:
        """Массовая вставка записей."""
        if not records:
            return
        
        data = [
            (r.path, r.filename, r.extension, r.size_bytes, r.width, r.height, r.hash, r.created_at, r.modified_at)
            for r in records
        ]
        
        try:
            with self.get_connection() as conn:
                conn.executemany("""
                    INSERT OR IGNORE INTO images 
                    (path, filename, extension, size_bytes, width, height, hash, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error during bulk insert: {e}")
            raise

    def record_saving(self, action_type: str, saved_bytes: int, path: str) -> None:
        """Записывает событие экономии места."""
        if saved_bytes <= 0:
            return

        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO space_savings (action_type, saved_bytes, original_path) VALUES (?, ?, ?)",
                    (action_type, saved_bytes, path),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error recording space saving: {e}")
            raise

    def get_total_savings(self) -> int:
        """Возвращает общую экономию в байтах."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(saved_bytes) FROM space_savings")
                res = cursor.fetchone()[0]
                return res if res is not None else 0
        except sqlite3.Error as e:
            logger.error(f"Error getting total savings: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """Общая статистика коллекции."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*), SUM(size_bytes) FROM images")
                row = cursor.fetchone()
                count = row[0] if row and row[0] is not None else 0
                total_size = row[1] if row and len(row) > 1 and row[1] is not None else 0
                
                cursor.execute("SELECT SUM(saved_bytes) FROM space_savings")
                res = cursor.fetchone()
                total_saved = res[0] if res and res[0] is not None else 0
                
                cursor.execute("SELECT extension, COUNT(*) FROM images GROUP BY extension")
                formats = dict(cursor.fetchall())
                
                return {
                    "total_images": count,
                    "total_size_bytes": total_size,
                    "total_saved_bytes": total_saved,
                    "formats": formats
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "total_images": 0,
                "total_size_bytes": 0,
                "total_saved_bytes": 0,
                "formats": {}
            }

    def get_extension_stats(self) -> dict[str, dict[str, Any]]:
        """Статистика по расширениям."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT extension, COUNT(*), SUM(size_bytes), AVG(size_bytes)
                    FROM images GROUP BY extension
                """)
                return {
                    row[0]: {"count": row[1], "size": row[2], "avg": row[3]}
                    for row in cursor.fetchall()
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting extension stats: {e}")
            return {}

    def get_chart_data(self) -> dict[str, Any]:
        """Данные для графиков."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Распределение по размерам (бакеты)
                cursor.execute("SELECT size_bytes FROM images")
                sizes = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("SELECT width * height FROM images")
                areas = [row[0] for row in cursor.fetchall()]
                
                return {"sizes": sizes, "areas": areas}
        except sqlite3.Error as e:
            logger.error(f"Error getting chart data: {e}")
            return {"sizes": [], "areas": []}

    def get_savings_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """История экономии места."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, action_type, saved_bytes, original_path
                    FROM space_savings ORDER BY id DESC LIMIT ?
                """, (limit,))
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting savings history: {e}")
            return []

    def clear(self) -> None:
        """Очистка таблицы изображений."""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM images")
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error clearing database: {e}")

    def get_all(self) -> list[ImageAnalysisRecord]:
        """Получение всех записей."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, path, filename, extension, size_bytes, width, height, hash, created_at, modified_at FROM images")
                return [
                    ImageAnalysisRecord(
                        id=row["id"],
                        path=row["path"],
                        filename=row["filename"],
                        extension=row["extension"],
                        size_bytes=row["size_bytes"],
                        width=row["width"],
                        height=row["height"],
                        hash=row["hash"],
                        created_at=row["created_at"],
                        modified_at=row["modified_at"]
                    )
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            logger.error(f"Error getting all records: {e}")
            return []
