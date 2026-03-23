import sqlite3
from typing import Any, Dict, List, Optional, Union

class SqliteRepositoryBase:
    """Base class for SQLite repositories that provides safe row access.
    
    This class addresses common pitfalls when working with `sqlite3.Row` objects,
    such as the absence of a `.get()` method. It provides utility methods
    for safe field retrieval and dictionary conversion.
    """
    
    @staticmethod
    def row_to_dict(row: Union[sqlite3.Row, dict, Any]) -> Dict[str, Any]:
        """Convert a sqlite3.Row or any row-like object to a standard dictionary.
        
        Args:
            row: The row object to convert. Can be a sqlite3.Row, dict, or None.
            
        Returns:
            A dictionary representation of the row. Returns empty dict if row is None.
        """
        if row is None:
            return {}
        if isinstance(row, dict):
            return row
        try:
            return dict(row)
        except (TypeError, ValueError):
            # Fallback for objects that might not be dict-convertible but have keys
            if hasattr(row, 'keys'):
                return {k: row[k] for k in row.keys()}
            return {}

    @staticmethod
    def get_field(row: Any, key: str, default: Any = None) -> Any:
        """Safely get a field from a row with a default value.
        
        Args:
            row: The row object (sqlite3.Row, dict, etc.).
            key: The field name to retrieve.
            default: Value to return if the key is not found or row is None.
            
        Returns:
            The value of the field or the default value.
        """
        if row is None:
            return default
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default

    def __init__(self, connection: Optional[sqlite3.Connection] = None):
        """Initialize the repository base.
        
        Args:
            connection: Optional active sqlite3 connection.
        """
        self._connection = connection

    def set_connection(self, connection: sqlite3.Connection):
        """Set the active database connection and configure it.
        
        Args:
            connection: The sqlite3 connection to use.
        """
        self._connection = connection
        # Ensure row_factory is set to Row for consistent access
        if self._connection:
            self._connection.row_factory = sqlite3.Row
