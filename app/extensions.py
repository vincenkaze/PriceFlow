from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Single source of truth for ALL extensions
db = SQLAlchemy()
migrate = Migrate()