"""
Security headers module.

This module provides middleware to add security headers to all responses
to protect against various attacks.
"""

from flask import request, current_app


class SecurityHeaders:
    """
    Security headers middleware.
    
    Adds various security headers to HTTP responses to protect against
    common web vulnerabilities.
    """
    
    @staticmethod
    def init_app(app):
        """
        Initialize security headers for the Flask app.
        
        Args:
            app: Flask application instance
        """
        @app.after_request
        def add_security_headers(response):
            """Add security headers to all responses."""
            # Content Security Policy
            # Adjust based on your needs - this is a restrictive policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline for compatibility
                "style-src 'self' 'unsafe-inline'; "  # Allow inline styles
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # X-Content-Type-Options: Prevent MIME type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # X-Frame-Options: Prevent clickjacking
            # Allow SAMEORIGIN for file serving endpoints
            if request.endpoint == 'serve_upload':
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            else:
                response.headers['X-Frame-Options'] = 'DENY'
            
            # X-XSS-Protection: Enable XSS filter (legacy, but still useful)
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Referrer-Policy: Control referrer information
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy: Control browser features
            permissions_policy = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=()"
            )
            response.headers['Permissions-Policy'] = permissions_policy
            
            # Strict-Transport-Security: Force HTTPS (only in production)
            if current_app.config.get('SESSION_COOKIE_SECURE', False):
                response.headers['Strict-Transport-Security'] = (
                    'max-age=31536000; includeSubDomains; preload'
                )
            
            # Remove server header (if possible)
            # Note: This might not work depending on your WSGI server
            if 'Server' in response.headers:
                del response.headers['Server']
            
            return response

