import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Union, Tuple, Optional


class DatabaseConnection:
    """
    Manages SQLite database connection and provides utility methods for executing queries.
    Designed as a singleton to maintain one connection throughout the application lifecycle.
    """
    _database_name = 'thunder.db'
    _instance = None

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._conn = None
            cls._instance._db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), cls._database_name)
        return cls._instance

    def __init__(self, db_path: str = None):
        # Constructor body intentionally left minimal since initialization occurs in __new__
        pass

    def initialize(self) -> None:
        """Create necessary database tables if they don't exist."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            # Configure connection to return dictionaries instead of tuples
            self._conn.row_factory = sqlite3.Row

        # Create clients table
        self.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                first_seen DATETIME NOT NULL,
                last_seen DATETIME NOT NULL,
                user_agent TEXT,
                ip TEXT,
                connection_type TEXT,
                active BOOLEAN DEFAULT 1
            )
        ''')

        # Create commands table with foreign key to clients
        self.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        ''')

        # Create index for faster client-based command lookups
        self.execute('CREATE INDEX IF NOT EXISTS idx_commands_client ON commands(client_id)')

    def get_connection(self) -> sqlite3.Connection:
        """Returns the SQLite connection object."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def execute(self, sql: str, params: Union[Tuple, Dict] = None) -> sqlite3.Cursor:
        """
        Execute a SQL statement (INSERT, UPDATE, DELETE, CREATE, etc.)
        
        Args:
            sql: The SQL statement to execute
            params: Optional parameters for the SQL statement
            
        Returns:
            The cursor object from the executed statement
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        return cursor

    def query(self, sql: str, params: Union[Tuple, Dict] = None) -> List[Dict]:
        """
        Execute a SELECT query and return results as a list of dictionaries.
        
        Args:
            sql: The SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            List of dictionaries representing the query results
        """
        cursor = self.execute(sql, params)
        results = cursor.fetchall()
        return [dict(row) for row in results]

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None