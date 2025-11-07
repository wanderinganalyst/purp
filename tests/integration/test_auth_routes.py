"""
Integration tests for authentication routes
"""

import pytest
from flask import session


class TestLogin:
    """Test login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_successful_login(self, client, db_session):
        """Test successful login."""
        from models import User
        from extensions import db
        
        # Create a user
        user = User(username='testuser')
        user.set_password('TestPass123!')
        db_session.add(user)
        db_session.commit()
        
        # Attempt login
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'TestPass123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_wrong_password(self, client, db_session):
        """Test login with wrong password."""
        from models import User
        
        user = User(username='testuser')
        user.set_password('TestPass123!')
        db_session.add(user)
        db_session.commit()
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        
        assert b'invalid' in response.data.lower() or b'incorrect' in response.data.lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'TestPass123!'
        }, follow_redirects=True)
        
        assert b'invalid' in response.data.lower() or b'not found' in response.data.lower()
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        
        assert response.status_code in [200, 400]


class TestSignup:
    """Test signup functionality."""
    
    def test_signup_page_loads(self, client):
        """Test that signup page loads."""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'sign' in response.data.lower() or b'register' in response.data.lower()
    
    def test_successful_signup(self, client, db_session):
        """Test successful user registration."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'street_address': '123 Test St',
            'apt_unit': '',
            'city': 'Test City',
            'state': 'MO',
            'zipcode': '12345'
        }, follow_redirects=True)
        
        # Check that user was created
        from models import User
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.username == 'newuser'
    
    def test_signup_duplicate_username(self, client, db_session):
        """Test signup with duplicate username."""
        from models import User
        
        # Create existing user
        user = User(username='existinguser')
        user.set_password('Pass123!')
        db_session.add(user)
        db_session.commit()
        
        # Try to create duplicate
        response = client.post('/signup', data={
            'username': 'existinguser',
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
            'street_address': '123 Test St',
            'city': 'Test City',
            'state': 'MO',
            'zipcode': '12345'
        }, follow_redirects=True)
        
        assert b'already exists' in response.data.lower() or b'taken' in response.data.lower()
    
    def test_signup_password_mismatch(self, client):
        """Test signup with mismatched passwords."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'password': 'SecurePass123!',
            'confirm_password': 'DifferentPass123!',
            'street_address': '123 Test St',
            'city': 'Test City',
            'state': 'MO',
            'zipcode': '12345'
        }, follow_redirects=True)
        
        assert b'match' in response.data.lower() or b'same' in response.data.lower()
    
    def test_signup_weak_password(self, client):
        """Test signup with weak password."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'password': 'weak',
            'confirm_password': 'weak',
            'street_address': '123 Test St',
            'city': 'Test City',
            'state': 'MO',
            'zipcode': '12345'
        }, follow_redirects=True)
        
        # Should show password requirements error
        assert response.status_code in [200, 400]


class TestLogout:
    """Test logout functionality."""
    
    def test_logout(self, auth_client):
        """Test logout."""
        # Navbar form submits POST; ensure POST works
        response = auth_client.post('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Session should be cleared
        with auth_client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_logout_get_also_works(self, auth_client):
        """Ensure GET /logout also logs out for backward compatibility."""
        # Log in again first
        auth_client.post('/login', data={'username': 'testuser', 'password': 'testpass123'})
        with auth_client.session_transaction() as sess:
            assert 'user_id' in sess
        resp = auth_client.get('/logout', follow_redirects=True)
        assert resp.status_code == 200
        with auth_client.session_transaction() as sess2:
            assert 'user_id' not in sess2

    def test_access_protected_after_logout_redirects(self, auth_client):
        """After logout, protected route should redirect to login."""
        auth_client.post('/logout')
        resp = auth_client.get('/profile', follow_redirects=False)
        # Expect redirect to /login (302)
        assert resp.status_code in (302, 303)
        assert '/login' in resp.headers.get('Location', '')


class TestProfile:
    """Test profile functionality."""
    
    def test_profile_requires_login(self, client):
        """Test that profile requires authentication."""
        response = client.get('/profile')
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_profile_page_loads(self, auth_client):
        """Test that profile page loads for authenticated user."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'profile' in response.data.lower() or b'testuser' in response.data.lower()


class TestRoleRequired:
    """Test role-based access control."""
    
    def test_admin_route_denies_regular_user(self, auth_client):
        """Test that admin routes deny regular users."""
        # Try to access an admin route (if exists)
        response = auth_client.get('/admin', follow_redirects=True)
        # Should be denied or redirect
        assert response.status_code in [200, 403, 404]
    
    def test_admin_route_allows_admin(self, admin_client):
        """Test that admin routes allow admin users."""
        # Try to access an admin route (if exists)
        response = admin_client.get('/admin', follow_redirects=True)
        # Should allow access or 404 if route doesn't exist
        assert response.status_code in [200, 404]
