from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from .connection import DatabaseConnection


class CommandRepository:
    """
    Repository class for managing command data in the database.
    Handles all CRUD operations for commands and command logs.
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def save_command(self, command: Dict[str, Any]) -> int:
        """
        Save a new command to the database.
        
        Args:
            command: Dictionary containing command data with at minimum:
                    client_id, type, and content fields
        
        Returns:
            The ID of the newly created command
        """
        now = datetime.now().isoformat()
        cursor = self.db.execute(
            """
            INSERT INTO commands (client_id, type, content, created_at, status)
            VALUES (:client_id, :type, :content, :created_at, :status)
            """,
            {
                'client_id': command['client_id'],
                'type': command['type'],
                'content': command['content'],
                'created_at': command.get('created_at', now),
                'status': command.get('status', 'pending')
            }
        )
        return cursor.lastrowid

    def get_command(self, command_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a command by its ID.
        
        Args:
            command_id: The unique ID of the command
            
        Returns:
            Dictionary containing command data or None if not found
        """
        result = self.db.query("SELECT * FROM commands WHERE id = ?", (command_id,))
        return result[0] if result else None

    def get_last_command(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent command for a specific client.
        
        Args:
            client_id: The ID of the client to get commands for
            
        Returns:
            Dictionary containing the most recent command data or None if none exists
        """
        result = self.db.query(
            """
            SELECT * FROM commands 
            WHERE client_id = ? AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1
            """,
            (client_id,)
        )
        return result[0] if result else None

    def get_commands_by_client(self, client_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all commands for a specific client, with an optional limit.
        
        Args:
            client_id: The ID of the client to get commands for
            limit: Optional maximum number of commands to return
            
        Returns:
            List of dictionaries containing command data
        """
        sql = "SELECT * FROM commands WHERE client_id = ? ORDER BY created_at DESC"
        if limit:
            sql += f" LIMIT {limit}"
        
        return self.db.query(sql, (client_id,))

    def list_commands(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all commands across all clients, with an optional limit.
        
        Args:
            limit: Optional maximum number of commands to return
            
        Returns:
            List of dictionaries containing command data
        """
        sql = "SELECT * FROM commands ORDER BY created_at DESC"
        if limit:
            sql += f" LIMIT {limit}"
        
        return self.db.query(sql)

    def update_command_status(self, command_id: int, status: str) -> None:
        """
        Update the status of a command.
        
        Args:
            command_id: The ID of the command to update
            status: The new status ('pending', 'executed', 'failed', etc.)
        """
        self.db.execute(
            "UPDATE commands SET status = ? WHERE id = ?",
            (status, command_id)
        )

    def clear_old_commands(self, max_commands: int = 100) -> int:
        """
        Remove older commands keeping only the most recent 'max_commands'.
        
        Args:
            max_commands: Maximum number of commands to retain
            
        Returns:
            Number of commands deleted
        """
        cursor = self.db.execute(
            """
            DELETE FROM commands
            WHERE id NOT IN (
                SELECT id FROM commands
                ORDER BY created_at DESC
                LIMIT ?
            )
            """,
            (max_commands,)
        )
        return cursor.rowcount