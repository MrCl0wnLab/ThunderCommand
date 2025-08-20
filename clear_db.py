from core.database.connection import get_db
from core.database import init_db
from core.database.client_repository import ClientRepository
from core.database.command_repository import CommandRepository
import sqlite3
import uuid
from datetime import datetime

def clear_database():
    """Limpa todas as tabelas do banco de dados e reinicia com valores padrão"""
    print("Limpando banco de dados...")
    
    # Primeiro, limpar todas as tabelas dentro de uma transação
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Desativar temporariamente as restrições de chave estrangeira
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Limpar todas as tabelas na ordem correta
        print("Removendo dados da tabela command_results...")
        cursor.execute("DELETE FROM command_results")
        
        print("Removendo dados da tabela commands...")
        cursor.execute("DELETE FROM commands")
        
        # socket_clients table removed - HTTP polling only
        
        print("Removendo dados da tabela clients...")
        cursor.execute("DELETE FROM clients")
        
        # Reativar restrições de chave estrangeira
        cursor.execute("PRAGMA foreign_keys = ON")
    
    # Agora execute VACUUM fora da transação
    print("Otimizando banco de dados (VACUUM)...")
    # Conectar diretamente ao banco de dados para executar VACUUM
    conn = sqlite3.connect('thunder_command.db')
    conn.isolation_level = None  # Desativar auto-commit para permitir VACUUM
    conn.execute("VACUUM")
    conn.close()
        
    print("Recriando comando padrão...")
    # Criar comando padrão (similar ao que é feito em app.py)
    default_command = {
        "id": str(uuid.uuid4()),
        "command": "",
        "timestamp": datetime.now().isoformat()
    }
    CommandRepository().create('default', 'js', '', default_command['id'])
        
    print("Limpeza do banco de dados concluída!")

if __name__ == "__main__":
    # Garantir que o banco de dados está inicializado
    init_db()
    
    # Limpar banco de dados
    clear_database()