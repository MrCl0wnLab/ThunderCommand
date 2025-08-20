from flask import Blueprint, jsonify, request, render_template
from app.auth import AuthManager
from app.services.client_manager import ClientManager
from app.services.command_executor import CommandExecutor

# Criar blueprint para rotas de administrador
admin_bp = Blueprint('admin', __name__)

# Decorador para exigir autenticação
login_required = AuthManager.login_required

# Serviços
client_manager = ClientManager()
command_executor = CommandExecutor()

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Renderiza o dashboard de administração"""
    return render_template('admin-dashboard.html')

@admin_bp.route('/clients')
@login_required
def get_clients():
    """Obtém lista de clientes ativos"""
    clients = client_manager.get_active_clients()
    return jsonify({"success": True, "clients": clients})

@admin_bp.route('/command', methods=['POST'])
@login_required
def create_command():
    """Cria um novo comando para ser executado por um cliente"""
    data = request.json
    
    # Validar dados da requisição
    if not all(key in data for key in ['client_id', 'type', 'content']):
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    # Criar comando
    try:
        command_id = command_executor.create_command(
            client_id=data['client_id'],
            command_type=data['type'],
            content=data['content']
        )
        return jsonify({"success": True, "command_id": command_id})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to create command"}), 500

@admin_bp.route('/command/<command_id>')
@login_required
def get_command_result(command_id):
    """Obtém o resultado da execução de um comando"""
    command = command_executor.command_repo.find_by_id(command_id)
    
    if not command:
        return jsonify({"success": False, "error": "Command not found"}), 404
    
    return jsonify({
        "success": True,
        "command": command,
        "executed": command.get('executed', False),
        "result": command.get('result')
    })
