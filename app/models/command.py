from dataclasses import dataclass
from datetime import datetime
import uuid
from enum import Enum

class CommandType(Enum):
    JAVASCRIPT = 'js'
    HTML = 'html'
    MANIPULATE = 'manipulate'
    VISIBILITY = 'visibility'
    HEAD = 'head'

@dataclass
class Command:
    id: str
    client_id: str
    command_type: str
    content: str
    timestamp: datetime
    executed: bool = False
    result: dict = None
    
    @classmethod
    def create(cls, client_id, command_type, content):
        """Cria um novo comando com ID único"""
        # Validar tipo de comando
        if command_type not in [t.value for t in CommandType]:
            raise ValueError(f"Invalid command type: {command_type}")
            
        return cls(
            id=str(uuid.uuid4()),
            client_id=client_id,
            command_type=command_type,
            content=content,
            timestamp=datetime.now()
        )
    
    def mark_executed(self, result=None):
        """Marca o comando como executado com resultado opcional"""
        self.executed = True
        self.result = result
    
    def to_dict(self):
        """Converte o comando para um dicionário"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'type': self.command_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'executed': self.executed,
            'result': self.result
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria um comando a partir de um dicionário"""
        return cls(
            id=data['id'],
            client_id=data['client_id'],
            command_type=data['type'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            executed=data.get('executed', False),
            result=data.get('result')
        )
