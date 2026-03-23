import sqlite3
import json
import os
from typing import List, Dict, Optional, Any, Tuple, Callable
from loguru import logger

class DatabaseManager:
    def __init__(self, db_path: str = "data.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # --- Projects Table ---
        # settings_json: contains delays, selectors, etc.
        # current_state: 'active', 'paused', 'finished'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                settings_json TEXT,
                start_urls_json TEXT,
                current_state TEXT DEFAULT 'active'
            )
        ''')

        # --- Pagination State Table ---
        # Tracks progress for each URL in a project
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagination_state (
                project_id INTEGER,
                url TEXT,
                last_page_url TEXT,
                direction TEXT DEFAULT 'forward',
                PRIMARY KEY (project_id, url),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')

        # --- Project Queue Table ---
        # order_index determines the execution order
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                order_index INTEGER,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')

        # --- Posts Table ---
        # native_id: ID from the source site (e.g., rule34 id)
        # data_json: Full scraped data (tags, raw fields)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                native_id TEXT,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, native_id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
        ''')

        # --- Resources Table ---
        # path: relative path to the file
        # dhash: perceptual hash for deduplication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                file_path TEXT,
                dhash TEXT,
                md5 TEXT,
                FOREIGN KEY(post_id) REFERENCES posts(id)
            )
        ''')
        
        # Index on dhash for faster global deduplication checks
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_dhash ON resources(dhash)')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    # --- Project Methods ---
    def create_project(self, name: str, settings: Dict, start_urls: List[str]) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO projects (name, settings_json, start_urls_json) VALUES (?, ?, ?)",
                (name, json.dumps(settings), json.dumps(start_urls))
            )
            project_id = cursor.lastrowid
            conn.commit()
            return project_id
        except sqlite3.IntegrityError:
            logger.error(f"Project with name '{name}' already exists.")
            return -1
        finally:
            conn.close()

    def get_all_projects(self) -> List[Dict]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_project_settings(self, project_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT settings_json FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None
        
    def get_project_name(self, project_id: int) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    # --- Queue Methods ---
    def add_to_queue(self, project_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        # Get max index
        cursor.execute("SELECT MAX(order_index) FROM project_queue")
        result = cursor.fetchone()
        next_index = (result[0] or 0) + 1
        
        cursor.execute(
            "INSERT INTO project_queue (project_id, order_index, status) VALUES (?, ?, ?)",
            (project_id, next_index, 'pending')
        )
        conn.commit()
        conn.close()

    def get_queue(self) -> List[Dict]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT q.*, p.name 
            FROM project_queue q 
            JOIN projects p ON q.project_id = p.id 
            ORDER BY q.order_index ASC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def move_queue_item_to_end(self, queue_id: int):
        """Moves a queue item to the end (looping behavior)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(order_index) FROM project_queue")
        max_idx = cursor.fetchone()[0] or 0
        
        cursor.execute("UPDATE project_queue SET order_index = ?, status = 'pending' WHERE id = ?", (max_idx + 1, queue_id))
        conn.commit()
        conn.close()

    def update_queue_index(self, queue_id: int, new_index: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE project_queue SET order_index = ? WHERE id = ?", (new_index, queue_id))
        conn.commit()
        conn.close()

    def move_project_to_end_of_queue(self, project_id: int):
        """Finds the queue item for the project and moves it to the end."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Find queue id
            cursor.execute("SELECT id FROM project_queue WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                queue_id = row[0]
                # Get max index
                cursor.execute("SELECT MAX(order_index) FROM project_queue")
                max_idx = cursor.fetchone()[0] or 0
                
                cursor.execute("UPDATE project_queue SET order_index = ?, status = 'pending' WHERE id = ?", (max_idx + 1, queue_id))
                conn.commit()
        finally:
            conn.close()

    # --- Pagination Methods ---
    def get_pagination_state(self, project_id: int, url: str) -> Optional[Dict]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM pagination_state WHERE project_id = ? AND url = ?", 
            (project_id, url)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_pagination_state(self, project_id: int, url: str, last_page_url: str, direction: str = 'forward'):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pagination_state (project_id, url, last_page_url, direction)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_id, url) DO UPDATE SET
                last_page_url = excluded.last_page_url,
                direction = excluded.direction
        ''', (project_id, url, last_page_url, direction))
        conn.commit()
        conn.close()

    def delete_pagination_state(self, project_id: int, url: str):
        """Clears pagination state for a specific start URL."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pagination_state WHERE project_id = ? AND url = ?", (project_id, url))
        conn.commit()
        conn.close()

    # --- Resource / Deduplication Methods ---
    def check_dhash_exists(self, dhash: str, exclude_project_id: int) -> List[Dict]:
        """
        Check if dhash exists in ANY project OTHER than the current one.
        Returns list of conflicting resources.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Find matches with small hamming distance (exact match for string for now, 
        # but logic should ideally handle hamming distance in python or extension)
        # For simplicity, we query exact matches here.
        cursor.execute('''
            SELECT r.*, p.name as project_name, p.settings_json
            FROM resources r
            JOIN posts post ON r.post_id = post.id
            JOIN projects p ON post.project_id = p.id
            WHERE r.dhash = ? AND p.id != ?
        ''', (dhash, exclude_project_id))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            d = dict(row)
            try:
                settings = json.loads(d.get("settings_json", "{}"))
                d["save_path"] = settings.get("save_path")
            except:
                d["save_path"] = None
            results.append(d)
        return results

    def get_all_other_hashes(self, exclude_project_id: int) -> List[Dict]:
        """
        Fetch all dhashes from other projects for efficient in-memory comparison.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.dhash, r.file_path as relative_path, p.id as project_id, p.name as project_name, p.settings_json
            FROM resources r
            JOIN posts post ON r.post_id = post.id
            JOIN projects p ON post.project_id = p.id
            WHERE p.id != ? AND r.dhash IS NOT NULL
        ''', (exclude_project_id,))
        rows = cursor.fetchall()
        conn.close()
        
        # Optimization: Parse settings once per project
        project_paths = {}
        results = []
        for row in rows:
            d = dict(row)
            pid = d['project_id']
            if pid not in project_paths:
                try:
                    s = json.loads(d.get('settings_json', '{}'))
                    project_paths[pid] = s.get('save_path')
                except:
                    project_paths[pid] = None
            
            d['save_path'] = project_paths[pid]
            # Remove heavy json string from result to save memory
            d.pop('settings_json', None) 
            results.append(d)
            
        return results

    def save_post(self, project_id: int, native_id: str, data: Dict) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (project_id, native_id, data_json)
            VALUES (?, ?, ?)
            ON CONFLICT(project_id, native_id) DO UPDATE SET data_json = excluded.data_json
        ''', (project_id, native_id, json.dumps(data)))
        
        # Get the ID (whether inserted or updated)
        if cursor.rowcount == 0: # It was an ignore, or update didn't change anything? 
             # On CONFLICT UPDATE should usually return rowid if using RETURNING, but for compatibility:
             cursor.execute("SELECT id FROM posts WHERE project_id = ? AND native_id = ?", (project_id, native_id))
             post_id = cursor.fetchone()[0]
        else:
             post_id = cursor.lastrowid if cursor.lastrowid else cursor.execute("SELECT id FROM posts WHERE project_id = ? AND native_id = ?", (project_id, native_id)).fetchone()[0]

        conn.commit()
        conn.close()
        return post_id

    def post_exists(self, project_id: int, native_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM posts WHERE project_id = ? AND native_id = ?", (project_id, native_id))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_existing_post_path(self, project_id: int, native_id: str) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.file_path 
            FROM resources r
            JOIN posts p ON r.post_id = p.id
            WHERE p.project_id = ? AND p.native_id = ?
            LIMIT 1
        ''', (project_id, native_id))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def save_resource(self, post_id: int, file_path: str, dhash: str, md5: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO resources (post_id, file_path, dhash, md5) VALUES (?, ?, ?, ?)",
            (post_id, file_path, dhash, md5)
        )
        conn.commit()
        conn.close()

    def update_project_settings(self, project_id: int, settings: str):
        """Updates the settings JSON for a project."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE projects SET settings_json = ? WHERE id = ?",
            (settings, project_id)
        )
        conn.commit()
        conn.close()

    def delete_project(self, project_id: int):
        """Deletes a project and all associated data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Delete resources (via posts)
            cursor.execute('''
                DELETE FROM resources 
                WHERE post_id IN (SELECT id FROM posts WHERE project_id = ?)
            ''', (project_id,))
            
            # Delete posts
            cursor.execute("DELETE FROM posts WHERE project_id = ?", (project_id,))
            
            # Delete queue items
            cursor.execute("DELETE FROM project_queue WHERE project_id = ?", (project_id,))
            
            # Delete pagination state
            cursor.execute("DELETE FROM pagination_state WHERE project_id = ?", (project_id,))
            
            # Delete project
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            
            conn.commit()
            logger.info(f"Project {project_id} deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            conn.rollback()
        finally:
            conn.close()

    # --- Export / Import Methods ---
    def export_project(self, project_id: int, file_path: str) -> bool:
        """Exports a project and its data to a separate SQLite file."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logger.error(f"Failed to overwrite export file: {e}")
                return False

        # Create new DB and Schema
        export_db = DatabaseManager(file_path)
        
        source_conn = self._get_connection()
        source_conn.row_factory = sqlite3.Row
        s_cursor = source_conn.cursor()
        
        dest_conn = export_db._get_connection()
        d_cursor = dest_conn.cursor()
        
        try:
            # 1. Project Info
            s_cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project_row = s_cursor.fetchone()
            if not project_row:
                logger.error(f"Project {project_id} not found for export")
                return False
                
            # Insert with ID to preserve internal consistency of the export file
            # (Though on import we will ignore the ID)
            d_cursor.execute(
                "INSERT INTO projects (id, name, settings_json, start_urls_json, current_state) VALUES (?, ?, ?, ?, ?)",
                (project_row['id'], project_row['name'], project_row['settings_json'], 
                 project_row['start_urls_json'], project_row['current_state'])
            )
            
            # 2. Pagination State
            s_cursor.execute("SELECT * FROM pagination_state WHERE project_id = ?", (project_id,))
            pag_rows = s_cursor.fetchall()
            d_cursor.executemany(
                "INSERT INTO pagination_state (project_id, url, last_page_url, direction) VALUES (?, ?, ?, ?)",
                [(r['project_id'], r['url'], r['last_page_url'], r['direction']) for r in pag_rows]
            )
            
            # 3. Posts & Resources
            # We iterate posts to handle resources
            s_cursor.execute("SELECT * FROM posts WHERE project_id = ?", (project_id,))
            post_rows = s_cursor.fetchall()
            
            for post in post_rows:
                d_cursor.execute(
                    "INSERT INTO posts (id, project_id, native_id, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
                    (post['id'], post['project_id'], post['native_id'], post['data_json'], post['created_at'])
                )
                
                # Resources for this post
                s_cursor.execute("SELECT * FROM resources WHERE post_id = ?", (post['id'],))
                res_rows = s_cursor.fetchall()
                d_cursor.executemany(
                    "INSERT INTO resources (id, post_id, file_path, dhash, md5) VALUES (?, ?, ?, ?, ?)",
                    [(r['id'], r['post_id'], r['file_path'], r['dhash'], r['md5']) for r in res_rows]
                )

            dest_conn.commit()
            logger.info(f"Exported project {project_id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            dest_conn.rollback()
            return False
        finally:
            source_conn.close()
            dest_conn.close()

    def import_project(self, file_path: str, conflict_callback: Optional[Callable[[str], str]] = None) -> bool:
        """
        Imports key project data from an exported SQLite file.
        conflict_callback(name) -> 'merge' | 'rename' | 'skip'
        """
        if not os.path.exists(file_path):
            logger.error(f"Import file not found: {file_path}")
            return False
            
        source_conn = sqlite3.connect(file_path)
        source_conn.row_factory = sqlite3.Row
        s_cursor = source_conn.cursor()
        
        dest_conn = self._get_connection()
        d_cursor = dest_conn.cursor()
        
        new_project_ids = []

        try:
            # 1. Read Projects from Source
            s_cursor.execute("SELECT * FROM projects")
            projects = s_cursor.fetchall()
            
            for proj in projects:
                original_name = proj['name']
                old_project_id = proj['id']
                
                # Check exist
                d_cursor.execute("SELECT id FROM projects WHERE name = ?", (original_name,))
                existing_row = d_cursor.fetchone()
                
                target_pid = None
                is_new_project = True 
                
                if existing_row:
                    decision = 'rename' # Default
                    if conflict_callback:
                        decision = conflict_callback(original_name)
                    
                    if decision == 'skip':
                        logger.info(f"Skipping import of '{original_name}'")
                        continue
                    elif decision == 'merge':
                        target_pid = existing_row['id']
                        is_new_project = False
                        logger.info(f"Merging '{original_name}' into existing project ID {target_pid}")
                    # else rename
                
                if is_new_project:
                    # Determine Name
                    new_name = original_name
                    counter = 1
                    while True:
                        d_cursor.execute("SELECT 1 FROM projects WHERE name = ?", (new_name,))
                        if not d_cursor.fetchone():
                            break
                        new_name = f"{original_name}_imported_{counter}"
                        counter += 1
                        
                    # Insert Project
                    d_cursor.execute(
                        "INSERT INTO projects (name, settings_json, start_urls_json, current_state) VALUES (?, ?, ?, ?)",
                        (new_name, proj['settings_json'], proj['start_urls_json'], proj['current_state'])
                    )
                    target_pid = d_cursor.lastrowid
                    new_project_ids.append(target_pid)
                    logger.info(f"Importing project '{original_name}' as '{new_name}' (ID: {target_pid})")

                # --- Insert Data into target_pid ---
                
                # 2. Pagination State (Merge: INSERT OR IGNORE)
                s_cursor.execute("SELECT * FROM pagination_state WHERE project_id = ?", (old_project_id,))
                pag_rows = s_cursor.fetchall()
                d_cursor.executemany(
                    "INSERT OR IGNORE INTO pagination_state (project_id, url, last_page_url, direction) VALUES (?, ?, ?, ?)",
                    [(target_pid, r['url'], r['last_page_url'], r['direction']) for r in pag_rows]
                )
                
                # 3. Posts (Merge: INSERT OR IGNORE)
                s_cursor.execute("SELECT * FROM posts WHERE project_id = ?", (old_project_id,))
                posts = s_cursor.fetchall()
                
                for post in posts:
                    # Attempt Insert
                    d_cursor.execute(
                        "INSERT OR IGNORE INTO posts (project_id, native_id, data_json, created_at) VALUES (?, ?, ?, ?)",
                        (target_pid, post['native_id'], post['data_json'], post['created_at'])
                    )
                    
                    # Need the actual ID (whether inserted or existing)
                    if d_cursor.rowcount > 0:
                        current_post_id = d_cursor.lastrowid
                    else:
                        d_cursor.execute("SELECT id FROM posts WHERE project_id = ? AND native_id = ?", (target_pid, post['native_id']))
                        current_post_id = d_cursor.fetchone()[0]
                    
                    # Resources
                    s_cursor.execute("SELECT * FROM resources WHERE post_id = ?", (post['id'],))
                    resources = s_cursor.fetchall()
                    
                    d_cursor.executemany(
                        "INSERT OR IGNORE INTO resources (post_id, file_path, dhash, md5) VALUES (?, ?, ?, ?)",
                        [(current_post_id, r['file_path'], r['dhash'], r['md5']) for r in resources]
                    )
                
            dest_conn.commit()
        except Exception as e:
            logger.error(f"Import failed: {e}")
            dest_conn.rollback()
            return False
        finally:
            source_conn.close()
            dest_conn.close()
        
        # Add NEW projects to queue
        for pid in new_project_ids:
            self.add_to_queue(pid)
            
        return True
