import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as needed"""
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        f'logs/{log_file}',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create different loggers for different components
app_logger = setup_logger('app', 'app.log')
websocket_logger = setup_logger('websocket', 'websocket.log')
command_logger = setup_logger('command', 'command.log')
auth_logger = setup_logger('auth', 'auth.log')

def log_command(client_id, command_type, command_id, success=True, error=None):
    """Structured logging for commands"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'client_id': client_id,
        'command_type': command_type,
        'command_id': command_id,
        'success': success
    }
    if error:
        log_data['error'] = str(error)
    
    if success:
        command_logger.info(f"Command executed - {log_data}")
    else:
        command_logger.error(f"Command failed - {log_data}")

def log_websocket_event(event_type, client_id=None, data=None, error=None):
    """Structured logging for WebSocket events"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'client_id': client_id,
    }
    if data:
        log_data['data'] = data
    if error:
        log_data['error'] = str(error)
        websocket_logger.error(f"WebSocket event error - {log_data}")
    else:
        websocket_logger.info(f"WebSocket event - {log_data}")

def log_auth_event(event_type, username, success=True, error=None):
    """Structured logging for authentication events"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'username': username,
        'success': success
    }
    if error:
        log_data['error'] = str(error)
        auth_logger.error(f"Auth event error - {log_data}")
    else:
        auth_logger.info(f"Auth event - {log_data}")
