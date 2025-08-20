import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
    DATABASE_URI = os.environ.get('DATABASE_URL', 'thunder_command.db')
    
    # Configurações de segurança
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configurações da aplicação
    CLIENT_TIMEOUT_MINUTES = 30
    MAX_COMMAND_LOGS = 1000
    POLLING_INTERVAL_MS = 5000
    
    # Configurações de autenticação
    DEFAULT_USERNAME = os.environ.get('ADMIN_USERNAME', 'tandera')
    DEFAULT_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'tandera')

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    
class ProductionConfig(Config):
    DEBUG = False

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()
