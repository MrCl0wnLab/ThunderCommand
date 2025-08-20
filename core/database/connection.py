from datetime import datetime
import os
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Union, Tuple, Optional


DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'thunder_command.db')

class DatabaseConnection:
    """
    Gerenciador de conexão com o banco de dados SQLite.
    
    Esta classe implementa o padrão Singleton para garantir uma única
    conexão com o banco de dados durante toda a execução do aplicativo.
    
    A conexão é thread-safe e configurada para retornar resultados
    como objetos sqlite3.Row, permitindo acesso aos dados por nome
    de coluna.

    Attributes:
        _instance (DatabaseConnection): Instância única da classe
        _conn (sqlite3.Connection): Objeto de conexão com o banco
    """
    _instance = None

    def __new__(cls):
        """
        Implementa o padrão Singleton para garantir uma única instância.
        
        Returns:
            DatabaseConnection: Instância única da classe
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """
        Obtém a conexão com o banco de dados SQLite.
        
        Se não houver uma conexão ativa, cria uma nova.
        A conexão é configurada para ser thread-safe e
        retornar resultados como objetos Row.
        
        Returns:
            sqlite3.Connection: Objeto de conexão com o banco
        """
        if self._conn is None:
            self._conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def execute(self, sql: str, params: Union[Tuple, Dict] = None) -> sqlite3.Cursor:
        """
        Executa uma consulta SQL com parâmetros.
        
        Args:
            sql (str): Query SQL a ser executada
            params (Union[Tuple, Dict], opcional): Parâmetros para
                substituir na query. Pode ser uma tupla para ? ou
                um dicionário para :name
        
        Returns:
            sqlite3.Cursor: Cursor para manipular os resultados
        
        Raises:
            sqlite3.Error: Em caso de erro na execução da query
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
        """Execute a query and return results as dictionaries"""
        cursor = self.execute(sql, params)
        results = cursor.fetchall()
        return [dict(row) for row in results]

    def close(self) -> None:
        """Close the database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None

@contextmanager
def get_db():
    """
    Gerenciador de contexto para conexões com o banco de dados.
    
    Fornece uma conexão SQLite configurada e gerencia automaticamente
    o commit/rollback e fechamento da conexão.
    
    Yields:
        sqlite3.Connection: Conexão configurada com o banco de dados
        
    Example:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients")
            results = cursor.fetchall()
    
    Raises:
        Exception: Qualquer exceção durante as operações no banco
            resultará em rollback automático
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """
    Inicializa o esquema do banco de dados.
    
    Cria todas as tabelas necessárias se elas não existirem:
    - clients: Armazena informações dos clientes conectados
    - commands: Registra comandos enviados aos clientes
    - command_results: Armazena resultados da execução dos comandos
    
    Também cria índices para otimizar consultas frequentes.
    
    Raises:
        sqlite3.Error: Em caso de erro na criação das tabelas
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create clients table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            last_activity TEXT NOT NULL,
            user_agent TEXT,
            ip TEXT,
            connection_type TEXT,
            commands_received INTEGER DEFAULT 0,
            successful_commands INTEGER DEFAULT 0,
            failed_commands INTEGER DEFAULT 0,
            screen_info TEXT
        )""")
        
        # Create commands table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            command TEXT NOT NULL,
            command_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )""")
        
        # Create command_results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_results (
            id TEXT PRIMARY KEY,
            command_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            result TEXT,
            execution_time REAL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (command_id) REFERENCES commands (id),
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )""")
        
# socket_clients table removed - no longer using WebSocket/Socket.IO
        
        # Create indices for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_client ON commands(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_results_command ON command_results(command_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_results_client ON command_results(client_id)')

__all__ = ['DatabaseConnection', 'get_db', 'init_db']