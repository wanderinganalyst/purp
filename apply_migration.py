#!/usr/bin/env python
"""Apply database migration for draft bills and staffers."""
from main import app
from extensions import db
from flask_migrate import upgrade

if __name__ == '__main__':
    with app.app_context():
        # Apply all pending migrations
        upgrade()
        print("✓ Migration applied successfully!")
