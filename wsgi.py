#!/usr/bin/env python3
"""
Production entry point for Purp application.
Use with Gunicorn: gunicorn -c gunicorn_config.py wsgi:application
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Validate we're in production mode
if os.getenv('FLASK_ENV') != 'production':
    print("WARNING: FLASK_ENV is not set to 'production'", file=sys.stderr)
    print("Set FLASK_ENV=production for production deployment", file=sys.stderr)

# Import and validate configuration
from config import ProductionConfig
try:
    ProductionConfig.validate()
except ValueError as e:
    print(f"Configuration Error: {e}", file=sys.stderr)
    sys.exit(1)

# Import the Flask app
from main import create_app

# Create application instance
application = create_app('production')

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.getenv('LOG_FILE', '/var/log/purp/app.log'))
    ]
)

if __name__ == '__main__':
    # This won't be called when using gunicorn
    # But useful for testing with: python wsgi.py
    application.run()
