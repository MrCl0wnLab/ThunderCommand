from flask import Blueprint, jsonify, request
from app.services.client_manager import ClientManager
from app.services.command_executor import CommandExecutor
from core.utils.logger import app_logger, command_logger

# Criar blueprint para rotas de comandos
command_bp = Blueprint('command', __name__)

# Serviços
client_manager = ClientManager()
command_executor = CommandExecutor()

@command_bp.route('', methods=['GET'])
def get_command():
    """Endpoint para cliente receber comandos pendentes"""
    client_id = request.args.get('client_id')
    action = request.args.get('action')
    
    if not client_id:
        return jsonify({"success": False, "error": "Missing client_id parameter"}), 400
    
    # Caso especial para registrar cliente
    if action == 'register':
        user_agent = request.headers.get('User-Agent', 'Unknown')
        ip_address = request.remote_addr
        client_id = client_manager.register_client(user_agent, ip_address)
        return jsonify({"success": True, "client_id": client_id})
    
    # Verificar se cliente está ativo
    is_active = client_manager.check_client_activity(client_id)
    if not is_active:
        return jsonify({"success": False, "error": "Client not found or inactive"}), 404
    
    # Buscar comando pendente
    command = command_executor.get_pending_command(client_id)
    
    if not command:
        return jsonify({"success": True, "command": None})
    
    command_logger.info(f"Sending command {command.id} to client {client_id}")
    
    return jsonify({
        "success": True,
        "command": command.to_dict()
    })

@command_bp.route('/result', methods=['POST'])
def post_command_result():
    """Endpoint para cliente enviar resultado de comando executado"""
    try:
        data = request.json
        
        if not all(key in data for key in ['command_id', 'result']):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        command_id = data['command_id']
        result = data['result']
        
        # Registrar resultado
        command_executor.mark_command_executed(command_id, result)
        command_logger.info(f"Received result for command {command_id}")
        
        return jsonify({"success": True})
        
    except Exception as e:
        app_logger.error(f"Error processing command result: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to process command result"
        }), 500
