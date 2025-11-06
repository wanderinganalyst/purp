"""
Configuration module for environment settings
"""

import os

# Determine if running in production
IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

# Print environment status on import
if IS_PRODUCTION:
    print("🚀 Running in PRODUCTION mode - fetching real data")
else:
    print("🔧 Running in DEVELOPMENT mode - using mock data")

def set_production_mode():
    """Set the environment to production mode"""
    os.environ['FLASK_ENV'] = 'production'
    print("✓ Switched to PRODUCTION mode")

def set_development_mode():
    """Set the environment to development mode"""
    os.environ['FLASK_ENV'] = 'development'
    print("✓ Switched to DEVELOPMENT mode")
