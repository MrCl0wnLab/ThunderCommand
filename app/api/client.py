from flask import Blueprint, jsonify, request
from app.services.client_manager import ClientManager
from core.utils.logger import app_logger

# Criar blueprint para rotas de cliente
client_bp = Blueprint('client', __name__)

# Serviços
client_manager = ClientManager()

@client_bp.route('/register', methods=['POST'])
def register_client():
    """Endpoint para registrar um novo cliente"""
    try:
        data = request.json or {}
        
        # Obter informações do cliente
        user_agent = request.headers.get('User-Agent', 'Unknown')
        ip_address = request.remote_addr
        
        # Registrar cliente
        client_id = client_manager.register_client(user_agent, ip_address)
        
        # Atualizar informações adicionais se fornecidas
        if 'info' in data and isinstance(data['info'], dict):
            client_manager.update_client_info(client_id, data['info'])
        
        return jsonify({
            "success": True,
            "client_id": client_id
        })
        
    except Exception as e:
        app_logger.error(f"Error registering client: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to register client"
        }), 500

@client_bp.route('/ping', methods=['POST'])
def ping_client():
    """Endpoint para manter cliente ativo (ping)"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({"success": False, "error": "Missing client_id"}), 400
        
        # Verificar e atualizar atividade do cliente
        is_active = client_manager.check_client_activity(client_id)
        
        if not is_active:
            return jsonify({"success": False, "error": "Client not found or inactive"}), 404
        
        # Atualizar informações adicionais se fornecidas
        if 'info' in data and isinstance(data['info'], dict):
            client_manager.update_client_info(client_id, data['info'])
        
        return jsonify({"success": True})
        
    except Exception as e:
        app_logger.error(f"Error in client ping: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to process ping"
        }), 500
