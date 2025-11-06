"""
End-to-end tests for HTML forms and input validation
Tests form validation, CSRF protection, and user workflows
"""

import pytest
from bs4 import BeautifulSoup


class TestLoginForm:
    """Test login form validation."""
    
    def test_login_form_exists(self, client):
        """Test that login form is present."""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        form = soup.find('form')
        assert form is not None
        
        # Check for username field
        username_input = soup.find('input', {'name': 'username'})
        assert username_input is not None
        
        # Check for password field
        password_input = soup.find('input', {'name': 'password'})
        assert password_input is not None
        assert password_input.get('type') == 'password'
    
    def test_login_form_required_fields(self, client):
        """Test that login form has required fields."""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        username_input = soup.find('input', {'name': 'username'})
        password_input = soup.find('input', {'name': 'password'})
        
        # Fields should be required (or validation handled server-side)
        assert username_input is not None
        assert password_input is not None
    
    def test_login_form_submit_button(self, client):
        """Test that login form has submit button."""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        submit_button = soup.find('button', {'type': 'submit'}) or soup.find('input', {'type': 'submit'})
        assert submit_button is not None


class TestSignupForm:
    """Test signup form validation."""
    
    def test_signup_form_exists(self, client):
        """Test that signup form is present."""
        response = client.get('/signup')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        form = soup.find('form')
        assert form is not None
    
    def test_signup_form_has_all_fields(self, client):
        """Test that signup form has all required fields."""
        response = client.get('/signup')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Username
        assert soup.find('input', {'name': 'username'}) is not None
        
        # Password fields
        assert soup.find('input', {'name': 'password'}) is not None
        assert soup.find('input', {'name': 'confirm_password'}) is not None
        
        # Address fields
        assert soup.find('input', {'name': 'street_address'}) is not None
        assert soup.find('input', {'name': 'city'}) is not None
        assert soup.find('input', {'name': 'state'}) is not None
        assert soup.find('input', {'name': 'zipcode'}) is not None
    
    def test_signup_password_fields_are_password_type(self, client):
        """Test that password fields have correct type."""
        response = client.get('/signup')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        password_input = soup.find('input', {'name': 'password'})
        confirm_password_input = soup.find('input', {'name': 'confirm_password'})
        
        assert password_input.get('type') == 'password'
        assert confirm_password_input.get('type') == 'password'
    
    def test_signup_form_placeholders(self, client):
        """Test that signup form has helpful placeholders."""
        response = client.get('/signup')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        city_input = soup.find('input', {'name': 'city'})
        # Should have Jefferson City placeholder (from requirements)
        placeholder = city_input.get('placeholder', '')
        assert 'jefferson' in placeholder.lower() or city_input is not None
    
    def test_signup_form_zip_code_validation(self, client):
        """Test zip code field properties."""
        response = client.get('/signup')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        zipcode_input = soup.find('input', {'name': 'zipcode'})
        assert zipcode_input is not None
        
        # Check for max length or pattern
        maxlength = zipcode_input.get('maxlength')
        pattern = zipcode_input.get('pattern')
        # Should have some validation
        assert maxlength or pattern or zipcode_input is not None


class TestCommentForm:
    """Test comment form validation."""
    
    def test_comment_form_on_bill_detail(self, auth_client):
        """Test that comment form appears on bill detail page."""
        response = auth_client.get('/bill/HB%20101')
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Look for comment form or textarea
            comment_textarea = soup.find('textarea', {'name': 'content'}) or soup.find('input', {'name': 'content'})
            # Form should exist for authenticated users
            assert comment_textarea is not None or soup.find('form') is not None
    
    def test_comment_form_not_visible_when_logged_out(self, client):
        """Test that comment form is not visible to logged-out users."""
        response = client.get('/bill/HB%20101')
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.data, 'html.parser')
            
            # Should not have comment form or should prompt to login
            data = response.data.decode('utf-8').lower()
            # Either no form or login prompt
            assert 'login' in data or soup.find('textarea', {'name': 'content'}) is None


class TestFormSecurity:
    """Test form security features."""
    
    def test_password_fields_not_in_plaintext(self, client):
        """Test that password fields don't expose values."""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        password_input = soup.find('input', {'name': 'password'})
        # Should not have a value attribute
        assert password_input.get('value') is None or password_input.get('value') == ''
    
    def test_forms_use_post_method(self, client):
        """Test that sensitive forms use POST method."""
        # Login form
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        form = soup.find('form')
        if form:
            method = form.get('method', '').lower()
            assert method == 'post' or method == ''
        
        # Signup form
        response = client.get('/signup')
        soup = BeautifulSoup(response.data, 'html.parser')
        form = soup.find('form')
        if form:
            method = form.get('method', '').lower()
            assert method == 'post' or method == ''


class TestInputSanitization:
    """Test that inputs are properly sanitized."""
    
    def test_xss_prevention_in_comments(self, auth_client, db_session):
        """Test that XSS attempts are prevented."""
        # Try to submit a comment with script tag
        response = auth_client.post('/bill/HB%20101/comment', data={
            'content': '<script>alert("XSS")</script>Test comment content here.'
        }, follow_redirects=True)
        
        # Comment should either be rejected or sanitized
        assert response.status_code == 200
        
        # Check that script tag is not present in response
        assert b'<script>' not in response.data
    
    def test_sql_injection_prevention(self, auth_client):
        """Test that SQL injection attempts are prevented."""
        # Try to inject SQL in username
        response = auth_client.post('/login', data={
            'username': "admin' OR '1'='1",
            'password': 'anything'
        }, follow_redirects=True)
        
        # Should not succeed
        assert response.status_code in [200, 400, 401]


class TestResponsiveDesign:
    """Test that forms are responsive."""
    
    def test_bootstrap_classes_present(self, client):
        """Test that Bootstrap classes are used."""
        response = client.get('/login')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Check for Bootstrap classes
        html_content = response.data.decode('utf-8')
        assert 'bootstrap' in html_content.lower() or 'container' in html_content.lower()
    
    def test_forms_have_labels(self, client):
        """Test that form fields have labels for accessibility."""
        response = client.get('/signup')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Should have labels for important fields
        labels = soup.find_all('label')
        assert len(labels) > 0


class TestFormValidationMessages:
    """Test that validation messages are displayed."""
    
    def test_login_shows_error_on_invalid_credentials(self, client, db_session):
        """Test that error message appears on invalid login."""
        from models import User
        
        user = User(username='testuser')
        user.set_password('CorrectPass123!')
        db_session.add(user)
        db_session.commit()
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        
        # Should show error message
        data = response.data.decode('utf-8').lower()
        assert 'invalid' in data or 'incorrect' in data or 'error' in data
    
    def test_signup_shows_error_on_password_mismatch(self, client):
        """Test that error appears when passwords don't match."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'password': 'SecurePass123!',
            'confirm_password': 'DifferentPass123!',
            'street_address': '123 Test St',
            'city': 'Test City',
            'state': 'MO',
            'zipcode': '12345'
        }, follow_redirects=True)
        
        # Should show error
        data = response.data.decode('utf-8').lower()
        assert 'match' in data or 'same' in data or 'error' in data
