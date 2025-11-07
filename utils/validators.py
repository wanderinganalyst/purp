"""
Input validation utilities for the application.
"""
import re
import os
from typing import Tuple, Set, Optional

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


def validate_username(username: Optional[str]) -> Tuple[bool, Optional[str]]:
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
    
    if len(username) > 50:
        return False, "Username must be no more than 50 characters."
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username must be alphanumeric (letters, numbers, underscores only)."
    
    return True, None


def validate_password(password: Optional[str]) -> Tuple[bool, Optional[str]]:
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
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least one special character."
    
    # Check against common passwords list (case-insensitive)
    if password.lower() in _COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a stronger password."
    
    return True, None


def validate_address(street_address: Optional[str], city: Optional[str]=None, state: Optional[str]=None, zipcode: Optional[str]=None) -> Tuple[bool, Optional[str]]:
    """
    Validate address components.
    
    Returns:
        (is_valid, error_message)
    """
    if not street_address or not street_address.strip():
        return False, "Street address is required."
    sa = street_address.strip()
    if len(sa) < 5:
        return False, "Street address must be at least 5 characters."
    if len(sa) > 200:
        return False, "Street address must be no more than 200 characters."
    # Basic invalid character check: disallow angle brackets
    if re.search(r'[<>]', sa):
        return False, "Street address contains invalid characters."
    
    if city is not None:
        if not city.strip():
            return False, "City is required."
        if len(city.strip()) > 100:
            return False, "City must be at most 100 characters."
    
    if state is not None:
        if not state.strip():
            return False, "State is required."
        state_clean = state.strip().upper()
        if not re.match(r'^[A-Z]{2}$', state_clean):
            return False, "State must be a 2-letter code (e.g., MO)."
    
    if zipcode is not None:
        if not zipcode.strip():
            return False, "Zip code is required."
        zipcode_clean = zipcode.strip()
        if not re.match(r'^\d{5}(-\d{4})?$', zipcode_clean):
            return False, "Zip code must be 5 digits or 9 digits with hyphen (e.g., 12345 or 12345-6789)."
    return True, None


def validate_apt_unit(apt_unit: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate apartment/unit number (optional field).
    
    Returns:
        (is_valid, error_message)
    """
    if apt_unit and len(apt_unit.strip()) > 50:
        return False, "Apt/Unit must be no more than 50 characters."
    # Detect obvious HTML/script injection
    if apt_unit and re.search(r'<[^>]*>', apt_unit):
        return False, "Apt/Unit contains invalid characters."
    return True, None


def sanitize_input(text: Optional[str], max_length: int = None) -> str:
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
    # Remove script tags entirely
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE|re.DOTALL)
    # Remove other HTML tags but keep their inner text
    sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_comment_content(content: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate comment content (expects input to be sanitized upstream).

    Returns:
        (is_valid, error_message)
    """
    if content is None:
        return False, "Comment cannot be empty."
    c = content.strip()
    if not c:
        return False, "Comment cannot be empty."
    # Allow very short comments; just enforce a reasonable max length
    if len(c) > 5000:
        return False, "Comment must be no more than 5000 characters."
    return True, None
