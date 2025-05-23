from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any, Optional
from .connection import get_db

class CommandRepository:
    """
    Repositório para gerenciamento de comandos no banco de dados.
    
    Esta classe é responsável por todas as operações relacionadas aos comandos
    no sistema Thunder Command, incluindo criação, consulta, atualização de status
    e gerenciamento de resultados de execução.

    O repositório mantém o histórico completo de comandos e seus resultados,
    permitindo rastreamento e análise posterior das operações realizadas.
    """
    
    @staticmethod
    def create(client_id: str, command_type: str, command: str, command_id: str = None) -> Dict[str, Any]:
        """
        Cria um novo comando no banco de dados.
        
        Args:
            client_id (str): Identificador único do cliente que receberá o comando
            command_type (str): Tipo do comando a ser executado.
                Valores possíveis:
                - 'shell': Comandos do sistema operacional
                - 'js': Comandos JavaScript
                - outros tipos conforme configuração
            command (str): Conteúdo do comando a ser executado
            command_id (str, opcional): ID personalizado para o comando.
                Se não fornecido, será gerado um UUID automaticamente
            
        Returns:
            Dict[str, Any]: Dicionário contendo os dados do comando criado:
                - id: Identificador único do comando
                - client_id: ID do cliente
                - command: Conteúdo do comando
                - command_type: Tipo do comando
                - timestamp: Data/hora de criação
                - status: Status inicial do comando ('pending')
        
        Raises:
            sqlite3.IntegrityError: Se houver violação de chave estrangeira
            sqlite3.Error: Para outros erros de banco de dados
        """
        if not command_id:
            command_id = str(uuid.uuid4())
            
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO commands (id, client_id, command, command_type, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (command_id, client_id, command, command_type, 'pending', now))
            
            # Atualiza a contagem de comandos recebidos do cliente
            cursor.execute('''
                UPDATE clients 
                SET commands_received = commands_received + 1
                WHERE id = ?
            ''', (client_id,))
            
            return {
                'id': command_id,
                'client_id': client_id,
                'command': command,
                'command_type': command_type,
                'timestamp': now
            }
    
    @staticmethod
    def get_by_id(command_id):
        """Obtém um comando pelo ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, 
                       COUNT(cr.id) as total_executions,
                       SUM(CASE WHEN cr.success THEN 1 ELSE 0 END) as success_count,
                       SUM(CASE WHEN NOT cr.success THEN 1 ELSE 0 END) as error_count
                FROM commands c
                LEFT JOIN command_results cr ON c.id = cr.command_id
                WHERE c.id = ?
                GROUP BY c.id
            ''', (command_id,))
            row = cursor.fetchone()
            if row:
                command = dict(row)
                
                # Obtém resultados do comando
                cursor.execute('''
                    SELECT * FROM command_results
                    WHERE command_id = ?
                    ORDER BY timestamp DESC
                ''', (command_id,))
                results = [dict(r) for r in cursor.fetchall()]
                command['results'] = results
                command['last_result'] = results[0] if results else None
                
                return command
            return None
    
    @staticmethod
    def get_client_command(client_id):
        """Obtém o comando atual para um cliente."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM commands
                WHERE client_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (client_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_logs(limit=100):
        """Obtém o histórico de comandos com seus resultados."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*,
                       COUNT(cr.id) as total_executions,
                       SUM(CASE WHEN cr.success THEN 1 ELSE 0 END) as success_count,
                       SUM(CASE WHEN NOT cr.success THEN 1 ELSE 0 END) as error_count
                FROM commands c
                LEFT JOIN command_results cr ON c.id = cr.command_id
                GROUP BY c.id
                ORDER BY c.timestamp DESC
                LIMIT ?
            ''', (limit,))
            commands = []
            for row in cursor.fetchall():
                command = dict(row)
                
                # Obtém resultados do comando
                cursor.execute('''
                    SELECT * FROM command_results
                    WHERE command_id = ?
                    ORDER BY timestamp DESC
                ''', (command['id'],))
                results = [dict(r) for r in cursor.fetchall()]
                command['results'] = results
                command['last_result'] = results[0] if results else None
                
                commands.append(command)
            
            return commands
    
    @staticmethod
    def add_result(command_id, client_id, success, result=None, execution_time=0):
        """Adiciona um resultado de execução para um comando."""
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO command_results 
                (command_id, client_id, success, result, execution_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (command_id, client_id, success, result, execution_time, now))
            
            # Atualiza contadores do cliente
            if success:
                cursor.execute('''
                    UPDATE clients 
                    SET successful_commands = successful_commands + 1
                    WHERE id = ?
                ''', (client_id,))
            else:
                cursor.execute('''
                    UPDATE clients 
                    SET failed_commands = failed_commands + 1
                    WHERE id = ?
                ''', (client_id,))
    
    @staticmethod
    def delete_client_commands(client_id: str) -> None:
        """
        Deleta todos os comandos e seus resultados para um determinado cliente.
        
        Args:
            client_id: O cliente cujos comandos devem ser deletados
        """
        with get_db() as conn:
            cursor = conn.cursor()
            # Primeiro deleta os resultados devido à restrição de chave estrangeira
            cursor.execute(
                "DELETE FROM command_results WHERE client_id = ?",
                (client_id,)
            )
            # Depois deleta os comandos
            cursor.execute(
                "DELETE FROM commands WHERE client_id = ?",
                (client_id,)
            )

    @staticmethod
    def clear_old_commands(days: int = 7) -> int:
        """
        Deleta comandos e seus resultados mais antigos do que o número de dias especificado.
        
        Args:
            days: Número de dias de histórico para manter
            
        Returns:
            Número de comandos deletados
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Primeiro deleta os resultados antigos
            cursor.execute("""
                DELETE FROM command_results 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            # Depois deleta os comandos antigos
            cursor.execute("""
                DELETE FROM commands 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            return cursor.rowcount