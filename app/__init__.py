from flask import Flask
from datetime import datetime
import os

from .config import config
from .extensions import db, migrate

def create_app(config_name='development'):
    # Use flask_app name to avoid the "module 'app' has no attribute" error
    flask_app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )

    flask_app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    #  THIS LINE IS CRITICAL — makes all your models visible to Alembic
    import app.models

    # Register blueprints
    from .routes.main import main_bp
    flask_app.register_blueprint(main_bp)

    # Context processor
    @flask_app.context_processor
    def inject_globals():
        return {'now': datetime.utcnow}

    print(f" PriceFlow App created in {config_name.upper()} mode")
    print(f"   DB → {flask_app.config['SQLALCHEMY_DATABASE_URI']}")
    print("    Models loaded | Routes ready | Simulation ready to go feral")

    return flask_app