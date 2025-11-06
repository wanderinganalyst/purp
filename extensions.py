from flask_sqlalchemy import SQLAlchemy

# single shared DB object to avoid circular imports
db = SQLAlchemy()
