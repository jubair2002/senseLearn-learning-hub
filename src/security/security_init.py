"""
Security initialization module.

This module initializes all security features for the Flask application.
"""

from flask import Flask
from .security_headers import SecurityHeaders
from .csrf import init_csrf
from .account_lockout import AccountLockout


def init_security(app: Flask):
    """
    Initialize all security features for the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Initialize security headers
    SecurityHeaders.init_app(app)
    
    # Initialize CSRF protection
    init_csrf(app)
    
    # Security is now initialized
    app.logger.info("Security features initialized")


def get_security_config() -> dict:
    """
    Get security configuration.
    
    Returns:
        Dictionary with security configuration
    """
    return {
        'rate_limiting': {
            'enabled': True,
            'default_max_requests': 100,
            'default_window_seconds': 60,
        },
        'account_lockout': {
            'enabled': True,
            'max_attempts': 5,
            'lockout_duration_minutes': 30,
        },
        'csrf': {
            'enabled': True,
        },
        'password_validation': {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True,
        },
    }

