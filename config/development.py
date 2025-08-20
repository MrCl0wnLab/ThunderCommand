# Configurações específicas para ambiente de desenvolvimento
from config import Config

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    CLIENT_TIMEOUT_MINUTES = 60  # Maior timeout para desenvolvimento
