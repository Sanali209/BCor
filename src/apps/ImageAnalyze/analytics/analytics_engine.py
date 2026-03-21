from __future__ import annotations

import logging
from typing import Any

from ..infrastructure.sqlite_repo import SqliteImageRepo

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, db_manager: SqliteImageRepo) -> None:
        self.db = db_manager

    def get_collection_summary(self) -> dict[str, Any]:
        """Get high-level collection stats."""
        return self.db.get_stats()

    def get_top_large_images(self, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch top largest images."""
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
        """
        return self.db.get_extension_stats()

    def get_raw_data_for_charts(self) -> dict[str, Any]:
        """
        Fetch raw area, size, and extension data for building histograms.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT width * height, size_bytes FROM images")
            rows = cursor.fetchall()
            areas = [row[0] for row in rows if row[0] is not None]
            sizes = [row[1] for row in rows if row[1] is not None]

            cursor.execute("SELECT extension, width, height FROM images")
            res_rows = cursor.fetchall()

            resolutions_by_ext: dict[str, list[float]] = {}
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
