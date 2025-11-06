"""
Pytest configuration and fixtures for the test suite
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'True'


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application instance."""
    from main import create_app
    from extensions import db
    
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    
    # Create application context
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for testing."""
    from extensions import db
    
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def auth_client(client, db_session):
    """Create a client with an authenticated user."""
    from models import User
    from extensions import db
    
    # Create a test user
    user = User(
        username='testuser',
        role='user',
        street_address='123 Test St',
        city='Test City',
        state='MO',
        zipcode='12345'
    )
    user.set_password('testpass123')
    db.session.add(user)
    db.session.commit()
    
    # Log in
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    return client


@pytest.fixture
def admin_client(client, db_session):
    """Create a client with an authenticated admin user."""
    from models import User
    from extensions import db
    
    # Create an admin user
    admin = User(
        username='admin',
        role='admin',
        street_address='456 Admin St',
        city='Admin City',
        state='MO',
        zipcode='54321'
    )
    admin.set_password('adminpass123')
    db.session.add(admin)
    db.session.commit()
    
    # Log in
    client.post('/login', data={
        'username': 'admin',
        'password': 'adminpass123'
    })
    
    return client


@pytest.fixture
def sample_bill():
    """Return sample bill data for testing."""
    return {
        'number': 'HB 123',
        'sponsor': 'Rep. Test Sponsor',
        'title': 'Test Bill Title',
        'status': 'Active',
        'last_action': '2025-11-01',
        'summary': 'This is a test bill summary.',
        'committee': 'Test Committee',
        'introduced': '2025-10-15'
    }


@pytest.fixture
def sample_address():
    """Return sample address data for testing."""
    return {
        'street': '201 W Capitol Ave',
        'city': 'Jefferson City',
        'state': 'MO',
        'zip': '65101'
    }
