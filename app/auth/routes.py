from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.auth import AuthManager
from core.utils.logger import auth_logger, log_auth_event

# Criar blueprint para rotas de autenticação
auth_bp = Blueprint('auth', __name__)

# Instanciar gerenciador de autenticação
auth_manager = AuthManager()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next', url_for('admin.dashboard'))
    
    # Verificar se o usuário já está autenticado
    if 'logged_in' in session:
        return redirect(next_url)
    
    error = None
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if auth_manager.verify_credentials(username, password):
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            
            auth_logger.info(f"Login successful for user {username}")
            log_auth_event(username, 'login', 'success')
            
            return redirect(next_url)
        else:
            error = "Credenciais inválidas"
            auth_logger.warning(f"Failed login attempt for username: {username}")
    
    return render_template('login.html', error=error, next=next_url)

@auth_bp.route('/logout')
def logout():
    if 'username' in session:
        username = session['username']
        auth_logger.info(f"User {username} logged out")
        log_auth_event(username, 'logout', 'success')
    
    session.clear()
    return redirect(url_for('auth.login'))
