from flask import Flask, Response, jsonify, request, render_template, session
from werkzeug.exceptions import HTTPException
from datetime import datetime
from core.utils.logger import app_logger
from core.database import init_db
from config import get_config
import os

# Importar blueprints
from app.auth.routes import auth_bp
from app.api import register_api_blueprints

def create_app():
    """Cria e configura a aplicação Flask"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Carregar configurações
    config = get_config()
    app.config.from_object(config)
    app.secret_key = config.SECRET_KEY
    
    # Inicializar banco de dados
    init_db()
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    register_api_blueprints(app)
    
    # Configurar handlers de erro
    register_error_handlers(app)
    
    # Rota raiz
    @app.route('/')
    def index():
        return render_template('login.html')
    
    return app

def register_error_handlers(app):
    """Registra handlers para erros HTTP"""
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        app_logger.error(f"HTTP error {error.code}: {error.description}")
        
        if request.path.startswith('/api') or request.path.startswith('/command'):
            return jsonify({
                "success": False,
                "error": error.description,
                "code": error.code
            }), error.code
            
        return render_template('error.html', error=error), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app_logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        
        if request.path.startswith('/api') or request.path.startswith('/command'):
            return jsonify({
                "success": False,
                "error": "Internal server error",
                "code": 500
            }), 500
            
        return render_template('error.html', 
                              error={"code": 500, "description": "Internal Server Error"}), 500
