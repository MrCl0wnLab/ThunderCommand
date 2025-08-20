# Inicializador de rotas da API
from app.api.admin import admin_bp
from app.api.client import client_bp
from app.api.command import command_bp

def register_api_blueprints(app):
    """Registra todos os blueprints da API no aplicativo Flask"""
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(client_bp, url_prefix='/api/client')
    app.register_blueprint(command_bp, url_prefix='/command')
