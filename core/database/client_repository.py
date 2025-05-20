from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .connection import DatabaseConnection


class ClientRepository:
    """
    Repository class for managing client data in the database.
    Handles all CRUD operations for clients.
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def add_client(self, client: Dict[str, Any]) -> None:
        """
        Add a new client to the database.
        
        Args:
            client: Dictionary containing client data with at minimum:
                   id, first_seen, and last_seen fields
        """
        now = datetime.now().isoformat()
        self.db.execute(
            """
            INSERT INTO clients (id, first_seen, last_seen, user_agent, ip, connection_type)
            VALUES (:id, :first_seen, :last_seen, :user_agent, :ip, :connection_type)
            """,
            {
                'id': client['id'],
                'first_seen': client.get('first_seen', now),
                'last_seen': client.get('last_seen', now),
                'user_agent': client.get('user_agent'),
                'ip': client.get('ip'),
                'connection_type': client.get('connection_type')
            }
        )

    def update_client(self, client: Dict[str, Any]) -> None:
        """
        Update an existing client in the database.
        
        Args:
            client: Dictionary containing client data with at minimum:
                   id and fields to update
        """
        self.db.execute(
            """
            UPDATE clients
            SET last_seen = :last_seen,
                user_agent = COALESCE(:user_agent, user_agent),
                ip = COALESCE(:ip, ip),
                connection_type = COALESCE(:connection_type, connection_type),
                active = :active
            WHERE id = :id
            """,
            {
                'id': client['id'],
                'last_seen': client.get('last_seen', datetime.now().isoformat()),
                'user_agent': client.get('user_agent'),
                'ip': client.get('ip'),
                'connection_type': client.get('connection_type'),
                'active': client.get('active', 1)
            }
        )

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get client information by its ID.
        
        Args:
            client_id: The unique ID of the client
            
        Returns:
            Dictionary containing client data or None if not found
        """
        result = self.db.query("SELECT * FROM clients WHERE id = ?", (client_id,))
        return result[0] if result else None

    def list_clients(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get a list of all clients, optionally filtering for active clients only.
        A client is considered active if they've been seen in the last 30 minutes.
        
        Args:
            active_only: If True, only return clients active in the last 30 minutes
            
        Returns:
            List of dictionaries containing client data
        """
        if active_only:
            # Calculate timestamp for 30 minutes ago
            threshold = (datetime.now() - timedelta(minutes=30)).isoformat()
            return self.db.query(
                "SELECT * FROM clients WHERE last_seen >= ? ORDER BY last_seen DESC",
                (threshold,)
            )
        else:
            return self.db.query("SELECT * FROM clients ORDER BY last_seen DESC")

    def delete_client(self, client_id: str) -> None:
        """
        Delete a client and all associated commands by its ID.
        The ON DELETE CASCADE in the database schema will handle
        deletion of associated commands.
        
        Args:
            client_id: The unique ID of the client to delete
        """
        self.db.execute("DELETE FROM clients WHERE id = ?", (client_id,))

    def mark_clients_inactive(self, timeout_minutes: int = 30) -> int:
        """
        Mark clients as inactive if they haven't been seen in a specified time period.
        
        Args:
            timeout_minutes: Number of minutes of inactivity to consider a client inactive
            
        Returns:
            Number of clients marked as inactive
        """
        threshold = (datetime.now() - timedelta(minutes=timeout_minutes)).isoformat()
        cursor = self.db.execute(
            """
            UPDATE clients 
            SET active = 0
            WHERE last_seen < ? AND active = 1
            """,
            (threshold,)
        )
        return cursor.rowcount