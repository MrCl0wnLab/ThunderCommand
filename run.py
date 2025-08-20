from app import create_app
from config import get_config
import os

app = create_app()

if __name__ == "__main__":
    config = get_config()
    debug_mode = config.DEBUG
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host=host, port=port, debug=debug_mode)
