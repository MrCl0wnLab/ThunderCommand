from app.models.command import Command, CommandType
from core.utils.logger import command_logger, log_command
from core.database.command_repository import CommandRepository
import json
import html

class CommandExecutor:
    def __init__(self):
        self.command_repo = CommandRepository()
    
    def create_command(self, client_id, command_type, content):
        """Cria e registra um novo comando"""
        # Validar o tipo de comando
        if command_type not in [t.value for t in CommandType]:
            raise ValueError(f"Invalid command type: {command_type}")
        
        # Criar objeto de comando
        command = Command.create(client_id, command_type, content)
        
        # Persistir no repositório
        self.command_repo.create(
            client_id=client_id,
            command_type=command_type,
            command_content=content,
            command_id=command.id
        )
        
        # Registrar log
        log_command(client_id, command_type, content, command.id)
        command_logger.info(f"Command created: {command.id} for client {client_id}")
        
        return command.id
    
    def generate_manipulation_command(self, target_id, action, content):
        """Gera comandos JavaScript seguros para manipulação DOM"""
        # Sanitizar e validar parâmetros
        target_id = html.escape(target_id)
        content = content  # A sanitização não deve ser feita aqui para preservar HTML válido
        
        valid_actions = ['ADD', 'REPLACE', 'INSERT_AFTER', 'INSERT_BEFORE']
        if action not in valid_actions:
            raise ValueError(f"Invalid DOM manipulation action: {action}")
        
        # Construir comando de manipulação
        manipulation_command = {
            'type': 'manipulate',
            'target_id': target_id,
            'action': action,
            'content': content
        }
        
        return json.dumps(manipulation_command)
    
    def generate_visibility_command(self, target_id, is_visible):
        """Gera comando para alterar visibilidade de elementos"""
        # Sanitizar parâmetros
        target_id = html.escape(target_id)
        
        # Construir comando de visibilidade
        visibility_command = {
            'type': 'visibility',
            'target_id': target_id,
            'is_visible': bool(is_visible)
        }
        
        return json.dumps(visibility_command)
    
    def get_pending_command(self, client_id):
        """Obtém o próximo comando pendente para um cliente"""
        command_data = self.command_repo.get_pending(client_id)
        
        if not command_data:
            return None
            
        return Command.from_dict(command_data)
    
    def mark_command_executed(self, command_id, result):
        """Marca um comando como executado com seu resultado"""
        self.command_repo.update_status(command_id, True, result)
        command_logger.info(f"Command {command_id} marked as executed")
