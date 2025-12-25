"""
CSRF (Cross-Site Request Forgery) protection module.

This module provides CSRF token generation and validation to protect
against CSRF attacks.
"""

from functools import wraps
from flask import request, jsonify, session, current_app
import secrets
import hmac
import hashlib


class CSRFProtection:
    """
    CSRF protection using token-based validation.
    
    Generates and validates CSRF tokens to prevent cross-site request forgery.
    """
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a new CSRF token.
        
        Returns:
            A secure random token string
        """
        token = secrets.token_urlsafe(32)
        return token
    
    @staticmethod
    def validate_token(token: str, session_token: str) -> bool:
        """
        Validate a CSRF token against the session token.
        
        Args:
            token: Token from request
            session_token: Token stored in session
            
        Returns:
            True if token is valid, False otherwise
        """
        if not token or not session_token:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(token, session_token)
    
    @staticmethod
    def get_token_from_request() -> str:
        """
        Extract CSRF token from request.
        
        Checks headers first (X-CSRF-Token), then form data.
        
        Returns:
            Token string or empty string if not found
        """
        # Check header first (preferred for AJAX requests)
        token = request.headers.get('X-CSRF-Token', '')
        if token:
            return token
        
        # Check form data
        if request.is_json:
            data = request.get_json() or {}
            return data.get('csrf_token', '')
        
        # Check form data
        return request.form.get('csrf_token', '')


def csrf_protect(f):
    """
    Decorator to protect a route with CSRF validation.
    
    Skips validation for GET, HEAD, and OPTIONS requests.
    Requires CSRF token in header (X-CSRF-Token) or form data (csrf_token).
    
    Example:
        @app.route('/api/update')
        @csrf_protect
        def update():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF check for safe methods
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return f(*args, **kwargs)
        
        # Get token from session
        session_token = session.get('csrf_token')
        if not session_token:
            current_app.logger.warning(
                f"CSRF token missing in session for {request.path}"
            )
            return jsonify({
                'success': False,
                'error': 'CSRF token missing. Please refresh the page.'
            }), 403
        
        # Get token from request
        request_token = CSRFProtection.get_token_from_request()
        
        # Validate token
        if not CSRFProtection.validate_token(request_token, session_token):
            current_app.logger.warning(
                f"CSRF token validation failed for {request.path} from {request.remote_addr}"
            )
            return jsonify({
                'success': False,
                'error': 'Invalid CSRF token. Please refresh the page.'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def init_csrf(app):
    """
    Initialize CSRF protection for the app.
    
    Sets up token generation and adds token to session.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def set_csrf_token():
        """Set CSRF token in session if not present."""
        if 'csrf_token' not in session:
            session['csrf_token'] = CSRFProtection.generate_token()
    
    @app.context_processor
    def inject_csrf_token():
        """Make CSRF token available to templates."""
        return {
            'csrf_token': session.get('csrf_token', '')
        }

