import json
from sqlite3 import Connection
from typing import Optional

from src.core.repository import AbstractRepository
from src.apps.experemental.boruscraper.domain.models import Project, Post, Resource
from src.apps.experemental.boruscraper.domain.repositories import IProjectRepository, IPostRepository


class SqliteProjectRepository(IProjectRepository, AbstractRepository[Project]):
    def __init__(self, connection: Connection):
        super().__init__()
        self.connection = connection

    def _add(self, aggregate: Project) -> None:
        """Add a new project or update an existing one."""
        cursor = self.connection.cursor()
        
        # Check if it exists
        if aggregate.id:
            cursor.execute(
                "UPDATE projects SET name = ?, settings_json = ?, start_urls_json = ?, current_state = ? WHERE id = ?",
                (
                    aggregate.name,
                    json.dumps(aggregate.settings),
                    json.dumps(aggregate.start_urls),
                    aggregate.current_state,
                    aggregate.id,
                ),
            )
        else:
            cursor.execute(
                "INSERT INTO projects (name, settings_json, start_urls_json, current_state) VALUES (?, ?, ?, ?)",
                (
                    aggregate.name,
                    json.dumps(aggregate.settings),
                    json.dumps(aggregate.start_urls),
                    aggregate.current_state,
                ),
            )
            aggregate.id = cursor.lastrowid

    def _get(self, reference: str) -> Optional[Project]:
        """Get project by ID (reference string)."""
        project_id = int(reference)
        return self.get_by_id(project_id)

    # --- IProjectRepository Implementation ---

    def get(self, project_id: int) -> Optional[Project]:
        return self.get_by_id(project_id)

    def save(self, project: Project) -> None:
        self._add(project)

    def create(self, name: str, settings: dict, start_urls: list) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO projects (name, settings_json, start_urls_json) VALUES (?, ?, ?)",
            (name, json.dumps(settings), json.dumps(start_urls))
        )
        return cursor.lastrowid

    def get_all_projects(self) -> list[dict]:
        self.connection.row_factory = dict_factory
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetch_queued_projects(self) -> list[dict]:
        self.connection.row_factory = dict_factory
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT q.*, p.name 
            FROM project_queue q 
            JOIN projects p ON q.project_id = p.id 
            ORDER BY q.order_index ASC
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_pagination_state(self, project_id: int, start_url: str) -> Optional[dict]:
        self.connection.row_factory = dict_factory
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM pagination_state WHERE project_id = ? AND url = ?", 
            (project_id, start_url)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_pagination_state(self, project_id: int, start_url: str, last_page_url: str, direction: str = "forward") -> None:
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO pagination_state (project_id, url, last_page_url, direction)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_id, url) DO UPDATE SET
                last_page_url = excluded.last_page_url,
                direction = excluded.direction
        ''', (project_id, start_url, last_page_url, direction))

    def delete_pagination_state(self, project_id: int, start_url: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM pagination_state WHERE project_id = ? AND url = ?", (project_id, start_url))

    # --- Existing Helper Methods ---

    def get_by_id(self, project_id: int) -> Optional[Project]:
        self.connection.row_factory = dict_factory
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        if row:
            project = Project(
                id=row["id"],
                name=row["name"],
                settings=json.loads(row["settings_json"]),
                start_urls=json.loads(row["start_urls_json"]),
                current_state=row["current_state"]
            )
            return project
        return None

    def get_all(self) -> list[Project]:
        self.connection.row_factory = dict_factory
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            projects.append(Project(
                id=row["id"],
                name=row["name"],
                settings=json.loads(row["settings_json"]),
                start_urls=json.loads(row["start_urls_json"]),
                current_state=row["current_state"]
            ))
        return projects

    def delete(self, project_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))


class SqlitePostRepository(IPostRepository, AbstractRepository[Post]):
    def __init__(self, connection: Connection):
        super().__init__()
        self.connection = connection

    def _add(self, aggregate: Post) -> None:
        cursor = self.connection.cursor()
        if aggregate.id:
            cursor.execute(
                "UPDATE posts SET project_id = ?, native_id = ?, data_json = ? WHERE id = ?",
                (aggregate.project_id, aggregate.native_id, json.dumps(aggregate.data), aggregate.id)
            )
        else:
            cursor.execute(
                "INSERT INTO posts (project_id, native_id, data_json) VALUES (?, ?, ?)",
                (aggregate.project_id, aggregate.native_id, json.dumps(aggregate.data))
            )
            aggregate.id = cursor.lastrowid
            
        # Also save resources associated with this post
        for res in aggregate.resources:
            cursor.execute(
                "INSERT INTO resources (post_id, file_path, dhash, md5) VALUES (?, ?, ?, ?)",
                (aggregate.id, res.file_path, res.dhash, res.md5)
            )

    def _get(self, reference: str) -> Optional[Post]:
        post_id = int(reference)
        return self.get_by_id(post_id)

    # --- IPostRepository Implementation ---

    def get(self, post_id: str) -> Optional[Post]:
        # Handle string or int IDs
        try:
            return self.get_by_id(int(post_id))
        except ValueError:
            return None

    def save(self, post: Post) -> None:
        self._add(post)

    def get_existing_post_path(self, project_id: int, post_id: str) -> Optional[str]:
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT r.file_path 
            FROM resources r
            JOIN posts p ON r.post_id = p.id
            WHERE p.project_id = ? AND p.native_id = ?
            LIMIT 1
        ''', (project_id, post_id))
        row = cursor.fetchone()
        return row[0] if row else None

    # --- Existing Helper Methods ---

    def get_by_id(self, post_id: int) -> Optional[Post]:
        self.connection.row_factory = dict_factory
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        
        if row:
            post = Post(
                id=row["id"],
                project_id=row["project_id"],
                native_id=row["native_id"],
                data=json.loads(row["data_json"]),
                resources=[]
            )
            
            # get resources
            cursor.execute("SELECT * FROM resources WHERE post_id = ?", (post_id,))
            res_rows = cursor.fetchall()
            for r in res_rows:
                post.add_resource(Resource(
                    file_path=r["file_path"],
                    dhash=r["dhash"],
                    md5=r["md5"]
                ))
            return post
        return None

    def post_exists(self, project_id: int, native_id: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM posts WHERE project_id = ? AND native_id = ?", (project_id, native_id))
        return cursor.fetchone() is not None

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
