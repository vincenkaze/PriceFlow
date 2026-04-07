from flask import Flask
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from .config import config
from .extensions import db, migrate
from flask_login import LoginManager

login_manager = LoginManager()

# SocketIO for real-time updates (optional)
try:
    from flask_socketio import SocketIO, emit as socket_emit
    socketio_available = True
except ImportError:
    socketio_available = False
    SocketIO = None
    socket_emit = None

# Global socket instance
socketio = SocketIO() if socketio_available else None

def create_app(config_name='development'):
    flask_app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )

    flask_app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Make models visible to Alembic
    import app.models

    # ================== REGISTER BLUEPRINTS ==================
    from .routes.main import main_bp
    flask_app.register_blueprint(main_bp)

    from .routes.admin import admin_bp         
    flask_app.register_blueprint(admin_bp, url_prefix='/admin')

    from .routes.api import api_bp
    flask_app.register_blueprint(api_bp, url_prefix='/api')

    from .routes.auth import auth_bp
    flask_app.register_blueprint(auth_bp)

    from .routes.cart import cart_bp
    flask_app.register_blueprint(cart_bp)

    from .routes.orders import orders_bp
    flask_app.register_blueprint(orders_bp)

    # Initialize SocketIO if available
    if socketio_available and socketio:
        socketio.init_app(flask_app)
        # Import and init WebSocket emitter
        try:
            from modules.websocket_emitter import ws_emitter
            ws_emitter.init_app(socketio)
            print("[WS] WebSocket real-time updates enabled!")
        except ImportError:
            print("[WARN] WebSocket emitter not available")

    # Ensure instance folder exists
    os.makedirs('instance', exist_ok=True)

    # Create database tables if they don't exist
    with flask_app.app_context():
        db.create_all()

    # Context processor
    @flask_app.context_processor
    def inject_globals():
        return {'now': datetime.utcnow}

    print(f" PriceFlow App created in {config_name.upper()} mode")
    print(f"   DB -> {flask_app.config['SQLALCHEMY_DATABASE_URI']}")
    print("    Models loaded | Main + Admin + Auth + Cart + Orders routes registered")

    return flask_app