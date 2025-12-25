"""
Rate limiting module to prevent abuse and brute force attacks.

This module provides rate limiting functionality using in-memory storage
or Redis (if available) to track request counts per IP address or user.
"""

from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time


class RateLimiter:
    """
    Rate limiter that tracks requests per IP address or user.
    
    Uses a sliding window algorithm to track requests within a time period.
    """
    
    def __init__(self):
        """Initialize the rate limiter with empty storage."""
        self._storage = defaultdict(list)
        self._lock = threading.Lock()
        self._cleanup_interval = 3600  # Clean up old entries every hour
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove old entries that are outside the time window."""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        with self._lock:
            keys_to_delete = []
            for key, timestamps in self._storage.items():
                # Remove timestamps older than 1 hour
                cutoff = current_time - 3600
                self._storage[key] = [ts for ts in timestamps if ts > cutoff]
                if not self._storage[key]:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._storage[key]
            
            self._last_cleanup = current_time
    
    def is_allowed(self, identifier: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if a request is allowed based on rate limit.
        
        Args:
            identifier: Unique identifier (IP address or user ID)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        self._cleanup_old_entries()
        
        current_time = time.time()
        cutoff = current_time - window_seconds
        
        with self._lock:
            timestamps = self._storage[identifier]
            # Remove old timestamps outside the window
            timestamps[:] = [ts for ts in timestamps if ts > cutoff]
            
            # Check if limit exceeded (check BEFORE adding current request)
            # If we already have max_requests, we can't allow another one
            current_count = len(timestamps)
            if current_count >= max_requests:
                # Log for debugging
                import logging
                logging.getLogger().warning(
                    f"Rate limit exceeded: identifier={identifier}, "
                    f"count={current_count}, max={max_requests}"
                )
                return False, 0
            
            # Add current request timestamp
            timestamps.append(current_time)
            remaining = max_requests - len(timestamps)
            
            return True, remaining
    
    def reset(self, identifier: str):
        """Reset rate limit for a specific identifier."""
        with self._lock:
            if identifier in self._storage:
                del self._storage[identifier]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60, per: str = 'ip', 
               error_message: str = "Rate limit exceeded. Please try again later."):
    """
    Decorator to rate limit a route.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        per: Rate limit per 'ip' or 'user'
        error_message: Error message to return when limit exceeded
    
    Example:
        @app.route('/api/login')
        @rate_limit(max_requests=5, window_seconds=60)  # 5 requests per 1 minute
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine identifier
            if per == 'user':
                from flask_login import current_user
                if current_user.is_authenticated:
                    identifier = f"user:{current_user.id}"
                else:
                    # Fallback to IP if user not authenticated
                    ip = request.remote_addr or request.environ.get('REMOTE_ADDR', 'unknown')
                    identifier = f"ip:{ip}"
            else:
                # Get IP address with fallback
                ip = request.remote_addr or request.environ.get('REMOTE_ADDR', 'unknown')
                identifier = f"ip:{ip}"
            
            # Check rate limit
            is_allowed, remaining = _rate_limiter.is_allowed(
                identifier, max_requests, window_seconds
            )
            
            # Log rate limit check (info level for visibility)
            current_app.logger.warning(
                f"[RATE LIMIT] identifier={identifier}, "
                f"is_allowed={is_allowed}, remaining={remaining}, "
                f"max_requests={max_requests}, path={request.path}, "
                f"ip={request.remote_addr}"
            )
            
            if not is_allowed:
                current_app.logger.error(
                    f"🚫 RATE LIMIT EXCEEDED: identifier={identifier}, "
                    f"path={request.path}, ip={request.remote_addr}"
                )
                # Return 429 immediately - don't call the function
                # Use make_response to ensure proper status code
                from flask import make_response
                response = make_response(jsonify({
                    'success': False,
                    'error': error_message,
                    'retry_after': window_seconds
                }), 429)
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(
                    int(time.time()) + window_seconds
                )
                return response
            
            # Add rate limit headers to response
            response = f(*args, **kwargs)
            
            # Handle tuple responses (response, status_code)
            if isinstance(response, tuple):
                response_obj, status_code = response
            else:
                response_obj = response
                status_code = None
            
            # Add headers to response object
            if hasattr(response_obj, 'headers'):
                response_obj.headers['X-RateLimit-Limit'] = str(max_requests)
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Reset'] = str(
                    int(time.time()) + window_seconds
                )
            
            # Return response in original format
            if isinstance(response, tuple):
                return response_obj, status_code
            return response_obj
        
        return decorated_function
    return decorator

