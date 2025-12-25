"""
Account lockout module.

This module provides functionality to lock user accounts after
multiple failed login attempts to prevent brute force attacks.
"""

from datetime import datetime, timedelta
from collections import defaultdict
import threading
from flask import request, current_app


class AccountLockout:
    """
    Account lockout manager.
    
    Tracks failed login attempts and locks accounts after threshold.
    """
    
    def __init__(self, max_attempts: int = 5, lockout_duration_minutes: int = 30):
        """
        Initialize account lockout.
        
        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_duration_minutes: Duration of lockout in minutes
        """
        self.max_attempts = max_attempts
        self.lockout_duration = timedelta(minutes=lockout_duration_minutes)
        self._failed_attempts = defaultdict(int)  # identifier -> count
        self._lockout_until = {}  # identifier -> datetime
        self._lock = threading.Lock()
        self._last_attempt_time = {}  # identifier -> datetime
    
    def record_failed_attempt(self, identifier: str):
        """
        Record a failed login attempt.
        
        Args:
            identifier: User identifier (email or user_id)
        """
        with self._lock:
            current_time = datetime.utcnow()
            
            # Reset attempts if lockout period has expired
            if identifier in self._lockout_until:
                if current_time > self._lockout_until[identifier]:
                    del self._lockout_until[identifier]
                    self._failed_attempts[identifier] = 0
            
            # Increment failed attempts
            self._failed_attempts[identifier] += 1
            self._last_attempt_time[identifier] = current_time
            
            # Lock account if threshold exceeded
            if self._failed_attempts[identifier] >= self.max_attempts:
                self._lockout_until[identifier] = current_time + self.lockout_duration
                current_app.logger.warning(
                    f"Account locked: {identifier} after {self._failed_attempts[identifier]} failed attempts"
                )
    
    def record_successful_attempt(self, identifier: str):
        """
        Record a successful login attempt and reset counter.
        
        Args:
            identifier: User identifier (email or user_id)
        """
        with self._lock:
            if identifier in self._failed_attempts:
                del self._failed_attempts[identifier]
            if identifier in self._lockout_until:
                del self._lockout_until[identifier]
            if identifier in self._last_attempt_time:
                del self._last_attempt_time[identifier]
    
    def is_locked(self, identifier: str) -> tuple[bool, datetime | None]:
        """
        Check if account is currently locked.
        
        Args:
            identifier: User identifier (email or user_id)
            
        Returns:
            Tuple of (is_locked, lockout_until_datetime)
        """
        with self._lock:
            if identifier not in self._lockout_until:
                return False, None
            
            lockout_until = self._lockout_until[identifier]
            current_time = datetime.utcnow()
            
            if current_time > lockout_until:
                # Lockout expired
                del self._lockout_until[identifier]
                self._failed_attempts[identifier] = 0
                return False, None
            
            return True, lockout_until
    
    def get_remaining_attempts(self, identifier: str) -> int:
        """
        Get remaining login attempts before lockout.
        
        Args:
            identifier: User identifier (email or user_id)
            
        Returns:
            Number of remaining attempts
        """
        with self._lock:
            attempts = self._failed_attempts.get(identifier, 0)
            return max(0, self.max_attempts - attempts)
    
    def reset(self, identifier: str):
        """
        Reset lockout for a specific identifier.
        
        Args:
            identifier: User identifier (email or user_id)
        """
        with self._lock:
            if identifier in self._failed_attempts:
                del self._failed_attempts[identifier]
            if identifier in self._lockout_until:
                del self._lockout_until[identifier]
            if identifier in self._last_attempt_time:
                del self._last_attempt_time[identifier]


# Global account lockout instance
_account_lockout = AccountLockout()


def get_account_lockout() -> AccountLockout:
    """Get the global account lockout instance."""
    return _account_lockout

