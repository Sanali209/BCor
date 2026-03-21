import logging
from typing import Any

from core.database import DatabaseManager

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_collection_summary(self) -> dict[str, Any]:
        """Get high-level collection stats."""
        return self.db.get_stats()

    def get_top_large_images(self, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch top 100 largest images."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT path, filename, extension, width, height, size_bytes 
                FROM images 
                ORDER BY size_bytes DESC 
                LIMIT ?
            """,
                (limit,),
            )
            # Convert to list of dicts
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_extension_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get detailed stats per extension: count, total size, avg size.
        Returns: {'jpg': {'count': 10, 'total_size': 1000, 'avg_size': 100}, ...}
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT extension, COUNT(*), SUM(size_bytes), AVG(size_bytes)
                FROM images
                GROUP BY extension
                ORDER BY SUM(size_bytes) DESC
            """)

            stats = {}
            for row in cursor.fetchall():
                ext = row[0]
                stats[ext] = {"count": row[1], "total_size": row[2], "avg_size": row[3]}
            return stats
        finally:
            conn.close()

    def get_raw_data_for_charts(self) -> dict[str, list]:
        """
        Fetch raw area, size, and extension data for building histograms.
        Returns dict with 'areas', 'sizes', 'extensions', 'resolutions_by_ext' lists.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # For general simple histograms
            cursor.execute("SELECT area, size_bytes FROM images")
            rows = cursor.fetchall()
            areas = [row[0] for row in rows if row[0] is not None]
            sizes = [row[1] for row in rows if row[1] is not None]

            # For stacked resolution histogram (fetching all might be heavy for >1M images,
            # but standard approach for desktop app local DB usually fine up to a point.
            # Optimization: Downsample if too large? For now, raw full scan.)
            cursor.execute("SELECT extension, width, height FROM images")
            res_rows = cursor.fetchall()

            # Structure: {'jpg': [mpix1, mpix2], 'png': [...]}
            resolutions_by_ext = {}
            for row in res_rows:
                ext = row[0]
                w, h = row[1], row[2]
                mpix = (w * h) / 1000000.0
                if ext not in resolutions_by_ext:
                    resolutions_by_ext[ext] = []
                resolutions_by_ext[ext].append(mpix)

            return {"areas": areas, "sizes": sizes, "resolutions_by_ext": resolutions_by_ext}
        finally:
            conn.close()

    def get_savings_stats(self) -> dict[str, Any]:
        """Get total savings and recent history."""
        total = self.db.get_total_savings()
        history = self.db.get_savings_history(1000)
        return {"total_saved_bytes": total, "history": history}
