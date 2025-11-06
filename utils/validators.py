"""
Input validation utilities for the application.
"""
import re
import os
from typing import Tuple, Set

# Load common passwords list
_COMMON_PASSWORDS: Set[str] = set()
_COMMON_PASSWORDS_FILE = os.path.join(os.path.dirname(__file__), 'common_passwords.txt')

def _load_common_passwords():
    """Load common passwords from file."""
    global _COMMON_PASSWORDS
    if _COMMON_PASSWORDS:
        return  # Already loaded
    
    try:
        if os.path.exists(_COMMON_PASSWORDS_FILE):
            with open(_COMMON_PASSWORDS_FILE, 'r', encoding='utf-8') as f:
                _COMMON_PASSWORDS = set(line.strip().lower() for line in f if line.strip())
    except Exception as e:
        print(f"Warning: Could not load common passwords list: {e}")

# Load passwords on module import
_load_common_passwords()


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username input.
    
    Rules:
    - 3-150 characters
    - Only alphanumeric and underscores
    
    Returns:
        (is_valid, error_message)
    """
    if not username:
        return False, "Username is required."
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    
    if len(username) > 150:
        return False, "Username must be at most 150 characters."
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores."
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password input.
    
    Rules:
    - At least 10 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one special character (any non-alphanumeric)
    - Not in common passwords list
    
    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "Password is required."
    
    if len(password) < 10:
        return False, "Password must be at least 10 characters long."
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least one special character."
    
    # Check against common passwords list (case-insensitive)
    if password.lower() in _COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a stronger password."
    
    return True, ""


def validate_address(street_address: str, city: str, state: str, zipcode: str) -> Tuple[bool, str]:
    """
    Validate address components.
    
    Returns:
        (is_valid, error_message)
    """
    if not street_address or not street_address.strip():
        return False, "Street address is required."
    
    if len(street_address.strip()) > 255:
        return False, "Street address must be at most 255 characters."
    
    if not city or not city.strip():
        return False, "City is required."
    
    if len(city.strip()) > 100:
        return False, "City must be at most 100 characters."
    
    if not state or not state.strip():
        return False, "State is required."
    
    state = state.strip().upper()
    if not re.match(r'^[A-Z]{2}$', state):
        return False, "State must be a 2-letter code (e.g., MO)."
    
    if not zipcode or not zipcode.strip():
        return False, "Zip code is required."
    
    zipcode = zipcode.strip()
    if not re.match(r'^\d{5}(-\d{4})?$', zipcode):
        return False, "Zip code must be 5 digits or 9 digits with hyphen (e.g., 12345 or 12345-6789)."
    
    return True, ""


def validate_apt_unit(apt_unit: str) -> Tuple[bool, str]:
    """
    Validate apartment/unit number (optional field).
    
    Returns:
        (is_valid, error_message)
    """
    if apt_unit and len(apt_unit.strip()) > 50:
        return False, "Apt/Unit must be at most 50 characters."
    
    return True, ""


def sanitize_input(text: str, max_length: int = None) -> str:
    """
    Sanitize text input by stripping whitespace and limiting length.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (optional)
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    sanitized = text.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_comment_content(content: str) -> Tuple[bool, str]:
    """
    Validate comment content.
    
    Returns:
        (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Comment cannot be empty."
    
    if len(content.strip()) > 5000:
        return False, "Comment must be at most 5000 characters."
    
    return True, ""
