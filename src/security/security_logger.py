"""
Security logging module.

This module provides specialized logging for security events
such as failed logins, suspicious activities, and security violations.
"""

from flask import request, current_app
from datetime import datetime
import json


class SecurityLogger:
    """
    Security event logger.
    
    Logs security-related events for monitoring and auditing.
    """
    
    @staticmethod
    def log_failed_login(email: str, reason: str = "Invalid credentials"):
        """
        Log a failed login attempt.
        
        Args:
            email: Email address used in login attempt
            reason: Reason for failure
        """
        current_app.logger.warning(
            f"SECURITY: Failed login attempt - Email: {email}, "
            f"IP: {request.remote_addr}, Reason: {reason}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_successful_login(user_id: int, email: str):
        """
        Log a successful login.
        
        Args:
            user_id: User ID
            email: User email
        """
        current_app.logger.info(
            f"SECURITY: Successful login - User ID: {user_id}, "
            f"Email: {email}, IP: {request.remote_addr}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_account_locked(identifier: str, reason: str = "Too many failed attempts"):
        """
        Log account lockout.
        
        Args:
            identifier: User identifier
            reason: Reason for lockout
        """
        current_app.logger.warning(
            f"SECURITY: Account locked - Identifier: {identifier}, "
            f"IP: {request.remote_addr}, Reason: {reason}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_suspicious_activity(activity_type: str, details: dict):
        """
        Log suspicious activity.
        
        Args:
            activity_type: Type of suspicious activity
            details: Additional details as dictionary
        """
        current_app.logger.warning(
            f"SECURITY: Suspicious activity - Type: {activity_type}, "
            f"IP: {request.remote_addr}, Details: {json.dumps(details)}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_rate_limit_exceeded(identifier: str, endpoint: str):
        """
        Log rate limit exceeded.
        
        Args:
            identifier: User or IP identifier
            endpoint: Endpoint that was rate limited
        """
        current_app.logger.warning(
            f"SECURITY: Rate limit exceeded - Identifier: {identifier}, "
            f"Endpoint: {endpoint}, IP: {request.remote_addr}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_csrf_violation(endpoint: str):
        """
        Log CSRF token violation.
        
        Args:
            endpoint: Endpoint where violation occurred
        """
        current_app.logger.warning(
            f"SECURITY: CSRF violation - Endpoint: {endpoint}, "
            f"IP: {request.remote_addr}, Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_injection_attempt(input_type: str, value: str):
        """
        Log potential injection attempt.
        
        Args:
            input_type: Type of injection (SQL, XSS, etc.)
            value: Suspicious input value (truncated)
        """
        truncated_value = value[:100] if len(value) > 100 else value
        current_app.logger.warning(
            f"SECURITY: Potential {input_type} injection - "
            f"IP: {request.remote_addr}, Value: {truncated_value}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_unauthorized_access(resource: str, user_id: int = None):
        """
        Log unauthorized access attempt.
        
        Args:
            resource: Resource that was accessed
            user_id: User ID if authenticated
        """
        user_info = f"User ID: {user_id}" if user_id else "Unauthenticated"
        current_app.logger.warning(
            f"SECURITY: Unauthorized access - {user_info}, "
            f"Resource: {resource}, IP: {request.remote_addr}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_password_change(user_id: int, email: str):
        """
        Log password change.
        
        Args:
            user_id: User ID
            email: User email
        """
        current_app.logger.info(
            f"SECURITY: Password changed - User ID: {user_id}, "
            f"Email: {email}, IP: {request.remote_addr}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def log_file_access(file_path: str, user_id: int, authorized: bool):
        """
        Log file access attempt.
        
        Args:
            file_path: Path to file accessed
            user_id: User ID
            authorized: Whether access was authorized
        """
        status = "Authorized" if authorized else "Unauthorized"
        current_app.logger.info(
            f"SECURITY: File access - {status} - User ID: {user_id}, "
            f"File: {file_path}, IP: {request.remote_addr}, "
            f"Time: {datetime.utcnow().isoformat()}"
        )

