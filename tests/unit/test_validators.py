"""
Unit tests for utils/validators.py
"""

import pytest
from utils.validators import (
    validate_username,
    validate_password,
    validate_address,
    validate_apt_unit,
    validate_comment_content,
    sanitize_input
)


class TestValidateUsername:
    """Test username validation."""
    
    def test_valid_username(self):
        """Test that valid usernames pass validation."""
        valid, error = validate_username('john_doe')
        assert valid is True
        assert error is None
        
    def test_valid_username_with_numbers(self):
        """Test username with numbers."""
        valid, error = validate_username('user123')
        assert valid is True
        assert error is None
    
    def test_username_too_short(self):
        """Test that short usernames fail."""
        valid, error = validate_username('ab')
        assert valid is False
        assert 'at least 3 characters' in error.lower()
    
    def test_username_too_long(self):
        """Test that long usernames fail."""
        valid, error = validate_username('a' * 51)
        assert valid is False
        assert 'no more than 50 characters' in error.lower()
    
    def test_username_invalid_characters(self):
        """Test that usernames with special chars fail."""
        valid, error = validate_username('user@name')
        assert valid is False
        assert 'alphanumeric' in error.lower()
    
    def test_username_empty(self):
        """Test that empty username fails."""
        valid, error = validate_username('')
        assert valid is False
    
    def test_username_none(self):
        """Test that None username fails."""
        valid, error = validate_username(None)
        assert valid is False


class TestValidatePassword:
    """Test password validation."""
    
    def test_valid_password(self):
        """Test that valid password passes."""
        valid, error = validate_password('SecurePass123!')
        assert valid is True
        assert error is None
    
    def test_password_too_short(self):
        """Test that short password fails."""
        valid, error = validate_password('Short1!')
        assert valid is False
        assert 'at least 8 characters' in error.lower()
    
    def test_password_no_uppercase(self):
        """Test that password without uppercase fails."""
        valid, error = validate_password('lowercase123!')
        assert valid is False
        assert 'uppercase' in error.lower()
    
    def test_password_no_lowercase(self):
        """Test that password without lowercase fails."""
        valid, error = validate_password('UPPERCASE123!')
        assert valid is False
        assert 'lowercase' in error.lower()
    
    def test_password_no_digit(self):
        """Test that password without digit fails."""
        valid, error = validate_password('NoDigitsHere!')
        assert valid is False
        assert 'digit' in error.lower()
    
    def test_password_no_special(self):
        """Test that password without special char fails."""
        valid, error = validate_password('NoSpecial123')
        assert valid is False
        assert 'special character' in error.lower()
    
    def test_password_empty(self):
        """Test that empty password fails."""
        valid, error = validate_password('')
        assert valid is False
    
    def test_password_none(self):
        """Test that None password fails."""
        valid, error = validate_password(None)
        assert valid is False


class TestValidateAddress:
    """Test address validation."""
    
    def test_valid_address(self):
        """Test that valid address passes."""
        valid, error = validate_address('123 Main St')
        assert valid is True
        assert error is None
    
    def test_address_too_short(self):
        """Test that short address fails."""
        valid, error = validate_address('12')
        assert valid is False
        assert 'at least 5 characters' in error.lower()
    
    def test_address_too_long(self):
        """Test that long address fails."""
        valid, error = validate_address('a' * 201)
        assert valid is False
        assert 'no more than 200 characters' in error.lower()
    
    def test_address_invalid_characters(self):
        """Test that address with invalid chars fails."""
        valid, error = validate_address('123 Main <script>')
        assert valid is False
        assert 'invalid characters' in error.lower()
    
    def test_address_empty(self):
        """Test that empty address fails."""
        valid, error = validate_address('')
        assert valid is False


class TestValidateAptUnit:
    """Test apartment/unit validation."""
    
    def test_valid_apt_unit(self):
        """Test that valid apt unit passes."""
        valid, error = validate_apt_unit('Apt 5B')
        assert valid is True
        assert error is None
    
    def test_empty_apt_unit(self):
        """Test that empty apt unit is valid (optional field)."""
        valid, error = validate_apt_unit('')
        assert valid is True
        assert error is None
    
    def test_apt_unit_too_long(self):
        """Test that long apt unit fails."""
        valid, error = validate_apt_unit('a' * 51)
        assert valid is False
        assert 'no more than 50 characters' in error.lower()
    
    def test_apt_unit_invalid_characters(self):
        """Test that apt unit with invalid chars fails."""
        valid, error = validate_apt_unit('Apt <script>')
        assert valid is False
        assert 'invalid characters' in error.lower()


class TestValidateCommentContent:
    """Test comment content validation."""
    
    def test_valid_comment(self):
        """Test that valid comment passes."""
        valid, error = validate_comment_content('This is a valid comment.')
        assert valid is True
        assert error is None
    
    def test_comment_too_short(self):
        """Test that short comment fails."""
        valid, error = validate_comment_content('Hi')
        assert valid is False
        assert 'at least 5 characters' in error.lower()
    
    def test_comment_too_long(self):
        """Test that long comment fails."""
        valid, error = validate_comment_content('a' * 5001)
        assert valid is False
        assert 'no more than 5000 characters' in error.lower()
    
    def test_comment_empty(self):
        """Test that empty comment fails."""
        valid, error = validate_comment_content('')
        assert valid is False
    
    def test_comment_with_html(self):
        """Test that comment with HTML tags fails."""
        valid, error = validate_comment_content('This has <script>alert("XSS")</script>')
        assert valid is False
        assert 'not allowed' in error.lower() or 'invalid' in error.lower()


class TestSanitizeInput:
    """Test input sanitization."""
    
    def test_sanitize_normal_text(self):
        """Test that normal text is unchanged."""
        result = sanitize_input('Normal text here')
        assert result == 'Normal text here'
    
    def test_sanitize_removes_html_tags(self):
        """Test that HTML tags are removed."""
        result = sanitize_input('Text with <b>bold</b>')
        assert '<b>' not in result
        assert '</b>' not in result
    
    def test_sanitize_removes_script_tags(self):
        """Test that script tags are removed."""
        result = sanitize_input('<script>alert("XSS")</script>')
        assert '<script>' not in result
        assert 'alert' not in result or result == ''
    
    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        result = sanitize_input('  text  ')
        assert result == 'text'
    
    def test_sanitize_respects_max_length(self):
        """Test that max length is enforced."""
        long_text = 'a' * 1000
        result = sanitize_input(long_text, max_length=100)
        assert len(result) <= 100
    
    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        result = sanitize_input('')
        assert result == ''
    
    def test_sanitize_none(self):
        """Test sanitizing None value."""
        result = sanitize_input(None)
        assert result == ''
