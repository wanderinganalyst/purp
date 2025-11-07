"""Configuration settings for the application."""
import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///bills.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_TYPE = 'filesystem'
    
    # Bills Cache
    BILLS_CACHE_TTL = int(os.environ.get('BILLS_CACHE_TTL', 300))  # 5 minutes
    REPS_CACHE_TTL = int(os.environ.get('REPS_CACHE_TTL', 300))    # 5 minutes
    
    # Address Verification
    USPS_USER_ID = os.environ.get('USPS_USER_ID')
    
    # URLs
    BILLS_URL = os.environ.get('BILLS_URL', 'https://house.mo.gov/BillList.aspx')
    REPS_URL = os.environ.get('REPS_URL', 'https://house.mo.gov/MemberRoster.aspx')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Database - Must use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Security
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # Performance
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/purp/app.log')
    
    # Validate required settings
    @classmethod
    def validate(cls):
        """Validate production configuration."""
        errors = []
        
        if not os.environ.get('SECRET_KEY') or os.environ.get('SECRET_KEY') == 'dev-secret-key':
            errors.append("SECRET_KEY must be set to a secure random value")
        
        if not os.environ.get('DATABASE_URL'):
            errors.append("DATABASE_URL must be set")
        
        if not os.environ.get('DATABASE_URL', '').startswith('postgresql'):
            errors.append("Production must use PostgreSQL database")
        
        if errors:
            raise ValueError("Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}