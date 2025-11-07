# Configuration Guide

This guide covers configuration options for Purp.

## Environment Variables

### Application Settings

```bash
# Flask environment (development, production, testing)
export FLASK_ENV=development

# Secret key for sessions (REQUIRED - change for production!)
export SECRET_KEY='your-secret-key-here'

# Database URL
export DATABASE_URL='sqlite:///instance/purp.db'
# For PostgreSQL:
# export DATABASE_URL='postgresql://user:password@localhost:5432/purp'
```

### Cache Configuration

```bash
# Bills cache TTL in seconds (default: 300 = 5 minutes)
export BILLS_CACHE_TTL=300

# Representatives cache TTL in seconds (default: 300 = 5 minutes)
export REPS_CACHE_TTL=300
```

### Development Mode

```bash
# Enable development mode (uses mock data)
export FLASK_ENV=development

# Disable debug mode
export FLASK_DEBUG=0
```

## Configuration Files

### main.py

Key configuration options in `main.py`:

```python
# Secret key (CHANGE THIS IN PRODUCTION!)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'sqlite:///instance/purp.db'
)

# Disable SQLAlchemy modification tracking
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Debug mode
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True') == 'True'
```

### config.py

The `config.py` file contains environment-specific configurations:

```python
class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/purp.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

## Database Configuration

### SQLite (Default - Development)

```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/purp.db'
```

**Pros:**
- No setup required
- Good for development
- File-based, portable

**Cons:**
- Not suitable for production
- Limited concurrency
- No advanced features

### PostgreSQL (Recommended - Production)

```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost:5432/purp'
```

**Setup:**

```bash
# Install PostgreSQL
brew install postgresql  # macOS
sudo apt-get install postgresql  # Ubuntu

# Create database
createdb purp

# Update DATABASE_URL
export DATABASE_URL='postgresql://localhost:5432/purp'
```

**Pros:**
- Production-ready
- High concurrency
- Advanced features
- Better performance

## Production Checklist

Before deploying to production, ensure:

- [ ] `DEBUG = False`
- [ ] Strong, random `SECRET_KEY` (use `secrets.token_hex(32)`)
- [ ] PostgreSQL database configured
- [ ] Environment variables set properly
- [ ] HTTPS/SSL enabled
- [ ] Reverse proxy configured (Nginx/Apache)
- [ ] Gunicorn or uWSGI configured
- [ ] Database backups enabled
- [ ] Logging configured
- [ ] Error monitoring enabled (Sentry, etc.)
- [ ] Security headers configured

## Security Configuration

### Generate Secure Secret Key

```python
import secrets
print(secrets.token_hex(32))
```

### Example Production Setup

```bash
# .env file (DO NOT COMMIT)
export FLASK_ENV=production
export SECRET_KEY='your-64-char-hex-string-here'
export DATABASE_URL='postgresql://user:password@db-host:5432/purp'
export FLASK_DEBUG=0
```

### Security Headers

Add to your reverse proxy (Nginx example):

```nginx
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

## Logging Configuration

### Development Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Production Logging

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/purp.log', maxBytes=10000000, backupCount=5)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
```

## Background Tasks

The application uses APScheduler for background tasks:

```python
# Schedule bills sync (weekly)
scheduler.add_job(
    func=sync_bills_job,
    trigger=CronTrigger(day_of_week='sun', hour=2),
    id='sync_bills_weekly',
    name='Sync bills every Sunday at 2 AM',
    replace_existing=True
)

# Schedule reps sync (quarterly)
scheduler.add_job(
    func=sync_reps_job,
    trigger=CronTrigger(month='1,4,7,10', day=1, hour=3),
    id='sync_reps_quarterly',
    name='Sync reps on first of quarter',
    replace_existing=True
)
```

## Docker Configuration

See [deployment/docker.md](../deployment/docker.md) for Docker-specific configuration.

## Cloud Deployment Configuration

See [deployment/cloud.md](../deployment/cloud.md) for cloud provider-specific configuration.
