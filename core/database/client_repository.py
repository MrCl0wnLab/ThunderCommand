import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .connection import DatabaseConnection, get_db


class ClientRepository:
    """
    Repositório para gerenciamento de clientes no banco de dados.
    
    Esta classe é responsável por todas as operações CRUD (Create, Read, Update, Delete)
    relacionadas aos clientes no sistema Thunder Command.

    Attributes:
        db (DatabaseConnection): Instância de conexão com o banco de dados
    """

    def __init__(self, db_connection: DatabaseConnection = None):
        """
        Inicializa o repositório de clientes.

        Args:
            db_connection (DatabaseConnection, opcional): Conexão com o banco de dados.
                Se não fornecido, uma nova conexão será criada.
        """
        self.db = db_connection or DatabaseConnection()

    def add_client(self, client: Dict[str, Any]) -> None:
        """
        Adiciona um novo cliente ao banco de dados.

        Args:
            client (Dict[str, Any]): Dicionário contendo os dados do cliente.
                Deve conter no mínimo os seguintes campos:
                - id (str): Identificador único do cliente
                - first_seen (str): Data/hora do primeiro contato
                - last_seen (str): Data/hora do último contato
                Campos opcionais:
                - user_agent (str): User-Agent do navegador
                - ip (str): Endereço IP do cliente
                - connection_type (str): Tipo de conexão

        Raises:
            sqlite3.IntegrityError: Se o ID do cliente já existir
            sqlite3.Error: Para outros erros de banco de dados
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

    @staticmethod
    def create_or_update(client_id, **kwargs):
        """Cria ou atualiza um cliente no banco de dados."""
        with get_db() as conn:
            cursor = conn.cursor()

            # Verifica se o cliente já existe
            cursor.execute('SELECT id FROM clients WHERE id = ?', (client_id,))
            exists = cursor.fetchone()

            if exists:
                # Atualiza cliente existente
                update_fields = []
                values = []
                for key, value in kwargs.items():
                    if isinstance(value, dict):
                        value = json.dumps(value)
                    update_fields.append(f"{key} = ?")
                    values.append(value)
                values.append(client_id)

                query = f"UPDATE clients SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, values)
            else:
                # Cria novo cliente
                kwargs['id'] = client_id
                if 'first_seen' not in kwargs:
                    kwargs['first_seen'] = datetime.now().isoformat()

                fields = list(kwargs.keys())
                placeholders = ['?'] * len(fields)
                values = [json.dumps(v) if isinstance(v, dict) else v for v in kwargs.values()]

                query = f"INSERT INTO clients ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(query, values)

    @staticmethod
    def get_by_id(client_id):
        """Obtém um cliente pelo ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if 'screen_info' in data and data['screen_info']:
                    data['screen_info'] = json.loads(data['screen_info'])
                return data
            return None

    @staticmethod
    def get_all(active_only=False):
        """Obtém todos os clientes, opcionalmente apenas os ativos."""
        with get_db() as conn:
            cursor = conn.cursor()
            if active_only:
                cleanup_time = (datetime.now() - timedelta(minutes=30)).isoformat()
                cursor.execute('SELECT * FROM clients WHERE last_seen > ?', (cleanup_time,))
            else:
                cursor.execute('SELECT * FROM clients')

            rows = cursor.fetchall()
            clients = []
            for row in rows:
                data = dict(row)
                if 'screen_info' in data and data['screen_info']:
                    data['screen_info'] = json.loads(data['screen_info'])
                clients.append(data)
            return clients

    @staticmethod
    def delete(client_id):
        """Remove um cliente e seus dados relacionados."""
        with get_db() as conn:
            cursor = conn.cursor()
# socket_clients table removed - HTTP polling only
            cursor.execute('DELETE FROM command_results WHERE client_id = ?', (client_id,))
            cursor.execute('DELETE FROM commands WHERE client_id = ?', (client_id,))
            cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))

# Socket.IO session methods removed - using HTTP polling only



    def increment_commands_received(self, client_id: str) -> None:
        """
        Increment the commands_received counter for a client.

        Args:
            client_id: The unique ID of the client
        """
        self.db.execute("""
            UPDATE clients 
            SET commands_received = commands_received + 1
            WHERE id = ?
        """, (client_id,))

    def increment_command_counters(self, client_id: str, success: bool) -> None:
        """
        Increment success or failure counters for a client.

        Args:
            client_id: The unique ID of the client
            success: Whether to increment successful_commands or failed_commands
        """
        field = "successful_commands" if success else "failed_commands"
        self.db.execute(f"""
            UPDATE clients 
            SET {field} = {field} + 1
            WHERE id = ?
        """, (client_id,))

    def update_activity(self, client_id: str, screen_info: str = None) -> None:
        """
        Update a client's last activity timestamp and optionally screen info.

        Args:
            client_id: The unique ID of the client
            screen_info: Optional screen information to update
        """
        now = datetime.now().isoformat()
        params = {
            'id': client_id,
            'last_activity': now,
            'screen_info': screen_info
        }
        
        if screen_info:
            self.db.execute("""
                UPDATE clients 
                SET last_activity = :last_activity,
                    screen_info = :screen_info
                WHERE id = :id
            """, params)
        else:
            self.db.execute("""
                UPDATE clients 
                SET last_activity = :last_activity
                WHERE id = :id
            """, params)