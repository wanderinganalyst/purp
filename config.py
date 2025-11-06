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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Ensure these are set in production
    def __init__(self):
        if not self.SECRET_KEY:
            raise ValueError("No SECRET_KEY set for production")
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("No DATABASE_URL set for production")

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}