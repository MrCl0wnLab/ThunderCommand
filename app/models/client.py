from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Client:
    id: str
    user_agent: str
    ip_address: str
    last_seen: datetime
    info: dict
    
    @classmethod
    def create(cls, user_agent, ip_address):
        """Cria um novo cliente com ID único"""
        return cls(
            id=str(uuid.uuid4()),
            user_agent=user_agent,
            ip_address=ip_address,
            last_seen=datetime.now(),
            info={}
        )
    
    def update_last_seen(self):
        """Atualiza o timestamp da última vez que o cliente foi visto"""
        self.last_seen = datetime.now()
    
    def to_dict(self):
        """Converte o cliente para um dicionário"""
        return {
            'id': self.id,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'last_seen': self.last_seen.isoformat(),
            'info': self.info
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria um cliente a partir de um dicionário"""
        return cls(
            id=data['id'],
            user_agent=data['user_agent'],
            ip_address=data['ip_address'],
            last_seen=datetime.fromisoformat(data['last_seen']),
            info=data.get('info', {})
        )
