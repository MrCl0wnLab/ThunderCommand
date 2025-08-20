from app.models.client import Client
from core.utils.logger import app_logger
from core.database.client_repository import ClientRepository
from datetime import datetime, timedelta
from config import get_config

class ClientManager:
    def __init__(self):
        self.client_repo = ClientRepository()
        self.config = get_config()
    
    def register_client(self, user_agent, ip_address):
        """Registra um novo cliente ou atualiza existente"""
        # Verificar se o cliente já existe pelo IP e User-Agent
        existing_client = self.client_repo.find_by_ip_and_ua(ip_address, user_agent)
        
        if existing_client:
            # Atualizar cliente existente
            self.client_repo.update_last_seen(existing_client['id'])
            app_logger.info(f"Client updated: {existing_client['id']} from {ip_address}")
            return existing_client['id']
        else:
            # Criar novo cliente
            client = Client.create(user_agent, ip_address)
            self.client_repo.create(
                client_id=client.id,
                user_agent=client.user_agent,
                ip_address=client.ip_address
            )
            app_logger.info(f"New client registered: {client.id} from {ip_address}")
            return client.id
    
    def get_client(self, client_id):
        """Obtém um cliente pelo ID"""
        client_data = self.client_repo.find_by_id(client_id)
        if not client_data:
            return None
        return Client.from_dict(client_data)
    
    def update_client_info(self, client_id, info):
        """Atualiza informações adicionais do cliente"""
        self.client_repo.update_info(client_id, info)
        app_logger.info(f"Client info updated: {client_id}")
    
    def get_active_clients(self):
        """Retorna todos os clientes ativos (visto recentemente)"""
        timeout = datetime.now() - timedelta(minutes=self.config.CLIENT_TIMEOUT_MINUTES)
        clients_data = self.client_repo.get_active_since(timeout)
        
        return [Client.from_dict(client_data).to_dict() for client_data in clients_data]
    
    def check_client_activity(self, client_id):
        """Verifica se um cliente está ativo e atualiza timestamp"""
        client = self.get_client(client_id)
        if not client:
            return False
            
        # Verificar se o cliente está dentro do timeout
        timeout = datetime.now() - timedelta(minutes=self.config.CLIENT_TIMEOUT_MINUTES)
        if client.last_seen < timeout:
            return False
            
        # Atualizar último acesso
        self.client_repo.update_last_seen(client_id)
        return True
