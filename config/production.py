# Configurações específicas para ambiente de produção
from config import Config
from datetime import timedelta

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    # Configurações mais restritivas para produção
    CLIENT_TIMEOUT_MINUTES = 15
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
