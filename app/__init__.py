from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from .config import config
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='development'):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # === REGISTER BLUEPRINTS ===
    from .routes.main import main_bp
    app.register_blueprint(main_bp)
    
    # Context processor for templates
    @app.context_processor
    def inject_globals():
        return {'now': datetime.utcnow}
    
    print(f" App created in {config_name.upper()} mode | DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("  Routes loaded — visit http://127.0.0.1:5000 to see the magic!")
    
    return app
