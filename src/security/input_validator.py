"""
Input validation and sanitization module.

This module provides utilities to validate and sanitize user input
to prevent injection attacks and ensure data integrity.
"""

import re
import html
from typing import Any, Optional
from flask import current_app


class InputValidator:
    """
    Input validator for common input types and patterns.
    """
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 format
    URL_PATTERN = re.compile(
        r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    )
    
    # Dangerous patterns to detect
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\bUNION\s+SELECT\b)',
        r'(\b--\s)',
        r'(\b/\*.*\*/\s)',
        r'(\b;\s*DROP\s)',
    ]
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        return bool(cls.EMAIL_PATTERN.match(email.strip().lower()))
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """
        Validate username format.
        
        Username must be 3-30 characters, alphanumeric with underscores only.
        
        Args:
            username: Username to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not username or not isinstance(username, str):
            return False
        return bool(cls.USERNAME_PATTERN.match(username.strip()))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        Validate phone number format (E.164).
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not phone or not isinstance(phone, str):
            return False
        return bool(cls.PHONE_PATTERN.match(phone.strip()))
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        return bool(cls.URL_PATTERN.match(url.strip()))
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """
        Detect potential SQL injection attempts.
        
        Args:
            value: Input value to check
            
        Returns:
            True if suspicious pattern detected, False otherwise
        """
        if not value or not isinstance(value, str):
            return False
        
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """
        Detect potential XSS attempts.
        
        Args:
            value: Input value to check
            
        Returns:
            True if suspicious pattern detected, False otherwise
        """
        if not value or not isinstance(value, str):
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_length(cls, value: str, min_length: int = 0, 
                       max_length: int = None) -> bool:
        """
        Validate string length.
        
        Args:
            value: String to validate
            min_length: Minimum length
            max_length: Maximum length (None for no limit)
            
        Returns:
            True if length is valid, False otherwise
        """
        if not isinstance(value, str):
            return False
        
        length = len(value)
        if length < min_length:
            return False
        if max_length is not None and length > max_length:
            return False
        return True


def sanitize_input(value: Any, input_type: str = 'text') -> str:
    """
    Sanitize user input based on type.
    
    Args:
        value: Input value to sanitize
        input_type: Type of input ('text', 'html', 'email', 'url')
        
    Returns:
        Sanitized string
    """
    if value is None:
        return ''
    
    # Convert to string
    if not isinstance(value, str):
        value = str(value)
    
    # Strip whitespace
    value = value.strip()
    
    # Type-specific sanitization
    if input_type == 'html':
        # Escape HTML entities
        value = html.escape(value)
    elif input_type == 'email':
        # Lowercase and strip
        value = value.lower().strip()
    elif input_type == 'url':
        # Basic URL sanitization
        value = value.strip()
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Log suspicious patterns
    if InputValidator.detect_sql_injection(value):
        current_app.logger.warning(
            f"Potential SQL injection detected: {value[:100]}"
        )
    
    if InputValidator.detect_xss(value):
        current_app.logger.warning(
            f"Potential XSS detected: {value[:100]}"
        )
    
    return value


def validate_and_sanitize(data: dict, schema: dict) -> tuple[dict, list[str]]:
    """
    Validate and sanitize a dictionary of input data based on a schema.
    
    Args:
        data: Input data dictionary
        schema: Validation schema with field names and rules
                Example: {
                    'email': {'type': 'email', 'required': True},
                    'name': {'type': 'text', 'required': True, 'max_length': 255},
                }
    
    Returns:
        Tuple of (sanitized_data, errors)
    """
    sanitized = {}
    errors = []
    
    for field, rules in schema.items():
        value = data.get(field)
        
        # Check required
        if rules.get('required', False) and (value is None or value == ''):
            errors.append(f"{field} is required")
            continue
        
        # Skip if not required and not provided
        if value is None or value == '':
            sanitized[field] = None
            continue
        
        # Sanitize based on type
        input_type = rules.get('type', 'text')
        sanitized_value = sanitize_input(value, input_type)
        
        # Validate based on type
        validator = InputValidator()
        is_valid = True
        
        if input_type == 'email':
            is_valid = validator.validate_email(sanitized_value)
            if not is_valid:
                errors.append(f"{field} must be a valid email address")
        elif input_type == 'username':
            is_valid = validator.validate_username(sanitized_value)
            if not is_valid:
                errors.append(
                    f"{field} must be 3-30 characters, alphanumeric with underscores only"
                )
        elif input_type == 'phone':
            is_valid = validator.validate_phone(sanitized_value)
            if not is_valid:
                errors.append(f"{field} must be a valid phone number")
        elif input_type == 'url':
            is_valid = validator.validate_url(sanitized_value)
            if not is_valid:
                errors.append(f"{field} must be a valid URL")
        
        # Validate length
        if is_valid:
            min_length = rules.get('min_length', 0)
            max_length = rules.get('max_length')
            if not validator.validate_length(sanitized_value, min_length, max_length):
                errors.append(
                    f"{field} length must be between {min_length} and {max_length or 'unlimited'}"
                )
                is_valid = False
        
        if is_valid:
            sanitized[field] = sanitized_value
        else:
            sanitized[field] = None
    
    return sanitized, errors

