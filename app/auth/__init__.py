from functools import wraps
from flask import session, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
from config import get_config
from core.utils.logger import auth_logger, log_auth_event

class AuthManager:
    def __init__(self):
        config = get_config()
        self.username = config.DEFAULT_USERNAME
        self.password_hash = generate_password_hash(config.DEFAULT_PASSWORD)
    
    def verify_credentials(self, username, password):
        is_valid = (username == self.username and 
                    check_password_hash(self.password_hash, password))
        
        log_auth_event(username, 'login', 'success' if is_valid else 'failed')
        return is_valid
    
    @staticmethod
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                auth_logger.warning(f"Unauthorized access attempt to {request.path}")
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
